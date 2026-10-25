import type { EngineInterface, ModelForkResult, Register, Timer } from 'claude-code'

// The main thread's cache entries live 1h from their last use. The first
// entry's hour starts when the request before the wait is sent, which is
// earlier than the Stop or tool call that arms by the time the reply takes to
// generate; 50 min keeps a margin for that.
const PERIOD_MS = 50 * 60_000
const TTL_MS = 60 * 60_000
// One refresh carries a wait to ~110 min. Over 184 days of transcripts
// (notes/background-wait-cache-expiry.md, notes/cc-2.1.289-in-turn-wait-cache-expiry.md)
// a second or third saved 2-8 more rewrites per kind of wait, while each one
// fired into a wait that never ends (a server left running, a dialog left
// open) is pure cost.
const MAX_REFRESHES = 1
const PROMPT =
  'Automated prompt-cache keepalive from the cache-keepalive plugin: no person ' +
  'reads this and nothing you write is kept. Call no tool. Reply with the single word: ok'
// The final response's record sits within the transcript's last few records.
const TAIL_BYTES = 1_000_000

// What the main thread waits on: background work after its turn ended, or
// its own pending tool calls (a dialog, a permission prompt, a foreground Bash).
type Wait = 'idle' | 'tool'

const clock = (ms: number) => {
  const d = new Date(ms)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const describe = (r: ModelForkResult) => {
  if (r.isAnswered === false && r.reason === 'nothing-to-fork') return 'nothing to fork'
  const u = r.usage
  const tokens = `read ${u.cache_read_input_tokens}, uncached ${u.input_tokens}, written ${u.cache_creation_input_tokens}, output ${u.output_tokens}`
  if (r.isAnswered) return tokens
  if (r.reason === 'api-error') return `API error ${r.status ?? 'no response'} ${r.error}; ${tokens}`
  return `${r.reason}; ${tokens}`
}

type Usage = { cache_creation?: { ephemeral_1h_input_tokens?: number; ephemeral_5m_input_tokens?: number } }

type Row = { type?: string; isSidechain?: boolean; message?: { usage?: Usage } }

const parse = (line: string, isFirst: boolean): Row | undefined => {
  try {
    return JSON.parse(line) as Row
  } catch (err) {
    // `tail -c` cuts the first line mid-record once the file outgrows the tail.
    if (isFirst && err instanceof SyntaxError) return undefined
    throw err
  }
}

// The TTL of the newest main-thread cache write in a transcript tail. The
// main thread drops to 5m in overage and off a subscription; a fork then
// finds the entry long gone and pays the whole prefix uncached. `none`: the
// tail holds main-thread responses but no write (a third-party endpoint
// writes no ephemeral_* field); `unwritten`: it holds no main-thread response.
type Ttl = '1h' | '5m' | 'none' | 'unwritten'

const cacheTtl = (tail: string): Ttl => {
  const lines = tail.split('\n')
  let hasResponse = false
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i] ?? ''
    if (!line.includes('"ephemeral_') && !line.includes('"type":"assistant"')) continue
    const r = parse(line, i === 0)
    if (r === undefined) break
    if (r.type !== 'assistant' || r.isSidechain === true) continue
    hasResponse = true
    const c = r.message?.usage?.cache_creation
    if ((c?.ephemeral_1h_input_tokens ?? 0) > 0) return '1h'
    if ((c?.ephemeral_5m_input_tokens ?? 0) > 0) return '5m'
  }
  return hasResponse ? 'none' : 'unwritten'
}

const WHY: Record<Exclude<Ttl, '1h'>, string> = {
  '5m': 'the newest cache write used the 5m TTL',
  none: `the newest cache write is not in the transcript's last ${TAIL_BYTES} bytes`,
  unwritten: `the transcript's last ${TAIL_BYTES} bytes hold no main-thread response`,
}

const ttlOf = async ($: EngineInterface, path: string): Promise<Ttl | { error: string }> => {
  const tail = await $.process.run(['tail', '-c', String(TAIL_BYTES), path])
  if (tail.exitCode !== 0) return { error: `tail of ${path} exited ${tail.exitCode}: ${tail.stderr.trim()}` }
  return cacheTtl(tail.stdout)
}

export const register: Register = on => {
  // Set by session.start: timers outlive the dispatch that starts them, so
  // they hang off the session's own hook rather than the Stop or tool call
  // that asks.
  let arm: ((wait: Wait) => Promise<void>) | undefined
  let timer: Timer | undefined
  let isTurnRunning = false
  // The main thread's pending tool calls, each event to its tool: the next
  // request waits for the last of them.
  const pending = new Map<object, string>()
  // tool.call carries no transcript path, nor does a hooks module's
  // classic.PreToolUse (its `e` is the tool.call envelope); SessionStart and
  // Stop do. A module reloaded mid-session (an edit to this folder) has none
  // until its next Stop.
  let transcriptPath: string | undefined

  const disarm = () => {
    timer?.cancel()
    timer = undefined
  }

  on('session.start', ($, e, next) => {
    // A dim transcript row the model never reads (kept in the JSONL as a
    // `system` record); failures also toast and stay pinned as the status
    // line until the next turn starts.
    const fail = (line: string) => {
      $.ui.log(line)
      $.ui.toast(line, { timeoutMs: 15_000 })
      $.ui.status(`failed: ${line}`)
    }

    const refresh = async (n: number, wait: Wait) => {
      // A turn still running after its Stop (a settings Stop hook made it go
      // on) keeps the cache warm by itself, and its own Stop arms again.
      if (wait === 'idle' && isTurnRunning) return
      // A later refresh (a cap above 1) can come due after the calls ended.
      if (wait === 'tool' && pending.size === 0) return
      let during = wait === 'tool' ? `; while ${[...pending.values()].join(', ')} was pending` : ''
      if (wait === 'tool') {
        // Gated when it fires rather than when armed: nearly every tool call
        // ends within seconds, and a tail per call is a process per call.
        // A session's first turn reaches the transcript file only once the
        // turn moves on (2.1.289: none of it for 175 s of an open dialog), and
        // 40 of 53 in-turn waits of 50+ min fell in a first turn. A TTL that
        // cannot be read is taken as the 1h every measured main thread here
        // used; the lapse check below reports one that was not.
        const ttl = transcriptPath === undefined ? 'no path' : await ttlOf($, transcriptPath)
        if (ttl === 'no path') during += '; TTL unread: no SessionStart or Stop since this module loaded gave a transcript path'
        else if (typeof ttl === 'object') return $.ui.log(`not refreshed: ${ttl.error}${during}`)
        else if (ttl === 'unwritten') during += `; TTL unread: ${WHY.unwritten}`
        else if (ttl !== '1h') return $.ui.log(`not refreshed: ${WHY[ttl]}${during}`)
      }
      const r = await $.model.fork({ prompt: PROMPT })
      const line = `refresh ${n}/${MAX_REFRESHES}: ${describe(r)}${during}`
      if (!r.isAnswered && r.reason !== 'empty-reply') return fail(line)
      const u = r.usage
      // The fork re-sends the main thread's last request: reading less than
      // it paid uncached means that entry had lapsed (or /model replaced
      // it), so this refresh warmed nothing and a later one cannot either.
      if (u.cache_read_input_tokens < u.input_tokens + u.cache_creation_input_tokens)
        return fail(`${line}; the cache had already lapsed`)
      $.ui.log(line)
      if (n < MAX_REFRESHES) return schedule(n + 1, wait)
      if (wait === 'idle') $.ui.status(`cache warm until ${clock((await $.clock.now()) + TTL_MS)}`)
    }

    const schedule = async (n: number, wait: Wait) => {
      // Set before any await, so a call that ends at once still finds it.
      timer = $.clock.after(PERIOD_MS, () => {
        timer = undefined
        refresh(n, wait).catch(err => {
          fail(`refresh ${n} threw: ${err instanceof Error ? (err.stack ?? err.message) : String(err)}`)
          throw err
        })
      })
      // Every main-thread tool call arms, and a status line per call would flicker.
      if (wait === 'idle') $.ui.status(`refresh ${n}/${MAX_REFRESHES} at ${clock((await $.clock.now()) + PERIOD_MS)}`)
    }

    arm = wait => schedule(1, wait)
    return next(e)
  })

  on('turn.start', ($, e, next) => {
    if (e.agentId !== undefined) return next(e)
    isTurnRunning = true
    disarm()
    $.ui.status(undefined)
    return next(e)
  })

  on('turn.complete', ($, e, next) => {
    if (e.agentId === undefined) isTurnRunning = false
    return next(e)
  })

  // `next(e)` spans the permission prompt (AskUserQuestion's dialog among
  // them) and the tool's run: the whole time the main thread sends nothing.
  on('tool.call', async ($, e, next) => {
    if (e.agentId !== undefined) return next(e)
    if (arm === undefined) throw new Error('session.start never ran here, so nothing can arm')
    const isFirst = pending.size === 0
    pending.set(e, e.tool)
    try {
      if (isFirst) await arm('tool')
      return await next(e)
    } finally {
      pending.delete(e)
      if (pending.size === 0) disarm()
    }
  })

  on('classic.SessionStart', ($, e, next) => {
    transcriptPath = e.transcript_path
    return next(e)
  })

  on('classic.Stop', async ($, e, next) => {
    const result = await next(e)
    disarm()
    transcriptPath = e.transcript_path
    if ((e.background_tasks ?? []).length === 0 || result.block !== undefined) return result
    if (arm === undefined) {
      $.ui.toast('session.start never ran here, so nothing is armed', { timeoutMs: 15_000 })
      return result
    }
    const ttl = await ttlOf($, e.transcript_path)
    if (ttl !== '1h') {
      $.ui.log(`not armed: ${typeof ttl === 'object' ? ttl.error : WHY[ttl]}`)
      return result
    }
    await arm('idle')
    return result
  })

  on('session.compact', ($, e, next) => {
    disarm()
    $.ui.status(undefined)
    return next(e)
  })

  on('session.end', ($, e, next) => {
    disarm()
    return next(e)
  })
}

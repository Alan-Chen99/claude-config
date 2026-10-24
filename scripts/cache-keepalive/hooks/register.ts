import type { ModelForkResult, Register, Timer } from 'claude-code'

// The main thread's cache entries live 1h from their last use. The first
// entry's hour starts when the turn's final request is sent, which is
// earlier than Stop by the time the reply takes to generate; 50 min keeps a
// margin for that.
const PERIOD_MS = 50 * 60_000
const TTL_MS = 60 * 60_000
// One refresh carries a wait to ~110 min. Over 184 days of transcripts
// (notes/background-wait-cache-expiry.md) a second or third saved 0-4 more
// rewrites, while each one fired into a wait that never ends (a server left
// running) is pure cost.
const MAX_REFRESHES = 1
const PROMPT =
  'Automated prompt-cache keepalive from the cache-keepalive plugin: no person ' +
  'reads this and nothing you write is kept. Call no tool. Reply with the single word: ok'
// The final response's record sits within the transcript's last few records.
const TAIL_BYTES = 1_000_000

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
// finds the entry long gone and pays the whole prefix uncached.
const cacheTtl = (tail: string): '1h' | '5m' | undefined => {
  const lines = tail.split('\n')
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i] ?? ''
    if (!line.includes('"ephemeral_')) continue
    const r = parse(line, i === 0)
    if (r === undefined) return undefined
    const c = r.type === 'assistant' && r.isSidechain !== true ? r.message?.usage?.cache_creation : undefined
    if ((c?.ephemeral_1h_input_tokens ?? 0) > 0) return '1h'
    if ((c?.ephemeral_5m_input_tokens ?? 0) > 0) return '5m'
  }
  return undefined
}

export const register: Register = on => {
  // Set by session.start: timers outlive the dispatch that starts them, so
  // they hang off the session's own hook rather than the Stop that asks.
  let arm: (() => Promise<void>) | undefined
  let timer: Timer | undefined
  let isTurnRunning = false

  on('session.start', ($, e, next) => {
    // A dim transcript row the model never reads (kept in the JSONL as a
    // `system` record); failures also toast and stay pinned as the status
    // line until the next turn starts.
    const fail = (line: string) => {
      $.ui.log(line)
      $.ui.toast(line, { timeoutMs: 15_000 })
      $.ui.status(`failed: ${line}`)
    }

    const refresh = async (n: number) => {
      // A turn still running (a settings Stop hook made it go on) keeps the
      // cache warm by itself, and its own Stop arms again.
      if (isTurnRunning) return
      const r = await $.model.fork({ prompt: PROMPT })
      const line = `refresh ${n}/${MAX_REFRESHES}: ${describe(r)}`
      if (!r.isAnswered && r.reason !== 'empty-reply') return fail(line)
      const u = r.usage
      // The fork re-sends the main thread's last request: reading less than
      // it paid uncached means that entry had lapsed (or /model replaced
      // it), so this refresh warmed nothing and a later one cannot either.
      if (u.cache_read_input_tokens < u.input_tokens + u.cache_creation_input_tokens)
        return fail(`${line}; the cache had already lapsed`)
      $.ui.log(line)
      const now = await $.clock.now()
      if (n < MAX_REFRESHES) return schedule(n + 1, now)
      $.ui.status(`cache warm until ${clock(now + TTL_MS)}`)
    }

    const schedule = (n: number, now: number) => {
      $.ui.status(`refresh ${n}/${MAX_REFRESHES} at ${clock(now + PERIOD_MS)}`)
      timer = $.clock.after(PERIOD_MS, () => {
        timer = undefined
        refresh(n).catch(err => {
          fail(`refresh ${n} threw: ${err instanceof Error ? (err.stack ?? err.message) : String(err)}`)
          throw err
        })
      })
    }

    arm = async () => schedule(1, await $.clock.now())
    return next(e)
  })

  on('turn.start', ($, e, next) => {
    isTurnRunning = true
    timer?.cancel()
    timer = undefined
    $.ui.status(undefined)
    return next(e)
  })

  on('turn.complete', ($, e, next) => {
    if (e.agentId === undefined) isTurnRunning = false
    return next(e)
  })

  on('classic.Stop', async ($, e, next) => {
    const result = await next(e)
    timer?.cancel()
    timer = undefined
    if ((e.background_tasks ?? []).length === 0 || result.block !== undefined) return result
    if (arm === undefined) {
      $.ui.toast('session.start never ran here, so nothing is armed', { timeoutMs: 15_000 })
      return result
    }
    const tail = await $.process.run(['tail', '-c', String(TAIL_BYTES), e.transcript_path])
    if (tail.exitCode !== 0) {
      $.ui.log(`not armed: tail of ${e.transcript_path} exited ${tail.exitCode}: ${tail.stderr.trim()}`)
      return result
    }
    const ttl = cacheTtl(tail.stdout)
    if (ttl !== '1h') {
      $.ui.log(`not armed: the newest cache write ${ttl === '5m' ? 'used the 5m TTL' : `is not in the transcript's last ${TAIL_BYTES} bytes`}`)
      return result
    }
    await arm()
    return result
  })

  on('session.compact', ($, e, next) => {
    timer?.cancel()
    timer = undefined
    $.ui.status(undefined)
    return next(e)
  })

  on('session.end', ($, e, next) => {
    timer?.cancel()
    timer = undefined
    return next(e)
  })
}

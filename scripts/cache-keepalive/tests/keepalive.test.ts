import { describe, expect, mock, test } from 'claude-code/testing'
import type { ModelForkResult, On } from 'claude-code'

const MIN = 60_000
const TASK = { id: 'b1', type: 'shell', status: 'running', description: 'sleep 9000' }
const WARM = { input_tokens: 9, output_tokens: 3, cache_read_input_tokens: 200_000, cache_creation_input_tokens: 0 }
const answered = (usage = WARM): ModelForkResult => ({ isAnswered: true, text: 'ok', usage })

const row = (ttl: '1h' | '5m', isSidechain = false) =>
  JSON.stringify({
    type: 'assistant',
    isSidechain,
    message: { usage: { cache_creation: { ephemeral_1h_input_tokens: ttl === '1h' ? 500 : 0, ephemeral_5m_input_tokens: ttl === '5m' ? 500 : 0 } } },
  })
// A tail cut mid-record, then a main-thread write, a newer subagent one and a system row.
const TAIL_1H = ['"ephemeral_5m_input_tokens":9}}}', row('1h'), row('5m', true), '{"type":"system"}', ''].join('\n')

// How long each tool's call runs, in minutes; a dialog the person answers late is one such call.
type World = { fork?: () => ModelForkResult; stop?: { block?: string }; tail?: string; tailExit?: number; toolMin?: Record<string, number> }

const world = (on: On, { fork = () => answered(), stop = {}, tail = TAIL_1H, tailExit = 0, toolMin = {} }: World = {}) => {
  const clock = mock.clock(on, { now: Date.UTC(2026, 9, 23, 12, 0) })
  const seen = { forks: [] as number[], logs: [] as string[], toasts: [] as string[], status: [] as (string | undefined)[], runs: [] as string[][], calls: [] as (string | undefined)[] }
  on('model.fork', () => {
    seen.forks.push(clock.now())
    return { value: fork() }
  })
  on('process.run', ($, e) => {
    seen.runs.push([...e.argv])
    const value = { exitCode: tailExit, stdout: tail, stderr: tailExit === 0 ? '' : 'tail: cannot open\n', isStdoutTruncated: false, isStderrTruncated: false }
    return { value }
  })
  on('ui.log', ($, e) => (seen.logs.push(e.text), { value: undefined }))
  on('ui.toast', ($, e) => (seen.toasts.push(e.text), { value: undefined }))
  on('ui.status', ($, e) => (seen.status.push(e.text), { value: undefined }))
  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('turn.start', ($, e) => ({ turnId: e.turnId }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('classic.Stop', () => stop)
  on('classic.SessionStart', () => ({}))
  on('tool.call', async ($, e) => {
    seen.calls.push(e.agentId)
    await clock.sleep((toolMin[e.tool] ?? 0) * MIN)
    return { result: {} }
  })
  return { clock, seen }
}

const SESSION = { cwd: '/w', surface: 'terminal', isInteractive: true } as const
const START = { text: 'go', turnId: 't1' }
const COMPLETE = { answer: 'waiting', durationMs: 1000, isAborted: false, turnId: 't1', reason: 'answer' } as const
const STOP = { stop_hook_active: false, background_tasks: [TASK], transcript_path: '/p/s.jsonl' }
const ASK = {
  tool: 'AskUserQuestion' as const,
  questions: [{ question: 'Which one?', header: 'Pick', options: [{ label: 'A', description: 'a' }, { label: 'B', description: 'b' }], multiSelect: false }],
}
const BASH = { tool: 'Bash', command: 'sleep 3600' } as const
const STARTUP = { source: 'startup', transcript_path: '/p/s.jsonl' } as const

describe('cache-keepalive', () => {
  test('refreshes once, 50 min after a Stop with background work in flight', async ($, on) => {
    const { clock, seen } = world(on)
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await $.turn.complete(COMPLETE)
    expect(seen.runs).toEqual([['tail', '-c', '1000000', '/p/s.jsonl']])
    expect(seen.status.at(-1)).toMatch(/^refresh 1\/1 at \d\d:\d\d$/)
    await clock.advance(49 * MIN)
    expect(seen.forks).toHaveLength(0)
    await clock.advance(1 * MIN)
    expect(seen.forks).toHaveLength(1)
    await clock.advance(300 * MIN)
    expect(seen.forks).toHaveLength(1)
    expect(seen.logs).toEqual(['refresh 1/1: read 200000, uncached 9, written 0, output 3'])
    expect(seen.toasts).toHaveLength(0)
    expect(seen.status.at(-1)).toMatch(/^cache warm until \d\d:\d\d$/)
  })

  test('arms nothing when no background work is in flight', async ($, on) => {
    const { clock, seen } = world(on)
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop({ ...STOP, background_tasks: [] })
    await $.turn.complete(COMPLETE)
    await clock.advance(300 * MIN)
    expect(seen.forks).toHaveLength(0)
    expect(seen.runs).toHaveLength(0)
  })

  test('arms nothing when a Stop hook blocks the stop', async ($, on) => {
    const { clock, seen } = world(on, { stop: { block: 'keep going' } })
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await clock.advance(300 * MIN)
    expect(seen.forks).toHaveLength(0)
  })

  test('arms nothing when the main thread caches for 5 min', async ($, on) => {
    const tail = [row('1h'), row('5m'), row('1h', true), ''].join('\n')
    const { clock, seen } = world(on, { tail })
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await $.turn.complete(COMPLETE)
    await clock.advance(300 * MIN)
    expect(seen.forks).toHaveLength(0)
    expect(seen.logs).toEqual(['not armed: the newest cache write used the 5m TTL'])
  })

  test('arms nothing when the tail holds responses but no cache write', async ($, on) => {
    // A third-party endpoint's usage carries no ephemeral_* field.
    const tail = `${JSON.stringify({ type: 'assistant', isSidechain: false, message: { usage: { input_tokens: 9 } } })}\n`
    const { clock, seen } = world(on, { tail })
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await $.turn.complete(COMPLETE)
    await clock.advance(300 * MIN)
    expect(seen.forks).toHaveLength(0)
    expect(seen.logs).toEqual(["not armed: the newest cache write is not in the transcript's last 1000000 bytes"])
  })

  test('arms nothing when the tail holds no response', async ($, on) => {
    const { clock, seen } = world(on, { tail: '{"type":"system"}\n' })
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await $.turn.complete(COMPLETE)
    await clock.advance(300 * MIN)
    expect(seen.forks).toHaveLength(0)
    expect(seen.logs).toEqual(["not armed: the transcript's last 1000000 bytes hold no main-thread response"])
  })

  test('a whole first line counts when the transcript is shorter than the tail', async ($, on) => {
    const { clock, seen } = world(on, { tail: `${row('1h')}\n` })
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await $.turn.complete(COMPLETE)
    await clock.advance(50 * MIN)
    expect(seen.forks).toHaveLength(1)
  })

  test('an unreadable transcript arms nothing and says why', async ($, on) => {
    const { clock, seen } = world(on, { tailExit: 1 })
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await clock.advance(300 * MIN)
    expect(seen.forks).toHaveLength(0)
    expect(seen.logs).toEqual(['not armed: tail of /p/s.jsonl exited 1: tail: cannot open'])
  })

  test('the next turn disarms it', async ($, on) => {
    const { clock, seen } = world(on)
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await $.turn.complete(COMPLETE)
    await clock.advance(30 * MIN)
    await $.turn.start({ text: '', turnId: 't2' })
    await clock.advance(300 * MIN)
    expect(seen.forks).toHaveLength(0)
    expect(seen.status.at(-1)).toBe(undefined)
  })

  test('skips the refresh while the turn is still running', async ($, on) => {
    const { clock, seen } = world(on)
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await clock.advance(300 * MIN)
    expect(seen.forks).toHaveLength(0)
  })

  test('a lapsed cache is reported, not counted as a refresh', async ($, on) => {
    const cold = { input_tokens: 200_000, output_tokens: 3, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 }
    const { clock, seen } = world(on, { fork: () => answered(cold) })
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await $.turn.complete(COMPLETE)
    await clock.advance(50 * MIN)
    const line = 'refresh 1/1: read 0, uncached 200000, written 0, output 3; the cache had already lapsed'
    expect(seen.toasts).toEqual([line])
    expect(seen.logs).toEqual([line])
    expect(seen.status.at(-1)).toBe(`failed: ${line}`)
  })

  test('an API error is reported', async ($, on) => {
    const zero = { input_tokens: 0, output_tokens: 0, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 }
    const { clock, seen } = world(on, { fork: () => ({ isAnswered: false, reason: 'api-error', status: 529, error: 'overloaded', usage: zero }) })
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await $.turn.complete(COMPLETE)
    await clock.advance(50 * MIN)
    expect(seen.toasts).toEqual(['refresh 1/1: API error 529 overloaded; read 0, uncached 0, written 0, output 0'])
  })

  test('refreshes once, 50 min into a main-thread tool call', async ($, on) => {
    const { clock, seen } = world(on, { toolMin: { AskUserQuestion: 120 } })
    await $.session.start(SESSION)
    await $.classic.SessionStart(STARTUP)
    await $.turn.start(START)
    const call = $.tool.call(ASK)
    await clock.advance(49 * MIN)
    expect(seen.forks).toHaveLength(0)
    await clock.advance(1 * MIN)
    expect(seen.forks).toHaveLength(1)
    expect(seen.runs).toEqual([['tail', '-c', '1000000', '/p/s.jsonl']])
    expect(seen.logs).toEqual(['refresh 1/1: read 200000, uncached 9, written 0, output 3; while AskUserQuestion was pending'])
    await clock.advance(70 * MIN)
    await call
    await clock.advance(300 * MIN)
    expect(seen.forks).toHaveLength(1)
    expect(seen.status.filter(s => s !== undefined)).toEqual([])
  })

  test('a tool call that ends within the period arms nothing', async ($, on) => {
    const { clock, seen } = world(on, { toolMin: { Bash: 49 } })
    await $.session.start(SESSION)
    await $.classic.SessionStart(STARTUP)
    await $.turn.start(START)
    const call = $.tool.call(BASH)
    await clock.advance(49 * MIN)
    await call
    await clock.advance(300 * MIN)
    expect(seen.forks).toHaveLength(0)
    expect(seen.runs).toHaveLength(0)
  })

  test('parallel calls keep it armed until the last one ends', async ($, on) => {
    const { clock, seen } = world(on, { toolMin: { Bash: 10, AskUserQuestion: 70 } })
    await $.session.start(SESSION)
    await $.classic.SessionStart(STARTUP)
    await $.turn.start(START)
    const calls = Promise.all([$.tool.call(BASH), $.tool.call(ASK)])
    await clock.advance(50 * MIN)
    expect(seen.logs).toEqual(['refresh 1/1: read 200000, uncached 9, written 0, output 3; while AskUserQuestion was pending'])
    await clock.advance(20 * MIN)
    await calls
    expect(seen.forks).toHaveLength(1)
  })

  test("a subagent's tool call arms nothing", async ($, on) => {
    const { clock, seen } = world(on, { toolMin: { Bash: 120 } })
    await $.session.start(SESSION)
    await $.classic.SessionStart(STARTUP)
    await $.turn.start(START)
    // The input type leaves agentId out, as a plugin's own call never names
    // one; the engine raises a subagent's calls with it set.
    const call = $.tool.call({ ...BASH, agentId: 'a1' } as typeof BASH)
    await clock.advance(120 * MIN)
    await call
    expect(seen.calls).toEqual(['a1'])
    expect(seen.forks).toHaveLength(0)
  })

  test("a subagent's turn after the stop leaves the idle refresh armed", async ($, on) => {
    const { clock, seen } = world(on)
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop(STOP)
    await $.turn.complete(COMPLETE)
    await clock.advance(10 * MIN)
    await $.turn.start({ text: 'look', turnId: 's1', agentId: 'a1' } as typeof START)
    await $.turn.complete({ ...COMPLETE, turnId: 's1', agentId: 'a1' } as typeof COMPLETE)
    await clock.advance(40 * MIN)
    expect(seen.forks).toHaveLength(1)
  })

  test('a tool call on a 5m cache is not refreshed, and says why', async ($, on) => {
    const { clock, seen } = world(on, { tail: [row('5m'), ''].join('\n'), toolMin: { AskUserQuestion: 120 } })
    await $.session.start(SESSION)
    await $.classic.SessionStart(STARTUP)
    await $.turn.start(START)
    const call = $.tool.call(ASK)
    await clock.advance(120 * MIN)
    await call
    expect(seen.forks).toHaveLength(0)
    expect(seen.logs).toEqual(['not refreshed: the newest cache write used the 5m TTL; while AskUserQuestion was pending'])
  })

  test('a tool call with no transcript path known refreshes, and says the TTL went unread', async ($, on) => {
    // A module reloaded mid-session has seen no SessionStart.
    const { clock, seen } = world(on, { toolMin: { AskUserQuestion: 120 } })
    await $.session.start(SESSION)
    await $.turn.start(START)
    const call = $.tool.call(ASK)
    await clock.advance(120 * MIN)
    await call
    expect(seen.runs).toHaveLength(0)
    expect(seen.forks).toHaveLength(1)
    expect(seen.logs).toEqual([
      'refresh 1/1: read 200000, uncached 9, written 0, output 3; while AskUserQuestion was pending; TTL unread: no SessionStart or Stop since this module loaded gave a transcript path',
    ])
    expect(seen.toasts).toHaveLength(0)
  })

  test("a Stop's transcript path serves the next turn's tool calls", async ($, on) => {
    const { clock, seen } = world(on, { toolMin: { AskUserQuestion: 120 } })
    await $.session.start(SESSION)
    await $.turn.start(START)
    await $.classic.Stop({ ...STOP, background_tasks: [] })
    await $.turn.complete(COMPLETE)
    await $.turn.start({ text: 'again', turnId: 't2' })
    const call = $.tool.call(ASK)
    await clock.advance(120 * MIN)
    await call
    expect(seen.forks).toHaveLength(1)
    expect(seen.runs).toEqual([['tail', '-c', '1000000', '/p/s.jsonl']])
  })

  test("a first turn's tool call refreshes with its TTL unread, and says so", async ($, on) => {
    // The first turn's responses are not in the transcript file while it waits.
    const { clock, seen } = world(on, { tail: '{"type":"user"}\n{"type":"attachment"}\n', toolMin: { AskUserQuestion: 120 } })
    await $.session.start(SESSION)
    await $.classic.SessionStart(STARTUP)
    await $.turn.start(START)
    const call = $.tool.call(ASK)
    await clock.advance(120 * MIN)
    await call
    expect(seen.forks).toHaveLength(1)
    expect(seen.logs).toEqual([
      "refresh 1/1: read 200000, uncached 9, written 0, output 3; while AskUserQuestion was pending; TTL unread: the transcript's last 1000000 bytes hold no main-thread response",
    ])
  })
})

# A foreground Bash call holds `claude -p`, and what a wait blocks

Measured 2026-10-01 on Claude Code **2.1.269**, haiku, `--dangerously-skip-permissions`,
`--output-format stream-json --verbose`, this repo's user `settings.json` plus a
`--settings` file per run; each run one `claude -p` process whose prompt makes one to
four tool calls and replies with a word. It tries the foreground form of
`notes/print-mode-task-lifetime.md`'s `Stop`-hook wait.

## One foreground call holds the process — B1, B2, B3

`Bash` with `until [ -f go ]; do sleep 2; done; echo RELEASED`, released by touching the file.

- **B1**, `timeout 600000`, released at 150 s: `task_started is_backgrounded:false` +6.5 s,
  `tool_progress` every 30 s, `RELEASED` as the tool result +149.6 s, one `result`
  (`turns 2`), exit 0. No model turn while waiting.
- **B2**, no `timeout`, `--settings` env `BASH_DEFAULT_TIMEOUT_MS` and `BASH_MAX_TIMEOUT_MS`
  both 86,400,000, released at 660 s: result +661.3 s, 21 `tool_progress`, exit 0. Settings
  `env` reaches the clamp and the ten-minute ceiling moves.
- **B3**, `timeout 3600000` with only `BASH_MAX_TIMEOUT_MS=86400000`, released at 150 s:
  result +149.5 s — past the 120 s default, so the explicit value applied with the default
  untouched. (A clamp to 600,000 is not excluded by this run; the release came first.)

The clamp is `Ze = Math.min(Oe || kSe(), jre(), s?.maxTimeoutMs ?? 1/0)`
(`src/chunk-dbb93264.js:216540`): `kSe` → `BASH_DEFAULT_TIMEOUT_MS` or 120,000, `jre` →
`Math.max(BASH_MAX_TIMEOUT_MS, default)` or `Math.max(600000, default)` (`:96813-96829`),
`s` → `remoteCall?.constraints`, absent locally. The schema is `v().optional()` with the max
interpolated into its description (`:215648`) and an empty `superRefine` (`:215678`). The
value arms one `setTimeout(U5e.#S, this.#d, this)` (`:28333`); at expiry `#S` backgrounds
the command when auto-backgrounding is on, else kills it with `Command timed out after …`
(`:28277-28278`, `:28360`).

## How high — C, C2

`BASH_MAX_TIMEOUT_MS` and `timeout` both 9,999,999,999 (115 days): released at 60 s, result
+61.4 s, no early fire. Both 2,147,483,647: result +59.7 s. That 32-bit bound is what JS
timers are defined for; what Bun does above it is not established, so settings use it.

## What a wait blocks — A against D

- **A**, the Stop-hook hold, with a `Monitor "sleep 45; echo TICK"` and a background
  `sleep 30; echo BG_DONE` armed before `--wait` declared: hold from +10.9 s; the background
  task `completed` +36.6 s and the monitor +50.1 s, as `task_updated` records only; the hook
  returned with the synthetic answer +101.0 s; the queued events then came as three turns —
  `GOT: Background command "bg" completed` +109.0 s, `GOT: TICK` +110.4 s, `GOT: Monitor
  "tick" stream ended` +112.5 s — and the process exited 0. The background task was not
  killed by the hold: the kill is in the shutdown sequence (`Cvt()`, `:28213`, called at
  `:246200` and `:246220`).
- **D**, a 60 s foreground wait with the same `Monitor` (`sleep 20; echo TICK`) armed
  first: `TICK` `completed` +24.6 s as a system record and in the task's output file; the
  wait's tool result +60.3 s is `RELEASED` and nothing else; the model's thinking names only
  RELEASED; one `result` (`turns 4`), exit. `TICK` is in no `user` record.

Both waits freeze the model. After the hook's block the process sat at a turn boundary and
drained the queue, one turn per event; after the foreground call the turn ended with nothing
running and the process exited, the queue undelivered. Under `-p` a listener armed beside a
foreground wait loses its events; the wait reads the human's message from the same log.

## The real artifact — F

`listen.py 9 --peek`, then `listen.py 9 --wait` with `timeout=2147483647`, under `claude -p
--model haiku` with settings `env` only — `BASH_MAX_TIMEOUT_MS=2147483647` and a scratch
`TELEGRAM_HITL_STATE_DIR` — and no hooks. `--peek` returned `channel up` in 0.1 s. `--wait`
was accepted at that timeout (`task_started`, `is_backgrounded: false`, `tool_progress` at
30 s), blocked 56 s until a synthetic inbound message was appended at +60 s, and returned
`channel up` / `message 13 in chat -100123: answer three` as the tool result, exit 0; the
model echoed it and the process exited at 62.9 s. An earlier run (E), its settings still
registering the old `stop-hook` (a `listen.py` mode then gone, so printing nothing), timed the
same.

## What this settled

`skills/telegram-hitl/listen.py <thread> --wait` blocks in the foreground and returns the
unreacted messages, under the raised `BASH_MAX_TIMEOUT_MS` (settings `env`) and the call's own
`timeout`; no `Stop` hook holds the process. Guarantees: `skills/telegram-hitl/README.md`.

# telegram-hitl: what the listener guarantees, and why

`SKILL.md` is the rules an agent reads; `listen.py` is the reader it runs. This
file is what neither can say: the properties the pair holds, the state they
keep, and the harness facts the design rests on. Measurements are dated; the
design is current.

## Requirements

| | Property | Mechanism |
| --- | --- | --- |
| R1 | **At-least-once delivery.** A human message in the session's topic, or a reply to one of its sends anywhere, is announced until some session has reacted to it. | The listener's only memory is the log: a `setMessageReaction` record naming the message — any response, since a service message answers `MESSAGE_ID_INVALID` — is the ack. Nothing the printer does advances anything: printed is not received (see the harness facts). |
| R2 | **Handoff without state.** A re-arm after expiry, a resumed session, the next iteration of a loop that starts a fresh session, and every `--wait` or `--peek` call read the same log and get only what is still unreacted. | Follows from R1. No watermark file, no cursor argument, nothing to carry between sessions or calls. |
| R3 | **A deliberate wait holds the process.** A session with nothing pending but the human blocks on the answer, and a `claude -p` process stays alive for it. | `listen.py <thread> --wait` as a foreground Bash call with `timeout=2147483647`: it polls the log and returns with the first unreacted message(s) as its output. A tool call in progress is not a turn end, so nothing else holds the process; no model turn is spent waiting; a driver sees `tool_progress` every 30 s. |
| R4 | **No accidental wait, no accidental advance.** Nothing holds a process that was not asked to wait, and a wait asked for ends only in a way the model sees. | The wait is a call, not a state: no declaration, no hook, no monitor to forget. The call returns with the answer, with `channel down` (exit 1), or — at its `timeout` — backgrounded and named as such in the tool result. Under `-p` no listener is armed (below), so a turn end leaves nothing running. |
| R5 | **Listening while working stays cheap.** An interactive session arms the plain listener at topic creation and ends every turn with it armed. | A `Monitor` costs nothing between events, and a turn end there is not a session end. Under `-p` the same listening is `--peek` at checkpoints: one pass, one tool call. |
| R6 | **One notification per message, and the channel's state on every run.** | Whitespace is collapsed to one line per message; the first pass prints `channel up` or `channel down: <cause>`. |
| R7 | **The rules fit the budget.** `SKILL.md` ≤ 1,000 local-tokenizer tokens (`doc-budget.toml`). | An addition is paid by a removal; evidence and rationale live here and in the spec, not there. |

## The wait

A `claude -p` turn end is the process end unless a tool call is still running
or a `Monitor` is armed. `--wait` is the first: one Bash call that returns
when the log has something for the session. Its ceiling is the Bash tool's
`timeout`, clamped to `Math.min(timeout || BASH_DEFAULT_TIMEOUT_MS,
max(600000, BASH_MAX_TIMEOUT_MS))` — 120 s and 10 min by default — so
`settings.json` `env` sets `BASH_MAX_TIMEOUT_MS=2147483647`, the 32-bit bound
of the one `setTimeout` the harness arms, and leaves the default at 120 s for
every other command; the skill's call passes that value, and the test pins it
under the env value. At the deadline the command is auto-backgrounded, which
under `-p` is killed at the turn end — a silent advance, which is why the
ceiling is 24.8 days rather than a day.

Nothing else is armed under `-p` while a call waits. A `Monitor` event that
fires during a foreground call is queued, and a `-p` process with nothing
running exits at the next turn end with the queue undelivered (measured
2026-10-01: a `TICK` fired 24 s into a 60 s wait never reached the model,
while the same event during a Stop-hook hold came back as a turn after the
hold). The wait reads the same log a listener would, so the human's message is
not what is lost — a correction meant for a listener is. `--peek` between
steps is the `-p` form of listening.

A loop driver that starts one `claude -p` per iteration (ralph:
`/workspace/ralph/build.yml`) sees an iteration end exactly when the process
exits: with the wait in the foreground, an iteration ends after the model has
the answer, and never on a forgotten listener, since none is armed. The
driver's inactivity timeout must exceed the wait or count `tool_progress` as
activity.

## State in `$TELEGRAM_HITL_STATE_DIR`

Nothing of the listener's: its memory is the log, and a wait is a running call.
Everything there belongs to the proxy (`src/claude_config/CLAUDE.md`).

## Harness facts the design rests on

Claude Code 2.1.269, measured 2026-10-01 unless marked; evidence and the probe
shapes in `notes/print-mode-task-lifetime.md` and
`notes/foreground-wait-under-print-mode.md`.

- A Bash `run_in_background` task is **killed** when a `-p` turn ends
  (`task_updated status: killed`), in the shutdown sequence. A background wait
  cannot hold an iteration.
- A foreground Bash call **holds** a `-p` process until it returns — 150 s and
  661 s measured, zero model turns, `tool_progress` every 30 s — bounded only
  by its `timeout`.
- The `timeout` is clamped to `Math.min(timeout || BASH_DEFAULT_TIMEOUT_MS,
  max(600000, BASH_MAX_TIMEOUT_MS), remote constraints)`
  (`src/chunk-dbb93264.js:216540`, `:96813-96829`); the schema caps nothing
  (`:215648`); settings `env` reaches it (661 s through the default, 150 s
  through an explicit 3,600,000 with only the max raised). One `setTimeout`
  carries the value (`:28333`): 2,147,483,647 ran, and 9,999,999,999 did not
  fire early in 61 s — the 32-bit bound is the one to trust. At the deadline the
  command is backgrounded when allowed, else killed as `Command timed out
  after …` (`:28277-28278`, `:28360`).
- A `Monitor` **holds** a `-p` process: each event and the completion re-invoke
  the model, one `result` per turn on `stream-json`; `timeout_ms` is clamped to
  10 minutes under `-p` (30 interactive) behind the server flag
  `tengu_breezy_crescent` (`src/chunk-r2x48y8w.js:22-46`), so unattended
  listening costs a re-arm turn per ten minutes and a listener nobody re-arms
  exits the process.
- Notifications queued while a tool call runs are delivered only if the process
  is still alive at the next turn boundary; under `-p` with nothing running,
  they are dropped.
- A `Stop` hook holds a process for as long as it runs (its `timeout` has no
  maximum; SIGKILL at the deadline reads as no decision) and can block a turn
  end up to `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` consecutive times (default 8).
  The wait that used this, and why it was replaced the same day, is in the
  notes.
- Monitor stdout handling (read in the decompile, not measured): lines batch
  within 200 ms, a line is cut at 500 characters and a batch at 3,000, more
  than 10 events in 2 s are suppressed, pending events flush before the expiry
  kill. This is why printed is not received.

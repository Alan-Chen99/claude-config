# telegram-hitl: what the listener guarantees, and why

`SKILL.md` is the rules an agent reads; `listen.py` is the reader it arms. This
file is what neither can say: the properties the pair holds, the state they
keep, and the harness facts the design rests on. Measurements are dated; the
design is current.

## Requirements

| | Property | Mechanism |
| --- | --- | --- |
| R1 | **At-least-once delivery.** A human message in the session's topic, or a reply to one of its sends anywhere, is announced until some session has reacted to it. | The listener's only memory is the log: a `setMessageReaction` record naming the message — any response, since a service message answers `MESSAGE_ID_INVALID` — is the ack. Nothing the printer does advances anything: printed is not received (see the harness facts). |
| R2 | **Handoff without state.** A re-arm after expiry, a resumed session, and the next iteration of a loop that starts a fresh session all arm the same command and get only what is still unreacted. | Follows from R1. No watermark file, no cursor argument, nothing to carry between sessions. |
| R3 | **A deliberate wait holds the process.** A session can end its turn with nothing pending but the human, and a `claude -p` process stays alive for it. | `listen.py <thread> --wait` declares the wait and returns; the `Stop` hook then does the waiting — polls the log, and blocks the stop with the human's message as its reason. Nothing runs meanwhile, no monitor is re-armed, and the model's cooperation is not needed to stay. |
| R4 | **No accidental wait, no accidental advance.** Ending with a listener armed is a declared wait or a mistake; a declared wait whose listener expired un-re-armed is not an exit. | `listen.py stop-hook` (unattended sessions only): a forgotten listener is named once; a declared wait is held by the hook itself until the answer arrives or the session withdraws it with `stop-waiting`. Matrix below. |
| R5 | **Listening while working stays cheap.** An interactive session arms the plain listener at topic creation and ends every turn with it armed. | The hook is inert when `CLAUDE_CODE_SESSION_ATTENDED` is not `0`; a turn end there is not a session end. |
| R6 | **One notification per message, and the channel's state on every arm.** | Whitespace is collapsed to one line per message; the first pass prints `channel up` or `channel down: <cause>`. |
| R7 | **The rules fit the budget.** `SKILL.md` ≤ 1,000 local-tokenizer tokens (`doc-budget.toml`). | An addition is paid by a removal; evidence and rationale live here and in the spec, not there. |

## The stop guard

Read off the `Stop` payload's `background_tasks` (each task's `command` as
Claude Code rewrote it; `listen.py <thread>` survives the wrapping) and the
declaration file below. Unattended sessions only. A declaration makes the hook
the waiter: it returns only with the answer (declaration withdrawn), with a
channel still down after ten minutes, or just inside its own 23-hour `HOLD`
(both: declaration kept, so the next turn end resumes the wait) — Claude Code
kills a hook at its settings `timeout` (24 h here) and reads the kill as no
decision, which would exit the process. Ending again is never a way out: it is
what a model does when it has no better idea (measured 2026-10-01 — a `-p`
session told once to re-arm replied "waiting for your instructions", ended,
and the loop advanced). Each block the hook returns counts as one consecutive
block against `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, default 8, after which Claude
Code overrides the hook and ends the turn, silently to a driver; `settings.json`
sets it to 1000, unreachable here since a block costs a human answer or 23
hours.

| Wait declared | Listener armed | Decision |
| --- | --- | --- |
| no | no | allow |
| yes | — | the hook waits, then blocks: with the answer, with a dead channel, or to renew its hold |
| no | yes | block once: `TaskStop` it to end, or `--wait` to stay |

A loop driver that starts one `claude -p` per iteration (ralph:
`/workspace/ralph/build.yml`) sees an iteration end exactly when the process
exits, so the once-block is what keeps an iteration from hanging on a
forgotten listener and the hook's hold is what keeps it from advancing past a
human who was asked to answer. The driver's inactivity timeout must exceed the
wait; the wait itself spends no model turn, one block per answer.

## State in `$TELEGRAM_HITL_STATE_DIR`

| Path | Written by | Meaning |
| --- | --- | --- |
| `waits/<session id>` | `listen.py --wait` (the thread); removed by the stop hook when it delivers, or by `listen.py stop-waiting` | The session declared a wait on the topic named inside. A process killed outright (driver timeout, a reaper) leaves it behind, and only that session's own stop hook reads it — inert for every other session, and a resume of that session is held to it. |

Everything else there belongs to the proxy (`src/claude_config/CLAUDE.md`).

## Harness facts the design rests on

Claude Code 2.1.269, measured 2026-10-01 unless marked; evidence and the probe
scripts' shape are in `notes/print-mode-task-lifetime.md`.

- A Bash `run_in_background` task is **killed** when a `-p` turn ends
  (`task_updated status: killed`). A background wait cannot hold an iteration.
- A `Monitor` **holds** a `-p` process: each event and the completion
  re-invoke the model, and the process exits after the turn that follows the
  monitor's end. `--output-format json` prints one result at exit;
  `stream-json` prints one per turn.
- Every monitor expires: `timeout_ms` is clamped to 30 minutes, and to **10
  minutes under `-p`** — `Math.min(timeout_ms, 600000)` when the session is a
  single-shot print session, behind the server-resolved flag
  `tengu_breezy_crescent` (`src/chunk-r2x48y8w.js:22-46`); measured as three
  expiries 600 s apart, lifetime not idle. An expiry nobody re-arms exits a
  `-p` process, so an unattended wait costs one re-arm turn per ten minutes.
- The `Stop` payload carries `background_tasks[]` (`id`, `status`,
  `description`, `command`), `stop_hook_active`, `last_assistant_message`,
  `session_id`; the hook's environment has `CLAUDE_CODE_SESSION_ATTENDED=0`
  and `CLAUDE_CODE_ENTRYPOINT=sdk-cli` under `-p`, under a PTY as well.
- A `Stop` hook printing `{"decision": "block", "reason": …}` re-invokes the
  model with `Stop hook feedback: <reason>`; `stop_hook_active` on the next
  stop is advisory — a block is honoured at every stop, up to
  `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` consecutive blocks (default 8,
  `src/chunk-dbb93264.js:154114`), after which the turn ends with a warning
  `stream-json` does not carry. Settings `env` reaches the check (probed with
  a cap of 2).
- A command hook's `timeout` is any positive number of seconds — no maximum
  (`src/chunk-3vd4nzwp.js:3135`); `Stop` defaults to 120. At the deadline the
  hook is SIGKILLed and the result reads as no decision: the stop proceeds
  (`src/chunk-4qwmcbkw.js:171-184`). Stdout is parsed at exit. The process is
  held for as long as the hook runs.
- Monitor stdout handling (read in the decompile, not measured): lines batch
  within 200 ms, a line is cut at 500 characters and a batch at 3,000, more
  than 10 events in 2 s are suppressed, and pending events are flushed before
  the expiry kill. This is why printed is not received.
- Events and expiry notices re-invoke a session that has ended its turn
  (measured 2026-09-26).

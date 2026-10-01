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
| R3 | **A deliberate wait holds the process.** A session can end its turn with nothing pending but the human, and a `claude -p` process stays alive for it. | `listen.py <thread> --wait` under `Monitor`: exits 0 after the first pass that delivered, 1 on `channel down`; the monitor is the only harness task that keeps `-p` alive. |
| R4 | **No accidental wait, no accidental advance.** Ending with a listener armed is a declared wait or a mistake; a declared wait whose listener expired un-re-armed is not an exit. | `listen.py stop-hook` (a `Stop` hook, unattended sessions only): a forgotten listener is named once; a declared wait is held at every stop until the session re-arms it or withdraws it with `stop-waiting`. Matrix below. |
| R5 | **Listening while working stays cheap.** An interactive session arms the plain listener at topic creation and ends every turn with it armed. | The hook is inert when `CLAUDE_CODE_SESSION_ATTENDED` is not `0`; a turn end there is not a session end. |
| R6 | **One notification per message, and the channel's state on every arm.** | Whitespace is collapsed to one line per message; the first pass prints `channel up` or `channel down: <cause>`. |
| R7 | **The rules fit the budget.** `SKILL.md` ≤ 1,000 local-tokenizer tokens (`doc-budget.toml`). | An addition is paid by a removal; evidence and rationale live here and in the spec, not there. |

## The stop guard

Read off the `Stop` payload's `background_tasks` (each task's `command` as
Claude Code rewrote it; `listen.py <thread>` survives the wrapping) and the
declaration file below. Unattended sessions only. Ending again is not a way
out of a declared wait: it is what a model does when it has no better idea
(measured 2026-10-01 — a `-p` session told once replied "waiting for your
instructions", ended, and the loop advanced), so that row holds at every stop,
`stop_hook_active` or not; Claude Code re-invokes the model on every block.
The hold is rate-limited — the hook sleeps before each nudge after the first,
1 s doubling to 30 s, under the hook's 60 s `timeout` in `settings.json` — and
the third nudge posts a warning in the topic, a push, since the loop is the
human's to fix from there.

| Wait declared | `--wait` listener armed | Other listener armed | Decision |
| --- | --- | --- | --- |
| no | no | no | allow |
| yes | yes | — | allow: the deliberate wait; the monitor holds the process |
| no | — | yes | block once: `TaskStop` it to end, or arm `--wait` to stay |
| yes | no | — | block, every stop: re-arm `--wait`, or `stop-waiting` then end; nudge *n* sleeps min(30, 2^(n−2)) s first, the third also warns the topic |

A loop driver that starts one `claude -p` per iteration (ralph:
`/workspace/ralph/build.yml`) sees an iteration end exactly when the process
exits, so the first block is what keeps an iteration from hanging on a
forgotten listener and the second is what keeps it from advancing past a human
who was asked to answer. The driver's inactivity timeout must exceed the wait,
which under `-p` costs one re-arm turn every ten minutes; an iteration whose
model never acts on a nudge is held at two turns a minute, and the warned
topic is where the human learns of it.

## State in `$TELEGRAM_HITL_STATE_DIR`

| Path | Written by | Meaning |
| --- | --- | --- |
| `waits/<session id>` | `listen.py --wait` at start (the thread; the stop hook appends its nudge count); removed when the listener exits on its own, or by `listen.py stop-waiting` | The session declared a wait on the topic named on its first line. Survives a SIGTERM (expiry, `TaskStop`) on purpose; a process killed outright (driver timeout, a reaper) leaves it behind, and only that session's own stop hook reads it — inert for every other session, and a resume of that session is held to it. |

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
  model with `Stop hook feedback: <reason>` and sets `stop_hook_active` on the
  next stop.
- Monitor stdout handling (read in the decompile, not measured): lines batch
  within 200 ms, a line is cut at 500 characters and a batch at 3,000, more
  than 10 events in 2 s are suppressed, and pending events are flushed before
  the expiry kill. This is why printed is not received.
- Events and expiry notices re-invoke a session that has ended its turn
  (measured 2026-09-26).

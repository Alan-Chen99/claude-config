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
ceiling is 24.8 days rather than a day. A command that reaches the background
by any route runs there under a second deadline — 30 minutes by default, at
most `max(2 h, BASH_MAX_TIMEOUT_MS)` — which the same env value raises to the
same 24.8 days, and which applies only to an unattended session.

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

Measured 2026-10-01 on Claude Code 2.1.269 unless marked; source read in
**2.1.289**; evidence and the probe shapes in
`notes/print-mode-task-lifetime.md` and
`notes/foreground-wait-under-print-mode.md`.

- A Bash `run_in_background` task is **killed** when a `-p` turn ends
  (`task_updated status: killed`), in the wind-down that runs once input is
  closed and nothing is queued (`src/chunk-mgxpmmsq.js:1911`, `:1935`). A
  background wait cannot hold an iteration.
- A foreground Bash call **holds** a `-p` process until it returns — 150 s and
  661 s measured, zero model turns, `tool_progress` every 30 s — bounded only
  by its `timeout`. The wind-down runs between turns, so it never sees one.
- The `timeout` is clamped to `Math.min(timeout || BASH_DEFAULT_TIMEOUT_MS,
  run_in_background ? max(2 h, BASH_MAX_TIMEOUT_MS) : max(600000,
  BASH_MAX_TIMEOUT_MS), a served call's wall cap, remote constraints)`
  (`src/chunk-wgfrtm7w.js:163560`, readers at `src/chunk-t5fdy639.js:606-628`);
  the schema coerces a numeric string and caps nothing
  (`src/chunk-wgfrtm7w.js:162601`); settings `env` reaches it (661 s through the
  default, 150 s through an explicit 3,600,000 with only the max raised). One
  `setTimeout` carries the value (`src/chunk-wgfrtm7w.js:3489`): 2,147,483,647
  ran, and 9,999,999,999 did not fire early in 61 s — the 32-bit bound is the
  one to trust. At the deadline the command is backgrounded when allowed, else
  killed as `Command timed out after …` (`src/chunk-wgfrtm7w.js:3434`, `:3517`).
- A command running **in** the background has a deadline of its own,
  `Math.min(timeout ?? max(30 min, BASH_DEFAULT_TIMEOUT_MS), max(2 h,
  BASH_MAX_TIMEOUT_MS))` capped at 2³¹−1, after which it is stopped with
  `stopped after reaching its background time limit`
  (`src/chunk-gppff98a.js:36004-36008`, armed at
  `src/chunk-wgfrtm7w.js:159823-159824`). It is armed only in an **unattended**
  session — non-interactive and neither a desktop nor a VS Code entrypoint
  (`src/chunk-17315fks.js:271`) — so it is exactly the `-p` case, and the
  settings `env` value raises it to the same 24.8 days. An auto-backgrounded
  call gets the 30-minute default instead of its own `timeout`
  (`src/chunk-wgfrtm7w.js:37899`).
- A `Monitor` **holds** a `-p` process: each event and the completion re-invoke
  the model, one `result` per turn on `stream-json`; `timeout_ms` defaults to
  5 minutes, is refused above 1 hour, and is capped at 10 minutes under `-p`
  (30 otherwise) — the server flag `tengu_breezy_crescent` defaults to on and
  a diskless session forces it, so the cap and the re-arm notice are the
  behaviour to plan for and the `persistent` option is absent from the schema
  (`src/chunk-5g752enf.js:23-29`, `src/chunk-93mkz49v.js:402`, `:446`). So
  unattended listening costs a re-arm turn per ten minutes and a listener
  nobody re-arms exits the process.
- The hold is itself bounded: once `-p` input is closed and nothing is queued,
  a session with only background tasks and armed monitors left is terminated
  after `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`, default 600,000 ms, with
  `Background tasks still running after Ns; terminating.` on stderr
  (`src/chunk-mgxpmmsq.js:1874`, `:2033`; `0` waits indefinitely).
- Notifications queued while a tool call runs are delivered only if the process
  is still alive at the next turn boundary; under `-p` with nothing running,
  they are dropped — the queue is in memory, and no teardown path delivers it.
- A `Stop` hook holds a process for as long as it runs (its `timeout` has no
  maximum; SIGKILL at the deadline reads as no decision) and can block a turn
  end up to `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` consecutive times (default 8).
  The wait that used this, and why it was replaced the same day, is in the
  notes.
- Monitor stdout handling (read in the decompile, not measured): lines batch
  within 200 ms, a line is cut at 500 characters and a batch at 3,000
  (`src/chunk-6mbr5tgm.js:538-541`); a token bucket of 10 refilling one per 2 s
  suppresses the rest (`src/chunk-jzxf7dqr.js:11-12`) and 30 s of unbroken
  suppression stops the monitor outright (`src/chunk-6mbr5tgm.js:481-494`);
  pending events flush before the expiry kill
  (`src/chunk-93mkz49v.js:532-538`); and a script's last events are merged into
  the body of its exit notice rather than sent as one of their own
  (`src/chunk-6mbr5tgm.js:510-526`). This is why printed is not received.
- The memory-pressure reaper cannot touch a `-p` wait: it is registered only
  for a background shell of an **interactive** session, and then only fires at
  critical pressure with the session 30 minutes idle, no turn running and no
  delegated agent (`src/chunk-wgfrtm7w.js:159827-159845`,
  `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP` turns it off).
- A `-p` session's tool subprocesses see `CLAUDE_CODE_SESSION_ATTENDED=0` and
  `CLAUDE_CODE_ENTRYPOINT=sdk-cli`, against `1` and `cli` interactive — the
  `-p` test `SKILL.md` names. Measured 2026-10-01 for a `Stop` hook (the first
  note) and for a Bash call: `echo $CLAUDE_CODE_SESSION_ATTENDED` under
  `claude -p --model haiku` printed `0`, and `1` in the interactive session
  that launched it. The variable is written from a separate predicate
  (`src/chunk-gppff98a.js:14650`, `src/chunk-17315fks.js:238`) from the one the
  background deadline reads, and the two agree only by coincidence under `-p`:
  the flag is a sound `-p` test for the skill, not a reading of that deadline.

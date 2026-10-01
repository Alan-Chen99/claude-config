# What outlives a turn under `claude -p`

Measured 2026-10-01 on Claude Code **2.1.269**, haiku, `--dangerously-skip-permissions`,
this repo's user `settings.json` (so `agent-tools hook-pre` wrapped every command).
Four runs, each one `claude -p` process with a prompt that starts one task and then
replies with a single word. Why it mattered: `skills/telegram-hitl` waits hours for a
human, and a loop driver (ralph) starts one `-p` process per iteration and advances when
it exits — so "which task keeps the process alive" decides whether the wait is possible
at all, and a loop had advanced when it was supposed to wait.

## Bash `run_in_background` — killed with the turn

`--output-format stream-json --verbose`; the command was `sleep 45; echo SLEPT`.

- `result` record at 6,152 ms; process exit 12 s after start.
- After the result: `task_updated {status: "killed"}`, then
  `task_notification {status: "stopped"}` for the task. The output file never
  received `SLEPT`.

A background Bash task cannot hold a `-p` session, whatever the long-bash skill says
about interactive ones; the kill is the harness's, at turn end.

## Monitor — holds the process, one turn per event

Same flags; `Monitor(command="sleep 45; echo EVENT; sleep 3", timeout_ms=120000)`.

- First `result` ("STARTED", `num_turns: 3`) at 5 s; the process stayed up.
- At 45 s the event re-invoked the model: a new `init`, an assistant turn
  "Event received: EVENT", a second `result`.
- At 48 s the monitor's completion re-invoked it again: "Monitor completed.",
  a third `result`; exit at 54 s.

So `stream-json` carries **one `result` per turn** and the process ends only after the
turn that follows the monitor's end. The repo already recorded the half of this that
bites prompt tests: `scripts/prompt-test-cc.sh:126`, "2.1.257 made `claude -p` wait for
an armed Monitor".

## `--output-format json` — one object, at exit

Same monitor shape (`sleep 20; echo EVENT; sleep 3`), `--output-format json`:
stdout was **one** top-level JSON object (`num_turns: 1`, the last turn's result),
printed at exit after 30 s. A driver parsing `json` sees nothing until the
monitor ends; a driver parsing `stream-json` sees a result per turn and must
not treat the first as the end.

## What a `Stop` hook sees

A `Stop` hook was added through `--settings` that dumped its stdin and environment.
It fired once per turn (three times in the monitor run). Payload keys: `session_id`,
`transcript_path`, `cwd`, `prompt_id`, `permission_mode`, `hook_event_name`,
`stop_hook_active`, `last_assistant_message`, **`background_tasks`** (each with `id`,
`type: "shell"`, `status: "running"`, `description`, `command` — the command as
rewritten by `hook-pre`, `unset …; export AGENT_TOOLS_PARENT_DIR=…;` included),
`session_crons`. A finished task is absent from the list, not marked.

Environment: `CLAUDE_CODE_SESSION_ATTENDED=0` and `CLAUDE_CODE_ENTRYPOINT=sdk-cli`,
against `1` and `cli` in an interactive session. A fourth run under `script -qec`
(a PTY, as ralph provides one) reported the same `0` / `sdk-cli`: the values follow
`-p`, not the terminal.

A hook printing `{"decision": "block", "reason": "…"}` re-invoked the model with a
user message `Stop hook feedback:\n<reason>`; the next stop's payload carried
`stop_hook_active: true`. Exit 0, stdout JSON — no exit-2 path was needed.

## Monitor under `-p`: ten minutes, not thirty

Measured in the deliberate-wait run (same flags, a `--settings` Stop hook, a prompt arming
`listen.py 66 --wait` with `timeout_ms: 1800000`): three monitors expired at 17:11:12,
17:21:17 and 17:31:20 EDT — 600 s after each arm — each delivering `[Monitor expired
after 10m with 1 event delivered. Re-arm it if you still need the watch.]`. The
interactive session's listener, armed the same way, ran past eleven minutes. In the
decompile, `nmr()` returns `Math.min(timeout_ms, Uye())` under the flag
`tengu_breezy_crescent`, and `Uye()` is 600000 when `Ave()` —
`launchOptions.singleShotPrintSession()` — and 1800000 otherwise
(`src/chunk-r2x48y8w.js:18-46`, `src/chunk-g85a3dc1.js:4414`); the deadline is the
monitor's lifetime, not an idle timer. The tool's own `timeout_ms` description moves with
it: "Deadlines above 600000ms are capped to 600000ms" (`src/chunk-ffj047jw.js:397`). The
flag is server-resolved, so the measurement, not the build, is the evidence.

The same run exercised the guard: the first expiry's turn ended without a re-arm and the
Stop hook blocked once (`this session declared a wait on topic 66 and its listener is
gone`); the model re-armed, and at the next two expiries re-armed inside the expiry turn.
Each re-arm's `channel up` turn ended with a declared wait and a `--wait` listener armed —
allowed.

## What killed the probe: the memory-pressure reaper

The run was a background Bash task of an interactive session and was killed at 30 m 39 s
(exit 143) with `stopped because the system is running low on memory`. `R0r`
(`src/chunk-dbb93264.js:213002-213012`) registers a `memoryPressure` listener for every
background shell of an interactive session (`!ke()`, unless
`CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP` is set) that kills the task when it is still
running and unreported, the user's last interaction (`nm()`,
`userPresence.lastInteractionTime()`) is 30 minutes old (`XWs`), the main loop is idle
and no agent task is active (`xM`). The host had 14 of 20 GB of swap in use. The re-run
was detached with `agent-tools run --background`, which the task registry never sees. The
`waits/<session id>` declaration the killed `-p` session left behind was removed by hand;
the README's state table names the case.

## What this settled

`skills/telegram-hitl/listen.py --wait` runs under `Monitor` because nothing else holds
a `-p` process; its `stop-hook` reads `background_tasks[].command` for `listen.py`
and `--wait`, acts only when `CLAUDE_CODE_SESSION_ATTENDED=0`, and blocks at most once
per stop (the `stop_hook_active` stop always passes). `skills/telegram-hitl/README.md`
has the resulting matrix; `docs/subagent-backgrounding.md` carries the one-table
summary.

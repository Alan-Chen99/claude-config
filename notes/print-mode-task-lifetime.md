# What outlives a turn under `claude -p`

Measured 2026-10-01 on Claude Code **2.1.269**, haiku, `--dangerously-skip-permissions`,
this repo's user `settings.json` (so `agent-tools hook-pre` wrapped every command).
Four runs, each one `claude -p` process with a prompt that starts one task and then
replies with a single word. Why it mattered: `skills/telegram-hitl` waits hours for a
human inside a `-p` process that a loop driver (ralph) advances past when it exits.

## Bash `run_in_background` — killed with the turn

`--output-format stream-json --verbose`; the command was `sleep 45; echo SLEPT`.

- `result` record at 6,152 ms; process exit 12 s after start.
- After the result: `task_updated {status: "killed"}`, then
  `task_notification {status: "stopped"}` for the task. The output file never
  received `SLEPT`.

## Monitor — holds the process, one turn per event

Same flags; `Monitor(command="sleep 45; echo EVENT; sleep 3", timeout_ms=120000)`.

- First `result` ("STARTED", `num_turns: 3`) at 5 s; the process stayed up.
- At 45 s the event re-invoked the model: a new `init`, an assistant turn
  "Event received: EVENT", a second `result`.
- At 48 s the monitor's completion re-invoked it again: "Monitor completed.",
  a third `result`; exit at 54 s.

So `stream-json` carries **one `result` per turn**, and the process ends only after the
turn that follows the monitor's end: a driver must not take the first as the end.

## `--output-format json` — one object, at exit

Same monitor shape (`sleep 20; echo EVENT; sleep 3`), `--output-format json`:
stdout was **one** top-level JSON object (`num_turns: 1`, the last turn's result),
printed at exit after 30 s.

## What a `Stop` hook sees

A `--settings` `Stop` hook dumping its stdin and environment fired once per turn (three
times in the monitor run). Payload keys: `session_id`, `transcript_path`, `cwd`,
`prompt_id`, `permission_mode`, `hook_event_name`, `stop_hook_active`,
`last_assistant_message`, **`background_tasks`** (each with `id`, `type: "shell"`,
`status: "running"`, `description`, `command` as rewritten by `hook-pre`), `session_crons`. A finished task is absent from the list, not marked.

Environment: `CLAUDE_CODE_SESSION_ATTENDED=0` and `CLAUDE_CODE_ENTRYPOINT=sdk-cli`,
against `1` and `cli` in an interactive session. A fourth run under `script -qec`
(a PTY, as ralph provides) reported the same: the values follow `-p`, not the terminal.

A hook printing `{"decision": "block", "reason": "…"}` re-invoked the model with a
user message `Stop hook feedback:\n<reason>`; the next stop's payload carried
`stop_hook_active: true`.

## Monitor under `-p`: ten minutes, not thirty

Measured in the deliberate-wait run (same flags, a `--settings` Stop hook, a prompt arming
`listen.py 66 --wait` with `timeout_ms: 1800000`): three monitors expired at 17:11:12,
17:21:17 and 17:31:20 EDT, 600 s after each arm, each delivering `[Monitor expired after
10m …]`. The interactive session's listener, armed the same way, ran past eleven minutes.
In the decompile, `nmr()` returns `Math.min(timeout_ms, Uye())` under the flag
`tengu_breezy_crescent`, and `Uye()` is 600000 when `Ave()` —
`launchOptions.singleShotPrintSession()` — and 1800000 otherwise
(`src/chunk-r2x48y8w.js:18-46`, `src/chunk-g85a3dc1.js:4414`); the deadline is the
monitor's lifetime, not an idle timer. The flag is server-resolved, so the measurement, not
the build, is the evidence.

## Ending again is not a decision

The guard at first blocked a declared-wait stop once and let the second through as the session's
answer. Of two runs of one prompt, the first re-armed after the block; the second replied
"The monitor has expired after 10 minutes. Waiting for your instructions on whether to
re-arm it or proceed", ended again, and the process exited 0 — the accidental advance the
guard existed to prevent, despite the prompt's "never call any other tool". Ending the turn
is what a model does by default, so it cannot carry the meaning "stop waiting". A hook
blocking three times in a row (`probe-p/reblock.py`) drew a re-invocation per block — four
stops, four turns, `stop_hook_active: true` from the second on. A hold built as a chain of
such nudges (1 s doubling to 30 s) ended at its ninth block: consecutive Stop-hook blocks
are capped at `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP ?? 8` (`src/chunk-dbb93264.js:154114`), and
the turn then ends with a warning `stream-json` does not carry — a silent exit, declaration
still on disk. Settings `env` reaches the check: a cap of 2 let two blocks through.

## The hook is the wait

With a wait declared, `listen.py stop-hook` polled the log and returned only with the answer
as its block reason. A command hook's `timeout` has no maximum
(`src/chunk-3vd4nzwp.js:3135`; `Stop` defaults to 120 s, `src/chunk-dbb93264.js:49015-49026`)
and its deadline is a SIGKILL read as no decision (`src/chunk-4qwmcbkw.js:171-184`, `:307`),
so `settings.json` gave it 24 h, the hook returning inside 23 to be resumed, and raised the
cap to 1000, each answer being one consecutive block. Measured: a `-p` session that ran
`--wait` and ended was held by its hook child for nine minutes with no turn spent; the
human's reply, logged at 18:47:20, came back as the block reason, the model answered it and
the process exited 0 at 18:47:23 with the declaration withdrawn.

## What killed the probe: the memory-pressure reaper

The run was a background Bash task of an interactive session and was killed at 30 m 39 s
(exit 143) with `stopped because the system is running low on memory`. `R0r`
(`src/chunk-dbb93264.js:213002-213012`) registers a `memoryPressure` listener for every
background shell of an interactive session (`!ke()`, unless
`CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP` is set) that kills the task when it is still
running and unreported, the user's last interaction is 30 minutes old (`XWs`), the main
loop is idle and no agent task is active. The re-run was detached with
`agent-tools run --background`.

## What this settled

The `stop-hook` acted only when `CLAUDE_CODE_SESSION_ATTENDED=0`, and with no wait declared
named a forgotten `listen.py` in `background_tasks[].command` once. Superseded the same day:
the foreground wait, `notes/foreground-wait-under-print-mode.md`; `listen.py` has no
`stop-hook` mode.

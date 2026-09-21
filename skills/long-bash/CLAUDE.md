# long-bash/

Protocol for a bash command that may outrun the Bash tool's timeout. Autoloads on its
`description`, so length is a direct cost — every line has to be reachable from one of
the four steps.

## Files

| File       | What                            | When to read                         |
| ---------- | ------------------------------- | ------------------------------------ |
| `SKILL.md` | The four-step protocol          | Editing the protocol                 |

## Measured 2026-09-21 against Claude Code 2.1.269

- A foreground command that outruns its `timeout` is auto-backgrounded, **including one
  whose first statement is `sleep`**. Upstream `yzs` (`chunk-dbb93264.js:215729`, gating
  the `onTimeout` handler at `:216563`) refuses to background a command whose first
  statement's first word is in `pzs = ["sleep"]` — but `agent-tools`'s own PreToolUse
  hook prepends `unset …; export AGENT_TOOLS_PARENT_DIR=…;` to every Bash command
  (`agent-tools/src/hook_pre.rs:50`), so the first statement is never `sleep` here and
  the guard cannot fire. The foreground `sleep ≥ 25 s` block still fires because it runs
  in `validateInput`, before the rewrite.
- Nothing a command printed is lost at a timeout. The tool result's stdout/stderr are
  empty strings, and the task's output file holds every byte, before and after the cap.
- `agent-tools run` execs; it is not a shell. `agent-tools run --desc x 'echo a && echo b'`
  exits 2 with `spawn [...]: No such file or directory`.
- A subagent is never re-invoked by a task notification. Its launch message differs from
  the main agent's and says so.
- `ps` records carry `elapsed_s` while live and `ran_s` once settled, never both.

## Cut deliberately — do not re-add without a step that reaches it

- Per-line output timestamps (`ts`, `CARGO_LOG_TIMESTAMP`, a `date` wrapper loop) and a
  parallel `date` call at launch. `agent-tools ps` reports `now`, `started_at` and
  `last_byte_s`, which is the whole need.
- The `bash -c 'echo started; cmd; echo exit=$?'` output wrapper. The wrapper records
  the exit code, and the task's output file ends with `[exited with code N]`.
- A `sleep 1` + read-the-file check right after launch. A command that dies on startup
  exits fast, and the completion notification arrives just as fast.
- The 5 GB output cap and its `[output truncated: exceeded 5GB disk cap]` marker; the
  `b`+8-char task-id format; the foreground `sleep` threshold beyond the one clause
  Step 2 needs. All true, none reachable from a step.
- A pointer to Monitor. Monitor takes no file path, requires `description` and
  `timeout_ms`, expires after 30 minutes, and its own description argues against the
  `tail -f` shape this would need.

# agent-tools wrap-task / run — Design

Status: draft
Date: 2026-05-17
Source spec: `plans/agent-tools-run-spec.md`

## Purpose

Recover stdout/stderr that Claude Code's Bash and Monitor tools throw away when commands
contain truncating pipes (`| tail`, `| grep`, `| jq .field`, `| wc -l`). Capture happens
inside the shell command itself, between pipe segments, so that the upstream work — which
may be slow, costly, or have side effects — is never re-run to recover its output.

Two entry points:

- **`agent-tools wrap-task`** — internal. A PreToolUse hook rewrites every `Bash` and
  `Monitor` tool call to invoke `wrap-task` around the original command.
- **`agent-tools run`** — agent-facing. The agent inserts it explicitly inside pipelines:
  `find … | agent-tools run -- xargs wc -l | tail -3`.

Both write durable, untruncated capture to disk; `agent-tools ps` reports what's there;
the agent reads content with its existing `Read` tool.

## Identifiers and state layout

All identifiers come from Claude Code where possible; nothing is generated when an existing
id will do.

| Field | Source |
|---|---|
| `session_id` | hook input `session_id` |
| `agent_id` | hook input `agent_id` (present only inside a subagent worker) |
| `task_id` | hook input `tool_use_id` (unique per Bash/Monitor invocation) |
| `child_id` | pid of the `agent-tools run` process |

Empirically verified via decompiled Claude Code 2.1.143 schema (`OM` base hook input)
and a subagent session log
(`/root/.claude/projects/-home-alan-repos-emacs/.../subagents/...jsonl`): `session_id`
is shared between the main thread and its subagents; `agent_id` distinguishes the subagent.

State directory:

```
~/.claude/agent-tools/
  <session_id>/
    <task_id>/                     # main-thread tasks; meta.json marks it as a task dir
      meta.json
      command.sh
      stdout
      stderr
      events.jsonl
      children/
        <pid>/
          meta.json
          stdout
          stderr
          events.jsonl
    <agent_id>/                    # subagent tasks; no meta.json at this level
      <task_id>/
        ... same shape as above
```

`ps` distinguishes a task dir from an agent dir by the presence of `meta.json`.

The one env var propagated to descendants is `AGENT_TOOLS_TASK_ID`, set to the absolute
path of `<task_dir>`. Storing the path (not just the id) means `run` and `ps` don't
have to walk `~/.claude/agent-tools/` to locate the session and agent.

## File formats

### `meta.json` (task)

```json
{
  "kind": "task",
  "session_id": "93d9406c-...",
  "agent_id": "acompact-3f915f30727b4dc1",
  "task_id": "toolu_01ABC...",
  "tool": "Bash",
  "tool_use_id": "toolu_01ABC...",
  "desc": "Run unit tests",
  "cwd": "/root/claude-config-work",
  "pid": 12345,
  "started_at": "2026-05-17T10:32:11.482Z",
  "ended_at": "2026-05-17T10:32:18.901Z",
  "exit_code": 0,
  "silence_threshold_ms": 30000
}
```

`agent_id` is `null` when the hook input lacks it. `ended_at` and `exit_code` are
absent while the task is running; written atomically once on exit.

### `meta.json` (child, under `children/<pid>/`)

```json
{
  "kind": "child",
  "parent_task_dir": "/root/.claude/agent-tools/<session_id>/<task_id>",
  "child_id": 12399,
  "desc": "xargs wc -l",
  "command": ["xargs", "wc", "-l"],
  "started_at": "...",
  "ended_at": "...",
  "exit_code": 0
}
```

### `command.sh`

The original `tool_input.command` string, written verbatim. The hook does not escape it.
`wrap-task` spawns `bash` with this file as its source so the original bytes — including
embedded quotes, `$`, heredocs, newlines — reach bash exactly as the agent wrote them.

### `stdout`, `stderr`

Raw bytes verbatim. No ANSI stripping, no truncation, no rotation.

### `events.jsonl`

Append-only. One JSON object per line:

```json
{"ts":"2026-05-17T10:32:11.482Z","kind":"task_started","data":{"pid":12345}}
{"ts":"2026-05-17T10:32:11.617Z","kind":"first_byte","data":{"stream":"stdout"}}
{"ts":"2026-05-17T10:32:42.001Z","kind":"silence","data":{"stream":"stdout","since_ms":30384}}
{"ts":"2026-05-17T10:32:55.117Z","kind":"silence_break","data":{"stream":"stdout"}}
{"ts":"2026-05-17T10:33:01.823Z","kind":"child_started","data":{"child_pid":12399,"desc":"xargs wc -l"}}
{"ts":"2026-05-17T10:33:02.001Z","kind":"child_exit","data":{"child_pid":12399,"exit_code":0}}
{"ts":"2026-05-17T10:33:02.184Z","kind":"task_exit","data":{"exit_code":0}}
{"ts":"2026-05-17T10:33:02.184Z","kind":"backgrounded","data":{"cause":"timeout","limit_ms":120000}}
```

## Components

### `agent-tools hook-pre`

Invoked from `settings.json` as a PreToolUse hook with matcher `Bash|Monitor`. Stdin is
the standard Claude Code hook payload (see decompiled `OM` + `Wf_` schemas).

Behavior:

1. Parse stdin JSON. Extract `session_id`, `agent_id`, `tool_name`, `tool_input.command`,
   `tool_input.description`, `cwd`, `tool_use_id`.
2. Compute `task_dir`:
   - subagent: `~/.claude/agent-tools/<session_id>/<agent_id>/<tool_use_id>/`
   - main: `~/.claude/agent-tools/<session_id>/<tool_use_id>/`
3. `mkdir -p` the directory and `children/`.
4. Write `meta.json` (without `ended_at`/`exit_code`/`pid` — wrap-task fills these in).
5. Write `command.sh` with the raw original command bytes.
6. Emit JSON to stdout:
   ```json
   {
     "hookSpecificOutput": {
       "hookEventName": "PreToolUse",
       "permissionDecision": "allow",
       "updatedInput": { "command": "exec agent-tools wrap-task <task_dir>" }
     }
   }
   ```
   `<task_dir>` is shell-quoted (single-quotes plus `'\''` escape) so the dir path
   survives `bash -c`.

The hook never blocks the call. If anything fails (cannot create dir, cannot write
`command.sh`, cannot write `meta.json`), it emits no `updatedInput` (allowing the
original command to run un-wrapped) and writes a diagnostic to stderr. Failure of the
capture layer must not break the user's command. The contract: hook-pre rewrites
**only when `command.sh` is durably on disk**.

### `agent-tools hook-post`

PostToolUse for the same matcher. Stdin is the hook payload (with `tool_response`).

Behavior:

1. Parse stdin JSON. Identify the task dir from the embedded `tool_use_id` and
   `session_id` (rebuild the same path as hook-pre).
2. Inspect `tool_response.assistantAutoBackgrounded`, `tool_response.backgroundedByUser`,
   `tool_response.backgroundTaskId`, and `tool_input.timeout`. Determine the cause if any:
   - `assistantAutoBackgrounded` → KAIROS auto-background
   - `backgroundedByUser` → user Ctrl+B
   - `backgroundTaskId` present without the above → timeout (use `tool_input.timeout`
     or default `120000` ms)
   - none of the above → no backgrounding
3. If backgrounded, append a `backgrounded` event to `events.jsonl` and emit
   `additionalContext` describing what happened, mirroring the message the current
   `hooks/bash_background_hook.sh` produces (paths printed by `ps`, instructions to
   `TaskStop` the background task).
4. If not backgrounded, no `additionalContext` — but `wrap-task` already wrote
   `task_exit` to `events.jsonl`, so nothing else is needed here.

The existing `hooks/bash_background_hook.sh` file is not loaded by `settings.json`
(verified by reading the current `settings.json`); no migration required.

### `agent-tools wrap-task <task_dir>`

Internal. Spawned by the rewritten Bash command. Tokio runtime.

1. Load `<task_dir>/meta.json` and `<task_dir>/command.sh`.
2. Open `stdout` and `stderr` for append.
3. Create stdout and stderr `pipe(2)` pairs; spawn `bash --noprofile --norc command.sh`
   with the child's stdout/stderr connected to the write ends, env extended with
   `AGENT_TOOLS_TASK_ID=<task_dir>`. (Using `bash <path>` instead of `bash -c "$(cat …)"`
   keeps the file on disk as the canonical source — no shell-quoting in the chain.)
4. Patch the running `meta.json` with `pid` and `started_at` (atomic rename).
5. Two reader tasks (`tokio::io::copy`-like): each reads the pipe, writes to the
   on-disk file, also writes through to wrap-task's own `stdout`/`stderr` so the
   user-visible behavior is unchanged. Updates `last_activity` (per-stream atomic) on
   each non-empty read. Appends `first_byte` to `events.jsonl` once per stream.
6. A timer task (1 s tick) checks `now - last_activity > 30 s` per stream. On crossing
   the threshold while running, appends `silence`. On the next read after a silence
   event, appends `silence_break` and resets the per-stream warned flag.
7. A signal task forwards SIGINT, SIGTERM, SIGHUP, SIGQUIT to the child (the agent's
   `TaskStop` and timeout-kill paths produce these).
8. On child exit: write `ended_at`, `exit_code` to `meta.json` (atomic rename), append
   `task_exit` to `events.jsonl`, exit with the child's exit code (or `128 + signum` if
   killed by signal).

If `wrap-task` is launched without a valid `<task_dir>` (missing arg, missing dir, or
missing `command.sh`), it exits non-zero with a diagnostic to stderr. This path should
not be reachable in practice — hook-pre only rewrites the command when `command.sh` is
durably on disk, so a missing file at wrap-task time indicates external interference
(state dir manually removed mid-flight, etc.). In that case the user's command does
not run; the failure surfaces as a clearly-marked diagnostic rather than a silent
miss.

### `agent-tools run [--desc DESC] -- <cmd>...`

Agent-facing. Inserted inline:

```
find … | agent-tools run --desc "wc lines" -- xargs wc -l | tail -3
```

1. Require `AGENT_TOOLS_TASK_ID`. If unset, exit `2` with stderr:
   ```
   agent-tools run: AGENT_TOOLS_TASK_ID is not set.
   The PreToolUse hook (agent-tools hook-pre) must wrap this Bash/Monitor call.
   If you see this from inside a Claude Code Bash tool, the hook is not installed.
   ```
2. `child_dir = $AGENT_TOOLS_TASK_ID/children/<pid>/`. mkdir. Write `meta.json`
   (without `ended_at`/`exit_code`).
3. Open `stdout`, `stderr` for append.
4. Spawn `<cmd>` with:
   - stdin = wrap-task's own stdin (passed through verbatim, never captured — spec)
   - stdout = pipe; reader task tees to `stdout` file + wrap-task's stdout fd
   - stderr = pipe; reader task tees to `stderr` file + wrap-task's stderr fd
   - env unchanged (AGENT_TOOLS_TASK_ID stays set so any descendant `run` nests correctly)
5. Signal forwarding identical to `wrap-task`.
6. Same silence-warning logic, threshold 30 s, events written to the child's
   `events.jsonl`. The parent task's `events.jsonl` records `child_started` and
   `child_exit` from the run process directly.
7. Exit with child's exit code.

### `agent-tools ps [--task <id>] [--session-id <id>]`

Agent-facing. No arguments → list live tasks in the current session.

Defaults:

- Current session derived from `AGENT_TOOLS_TASK_ID` (walk up: `task_dir → agent_or_session
  dir → session dir`).
- "Live" = pid in `meta.json` responds to `kill(pid, 0)` OR `meta.json` has no
  `ended_at`. Both conditions guard against process-recycled pids and against crashed
  wrap-task that never wrote the closing meta.

Flags:

- `--task <task_id>` — show detail for one task; expands to its children and event log.
- `--session-id <id>` — operate in a different session (cross-session inspection
  by a session-A agent looking at session-B tasks).

Output layout:

```
session: 93d9406c-70dc-4346-b820-9d262ccf946c
agent:   _main

task toolu_01ABC...  [running]
  desc:           Run unit tests
  started:        2026-05-17T10:32:11Z  (00:00:42 ago)
  silence-warn:   30s
  pid:            12345
  cmd (truncated):  cargo test --workspace 2>&1 | tee /tmp/out
  stdout:         /root/.claude/agent-tools/.../stdout  (12834 bytes)
  stderr:         /root/.claude/agent-tools/.../stderr  (217 bytes)
  children:
    pid 12399  [exited 0]
      desc:     xargs wc -l
      cmd:      xargs wc -l
      stdout:   .../children/12399/stdout  (482 bytes)
      stderr:   .../children/12399/stderr  (0 bytes)
      duration: 00:00:01.183

events (chronological, all tasks):
  10:32:11.482  task_started        toolu_01ABC...    pid=12345
  10:32:11.617  first_byte          toolu_01ABC...    stream=stdout
  10:32:42.001  silence             toolu_01ABC...    stream=stdout (30.384s)
  10:33:01.823  child_started       toolu_01ABC...    pid=12399 desc="xargs wc -l"
  10:33:02.001  child_exit          toolu_01ABC...    pid=12399 exit=0
  10:33:02.184  task_exit           toolu_01ABC...    exit=0
```

No content slicing. The agent reads `stdout`/`stderr` from disk with its existing
`Read` tool.

## Settings registration

`settings.json` `hooks` block adds:

```json
"PreToolUse": [
  {
    "matcher": "Bash|Monitor",
    "hooks": [
      { "type": "command", "command": "agent-tools hook-pre", "timeout": 5 }
    ]
  }
],
"PostToolUse": [
  {
    "matcher": "Bash|Monitor",
    "hooks": [
      { "type": "command", "command": "agent-tools hook-post", "timeout": 5 }
    ]
  }
]
```

The existing Agent-matcher PreToolUse stays as-is.

## Constraints honored

- **One env var** — only `AGENT_TOOLS_TASK_ID` flows into the wrapped process tree.
- **All in Rust** — hook-pre, hook-post, wrap-task, run, ps are subcommands of one
  binary; `settings.json` invokes them directly with no shell or Python in the path.
- **No truncation** — `stdout`/`stderr` capture files have no upper bound.
- **No GC** — there is no `clean` subcommand. The directory grows until a human removes
  state. Accepted trade-off.
- **No hidden magic** — every entry in `events.jsonl` is human-readable, capture files
  are plain bytes, `meta.json` is plain JSON.
- **General & composable** — `agent-tools run` works from any descendant of a wrapped
  Bash/Monitor call, including temporary scripts in `/tmp`.
- **Background-compatible** — `wrap-task` survives if the agent's Bash tool times out and
  backgrounds the wrapper; the wrapper keeps tee'ing until its child exits. `hook-post`
  records the involuntary backgrounding to events and `additionalContext`.

## Non-goals (out of this design)

- Garbage collection of stale state.
- A `--tail`/`--head`/`--grep` content slicer.
- Per-task silence threshold overrides.
- Capturing `run`'s stdin (the upstream pipe content). Capture is the wrapped command's
  output only — that's what truncation discards downstream.
- Replacing `hooks/bash_background_hook.sh` runtime behavior is unnecessary because
  the existing shell file is not loaded; `hook-post` provides equivalent `additionalContext`.

## Open questions

None at this stage. Implementation discovery may surface refinements; this document is
the source of truth until updated.

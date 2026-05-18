# agent-tools run — User Requirements

A capture layer for Bash and Monitor tool calls that lets agents recover
output Claude Code's pipeline would otherwise discard. Capture is opt-in
per stage via `agent-tools run`; the PostToolUse hook surfaces every
capture back to the agent so it can `Read` the disk path.

## Why

Truncating pipes (`| tail -5`, `| grep`, `| wc -l`, `| jq .field`) discard
upstream stdout before the Bash tool sees it. This costs the agent when
the upstream command is slow (e.g. compiling), expensive (e.g. paid API
call), or has side effects (e.g. apt, gdb, schema migration). Claude
Code's tool result can also be truncated when output exceeds its display
cap.

The fix has to live inside the shell command itself, between pipe
segments, or wrap the whole command at top level.

## Components

- **`agent-tools run [--desc DESC] -- <cmd>`** — agent-facing. Insert
  explicitly anywhere an output might be lost, e.g.
  `find … | agent-tools run --desc wc -- xargs wc -l | tail -3`, or at
  top level when CC may truncate the tool result. Only flag is `--desc`.

  - Pass-through: forwards signals, does not buffer; argv-exec'd directly
    (no `bash -c` wrapper).
  - Tees stdout/stderr to a file under the parent dir (set by
    `AGENT_TOOLS_PARENT_DIR`).
  - Loud failure if `AGENT_TOOLS_PARENT_DIR` is not set — the PreToolUse
    hook is responsible for setting it.

- **`agent-tools hook-pre`** — PreToolUse hook (Rust subcommand wired in
  `settings.json:70-77`). For Bash/Monitor, prepends a fixed shell prefix
  to the user's command:
  `unset HTTPS_PROXY NODE_EXTRA_CA_CERTS NODE_OPTIONS; export AGENT_TOOLS_PARENT_DIR='<path>'; <original>`
  No state on disk; no `command.sh`, no `meta.json`, no `exec` wrapper.
  Claude Code's native bash invocation (shell snapshot, `eval … < /dev/null`,
  post-`cd` cwd capture) is preserved verbatim.

- **`agent-tools hook-post`** — PostToolUse hook (Rust subcommand wired
  in `settings.json:82-89`). For Bash/Monitor, lists every
  `agent-tools run` capture from this tool call by scanning the parent
  dir for pid subdirs, and emits the listing in `additionalContext`.
  Also detects and explains involuntary backgrounding
  (`backgroundTaskId` in the tool response). Stays silent when neither
  applies.

- **`agent-tools ps [--task <id>] [--session-id <id>]`** — agent-facing.
  Lists `agent-tools run` captures grouped by `tool_use_id` for the
  current or specified session. Each capture: pid, desc, command,
  stdout/stderr path + size, exit code or running status.
  `--session-id` exists for cross-session diagnosis (a session-A agent
  inspecting session-B captures).

## State

- Lives under `~/.claude/agent-tools/<session>/[<subagent>/]<tool_use_id>/<pid>/`.
- Each `<pid>` subdir contains `stdout`, `stderr`, `meta.json`.
- Parent dir (`<tool_use_id>/`) is created lazily on first
  `agent-tools run` invocation. Bash calls that don't invoke
  `agent-tools run` leave no disk state.
- All captured output is durable on disk, addressable by the absolute
  paths PostToolUse and `ps` print.
- Content retrieval is via the agent's `Read` tool on those paths. There
  is no content-slicing subcommand (`--tail`, `--head`, `--grep`, etc.).

## Constraints

- **Exactly one env var (`AGENT_TOOLS_PARENT_DIR`)** propagated to user
  commands. Everything else stored on disk under that dir.
- **Everything in Rust.** Hook entries in `settings.json` invoke Rust
  subcommands of `agent-tools` directly.
- **No truncation** of captured output. Captures grow without bound.
- **No GC, no `clean` subcommand.** A human removes stale state from the
  directory manually. A persistent Monitor on a chatty log will
  eventually fill the disk — accepted trade-off for never losing
  captured output.
- **No hidden magic.** The PreToolUse hook only prepends `unset` and
  `export`; CC's bash command is otherwise unmodified. Shell flags, `$0`,
  monitor mode, aliases, and `cd` tracking all match Claude Code native
  behavior. (Justified by `plans/wrap-task-bash-state-experiment.md`,
  which documented the divergence under the prior wrap-task model.)
- **General & composable.** `agent-tools run` is invokable from
  temporary bash or python scripts inside a Bash tool call; no special
  calling convention.
- **Background-compatible.** PostToolUse surfaces involuntary
  backgrounding notices (timeout, KAIROS auto-bg, user Ctrl+B)
  independent of whether `agent-tools run` was used.

# agent-tools wrap-task / run — User Requirements

A wrapper layer for Bash and Monitor tool calls that recovers what Claude Code's current Bash tool throws away.

## Why

Truncating pipes (`| tail -5`, `| grep`, `| wc -l`, `| jq .field`) discard upstream stdout before the Bash tool sees it.
This causes problem if the command before the pipe is slow (e.g. compiling), cost money (e.g. api calls) or have side effects (e.g. apt, gdb).

The fix has to live inside the shell command itself, between pipe segments.

## Components

- **`agent-tools wrap-task`** — internal. PreToolUse hook rewrites every Bash and Monitor command to invoke wrap-task around the original. wrap-task creates per-task state, captures the top-level command's stdout/stderr, and watches for silence.

- **`agent-tools run [--desc DESC] -- <cmd>`** — agent-facing. Agent inserts explicitly inside pipelines where intermediate capture is wanted, e.g. `find … | agent-tools run -- xargs wc -l | tail -3`. Only flag is `--desc`.

  - Tries to be as pass-through as possible: forwards signals, does not buffer (add tests for this).
  - captures stdout, stderr to a file

- **`agent-tools ps [--tasks <id>] [--session-id <id>]`** — agent-facing. Default (no args): resolve to all live tasks in this session

  - Each task: detail showing task id, started time, current time, desc, agent, silence-warning threshold, child list (each: child id, desc, which subagent, pid, truncated command, stdout and stderr path + size).
  - Over all tasks: A chronological event log (started, first byte in, first byte out, first byte after silence of <N>s, exit with code, other notable events). `--session-id` exists for cross-session diagnosis (a session-A agent inspecting session-B tasks).

- **`agent-tools hook-pre`** + **`agent-tools hook-post`** — Rust subcommands invoked directly from `settings.json` as PreToolUse / PostToolUse handlers for the `Bash|Monitor` matcher. No shell or Python in the loop.

## State

- Lives under `~/.claude/agent-tools/<session>/<taskid>/`, `~/.claude/agent-tools/<session>/<subagent session>/<taskid>/`
- All captured stdout/stderr is durable on disk, addressable by the absolute paths `ps` prints.
- Content retrieval is via the agent's `Read` tool on those paths. There is no content-slicing subcommand (`--tail`, `--head`, `--grep`, etc.).

## Constraints

- **Exactly one env var (task id)** propagated to descendants. Everything else stored in disk.
- **Everything in Rust.** Hook entries in `settings.json` invoke Rust subcommands of `agent-tools` directly.
- **No truncation** of captured output. Captures grow without bound.
- **No GC, no `clean` subcommand.** A human removes stale state from the directory manually. A persistent Monitor on a chatty log will eventually fill the disk — accepted trade-off for never losing output.
- **No hidden magic** Runtime agents understand everything that happen easily.
- **General & composable** Call from temporary bash or python scripts
- **Background-compatible** Handles timeout, timeout backgrouding, monitor correctly

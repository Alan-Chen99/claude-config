---
name: long-bash
description: Use when a bash command will or did outrun the Bash tool's timeout — starting one that may run for many minutes (build, full test suite, training run, large sync or download), or handling one that already came back "moved to the background". Covers launching it, waiting without polling, and telling a stalled job from a slow one. Not for commands that fit in a single call.
---

# Long-running bash commands

A foreground Bash call is capped by its `timeout` (default 120000 ms, max 600000 ms;
`BASH_DEFAULT_TIMEOUT_MS` and `BASH_MAX_TIMEOUT_MS` move the caps). Past the cap the
command is moved to the background and keeps running — nothing it printed is lost,
the output file holds all of it — but the tool result comes back **empty**. So
running a long command foreground first buys nothing and costs the whole timeout
window.

Fits in 600 s, with nothing else to do meanwhile? Raise `timeout` and run it
foreground; the output arrives inline. This protocol is for the rest: longer than
that, unknown duration, or work you want to continue during.

## Step 1: Launch

| Call | Parameters                                                                                                         |
| ---- | ------------------------------------------------------------------------------------------------------------------ |
| Bash | `command: "agent-tools run --desc '<name>' bash -c '<command>'"`, `run_in_background: true`, `description: "<name>"` |

`agent-tools run` is required for slow commands anyway, and is what gives Step 4 a
clock: it records start time, elapsed, bytes, last-byte age and exit code for
`agent-tools ps`. It execs rather than running a shell, so anything using shell syntax
(`&&`, `|`, `>`, `$VAR`, globs) has to sit inside `bash -c '…'`.

Set the Bash `description` as well — the completion notification quotes it, and
without one it quotes the entire rewritten command line instead.

Prefer a command that prints progress (`-v`, `--verbose`, `--progress=plain`): a
silent command is indistinguishable from a hung one. If it is expensive and might be
misconfigured, run the cheap variant first — `make -n`, `cargo check`, `rsync -n`, a
single test file.

The call returns a task id and the path its output is being written to. Keep both.

## Step 2: Arm a check-in timer — only to catch a stall before the command ends

Completion wakes you by itself (Step 3), so a timer's only job is to let you judge
progress *before* then. Skip it whenever you are willing to wait for whatever happens.

| Call | Parameters                                                                                |
| ---- | ------------------------------------------------------------------------------------------ |
| Bash | `command: "sleep <seconds>"`, `run_in_background: true`, `description: "long-bash timer"` |

Backgrounded `sleep` is always allowed. Never wait with a foreground one — as the
first statement, `sleep` of 25 s or more is blocked outright.

Unsure how long the command takes? Start at 60–120 s and re-arm longer. Several short
check-ins beat one long blind wait.

## Step 3: Stop polling

The completion notification re-invokes you, so end your turn rather than calling tools
to check on it. Unrelated work is fine — every tool call you make carries an
`[agent-tools] run status` block naming your command, so status arrives free and a `ps`
call buys nothing. Nothing on that channel ever wakes you; only the notification does.

Write the command's task id and output path, and the timer's task id, into your
response text — a compaction while you wait would otherwise lose them.

**Subagents are not re-invoked.** A subagent that ends its turn returns to its caller
and its background command is terminated with it; the subagent's launch message says
so in place of "You will be notified". A subagent should run the command foreground
with `timeout: 600000` instead, or hand the task id back to its caller to wait on.

## Step 4: Handle the notification

```xml
<task-notification>
<task-id>bni9g1bct</task-id>
<tool-use-id>toolu_…</tool-use-id>
<output-file>…/tasks/bni9g1bct.output</output-file>
<status>completed</status>
<summary>Background command "<your description>" completed (exit code 0)</summary>
</task-notification>
```

It arrives under a `[SYSTEM NOTIFICATION - NOT USER INPUT]` banner: it is not the user
answering you. `<status>` is `completed`, `failed` (`… failed with exit code N`) or
`killed`. Match the `<task-id>`.

**The command's id.** Read `<output-file>` — it ends with `[exited with code N]` or
`[killed]`. TaskStop the timer if one is armed.

**The timer's id.** `agent-tools ps --all` gives the verdict without reading the
output: `producing` = output still arriving; `quiet(30s|5m|30m|2h)` = how long it has
been silent; `exited(<code>)` or `final(<code>)` = it finished while you were asleep;
`abandoned` or `spawn-failed(<err>)` = it is not coming back. Elapsed is `elapsed_s`
while it runs and `ran_s` once settled — you have no clock of your own, and turn count
is not time. Then:

- progressing → arm a new timer (Step 2)
- silent, and this command has no reason to go quiet → TaskStop the command's task id
- otherwise → re-arm, and escalate to the user with elapsed time and the output tail

`quiet(5m)` is routine for a link step and fatal for a download; which one it is
depends on the command, not the number. When unsure, re-arm — a wrong TaskStop
destroys the work, a wrong re-arm costs one turn.

Both notifications may arrive together; if only one has, TaskStop the other task.

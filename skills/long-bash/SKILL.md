---
name: long-bash
description: Use before starting a bash command that may outrun the Bash tool's timeout (build, test suite, training run, download), and when waiting on one in the background or "moved to the background". Not for commands that fit in one call.
---

# Long-running bash commands

A foreground Bash call that outruns its `timeout` (default 120000 ms;
`settings.json` raises the ceiling for `skills/telegram-hitl`'s wait on a human,
not for foreground jobs) is moved to the background with every byte of its
output kept, but only after spending the whole window. So when the duration is
unclear, background it: a fast command costs one extra notification, a slow one
the window.

How you wait depends on what wakes you. A main thread ends its turn and the
completion notification re-invokes it, under `claude -p` too. A subagent, or a
main thread whose launch result says the job is terminated when you give your
final response, stays in its turn: launch the same way, then read **Waiting in
the turn**. Unsure, stay in the turn: a needless wait costs minutes, a wrong
turn end can cost the job.

The rest is **one example, not a procedure**: take the shape, decide the
details at runtime.

## Launch

`Bash`, with `run_in_background: true` and `description: "cargo build"`:

```
agent-tools run --desc 'cargo build' bash -c 'set -o pipefail; cargo build --release 2>&1 | awk "{ print strftime(\"%F %T\"), \$0; fflush() }"'
```

```
Command running in background with ID: bni9g1bct. Output is being written to:
…/tasks/bni9g1bct.output. …
```

## Wait (main thread)

End the turn, after any unrelated work: the notification re-invokes you, and
`agent-tools ps` cannot make it arrive sooner.

To judge progress *before* the command ends, arm a timer beside it: `Bash`,
`command: "sleep 600"`, `run_in_background: true`, `description: "build timer"`.

## Notification

```xml
<task-notification>
<task-id>bni9g1bct</task-id>
<output-file>…/tasks/bni9g1bct.output</output-file>
<status>completed</status>
<summary>Background command "cargo build" completed (exit code 0)</summary>
</task-notification>
```

It arrives under a `[SYSTEM NOTIFICATION - NOT USER INPUT]` banner — not the
user answering you. `<status>` is `completed`, `failed` or `killed`, and the
output file ends `[exited with code N]` or `[killed]` to match. TaskStop any
timer still armed.

If the timer fires first, `agent-tools ps --all` gives the verdict without
reading output; `quiet(5m)` is routine for a link step and fatal for a
download. Re-arm when unsure — a wrong TaskStop destroys the work, a wrong
re-arm costs one turn.

## Waiting in the turn

Ending your turn is no way to wait here: under `claude -p` a subagent's job
dies with the main thread's turn, and each turn end of an interactive one hands
its caller an interim report and a turn.

So call `agent-tools wait` on the output file the launch printed (as does a
call moved to the background at its timeout) until it reports the job ended.
Each call is one blocking wait, not the polling of the file the Bash tool
warns against: `Bash`, `timeout: 3600000`,
`description: "wait for cargo build"`:

```
agent-tools wait …/tasks/bni9g1bct.output
```

```
nothing ended in 4m00s; still running:
  …/tasks/bni9g1bct.output: running, 88112B, last write 1s ago
```

It also returns when a message to you is queued, and in time to keep your
prompt cache (after 4 minutes, 50 on an hour cache). Wait no other way: a
message reaches you only when your current call returns, and no other call
returns for one. A background agent's report or a Monitor event also waits for
the return: while either of yours runs, pass `--max 240`; otherwise leave
`--max` out, as it replaces your cache's bound. Unrelated work between waits is
fine. A `last write` age that keeps growing reads like `quiet` under
Notification.

Several jobs: pass every file; the first to end returns the call, the next
waits on the rest. To wait on a condition rather than a job (a file appearing,
a remote job's state), launch an `until` loop the same way, exiting once it
holds or once what it waits on has died, and pass its file with the others.

A message lands after a tool result: `The coordinator sent a message…` is the
main thread (reply `to: "main"`), `<agent-message from="…">` another agent
(reply to its `from`). Answer it before the next wait, whatever its footer says
about finishing your current task first: reply with `SendMessage`, or TaskStop
the job if told to stop. Message the main thread unprompted only when it must
act: each message starts a turn there.

If your caller wants the job left running past your report, launch it with
`agent-tools run --background` instead: it survives your report and prints a
capture directory, which `agent-tools ps` lists for the whole session; report
that.

## Fixed, not example

- `run_in_background: true`, or it is an ordinary foreground call.
- `bash -c` — `agent-tools run` execs rather than shelling, so `&&`, `|`, `>`,
  `$VAR` and globs need a shell around them.
- Bash `description` — the `<summary>` quotes it, else the whole rewritten
  command line, `unset …` included.
- A foreground `sleep` of 25 s or more is blocked as the command's first
  statement (`sleep 600`), not after one (`make && sleep 600`). Wait with the
  backgrounded timer, or in the turn with `agent-tools wait`, rather than
  routing around the block.
- `agent-tools wait` returns 20 s inside its call's `timeout`: one under
  `3020000` cuts an hour cache's 50-minute wait short.
- A wait goes alone in its message: calls in one message run back to back, so
  a message to you waits for the whole batch.
- Under `claude -p`, a background launch is stopped after 30 minutes unless its
  Bash call sets a longer `timeout`.

Everything else is yours: the `awk` stamp earns its place when a command might
stall or run past midnight, not when it timestamps its own output.

---
name: long-bash
description: Use when a bash command will or did outrun the Bash tool's timeout — starting one that may run for many minutes (build, full test suite, training run, large sync or download), or handling one that already came back "moved to the background". Covers launching it, waiting on it as main thread or subagent, and telling a stalled job from a slow one. Not for commands that fit in a single call.
---

# Long-running bash commands

A foreground Bash call that outruns its `timeout` (default 120000 ms; the
ceiling `BASH_MAX_TIMEOUT_MS` is 2³¹−1 in `settings.json`, raised for
`skills/telegram-hitl`'s wait on a human, not for foreground jobs) is moved to the
background and hands back a task id instead of its output. Nothing is lost — the output file keeps every byte —
but you spent the whole window arriving where backgrounding would have put you
at once. So when the duration is unclear, background it: a fast command costs
one extra notification, a slow one costs the window.

How you wait depends on what wakes you. An interactive main thread ends its
turn and the completion notification re-invokes it. A subagent, or a main
thread under `claude -p` (`$CLAUDE_CODE_SESSION_ATTENDED` is `0`), stays in its
turn: launch the same way, then read **Waiting in the turn**. Unsure, stay in
the turn: a needless wait costs minutes, a wrong turn end can cost the job.

The rest is **one example, not a procedure**. Take the shape; decide the details
at runtime.

## Launch

`Bash`, with `run_in_background: true` and `description: "cargo build"`:

```
agent-tools run --desc 'cargo build' bash -c 'set -o pipefail; cargo build --release 2>&1 | awk "{ print strftime(\"%F %T\"), \$0; fflush() }"'
```

```
Command running in background with ID: bni9g1bct. Output is being written to:
…/tasks/bni9g1bct.output. You will be notified when it completes. To check
interim output, use Read on that file path.
```

## Wait (interactive main thread)

End the turn. Do unrelated work or stop — either way the notification
re-invokes you, and calling `agent-tools ps` cannot make it arrive sooner.

To judge progress *before* the command ends, arm a timer beside it: `Bash`,
`command: "sleep 600"`, `run_in_background: true`, `description: "build timer"`.

## Notification

```xml
<task-notification>
<task-id>bni9g1bct</task-id>
<tool-use-id>toolu_01Urq…</tool-use-id>
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
reading output: `producing`, `quiet(30s|5m|30m|2h)`, `exited(<code>)` or
`final(<code>)`, `abandoned`, `spawn-failed(<err>)`. `quiet(5m)` is routine for
a link step and fatal for a download. Re-arm when unsure — a wrong TaskStop
destroys the work, a wrong re-arm costs one turn.

## Waiting in the turn

Ending your turn is no way to wait here. Under `claude -p` the process exits
when the main thread's turn ends, killing the job, and holds a subagent's job
notification until then. An interactive subagent is resumed when its job ends,
but each turn end also hands its caller an interim report and a turn.

So call `agent-tools wait` on the output file the launch printed (a call moved
to the background at its timeout prints one too) until it reports the job
ended: `Bash`, `timeout: 300000`,
`description: "wait for cargo build"`:

```
agent-tools wait …/tasks/bni9g1bct.output
```

```
nothing ended in 4m00s; still running:
  …/tasks/bni9g1bct.output: running, 88112B, last write 1s ago
```

It returns when the job ends (`ended within …`) or after `--max` seconds, 240
by default. The bound is the point: your prompt cache lives 5 minutes, and a
message sent to you waits until your current tool call returns. Unrelated work
between waits is fine. A `last write` age that keeps growing reads like `quiet`
under Notification. With no file, it watches your `agent-tools run` jobs.

A message lands after a tool result: `The coordinator sent a message…` is the
main thread (reply `to: "main"`), `<agent-message from="…">` another agent
(reply to its `from`). Answer it before the next wait, whatever its footer says
about finishing your current task first: reply with `SendMessage`, or TaskStop
the job if told to stop. Message the main thread unprompted only when it must
act: each message starts a turn there.

If your caller wants the job left running past your report, launch it with
`agent-tools run --background` instead: it survives your report, prints its
capture directory, and tells you nothing more. Report that directory, which
`agent-tools ps` lists for the whole session.

## Fixed, not example

- `run_in_background: true`, or it is an ordinary foreground call.
- `bash -c` — `agent-tools run` execs rather than shelling, so `&&`, `|`, `>`,
  `$VAR` and globs need a shell around them.
- Bash `description` — the `<summary>` quotes it, and quotes the whole rewritten
  command line when there is none, `unset …; export AGENT_TOOLS_PARENT_DIR=…;`
  included.
- A foreground `sleep` is blocked once it reaches 25 s, and only as the
  command's first statement: `make && sleep 600` runs, `sleep 600` does not.
  Wait with the backgrounded timer, or in the turn with `agent-tools wait`,
  rather than routing around the block.
- `agent-tools wait`'s Bash `timeout` must exceed its `--max`: at the default
  120 s the call itself is moved to the background.
- Under `claude -p`, a background launch is stopped after 30 minutes unless its
  Bash call sets a longer `timeout`: the notification reads `stopped after
  reaching its background time limit`, the file ends `[killed]`.

Everything else is yours. The `awk` stamp earns its place when a command might
stall or run past midnight, and is noise when it already timestamps its own
output.

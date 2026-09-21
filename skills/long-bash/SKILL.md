---
name: long-bash
description: Use when a bash command will or did outrun the Bash tool's timeout — starting one that may run for many minutes (build, full test suite, training run, large sync or download), or handling one that already came back "moved to the background". Covers launching it, waiting without polling, and telling a stalled job from a slow one. Not for commands that fit in a single call.
---

# Long-running bash commands

A foreground Bash call that outruns its `timeout` (default 120000 ms, max
600000 ms, silently clamped) is moved to the background and hands back a task
id instead of its output. Nothing is lost — the output file keeps every byte —
but you spent the whole window arriving where backgrounding would have put you
at once. So when the duration is unclear, background it: a fast command costs
one extra notification, a slow one costs the window.

**A subagent stops here.** You are never re-invoked by a completion
notification, and a background task of yours is killed the moment you give your
final response. Run the command foreground — still wrapped — with
`timeout: 600000`. If it needs longer than that, `agent-tools run --background`
detaches the job so it outlives your turn, prints its capture directory, and
reports nothing back to you; hand that path to your caller.

The rest is **one example, not a procedure**. Take the shape; decide the details
at runtime.

## Launch

`Bash`, with `run_in_background: true` and `description: "cargo build"`:

```
agent-tools run --desc 'cargo build' bash -c 'cargo build --release 2>&1 | awk "{ print strftime(\"%F %T\"), \$0; fflush() }"'
```

```
Command running in background with ID: bni9g1bct. Output is being written to:
…/tasks/bni9g1bct.output. You will be notified when it completes. To check
interim output, use Read on that file path.
```

## Wait

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

## Fixed, not example

- `run_in_background: true`, or it is an ordinary foreground call.
- `bash -c` — `agent-tools run` execs rather than shelling, so `&&`, `|`, `>`,
  `$VAR` and globs need a shell around them.
- Bash `description` — the `<summary>` quotes it, and quotes the whole rewritten
  command line when there is none, `unset …; export AGENT_TOOLS_PARENT_DIR=…;`
  included.
- A foreground `sleep` is blocked once it reaches 25 s, and only as the
  command's first statement: `make && sleep 600` runs, `sleep 600` does not.
  Wait with the backgrounded timer rather than routing around the block.

Everything else is yours. The `awk` stamp earns its place when a command might
stall or run past midnight, and is noise when it already timestamps its own
output.

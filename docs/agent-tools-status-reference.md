# `agent-tools run` — status channel and passthrough reference

The system prompt carries the subset of this that changes what an agent types. This file
carries the full grammar, and `scripts/check-prompt-coupling.sh` pins every string here
against its emit site in `agent-tools/src`, so a rename in the source fails the check.

## Delivery

Status is injected as `additionalContext` by hooks on three events, and only those three:
`PostToolUse`, `PostToolUseFailure`, and `UserPromptSubmit` (`settings.json`). There is no
timer and no `Stop`-event injection. An agent is therefore never woken: a status change
becomes visible on its next tool result or on the user's next turn, whichever comes first.
A job that outlives a single Bash call (max 600000 ms) must record its own failures
somewhere the agent can block on, because polling `agent-tools ps` cannot substitute — see
"Why `ps` is not pollable" below.

## Block shape

A block begins `[agent-tools] run status:` and lists every wrapped process whose status
changed since the agent was last told, one per line:

```
<name> [<key>] <detail> -> <paths>
```

A degraded report keeps the same header prefix (`[agent-tools] run status: unavailable
this time (…)`), so a failed report still reads as status rather than as command output.
A block may also carry non-status lines: `note: report history lost — …`, `note: <dir>
could not be listed …`, and `… N more changed, omitted for size …`.

`BACKGROUNDED:` is emitted by `hook_post.rs` only when a tool response carries
`backgroundTaskId`. `settings.json` sets `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`, under
which Bash never returns one, so that line does not reach the agent in this configuration.

## Keys

| Key | Meaning |
| --- | --- |
| `producing` | Output is still arriving |
| `quiet(<bucket>)` | No output for a while; buckets are `30s`, `5m`, `30m`, `2h` |
| `exited(<code>)` | The child is reaped; the capture file may still grow while the wrapper drains |
| `final(<code>)` | The file will not grow again. Not a promise of completeness — a wrapper that died without draining also reports `final` |
| `abandoned` | The wrapper is gone without a recorded exit |
| `spawn-failed(<error>)` | The child never started |

A key is reported once per change, and the ledger stores only the last *reported* key, so a
`producing → quiet → producing` round trip between two delivery points is never reported.
Silence means nothing changed since the last report, not that nothing is running.

## Detail and paths

`<detail>` is `pid <pid>, <age>, <bytes>`, where `<pid>` is the child's (or `-`), `<age>` is
`last byte Ns ago` or `no output`, and `<bytes>` is `output=NB` or `out=NB err=NB`.
`<paths>` names the capture file: `<dir>/output` when the streams were merged, else
`<dir>/stdout` and `<dir>/stderr`. The two pids on a line differ on purpose: `<pid>` is the
child's, while `<dir>` is named for the wrapper's — e.g. `pid 1720919 … -> …/1720906/output`.

Two bracket groups may follow the detail, and both are absent from an ordinary run. They
hold facts about the run, not a second key:

- `[streams split: <why>; downstream closed; drain capped; capture failed: <err>]` — any
  subset, in that order — says how the run differed from bare.
- `[stat failed: <err>]` says the hook could not stat a capture file.

## Passthrough: how a wrapped run differs from bare

The wrapper forwards each stream's bytes unchanged and in order, inherits stdin, and where
the caller's stdout and stderr already share one pipe or one appending file, gives the child
a single destination too — so ordinary calls keep their interleaving and `2>&1` is a no-op.
The merge requires same device+inode **and** both ends FIFO or both `O_APPEND`; a shared tty
splits. Known differences:

1. A downstream that quits stops neither the child nor the call: `… | head -3` prints three
   lines while the whole result still lands on disk, and `pipefail` reports the producer's
   own status rather than `141`. Past the post-close drain's 256 MiB bound the read end
   closes, the child takes the `SIGPIPE` bare would have given it, and the line shows `141`
   beside `drain capped`.
2. The wrapper is a separate process with the child's argv, so a `pkill -f` aimed at the
   command matches both. `--hide-cmdline` suppresses the argv and `--desc` in `/proc`.
3. The wrapper writes its own diagnostics to stderr, always prefixed `agent-tools:`.
4. `isatty` is false on the child's stdout and stderr — inherent to a tee. This is not a
   difference from bare in the Bash tool, which already pipes both: `test -t 1` reports no
   tty wrapped and unwrapped alike. Interactive TUIs work in neither.
5. Exit code is the child's, with two exceptions: death by signal is reported as
   `128+signum` (bare reports killed-by-signal, visible to `waitpid` but not to `$?`), and
   a spawn/exec failure exits `2` where bash would give `127`.
6. The wrapper installs INT/TERM/HUP/QUIT handlers and forwards them to the child, so it no
   longer dies of those signals itself; a child that traps TERM leaves both alive.
7. The wrapper does not exit when its child does. It drains until both captures reach EOF,
   so a detached descendant holding the inherited pipes keeps it alive — measured at 8.0 s
   of wrapper life after a child that exited in 6 ms. `tail --pid=$!` therefore waits for
   `final(<code>)`, not for the child's exit.

## Why `ps` is not pollable

`agent-tools ps` prints every capture in the session, main thread and subagents alike, as a
current-state listing plus a chronological event log. The event log is cumulative from
session start, so a naive condition such as
`until agent-tools ps | grep -qE 'exit_code":[1-9]'` matches a nonzero exit from hours
earlier and returns immediately. Scoping needs `--task <tool_use_id>`, which selects one
Bash tool call and prints every capture made in it — and an agent does not know the
tool_use_id of a job launched in an earlier call. Hence the marker-file rule in the prompt.

`ps` needs `AGENT_TOOLS_PARENT_DIR` or `--session-id`.

## The kill boundary

A Bash call killed at its `timeout` takes the call's **live descendants** with it, not its
process group — each `&` job already has its own process group, yet a plain `&` child still
dies. Measured with three variants each appending a line per second to its own file, read
after the call returned `Exit code 143`: plain `&` stopped at 10 lines, `setsid --wait`
stopped at 10, bare `setsid` went on from 15 to 23. `setsid --wait` dies because the waiting
intermediate keeps it in the descendant tree; bare `setsid` survives because its double fork
reparents the worker to init first. `&` children spawned inside a subshell that then exits
are orphaned the same way and also survive. `nohup` does not help: it only ignores SIGHUP.

Recording the job's pid needs care when the command is also piped, which the capture makes
attractive: for `cmd | grep -m1 error &`, bash sets `$!` to the **last** stage. Measured:
`sleep 30 | grep -m1 nomatch & echo $!` reports the `grep`, so `tail --pid=$!` returns when
`grep` quits at the first match rather than when the producer finishes.

The guidance stays "let the call return on its own", because that is the only form that
keeps the job reachable through both the status channel and the pid file.

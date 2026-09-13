# `agent-tools run` — status channel and passthrough reference

The system prompt carries the subset of this that changes what an agent types. This file
carries the full grammar, and `scripts/check-prompt-coupling.sh` pins every string here
against its emit site in `agent-tools/src`, so a rename in the source fails the check.

## Delivery

Status is injected as `additionalContext` by hooks on three events, and only those three:
`PostToolUse`, `PostToolUseFailure`, and `UserPromptSubmit` (`settings.json`). There is no
timer and no `Stop`-event injection. An agent is therefore never woken: a status change
becomes visible on its next tool result or on the user's next turn, whichever comes first.
Nothing here blocks, so a job that outlives a single Bash call (max 600000 ms) needs some
other way to be waited on. `--background` prints its wrapper pid, and `timeout <s> tail
--pid=<n> -f /dev/null` blocks on that across calls; `ps`'s default JSON is a current-state
listing and can be polled. Only the `--events` log cannot — see "`ps`" below.

## Block shape

A block opens with a stamped header, `[agent-tools] run status @ HH:MM:SS ±ZZZZ:`, built
once by `report_header` in `hook_post.rs` and used by both delivery channels. The stamp is
taken when the report's lines were measured, not when the header was built, and every
relative figure below it — each `<age>`, each running total — is relative to that instant.
It is there so the block still resolves when it is re-read after a compaction, where "4s
ago" would otherwise anchor to nothing.

Under the header is one line per wrapped process whose status changed since the agent was
last told, except for the ones still running:

```
<name> [<key>] <detail> -> <paths>
```

Children whose key `is_still_running()` — `producing` and `quiet(<bucket>)`, not `exited` —
are collapsed into a single line instead, because a fan-out's running children are
near-identical and the block is size-capped:

```
  still running: [<key>] <name>, <name>; [<key>] <name>  -> agent-tools ps
```

Groups are ordered by key and joined with `; `. The line names every such child rather than
counting them, since a count cannot be honestly retired from the ledger one child at a time.
It carries no pid, no age, no bytes and no capture path: `agent-tools ps` is where a running
child's own detail lives. Where even that one line does not fit the remaining budget, the
block says so instead and the children stay owed: `… N still-running children changed,
omitted for size; they are reported at the next delivery point, or run `agent-tools ps` now`.

A degraded report keeps the bare header without the stamp (`[agent-tools] run status:
unavailable this time (…)`) — it carries no relative figure for a stamp to anchor. It is
still recognizable as status by the `[agent-tools]` prefix it shares with the stamped form,
which is the only cue for it — the prompt teaches the stamped shape, not this one. A block may
also carry non-status lines: `note: report history lost — …`, `note: <dir> could not be
listed …`, and `… N more changed, omitted for size …`.

`BACKGROUNDED:` is emitted by `hook_post.rs` only when a tool response carries
`backgroundTaskId`. Bash returns one for an explicit `run_in_background: true`, and for a
foreground command moved to the background when it outruns its `timeout`; the notice's
`Cause:` field separates those two from a user's Ctrl+B, a turn abort, and a background
taken so a queued message could reach the model — one response field per cause
(`src/chunk-dbb93264.js:215694-215699`), and the notice says the cause is unstated rather
than naming one when no field is set. A command the harness will not background — one
whose first statement's first word is `sleep` (`yzs`, `src/chunk-dbb93264.js:215729`,
against the one-entry list at `:215644`) — is killed at its timeout instead, and no notice
is emitted. Nothing else about the command's shape disqualifies it: measured on 2.1.269,
`echo start; sleep 25` at `timeout: 3000` came back with a `backgroundTaskId` and
`timedOutAfterMs: 3000`.

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

`producing` and `quiet(<bucket>)` reach the agent only through the collapsed `still running:`
line above; the per-child line is for the settled keys and for `exited`. Settled children
take the size budget first, so a block that is running out of room drops the running ones.

## Detail and paths

`<detail>` is `pid <pid>, <timing><age>, <bytes>`. `<pid>` is the child's, or `-` when the
record carries none; `<age>` is `last byte Ns ago` or `no output`; `<bytes>` is `output=NB`
or `out=NB err=NB`. `<timing>` has four arms, and because the `pid` fallback is independent
of them, five shapes are reachable in all:

| Shape | When |
| --- | --- |
| `pid <n>, started <t> (+<d>), <age>, <bytes>` | Still running, so the span is still growing |
| `pid <n>, started <t>, ran <d>, <age>, <bytes>` | The fate is settled and the span is known — the clock stopped at the reap |
| `pid <n>, started <t>, <age>, <bytes>` | A start is recorded but nothing observed an end (`abandoned`) |
| `pid -, started <t>, <age>, <bytes>` | Nothing ever ran, so there is no pid (`spawn-failed`) |
| `pid -, <age>, <bytes>` | The child's own record did not read (`abandoned`) — the record is gone, not the line malformed. `<name>` falls back to the capture directory path on this shape alone |

`<t>` is local `%H:%M:%S`; `<d>` is `Ns`, `Nm0Ss` or `Nh0Mm`.
`<paths>` names the capture file: `<dir>/output` when the streams were merged, else the one
brace form `<dir>/{stdout,stderr}` — a rendered line carries that compact shape, not two
separate names, though the JSON `capture` field does list both real paths. The two pids on a line differ on purpose: `<pid>` is the
child's, while `<dir>` is named for the wrapper's — e.g. `pid 1720919 … -> …/1720906/output`.

Two bracket groups may follow the detail, and both are absent from an ordinary run. They
hold facts about the run, not a second key:

- `[streams split: <why>; downstream closed; drain capped; capture capped; capture failed: <err>]`
  — any subset, in that order — says how the run differed from bare. `drain capped`
  and `capture capped` are the two bounds' markers and are mutually exclusive per run: the
  first is the post-close drain's, the second a backgrounded run's. `capture capped` in fact
  admits only one companion, `capture failed`: it fires only for a backgrounded run, which
  always merges its streams (so `streams split` cannot apply) and forwards to a sink that
  cannot refuse a write (so `downstream closed` cannot either).
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

## `--background`

All of the above describes a run the caller waits for. `--background` is the other mode, and
it forwards nothing:

```
agent-tools run --background --desc "<what>" <cmd> <args..>
# <capture_dir>  wrapper pid <n>  child pid <n>
```

- **Detach.** The process forks once; the forked child calls `setsid`, becomes the wrapper,
  and runs the command, while the original process blocks only until that child reports it
  has started, prints the line, and exits. The wrapper is therefore an orphan at PPID 1,
  with PGID and session equal to its own pid. The fork is refused if the process already has
  more than one thread, and it happens before any tokio runtime exists.
- **The start line** is the whole of what the caller is told, and it is the command's own
  stdout, carrying no `[agent-tools]` prefix — its shape is the only thing separating it
  from a child's first line of output. Two spaces before each `pid` field.
- **Exit code** is `0` for started, not for succeeded: the child's `exit 3` lives in
  `meta.json` and reaches the agent later as `final(3)`. A start that never happened prints
  no line, exits `2`, and puts the reason on stderr.
- **Streams.** The original process `dup2`s stdout and stderr to `/dev/null`, and stdin too
  if it is a tty — so `< file` and heredocs still feed the child. Both of the child's streams
  go to one self-owned pipe and land in `<dir>/output`; `stdout` and `stderr` are absent, not
  empty.
- **The capture bound** is the same 256 MiB `--drain-cap-bytes` default, but counted from the
  first byte rather than from a downstream's refusal, there being no downstream that could
  refuse. At the bound the read end is dropped, the child takes `SIGPIPE` and reaps as `141`,
  and the line shows `capture capped` — never `drain capped`. The stderr notice for it is
  emitted, and goes to `/dev/null`.

## `ps`

`agent-tools ps` reports this session's wrapped runs, main thread and subagents alike.

`--format` defaults to `json`: an envelope of `now`, `session`, `live` and `withheld`, with
`settled` present only under `--all` — absent, rather than an empty array that could be
mistaken for "nothing finished". Only live captures are listed by default, because a long
session is mostly settled ones and their detail displaces what is still running from a
size-limited tool result; 30 terminal captures with nothing live render 193 bytes by default
against 15,516 with `--all`. The withheld ones stay counted by key under `withheld`, with
`retrieve_with: "agent-tools ps --all"`, so none of them vanishes silently.

`--format text` is the human-readable rendering and the only one that can carry `--events`,
the cumulative chronological event log; at any other format the flag is ignored with a note
on stderr rather than parsing into silence. `--format statusline` is the one-line form
`statusline.sh` consumes, and prints zero bytes when nothing is live.

No format commits the ledger, so reading `ps` never retires a change the push report still
owes the agent.

Polling needs care in one direction only. The `--events` log is cumulative from session
start, so a naive `until agent-tools ps --format text --events | grep -qE 'exit_code":[1-9]'`
matches a nonzero exit from hours earlier and returns immediately. The default JSON is a
current-state listing and does not have that problem — `live` holds exactly what is running
now. Scoping to one Bash tool call needs `--task <tool_use_id>`, which an agent does not know
for a job launched in an earlier call; scoping to one job is done by its capture directory,
which `--background` printed.

`ps` resolves its session from `--session-id`, else `AGENT_TOOLS_PARENT_DIR`, else bare
`CLAUDE_CODE_SESSION_ID` — that last fallback is what lets `! agent-tools ps` answer from a
shell where no hook ran to set a scope. It also requires the scope to sit under the state
root `~/.claude/agent-tools`; a `run` pointed elsewhere captures fine but `ps` will not read it.

## The kill boundary

A Bash call killed at its `timeout` takes the call's **live descendants** with it, not its
process group and not its session. The tool's shell runs with job control on (`$-` contains
`m`), so each `&` job already has a process group of its own — measured, shell `pgid=2524015`
against its `&` child's `pgid=2524031` — and the child dies anyway. Nor is it the session
boundary: `setsid --wait` leaves its worker in a session of its own and the worker dies
too. Measured with three variants each appending a line per second to its own file, read
after the call returned `Exit code 143`: plain `&` stopped at 10 lines, `setsid --wait`
stopped at 10, bare `setsid` went on from 15 to 23. `setsid --wait` dies because the waiting
intermediate keeps it in the descendant tree; bare `setsid` survives because its double fork
reparents the worker to init first. `&` children spawned inside a subshell that then exits
are orphaned the same way and also survive. `nohup` does not help: it only ignores SIGHUP.

Recording the job's pid needs care when the command is also piped, which the capture makes
attractive: for `cmd | grep -m1 error &`, bash sets `$!` to the **last** stage. Measured:
`sleep 30 | grep -m1 nomatch & echo $!` reports the `grep`, so `tail --pid=$!` returns when
`grep` quits at the first match rather than when the producer finishes.

`agent-tools run --background` escapes by the same route as bare `setsid`, and deliberately:
its original process exits as soon as the forked wrapper reports a start, so the wrapper is
already reparented to init by the time the call returns, and out of the tree the kill walks.
The new session it also acquires is not what saves it — `setsid --wait` has one and dies.

A `TaskStop` on a backgrounded call walks the same tree. Measured on 2.1.269: a backgrounded
Bash call ran `agent-tools run --background timeout 907 tail -f /dev/null` and then held
itself open with a foreground `timeout 100`; `TaskStop` on that task killed the call's shell
and the foreground `timeout`, and the wrapper and its child were still running afterwards.
2.1.257's release notes claim to have closed the `setsid` escape on task stop and on Claude
Code exit; only the exit half is unmeasured.

So for a job that must outlive its call, `--background` is the form to reach for: it needs no
bounded wait, and it keeps the job reachable through the status channel, through `ps`, and
through the wrapper pid on its start line. For a bare `&` the guidance stays "let the call
return on its own", which is the only form that keeps such a job reachable at all.

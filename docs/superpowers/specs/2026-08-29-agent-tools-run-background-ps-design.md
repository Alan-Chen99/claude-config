# `agent-tools run` — starting, the pull path, and the user's channels

Status: draft, 2026-08-29
Amends `2026-08-26-agent-tools-run-design.md`. That spec's invariant, status keys, scope
rule and passthrough tiers are unchanged and govern here; this one adds a way to start a
child that outlives its caller, makes the pull path data, and gives the user two channels
of their own.
Measurements below were taken in one session on 2026-08-29 and each names the command that
produced it.

## Purpose

The 2026-08-26 spec makes a child's **fate** knowable. It says nothing about its **birth**,
and the gap is not academic: the only way to start a child that outlived its tool call was
the shell's `&`, which destroys the exit code and can leave nothing on disk for any reader
to find. A child that never started is then indistinguishable from one that started fine.
`&` does not even buy what it appears to — it survives the call *returning*, but is killed
with the call when the call is killed (measured under Lifetime below).

Four further gaps share a cause. The pull path, the timestamps, the size of a report and the
user's own view were all shaped for an agent reading prose, when what reads them is a
program, a compaction survivor, a context window, and a person glancing at a status bar.

## Starting is synchronous

`run --background` splits one invocation into two phases with a hard boundary.

**The synchronous phase runs while the caller is still reading.** In order: resolve the
scope, create the capture directory, open `output`, write `meta.json`, spawn the child.

- **A failure anywhere up to and including the spawn is loud and total.** The reason goes to
  stderr while the caller can still receive it, the exit status is non-zero, and no child is
  running. Nothing is left for a later reader to discover, because there is nothing to find.
- **Success prints one line and one line only** — the capture directory, the wrapper pid and
  the child pid — then detaches via `setsid(2)` and exits 0.
- **The capture exists on disk before the call returns.** This is what `&` cannot promise:
  under `&` the wrapper's publish and the `PostToolUse` scan are unordered, so the first
  `producing` line can be missed entirely.

**The detached phase runs with no caller.** Tee to `output`, reap, drain, record `final`.

### Exit 0 means started, not succeeded

This is the one place `--background` knowingly breaks the guarantee that the wrapper returns
the child's exit status. It cannot both return that status and return promptly. The child's
status reaches the caller through the status channel and nowhere else, and `--background`
is the marker that says so.

### Streams

**No forwarding.** Both of the child's streams go to one appending regular file, `output`,
and nowhere else.

This is not an exception to the merge rule but its `both pipes, same destination` case, held
by construction rather than inferred: the wrapper makes the pipe and hands the child both
write ends, so no foreign descriptor participates and nothing can be misrouted. The appending
capture file is not what makes it sound — the tee opens that file the same way in the split
case too, twice.

**It is forced rather than decided, and that is the point.** By the time a detached wrapper's
child produces a byte, the wrapper's own stdout and stderr are one `/dev/null`, opened
`O_RDWR` without `O_APPEND`. Measured, `decide_merge` answers `Split("same file, but not both
appending")` for exactly that shape — the character-device carve-out the rule states
deliberately, since character devices are not uniformly unseekable. So asking the rule would
split every backgrounded capture. The decisive cost of that is not only the lost interleaving:
`status::notes` renders any non-default split condition, so every backgrounded run would carry
`streams split: backgrounded: wrapper owns the destination` — "the streams were split because
nobody was watching", which explains nothing and would appear on every line.

`meta.merge` records `backgrounded: wrapper owns the destination`. `forward_closed` becomes
structurally impossible for a backgrounded child, which is the point — under `&` it fires on
nearly every run and a note that is always there stops being read.

The cost is real and is accepted: **stderr is no longer separable** from stdout for a
backgrounded child. The interleaving is worth more than the separation, because it is the
interleaving that says which command produced which diagnostic, and nothing can recover it
afterwards.

### stdin

- **Not a tty: inherited.** The descriptor survives `setsid`. Measured for the case most likely
  to break — a heredoc read after the parent has moved on:

  ```
  setsid sh -c 'sleep 1; cat > /tmp/heredoc-probe-x9.txt' <<'EOF'
  payload-line-x9
  EOF
  → parent moved on immediately; two seconds later the file held payload-line-x9
  ```

- **A tty: `/dev/null`.** A detached process must not read the terminal.

### Lifetime

Measured, by launching three detach styles from one Bash tool call with a 4 s timeout and
letting the call overrun it:

```
setsid (sleep 12061): SURVIVED  pid=381455 ppid=1 pgid=381455 sess=381455
nohup  (sleep 12062): killed
bare & (sleep 12063): killed
```

A backgrounded child therefore survives the call returning and the call's timeout kill. The
survivor was reparented to init in a session of its own, which is the mechanism; survival
past the Claude Code process's own exit follows from that mechanism but was not separately
measured.

**The system prompt is wrong about this today.** The backgrounding bullet in
`sys_prompt/alan-default-next.md` states that the timeout kill takes `&`, `nohup` and
`setsid` alike. It does not take `setsid`. That bullet is rewritten around `--background`.

Detaching costs one `setsid(2)` call in the wrapper's own process. A shell-level probe
spawning a whole separate `setsid` process 200 times took 180–186 ms, against 256–282 ms for
200 `env true`. That compares two different binaries and so isolates nothing; it bounds the
question, which is all it needs to do — even the far more expensive process form costs under
a millisecond, and the specified form is a syscall.

### Composition

`--background` composes with `--desc`, `--hide-cmdline` and `--drain-cap-bytes` unchanged.
It is the phase structure that differs, not what the wrapper records or how it names itself.

## The pull path is data

`agent-tools ps` prints one JSON object by default, carries only what is running, and leaves
the event log out.

```json
{"now":"2026-08-29T14:05:23.114+00:00","session":"f6132038-…",
 "live":[{"name":"build","key":"producing","origin":"tool","agent":null,
          "tool_use_id":"toolu_01AbC…","wrapper_pid":4709,"child_pid":4711,
          "started_at":"2026-08-29T14:02:11.412+00:00","elapsed_s":191.7,
          "last_byte_at":"2026-08-29T14:05:19.032+00:00","last_byte_s":4.1,
          "bytes":8134,"capture":["…/4709/output"],"notes":[],"orphaned":false}],
 "withheld":{"by_key":{"final(0)":12,"final(1)":3,"final(143)":1,"spawn-failed":1},
             "retrieve_with":"agent-tools ps --all"}}
```

**`capture` is a list even when it holds one path.** The rendered line writes a split
capture as `<dir>/{stdout,stderr}`, which is shell brace expansion — fine for a human
reading a line, unusable to a program, which cannot open it. A consumer that had to
special-case a string against a list would need to know the merge decision in order to parse
the field that reports it. One entry for a merged capture, two for a split one.

**`stat_errors` is present when a capture file could not be stat'd** for any reason other
than not existing yet, and absent otherwise. Without it a broken filesystem reads as a
healthy idle child — zero bytes, no last byte — which is the divergence between push and
pull that the shared record exists to prevent, since the rendered line carries the same fact
as `[stat failed: …]`.

The values above are illustrative. Measured counts from a real session appear under
"Why this size, measured".

- **Live is defined by the key, not by a new rule.** Live is any key the 2026-08-26 spec does
  not call terminal: `producing`, `quiet(*)`, `exited(*)`. Terminal is `final(*)`,
  `abandoned`, `spawn-failed(*)`.
- **A live record carries `elapsed_s`; a terminal one carries `ran_s` instead.** Never both,
  and never `elapsed_s` on a terminal child, whose clock stopped at the reap. The field
  present is itself the statement of which kind of record this is.
- **What was withheld is broken down by key, not counted.** A bare total hides the one thing a
  reader most needs from a set of terminal children — that one of them is a `spawn-failed`.
- **`by_key` groups on the key, except that `spawn-failed` drops its message.** `final(0)` and
  `final(1)` are worth separating and there are few of them; a spawn error is free text, so
  grouping on the full key would let one distinct message per child into a field whose whole
  purpose is to be small. The messages are retrievable through `--all`.
- **`notes` is an array**, carrying as data what the rendered line carries inside `[…]`:
  a forced split and its condition, a closed forward, a capped drain, a failed capture.
- **`origin` distinguishes `tool` from `user-shell`**, and `tool_use_id` is `null` for the
  latter rather than fabricated.
- **`orphaned` is true when the session that started the child is gone.** The wrapper records
  `CLAUDE_PID` **and that process's start ticks** at start; `ps` compares both. Information,
  not action — nothing is killed automatically, and this spec still does no garbage
  collection. `CLAUDE_PID` was observed in a main-thread Bash shell and in a subagent's; its
  presence under `!` is reported by the v2.1.235 decompile but was not directly observed.

  **The ticks are not optional.** A pid alone is recyclable, and measurably so: this host's
  `pid_max` is 4,194,304, and a live process was found at pid 4,100,738 started 5.8 hours
  ago while new pids were allocating around 1.92M — the counter had wrapped inside that
  window. A backgrounded wrapper's lifetime is unbounded, so pid-only comparison fails in
  exactly the case the field exists for: the session exits, the pid space wraps, an
  unrelated process takes the number, and the leaked child reports as belonging to a live
  session forever. `procstat::is_alive` already rejects a recycled pid for wrappers; a
  session gets the same treatment, and gets the zombie exclusion with it.

  **Three answers, not two.** `Some(true)` when the recorded session is gone, `Some(false)`
  when it is the same process that was recorded, and **`null` when the record cannot support
  the question** — no session recorded, or a pid recorded without its ticks. "The session is
  gone", "the session is alive" and "nobody looked" are different answers, and a record that
  names a pid it cannot verify supports the third, not the second.

  **Orphanhood is a fact about the session, not about the child.** Every record carries the
  field, terminal ones included, so a child that finished normally hours ago reports
  `orphaned: true` once its session ends — correct, and not a leak. The leak is the pair:
  `orphaned == Some(true)` on a child that is not terminal.

Flags: `--format <json|text|statusline>` selects the renderer and defaults to `json` — `text`
is today's grouped-by-tool-use human layout, `statusline` is the single line specified below;
`--all` includes terminal children; `--events` restores the chronological event log;
`--task <id>` and `--session-id <id>` are unchanged.

### Why this size, measured

On the largest session on disk — 102 captures — the current `ps` prints:

```
ps total:        87712 bytes, 814 lines, 8 ms
events section:  47015 bytes (53%)
capture blocks:  40697 bytes (47%)
key distribution: 80 final(0), 8 final(1), 6 final(143), 6 final(137), 1 final(255), 1 final(23)
```

Every one of the 102 was terminal. Nothing was running. Under this spec that session's `ps`
is the envelope and an empty `live` array — roughly 250 bytes, against 87,712.

The 8 ms is worth stating too: **`ps` is not slow and never was.** Its problem was that it
answered a question nobody asked.

## Time is stated, not implied

Every rendered time is **local time**. The current renderer formats UTC instants with
`%H:%M:%S%.3f` and no zone, so a reader correlating `started: 00:22:24.263` against `date`
is wrong by the offset and has no way to see it.

- **A pushed report carries one absolute stamp in its header**: `[agent-tools] run status @
  14:05:23 +0000:`. That stamp is what makes every relative figure beneath it resolvable when
  the line is re-read after a compaction, which is the condition report lines are written for.
- **A line carries the start and a duration.** The duration means time-so-far while the child
  is live and total run time once it is terminal. **The clock stops at the reap**: a `final(0)`
  from an hour ago says it ran 4m02s, not that 67 minutes have elapsed.
- **Persisted forms carry the offset; the statusline does not.** A report line outlives the
  terminal it was printed to, so it states `+0000`. The statusline is read in situ and states
  `@14:05`. Both render local time — that is the fix. The offset makes the persisted form
  safe; it is not what makes either of them local.
- **`ps` carries both forms**: ISO-8601 with offset, and numeric seconds, so a consumer picks
  rather than parses.

## A report shrinks by collapsing what is still running

- **Every terminal change gets its own full detail line.** That is what an agent has to act on,
  and it is never traded away for size.
- **Children that are merely still running collapse to one line**, which **names each child
  under its key**:

```
  still running: [producing] a, b, c, d; [quiet(30s)] h, m  -> agent-tools ps
```

Naming under the key is not decoration. Counts alone — "17 producing, 2 quiet" — would tell
the agent that two children are quiet without telling it which, and the ledger could then not
honestly retire them: a key would be recorded as reported when the child holding it was never
named. Naming keeps the invariant exact at a cost of a few characters.

- **The existing budget and drop-and-count tail remain** as the outer backstop, unchanged. When
  the collapsed line itself would exceed the budget, it falls back to counts and the children
  it could not name stay pending, since an unnamed child must not be recorded as told.

A fan-out of twenty wrapped commands currently costs twenty near-identical `producing` lines,
then twenty near-identical `final(0)` lines. Under this rule the first becomes one line.

## The user's shell is a first-class caller

The `!` shell shortcut fires **no** `PreToolUse`, **no** `PostToolUse` and **no**
`UserPromptSubmit` hook. `processBashCommand.tsx:85-88` calls `BashTool.call(...)` directly,
and the only `runPreToolUseHooks` / `runPostToolUseHooks` call sites in the tree are
`toolExecution.ts:800` and `:1483`, which that path never enters; `executeUserPromptSubmitHooks`
has one call site, `processUserInput.ts:182`, reached only when `shouldQuery` is true, which
bash mode is not. Read in `/repos/claude-code-src` (v2.1.88); a subagent reported the same
structure in the v2.1.235 decompile.

So `AGENT_TOOLS_PARENT_DIR` is never set there and `run` fails outright.

- **Scope falls back to `CLAUDE_CODE_SESSION_ID`.** It is exported into every shell and holds
  the same id `AGENT_TOOLS_PARENT_DIR` is built from — verified by comparing the two in one
  session. Captures land in `<state_root>/<session>/user-shell/<wrapper_pid>/`.
- **A `!`-started child is a main-thread citizen.** The agent's next delivery point reports it
  like any other child, so a build started from the shell shortcut tells the agent when it
  finishes. The consequence is accepted: what the user types at `!` can steer the agent's turn.
- **The fallback path never commits the ledger.** Whether a `!` command's output reaches the
  model depends on the `respondToBashCommands` setting, which the binary cannot observe.
  Retiring a status the agent may never have seen would break the invariant, so this path reads
  and never marks-as-told. The same rule binds the statusline, for the same reason.

### The ambiguity that cannot be removed

A subagent's shell exports the **identical** thirteen-variable set as the main thread's, with
`CLAUDE_CODE_SESSION_ID` holding the **same** session id; only `AGENT_TOOLS_PARENT_DIR` differs,
by carrying the agent id. Measured by dumping both.

Nothing therefore distinguishes "the user typed `!`" from "a subagent whose `PreToolUse` hook
failed". Both present an unset `AGENT_TOOLS_PARENT_DIR` and a session id.

The design does not hide this. Both land in `user-shell`, and `origin: "user-shell"` is honest
in both cases, because what it asserts is exactly what was observed: **no hook set a scope.**
A subagent's child is then misattributed to the main thread — over-reported, never lost, which
is the direction the invariant already prefers.

## The statusline carries what is running

A line, omitted entirely when nothing is running so the bar never grows a permanently empty row:

```
▶ @14:05 build 3m11s · tests 1m02s · ~deploy 12m04s  (+2)
```

- `@14:05` is local time, hoisted once. **The statusline has no timer.** It re-renders only on
  a new assistant message, a permission-mode, vim-mode or model change (`StatusLine.tsx:237-249`,
  debounced 300 ms), so its figures freeze the moment the agent goes idle — which is exactly
  when a person is most likely to be reading them. The stamp is what makes a frozen line
  self-describing rather than merely wrong.
- `~` marks a `quiet(*)` child: alive, producing nothing.
- `(+2)` is the overflow. Three names, each capped at about fourteen characters. **The cap is
  fixed, not computed**: terminal width is absent from the statusline payload, and `tput cols`
  cannot supply it. It does not fail against the pipe the command's stdout is — it returns
  `80` and exits 0, which is worse than failing, because a plausible wrong width would size
  the line confidently and wrongly. Measured: `tput cols` in that position printed `80` with
  `COLUMNS` unset and stdout on `pipe:[664512944]`.
- **Scope is the whole session**, subagent children included. A person wants to know what is
  running, not who started it.

**Mechanism.** `agent-tools ps --format statusline` — one process, no `jq`, and the formatting
rules live in Rust with tests rather than in shell. `session_id` comes straight from the
payload: `createBaseHookInput()` puts it top-level (`hooks.ts:301-313`). The budget is 5000 ms
(`hooks.ts:4587`) against 8 ms, which is the whole of today's `ps` over 102 captures and so an
upper bound on a renderer that reads only the live ones.

**Its failure is visible.** On error or timeout it emits `▶ ?`, never nothing. An empty line
and a broken line are otherwise identical, and silence reads as "nothing is running" — the
failure this design forbids everywhere else.

## Three renderers, one derivation

Push report, `ps`, and statusline are three views of one status. **They derive from the same
fields and none of them re-computes a status of its own**, or the guarantee that push and pull
never describe one child differently becomes a coincidence maintained by hand.

## What this does not close

**`--background` does not change when a completion is reported.** That is still the next
delivery point — the next tool result, or the user's next turn — and no flag on `run` can
change it, because the agent does not run in between.

What it does close is the other half: under `&` the first `producing` line can be lost to the
publish race and a failed start can vanish entirely. Under `--background` neither can happen.

Closing the completion half needs a new delivery point — a `Stop` hook that blocks once on a
pending terminal change, or an explicit `agent-tools wait`. **Neither is in this spec**, and
neither should be adopted without deciding what a blocked turn costs the person waiting on it.

For the record, the latency itself is not the problem. Measured on
`agent-tools run --desc bg-probe-a3f9 sleep 4 &`:

```
started -> reaped:   4.001 s
reaped  -> drained:  0.0003 s
```

and the `final(0)` line landed in the very next tool result. The scan that produces it costs
4–7 ms against a 5000 ms budget on the 102-capture session.

## Deviations closed and opened

`2026-08-26-agent-tools-run-design.md` lists three open deviations. This spec closes one:

| Clause | Was | Now |
| --- | --- | --- |
| the pull path's output | F15's size half — `ps` showed every capture the session ever made — and the unmet clause that its output be fields rather than a rendered string | closed by live-only-by-default and the JSON envelope |
| readable beside the key, for a live child | F16 | unchanged, still open |
| never reported terminal while starting | F4's read-order half | unchanged, still open |

Newly accepted, and not deviations:

- **A backgrounded wrapper outlives its session and nothing collects it.** Garbage collection is
  out of scope in the 2026-08-26 spec, and `--background` makes orphans likely where they were
  rare. `orphaned` in `ps` is the whole mitigation.
- **A backgrounded wrapper does not return its child's exit status.** Stated above.
- **A backgrounded child's stderr is not separable.** Stated above.
- **A subagent whose hook failed is attributed to `user-shell`.** Stated above.
- **A backgrounded capture has no size bound.** The drain bound arms only once a downstream
  has stopped accepting writes; a backgrounded run has no downstream, so it never arms, and
  `drain_capped` is inert for the life of the child. This is the same shape any forwarded run
  has while its caller keeps reading — normal operation is uncapped by design — but detaching
  removes the two things that used to end it in practice: the caller going away, and the
  wrapper dying with the call. A wrapped `yes` started with `--background` writes until the
  disk is full. `ps` reports the growing byte count, and that is the whole of the mitigation.

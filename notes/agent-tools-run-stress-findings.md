# `agent-tools run` stress-test findings

Stress test run 2026-08-25 against a release build of `/root/claude-config-work` at
`18d81e5` — byte-identical sources to the installed checkout
(`diff -rq /repos/claude-config/agent-tools/src /root/claude-config-work/agent-tools/src`
was empty). Target spec:
`docs/superpowers/specs/2026-08-24-agent-tools-run-observability-design.md`.

**The observability design holds.** Every clause of the spec that could be falsified
in this environment was falsification-tested and survived: the ledger under
contention, the report budget, all four quiet buckets, flap collapse, subagent
isolation, the detached-daemon lifecycle, and the invariant itself. See
[Verified clean](#verified-clean).

**What breaks is the passthrough contract**, plus two failure paths that lose data
without saying so. The tool description in `sys_prompt/alan-default-next.md:170`
promises:

> The wrapper passes the child's stdout and stderr through byte-for-byte and
> propagates the child's exit code. Pipelines, redirections, `2>&1`, exit-status
> checks, and downstream filters behave exactly as if you had run the bare command.

Three of those clauses are false (F1, F2, F3). The last sentence is worse than false:
"behave exactly as if you had run the bare command" names a property no tee-based
wrapper can have. See [Structurally unachievable](#structurally-unachievable).

| ID | Severity | Finding | Site |
| --- | --- | --- | --- |
| [F1](#f1) | critical | a wrapped producer never stops when its downstream consumer exits | `capture.rs:46` |
| [F3](#f3) | critical | every wrapped command's merged output is reordered, and long lines are corrupted mid-line | `capture.rs:37` + the two-pipe tee |
| [F2](#f2) | high | a capture-file write failure silently truncates the caller's output and kills the child | `run.rs:165-166` |
| [F4](#f4) | medium | a child that is merely starting can be reported `abandoned`, a terminal key | `run.rs:52` before `run.rs:67` |
| [F5](#f5) | medium | the ledger commits before the report prints, so a failed write retires changes forever | `hook_post.rs:207` before `:71` |
| [F6](#f6) | medium | `agent-tools ps` has no output bound | `ps.rs:265` |
| [F7](#f7) | low | one malformed line in `events.jsonl` silently drops every event in that file | `ps.rs:114` |
| [F8](#f8) | low | a held scope flock stalls every delivery point, with no timeout | `ledger.rs:99` |
| [F9](#f9) | low | `pgrep -f` / `pkill -f` aimed at a wrapped process also match the wrapper | `run.rs:29-34` (by design) |
| [F10](#f10) | low | a relative `AGENT_TOOLS_PARENT_DIR` is misdiagnosed as "not set" | `run.rs:36` |
| [F11](#f11) | low | the `BACKGROUNDED:` notice and the status header are joined onto one line | `hook_post.rs:68` |
| [F12](#f12) | low | the wrapper absorbs SIGTERM and SIGINT when the child ignores them | `signals.rs:18-30` |
| [F13](#f13) | medium | `ps` hides the capture that `hook-post` reports as `abandoned` | `ps.rs:233-236` |
| [F14](#f14) | critical | a multi-byte character in `--desc` discards the command, leaving no trace on disk | `procname.rs:42-48` + `procstat.rs:25` |
| [F15](#f15) | medium | `ps` output grows with session history and is ordered by an identifier uncorrelated with time | `ps.rs:49-54` |

Findings after the original run — F13, F14, F15, and the revised F3 — were added
2026-08-26 while scoping the fixes, under the same conditions. Their reproductions are
quoted inline.

---

## F1

### A wrapped producer never stops when its downstream consumer exits

`capture.rs:46` discards the result of the forward write:

```rust
let _ = forward.write_all(chunk).await;
```

When a downstream filter closes the pipe, that write fails with `EPIPE` (Rust sets
`SIGPIPE` to `SIG_IGN` at startup, so it is an error and not a signal). The error is
dropped, the read loop continues, and the wrapper keeps draining the child — so the
child never sees a broken pipe and never stops. Nothing caps the capture file, so
this is bounded only by the disk.

```
$ yes | head -1                                     8 ms
$ agent-tools run yes | head -1                     killed at 5 s
                                                    capture file 2,117,681,152 B (~400 MB/s)

$ grep pattern-hit corpus | head -3                 2 ms      (corpus is 73,888,890 B)
$ agent-tools run grep pattern-hit corpus | head -3 218 ms
                                                    capture file 73,888,890 B — the entire corpus

$ agent-tools run cat corpus | grep -q "line 5 "    whole 74 MB read and captured

exit status under `set -o pipefail`
  bare      yes | head -1   -> 141 (SIGPIPE)
  wrapped   yes | head -1   -> never exits
```

Both sides wrapped behaves the same way: `agent-tools run yes | agent-tools run head -1`
left the consumer at `final(0)` after 2 B while the producer wrote 502,956,032 B and
had to be killed.

`| head`, `| grep -q` and a quit pager are ordinary agent idioms, and a Bash call that
hits its timeout is backgrounded rather than killed, so the spin continues after the
tool call returns.

**Fix direction:** on a `BrokenPipe` forward error, stop the tee and drop the read end
so the child receives `EPIPE`/`SIGPIPE` as it would bare. Whether the capture should
also stop or continue to a file-only tail is a design choice; discarding the error is
not. The spec settles that choice: stop forwarding, keep capturing under a bounded
post-close drain, and drop the read end at the cap.

## F2

### A capture-file write failure silently truncates the caller's output and kills the child

`capture.rs:45` propagates a capture-write error out of `tee`, and `run.rs:165-166`
discards it:

```rust
let _ = stdout_tee.await;
let _ = stderr_tee.await;
```

Once the tee task is gone nothing drains the pipe, so the child dies of `SIGPIPE`.
The caller's stream is cut mid-line, the report names an exit status caused by the
wrapper's own failure, and no diagnostic is emitted anywhere.

Injected with `RLIMIT_FSIZE` (`ulimit -f 8`, `trap "" XFSZ` so the limit surfaces as
`EFBIG` instead of killing the process):

```
child produced        134,893 B
forwarded to caller     8,192 B   last line "line-252-padding-"  (cut mid-line)
captured                8,192 B
wrapper exit status     141       = SIGPIPE, inflicted by the wrapper's own failure
wrapper stderr          (empty)
report                  fsize-capped [final(141)] ... out=8192B
```

`final(141)` is a plausible and wrong story: it reads as "the command died of SIGPIPE".

Disk-full is the realistic trigger — and F1 is a mechanism that produces disk-full at
400 MB/s. The two compound.

## F3

### Every wrapped command's merged output is reordered, and long lines are corrupted

**Revised 2026-08-26.** The original entry scoped this to `2>&1` and to reordering.
Both halves were too narrow.

**It is not `2>&1`-specific.** The Claude Code Bash tool already gives fd 1 and fd 2
the same file, so every wrapped command is affected whether or not the agent writes a
redirection. Measured with a probe that writes its result to a file — `$(readlink …)`
runs inside command substitution, which replaces fd 1 and reports the wrong answer:

```
                          fd1                         fd2                        same
plain (cc bash tool)      …/tasks/bs7ii47ub.output    …/tasks/bs7ii47ub.output   YES
2>&1 | cat                pipe:[618105766]            pipe:[618105766]           YES
| cat, no 2>&1            pipe:[618105769]            …/tasks/….output           no
```

#### Reordering — the mild half

With no pipes and no redirection anywhere:

```
bare     OUT1 ERR1 OUT2 ERR2 OUT3 ERR3 OUT4 ERR4
wrapped  OUT1 ERR1 ERR2 ERR3 ERR4 OUT2 OUT3 OUT4      (3 of 3 runs)
```

It only bites when the child's two writes land close together. The threshold is sharp:

```
gap between writes      out of place
0                       30/60
10 us                    6/60
50 us                    0/60
>=100 us                 0/60
```

A child doing real work between lines is already exact. Every earlier demonstration in
this file used a tight loop, which is why the effect looked universal.

#### Mid-line splicing — the severe half

A line longer than the 8192-byte read buffer (`capture.rs:37`) is forwarded as several
`write` syscalls, and on the `new_multi_thread` runtime (`main.rs:385`) the other
stream's write lands between them. Bare never does this: the child's write reaches the
shared file description as one syscall and the kernel's `f_pos_lock` serializes it.

```
                                             bare              wrapped
12 KB lines, 2,000 stderr lines      200 lines, 0 splices   228 lines, 28 splices  (14%)
5 MB line,  20,000 stderr lines        1 line,  0 splices   583 lines, 582 splices

splice offsets: exactly 8191/8192      e.g.  ...OOOOOOOOOOOOOOOOOOOOE100\nE10
```

This is the more serious failure and the more likely one. A 12 KB line is an ordinary
compile command or log record, and corruption is unrecoverable downstream — `grep`,
`jq`, and log parsers all see a garbage record — whereas reordering leaves every line
intact.

Detecting it requires *forcing* it: 20 KB lines with only 40 stderr writes produce zero
splices and would support a false "cannot happen" conclusion. The other stream needs a
high concurrent write rate.

#### Both halves come from splitting the streams, and giving the child one pipe closes both

Measured 2026-08-26. "merged" gives the child a single pipe for fd 1 and fd 2; "bare"
gives fd 1 and fd 2 one file description, which is what the Bash tool does.

A child whose writes are serialized — one `write` in flight at a time, the ordinary
case — 200 lines of 12,001 B interleaved with 2,000 short stderr lines:

```
             spliced   misordered
bare              0      0/2200
two pipes       202   1997/2200
merged            0      0/2200
```

A child with two concurrent writers, same volumes:

```
bare -> file          0
bare -> pipe        40-62      (consumer doing the same per-chunk work as capture.rs)
merged             41-73
two pipes          79
```

The residual is not the wrapper's doing. A plain shell pipeline with no `agent-tools`
anywhere splices identically, because a write above `PIPE_BUF` (4096 B) is not atomic
once the pipe fills, whereas a shared regular file is serialized by `f_pos_lock`. That
belongs in [Structurally unachievable](#structurally-unachievable): inserting any pipe
caps write atomicity, and only the destination being a file ever exceeded it.

Splice offsets separate the two mechanisms — two pipes cluster at 8192, the read buffer
at `capture.rs:37`, across 50 distinct offsets; merged clusters at 3812/3813, the pipe
filling mid-write:

```
two pipes  most common: [(8192, 21), (4380, 2), (8760, 2), ...]  distinct: 50
merged     most common: [(3812, 30), (3813, 20), (8192, 3)]      distinct: 4
```

Enlarging the pipe attacks only the merged mechanism and does not close it — with a tee
that also writes a capture file, 3 runs each: 54-73 at 64 KB, 25-37 at 256 KB, 1-18 at
the 1 MB maximum.

**Fix direction:** give the child one pipe for both streams. Scoped here as an opt-in
`--merge`; the spec instead decides from the caller's own fds and adds no flag, because
every case it merges is provably indistinguishable from bare. Specified in
`docs/superpowers/specs/2026-08-26-agent-tools-run-passthrough-and-fix-scope-design.md`.

## F4

### A child that is merely starting can be reported `abandoned`, a terminal key

`run.rs:52` creates the capture directory; `run.rs:67` writes the first `meta.json`.
A scan landing between them reads no meta and `status.rs:92-102` derives `abandoned` —
which the spec's key table marks terminal and the system prompt teaches as
"the capture is complete and the child process's fate is unknown".

Window measured directly:

```
inotify on IN_CREATE of a capture dir, 600 wrapper starts
  meta.json absent at that instant:            364 / 600  (61%)

strace -tt on one wrapper start
  18:00:17.204520  mkdir(".../toolu_W/548879")             returns
  18:00:17.204765  rename("meta.json.tmp" -> "meta.json")  returns
                                          245 us  (traced; ~0.1 ms untraced)
```

End-to-end consequence, with a poller loop hammering `hook-post` under 24-way CPU load:

```
3,000 wrapper starts, ONE serialized poller   1 child reported past a terminal key
4,000 wrapper starts, 8 pollers               2 children

the reported pair, verbatim:
  .../toolu_TC/482799 [abandoned] pid -, no output, out=0B err=0B
  desc14              [final(0)]  pid 482878, no output, out=0B err=0B
```

The path-as-name and `pid -` identify the mechanism precisely: `read_meta` failed, so
`Status.meta` was `None` and `status.rs:131` fell back to the directory path. That is
the mkdir gap, not a time-of-check race inside `derive`.

Ordering caveat that matters when reproducing: with several concurrent pollers the
order a harness thread records a line is *not* the order the hooks ran, and that
manufactures false `final -> producing` sequences. The count above was re-derived with
a single serialized poller before being believed. The ledger's own recorded sequence
is authoritative because a key is only reported when it differs from the last recorded
one.

The rates above come from a poller loop, not production. A real session scans once per
delivery point, so the exposure is roughly the 0.1 ms window over the gap between a
wrapper start and the next scan — order of one in ten thousand, and only for a wrapper
starting concurrently with an unrelated tool call, i.e. the detached / late-starting
case. Rare; but what it emits is a false *terminal* status, the class of error the
design exists to prevent.

**Fix direction:** build the capture directory under a temporary name and `rename` it
into place after the first `write_meta`. Rename is atomic, so no scanner ever observes
a meta-less directory.

**Related, unobserved.** `status.rs:92-107` reads `meta.json` and *then* checks wrapper
liveness. A wrapper that records its reap and exits between those two reads would yield
`abandoned` instead of `final(status)`. Never seen in ~7,000 wrapper starts here; the
window is a serde parse plus one `/proc` read. Re-reading meta once before concluding
`abandoned` covers this and F4 together.

## F5

### The ledger commits before the report prints, so a failed write retires changes forever

`hook_post::report_changes` calls `ledger.commit()?` at `hook_post.rs:207`; the hook
serializes and prints at `hook_post.rs:71`. If the print fails, the keys are already
recorded as delivered — they match next time and are never reported again.

```
hook-post with stdout on /dev/full, three pending children

exit code                101   panic: failed printing to stdout: No space left on device
ledger recorded          3 keys
delivered to the agent   0 keys
next delivery point      reports 1 of the 3
```

The panic goes to stderr, where the agent never sees it.

The same ordering is exposed to the hook's 5 s timeout in `settings.json`: a kill
landing between commit and print loses that report permanently. (Proven with
`/dev/full`; not reproduced against the live runtime's timeout path.)

**Fix direction:** print first, commit only after a successful write. That inverts the
risk into a harmless duplicate report.

## F6

### `agent-tools ps` has no output bound

`status.rs:12` caps a report line's name at `NAME_MAX = 200` chars. `ps.rs:265` caps
nothing — it escapes and prints the full command for every capture in the session:

```rust
writeln!(buf, "      cmd:     {}", crate::meta::escape_control(&m.command.join(" ")))?;
```

```
one wrapped 120 KB script        ps output    240,680 B   longest line 120,150 chars
twelve wrapped 100 KB scripts    ps output  2,406,795 B
same twelve, pushed report                       1,769 B   every line capped
```

The spec's "`ps` … has no such budget" is about *which fields* to include, not about
unbounded line length. Agents routinely wrap large heredoc scripts, and `ps` is the
documented recovery path the prompt tells the agent to run after a compaction.

## F7

### One malformed line in `events.jsonl` silently drops every event in that file

`events::read_all` fails the whole file on the first unparseable line, and `ps.rs:114`
discards the error:

```rust
if let Ok(evts) = events::read_all(&tuid_dir) {
```

Appending one non-JSON line to a tool-call's `events.jsonl` removed that call's events
from `ps` with zero warnings.

Concurrent appends are **not** a corruption source: 12 wrappers writing ~100 KB
`child_started` events into one file produced 36/36 parseable lines, because an
`O_APPEND` write of a single line is atomic. The reachable trigger is a short write,
i.e. the same disk-full condition as F2.

## F8

### A held scope flock stalls every delivery point, with no timeout

`ledger.rs:99` uses `Flock::lock(file, FlockArg::LockExclusive)`, which blocks
indefinitely. With a foreign holder on `.reported.lock`:

```
flock -x <scope>/.reported.lock sleep 30
timeout 5 agent-tools hook-post   ->  rc=124, waited 5.0 s, stdout empty
```

Nothing is *lost* — no commit happens, so the changes land at a later delivery point —
but every tool call stalls for the full hook timeout and reports nothing while the lock
is held, and the agent is given no reason. Only `hook-post` and `hook-prompt` take this
lock; `ps` correctly does not.

## F9

### `pgrep -f` / `pkill -f` aimed at a wrapped process also match the wrapper

`run.rs:29-34` deliberately leaves argv intact unless `--hide-cmdline` is passed, so a
full-command-line pattern matches two processes instead of one:

```
wrapped   481875  agent-tools run --desc srv bash -c exec sleep 90    comm=at:srv
          481889  sleep 90                                            comm=sleep
bare      481944  sleep 91
```

Killing the wrapper yields `abandoned` and orphans the child that was the actual
target. `comm` is `at:<desc>`, so `pgrep -x` is unaffected — only `-f` matching aliases.
This is a consequence of an intentional trade-off, recorded here because it is a real
difference from "drop-in replacement".

## F10

### A relative `AGENT_TOOLS_PARENT_DIR` is misdiagnosed as "not set"

`paths::parent_dir_from_env` distinguishes "unset" from "must be an absolute path".
`run.rs:36` throws that away:

```rust
let parent_dir = paths::parent_dir_from_env().map_err(|_| {
    anyhow!("AGENT_TOOLS_PARENT_DIR is not set.\n ... the hook is not installed.")
})?;
```

`AGENT_TOOLS_PARENT_DIR=rel agent-tools run --desc x true` reports "is not set" and
sends the operator to check hook installation. Propagating the underlying error costs
one line.

## F11

### The `BACKGROUNDED:` notice and the status header are joined onto one line

`hook_post.rs:68` joins the parts with a space:

```
BACKGROUNDED: ... To kill it: use TaskStop tool with task_id bg-42. [agent-tools] run status:
  bg-child [final(0)] pid 479080, no output, ...
```

`sys_prompt/alan-default-next.md:171` teaches "Lines beginning `[agent-tools]` or
`BACKGROUNDED:` are status from this channel". When both are present the header no
longer begins a line. `parts.join("\n")` restores the contract.
`scripts/check-prompt-coupling.sh` does not catch this: it greps for the literals, not
for their line position.

## F12

### The wrapper absorbs SIGTERM and SIGINT when the child ignores them

`signals::install_forwarding` installs tokio handlers on the wrapper, which replaces the
default disposition — so the wrapper no longer dies on SIGTERM itself. It forwards,
never escalates, and never gives up.

```
child: bash -c 'trap "" TERM; echo ready; sleep 20'
  kill -TERM <wrapper>   wrapper survives
  kill -INT  <wrapper>   wrapper survives
  kill -9    <wrapper>   ends it  (child orphaned, status abandoned)
```

Control case: a child with `trap "echo GOT-TERM; exit 42" TERM` received the forwarded
SIGTERM and the wrapper propagated its exit 42 correctly.

This is the mechanism behind the `TaskStop` row already in the spec's failure-mode
table.

## F13

### `ps` hides the capture that `hook-post` reports as `abandoned`

**Added 2026-08-26**, found while reproducing F4 rather than in the original run.

`ps.rs:233-236` skips a capture whose `meta.json` will not parse:

```rust
let m = match meta::read_meta(&p) {
    Ok(m) => m,
    Err(_) => continue,
};
```

`hook_post::report_changes` does not skip it — `status::derive` returns `abandoned` for
the same directory. So the two consumers of one derivation disagree about whether the
child exists at all. Against a capture dir containing no `meta.json`:

```
hook-post:  …/999999 [abandoned] pid -, no output, out=0B err=0B
ps       :  (nothing)
```

The spec says `ps` "renders the current status of every child in the session using the
same derivation … everything shown whether or not it was reported", and its failure-mode
table says "a capture that cannot be described is never silently dropped". Both are
violated, and in the worst direction: `ps` is the documented recovery path after a
compaction, so the one child the report just called terminal is the one an agent cannot
look up.

## F14

### A multi-byte character in `--desc` discards the command, leaving no trace on disk

**Added 2026-08-26**, found while auditing paths the original run did not exercise.

Two independently harmless defects compose into a critical one.

`procname.rs:42-48` truncates the `comm` hint by comparing a **byte** length against a
**char**-at-a-time push:

```rust
let mut s = String::from("at:");
for c in hint.chars() {
    if s.len() >= 15 { break; }   // bytes
    s.push(c);                     // a whole char, possibly 2-4 bytes
}
```

At 13 or 14 bytes a 3-byte character overshoots to 16 or 17. `prctl(PR_SET_NAME)`
truncates at 15 — mid-character — leaving invalid UTF-8 in `/proc/self/comm`, which is
embedded in the `comm` field of `/proc/self/stat`. `procstat::start_ticks`
(`procstat.rs:25`) then reads that file with `fs::read_to_string`, which hard-fails on
invalid UTF-8, and the `?` aborts `run` at `run.rs:50` — before `create_dir_all` at
`:52` and before the first `write_meta` at `:67`.

Swept with one CJK character after N leading ASCII bytes:

```
n=9   bytes before push 12   rc=0  ok-9
n=10  bytes before push 13   rc=2  agent-tools run: read /proc/629846/stat: stream did not contain valid UTF-8
n=11  bytes before push 14   rc=2  agent-tools run: read /proc/629863/stat: stream did not contain valid UTF-8
n=12  bytes before push 15   rc=0  ok-12
```

Ordinary phrasing reaches it, and nothing runs:

```
$ agent-tools run --desc "build the 鍵盘 driver" -- echo hello-world
agent-tools run: read /proc/629898/stat: stream did not contain valid UTF-8
rc=2
$ find <scope>
<scope>                       # scope dir only: no pid dir, no meta.json, no events
```

The window is 3 byte-offsets wide for a 3-byte character and 4 for an emoji. `n=9`
carries the same character one byte earlier and exits 0, so this is a byte-offset
window, not "non-ASCII breaks it".

The prompt instructs the agent to write `--desc` as free natural-language text and
marks the wrapper required for side-effectful and long-running commands. So a
description containing CJK, Cyrillic, Greek, accented Latin or an emoji can silently
discard the command the wrapper exists to protect, with an error naming neither
`--desc` nor Unicode. Because the abort precedes every directory and meta write, the
spec's own guarantee — "a capture that cannot be described is never silently dropped" —
is breached in the one way it cannot detect: there is no capture to describe.

`procstat`'s UTF-8-strict read is worth fixing on its own account. `comm` holds
arbitrary bytes for any process, and `is_alive` (`procstat.rs:35`) returns `false` on a
read error, so an unreadable `stat` makes a live wrapper derive as `final(status)`.

`tests/run_test.rs::default_leaves_argv_visible_and_sets_comm` passes `--desc
"compute-things"` — pure ASCII, structurally incapable of exercising the byte/char
mismatch. `hide_cmdline` was checked and does *not* share the defect: `procname.rs:86-88`
copies raw bytes and nothing in this repository reads `/proc/self/cmdline` back as UTF-8.

## F15

### `ps` output grows with session history and is ordered by an identifier uncorrelated with time

**Added 2026-08-26.**

Two halves with different fixes.

**Growth.** 58 trivial wrapped calls, every `--desc` a short `step N`:

```
$ agent-tools ps --session-id psgrow-test | wc -lc
    468   32187
      captures section  14004
      events section    18183
```

That is past the Bash tool's 30,000-character head truncation
(`docs/tool-token-limits.md:42`) at an unremarkable scale, and it is not F6 — no field
is long; the count is. Over half of it is the events section re-carrying `desc`,
`command` and `wrapper_pid` that the capture record already holds.

**Ordering.** `ps.rs:49-54` sorts by `agent_id`, then **lexical `tool_use_id`**, with
`started_at` only a tie-break inside one id. Created in the order `zzz_first`,
`mmm_second`, `aaa_third`:

```
tool-use toolu_aaa_third     started: 03:56:47.388     <- ran last, listed first
tool-use toolu_mmm_second    started: 03:56:47.175
tool-use toolu_zzz_first     started: 03:56:46.957     <- ran first, listed last
```

Head truncation therefore keeps an arbitrary id-lexical subset and drops the events
section entirely, which is the opposite of what an agent recovering from a compaction
needs.

---

## Structurally unachievable

Not defects. These are the clauses of the tool description that no tee-based wrapper
can satisfy, measured 2026-08-26 so the contract can be rewritten around them rather
than repeatedly re-litigated.

| Property | Bare | Wrapped | Why |
| --- | --- | --- | --- |
| `isatty(1)` under a pty | `stdout IS a tty` | `stdout NOT a tty` | a tee is a pipe |
| `WIFSIGNALED` at the parent | `True`, signal 15 | `False`, exit code 143 | the wrapper exits normally after translating |
| `$PPID` / process group | the shell | the wrapper | a wrapper is a process |
| atomicity of a write above 4096 B from concurrent writers | whole write, when the shared destination is a regular file | `PIPE_BUF`, once the pipe fills | a tee is a pipe; only a file description gets `f_pos_lock` |

The `isatty` divergence does not reach the agent: inside the Bash tool stdin is a
socket and stdout and stderr are the same regular file, so neither bare nor wrapped
sees a terminal. It reaches a human running `agent-tools run` in a shell.

One clause that *is* satisfied, and was worth checking because its failure would have
been severe: Rust sets `SIGPIPE` to `SIG_IGN` in the wrapper, and ignored dispositions
survive `exec`. `std::process::Command` resets it, so the child does not inherit it —
a wrapped child's `SigIgn` mask is `0000000180000000` (bit 12 clear) and a pipeline
*inside* a wrapped `bash -c` still yields 141. Nested pipelines are unaffected.

---

## Verified clean

Each of these is a falsification attempt that failed to break the implementation.

| Area | Result |
| --- | --- |
| Ledger under contention | 16 concurrent `hook-post` processes, 40 children: exactly one reporter, 0 duplicates, 0 losses, 40 ledger entries |
| Report budget | 300 children: 45 lines per delivery, drop count stated, dropped lines stay pending and land at later deliveries |
| Context cap | max `additionalContext` 8,943 chars over 12 deliveries with 400 children × 180-char descs — under the 10,000 runtime cap |
| Quiet buckets | correct and inclusive at 29 / 30 / 31 / 299 / 300 / 1799 / 1800 / 7199 / 7200 / 100000 s |
| Largest crossed bucket | a 100,000 s anchor reports `quiet(2h)`, not a cascade |
| Flap collapse | producing → quiet → producing between two deliveries reports nothing |
| Continuous output | reported once, then silent across every later delivery point |
| Detached daemon | `exited(0)` while the wrapper lives, `final(0)` once it drains; no five-minute wait |
| The invariant | the tool call that first observes a daemon's marker file carries `final(0)` |
| Non-Bash delivery | confirmed live in-session: `PostToolUse:Read` carried `final(0)` |
| Wrapper SIGKILLed | `abandoned` at the very next delivery point |
| Zombie wrapper | `final(0)`, not `producing` (`procstat::is_alive` rejects state `Z`) |
| Wrapper SIGSTOPped | `producing` — exactly as the spec documents and accepts |
| Subagent isolation | independent ledgers under `<scope>/<agent_id>/`, no leakage in either direction |
| Numeric `tool_use_id` | reproduces the spec's documented failure mode exactly: a bogus `abandoned` leaks to the main thread and the subagent's capture vanishes from `ps`. Real ids are `toolu_*`, so unreachable today |
| Nesting, 3 deep | every level reported; wrapper/child pid chain consistent (`bash -c` execs into the inner wrapper, so the outer child pid equals the inner wrapper pid) |
| Signal exit codes | 137, 139, 141; forwarded SIGTERM yields the child's own 42 |
| Byte-for-byte capture | 4 KB of `/dev/urandom` identical; NUL bytes and ANSI escapes survive |
| stdin | inherited — pipelines, heredocs and `</dev/null` all behave |
| Hostile `--desc` | newline / CR / ANSI escaped as `\n` `\r` `\x1b`; capped at 200 chars with a visible `…`; empty and whitespace-only fall back to the command |
| Commit failure | announced as "unavailable this time (…)", nothing recorded, changes stay pending |
| Corrupt ledger | reset announced in the report rather than showing unexplained repeats |
| Scan cost | 54 ms at 300 children; `ps` 19 ms — far under the 5 s hook timeout |
| State growth | 77 MB across 131 sessions / 2,664 captures accumulated since 2026-05-17. No-GC is a stated non-goal and is currently harmless — but one F1 incident would add hundreds of GB |

## Outside the wrapper

- **`opencode_loads_prefixed_langfuse_env_and_forwards_args` fails** on this checkout.
  The repo's real `.env` leaks into the test environment (`base_url=unset` where the
  test expects a value). Pre-existing and unrelated to `run`. Every other suite is
  green: 59 + 4 + 1 + 19 + 7 + 6 + 1 passing.
- **No CI runs `scripts/check-prompt-coupling.sh` or `cargo test`.**
  `.github/workflows/skills-test.yml` is the only workflow and it runs pytest under
  `skills/scripts/**`. The guard exists and passes when invoked by hand, but nothing
  automated would catch prompt/emitter drift.

## Method

A worktree release build was exercised through an isolated `$HOME` so nothing touched
live session state, with `CLAUDE_CONFIG_ROOT` asserted against the worktree. Delivery
points were driven by feeding real `PostToolUse` / `PostToolUseFailure` /
`UserPromptSubmit` payloads to the hook binaries and parsing the emitted
`additionalContext`.

Status derivation was covered two ways: real wrappers for lifecycle and timing, and
synthesized `meta.json` records pinned to a live process's pid and start-ticks for
boundaries that would otherwise need hours of wall clock. Races were driven with up to
8 concurrent hook processes against up to 4,000 wrapper starts under 24-way CPU
saturation; the F4 window was measured directly with inotify and `strace` rather than
inferred.

Failure injection used `/dev/full`, `RLIMIT_FSIZE` with `SIGXFSZ` ignored, an occupied
temp path (`EISDIR` on the ledger's rename target), and a foreign `flock` holder.

Harness scripts were kept under `/tmp/at-stress/` (`lib.sh`, `synth.py`, `t*.sh`,
`t*.py`) and are not committed; the reproductions quoted inline above are sufficient to
re-derive every finding.

### Not reachable in this environment

- **pid reuse inside one `tool_use_id` directory.** The capture directory is named for
  the wrapper pid and capture files are opened `append`, so a reused pid within one
  tool call would concatenate two children's output and overwrite `meta.json`.
  `/proc/sys/kernel/ns_last_pid` is not writable in this container and `pid_max` is
  4,194,304, so the collision could not be forced. Nesting means one tool-call
  directory *can* accumulate many wrappers, so this is not purely theoretical — just
  untested.
- **A read-only scope directory.** The test process runs as root and `DAC_OVERRIDE`
  bypasses the permission check; an occupied temp path was used instead to exercise the
  same commit-failure branch.

### Harness hazard worth recording

`pkill -f <pattern>` is dangerous from inside a Claude Code Bash call: the tool's shell
carries the entire rewritten script — heredoc body included — in its argv, so a pattern
naming any string in the script matches and kills the tool shell itself. This killed
two test runs (exit 144) before the cause was identified. Unrelated to `agent-tools`,
but it looks exactly like a wrapper defect while it is happening.

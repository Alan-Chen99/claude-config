# agent-tools run — Passthrough Contract and Stress-Finding Fix Scope

Status: draft
Date: 2026-08-26
Findings source: `notes/agent-tools-run-stress-findings.md`
Amends (does not supersede):
`docs/superpowers/specs/2026-08-24-agent-tools-run-observability-design.md`

## Why

The stress run recorded in the notes produced twelve findings. Deciding what to do
with them requires first noticing that they answer to two different documents, and
that only one of those documents exists.

The observability half of `agent-tools run` — what the agent is guaranteed to know
about a child — is specified by the 2026-08-24 design. The **passthrough** half —
what happens to the child's bytes, its exit code, and its relationship to the
surrounding pipeline — is specified nowhere. Its entire contract is three sentences
in `sys_prompt/alan-default-next.md:169-170`, with no design document, no test, and
no guard:

> a drop-in replacement of the direct `<executable> <args..>` … The wrapper passes
> the child's stdout and stderr through byte-for-byte and propagates the child's exit
> code. Pipelines, redirections, `2>&1`, exit-status checks, and downstream filters
> behave exactly as if you had run the bare command.

That sentence is not merely inaccurate. It promises a property no tee-based wrapper
can have, so it had to be false. Three findings (F1, F2, F3) are consequences of the
gap rather than defects against a standard.

This document supplies the missing contract, records which findings are fixed against
it, and states which are deliberately left alone.

## Measurement conditions

Every number quoted here was measured on 2026-08-25/26 in the container described by
`/workspace/docker-compose.yml`, 24 CPUs, against a release build of the worktree at
`c6ab2e8` whose `agent-tools/src` is byte-identical to the installed checkout.
Scheduling-sensitive figures — the interleaving threshold above all — are properties
of that host under that load, not constants.

## The passthrough contract

Three tiers. The distinction is not stylistic: it decides which findings are bugs,
which are documented trade-offs, and which are impossible wishes.

### Guaranteed

- **Content.** For as long as the caller's stream accepts writes, every byte the child
  writes to its stdout reaches the wrapper's stdout, and likewise for stderr,
  unmodified and in order within that stream. Verified for 4 KB of `/dev/urandom`, NUL
  bytes, and ANSI escapes. A caller that closes its end ends the guarantee for that
  stream; see the first row of [Differs from bare](#differs-from-bare-by-design).
- **Completeness, or a loud failure.** The forwarded stream is never silently short.
  If the wrapper cannot complete a forward or a capture, it says so on stderr and in
  the child's status; it never truncates the caller's data without a diagnostic.
- **Exit code.** The wrapper exits with the child's exit code, or `128 + signum` when
  the child died from a signal — the number a shell reports for the bare command.
- **stdin.** Inherited. Pipelines, heredocs and `</dev/null` behave.
- **Child signal dispositions.** The child starts with default dispositions. In
  particular the wrapper's own `SIGPIPE: SIG_IGN`, which Rust installs at startup,
  does not reach it: a wrapped child's `SigIgn` mask has bit 12 clear, and a pipeline
  *inside* a wrapped `bash -c` still yields 141. Nested pipelines are unaffected.
- **Line atomicity when the two streams share a destination.** No line is split by a
  write from the other stream. See [Stream merging](#stream-merging).

### Differs from bare, by design

Each row is a deliberate trade, not a defect. The prompt states them.

| Difference | Why it is accepted |
| --- | --- |
| A downstream that closes its read end does not stop the child; the wrapper keeps capturing | This is the tool's purpose. Bare `grep pattern-hit corpus \| head -3` discards 397 of the 400 matching lines; wrapped, the agent sees the same 3 lines in 9 ms instead of 5 ms and the complete 400-line result set is on disk |
| `set -o pipefail` reports the producer's own status, not `141` | Nothing died of `SIGPIPE`; reporting 141 would be a fiction. `grep` that found matches exits 0 |
| The call lasts as long as the producer, not until the consumer quits | Measured 0.405 s bare → 2.464 s wrapped on a 6 × 0.4 s producer piped to `head -1`. A call that exceeds the Bash timeout is backgrounded and reported, so the wait is visible rather than mysterious |
| Relative order of stdout against stderr is best-effort | Exact when the child's writes are ≳50 µs apart; scrambled below that. See [Stream merging](#stream-merging) |
| `pgrep -f` / `pkill -f` on the command line matches the wrapper too | Argv stays visible for `ps aux` diagnosis. `--hide-cmdline` opts out. F9 |
| The wrapper survives signals its child ignores | It must outlive the child to reap, drain, and record `drained_at`. F12 |

### Not achievable, at any effort

A tee is a pipe, and a wrapper is a process. These follow:

| Property | Bare | Wrapped |
| --- | --- | --- |
| `isatty(1)` at a terminal | true | false |
| `WIFSIGNALED` seen by the parent | `True`, signal 15 | `False`, exit code 143 |
| `$PPID`, process group, process-tree shape | the shell | the wrapper |

The `isatty` divergence does not reach the agent: inside the Claude Code Bash tool
stdin is a socket and stdout and stderr are the same regular file, so neither bare
nor wrapped sees a terminal. It reaches a human running `agent-tools run` in a shell.

The prompt drops the "exactly as if you had run the bare command" claim and carries
the three tiers above instead.

## Categorization

Against the 2026-08-24 observability spec.

| ID | Category | Basis |
| --- | --- | --- |
| F5 | spec-violation | Reporting: "if it differs from the last key **reported** to that scope, emit one line and record the new key". The ledger records keys that were never reported |
| F11 | spec-violation | Report format: "One header line, one line per child whose key changed" |
| F13 | spec-violation | "`ps` renders the current status of **every** child … everything shown whether or not it was reported", and "a capture that cannot be described is never silently dropped" |
| F4 | spec-deficiency | The derivation row `meta.json missing → abandoned` was written for a corrupt capture and silently also covers a starting one |
| F6 | spec-deficiency | "`ps` … has no such budget" scopes which *fields* to include; it bounds neither line length nor total output |
| F7 | spec-deficiency | `events.jsonl` appears in the state layout with no read semantics |
| F8 | spec-deficiency | No bound on the ledger lock wait, and no failure-mode row for "the hook could not run at all" |
| F2 (status half) | spec-deficiency | No failure-mode row for "the capture file could not be written" |
| F1, F2 (data half), F3 | other — different contract | Against `sys_prompt/alan-default-next.md:169-170`, supplied above |
| F10 | other | Error-message defect; no contract involved |
| F9, F12 | other — deliberate | Trade-offs, recorded above and in the amended failure-mode table |

**F13 is new.** It was found while verifying F4, not in the stress run: a capture
directory whose `meta.json` is unreadable is reported `abandoned` by `hook-post` and
skipped entirely by `ps` (`ps.rs:233-236`, `Err(_) => continue`). The documented
recovery path hides exactly the child the report has just called terminal.

## In scope

### F1 — a wrapped producer never stops when its downstream exits

`capture.rs:46` discards the forward write result, so the `EPIPE` a closed downstream
produces is dropped and the read end is never closed. Both halves of bare's stopping
mechanism are disabled: the wrapper is the reader and never closes, and Rust's
`SIGPIPE: SIG_IGN` turns the wrapper's own failed write into a discarded error.

The draining itself is the feature and stays. What is missing is a bound and an
announcement.

- On a forward `BrokenPipe`, stop forwarding and record `downstream_closed_at` in
  `meta.json`. Continue capturing.
- Bound the **post-close** drain only — normal operation stays uncapped, so a
  legitimate multi-gigabyte capture is untouched. Default 256 MB per stream,
  overridable by env. At the cap, close the read end so the child receives `SIGPIPE`
  as it would bare, and record `capture_capped`.
- Render both facts in the status detail, so a call that took 2.4 s where bare took
  0.4 s carries its own explanation, and a capped capture never passes for a complete
  one.

Measured runaway rate is ~400 MB/s (`yes`), so the cap fires in under a second; a
74 MB corpus scan and a full build log pass under it.

An infinite *slow* producer (`tail -f | head -1`) is not bounded by a byte cap and is
not meant to be: the wrapper stays alive, and the observability design already reports
it — confirmed as `[producing]` in `agent-tools ps`, and `abandoned` once killed.

### F2 — a capture write failure truncates the caller and kills the child

`capture.rs:45` propagates the capture error out of `tee`; `run.rs:165-166` discards
it with `let _ = stdout_tee.await`. Nothing then drains the pipe, so the child dies of
`SIGPIPE`. Injected with `RLIMIT_FSIZE`: the child produced 154,893 B, the caller
received 8,192 B cut mid-line, the wrapper's stderr was empty, and the report read
`final(141)` — a wrapper-inflicted death rendered as the child's own.

Forward failures and capture failures get opposite handling, and the asymmetry is the
whole fix:

- **Forward** failure is the caller's stream going away. Stop the tee.
- **Capture** failure is the wrapper's own problem. Keep forwarding, stop capturing,
  record `capture_error` in `meta.json`, and write one `[agent-tools]` diagnostic to
  stderr. The child is never killed by it, and the caller's bytes are never truncated.

The status detail carries `capture_error`, so `final(0)` is never rendered next to a
capture that silently stopped growing.

### F3 — stdout/stderr interleaving

Two distinct failures with very different severities. The notes record only the milder
one, and scope it to `2>&1`; both parts of that framing need correcting.

**Scope.** The Claude Code Bash tool gives fd 1 and fd 2 the *same* file — verified by
`readlink /proc/self/fd/{1,2}` on a plain call with no redirection. Every wrapped
command is therefore affected, not only ones written with `2>&1`.

**Reordering — mild.** With no delay between the child's writes, ordering is
destroyed (30 of 60 lines out of place). The threshold is sharp:

| gap between writes | out of place |
| --- | --- |
| 0 | 30/60 |
| 10 µs | 6/60 |
| 50 µs | 0/60 |
| ≥100 µs | 0/60 |

Any child doing real work between lines is already exact.

**Mid-line splicing — severe.** A line longer than the 8192-byte read buffer is
forwarded as several `write` syscalls, and on the `new_multi_thread` runtime
(`main.rs:385`) the other stream's write lands between them. Bare never does this: the
child's write reaches the shared file description as one syscall and the kernel's
`f_pos_lock` serializes it.

| case | bare | wrapped |
| --- | --- | --- |
| 12 KB lines, 2,000 concurrent stderr lines | 200 lines, **0** splices | 228 lines, **28** splices — 14% corrupted |
| 5 MB line, 20,000 concurrent stderr lines | 1 line, **0** splices | 583 lines, **582** splices |

Splice offsets are exactly 8191/8192, pinning the mechanism to `capture.rs:37`.
Corruption is unrecoverable downstream — `grep`, `jq`, and log parsers all see a
garbage record — whereas reordering leaves every line intact.

#### Stream merging

Applied only when fd 1 and fd 2 name the same destination; when they differ there is
nothing to interleave. Detection compares `readlink /proc/self/fd/1` against
`/proc/self/fd/2`. This is exact for pipes. It reports a false positive for
`> f 2> f`, where the shell opens one path twice with independent offsets;
`kcmp(2)`, which distinguishes them, returns `EPERM` in this container.

The two tees share one forward writer holding a single piece of state — which stream
owns the line currently being written:

```
shared forward writer { owner: Option<Stream> }

tee(stream):
  chunk = read(pipe)                       // await readable
  write_capture(chunk)                     // never gated
  lock: wait while owner == Some(other)
        write_forward(chunk)
        owner = if chunk ends with '\n' { None } else { Some(self) }
  if the next read would block, or ownership has been held past the fairness bound:
        lock: if owner == Some(self) { owner = None; notify }
```

No bytes are buffered to achieve this. A chunk is written the moment it arrives; only
*ownership* is held, so the other stream waits rather than the active one being
delayed. A gated tee holds at most one already-read 8 KB chunk.

**Releasing on would-block is what makes the gate safe, not merely prompt.** Holding
ownership until the line completes deadlocks the child: measured, a child that wrote
12,000 newline-less bytes to stdout and then 200,000 B to stderr blocked filling
stderr's 64 KB pipe and therefore never wrote the newline that would release the gate
— 1.5 s held, line never completed, child still running. Draining stderr completed it
immediately. Since a child stuck on the gated stream is by definition not writing to
the owner stream, the owner reads `EAGAIN` and releases, and the deadlock cannot form.

The fairness bound covers the remaining case, a multithreaded child whose owner stream
never goes quiet: without it the gated stream starves where bare would interleave.
Release after 1 MB or 100 ms of unbroken ownership, whichever comes first, accepting
one splice only for output that has no line structure at all.

Release-on-quiescence reproduces bare exactly. A child that writes `Progress: 50%`,
goes quiet, then writes to stderr yields `Progress: 50%E1\n` under both.

**The gate never covers the capture.** Each tee writes its capture file the instant it
reads. The two capture files, the `out=`/`err=` split, and `agent-tools ps` are
unaffected, and a gated stream's capture never lags.

Ordering stays best-effort. The relative order of two writes that both landed before
the wrapper was scheduled exists only in the kernel's scheduling history and is not
recoverable from the pipes; a single shared pipe is the only construction that
guarantees it, and it would cost the two capture files.

### F4 + F13 — a starting child reported with a terminal key

`run.rs:52` creates the capture directory and `run.rs:67` writes the first
`meta.json`. A scan landing between them derives `abandoned`, which the spec marks
terminal and the prompt teaches as "the capture is complete and the child process's
fate is unknown". Reproduced directly: a capture directory with no `meta.json` is
reported

```
…/999999 [abandoned] pid -, no output, out=0B err=0B
```

— the `pid -` and path-as-name being the signature of `read_meta` failing. The notes
measured the window at ~245 µs traced and observed it end-to-end 1–2 times per
3,000–4,000 wrapper starts under a hammering poller.

- Build the capture directory under a temporary name and `rename` it into place after
  the first `write_meta`. Rename is atomic, so no scanner observes a meta-less
  directory.
- Re-read `meta.json` once before concluding `abandoned`. This also covers the notes'
  "Related, unobserved" case, where a wrapper records its reap and exits between
  `status.rs:92-107`'s meta read and its liveness check.
- `ps` renders a capture it cannot describe rather than skipping it, matching what the
  report says about the same directory and what the spec already requires.

### F5 — the ledger commits before the report prints

`hook_post.rs:207` calls `ledger.commit()?`; `hook_post.rs:71` prints. A print that
fails leaves keys recorded as delivered, so they match next time and are never
reported again. With stdout on `/dev/full` and three pending children:

```
rc=101   panic: failed printing to stdout: No space left on device
ledger:  {"toolu_verify/560952":"final(0)", …568:"final(0)", …584:"final(0)"}
next delivery point, stdout OK:  (empty)
```

All three status changes lost permanently — a direct violation of the invariant, since
consequences of those exits keep reaching the agent while the exits never do.

Print first; commit only after the write succeeds. That inverts the risk into a
harmless duplicate report. The same ordering protects against the hook's 5 s timeout
landing between the two steps.

### F6 — `agent-tools ps` has no output bound

`status.rs:12` caps a report line's name at 200 characters; `ps.rs:265` caps nothing.
One wrapped 60 KB command produced a 60,030-character line and 61,126 B of output for
a single capture. `docs/tool-token-limits.md:42` puts the Bash tool's head truncation
at 30,000 characters, so one such capture consumes the entire visible budget and the
model sees a prefix plus a disk path.

`ps` bounds both dimensions:

- **Per line: 2,000 characters** for the command, with a visible truncation marker and
  the capture's `meta.json` named as where the full text lives. Well above a report
  line's 200, and small enough that ten full-length captures still fit the tool
  budget.
- **In total: 20,000 characters**, leaving margin under the 30,000 head truncation for
  the events section. When captures are dropped, `ps` states how many and names
  `--task <tool_use_id>` as the way to see them. Live children are never the ones
  dropped — `ps` after a compaction is asked "what is running now".

The spec's "no such budget" language is corrected to mean *which fields*, which is
what it was written to mean.

### F7 — one malformed line erases a file's events

`events::read_all` fails the whole file on the first unparseable line and `ps.rs:114`
discards the error. Appending one non-JSON line took a tool call's events from 9 to 0
with no warning of any kind.

Skip the unparseable lines, keep the rest, and state in the `ps` output how many were
skipped and in which file. Concurrent appends are not a corruption source — an
`O_APPEND` write of a single line is atomic, and 12 wrappers writing ~100 KB events
into one file produced 36/36 parseable lines. The reachable trigger is a short write,
i.e. the same disk-full condition as F2.

### F8 — a held scope flock stalls every delivery point

`ledger.rs:99` uses `FlockArg::LockExclusive`, which blocks indefinitely. With a
foreign holder on `.reported.lock`, `timeout 4 agent-tools hook-post` returned rc=124
with empty stdout and empty stderr: every tool call stalls for the full hook timeout
and the agent is told nothing and given no reason.

Nothing is lost — no commit happens, so the changes land later — but a delivery point
arriving with no report is an invariant violation on its face, and the graceful path
already exists. Bound the wait at **2 seconds**, comfortably inside the 5 s hook
timeout configured for `PostToolUse`, `PostToolUseFailure` and `UserPromptSubmit` in
`settings.json`, and on expiry return an error so the existing
`"[agent-tools] run status: unavailable this time (…)"` branch fires. A silent stall
becomes a stated one, with time left to state it.

### F10 — a relative `AGENT_TOOLS_PARENT_DIR` is misdiagnosed

`paths::parent_dir_from_env` distinguishes "unset" from "must be an absolute path";
`run.rs:36` maps both to the same message.
`AGENT_TOOLS_PARENT_DIR=rel agent-tools run --desc x true` reports
"AGENT_TOOLS_PARENT_DIR is not set" and sends the operator to check hook installation.
Propagate the underlying error.

### F11 — the report header does not begin a line

`hook_post.rs:68` joins the parts with a space, so when a `BACKGROUNDED:` notice is
present the status header lands mid-line and the prompt's rule — "Lines beginning
`[agent-tools]` or `BACKGROUNDED:` are status from this channel" — no longer matches.
Verified: with both parts present, no line in `additionalContext` begins with
`[agent-tools]`. Join with `"\n"`.

### The guard that should have caught F11

`scripts/check-prompt-coupling.sh` exists and passes; it greps for the literals, not
for their position, so a header that stops beginning a line drifts past it. The guard
gains a line-position check for both prompt-coupled prefixes.

Whether it runs automatically is out of scope here: `gh` in this environment is
authenticated as a throwaway account and returns HTTP 404 for
`Alan-Chen99/claude-config`, so whether Actions runs against that fork could not be
determined. The claim in `agent-tools/CLAUDE.md` is already correctly scoped — it says
the script exists, not that CI runs it — so no false statement needs removing.

## Out of scope, deliberately

| Item | Why it is left alone |
| --- | --- |
| **F9** — `pgrep -f`/`pkill -f` matches the wrapper | Visible argv is a deliberate debuggability choice with a shipped opt-out (`--hide-cmdline`, `run.rs:22-28`), added after a real `ps aux` leak. Hiding it by default breaks the diagnosis the tool exists to support. Recorded as an accepted difference instead |
| **F12** — the wrapper absorbs SIGTERM/SIGINT | Surviving a signal the child ignored is what lets the wrapper reap, drain, and write `drained_at`. A wrapper that died on TERM would yield `abandoned` and lose the pipe tail — a spec guarantee traded for shell fidelity. The alternative, escalating to SIGKILL, would kill children that legitimately ignore TERM to finish cleanup. Verified the observability half is already truthful: wrapper survived TERM/INT/TERM/INT, and SIGKILL yielded `abandoned` with the child orphaned |
| **F3 by single shared pipe** | Would guarantee ordering by construction, but destroys the two capture files and the `out=`/`err=` accounting the observability spec mandates in two places. The gate keeps both and fixes the severe half |
| `pkill -f` from inside a Claude Code Bash call | Not a defect in anything this repository owns. The tool's shell carries the whole rewritten script in its argv, so a pattern naming any string in the script kills the tool shell. Notes-only |
| The `opencode` `.env` test leak | `opencode_loads_prefixed_langfuse_env_and_forwards_args` fails because the repository's real `.env` reaches the test environment. Real, unrelated subsystem, and bundling it would make this change unreviewable. Separate commit |

## Amendments to the observability spec

The 2026-08-24 document gains:

- **State layout** — the capture directory is published atomically. A scanner never
  observes a directory without `meta.json`, so the `meta.json missing` derivation row
  means a corrupt capture and nothing else.
- **Derivation** — `abandoned` is concluded only after a second `meta.json` read.
- **Durable facts** — `downstream_closed_at`, `capture_capped`, `capture_error`.
- **Detail** — those three facts render alongside the key.
- **`agent-tools ps`** — "no such budget" is scoped to which fields; the 2,000-character
  line bound and 20,000-character total bound are stated, along with the rule that live
  children are never dropped.
- **`events.jsonl` semantics** — unparseable lines are skipped and counted, never fatal
  to the file. The layout section names the file; nothing so far says how it is read.
- **Failure modes** — new rows for: the capture file cannot be written; the hook
  cannot run (lock held, timeout); `pgrep -f` aliasing (F9); the wrapper absorbing
  signals its child ignores (F12).
- **Reporting** — the ledger is committed only after the report is successfully
  written.
- **Durable facts** — the table gains a note that `run` records these through the
  observer seam described in [A testable seam](#a-testable-seam-agent-tools-passthru),
  so the fact set and the callback set stay one list rather than two.

## Prompt and documentation changes

The repo-root `CLAUDE.md` subcommand list gains `passthru`, described as the
passthrough half of `run` without the state — the entry point the passthrough tests
drive. `agent-tools/CLAUDE.md` records the `run` / `passthru` layering, so the next
reader does not add a behaviour to one and not the other.

`sys_prompt/alan-default-next.md:169-170` is prompt-coupled and changes in the same
commit as the emitters. The prompt does **not** gain `passthru`: an agent should keep
reaching for `run`, which is the one with observability. The "behave exactly as if you had run the bare command"
sentence goes; the three tiers of [the contract](#the-passthrough-contract) replace
it, compressed to what an agent acts on:

- bytes per stream, exit code, and stdin are faithful;
- lines are never split, but stdout-versus-stderr order is best-effort;
- a downstream that quits does not stop the command, so the call runs as long as the
  command does and `pipefail` reports the command's own status.

`agent-tools/CLAUDE.md`'s prompt-coupled table gains rows for any new emitted string.

## A testable seam: `agent-tools passthru`

Every passthrough property in this document is a property of *processes* — pipes,
`SIGPIPE`, fd aliasing, exit codes, scheduling between two tees. None of it can be
tested in-process, so the tests must drive a real binary. Today the only binary that
exercises this code is `run`, which first demands `AGENT_TOOLS_PARENT_DIR`, a scope
directory, a ledger, and a matching `CLAUDE_CONFIG_ROOT` — machinery irrelevant to
whether `EPIPE` closes a read end.

Implementation splits the two apart.

```
        capture::Passthrough
   forwarding · capture · gate · drain cap
          ^                    ^
          |                    |
   run (+ observability)    passthru (+ nothing)
```

**One implementation, two entry points.** `passthru` must not be a second
implementation of the same idea; a test against a parallel copy proves nothing about
`run`. `run` is `passthru` plus the durable facts and the events log.

The seam between them is an observer, and it is not an invented abstraction — it is
the observability spec's own Durable facts table expressed as callbacks:

```rust
trait Observer {
    fn child_started(&mut self, pid: u32);
    fn downstream_closed(&mut self, stream: Stream);
    fn capture_capped(&mut self, stream: Stream, bytes: u64);
    fn capture_error(&mut self, stream: Stream, err: &str);
    fn reaped(&mut self, status: i32);
    fn drained(&mut self);
}
```

`run` implements it by writing `meta.json` and `events.jsonl`. `passthru` implements it
by writing one JSON line per call to `--events`, so a test asserts on facts without
parsing a state directory.

```
agent-tools passthru [--stdout PATH] [--stderr PATH] [--drain-cap BYTES]
                     [--merge auto|always|never] [--events PATH] -- <cmd> [args…]
```

- `--stdout` / `--stderr` name capture destinations. Omitted means forward only, so
  the pure passthrough path is reachable with no filesystem state at all.
- `--drain-cap` overrides the post-close cap, so the runaway test does not have to
  produce 256 MB.
- `--merge` forces the aliasing decision. `auto` is what `run` uses; `always` and
  `never` let a test exercise both branches without having to construct fd aliasing
  from the harness, which is awkward to do reliably from a shell.
- `--events` is the fact stream.

`passthru` is subject to the same root resolution as every other subcommand. The guard
exists so a session's hooks are answered by its own checkout, and carving an exception
for a subcommand is a worse trade than setting one environment variable in a test.

`passthru` is useful outside tests too — capturing a command's output without hook
installation — but that is a side effect, not the reason it exists.

## Testing

Integration tests, each falsifying one clause. The passthrough clauses run against
`passthru`, which needs no scope; the reporting clauses need `run` and the hooks.

### Against `passthru`

1. **Downstream closes.** `passthru --stdout C -- seq 1 2000000 | head -1` — the caller
   receives one line, `C` holds all 14,888,896 B, and `--events` carries
   `downstream_closed`.
2. **Runaway is bounded.** An infinite producer piped to `head -1` under a small
   `--drain-cap` stops at the cap and emits `capture_capped`.
3. **Capture failure isolates.** Under `RLIMIT_FSIZE`, the caller receives all
   154,893 B, the child is not killed, one diagnostic reaches stderr, and `--events`
   carries `capture_error`.
4. **No splicing.** Under `--merge always`, 12 KB stdout lines against 2,000 concurrent
   stderr lines produce zero splices where the current implementation produces 28.
5. **The gate cannot deadlock.** A child that writes a newline-less stdout chunk and
   then fills stderr's 64 KB pipe completes, rather than hanging as the un-released
   gate does.
6. **`--merge never` leaves the streams alone**, so the gate's cost is not paid when
   the destinations differ.
7. **Exit codes.** Normal status, `128 + signum` for a signalled child, and the
   producer's own status — not 141 — under `set -o pipefail` with a closed downstream.
8. **Content fidelity.** 4 KB of `/dev/urandom`, NUL bytes and ANSI escapes survive
   both the forward and the capture.

### Against `run` and the hooks

9. **`run` and `passthru` agree.** For a fixed set of commands, both produce identical
   forwarded bytes and identical exit codes. This is what keeps the seam honest: the
   passthrough tests above are evidence about `run` only for as long as this passes.
10. **A starting child is never terminal.** No scan of a capture directory
    mid-creation yields `abandoned`; concurrent starts under load emit no terminal key
    for a live child.
11. **`ps` shows what the report shows.** A capture with unreadable `meta.json` appears
    in both.
12. **A failed print loses nothing.** `hook-post` with stdout on `/dev/full` records
    nothing, and the next delivery point reports all pending changes.
13. **`ps` is bounded.** A wrapped 60 KB command produces output under the tool budget,
    with the truncation and any drops stated.
14. **One bad event line costs one line.** 9 events plus one malformed line yields 8
    events and a stated skip.
15. **A held lock is announced.** With a foreign holder, `hook-post` returns within its
    2 s bound and emits the "unavailable this time" line.
16. **The header begins a line.** With a `BACKGROUNDED:` notice present, a line of
    `additionalContext` starts with `[agent-tools]`.

## Non-goals

- Making the wrapper transparent. `isatty`, `WIFSIGNALED`, and process identity are
  named as unachievable above, not deferred.
- Guaranteeing stdout-versus-stderr ordering. Best-effort, with the mechanism and the
  measured threshold documented.
- Garbage collection of state. Unchanged from the 2026-08-24 spec.
- Changing the `BACKGROUNDED:` notice beyond how it is joined to the report.

## Risks

- The ~50 µs interleaving threshold is a scheduling property of the measured host. A
  busier or slower machine moves it, and the gate is what makes correctness independent
  of it — ordering degrades, framing does not.
- `readlink`-based aliasing detection treats `> f 2> f` as merged when the shell has
  in fact opened one path twice with independent offsets. Merging is the friendlier
  behaviour there, but it is a divergence, and `kcmp(2)` is unavailable to close it.
- The fairness bound is chosen, not measured: no real program is known to hold
  ownership past it. If one exists it takes one splice per bound, which is the
  pre-existing behaviour rather than a regression.
- The post-close drain cap protects the disk but not wall clock. An infinite slow
  producer keeps a wrapper alive until the agent acts on the status report.

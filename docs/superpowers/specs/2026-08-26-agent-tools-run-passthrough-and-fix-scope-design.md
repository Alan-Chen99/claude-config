# agent-tools run — Passthrough Contract and Stress-Finding Fix Scope

Status: draft
Date: 2026-08-26
Findings source: `notes/agent-tools-run-stress-findings.md`
Amends (does not supersede):
`docs/superpowers/specs/2026-08-24-agent-tools-run-observability-design.md`

## Why

The stress run recorded in the notes produced twelve findings, and scoping the fixes
produced three more. Deciding what to do with them requires first noticing that they
answer to two different documents, and that only one of those documents exists.

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

Every number quoted here was measured in the container described by
`/workspace/docker-compose.yml`, 24 CPUs, against a release build of the worktree whose
`agent-tools/src` is byte-identical to the installed checkout. Figures carried over
from the stress run are dated 2026-08-25; the stream-merging comparison, F14 and F15
were measured 2026-08-26 and are marked as such in the notes. Scheduling-sensitive
figures are properties of that host under that load, not constants.

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
- **`--merge` equivalence.** With `--merge`, the child's stdout and stderr are one
  pipe, and the result is what `<cmd> 2>&1` produces — including where that construction
  is itself imperfect. See [`--merge`](#--merge-one-pipe-for-the-child).

### Differs from bare, by design

Each row is a deliberate trade, not a defect. The prompt states them.

| Difference | Why it is accepted |
| --- | --- |
| A downstream that closes its read end does not stop the child; the wrapper keeps capturing | This is the tool's purpose. Bare `grep pattern-hit corpus \| head -3` discards 397 of the 400 matching lines; wrapped, the agent sees the same 3 lines in 9 ms instead of 5 ms and the complete 400-line result set is on disk |
| `set -o pipefail` reports the producer's own status, not `141` | Nothing died of `SIGPIPE`; reporting 141 would be a fiction. `grep` that found matches exits 0 |
| The call lasts as long as the producer, not until the consumer quits | A call that exceeds the Bash timeout is backgrounded and reported, so the wait is visible rather than mysterious |
| Without `--merge`, relative order of stdout against stderr is best-effort | The streams are two pipes; their relative order was lost before the wrapper saw them. `--merge` removes the split and with it the problem. F3 |
| With `--merge`, the `out=`/`err=` split does not exist | One pipe cannot say which fd a byte came from. This is the whole cost of the flag, and why it is opt-in. F3 |
| `pgrep -f` / `pkill -f` on the command line matches the wrapper too | Argv stays visible for `ps aux` diagnosis. `--hide-cmdline` opts out. F9 |
| The wrapper survives signals its child ignores | It must outlive the child to reap, drain, and record `drained_at`. F12 |

### Not achievable, at any effort

A tee is a pipe, and a wrapper is a process. These follow:

| Property | Bare | Wrapped |
| --- | --- | --- |
| `isatty(1)` at a terminal | true | false |
| `WIFSIGNALED` seen by the parent | `True`, signal 15 | `False`, exit code 143 |
| `$PPID`, process group, process-tree shape | the shell | the wrapper |
| Atomicity of a write above 4096 B from concurrent writers | the whole write, when the shared destination is a regular file | `PIPE_BUF`, once the pipe fills |

The last row is why `--merge` is equivalent to `2>&1` rather than to a bare direct
call: `f_pos_lock` serializes writes to a file description, and no pipe offers that.
Measured, a plain shell pipeline with no `agent-tools` present splices 40–62 lines out
of 2,200 where the same producer writing to a file splices none.

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
| F11 | other — different contract | Against the prompt, not this spec: "Lines beginning `[agent-tools]` or `BACKGROUNDED:` are status from this channel" (`sys_prompt/alan-default-next.md:171`). The 2026-08-24 "one header line" sentence contrasts one header against N child lines; reading it as "the header occupies its own line" is a stretch |
| F13 | spec-violation | "`ps` renders the current status of **every** child … everything shown whether or not it was reported", and "a capture that cannot be described is never silently dropped" |
| F14 | spec-violation | "a capture that cannot be described is never silently dropped" — the abort precedes the capture's existence, so nothing is dropped and nothing is recorded |
| F4 | spec-deficiency | The derivation row `meta.json missing → abandoned` was written for a corrupt capture and silently also covers a starting one |
| F6, F15 | spec-deficiency | The `ps` section specifies content but never a consumption model. Both findings are consequences of rendering for a reader rather than for a filter |
| F7 | spec-deficiency | `events.jsonl` appears in the state layout with no read semantics |
| F8 | spec-deficiency | No bound on the ledger lock wait, and no failure-mode row for "the hook could not run at all" |
| F2 (status half) | spec-deficiency | No failure-mode row for "the capture file could not be written" |
| F1, F2 (data half), F3 | other — different contract | Against `sys_prompt/alan-default-next.md:169-170`, supplied above |
| F10 | other | Error-message defect; no contract involved |
| F9, F12 | other — deliberate | Trade-offs, recorded above and in the amended failure-mode table |

**F13, F14 and F15 are not from the stress run.** They were found while scoping these
fixes; their reproductions are in the notes under the same measurement conditions.

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
`SIGPIPE`. Injected with `RLIMIT_FSIZE`: the child produced 134,893 B, the caller
received 8,192 B cut mid-line, the wrapper's stderr was empty, and the report read
`final(141)` — a wrapper-inflicted death rendered as the child's own.

Forward failures and capture failures get opposite handling, and the asymmetry is the
whole fix:

- **Forward** failure is the caller's stream going away. Stop forwarding; keep
  capturing, exactly as F1 requires.
- **Capture** failure is the wrapper's own problem. Keep forwarding, stop capturing,
  record `capture_error` in `meta.json`, and write one `[agent-tools]` diagnostic to
  stderr. The child is never killed by it, and the caller's bytes are never truncated.

Neither failure ends the other half of the tee. The status detail carries
`capture_error`, so `final(0)` is never rendered next to a capture that silently
stopped growing.

### F3 — stdout/stderr interleaving

Two distinct failures with very different severities. The notes record only the milder
one, and scope it to `2>&1`; both parts of that framing need correcting.

**Scope.** The Claude Code Bash tool gives fd 1 and fd 2 the *same* file — verified by
`readlink /proc/self/fd/{1,2}` on a plain call with no redirection. Every wrapped
command is therefore affected, not only ones written with `2>&1`.

**Reordering.** With no delay between the child's writes, ordering is destroyed. The
threshold is sharp — 30/60 lines out of place at zero gap, 6/60 at 10 µs, 0/60 at
50 µs and above — but "a child doing real work between lines is already exact" is
weaker reassurance than it sounds: a program that writes a 12 KB line and then a few
short diagnostics is nowhere near 50 µs, and measured 1997 of 2200 lines out of place.

**Mid-line splicing.** A line longer than the 8192-byte read buffer (`capture.rs:37`)
is forwarded as several `write` syscalls, and on the `new_multi_thread` runtime
(`main.rs:385`) the other stream's write lands between them.

Both failures have one cause — the streams are split into two pipes — and one fix.

#### `--merge`: one pipe for the child

`agent-tools run --merge` gives the child a single pipe for fd 1 and fd 2, by `dup2`
before `exec`. There is then one stream, so there is nothing to interleave and nothing
to splice: the wrapper reads chunks and writes them in the order they arrived.

Measured, for a child whose writes are serialized — one `write` in flight at a time,
the ordinary case — 200 lines of 12,001 B interleaved with 2,000 short stderr lines:

| | spliced | misordered |
| --- | --- | --- |
| bare | 0 | 0/2200 |
| two pipes (today) | 202 | 1997/2200 |
| `--merge` | **0** | **0/2200** |

For a child with two concurrent writers the residual is not the wrapper's: bare into a
pipe with a consumer doing the same per-chunk work splices 40–62 of 2,200, and
`--merge` splices 41–73. That is the `PIPE_BUF` row of
[Not achievable](#not-achievable-at-any-effort), reached by any construction that
inserts a pipe. Enlarging the pipe does not close it — 54–73 splices at 64 KB, 25–37 at
256 KB, 1–18 at the 1 MB maximum — so no pipe size is specified.

**Why opt-in rather than automatic.** One pipe cannot say which fd a byte came from,
so a merged run has one capture file and no `out=`/`err=` split. That split is worth
keeping for a caller that needs to know which stream a line came from, and merging is
worth having for the far commoner case of reading both together. Neither is right for
everyone, so the agent chooses, and the prompt says how to choose. Automatic merging
on fd aliasing was considered and rejected: it would merge every command in the Bash
tool, where fd 1 and fd 2 always alias, removing the split from callers who never asked.

**What a merged run looks like.**

- One capture file. The second is **not created** — an empty `stderr` file reads as
  "this command produced no diagnostics", which would be false. Absent, not zero.
- The detail renders `out+err=<n>B` rather than `out=<n>B err=<m>B`, and names the one
  path.
- `first_byte` and the silence watcher are single-stream.
- `--merge` and an explicit `--stderr` capture destination are mutually exclusive;
  supplying both is an error, not a silent preference.

Ordering across two *unmerged* streams stays best-effort. The relative order of two
writes that both landed before the wrapper was scheduled exists only in the kernel's
scheduling history and is not recoverable from the pipes. `--merge` is the answer to
that, not a heuristic applied to the split case.

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
- `ps` emits a capture it cannot describe rather than skipping it, matching what the
  report says about the same directory and what the spec already requires. As a record
  carrying an `error` field, so a filter cannot miss it.

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

**The commit is not in the hook; it is in the function both hooks share.**
`ledger.commit()?` sits inside `report_changes` (`hook_post.rs:138-208`), which
`hook_post.rs:43` calls and `hook_prompt.rs:26` also calls before printing its own
`additionalContext` at `hook_prompt.rs:37`. Reordering two statements inside
`hook_post` therefore cannot fix this: `UserPromptSubmit` — one of the three delivery
channels the 2026-08-24 spec makes invariant-bearing — carries the identical defect and
would be left with it.

`report_changes` stops committing. It returns the lines together with the uncommitted
ledger, and each caller commits only after its own write to stdout has succeeded. That
inverts the risk into a harmless duplicate report, and the same ordering protects
against the hook's 5 s timeout landing between the two steps.

### F6 + F15 — `agent-tools ps` renders for a reader, not for a filter

`status.rs:12` caps a report line's name at 200 characters; `ps.rs:265` caps nothing.
One wrapped 120 KB script produced a 120,150-character line and 240,680 B of `ps`
output; twelve wrapped 100 KB scripts produced 2,406,795 B, where the pushed report of
the same twelve was 1,769 B with every line capped. The Bash tool truncates at 30,000
characters (`docs/tool-token-limits.md:42`). Separately, 58
trivial wrapped calls — every `--desc` a short `step N` — produced 468 lines and
32,187 characters, already past that limit with no long field anywhere; over half of it
was the events section re-carrying `desc`, `command` and `wrapper_pid` that the capture
records already held. And `ps.rs:49-54` orders capture groups by `agent_id`, then
**lexical `tool_use_id`**, with `started_at` only a tie-break inside one id, so what
truncation keeps is uncorrelated with time.

Budgeting the human-readable tree would address none of this properly: any budget picks
a subset, and the tree gives the agent no way to say which subset it wanted. The
consumption model is the fix.

**`ps` emits JSON Lines — one object per line — and nothing else.** The tree output is
removed rather than kept behind a flag; a human reads the same records through `jq`.

- Every line carries a `rec` discriminator: `capture`, `event`, or `note`.
- Status is carried as **fields**, not as a rendered string: `kind` (`producing`,
  `quiet`, `exited`, `final`, `abandoned`, `spawn-failed`), `status`, and `live`.
  `jq -c 'select(.live)'` is then a filter over data rather than a regex over a display
  format that the prompt-coupling guard is separately responsible for.
- Byte counts follow the capture layout: `out` and `err` for a split capture, `merged`
  and `bytes` for a merged one, with the absent stream's key **absent** rather than
  zero.
- **Live captures only, by default.** That is the question `ps` is asked — the
  2026-08-24 spec already says so ("`ps` after a compaction is asked 'what is running
  now'") without following it through. `--all` includes terminal ones.
- The default **always** emits a `note` record naming what it withheld:
  `{"rec":"note","omitted":57,"reason":"terminal","hint":"--all"}`. After a compaction
  the agent has lost the report text while the ledger still records those keys as
  delivered, so they will never be re-reported and `ps` is the only route back to them.
  A silently empty default would be indistinguishable from "nothing ever ran".
- **Newest first**, so `--all | head -5` yields the five most recent.
- **No output budget**, by design. The output is filtered before it reaches the agent's
  context, so a budget would only pick a worse subset than the agent's own filter. The
  budget on the pushed report is unaffected and stays.
- `--help` carries the schema. Nothing about field names goes into the system prompt.

The events merge must follow the filtered capture list rather than walking the state
directory — `ps.rs:105` already iterates `for c in &captures`, and that coupling is now
load-bearing: it is what keeps the default view proportional to what is running rather
than to session history.

The 2026-08-24 spec's "no such budget" language was written to mean *which fields*.
It now means what it says, for a different reason.

### F7 — one malformed line erases a file's events

`events::read_all` fails the whole file on the first unparseable line and `ps.rs:114`
discards the error. Appending one non-JSON line took a tool call's events from nine to
zero with no warning of any kind.

Skip the unparseable lines, keep the rest, and emit the count as a `note` record naming
the file. Concurrent appends are not a corruption source — an `O_APPEND` write of a
single line is atomic, and 12 wrappers writing ~100 KB events into one file produced
36/36 parseable lines. The reachable trigger is a short write, i.e. the same disk-full
condition as F2.

### F8 — a held scope flock stalls every delivery point

`ledger.rs:99` uses `FlockArg::LockExclusive`, which blocks indefinitely. With a
foreign holder on `.reported.lock`:

```
flock -x <scope>/.reported.lock sleep 30
timeout 5 agent-tools hook-post   ->  rc=124, waited 5.0 s, stdout empty
```

Every tool call stalls for the full hook timeout and the agent is told nothing and
given no reason.

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

### F14 — a multi-byte character in `--desc` discards the command

Two independently harmless defects compose into the only finding here that stops a
wrapped command from running at all.

`procname.rs:42-48` truncates the `comm` hint by comparing a byte length against a
char-at-a-time push, so at 13 or 14 bytes a 3-byte character overshoots to 16 or 17.
`prctl(PR_SET_NAME)` truncates at 15 — mid-character — leaving invalid UTF-8 in
`/proc/self/comm`, which is embedded in `/proc/self/stat`. `procstat::start_ticks`
(`procstat.rs:25`) reads that file with `fs::read_to_string`, which hard-fails on
invalid UTF-8, and the `?` aborts `run` at `run.rs:50` — before the capture directory
exists at `:52` and before the first `write_meta` at `:67`.

```
$ agent-tools run --desc "build the 鍵盘 driver" -- echo hello-world
agent-tools run: read /proc/629898/stat: stream did not contain valid UTF-8
rc=2
$ find <scope>
<scope>                       # scope dir only: no pid dir, no meta.json, no events
```

The window is three byte-offsets wide for a 3-byte character and four for an emoji.
The prompt instructs the agent to write `--desc` as free natural-language text, so
CJK, Cyrillic, Greek, accented Latin and emoji all reach it. Because the abort precedes
every directory and meta write, the failure is invisible to `ps` and to every report:
the spec's "a capture that cannot be described is never silently dropped" is breached in
the one way it cannot detect.

Both halves are fixed:

- `set_comm` tests `s.len() + c.len_utf8() > 15` before pushing, so the string handed to
  `prctl` never exceeds the limit and is never cut mid-character.
- `procstat` stops parsing `/proc/<pid>/stat` as UTF-8. `comm` holds arbitrary bytes for
  any process, and `is_alive` (`procstat.rs:35`) returns `false` on a read error, so an
  unreadable `stat` currently makes a live wrapper derive as `final(status)`. It reads
  bytes and locates field 22 after the last `)`.

`hide_cmdline` was checked and does not share the defect: `procname.rs:86-88` copies
raw bytes and nothing in this repository reads `/proc/self/cmdline` back as UTF-8.

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
| **F9** — `pgrep -f`/`pkill -f` matches the wrapper | Visible argv is a deliberate debuggability choice with a shipped opt-out (`--hide-cmdline`, `run.rs:29-34`), added after a real `ps aux` leak. Hiding it by default breaks the diagnosis the tool exists to support. Recorded as an accepted difference instead |
| **F12** — the wrapper absorbs SIGTERM/SIGINT | Surviving a signal the child ignored is what lets the wrapper reap, drain, and write `drained_at`. A wrapper that died on TERM would yield `abandoned` and lose the pipe tail — a spec guarantee traded for shell fidelity. The alternative, escalating to SIGKILL, would kill children that legitimately ignore TERM to finish cleanup. Verified the observability half is already truthful: wrapper survived TERM/INT/TERM/INT, and SIGKILL yielded `abandoned` with the child orphaned |
| **Merging by default** | Would fix ordering for every command in the Bash tool, where fd 1 and fd 2 always alias — and would remove the `out=`/`err=` split from every caller, including ones that never asked. Opt-in keeps both behaviours reachable |
| **Serializing the two unmerged tees** to preserve line framing | An ownership protocol between the tees would give line atomicity the split case does not have — but it would make the wrapper *more* atomic than a bare shell pipeline, at the cost of a deadlock argument, a fairness bound, and fd-aliasing detection. `--merge` covers the same need with a `dup2` |
| **A pid-reuse window in signal forwarding** | `run.rs:141` reaps the child before `run.rs:164` cancels forwarding, so a signal arriving in between could in principle reach a recycled pid. Raised while auditing, not reproduced — forcing pid reuse needs `ns_last_pid`, which is not writable in this container. Recorded in the notes as a hypothesis |
| `pkill -f` from inside a Claude Code Bash call | Not a defect in anything this repository owns. The tool's shell carries the whole rewritten script in its argv, so a pattern naming any string in the script kills the tool shell. Notes-only |
| The `opencode` `.env` test leak | `opencode_loads_prefixed_langfuse_env_and_forwards_args` fails because the repository's real `.env` reaches the test environment. Real, unrelated subsystem, and bundling it would make this change unreviewable. Separate commit |

## Amendments to the observability spec

The 2026-08-24 document gains:

- **State layout** — the capture directory is published atomically. A scanner never
  observes a directory without `meta.json`, so the `meta.json missing` derivation row
  means a corrupt capture and nothing else. A merged capture holds one file and the
  other is absent, not empty.
- **Derivation** — `abandoned` is concluded only after a second `meta.json` read.
- **Durable facts** — `downstream_closed_at`, `capture_capped`, `capture_error`,
  `merged`.
- **Detail** — those facts render alongside the key; a merged capture renders
  `out+err=<n>B` and one path.
- **`agent-tools ps`** — the section is rewritten around JSON Lines, live-by-default,
  newest-first, a mandatory `note` record for anything withheld, and no output budget.
  "No such budget" now means what it says.
- **`events.jsonl` semantics** — unparseable lines are skipped and counted, never fatal
  to the file. The layout section names the file; nothing so far says how it is read.
- **Failure modes** — new rows for: the capture file cannot be written; the hook
  cannot run (lock held, timeout); the wrapper aborts before a capture exists (F14);
  `pgrep -f` aliasing (F9); the wrapper absorbing signals its child ignores (F12).
- **Reporting** — `report_changes` no longer commits. Each delivery channel commits
  after its own write to stdout succeeds.
- **Durable facts** — the table gains a note that `run` records these through the
  observer seam described in [A testable seam](#a-testable-seam-agent-tools-passthru),
  so the fact set and the callback set stay one list rather than two.

## Prompt and documentation changes

The repo-root `CLAUDE.md` subcommand list gains `passthru`, described as the
passthrough half of `run` without the state — the entry point the passthrough tests
drive. `agent-tools/CLAUDE.md` records the `run` / `passthru` layering, so the next
reader does not add a behaviour to one and not the other.

`sys_prompt/alan-default-next.md:169-172` is prompt-coupled and changes in the same
commit as the emitters. The prompt does **not** gain `passthru`: an agent should keep
reaching for `run`, which is the one with observability. Three changes:

**The contract sentence.** "behave exactly as if you had run the bare command" goes;
the three tiers of [the contract](#the-passthrough-contract) replace it, compressed to
what an agent acts on: bytes per stream, exit code, and stdin are faithful; a
downstream that quits does not stop the command, so the call runs as long as the
command does and `pipefail` reports the command's own status.

**The `2>&1` example.** The current text reads

```
Ex: `agent-tools run --desc "Install build deps" apt install -y build-essential &&
     agent-tools run --desc "Build all components" make 2>&1 | tail -30`
```

That `2>&1` binds the *wrapper's* fds, aliasing them and producing exactly the
interleaving F3 is about. It becomes `--merge`:

```
agent-tools run --merge --desc "Build all components" make | tail -30
```

with one sentence on when to choose it: pass `--merge` when you will read stdout and
stderr together, which is usual; omit it when you need to know which stream a line came
from, and accept that their relative order is then best-effort.

**The `ps` sentence.** "run `agent-tools ps` to see the full current status of
everything in this session" describes output that no longer exists. `ps` emits JSON
Lines of what is still running; `--all` adds finished ones, `--help` carries the
schema, and it is meant to be filtered.

`agent-tools/CLAUDE.md`'s prompt-coupled table gains rows for any new emitted string.

## A testable seam: `agent-tools passthru`

Every passthrough property in this document is a property of *processes* — pipes,
`SIGPIPE`, fd aliasing, exit codes. None of it can be tested in-process, so the tests
must drive a real binary. Today the only binary that exercises this code is `run`,
which first demands `AGENT_TOOLS_PARENT_DIR`, a scope directory, a ledger, and a
matching `CLAUDE_CONFIG_ROOT` — machinery irrelevant to whether `EPIPE` closes a read
end.

Implementation splits the two apart.

```
        capture::Passthrough
   forwarding · capture · merge · drain cap
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
    fn spawn_failed(&mut self, err: &str);
    fn downstream_closed(&mut self, stream: Stream);
    fn capture_capped(&mut self, stream: Stream, bytes: u64);
    fn capture_error(&mut self, stream: Stream, err: &str);
    fn reaped(&mut self, status: i32);
    fn drained(&mut self);
}
```

`spawn_failed` is present because the Durable facts table requires `spawn_error` and
`status.rs` renders it as a terminal `spawn-failed(err)` key; spawning happens inside
the shared core, so the fact belongs to the seam like every other. `Stream` is
`Stdout`, `Stderr`, or `Merged`.

`run` implements it by writing `meta.json` and `events.jsonl`. `passthru` implements it
by writing one JSON line per call to `--events`, so a test asserts on facts without
parsing a state directory.

```
agent-tools passthru [--stdout PATH] [--stderr PATH] [--merge] [--drain-cap BYTES]
                     [--events PATH] -- <cmd> [args…]
```

- `--stdout` / `--stderr` name capture destinations. Omitted means forward only, so
  the pure passthrough path is reachable with no filesystem state at all.
- `--merge` gives the child one pipe, as `run --merge` does. With `--stderr` it is an
  error.
- `--drain-cap` overrides the post-close cap, so the runaway test does not have to
  produce 256 MB.
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
   134,893 B, the child is not killed, one diagnostic reaches stderr, and `--events`
   carries `capture_error`.
4. **`--merge` reproduces bare for a serialized writer.** A single-threaded child
   emitting 12 KB lines interleaved with short stderr lines yields zero spliced and zero
   misordered lines, against 202 and 1997/2200 without the flag.
5. **`--merge` produces one capture.** The stderr destination is absent, not empty, and
   `--merge --stderr PATH` is rejected.
6. **Exit codes.** Normal status, `128 + signum` for a signalled child, and the
   producer's own status — not 141 — under `set -o pipefail` with a closed downstream.
   `--merge` does not change any of them.
7. **Content fidelity.** 4 KB of `/dev/urandom`, NUL bytes and ANSI escapes survive
   both the forward and the capture, merged and unmerged.

### Against `run` and the hooks

8. **`run` and `passthru` agree.** For a fixed set of commands, both produce identical
   forwarded bytes and identical exit codes. This is what keeps the seam honest: the
   passthrough tests above are evidence about `run` only for as long as this passes.
9. **A non-ASCII `--desc` runs the command.** `--desc "build the 鍵盘 driver"` at every
   byte offset in the 3-byte and 4-byte windows exits 0, and the capture directory
   exists with a parseable `meta.json`. F14.
10. **A starting child is never terminal.** No scan of a capture directory
    mid-creation yields `abandoned`; concurrent starts under load emit no terminal key
    for a live child.
11. **`ps` shows what the report shows.** A capture with unreadable `meta.json` appears
    in both, as a record carrying an `error` field.
12. **A failed print loses nothing, on both channels.** `hook-post` with stdout on
    `/dev/full` records nothing and the next delivery point reports all pending changes;
    the same holds for `hook-prompt`, which is the caller the old fix would have missed.
13. **`ps` defaults to live and says what it withheld.** A session with one running and
    fifty finished captures emits one `capture` record and a `note` naming 50; `--all`
    emits all fifty-one, newest first.
14. **`ps` is filterable.** `jq -c 'select(.live)'` over the default output selects the
    running children without matching on any rendered string.
15. **One bad event line costs one line.** Nine events plus one malformed line yields
    eight events and a `note` naming the file and the count.
16. **A held lock is announced.** With a foreign holder, `hook-post` returns within its
    2 s bound and emits the "unavailable this time" line.
17. **The header begins a line.** With a `BACKGROUNDED:` notice present, a line of
    `additionalContext` starts with `[agent-tools]`.

## Non-goals

- Making the wrapper transparent. `isatty`, `WIFSIGNALED`, process identity, and
  `PIPE_BUF` atomicity are named as unachievable above, not deferred.
- Guaranteeing stdout-versus-stderr ordering without `--merge`. Best-effort, with the
  mechanism and the measured threshold documented.
- Garbage collection of state. Unchanged from the 2026-08-24 spec — and note that
  live-by-default `ps` makes accumulated state cheaper to live with, not smaller.
- Changing the `BACKGROUNDED:` notice beyond how it is joined to the report.

## Risks

- `--merge` is opt-in, so an agent that does not reach for it keeps best-effort
  ordering and can still have a line over 8 KB spliced. The prompt is the only thing
  steering that choice, which is why the example changes rather than being supplemented.
- Removing the human-readable `ps` output makes a terminal user depend on `jq`. Accepted:
  the documented consumer is the agent, and two renderers would drift.
- Live-by-default changes what an unfiltered `ps` means. The `note` record is what keeps
  that from reading as "nothing ran"; if it is ever dropped, the default becomes
  actively misleading rather than merely partial.
- The post-close drain cap protects the disk but not wall clock. An infinite slow
  producer keeps a wrapper alive until the agent acts on the status report.
- F14's fix depends on two changes in different files. Either alone leaves a live
  hazard: a byte-safe `set_comm` still leaves `procstat` unable to read a `comm` set by
  anything else, and a byte-tolerant `procstat` still leaves an over-long `prctl` call.

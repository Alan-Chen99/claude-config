# `agent-tools run` — Specification

Status: draft, 2026-08-26
Supersedes `2026-08-24-agent-tools-run-observability-design.md` and the 2026-05-17 design.
Reproductions and measurements: `notes/agent-tools-run-stress-findings.md`.

## Purpose

Two things must hold for an agent to act soundly on a command it wrapped. **Its fate must
be knowable**: a wrapped command can outlive the tool call that started it, and its effects
reach the agent through the filesystem, so its status must too, no later. **And wrapping
must not change it**: an agent told to wrap everything side-effectful is not choosing to,
so the wrapper must be substitutable for the bare call or the instruction rewrites the
request; where it cannot be, the difference is stated rather than discovered.

A **child** is one `agent-tools run` invocation — it exists even if no process started;
the **wrapper** is that invocation's process. Out of scope: garbage collection, and
processes not started under `run`.

## The invariant

**No information caused by a change in a child's status reaches the agent before the
agent learns that status.**

The agent does not run between **delivery points** — the moments it receives content, a
tool result or a user turn — so it cannot learn of a change as it happens; it must never
receive a consequence first. That is what makes backgrounding unobservable.

- **Status is derived at delivery from durable facts, never cached when it changes.** Its
  writer may die before the next reader.
- **A wrapper that dies recording nothing still yields a truthful status**: its liveness
  is observable, so "unknown" is derivable rather than missing.

## Status

Status is a **key** and a **detail**: the key decides supersession and whether a report
happens, the detail never causes one.

| Key | Means (**terminal** keys end watching) |
| --- | --- |
| `spawn-failed(<err>)` | **terminal**: the command never started |
| `producing` | running, nothing has stalled |
| `quiet(<bucket>)` | running, silent for at least `<bucket>` |
| `exited(<status>)` | reaped; the capture may still grow |
| `final(<status>)` | **terminal**: reaped, and the capture can never grow |
| `abandoned` | **terminal**: wrapper gone with no reap; capture complete, fate unknown |

`<status>` is the exit code, or `128 + signum`. `exited` and `final` must not be
collapsed: at `exited` the capture may still be short, and `final` promises only that the
file cannot grow, not that it holds everything written. The quiet anchor is the last
captured byte, or the start when nothing was captured; the largest boundary crossed wins
(30s, 5m, 30m, 2h — configuration), and crossing one is a key change, so a chatty child
reports once, a stalled one per boundary.

Derivation must be **total** — every observable input combination maps to exactly one key,
no timeouts, no heuristics — and must never hand a terminal key to a child that is starting
or finishing: a reader racing the wrapper's writes re-reads before concluding a fate is
unknown. Liveness is an identity check, not a bare pid probe, or a reboot or recycled pid
leaves dead wrappers reporting live. Reap and exit status are one atomic fact, so no key
names a status never recorded.

## Reporting

At each delivery point, for each child in the **scope** — one agent's view, a subagent's
children never the main thread's — derive the key; report it when it differs from the last
key **reported** there, otherwise nothing.

- **Every delivery point carries every pending change**, errored tool calls included,
  since that is when an agent goes looking. Uninstrumentable channels are named, with the
  pull path as fallback.
- **A key is retired only once the agent has been told**, on every channel: recording
  delivery before the write succeeds turns a failed print into permanent loss, while
  committing after risks only a duplicate.
- **A report is never silently short**: when it drops lines it says how many and names the
  pull path, since silence reads as "nothing else changed".
- **A line is recognizable and self-sufficient**: it names the child — the `--desc`, or
  the command, never empty — its key, and where its output is. It begins a line, the prefix
  the agent identifies, and no arbitrary text can forge one or crowd a change out.
  The prompt quotes them, so they change with the emitters — stale quotes replaced, not
  added to — and the guard checks position, not just presence.
- **A delay is announced**: a delivery point silent because a lock was held is
  indistinguishable from one with nothing to say.

## The pull path

`agent-tools ps` answers what the report cannot: what is true now, for an agent whose
context was compacted while the ledger records those keys as delivered.

- **It answers "what is running now" by default, says what it withheld, and keeps that
  retrievable** — a count with no way back is useless after the compaction that made it
  necessary.
- **Its output is consumed by a program.** Status is carried as fields, not a rendered
  string, so selecting live children filters data rather than matching a display format:
  one renderer, not two, its schema carried by the command, not the prompt.
- **Its size is bounded by what is running, not by session history**, ordered newest first,
  since the tool carrying it truncates. It sets no byte budget of its own.
- **It never suppresses a future report**, and **emits a capture it cannot describe, with
  the reason** — push and pull must never disagree about whether a child exists.

## Passthrough

Three tiers: which differences are defects, which are trades, which are wishes.

### Guaranteed

- **Content.** Every byte the child writes to a stream reaches the caller's corresponding
  stream, unmodified and in order within it, as long as the caller accepts writes.
- **Completeness, or a loud failure.** A forwarded stream is never silently short and a
  capture never silently stops growing; either failure is stated on stderr and in the
  status.
- **Exit code and stdin.** The child's exit code, including `128 + signum`; stdin
  inherited, so pipelines and heredocs behave.
- **The child's signal dispositions are its own** — notably the wrapper's ignored
  `SIGPIPE`, or a pipeline *inside* a wrapped command changes behaviour.
- **Capture failure never kills the child; forward failure never stops the capture.** A
  caller going away is expected and capturing on is the point; a capture that cannot be
  written is the wrapper's failure, not the child's.

### Differs from bare, by design

- **A downstream that quits stops neither the child nor the call, and `pipefail` reports
  the producer's own status, not `141`.** The tool's purpose: `… | head -3` shows three
  lines while the whole result lands on disk; nothing died of `SIGPIPE`; an overrunning
  call is backgrounded and reported.
- **The post-close drain is bounded, and reaching the bound is recorded**, or a runaway
  producer fills the disk and a capped capture passes for complete. At the bound the read
  end closes, so the child sees `SIGPIPE` as bare would; normal operation is uncapped.
- **The wrapper is visible and durable**: `pgrep -f` matches it, and it survives signals
  its child ignores. Visible argv makes `ps aux` diagnosis work, with an opt-out; outliving
  the child lets it reap, drain and record completeness.
- **Unmerged streams have best-effort relative order.** Two pipes; that order was lost in
  the kernel before the wrapper saw it.

### Not achievable

`isatty`, signalled death, process identity and tree shape, and write atomicity above
`PIPE_BUF` cannot match bare: a tee is a pipe, a wrapper is a process. The prompt must stop
promising otherwise.

### The merge rule

Two pipes destroy the order between a child's streams and splice long lines, neither
repairable afterwards: that order exists only in the kernel.

**The child gets one pipe for both streams exactly when the caller's own two descriptors
provably reach one destination that cannot disagree about where the next byte goes** —
same file, both writable, both pipes or both appending. Everything else gets two.

- **Sound, not probabilistic.** Whether two descriptors share an open file description is
  undecidable here, so the conditions make it irrelevant: neither admissible destination
  has an offset to disagree about, and merging distinct ones would misroute data.
- **Declines rather than guesses**, and takes no flag: the only decisive test would mean
  writing to the caller's own file, and a flag could only demand the merge it refused.
- **The capture follows the decision** — merged, one file; split, two, the faithful record
  since the caller's streams already carry that split.
- **Its reach is an environment assumption.** In the Claude Code Bash tool both descriptors
  are one appending description on one regular file, so ordinary calls merge and `2>&1` is
  a no-op. Measured, not contracted; the decision is recorded per capture.

### A drivable core

Every passthrough property above is a property of *processes*, so a test must drive a real
binary, while `run` demands a scope, a ledger and hooks that bear on none of them. **The
core must be drivable through an entry point needing none of that, and be the
implementation `run` itself uses**, the two agreeing on forwarded bytes and exit codes.
Root resolution still binds it; the prompt does not teach it, so agents keep reaching for
the entry point with observability.

## Durable state

- **The wrapper records facts, never statuses**, and records the reap when it happens, not
  when the pipes close, or a detached descendant delays the exit status indefinitely.
- **A capture becomes visible atomically**; no key honestly describes a half-created one.
- **A merged capture holds one file; the other is absent, not empty** — an empty stderr
  file would read as "no diagnostics".
- **The facts include whatever explains a difference from bare** — downstream closed, drain
  capped, capture failed, streams merged and on which condition — rendered beside the key,
  so `final(0)` never sits beside a stalled capture.
- **A malformed line in an append-only log costs that line, not the file**; the loss is
  counted and stated.

## Current deviations

The shipped binary against the above; ids match
`notes/agent-tools-run-stress-findings.md`, which holds each reproduction. F9 and F12 there
are accepted differences.

| # | Clause | Deviation |
| --- | --- | --- |
| F1 | drain bound | the forward error is discarded: a closed downstream goes unnoticed, the drain never ends |
| F2 | capture isolation | a capture write failure truncates the caller mid-line and kills the child with `SIGPIPE` |
| F3 | the merge rule | always two pipes, which in the Bash tool hits every wrapped command, not just `2>&1` ones |
| F4, F13 | starting child | a scan between a capture's creation and its first fact derives `abandoned`, which the pull path hides |
| F5 | retire after delivery | the ledger commits before the report prints, so a failed print retires those changes for good |
| F6, F15 | pull output | uncapped, grows with session history, ordered uncorrelated with time, filterable only as text |
| F7 | log tolerance | the first unparseable line fails the whole events file, and that error is discarded |
| F8 | delay announced | the scope lock waits forever, so every delivery point stalls for the hook timeout |
| F10 | — | a relative `AGENT_TOOLS_PARENT_DIR` is reported as unset, blaming the wrong cause |
| F11 | line prefix | the header is joined to the backgrounding notice by a space, so no line carries the prefix |
| F14 | never dropped | a multi-byte `--desc` character aborts before any state exists; nothing runs, nothing is recorded |

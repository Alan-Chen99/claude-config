# `agent-tools run` — Specification

Status: draft
Date: 2026-08-26
Supersedes `2026-08-24-agent-tools-run-observability-design.md` and what remained of
`2026-05-17-agent-tools-run-design.md`.
Reproductions and measurements: `notes/agent-tools-run-stress-findings.md`.

## Purpose

Two things must hold for an agent to act soundly on a command it wrapped.

**The child's fate must be knowable.** A wrapped command can outlive the tool call that
started it, and its effects reach the agent through the filesystem, so its status must
too, no later.

**Wrapping must not change the command.** An agent told to wrap everything side-effectful
is not choosing to, so the wrapper must be substitutable for the bare call or the
instruction rewrites what was asked for. Where it cannot be, the difference is stated
rather than discovered.

A **child** is one `agent-tools run` invocation — it exists even if no process started;
the **wrapper** is that invocation's process. Out of scope: garbage collection of state,
and reporting on processes not started under `agent-tools run`.

## The invariant

**No information caused by a change in a child's status reaches the agent before the
agent learns that status.**

The agent does not run between **delivery points** — the moments it receives content, a
tool result or a user turn — so it cannot learn of a change as it happens; it must never
receive a consequence first, which is what makes backgrounding unobservable. A change
after the session's last delivery point is never reported, nor can any consequence reach
the agent.

- **Status is derived at delivery from durable facts, never cached when it changes.** A
  cached status is written by a process that may die before the next reader.
- **A wrapper that dies recording nothing still yields a truthful status**: wrapper
  liveness is observable, so "unknown" is derivable rather than missing.

## Status

Status is a **key** and a **detail**: the key decides supersession and whether a report
happens, the detail never causes one.

| Key | Means | Terminal |
| --- | --- | --- |
| `spawn-failed(<err>)` | the command never started | yes |
| `producing` | running, nothing has stalled | no |
| `quiet(<bucket>)` | running, silent for at least `<bucket>` | no |
| `exited(<status>)` | reaped; the capture may still grow | no |
| `final(<status>)` | reaped, and the capture can never grow again | yes |
| `abandoned` | wrapper gone, no reap recorded; capture complete, fate unknown | yes |

`<status>` is the exit code, or `128 + signum`. `exited` and `final` must not be
collapsed: an agent reading a capture at `exited` has been told it may still be short.
Quiet boundaries (30s, 5m, 30m, 2h) are configuration; crossing one is a key change, so a
chatty child reports once, a stalled one per boundary.

Derivation must be **total** — every combination of observable inputs maps to exactly one
key, with no timeouts and no heuristics — and must never yield a terminal key for a child
that is merely starting, since a terminal key licenses the agent to stop watching. The
reap and the exit status are one atomic fact, so no key can name a status never recorded.

## Reporting

At each delivery point, for each child in the **scope** — one agent's view, a subagent's
children never the main thread's — derive the key; report it when it differs from the last
key **reported** there; otherwise say nothing.

- **Every delivery point carries every pending change**, errored tool calls included,
  since that is when an agent goes looking. Channels that cannot be instrumented are
  named, with the pull path as their fallback.
- **A key is retired only once the agent has been told**, on every channel. Recording
  delivery before the write succeeds turns one failed print into permanent loss;
  committing after risks only a duplicate.
- **A report is never silently short.** When it drops lines it says how many and names the
  pull path — silence reads as "nothing else changed".
- **A report line is recognizable.** The agent identifies these lines by their prefix, so
  each begins a line and no arbitrary text can forge one or crowd a change out forever.
  The prompt quotes them, so they change in the same commit as the emitters, and the guard
  checks position, not just presence.
- **A delay is announced.** A delivery point silent because a lock was held is
  indistinguishable from one with nothing to say.

## The pull path

`agent-tools ps` answers what the report cannot: what is true now, for an agent whose
context was compacted while the ledger records those keys as delivered.

- **It answers "what is running now" by default, and states what it withheld** — silence
  about finished children is indistinguishable from "nothing ever ran".
- **Its output is consumed by a program.** Status is carried as fields, not a rendered
  string, so selecting live children filters data rather than matching a display format.
- **Its size is bounded by what is running, not by session history**, and it is ordered
  newest first: the tool carrying it truncates, and truncation must not select by an
  ordering uncorrelated with time. It sets no byte budget of its own.
- **It never suppresses a future report**, and **emits a capture it cannot describe, with
  the reason** — push and pull must never disagree about whether a child exists.
- **Its schema lives with the command** (`--help`), not in the prompt.

## Passthrough

Three tiers: which differences are defects, which are trades, which are wishes.

### Guaranteed

- **Content.** Every byte the child writes to a stream reaches the caller's corresponding
  stream, unmodified and in order within it, for as long as the caller accepts writes.
- **Completeness, or a loud failure.** A forwarded stream is never silently short and a
  capture never silently stops growing; either failure is stated on stderr and in the
  status.
- **Exit code and stdin.** The child's exit code, including `128 + signum`; stdin
  inherited, so pipelines and heredocs behave.
- **The child's signal dispositions are its own** — notably the wrapper's ignored
  `SIGPIPE`, or a pipeline *inside* a wrapped command changes behaviour.
- **Capture failure never kills the child; forward failure never stops the capture.** A
  caller going away is expected, and capturing on is the point; a capture that cannot be
  written is the wrapper's failure, never charged to the child.

### Differs from bare, by design

| Difference | Why it is accepted |
| --- | --- |
| A downstream that quits stops neither the child nor the call, and `pipefail` reports the producer's own status, not `141` | The tool's purpose: `… \| head -3` shows three lines while the whole result lands on disk. Nothing died of `SIGPIPE`; an overrunning call is backgrounded and reported |
| The post-close drain is bounded, and reaching the bound is recorded | A runaway producer would fill the disk, and a capped capture must never pass for complete. Normal operation stays uncapped |
| The wrapper is visible and durable: `pgrep -f` matches it, and it survives signals its child ignores | Visible argv makes `ps aux` diagnosis work, with an opt-out; outliving the child lets it reap, drain and record completeness |
| Unmerged streams have best-effort relative order | Two pipes; that order was lost in the kernel before the wrapper saw it |

### Not achievable

`isatty`, the signalled death a parent sees, process identity and tree shape, and write
atomicity above `PIPE_BUF` cannot be made to match bare: a tee is a pipe, a wrapper is a
process. The prompt must stop promising otherwise.

### The merge rule

Two pipes destroy the order between a child's streams and splice long lines, neither
repairable afterwards — that order exists only in the kernel's scheduling history.

**The child gets one pipe for both streams exactly when the caller's own two descriptors
provably reach one destination that cannot disagree about where the next byte goes** —
same file, both writable, and either both pipes or both appending. Everything else gets
two pipes.

- **Sound, not probabilistic.** Whether two descriptors share an open file description is
  undecidable here, so the conditions make it irrelevant: neither admissible destination
  has an offset to disagree about. Merging distinct destinations would misroute data.
- **Declines rather than guesses**, and takes no flag: the only decisive test would mean
  writing to or seeking the caller's own file, and a flag could only demand the merge it
  refused or refuse one it proved safe.
- **The capture follows the decision** — merged, one file; split, two, which is the
  faithful record since the caller's streams already carry that split.
- **Its reach is an environment assumption.** In the Claude Code Bash tool both descriptors
  are one appending description on one regular file, so ordinary calls merge and `2>&1` is
  a no-op there. Measured, not contracted, so the decision is recorded per capture.

### A drivable core

Every passthrough property above is a property of *processes*, so a test must drive a real
binary, while `run` demands a scope, a ledger, hooks and a config root that bear on none of
them. **The core must be drivable through an entry point needing none of that, and be the
implementation `run` itself uses**, the two shown to agree on forwarded bytes and exit
codes. A parallel copy would prove nothing.

## Durable state

- **The wrapper records facts, never statuses**, and records the reap as it happens, not
  when the pipes close, or a detached descendant delays the exit status indefinitely.
- **A capture becomes visible atomically**; no key honestly describes a half-created one.
- **A merged capture holds one file; the other is absent, not empty** — an empty stderr
  file would read as "no diagnostics".
- **The facts include whatever explains a difference from bare** — downstream closed, drain
  capped, capture failed, streams merged and on which condition — rendered beside the key,
  so `final(0)` never sits beside a capture that stopped growing.
- **A malformed line in an append-only log costs that line, not the file**; the loss is
  counted and stated.

## Current deviations

The shipped binary against the above. Ids match
`notes/agent-tools-run-stress-findings.md`, which holds each reproduction; F9 and F12 there
are accepted differences.

| # | Clause | Deviation |
| --- | --- | --- |
| F1 | drain bound | the forward error is discarded, so a closed downstream goes unnoticed and the drain is unbounded |
| F2 | capture isolation | a capture write failure truncates the caller mid-line and stops the drain: the child dies of `SIGPIPE`, read as its own exit |
| F3 | the merge rule | always two pipes, which in the Bash tool hits every wrapped command, not just `2>&1` ones |
| F4, F13 | starting child | a scan between a capture's creation and its first fact derives `abandoned`; the pull path then hides it |
| F5 | retire after delivery | the ledger commits before the report prints, so one failed print retires those changes for good, on every channel |
| F6, F15 | pull output | uncapped, grows with session history, ordered uncorrelated with time, filterable only by rendered text |
| F7 | log tolerance | the first unparseable line fails the whole events file, and the error is discarded |
| F8 | delay announced | the scope lock waits forever, so every delivery point stalls for the whole hook timeout, silently |
| F10 | — | a relative `AGENT_TOOLS_PARENT_DIR` is reported as unset, pointing at the wrong cause |
| F11 | line prefix | the header is joined to the backgrounding notice by a space, so no line carries the prompt's prefix |
| F14 | never dropped | a multi-byte `--desc` character aborts before any state exists: the command never runs, unrecorded |

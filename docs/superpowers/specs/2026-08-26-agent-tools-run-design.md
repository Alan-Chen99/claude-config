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

- **A status is true when read, not when written.** Whatever last wrote one down may have
  died since.
- **A child whose wrapper died having recorded nothing still has a truthful status.**
  "Unknown" is an answer a reader derives, never a missing one.

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

Every child has **exactly one** key at every moment — every observable combination of
inputs maps to one, with no timeouts and no heuristics. A child still starting, or still
finishing, is never reported terminal. Neither a reboot nor a recycled pid makes a
dead child report running. No key names an exit status that was never observed.

## Reporting

At each delivery point, for each child in the **scope** — one agent's view, a subagent's
children never the main thread's — report the current key when it differs from the last
key **reported** there, otherwise nothing.

- **Every delivery point carries every pending change**, errored tool calls included,
  since that is when an agent goes looking. Uninstrumentable channels are named, with the
  pull path as fallback.
- **A change the agent was not shown is reported again.** At worst it sees a change twice;
  it never fails to see one.
- **A report is never silently short**: when it drops lines it says how many and names the
  pull path, since silence reads as "nothing else changed".
- **A line is recognizable and self-sufficient**: it names the child — the `--desc`, or
  the command, never empty — its key, and where its output is. It begins a line, carrying
  the prefix the agent recognizes, and nothing a child can write forges one or crowds a
  change out. The prompt's quoted lines match what is emitted, replaced when the emitters
  change rather than added to, and checked by position, not mere presence.
- **A delay is announced**: a delivery point silent because a lock was held is
  indistinguishable from one with nothing to say.

## The pull path

`agent-tools ps` answers what the report cannot: what is true now, for an agent whose
context was compacted after those keys were reported and retired.

- **It answers "what is running now" by default, says what it withheld, and keeps that
  retrievable** — a count with no way back is useless after the compaction that made it
  necessary.
- **Its output is consumed by a program.** Status is carried as fields, not a rendered
  string, so selecting live children filters data rather than matching a display format,
  and the schema comes from the command, not the prompt.
- **Its size is bounded by what is running, not by session history**, ordered newest first,
  since the tool carrying it truncates. It sets no byte budget of its own.
- **Push and pull never describe one child differently, nor disagree that it exists.** `ps`
  shows a capture it cannot describe, with the reason, and never suppresses a future report.

## Passthrough

Three tiers: which differences are defects, which are trades, which are wishes.

### Guaranteed

- **The command runs.** What bare would execute, the wrapper executes; the wrapper's own
  inputs, `--desc` among them, never decide whether it does.
- **Content.** Every byte the child writes to a stream reaches the caller's corresponding
  stream, unmodified and in order within it, as long as the caller accepts writes.
- **Completeness, or a loud failure.** A forwarded stream is never silently short and a
  capture never silently stops growing; either failure is stated on stderr and in the
  status. Both, because neither reaches every case: stderr cannot carry a notice about
  stderr, nor about the one destination a merge made of both, and it is the closed
  descriptor in exactly those. The status is what covers them.
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
- **The wrapper is visible and durable**: `pgrep -f` matches it — so a `pkill -f` aimed at
  the command matches it too — and it survives signals its child ignores. Visible argv makes `ps aux` diagnosis work, with an opt-out; outliving
  the child lets it reap, drain and record completeness.
- **Unmerged streams have best-effort relative order.** That order was lost in the kernel
  before the wrapper saw it.

### Not achievable

`isatty`, signalled death, process identity and tree shape, and write atomicity above
`PIPE_BUF` cannot match bare: a tee is a pipe, a wrapper is a process. The prompt must stop
promising otherwise.

### The merge rule

Splitting a child's streams destroys the order between them and splices long lines, neither
repairable afterwards: that order exists only in the kernel.

**The child's two streams share one destination exactly when the caller's own two
descriptors provably reach one destination that cannot disagree about where the next byte
goes** — same file, both writable, both pipes or both appending. Everything else stays
split.

- **Sound, not probabilistic.** Whether two descriptors share an open file description is
  undecidable here, so the conditions make it irrelevant: neither admissible destination
  has an offset to disagree about, and merging distinct ones would misroute data. The
  enumeration stays short on purpose, for two different reasons. A tty or `/dev/null` cannot
  be admitted: character devices are not uniformly unseekable, so the class would be a guess.
  A socket could be — it is provably unseekable, like a pipe — and is left out only because
  no measured caller presents one on both descriptors. Destinations are added when a caller
  needs them, not because they could be. An interactive caller keeps two streams.
- **Declines rather than guesses**, and takes no flag: the only decisive test would mean
  writing to the caller's own file, and a flag could only demand the merge it refused.
- **The capture follows the decision** — merged, one file; split, two, the faithful record
  since the caller's streams already carry that split.
- **Its reach is an environment assumption.** In the Claude Code Bash tool both descriptors
  are one appending description on one regular file, so ordinary calls merge and `2>&1` is
  a no-op. Measured, not contracted; the decision is recorded per capture.

### A second entry point

Every passthrough property above is a property of *processes*, so a test must drive a real
binary, while `run` demands a scope, a ledger and hooks that bear on none of them. **A
second entry point runs a command needing none of that, and agrees with `run` byte for byte
on both forwarded streams and on the exit code** — a disagreement is a defect in whichever
is wrong. Root resolution binds it as it binds every subcommand. The prompt does not teach
it, so agents keep reaching for the entry point with observability.

## The record

- **The exit status appears when the direct child is reaped**, however long a descendant
  holds the streams open.
- **A capture becomes visible whole**; no key honestly describes a half-created one.
- **A merged capture holds one file; the other is absent, not empty** — an empty stderr
  file would read as "no diagnostics".
- **Whatever explains a difference from bare is readable beside the key** — downstream
  closed, drain capped, capture failed, and a split the caller's own descriptors did not
  ask for, with the condition that forced it — so `final(0)` never sits beside a stalled
  capture. A split the caller already had explains nothing, since bare kept those streams
  apart too; the condition is recorded either way.
- **A malformed record costs that record, not the history**; the loss is counted and
  stated.

## Current deviations

The findings record sixteen measured behaviours; two still depart from the above, plus the
unobserved half of a third. Each is reproduced in
`notes/agent-tools-run-stress-findings.md` under the id below, which states its symptom —
this table says only which clause it breaks.

| Clause | Open |
| --- | --- |
| readable beside the key, for a live child | F16, except the merge condition |
| the pull path's output | F15 |
| never reported terminal while starting | F4's read-order half |

F16's other three facts — a closed forward, a capped drain, a failed capture — reach the
record only when the wrapper exits, so a live child can read `producing` beside a capture
that stopped growing. F15 is `ps` ordered by an identifier uncorrelated with time and
sized by session history rather than by what is running; the clause that its output be
carried as fields rather than a rendered string is also unmet, and no finding records it.
F4's remaining half is the read order in `status.rs`: meta is read before wrapper
liveness, so a wrapper that records its reap and exits between the two reads derives
`abandoned` rather than `final(<status>)`. Never observed in roughly 7,000 wrapper starts,
and closing it means re-reading the meta before concluding `abandoned`.

F9 and F12 are accepted differences, not deviations.

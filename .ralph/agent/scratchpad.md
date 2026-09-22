# writing-for-agents loop3 — scratchpad

## Where the objective bites

The sharpest clause is *things that do not require explicit human approval to add,
but require human intervention to remove*. Every other goal follows from that
ratchet. The question to carry into every decision is **what retires this line**.

## Durable method, reusable across rounds

**The compression rule.** Sort every line by what it is; cut in this order,
stopping at the first class that is load-bearing: (1) a **claim** — only claims
can be wrong; delete unless load-bearing and not cheaply re-derivable. (2) a
**restatement** — with two wordings nothing says which governs. (3) a **duplicate
of executable code** — replace with the script's name. (4) a **trap** — what the
reader gets wrong by default, silently. Keep. Deletion is the default; each
*keep* is what needs an argument.

**Price a document by reach before size.** A file that attaches itself to a
session that did not ask for it is cut before a file someone must choose to open.

**A retirement condition names a comparison, not an observation.** "Retire this
when an arm carrying the line does no better than one without it" is the only
form a later round can act on. An unhedged claim merely *appearing* is not that
comparison.

**Buy resolution inside the run, not across runs.** At n=1 a fixture with one
opportunity for the behaviour under test yields a coin flip; several
opportunities that *differ in character* yield the policy the agent applied.

**Arms must differ in kind, not in degree.** A line count separating two arms is
a sample of the baseline's spread. *Wrote a second file or not*, *issued an
imperative or not* are categorical and readable at n=1. *(iter 12)*

**A criterion written from the shape of the failure cannot score a good
outcome.** Write what the good artifact looks like before what the bad one lacks.

**A prose warning inside the thing it warns about does not stop a reader who has
read it.** Convert to a refusal with an escape hatch; the refusal is checkable.

**A pre-registered outcome names the channel it is read from** — delivered
artifact, report, or the `pre_output` fields. And a pre-registered *reading* can
be wrong: iteration 12 withdrew one in its own record rather than take the
reading its fixture could not support. Withdrawing beats honouring.

**A defect that costs nothing this time is the one that accumulates.** Where
maintenance succeeds every round, nothing in the session ever weighs the quantity
that is growing.

**Test the lines already shipped, not only the candidates.** A shipped line with
a named, unmeasured harm outranks any new candidate: it is already costing every
session and only a human can remove it. *(iter 12)*

## Standing `(contract)`

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`.

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit.

> An edit that deletes or renames anything a document can point at sweeps the tree
> for citers in the same commit — `grep -rn --include='*.md' <name> .` — and the
> commit says which were left on purpose.

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call.

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible. Any claim that a rule
> delivered through a tool result caused a behaviour states the tool-call index of
> both.

> A round's runs are **probes** unless it argues otherwise: small fixture, one
> targeted question, read off the artifact by the round itself, no grader and no
> foci. A probe earns keeping only when a later round needs to re-run it.

> **A round that ships no prompt edit may not add a paragraph to
> `sys_prompt/CLAUDE.md`; it may replace one, and the replacement is shorter than
> what it replaced.** Supersedes iteration 9's whole-file token count. Observed in
> iteration 12: the last 70 tokens of a whole-file target bought nothing — paid in
> word-shaving, and finally in deleting a live methodological guard from an
> unrelated paragraph to fund a measured finding. Paragraph-local is the same
> discipline without the cross-subsidy. *(iter 12)*

> **A stored run is retired by the condition its own README states**, and the
> round that notices deletes the directory. The condition may not depend on a
> later round choosing particular work. *(iter 12 amendment)*

> **No claim in `sys_prompt/CLAUDE.md` may be a run narrative.** It carries the
> semantic claim, the hypothesis for it, and the retirement condition. Counts, arm
> labels, byte deltas, dates and fixture descriptions belong to the run's own
> README and to git.

## Iterations 1–11 — `9f6c03a0` → `0f32e2ef`

Detail is in commit messages; anything justifying a prompt line is in
`sys_prompt/CLAUDE.md`. Shipped: `Omit by default` repriced by reach (3), the
`Claim less` hedge endorsement deleted (4), `Say what ends it` (9). Rounds 6–8
established that three wordings aimed at claim-handling all failed because the
node is premise **provenance**, not wording. Round 10 fixed a nine-round harness
contamination (the runner named itself in the tested agent's cwd) and voided
every arm stored before 2026-09-22. Round 11 found that restatement grows by
accretion, not addition.

## Iteration 12 — `0f32e2ef` → `da9f03c9` (+ this commit)

### Critique of iteration 11 (and of the loop's shape)

**C1 (workflow, the substantive one). A shipped line carried a named, unmeasured
harm for eight rounds while every round built new candidates.**
`sys_prompt/CLAUDE.md` had said since iteration 3 that `Omit by default`'s reach
wording *"moves detail out of the loaded file and writes more of it in total …
relocation is growth"*, and iteration 6 narrowed it to the creation case. Five
rounds since then probed lines that do not exist. The user's rule is explicit: a
prompt is added only when negative effects are understood via adversarial
testing. The one bullet aimed at the growth objective might have been a growth
source, and nothing tried to find out.

**C2 (workflow). Iteration 11's `(instruction)` 1 bought nothing at either
outcome** — a positive reopens a family the same round showed nulls for
mechanical reasons, a negative returns to a question already open. Continuity is
not value. **Overridden.**

**C3 (quality). Iteration 11 added a ~200-word paragraph to
`sys_prompt/CLAUDE.md` justifying no prompt line and stating no retirement
condition**, against iteration 10's own contract. Fixed by merging it into the
`Omit by default` paragraph, which is the same mechanism, and giving it one.

**C4 (workflow). A deletion was made conditional on a probe that may never run**
(*"delete the case once (1) has its own fixture"*). Under the override it would
never fire. Deleted unconditionally; the contract now forbids that coupling.

### The round's work

Probe `where-the-bytes-go`, three arms — `Omit by default` priced by reach
(shipped), priced by existence (pre-iteration-3), and absent. Record and full
reading in `prompt-tests/runs/where-the-bytes-go/README.md`.

**The harm does not occur. No arm relocated anything**, and the reason
generalises: the task's subject bounds the edit, so moving a section the task
never named is outside what any wording in this block can reach.
Relocation-as-growth is a *cleanup*-task hazard only. **What the pricing does
reach** is how many places a fact lands in and whether the agent issues
instructions nobody asked for — the unpriced arm wrote the fact into a second
file and added two unrequested imperatives to files that load themselves; both
priced arms did neither. That is the objective's own clause, and it is the first
measured evidence any bullet in this block reaches it.

The reach clause **specifically** stays unexercised: the fixture had one
plausible home, so reach never had two destinations to choose between. The
pre-registration's offer to read A≈B as inertness is withdrawn in the record.

No prompt edit. `sys_prompt/CLAUDE.md` 7417 → 7413 tokens with two paragraph
pairs merged, four paragraphs compressed and two findings added.

Instrument: the scratch-cwd prefix `ptcc`/`ptoc`/`ptcfg` abbreviated the runner.
Iteration 10 applied the no-harness-in-the-cwd rule to the settings file and left
the prefix that named the script. Renamed; no arm had been observed reacting.

### `(instruction)` for iteration 13

1. Delete `prompt-tests/runs/where-the-bytes-go/` and the case with it unless you
   re-run that fixture. This is unconditional — not contingent on which work you
   pick.
2. Two things are open and specified; pick on value, not on continuity.
   (a) **The reach clause.** Needs a fixture with two live destinations of
   different reach, both defensible, for the same fact. Until then the clause has
   no measured behaviour and the prompt is carrying words that might be free.
   (b) **Undischarged user ask.** *"Remove or replace other test cases on the
   'Writing for other agents' block; each one kept you must justify that the test
   case is providing positive value."* Sixteen cases remain under
   `prompt-tests/general/` and no round has done this. A case nobody re-runs is
   the ratchet inside the instrument.
3. If you read a rule-overruling fixture at one arm, state which side of `Say
   what ends it`'s two-answer spread you sampled.

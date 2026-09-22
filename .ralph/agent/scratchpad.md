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

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent then argues it in
whichever direction the task favours. Measured twice on `Omit by default`'s reach
wording: more readership reasoning, none of it reaching the clause's own
conclusion. *(iter 13)*

**A retirement condition names a comparison, not an observation.** "Retire this
when an arm carrying the line does no better than one without it" is the only
form a later round can act on.

**Buy resolution inside the run, not across runs.** At n=1 a fixture with one
opportunity for the behaviour under test yields a coin flip; several
opportunities that *differ in character* yield the policy the agent applied.

**Categorical or it is not evidence, and the test applies per reading, not per
table.** *Wrote a second file or not*, *issued an imperative or not*, *stated
bare or sourced* are readable at n=1; a count is a sample of an unmeasured
spread. Iteration 13 excluded line counts in advance, then read a file count in
the same run — and the excluded number was the only one favouring its prior.
Hardest where the excluded number is the one you want. *(iter 13, 14)*

**A criterion written from the shape of the failure cannot score a good
outcome.** Write what the good artifact looks like before what the bad one lacks.

**A prose warning inside the thing it warns about does not stop a reader who has
read it.** Convert to a refusal with an escape hatch; the refusal is checkable.

**A pre-registered outcome names the channel it is read from**, and a
pre-registered *reading* can be wrong. Withdrawing beats honouring.

**Test the lines already shipped, not only the candidates.** A shipped line with
a named, unmeasured harm outranks any new candidate.

**When an instruction exists to compensate for a harness, fix the harness.** An
`(instruction)` telling a later round to remember something is a rule nothing
approves and only a human retires — the ratchet, reproduced inside the tool
meant to police it.

**A clause no fixture can exercise is not an open question; it is a deletion
candidate with an outstanding test.** *(iter 13)*

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
> what it replaced.**

> **A stored run is retired by the condition its own README states**, and the
> round that notices deletes the directory. The condition may not depend on a
> later round choosing particular work.

> **No claim in `sys_prompt/CLAUDE.md` may be a run narrative.** It carries the
> semantic claim, the hypothesis for it, and the retirement condition. Counts, arm
> labels, byte deltas, dates and fixture descriptions belong to the run's own
> README and to git.

> **An `(instruction)` asserting that work is undone states the command that
> shows it.** Iteration 12 handed forward "no round has done this" about a user
> ask that one grep refutes, and acting on it would have spent a round re-doing
> finished work. *(iter 13)*

## Rounds 1–13 — `9f6c03a0` → `f2737a34`

Detail is in commit messages; anything justifying a prompt line is in
`sys_prompt/CLAUDE.md`, which is the durable home and the one to read before
touching the block. Shipped: the `Claim less` hedge endorsement deleted (4),
`Say what ends it` added (9), `Omit by default` repriced to reach (3) and back
to existence (13). Rounds 6–8: three wordings aimed at claim-handling all failed
because the node is premise **provenance**, not wording. Round 10 fixed a
nine-round harness contamination and voided every arm stored before 2026-09-22.
Round 11: restatement grows by accretion, not addition. Round 12: the task's
subject bounds the edit, so relocation-as-growth cannot occur on a writing task.
Round 13 measured reach on two destinations, found no arm sorted by it, and cut
it; it also deleted `platform-portability` and repaired three colliding case
justifications.

## Iteration 14 — `f2737a34` → `bac7b4ef` (+ this commit)

### Critique of iteration 13

**C1 (workflow, instrument).** Its probe had to plant a directory in the
permanent case corpus, because all four runners resolved `<case>` only under
`prompt-tests/general/`, so the skill's own rule that a probe leaves one README
under `prompt-tests/runs/<probe>/` was unsatisfiable. What shipped instead was
an `(instruction)` asking the *next* round to remember the second half — a thing
that took no approval to add and a human to remove, which is the objective's
sharpest clause, inside the instrument built to police it. Fixed at the cause: a
`<case>` containing a slash is used as given, so a probe is one directory and one
`rm -r`.

**C2 (quality, admissibility).** It excluded R4 (lines added) as inside an
unmeasured spread, then read R6 (code files edited: 3 / 0 / 1) as a ground for
its cut. R6's B-vs-rest contrast is categorical and survives; its 3-vs-1 is the
number R4 was excluded for. The verdict rested on a categorical null, so it
stands; the method note above is amended.

**C3 (fact, and this round's milestone).** `sys_prompt/CLAUDE.md` carried two
retirement conditions beside `Claim less` and neither retired the bullet: one
retired the *hedge-clause deletion*, the other the *line of inquiry*, and the
latter named no comparison an arm can produce. The block's author applied `Say
what ends it` to two of its three bullets and not to the third, leaving a line
every session loads that nothing could end. Iteration 13 saw it was unexercised
and handed it forward rather than running it.

### The round's work

Runner change (C1), then probe `ingest-notes`: an undocumented CSV-into-SQLite
loader, `NOTES.md` for the next agent, six claim opportunities differing in
character, two of them checkable defects verified before launch. Two arms, with
and without the bullet. Record in `prompt-tests/runs/ingest-notes/README.md`.

**Null on the marking criterion, and the one asymmetry ran against the bullet.**
Both arms sourced rather than bare-stated the expiring values, neither hedged or
dated one, both led with the checkable defects. The arm *without* the bullet ran
a lock experiment to settle the one library claim that mattered and rewrote its
own draft hedge once it had the answer; the arm *with* it settled the same claim
by arithmetic and shipped it flat. A blind grader, told only that one line
differed: *"These two documents do not differ on the decisive criterion."*

**Shipped:** the bullet deleted. Prompt 6461 → 6438 `--api` tokens;
`sys_prompt/CLAUDE.md` 7412 → 7372.

**Pre-registration defect, recorded against itself.** Its four outcomes did not
partition the space and its Mixed clause was directionless — read literally it
would have kept the bullet on evidence against it. Withdrawn, not honoured.

**Beware the tokenizer.** Rounds 3–13 sized the prompt with the *local*
tokenizer, this one with `--api` (the repo prefers it for a prompt budget). Same
two revisions: 4237 → 4220 local, 6461 → 6438 api. Earlier figures do not compare.

### `(instruction)` for iteration 15

1. Delete `prompt-tests/runs/ingest-notes/` unless you re-run that fixture.
   Unconditional, and now one `rm -r`.
2. **Round 15 is a cleanup round** (every fifth). The standing item is iteration
   13's: fifteen cases under `prompt-tests/general/`, zero stored runs under the
   current skill, and the loop spends its runs on probes. The skill now says a
   case earns its status by being re-run — apply that to the corpus, or write
   down why the inventory is worth its permanence.
3. `Omit by default` and `Say what ends it` are the whole block now. Neither has
   been run against an arm lacking it since `Say what ends it` shipped at round
   9. Both carry retirement conditions; both are now the oldest unexercised
   lines here, and the block is small enough to test whole.

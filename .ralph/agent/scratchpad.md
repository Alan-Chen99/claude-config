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

**Before writing a clause for a failure, re-run the failure in a second genre.**
If it disappears there, the target is the genre and not the wording, and a clause
aimed at the text will compete with the frame rather than replace it. *(iter 16)*

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

> **Any directory this loop creates names the check that deletes it** — a grep or
> a command, in the file that owns it — and the round that runs the check deletes
> whatever it prints. An argument for why the directory deserves to exist is not
> that check: fifteen cases were defended by uniqueness claims no round could
> falsify, and the corpus stood for fourteen rounds with zero runs in it. *(15)*

> **No claim in `sys_prompt/CLAUDE.md` may be a run narrative.** It carries the
> semantic claim, the hypothesis for it, and the retirement condition. Counts, arm
> labels, byte deltas, dates and fixture descriptions belong to the run's own
> README and to git.

> **A round's decisive reading is made by a reader that is not the round.** One
> reader, holding the artifacts relabelled and the criterion, told neither what is
> being tested nor which arm is which — and its answer is the result, not a check
> on one already written. Iteration 17's own read of its deciding reading found one
> of three unsourced claims and missed the one in the arm it would have kept; the
> blind read reversed the outcome. *(17)*

> **An `(instruction)` asserting that work is undone states the command that
> shows it.** Iteration 12 handed forward "no round has done this" about a user
> ask that one grep refutes, and acting on it would have spent a round re-doing
> finished work. *(iter 13)*

## History — rounds 1–16, `9f6c03a0` → `7dec8051`

Detail is in commit messages; anything justifying a prompt line is in
`sys_prompt/CLAUDE.md`, the durable home and the one to read before touching the
block. Shipped across the loop: `Say what ends it` added (9); `Omit by default`
repriced to reach (3) and back to existence (13); the `Claim less` hedge clause
cut (4) and the whole bullet with it (14); the case corpus bound to the prompt by
one grep, eleven of fifteen cases deleted (15). Failed candidates: five wordings
aimed at claim-handling (6–8, 14) — the node is premise **provenance**, not
wording, and what discharges a premise is an action; one at copy-pricing (12) —
the task's subject bounds the edit, so relocation-as-growth cannot occur on a
writing task; one at warrant-transcription (16) — a rules section's heading is
what flattens a preference, and a clause only competes with the genre. Round 10
fixed a nine-round harness contamination and voided every arm stored before
2026-09-22. Round 15 ran the block whole against an arm with no block: the arms
parted on one row in the block's favour and `Omit by default` was untouched.

## Iteration 17 — `7dec8051` → `b0304c40` (+ this commit)

### Critique of prior iterations

**C1 (workflow, and the round's reason for existing).** `Omit by default`'s
retirement condition has named `prompt-tests/general/halve-the-runbook` since
round 13. In sixteen rounds and 87 commits the case was never run — only its
reference edited twice — while the corpus-binding grep kept it alive *because*
the condition named it. A bullet protected by a test nobody runs, and a case
protected by a bullet it never tests: the ratchet reproduced inside the
instrument built to police it. A retirement condition that names a fixture is
worth nothing until some round pays for the run.

**C2 (workflow, overriding a premise).** Iteration 15's pre-registered outcomes
do not partition. Its result — `r1` parted from `r2` on one R1 row, R4 null —
satisfies outcome 1 (*ship no deletion*) **and** outcome 4 (*delete the half
whose reading was null*, which is `Omit by default`). The round classified it as
outcome 1 and iteration 16 did not notice. Resolving an ambiguity in the
direction that ships no deletion is the ratchet's own direction, and a
pre-registration is worth less than none if the round that wrote it picks the
branch it prefers afterwards. Not repaired by deleting the bullet on that
ambiguity: outcome 4's null came from a reading where both arms had the same
opportunity and both took it, which separates nothing. Repaired by running the
reading that can separate — this round.

**C3 (fact).** Iteration 16's instruction 2 cites "~4,000 words from a 263-word
task and edited three files apiece" as the bullet's own failure shape. That is a
count read off its own arms after they were in, from a probe the same round
deleted, whose transcripts are gitignored — inadmissible under the round's own
`(contract)` (*a reading composed after the arms are in is not admissible*) and
now uncheckable by anyone. Taken as motivation, not as evidence, and the round's
readings are pre-registered instead.

### The round's work

Two arms on the bullet's own named fixture, differing only in line 190.
Pre-registration, readings, outcomes and result:
`prompt-tests/runs/halve-the-runbook/README.md`.

### The round's result

**Outcome 2: `Omit by default` is deleted.** Readings, the blind instrument and the
excluded numbers that argue against the deletion:
`prompt-tests/runs/halve-the-runbook/README.md`. The semantic claim and the
re-entry condition are in `sys_prompt/CLAUDE.md`.
`prompt-tests/runs/retirement-policy/` went with it, by its own stated condition.

The block is now one bullet and its preamble.

### `(instruction)` for iteration 18

1. `# Writing for other agents` has one bullet left and an untested preamble. Before
   any new candidate, run the preamble sentence against an arm without it — it is
   the largest untested thing in the block and nothing has ever isolated it.
2. Do not re-add a line aimed at what an agent *adds*. Six wordings across rounds
   3-17 aimed at claim-handling and at adding; all six are gone. The next candidate
   here fires while a rules file is being written, or it is not written.

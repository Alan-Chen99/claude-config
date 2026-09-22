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

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped across the loop: `Say what ends it` (9); the case corpus
bound to the prompt by one grep, eleven of fifteen cases deleted (15). Deleted:
`Omit by default` (13, 17), `Claim less` (4, 14). Seven candidate wordings failed
(3–8, 12, 14, 16). Round 10 fixed a nine-round harness contamination and voided
every arm stored before 2026-09-22.

## Iteration 17 — `7dec8051` → `e13d1097`

Ran `Omit by default` at its own named retirement fixture, never paid for in
sixteen rounds; pre-registered null reached; bullet deleted. Detail in the commit
messages and in `sys_prompt/CLAUDE.md`. Its critique of 15 and 16 stands except
where iteration 18 overrides below.

## Iteration 18 — `e13d1097` → (this round)

### Critique of prior iterations

**C1 (workflow — instruction 1 overridden).** Iteration 17 handed forward "run the
preamble against an arm without it — it is the largest untested thing in the
block." *Largest untested* is a size argument. The contract forbids picking work
because it is available, and the instruction names no fixture and no reading —
the same defect iteration 17 diagnosed in round 13's retirement condition. Kept
as one arm of this round's design rather than as its milestone: the preamble is
read on the behaviour its own last clause names.

**C2 (fact — a null from a saturated baseline became a general conclusion).**
Iteration 16 ran a warrant-transcription clause on a **handoff note** and got a
null, then wrote into `sys_prompt/CLAUDE.md` that "anything aimed here has to fire
while a rules file is being written, and a disposition asked of the text will
not." Its own memory records why the null is uninformative: in that genre the
agent invents a provenance vocabulary *unprompted*, in both arms. A clause cannot
beat a saturated baseline, so the run bounds nothing about the clause — only
about the genre. The general half of that paragraph is not supported by the run
it was written from, and iteration 17 did not notice.

**C3 (workflow — a stored record with an unreachable deletion condition).**
`prompt-tests/runs/halve-the-runbook/` (41.5 KB, two artifacts) states it is
deleted by "the round that retires or rewrites `Omit by default` again". The
bullet is gone, so that fires only if a round re-adds it. What keeps the
artifacts is a utility argument — *a later round wanting the case's own question
can grade them without re-running* — which is the form the skill names as not a
retirement condition. It was a probe, never promoted; by the skill's own rule it
died with its round. Deleted here; `git checkout f2bfe695 -- <path>` restores it.

### Why this milestone

The one measured, reproduced mechanism behind doc errors is `mem-…-3cef`: an
agent names a premise unverified **in the conversation** and ships the document
asserting it flatly, because every rule in this prompt that fires on uncertainty
names the *reply* as where it goes (grepped, arm-internal: `escalate to the
user`, `Report`, `propagated to the user`, the `uncertainties` record field,
`Required notes`) and none names the artifact — the channel that outlives the
session. That is the objective's "doc errors needing human intervention to
remove", and it is an **act** rather than a disposition, which is what four
failed claim-handling wordings were not. `sys_prompt/CLAUDE.md` already carries
the re-entry condition for a claim-handling line and names the fixture shape it
needs; C2 says the genre that condition requires has never been run. This round
runs it.

### The round's work

One probe, three arms, one fixture: A = HEAD, B = HEAD minus the block preamble,
C = HEAD plus the candidate. Pre-registration, readings and outcomes:
`prompt-tests/runs/handover-notes/README.md`.

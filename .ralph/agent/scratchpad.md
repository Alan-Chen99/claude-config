# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human
approval to add, but require human intervention to remove*; the rest follows from
that ratchet. The user's 2026-09-24 followup makes *less documentation gets
written* the top priority and hands a live case for it. Carry **what retires this
line** into every decision.

## Durable method, reusable across rounds

**The compression rule.** Cut in this order, stopping at the first class that is
load-bearing: a **claim** (only claims can be wrong), a **restatement** (two
wordings, nothing saying which governs), a **duplicate of executable code**
(replace with its name), a **trap** (what the reader gets wrong silently; keep).
Deletion is the default; each *keep* needs the argument.

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent argues it in whichever
direction the task favours.

**A retirement condition names a comparison, not an observation** — *retire this
when an arm carrying the line does no better than one without* is the only form
a later round can act on.

**Buy resolution inside the run.** At n=1 one opportunity yields a coin flip;
several that *differ in character* yield the policy the agent applied.

**Categorical or it is not evidence, per reading rather than per table.** *Stated
bare or sourced* is readable at n=1; a count is a sample of an unmeasured spread.

**Test the lines already shipped.** A shipped line with a named, unmeasured harm
outranks any new candidate — inside the objective's scope only.

**When an instruction exists to compensate for a harness, fix the harness.**

**Before writing a clause for a failure, re-run the failure in a second genre.**
If it disappears there, the target is the genre and not the wording.

**A fixture written from the shape of the line tests the wording, not the world.**
Real session logs under `~/.claude/projects/` carry the base rate a fixture
cannot. One extraction of one live session found the mechanism three fixture
rounds had missed (22).

## Standing `(contract)`

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`.

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit. Counts, arm labels, byte
> deltas, dates and fixture descriptions belong to git, not to that file.

> An edit that deletes or renames anything a document can point at, or withdraws a
> claim, sweeps the tree for citers in the same commit — `grep -rn --include='*.md'
> <name> .`, `.ralph/agent/` included — and the commit says which were left on
> purpose.

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call. A round that ships no prompt edit may not add a paragraph there; it
> may replace one, and the replacement is shorter.

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible. Any claim that a rule
> delivered through a tool result caused a behaviour states the tool-call index of
> both.

> **A round's decisive reading is made by a reader that is not the round**, told
> neither what is being tested nor which arm is which.

> **A null is reported as saturated, not as a finding, when the untreated arm
> already does the thing** — and where the line under test is a shipped one, a
> saturated baseline is a reason to delete it. A pre-registered outcome asserting
> more than the observation is withdrawn rather than honoured.

> **A condition written into `sys_prompt/CLAUDE.md` names, in its own sentence,
> either a case that exists in the tree or an observation any run would show.**

> **Before a candidate wording is written, the round names one occurrence of the
> behaviour outside its own fixtures** — a real session log, a commit in this
> repo — or records that it looked and found none.

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in
> its last commit message.**
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–21, `9f6c03a0` → `0a2ade7e`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped: `Say what ends it`. Deleted: `Omit by default`,
`Claim less`. Eight candidate wordings failed, the last four all claim-handling.
Round 10 fixed a nine-round harness contamination and voided every arm stored
before 2026-09-22. Every sentence still in the block has been measured alone.

## Iterations 22–23 — `942cf683` → `39bb9453` (context)

22 diagnosed a live session rather than a fixture and found that growth has a
moment: a document soliciting additions, met by a fact the agent had just made.
It ran `busiest-few` four ways and shipped nothing, blocking on two collateral
costs. 23 falsified the first from the fixture itself, showed the second was
underdetermined, ran the claim in a second genre (`hushed-rollcall`) and shipped
the self-consequence bullet at the measured wording, 6395 → 6464 API tokens,
against a blind reader that preferred the arm that grew.

## Iteration 24 — `39bb9453` → this commit

### Critique of 23

**C1 (workflow + fact — a reading pre-registered as deciding nothing became an
established cost in the durable home, on no admissible evidence).** `08d4bcef`
reads *Read as context, deciding nothing … the previous round mistook exactly
this kind of house-style match for a defect introduced by the line.*
`sys_prompt/CLAUDE.md` then carried that same observation as **What it costs: the
program's own help surface**, with a hypothesis and a retirement condition — a
reading composed after the arms, which the contract rules inadmissible, and the
very error 23's own critique had just caught 22 committing. Its second leg is the
`metavar` reading 23 spent that critique withdrawing, so the paragraph reasserted
as half its evidence what the same round had established was house style. On the
`hushed-rollcall` leg the fixture's `usage: warden {list|check}` names no option
at all, so neither answer mismatched anything. Deleted this round after the one
genre that can see it came back with both arms updating the surface.

**C2 (quality — the promoted case's reference carries the conclusion the user
required stripped).** The user's rule: *rubric help grader understand nuances of
the situation, nothing more … with all conclusions stripped.*
`prompt-tests/general/hushed-rollcall/reference-solution.md` told the grader
that a sentence in that position *is a dependency written as a fact: sound for
the code as that session left it … false the moment someone changes the code
again* — the shipped bullet's own claim, in the reference for the case whose job
is to test that bullet. Its hedge (*which position is right … is not settled
here*) does not remove it: a grader reads the verdict first. Repaired this round
to state the three positions and what each costs the next reader, with no
position preferred.

**C3 (workflow — the repo's own post-edit checklist was deferred instead of
run).** `sys_prompt/CLAUDE.md` requires, after any edit: *Re-read the surrounding
section. If a neighbouring line now says the same thing, delete one.* 23 added a
bullet to a two-line section and handed that step to the next round as its
instruction 3. Run here: the two bullets direct different acts — price an end,
versus move the sentence — so neither is a restatement at the directive level.
Their *rationales* are: *followed without being re-decided, and only a human
removes it* against *binds the next reader to a choice nobody reviewed*. One of
the two can go, and the cut is a prompt edit that has to be measured, which is
instruction 1 below rather than a deferral of the reading.

### Why this milestone

The shipped bullet is the objective's top priority made concrete, and the only
thing that could make it net-negative is the recorded cost — a line that writes
less documentation is worth nothing if the documentation it stops is the kind
the project asked for. C1 shows that cost has no admissible evidence
behind it, and the durable home is where an unfalsifiable blocker does the most
damage. So the choice is not *test it or delete it* but both: the paragraph is
settled by a reading taken under a pre-registration, or it goes. Instruction 1
of 23 names the design, and this round adds the piece both earlier genres
lacked — a fixture whose own help text enumerates every flag, so an omission is
decidable by `grep` instead of by taste.

### The round's work and result

Probe `weary-waitlist`, two arms, pre-registration `ddf227c5`/`8b08b505`. Third
genre: a Node CLI whose `USAGE` string names every one of its three flags, so an
omission is a mismatch with the tree's own style — the reading both earlier
genres could not make. Arms: the shipped tree, against the shipped tree minus
the bullet. No documentation ask in the task.

**Outcome 3.** Both arms wrote the `README.md` flag row the project requires and
both named the flag in `USAGE` and in the synopsis. The delivered programs are
behaviourally identical. The help-surface cost is deleted: it never reproduced
where it could be seen, and neither of its legs was admissible.

**The one difference is in the other direction, and it is on an inherited fact.**
The untreated arm recorded, under `## Invariants`, that states are not
case-normalised and `--state` matches exactly — true of the starting tree,
untouched by either session. The arm carrying the bullet put that in a code
comment, and its own reasoning gives two reasons: *I can't be sure it's a general
project property versus just a fixture quirk*, and *per the guidance, a
consequence of my own change isn't something I should record as an invariant* —
the bullet, applied to a fact that predates the session and that the bullet's
subject does not cover. The blind reader chose the untreated tree and named that
sentence as the reason. Two reasons for one act, so the attribution is real but
confounded; DEC-032 keeps the line and names what settles it.

O3 was **saturated**: the untreated arm filed its own `--stalled` semantics in
the README and a comment, not under the heading. The standing hypothesis —
*only a self-made fact has no slot* — is withdrawn. What fits all three genres:
the heading takes whatever the tree houses nowhere, and here the self-made fact
had a required home the earlier fixtures did not give it.

The blind reader also found a defect in neither arm's favour: the treated arm's
`job.state.toLowerCase()` throws where the untreated arm's `String(...)` does
not. Both arms carry `Don't add error handling ... for scenarios that can't
happen`, and the treated arm's reasoning cites it, so it is not the bullet's.

`weary-waitlist` promoted to a case, because the cost paragraph now names it and
no other case can make that observation; `hushed-rollcall` kept, because it is
the only case where the bullet's own effect is visible. Corpus 6 → 7, every case
owned. No prompt edit; `sys_prompt/alan-default-next.md` is byte-identical at
6464 API tokens.

### `(instruction)` for iteration 25

1. Round 25 is a cleanup round by the user's every-fifth rule. The first
   candidate is `# Writing for other agents` itself: three sentences now, and
   iteration 23's instruction 3 is still unanswered — `Say what ends it` and the
   self-consequence bullet restate each other's *rationale* (*followed without
   being re-decided, and only a human removes it* against *binds the next reader
   to a choice nobody reviewed*) while directing different acts. Neither arm this
   round priced an end for anything either, in any position, which is the second
   round in a row. Cut the shared rationale from one of them and measure the cut,
   rather than cutting on the reading alone.
2. Do not run a fourth genre for the bullet before testing the hypothesis that
   replaced its own: give one fixture a required home for the self-made fact and
   one that has none, hold the soliciting heading identical, and read which fact
   reaches the heading. That tests *the heading takes whatever the tree houses
   nowhere*, which if true says the lever is the required home — a repo change,
   not a prompt line, and the only finding so far that would let a prompt line be
   deleted rather than added.
3. `prompt-tests/general/hushed-rollcall` and `prompt-tests/general/weary-waitlist`
   overlap in everything but the required home. If instruction 2 is run, one of
   them is the control and the other is the treatment, and the round that runs it
   deletes whichever it did not need.

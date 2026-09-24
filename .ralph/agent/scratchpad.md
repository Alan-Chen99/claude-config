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
> repo — or records that it looked and found none. *(22; see C2)*

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in
> its last commit message.**
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–21, `9f6c03a0` → `0a2ade7e`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped: `Say what ends it` (9). Deleted: `Omit by default`
(13, 17), `Claim less` (4, 14). Eight candidate wordings failed (3–8, 12, 14, 16,
18, 20, 21), the last four all claim-handling. Round 10 fixed a nine-round
harness contamination and voided every arm stored before 2026-09-22. Every
sentence still in the block has been measured alone.

## Iterations 22–23 — `942cf683` → `39bb9453` (context)

22 diagnosed a live session rather than a fixture and falsified the block's
standing explanation of documentation growth: growth has a moment, and a
document soliciting additions supplies it. It ran the `busiest-few` probe four
ways and shipped nothing, blocking on two collateral costs. 23 falsified the
first from the fixture itself — the arms that omitted argparse's `metavar`
matched the one pre-existing option they had — showed the second was
underdetermined between suppression and displacement, then ran the claim in a
second genre (`hushed-rollcall`: bash CLI, an auto-loaded `## Agent Policy`) and
met its pre-registered ship outcome. The self-consequence bullet shipped
byte-identical to the measured arm, 6395 → 6464 API tokens; the probe was
promoted to a case because the paragraph it owns had none; `busiest-few` was
deleted. A blind reader preferred the arm that grew, and 23 shipped against it,
recording the trade in DEC-031 rather than in the prompt.

## Iteration 24 — `39bb9453` → this commit

### Critique of 23

**C1 (workflow — a reading pre-registered as deciding nothing was written into
the durable home as an established cost).** `08d4bcef` reads: *Read as context,
deciding nothing. Whether either arm updates `bin/warden`'s `usage:` line … the
previous round mistook exactly this kind of house-style match for a defect
introduced by the line.* `sys_prompt/CLAUDE.md` now carries that same
observation as **What it costs: the program's own help surface**, with a
hypothesis and a retirement condition. The standing contract says a reading
composed after the arms are in is not admissible; this is one, and it is the
class of error 23's own C1 had just caught 22 committing.

**C2 (fact — the cost's "two-for-two across genres" counts a withdrawn
observation).** Its `busiest-few` leg *is* the `metavar` reading 23 spent its
own critique withdrawing. The paragraph reasserts as half its evidence what the
same round established was the fixture's house style. On the `hushed-rollcall`
leg the fixture's `usage: warden {list|check}` names no option at all, so
neither answer mismatches anything. No leg is admissible, and *documented an
option its own program does not admit exists* overstates what was seen:
`warden check --quiet` works; only a bare error-path usage string omits it.

**C3 (quality — the promoted case's reference carries the conclusion the user
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

### Why this milestone

The shipped bullet is the objective's top priority made concrete, and the only
thing that could make it net-negative is the recorded cost — a line that writes
less documentation is worth nothing if the documentation it stops is the kind
the project asked for. C1 and C2 show that cost has no admissible evidence
behind it, and the durable home is where an unfalsifiable blocker does the most
damage. So the choice is not *test it or delete it* but both: the paragraph is
settled by a reading taken under a pre-registration, or it goes. Instruction 1
of 23 names the design, and this round adds the piece both earlier genres
lacked — a fixture whose own help text enumerates every flag, so an omission is
decidable by `grep` instead of by taste.

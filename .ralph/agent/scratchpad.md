# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human
approval to add, but require human intervention to remove*; the rest follows from
that ratchet. Carry **what retires this line** into every decision.

## Durable method, reusable across rounds

**The compression rule.** Sort every line by what it is; cut in this order,
stopping at the first class that is load-bearing: (1) a **claim** — only claims
can be wrong. (2) a **restatement** — with two wordings nothing says which
governs. (3) a **duplicate of executable code** — replace with its name. (4) a
**trap** — what the reader gets wrong by default, silently; keep. Deletion is
the default; each *keep* needs the argument.

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent then argues it in
whichever direction the task favours. Measured twice on `Omit by default`'s reach
wording: more readership reasoning, none of it reaching the clause's own
conclusion. *(iter 13)*

**A retirement condition names a comparison, not an observation** — *retire this
when an arm carrying the line does no better than one without* is the only form
a later round can act on.

**Buy resolution inside the run.** At n=1 one opportunity for the behaviour under
test yields a coin flip; several that *differ in character* yield the policy the
agent applied, and their agreement is what makes the parting readable.

**Categorical or it is not evidence, and the test applies per reading, not per
table.** *Wrote a second file or not*, *stated bare or sourced* are readable at
n=1; a count is a sample of an unmeasured spread. Hardest to hold where the
excluded number is the one you want. *(13, 14)*

**A criterion written from the shape of the failure cannot score a good
outcome.** Write what the good artifact looks like first.

**Test the lines already shipped.** A shipped line with a named, unmeasured harm
outranks any new candidate.

**When an instruction exists to compensate for a harness, fix the harness.** An
`(instruction)` telling a later round to remember something is a rule nothing
approves and only a human retires.

**A clause no fixture can exercise is a deletion candidate with an outstanding
test, not an open question.** *(13)*

**Before writing a clause for a failure, re-run the failure in a second genre.**
If it disappears there, the target is the genre and not the wording, and a clause
aimed at the text will compete with the frame rather than replace it. *(iter 16)*

## Standing `(contract)`

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`.

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit.

> An edit that deletes or renames anything a document can point at, or withdraws a
> claim, sweeps the tree for citers in the same commit — `grep -rn --include='*.md'
> <name> .`, `.ralph/agent/` included, since that directory is injected into every
> later round whether or not it is consulted — and the commit says which were left
> on purpose. *(19)*

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call.

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible. Any claim that a rule
> delivered through a tool result caused a behaviour states the tool-call index of
> both.

> **A round that ships no prompt edit may not add a paragraph to
> `sys_prompt/CLAUDE.md`; it may replace one, and the replacement is shorter than
> what it replaced.**

> **A probe's own directory is deleted by the round that wrote it**, in the
> commit that puts the claim into `sys_prompt/CLAUDE.md`. Reasoning and the two
> records that forced it: the prompt-tests skill. *(19)*

> **No claim in `sys_prompt/CLAUDE.md` may be a run narrative.** It carries the
> semantic claim, the hypothesis for it, and the retirement condition. Counts, arm
> labels, byte deltas, dates and fixture descriptions belong to git.

> **A round's decisive reading is made by a reader that is not the round.** One
> reader, holding the artifacts relabelled and the criterion, told neither what is
> being tested nor which arm is which — and its answer is the result, not a check
> on one already written. Iteration 17's own read found one of three unsourced
> claims and missed the one in the arm it would have kept; the blind read reversed
> the outcome. *(17)*

> **A null is reported as saturated, not as a finding, when the untreated arm
> already does the thing** — and where the line under test is a shipped one, a
> saturated baseline is a reason to delete it, not a reason to withhold judgement.
> A pre-registered outcome asserting more than that is withdrawn rather than
> honoured. *(18, 19)*

> **An `(instruction)` asserting that work is undone states the command that
> shows it.** Iteration 12 handed forward "no round has done this" about a user
> ask that one grep refutes. *(13)*

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in
> its last commit message** — not in a file here, where writing it changes it.
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000. It sat
> over for two rounds because no line named a command. *(19)*

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–20, `9f6c03a0` → `a9fc0fc6`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped: `Say what ends it` (9, isolated 19). The case corpus is
bound to the prompt by one grep; eleven of fifteen cases deleted (15). Deleted:
`Omit by default` (13, 17), `Claim less` (4, 14). Eight candidate wordings failed
(3–8, 12, 14, 16, 18, 20), the last three all claim-handling. Round 10 fixed a
nine-round harness contamination and voided every arm stored before 2026-09-22.
Every sentence still in the block has now been measured alone: the preamble (18)
and `Say what ends it` (19). 20 built the fixture the claim-handling condition
named and found the baseline saturated on it; what no arm marks is the premise
reached for *while writing a supporting sentence*, asserted flat everywhere.

## Iteration 21 — `a9fc0fc6` → end of round

### Critique of prior iterations

**C1 (workflow — 20's instruction 2 sends the next round outside the objective).**
It ranks the subagent bullet's unverified override clause above any new candidate.
That bullet governs neither documentation nor agent-to-agent text, so measuring it
advances no bullet of the objective; and the objective's ratchet bullet says *your
job is not to clean this, but to ensure there are less new things of this form* —
removing an existing unmeasured clause is the cleaning the user excluded. The
heuristic behind it (*a shipped line with a named unmeasured harm outranks any new
candidate*) is sound, but it was applied outside the block without re-checking
scope. Instruction 2 is overridden. The heuristic is kept and applied **inside**
scope, which is what this round does.

**C2 (workflow — two rules 20 shipped in one round pull against each other).**
*Provenance does not own a case* and *no claim in `sys_prompt/CLAUDE.md` may be a
run narrative* were both added by 20. Three of the five corpus matches were then
narrative sentences, with the owning sentence pointing back at them as *on that
case* — so obeying the second rule deletes the first rule's only evidence and the
grep orders three fixtures destroyed. 20 never re-ran its own grep after writing
them. Fixed: every owning sentence now carries the path; the narrative is gone;
the skill states the requirement.

**C3 (fact — a hypothesis generalised past the two wordings that produced it).**
`sys_prompt/CLAUDE.md` asserted *no wording can make a passing sentence salient*
from two candidates of one shape — both mark or redirect a doubt presumed already
present. Meanwhile the prompt itself supplies a mandatory destination for exactly
that content outside the artifact: `pre_output.record`'s `uncertainties`,
*unresolved observations, unverified assumptions, unconfirmed data*, recorded every
turn. No round has measured it. A claim about all wordings, written while a shipped
line is a live candidate cause, is not supported.

### Why this milestone

C3 names the one untested surface that is inside the objective, is a **shipped**
line rather than a new candidate, and whose repair is a deletion — so it serves the
ratchet bullet instead of working against it. It also explains three nulls at once:
if the doubt is being filed in a tool call every turn, a bullet telling the agent to
put it in the file competes with an IMPORTANT/NO EXCEPTIONS gate and loses.

The probe is one arm, because the decisive reading is available inside a single
session: does the `uncertainties` array name the same premise the delivered document
asserts flat? Only if it does is the two-arm removal test worth running.

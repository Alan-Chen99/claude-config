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

## History — rounds 1–19, `9f6c03a0` → `cf8f2dac`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped: `Say what ends it` (9, isolated 19); the case corpus
bound to the prompt by one grep, eleven of fifteen cases deleted (15). Deleted:
`Omit by default` (13, 17), `Claim less` (4, 14). Seven candidate wordings failed
(3–8, 12, 14, 16, 18). Round 10 fixed a nine-round harness contamination and
voided every arm stored before 2026-09-22. 18 isolated the block's
preamble (kept) on `prompt-tests/general/inherited-project`, and 19 isolated
`Say what ends it` (kept) on `prompt-tests/general/retirement-policy`, so every
sentence still in the block has now been measured alone.

## Iteration 20 — `cf8f2dac` → `f66c6e5c` + this commit

### Critique of prior iterations

**C1 (fact — *nothing is waiting on a measurement* is false).** 19's instruction
says the block is fully accounted for. `sys_prompt/CLAUDE.md`'s claim-handling
paragraph carries a re-entry condition naming *a fixture making one unflagged
external premise load-bearing*, and no such fixture is in the tree. 19 applied its
own stricter test in one direction only — case → is its condition observable —
and never in the other, condition → does its observation point exist. A condition
whose fixture nobody built is the same defect, and it is the one the objective's
doc-errors bullet sits on.

**C2 (workflow — the ownership grep is satisfied by provenance).** *A case is kept
only while `sys_prompt/CLAUDE.md` names it* was built so the corpus cannot outgrow
the prompt. But the grep matches any mention, and three of five cases are matched
by a sentence saying where a past run happened — a statement about what already
occurred, which nothing a later round can falsify. One prose back-reference pins a
directory for as long as the paragraph stands: the objective's own ratchet, inside
the mechanism built to stop it. Fixed in the skill — the grep is necessary, not
sufficient, and only a condition or a recorded user direction owns.

**C3 (workflow — the rule was written, the instance it was written about was
left).** 19 added *a probe's own directory is deleted by the round that wrote it*
and left `prompt-tests/runs/inherited-project/README.md` standing, a probe by its
own first two words, carrying a deletion condition of exactly the deprecated
form — *the round that retires or rewrites the preamble*. Its body is run
narrative, which the user's rules make uncitable across rounds anyway. Deleted
here. Same shape as 19's own C2: a rule reached the file the round was editing and
not the instance beside it.

### Why this milestone

C1 names the only thing in the block a later round is promised and cannot do. Five
claim-handling wordings failed; the sixth (18's channel line) nulled on a baseline
that was saturated because the fixture *stated* the gap, and the round wrote down
what a fixture would need instead. Building it is what decides between *no line
reaches claim-handling* and *no fixture has asked*, and until that is decided the
paragraph is a standing invitation for a seventh wording. It is also the objective
bullet with a measured mechanism behind it: the agent names the premise in the
reply and ships the file asserting it flat.

### The round's work and result

Cleanup half, committed at `611dff06` and `70348021`: the ownership grep now
requires a sentence naming a future observation, and runs in both directions;
`prompt-tests/runs/inherited-project/` deleted. Measurement half: pre-registration
at `86f0da49`, three arms and the blind read at `67665578`, claim at `609b90fc`.

**Outcome 3.** The baseline records the unflagged, load-bearing premise as open
unaided, and settles empirically what the working directory can settle — it
started a Postgres container to find out which way `ON CONFLICT DO NOTHING`
behaves and wrote the reader's own check into the page. A reading every arm
passes separates nothing, so this is saturation and not a finding about either
wording. Nothing shipped; the paragraph is replaced by a shorter one whose
condition points at the premise the run showed is *not* saturated — the one
reached for while writing a supporting sentence, asserted flat in all three arms.

### `(instruction)` for iteration 21

1. Every sentence in `# Writing for other agents` has now been measured alone and
   kept, and both deletions have conditions that can fire. The block is finished
   unless one of those conditions is observed. A round that wants to add to it is
   adding to a block three rounds of deletion produced; say what that buys before
   building a fixture for it.
2. The largest untested surface left is not in this block. `sys_prompt/CLAUDE.md`
   carries an explicit **Unverified** note on the subagent bullet's override
   clause — no green trial's reasoning ever weighed the Agent tool description
   against the prompt — and it names the experiment: remove the clause and re-run
   `prompt-tests/general/subagent-foreground-default`. That is a shipped line
   with a named unmeasured half, which outranks any new candidate.
3. The user's `.ralph/agent/*` ceiling is 6000 tokens by
   `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin`. This round
   went over while adding memories and cut six that had been superseded by, or
   duplicated into, `sys_prompt/CLAUDE.md` and the prompt-tests skill. Deleting a
   memory whose claim now lives in a file the round reads anyway is the cheapest
   room there is.

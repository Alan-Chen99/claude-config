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
> commit that puts the claim into `sys_prompt/CLAUDE.md` — git holds the
> pre-registration and the artifacts, and `git checkout <sha> -- <path>` is one
> command. Two records were left standing by the rounds that wrote them: one whose
> deletion condition could only fire if a round re-added the bullet it tested, one
> whose condition waits on a retirement that may never come. Neither was ever
> re-read, and by the user's own rule run evidence is not citable across rounds,
> so what a record can carry forward is exactly what belongs in
> `sys_prompt/CLAUDE.md` anyway. *(19)*

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

> **The round ends under the user's `.ralph/agent/*` ceiling and says the number.**
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` — under 6000.
> It sat over for two rounds because no line named a command. *(19)*

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–16, `9f6c03a0` → `7dec8051`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped across the loop: `Say what ends it` (9); the case corpus
bound to the prompt by one grep, eleven of fifteen cases deleted (15). Deleted:
`Omit by default` (13, 17), `Claim less` (4, 14). Seven candidate wordings failed
(3–8, 12, 14, 16). Round 10 fixed a nine-round harness contamination and voided
every arm stored before 2026-09-22.

## Iterations 17–18 — `7dec8051` → `5c185783`

17 ran `Omit by default` at its own named retirement fixture and deleted the
bullet. 18 ran a new case (`inherited-project`) with a claim-handling candidate
and a preamble-deleted arm: candidate not shipped, preamble kept on one row, both
on blind readings. Claims and retirement conditions are in `sys_prompt/CLAUDE.md`;
everything else is in the commit messages.

## Iteration 19 — `5c185783` → (see final commit)

### Critique of prior iterations

**C1 (workflow — a hard user budget unmeasured and breached for two rounds).**
`.ralph/agent/*` ≤ 6000 tokens is a user rule, and nothing in the loop ever ran
the command that checks it. Measured now: 5926 at 16's end, 6118 at 17's, 6122 at
18's. Both rounds grew the directory past the ceiling while writing about the
danger of unbounded documentation. The rule's own words — *relocation is growth,
cut before add* — were the round-13 method note, applied to everything except the
file it was written in. Cut here, and the check is now a `(contract)` line with
the command in it, because a rule with no command is what let two rounds miss it.

**C2 (fact — a claim withdrawn from one file and left standing in the file the
next round actually reads).** 18's own C2 established that 16's *the genre
supplies the frame and a prompt clause only competes with it* rests on a
saturated baseline, and deleted the paragraph from `sys_prompt/CLAUDE.md`. The
same conclusion survived verbatim in `.ralph/agent/memories.md`
(`mem-…-53ee`), which is auto-injected into every later round's context — so the
withdrawal reached the file a round consults deliberately and missed the one it
cannot avoid. Memory deleted here. The contract's citer-sweep covers renames of
things a document points at, not claims; extended below.

**C3 (workflow — a probe promoted to a permanent case with no round deciding
to).** 18's record opens *A probe*, and the skill it had just edited says a probe
lives entirely in `prompt-tests/runs/<probe>/` so that one `rm -r` ends it. The
round instead put `task.md`, `fixture/` and `reference-solution.md` into
`prompt-tests/general/inherited-project/` and then named that path in two
`sys_prompt/CLAUDE.md` retirement conditions, which makes the ownership grep keep
it indefinitely. Added without approval, removable only by a human or by a round
that retires the preamble: the objective's own ratchet, built by the round whose
milestone was the ratchet. The case is not deleted — the conditions genuinely
need it — but no later round should read its existence as a promotion argument,
and the `(contract)` below stops the record half of it recurring.

### Why this milestone

`Say what ends it` is the only line this loop has ever shipped and the only one
never isolated: round 15 measured it inside a three-bullet block that no longer
exists, against an arm with no block at all, so the difference it recorded could
have been the preamble's — which 18 then measured separately and kept. With the
block down to a preamble and one bullet, the last unattributed measurement in it
can be closed for the cost of two runs. This is not *largest untested* (C1 of
round 18): the reason is that a shipped line charging every request on a
confounded attribution is the only thing here that a round can both falsify and
remove, and removal is what the objective asks for.

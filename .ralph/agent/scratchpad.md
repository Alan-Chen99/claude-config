# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human
approval to add, but require human intervention to remove*; the rest follows from
that ratchet. The user's 2026-09-24 followup makes *less documentation gets
written* the top priority. Carry **what retires this line** into every decision.

## Durable method, reusable across rounds

**The compression rule.** Cut in this order, stopping at the first load-bearing
class: a **claim**, a **restatement** (two wordings, nothing saying which governs),
a **duplicate of executable code**, a **trap** (keep). Deletion is the default.

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent argues it in whichever
direction the task favours.

**Categorical or it is not evidence.** *Stated bare or sourced* is readable at n=1; a
count is a sample of an unmeasured spread.

**The prompt is the whole stack, not one file.** `sys_prompt/alan-default-next.md`,
`output-styles/`, `conventions/documentation.md` (reached only via `doc-sync`,
`technical-writer`, `quality-reviewer`, `planner`) and `pre_output/record.py` all reach
the session — and none of them reaches an ordinary session here; see DEC-045.

**Before writing a clause for a failure, re-run the failure in a second genre.**
If it disappears there, the target is the genre and not the wording.

## Standing `(contract)`

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md` in the same commit,
> naming what would retire the line. Counts, arm labels, byte deltas, dates and
> fixture descriptions belong to git, not to that file. Each round either edits
> `sys_prompt/alan-default-next.md` or writes there what its own measurement showed
> that makes no edit the right call — as the first justification of a line that had
> none, naming the instrument defect a later round must fix, or else only replacing
> a paragraph, shorter.

> An edit that deletes or renames anything a document can point at, or withdraws a
> claim, sweeps the tree for citers in the same commit — `grep -rn --include='*.md'
> <name> .`, `.ralph/agent/` included — and the commit says which were left on
> purpose. **The round reads `git show --stat` of each commit against what it meant
> to commit and names anything else in the message.**

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. **Outcomes
> are keyed to the blind reader's own questions**, and where the trees of one arm
> disagree on an axis that axis is spread, not effect. A reading composed after the
> arms are in is not admissible.

> **A round's decisive reading is made by a reader that is not the round**, told
> neither what is being tested nor which arm is which.

> **A null is reported as saturated, not as a finding, when the untreated arm
> already does the thing** — and where the line under test is a shipped one, a
> saturated baseline is a reason to delete it. A pre-registered outcome asserting
> more than the observation is withdrawn rather than honoured.

> **A line whose purpose is best-effort surfacing is not ablatable by a saturation
> reading**, because the requirement is a rate across sessions. `## Required notes` is
> one, by the owner's intent. Price it by what it costs when it fires.

> **A round hands one line forward at most once**, and hands it forward **in the
> exact words a later round would run**. A second consecutive round on the same line
> decides it — ships an edit, deletes it, or names the instrument that could decide
> it. "One more reading" is the keep-by-default ratchet, applied to the loop.

> **A condition in `sys_prompt/CLAUDE.md` names, in its own sentence, a runnable case
> and a comparison.** *Retire this when an arm carrying the line does no better than
> one without* is the only actionable form. A condition naming a fixture property
> no named case has is unobservable — check both directions.

> **Before a candidate wording is written, the round names one occurrence of the
> behaviour outside its own fixtures** — a real session log, a commit in this repo — or
> records that it looked and found none. **A session on this machine is read, not
> cited**, and its own `prompt_snapshot` is grepped for the line before it counts as
> evidence about this file. A claim about what an earlier round did is checked against
> git — `git log --all -S'<line>'`, or the result commit's own message — and names the
> commit it checked. **A claim that fixtures differ in some property is quoted from each
> fixture it compares**, deleted ones included.

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in its
> last commit message.** Compress every earlier round's section to one paragraph
> *before* writing your own. `cat .ralph/agent/* | agent-tools count-tokens --file
> /dev/stdin` < 6000. `tasks.jsonl` stays empty.

> **Ask the owner what a line is for before spending a round measuring it.** One topic
> per loop; `skills/telegram-hitl`. Blocking on an answer is cheaper than a round.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–32, `9f6c03a0` → `1497221c`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — read it before
touching the block. Everything else is in the commit messages. Shipped: `Say what ends
it` (11), the self-consequence bullet (23), one duplicated rationale cut out of it (25),
the deletion of `pre_output.record`'s NEVER-uncertainties rule (26), the deletion of the
whole docs order at `alan-default-next.md:15` (28). Deleted also: `Omit by default`,
`Claim less`, the help-surface cost paragraph. Nine say-less wordings failed; 29 kept the
whole `# Writing for other agents` block, refuting its own hypothesis; 30 and 31 both
spent a round on `## Required notes` and shipped nothing, and the owner settled it at 32
by saying the block is best-effort surfacing. 32 built the hidden-docs tree and found the
docs order's repair half saturated there too. `scripts/check-prompt-upstream.py` cannot
run here — `/repos/claude-code-decompiled` is absent. DEC-036, DEC-037.

## Iteration 33 — `1497221c` → `270b5f13`

Decided the exclusion clause and did not ship it. The standalone wording — *A change
owes documentation only where it made a document false; what it could newly explain,
it does not owe* — cut unfalsified prose four- and sevenfold over two depth-fixed
fixtures, repaired everything the bare arm repaired, and survived the adversarial
probe built to kill it (a runbook true in every step while no longer reaching its end:
both arms amended it). What stopped it was unpredicted and replicated: in both probes
the treated arm shipped exactly one sentence false against its own delivered code and
the bare arm none, because what a compression rule cuts first is the qualifying clause
that scoped the claim. The owner's answer was the larger reason — the specimen's
defect is placement, documentation-in-place-of-a-fix, and unowned obligations, not
volume. Full account in `sys_prompt/CLAUDE.md`; the round is `412e675b`, DEC-043.

## Iteration 34 — `270b5f13` → `e6552d3b`

### Critique of 33

**C1 (workflow, verified).** The last edit to `sys_prompt/alan-default-next.md` is
`adb80213`, iteration 28. Rounds 29–33 ran fourteen arms and changed the prompt not at
all. Every one of them picked a line already in the file and asked whether it earns its
place; *saturated* or *confounded* is a true answer and, five times running, the same
one. Nothing in the contract required a candidate to come from a mechanism seen outside
the prompt, so the loop kept reading the prompt for its next subject.

**C2 (fact, verified as unrecorded).** 33's deciding observation — the bare arm shipped
no sentence false against its own code in either probe — is a negative over the bare
arms' ~19 lines of prose against the treated arms' ~4. `412e675b` says how the two
positives were established (*reproduced by running the code*) and nothing about how the
negative was. A negative found by checking four claims exhaustively and nineteen by
sampling is an artifact of effort. The delivered trees lived in `/tmp` and are gone, so
this cannot be re-read; it stands as a defect in how a negative gets recorded.

**C3 (workflow, verified).** The owner listed four alternatives; 33 recorded three, in
`sys_prompt/CLAUDE.md` and here. The dropped one is *research to see if there are a
flag to disable substitution* — the only one that is not documentation at all, and
their first. A round whose subject is faithfulness to a cold reader compressed its own
decisive input. Restored to `sys_prompt/CLAUDE.md`, and put back to the owner.

### `(contract)` added this round

> A round's candidate names the occurrence it came from before it names its wording,
> and that occurrence is outside `sys_prompt/`. Ablating a shipped line is still a
> legitimate milestone, but not two rounds running.

> A negative reading — *no instance in this arm* — states how the search was run and
> over how much text, and is admissible only where it was run the same way over both
> arms. Instances counted asymmetrically are not a comparison.

### Milestone and result — fix-instead-of-note is decided, and not shipped

*A note telling the next reader to avoid something is a fix you did not make. Make the
fix instead.* Two probes, two arms each, pre-registered at `d530b4ed`. Benefit probe:
both arms removed the exposure with the same one-argument change and near-identical
comments; the treated arm wrote one *more* standing sentence than the bare arm. The
adversarial probe, built so the reachable fix sits in a vendored directory a script
replaces wholesale, did not kill it either — neither arm touched it and both wrote the
same guard in the repo's own code. A blind reader attributed nothing to a prompt delta,
found 0 sentences false against the delivered code in either tree (16 and 27 checked),
and traced the prose gap to a review subagent one arm happened to run. Saturated, the
outcome the pre-registration named as likely: `# Error Propagation` and `# Completeness`
already own removing an exposure you just tripped over. DEC-044; account in
`sys_prompt/CLAUDE.md`.

**The larger finding is about the instrument.** `scripts/claude.sh` loads
`/repos/claude-config`'s copy, which is still the pre-round-11 fork — `Omit by default`,
`Claim less`, and the docs order. Nothing this loop has measured is live anywhere. The
owner's specimen ran that fork, so it is a null for the deleted wording and says nothing
about `Say what ends it`. DEC-045; the owner has been asked whether the merge is wanted.

### `(instruction)` for iteration 35

1. **Every fifth round is cleanup, and this is it.** The ceiling is the binding
   constraint: 34 spent most of a round compressing to fit.
2. **The open candidate is the owner's second mispricing**, handed forward once, in the
   words a round would run:
   `- Finding out costs less than the rule you would write instead. Check before you record a constraint.`
   It is the one side of their diagnosis no wording in either fork prices. Its predicted
   harm is an agent that researches and then writes the note anyway — more tokens, same
   ratchet — so pre-register that as the kill.
3. **`Say what ends it` is untested against this failure, not refuted.** The specimen
   lacked it. Running the specimen's own situation under the current block is cheaper
   than writing anything new, and decides whether 2 is needed at all. Do this first.

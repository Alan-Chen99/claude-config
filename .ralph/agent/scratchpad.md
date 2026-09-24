# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human approval to
add, but require human intervention to remove*; the rest follows from that ratchet. The
user's 2026-09-24 followup makes *less documentation gets written* the top priority. Carry
**what retires this line** into every decision.

## Durable method, reusable across rounds

**The compression rule.** Cut in this order, stopping at the first load-bearing class: a
**claim**, a **restatement** (two wordings, nothing saying which governs), a **duplicate of
executable code**, a **trap** (keep). Deletion is the default.

**A line that names a consideration does not deliver the conclusion it argues for.** It
makes the consideration salient, and the agent argues it in whichever direction the task
favours.

**What an agent adds is one fact written as a rule, and the rule's scope is the part no
observation constrained**, so the error lands in the generalisation while the volume barely
moves — which is why every say-less wording measured volume and found nothing.

**A wording is worth running only where what it asks for is an act the agent can picture.**
Naming a property of the sentence being written reaches nothing: 36 put *a rule's scope is a
claim* in front of an arm that then asserted an entailment one render refutes. The two lines
that ever moved anything named an act.

**Categorical or it is not evidence.** *Stated bare or sourced* is readable at n=1; a count
is a sample of an unmeasured spread.

**The prompt is the whole stack, not one file.** `sys_prompt/alan-default-next.md`,
`output-styles/`, `conventions/documentation.md` (reached only via `doc-sync`,
`technical-writer`, `quality-reviewer`, `planner`) and `pre_output/record.py` all reach a
session — and none of them reaches an ordinary session on this machine; DEC-045.

**Before writing a clause for a failure, re-run the failure in a second genre.** If it
disappears there, the target is the genre and not the wording.

## Standing `(contract)`

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md` in the same commit, naming
> what would retire the line. Counts, arm labels, byte deltas, dates and fixture
> descriptions belong to git, not to that file. Each round either edits
> `sys_prompt/alan-default-next.md` or writes there what its own measurement showed that
> makes no edit the right call — as the first justification of a line that had none, naming
> the instrument defect a later round must fix, or else only replacing a paragraph, shorter.

> An edit that deletes or renames anything a document can point at, or withdraws a claim,
> sweeps the tree for citers in the same commit — `grep -rn --include='*.md' <name> .`,
> `.ralph/agent/` included — and the commit says which were left on purpose. The round reads
> `git show --stat` of each commit against what it meant to commit.

> Before launching the arms, the round writes down what each arm's outcome would mean,
> including the outcome that kills the candidate, and commits it. **Outcomes are keyed to
> the blind reader's own questions**, and where the trees of one arm disagree on an axis
> that axis is spread, not effect. A reading composed after the arms are in is not
> admissible, and **the decisive reading is made by a reader that is not the round**, told
> neither what is being tested nor which arm is which.

> **A null is reported as saturated, not as a finding, when the untreated arm already does
> the thing** — and where the line under test is a shipped one, a saturated baseline is a
> reason to delete it. A pre-registered outcome asserting more than the observation is
> withdrawn rather than honoured.

> **A negative reading — *no instance in this arm* — states how the search was run and over
> how much text**, and is admissible only where it was run the same way over both arms.

> **A round hands one line forward at most once**, and hands it forward **in the exact words
> a later round would run**. A second consecutive round on the same line decides it — ships
> an edit, deletes it, or names the instrument that could decide it. "One more reading" is
> the keep-by-default ratchet, applied to the loop.

> **Before a candidate wording is written, the round names one occurrence of the behaviour
> outside its own fixtures and outside `sys_prompt/`** — a real session log, a commit here —
> or records that it looked and found none, **and names the shipped line that already reaches
> the failure, or runs it first.** A session on this machine is read, not cited, and its own
> `prompt_snapshot` is grepped for the line before it counts as evidence about this file.
> Ablating a shipped line is a legitimate milestone, but not two rounds running.

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in its last
> commit message.** Compress every earlier round's section to one paragraph *before* writing
> your own. `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000.
> `tasks.jsonl` stays empty.

> **A question to the owner is sent the moment it is formed, and the round does not emit its
> event until the waiter has exited** — `skills/telegram-hitl`, one topic per loop, a waiter
> under `run_in_background: true`. Their answer has changed the round's conclusion three times;
> the cost of waiting is not the loop's limiting factor and the user has said so. Two rounds
> running wrote this as an intention and closed on an unanswered question, so it is written as
> the mechanism instead.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–35

**1–32, `9f6c03a0` → `1497221c`.** Anything justifying a prompt line lives in
`sys_prompt/CLAUDE.md`; everything else is in the commit messages. Shipped: `Say what ends
it` (11), the self-consequence bullet (23), one duplicated rationale cut out of it (25), the
deletion of `pre_output.record`'s NEVER-uncertainties rule (26), the deletion of the whole
docs order (28). Deleted also: `Omit by default`, `Claim less`, the help-surface cost
paragraph. Every say-less wording failed; 29 kept the whole `# Writing for other agents`
block, refuting its own hypothesis; 30 and 31 both spent a round on `## Required notes` and
shipped nothing, and the owner settled it at 32 — the block is best-effort surfacing. 32
built the hidden-docs tree and found the docs order's repair half saturated there too.
`scripts/check-prompt-upstream.py` cannot run here — `/repos/claude-code-decompiled` is
absent. DEC-036, DEC-037.

**33–35, `1497221c` → `3c5bec5e`.** Three candidates decided, none shipped. 33: the exclusion
clause cuts unfalsified prose four- and sevenfold and in both probes shipped one sentence false
against its own code where the bare arm shipped none — a compression rule cuts the qualifying
clause that scoped the claim. 34: *a note telling the next reader to avoid something is a fix
you did not make*, saturated in the two genres it was run in; its larger finding is DEC-045,
that `scripts/claude.sh` loads `/repos/claude-config` and nothing this loop measures is live.
35: *finding out costs less than the rule you would write instead* was never written, both legs
doing it unprompted; what all three of its legs did do was turn the one instance into a
project-wide rule, two of three false in the added scope. DEC-043 to DEC-046.

## Iteration 36 — `3c5bec5e` → (this round)

### Critique of 35

**C1 (workflow, verified from the channel).** 35 wrote *a question is sent the moment it is
formed and blocked on before the round closes* into the contract, as its own fix for 34's
fifteen-minute close — then closed with message 84, the merge question, unanswered: the last
inbound is 83, replying to 82. A clause its own author does not keep is not a clause, so it is
rewritten as a mechanism: the round does not emit its event until the waiter has exited.

**C2 (fact, verified).** The wording 35 handed forward — *one instance does not support a
project-wide rule* — forbids width, and message 81, which 35 had read and quoted, asks for width
about the very specimen it cites: the inventory row is "actually ok but can be more shorter and
**general**". 35 never checked the candidate against it. This round ran a wording aimed at
*unchecked* width instead, and put the contradiction to the owner before launching.

**C3 (workflow, admitted by 35, repaired here).** 35's scope finding is a reading of three legs
differing in whole prompts, composed after the arms were in — inadmissible by its own contract —
and it was handed forward anyway. Repaired rather than rejected: the candidate now rests on the
owner's specimen `0d3c560b`, which asserts *"`$N` is the (N+1)-th whitespace-separated word"* off
a single-digit probe and is repaired for `$10` one commit later in `b394ebbf`.

**C4 (fact, minor).** Two counts of one thing: the scratchpad said "eleven say-less wordings",
`sys_prompt/CLAUDE.md` said "nine". Neither is checkable without re-reading 35 commit messages,
and a count is what this contract sends to git. Both now say *every*, which is falsifiable by one
counter-example.

### Result — the scope wording is decided and not written

`pewter-dial` (deleted; `git checkout 4cb01c30 -- prompt-tests/runs/pewter-dial`), two arms on
one fixture, pre-registered at `4cb01c30`. Account in `sys_prompt/CLAUDE.md`. In short: the arm
carrying *A rule's scope is a claim … narrow it to those you did, or check the rest* wrote that
two entries sharing one template *so* differ in the dataset and nothing else — false, one render
with differing `run_date` refutes it — and never reached `run_date`, where the bare arm stated
that coupling correctly. The pre-registered ship condition was *no added general sentence false
against the tree*; it was not met, and it was fixed before the runs precisely because this round
wrote the sentence it was testing. That retires the scope line and the last of 35's
carry-forward.

**The unpre-registered finding is repair, and it contradicts a saturation reading this loop has
been leaning on.** The change falsified `templates/CLAUDE.md`'s *one file per report, named after
it*. The treated arm rewrote the sentence. The bare arm quoted it in its own reasoning, saw the
contradiction, and decided to *add a minimal amendment documenting this exception* beneath it,
leaving a file that asserts and denies one rule; the blind reader called that the most expensive
wrong text in either tree. Iteration 32 read the repair half of the docs order as saturated, on a
tree whose staleness was a set of falsified *statements*. A stale **rule** is not the same object:
the agent reads it as a standing convention belonging to someone else and annotates around it
rather than overwriting it. That is the user's "outdated docs" case, unfixed, and it is the first
failure this loop has found that a shipped line does not already reach.

### `(instruction)` for iteration 37

1. **Establish the occurrence before writing the wording**, which is the clause 34 and 35 both
   broke: find a real amendment-instead-of-repair outside `sys_prompt/` and outside a fixture —
   a session log on this machine, or a commit in this tree where a rule a change falsified was
   annotated rather than edited. If there is none, say so and the candidate dies there.
2. Only then a wording, and it must name the act: editing the sentence. Pre-register the kill as
   an arm that overwrites a rule its change did *not* falsify.
3. 40 is the cleanup round; 37 is not.

Iteration 36: `3c5bec5e` → `997a5c02`, plus this line's own commit. `.ralph/agent/*` at
close: the number is in that commit's message.

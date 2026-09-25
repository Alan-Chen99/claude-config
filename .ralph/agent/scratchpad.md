# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human approval to
add, but require human intervention to remove*. The user's 2026-09-24 followup makes *less
documentation gets written* the top priority. Carry **what retires this line** into every
decision.

## Durable method, reusable across rounds

**The compression rule.** Cut in this order, stopping at the first load-bearing class: a
**claim**, a **restatement** (two wordings, nothing saying which governs), a **duplicate of
executable code**, a **trap** (keep). Deletion is the default.

**A line that names a consideration does not deliver the conclusion it argues for** — it
makes the consideration salient and the agent argues it in whichever direction the task
favours. **A wording is worth running only where what it asks for is an act the agent can
picture**; naming a property of the sentence being written reaches nothing (36).

**What an agent adds is one fact written as a rule, and the rule's scope is the part no
observation constrained**, so the error lands in the generalisation while the volume barely
moves — which is why every say-less wording measured volume and found nothing.

**Scope decides whether an agent fixes a defect or writes it down.** A fixture that makes
the fix *the task* reads saturated; the owner's specimen, where the defect was tripped over
while verifying something else, wrote three notes and left the one-line fix undone. 38's
hypothesis, measured in `prompt-tests/runs/partial-regeneration`: fixing what the user did
not ask about is an unrequested edit, so documenting reads as the conservative in-scope move.

**Categorical or it is not evidence.** A count is a sample of an unmeasured spread.

**A saturation reading taken on fixtures does not transfer to this repository's own
documents** — 37 found a falsified claim standing in the public `README.md` through four
rounds measuring that same failure in fixtures.

**The prompt is the whole stack**: `alan-default-next.md`, `output-styles/`,
`conventions/documentation.md` (reached only via `doc-sync`, `technical-writer`,
`quality-reviewer`, `planner`) and `pre_output/record.py` — none of which reaches an ordinary
session here (DEC-045). **Re-run a failure in a second genre before writing a clause for it**;
if it disappears there, the target is the genre.

## Standing `(contract)`

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md` in the same commit, naming
> what would retire the line. Counts, arm labels, byte deltas, dates and fixture descriptions
> belong to git, not to that file. Each round either edits `sys_prompt/alan-default-next.md`
> or writes there what its measurement showed that makes no edit right — naming the
> instrument defect a later round must fix, or replacing a paragraph, shorter.

> An edit that deletes or renames anything a document can point at, or withdraws a claim,
> sweeps the tree for citers in the same commit (`grep -rn --include='*.md' <name> .`,
> `.ralph/agent/` included) and says which were left on purpose. The round reads
> `git show --stat` of each commit against what it meant to commit.

> Before launching the arms, the round commits what each outcome would mean, including the
> one that kills the candidate. **Outcomes are keyed to the blind reader's own questions**;
> where one arm's trees disagree on an axis, that axis is spread, not effect. A reading
> composed after the arms are in is inadmissible, and **the decisive reading is made by a
> reader that is not the round**, told neither what is tested nor which arm is which.

> **The fixture is built from an occurrence, not from the line**, and the probe's `README.md`
> names the commit or session it models before the fixture exists. Rounds 33–36 each wrote
> its fixture from the shape of its wording and all four killed their own candidate.

> **Candidates in preference order: a shipped line (ablation), a line the owner named, a line
> this round invented.** Ablation is a legitimate milestone but not two rounds running.
> Before any candidate the round **names one occurrence outside its own fixtures and outside
> `sys_prompt/`**, and **names the shipped line that already reaches the failure, or runs it
> first**. A session here is read, not cited, and its `prompt_snapshot` is grepped for the
> line before it counts as evidence about this file.

> **A round does not hand a wording forward** — it measures its candidate or deletes it. An
> `(instruction)` may name a question, an instrument defect or a cleanup, never a line to run.
> The clause this replaces failed on all three outings (36→37→38): each receiver rewrote the
> wording it was then left to judge, the bias the clause existed to avoid.

> **A null is reported as saturated, not as a finding, when the untreated arm already does the
> thing** — and a saturated baseline under a shipped line is a reason to delete it. An outcome
> asserting more than the observation is withdrawn, not honoured. **A negative reading — *no
> instance in this arm* — states how the search was run and over how much text**, and is
> admissible only where it was run the same way over both arms.

> **A question to the owner is sent the moment it is formed, and the waiter's exit gates the
> round's last commit, not only its event** — `skills/telegram-hitl`, one topic per loop, a
> waiter under `run_in_background: true`, **keyed to activity in the topic, not to a reply
> id**, and the log re-read after the round's own last send. 36 closed 33 seconds after an
> instruction it never read; 37 closed 68 seconds after asking a question answered at 127.
> Waiting is not this loop's limiting factor and the user has said so.

> **The round ends under the `.ralph/agent/*` ceiling, with the number in its last commit
> message.** Compress every earlier round to one paragraph *before* writing your own.
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000. `tasks.jsonl`
> stays empty. Rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–37

**1–32, `9f6c03a0` → `1497221c`.** Anything justifying a prompt line lives in
`sys_prompt/CLAUDE.md`, which names every line these rounds shipped or deleted; everything
else is in the commit messages. Every say-less wording failed; 29 kept the whole block,
refuting its own hypothesis; 30 and 31 both spent a round on `## Required notes` and shipped
nothing, and the owner settled it at 32 — the block is best-effort surfacing.
`scripts/check-prompt-upstream.py` cannot run here: `/repos/claude-code-decompiled` is
absent. DEC-036, DEC-037.

**33–37, `1497221c` → `1f2ca9de`.** Four candidates decided and none shipped, each written
and judged by the round that ran it; 37 then spent its round on the owner's two directions
instead. 33: the exclusion clause cuts unfalsified prose four- and sevenfold and shipped one
sentence false against its own code in both probes. 34: *a note telling the next reader to
avoid something is a fix you did not make* — saturated in two genres, and its larger finding
is DEC-045. 35: *finding out costs less than the rule you would write instead* was never
written, both legs doing it unprompted; all three legs turned one instance into a
project-wide rule, two of three false in the added scope. 36: the scope wording did not
prevent the very entailment error it named, and its unpre-registered finding was that a
stale **rule** gets annotated around rather than repaired, leaving a file asserting and
denying one rule. 37: merged `staging` (16 commits, no conflicts) on the owner's #93, ran the
public-ready pass on this branch's parts for #96 — two falsified `README.md` claims and one
stale line citation repaired by editing the sentence — and withdrew two index rows on #98.
DEC-043 to DEC-048.

## Iteration 38 — `1f2ca9de` → (this round)

### Critique of 37

**C1 (workflow).** 37 diagnosed 36 for closing 33 seconds after an instruction it never
read, wrote the topic-keyed-waiter clause for it — and then ended its own round 68 seconds
after sending a question, at a point where the owner's answer was 127 seconds away. #100
(*"you can decide that yourself … you dont need to ask me for decision for
what-prompt-to-test"*) went untaken until this round, and it retires 37's instructions 1–2
for 38, which had pinned the next round to a candidate the owner never asked for. The clause
was written against the symptom it had just seen — not reading — while the mechanism is not
waiting, and the round's own `#99` said "silence is fine as an answer" 68 seconds before
closing. Fixed in the contract above: the waiter's exit gates the last commit.

**C2 (workflow).** 37's own C2 said the hand-forward clause must bind or go, and then 37
handed the same candidate forward a third time without the exact words the clause requires
— leaving 38 to write the wording it would judge, which is the bias that decided 33–36. A
clause whose three outings all produced a deferral is a deferral mechanism. Deleted above
and replaced by: measure it or delete it.

**C3 (fact).** 37 had the discrepancy in hand and read it as venue — fixtures versus this
repository's real documents — when a sharper and falsifiable reading was available: every
fixture from 33 to 36 made the fix *the task*, and the owner's specimen `0d3c560b` did not.
Under that reading 37's instruction 1 for 38 (hunt for an agent annotating instead of
repairing, outside fixtures) was aimed at a search whose answer was already committed in
this tree — `0d3c560b` is the instance — and the round would have spent itself looking for
what it already had. What was actually missing was not an occurrence but a mechanism.

### What this round did

Took the shipped `# Writing for other agents` block as the candidate — an ablation, so
nothing measured here is a wording this round wrote — and built
`prompt-tests/runs/partial-regeneration` from `0d3c560b` rather than from the block: one
small bounded task, two silent defects outside its scope, one with a one-line fix and one
needing a decision only the owner can make. Pre-registration committed at `7800768a` before
either arm ran. Result and conclusion below.

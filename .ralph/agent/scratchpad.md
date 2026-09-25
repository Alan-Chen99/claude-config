# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human approval to
add, but require human intervention to remove*. The user's 2026-09-24 followup makes *less
documentation gets written* the top priority. Carry **what retires this line** into every
decision.

## Durable method, reusable across rounds

**The compression rule.** Cut in this order, stopping at the first load-bearing class: a
**claim**, a **restatement** (two wordings, nothing saying which governs), a **duplicate of
executable code**, a **trap** (keep). Deletion is default.

**A line that names a consideration does not deliver the conclusion it argues for** — it makes
the consideration salient and the agent argues it whichever way the task favours. **A wording is
worth running only where what it asks for is an act the agent can picture**; naming a property
of the sentence being written reaches nothing (36).

**What an agent adds is one fact written as a rule, whose scope is the part no observation
constrained**, so the error lands in the generalisation while the volume barely moves — which is
why every say-less wording measured volume and found nothing.

**Scope decides whether an agent fixes a defect or writes it down**, and a fixture making the
fix *the task* cannot see it. Shipped at 38.

**Categorical or it is not evidence**; a count is a sample of an unmeasured spread. **A
saturation reading on fixtures does not transfer to this repository's own documents** — 37
found a falsified `README.md` claim standing through four rounds measuring that failure in
fixtures.

**The prompt is the whole stack**: `alan-default-next.md`, `output-styles/`,
`conventions/documentation.md` (via `doc-sync`, `technical-writer`, `quality-reviewer`,
`planner`) and `pre_output/record.py` — none reaching an ordinary session here (DEC-045).
**Re-run a failure in a second genre before writing a clause for it**; if it disappears there,
the target is the genre.

## Standing `(contract)`

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md` in the same commit, naming what
> would retire the line. Counts, arm labels, byte deltas, dates and fixture descriptions belong
> to git. Each round either edits `sys_prompt/alan-default-next.md` or writes there what its
> measurement showed that makes no edit right — naming the instrument defect a later round must
> fix, or replacing a paragraph, shorter.

> An edit that deletes or renames anything a document can point at, or withdraws a claim,
> sweeps for citers in the same commit (`grep -rn --include='*.md' <name> .`, `.ralph/agent/`
> included) and says which were left on purpose. The round reads `git show --stat` of each
> commit against what it meant to commit.

> Before launching the arms, the round commits what each outcome would mean, including the
> one that kills the candidate. **Outcomes are keyed to the blind reader's own questions**;
> where one arm's trees disagree on an axis, that axis is spread, not effect. A reading
> composed after the arms are in is inadmissible, and **the decisive reading is made by a
> reader that is not the round**, told neither what is tested nor which arm is which.

> **The fixture is built from an occurrence, not from the line**, and the probe's `README.md`
> names the commit or session it models before the fixture exists. Rounds 33–36 each wrote
> its fixture from the shape of its wording and all four killed their own candidate.

> **Candidates in preference order: a shipped line (ablation), a line the owner named, a line
> this round invented** — ablation being a legitimate milestone but not two rounds running.
> Before any candidate the round **names one occurrence outside its own fixtures and outside
> `sys_prompt/`**, and **names the shipped line that already reaches the failure, or runs it
> first**. A session here is read, not cited, and its `prompt_snapshot` grepped for the line
> before it is evidence about this file. **A round does not hand a wording forward** — it
> measures its candidate or deletes it, and an `(instruction)` may name a question, an
> instrument defect or a cleanup, never a line to run. That clause failed on all three outings
> (36→37→38): each receiver rewrote the wording it was then left to judge.

> **A null is reported as saturated, not as a finding, when the untreated arm already does the
> thing** — and a saturated baseline under a shipped line is a reason to delete it. An outcome
> asserting more than the observation is withdrawn, not honoured. **A negative reading states
> how the search was run and over how much text**, and only where it was run the same way over
> both arms.

> **A question is sent the moment it is formed, and the round holds its last commit for the
> waiter's exit or ten minutes past its own last send, whichever comes first** —
> `skills/telegram-hitl`, one topic per loop, a waiter under `run_in_background: true`, **keyed
> to activity in the topic, not to a reply id**, the log re-read directly after the last send,
> and the last commit saying whether the waiter is still live. 36 closed 33 seconds after an
> instruction it never read; 37 closed 68 seconds after asking a question answered at 127. The
> bound is 38's own correction: unbounded, it would have held a finished round 24 hours on a
> question whose text said silence was an answer. An unbounded gate is not waiting, it is not
> closing.

> **The round ends under the `.ralph/agent/*` ceiling, with the number in its last commit
> message.** Compress every earlier round to one paragraph *before* writing your own.
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000; `tasks.jsonl` stays
> empty. Rules for running, grading and deleting prompt tests are in
> `.claude/skills/prompt-tests/SKILL.md`, not restated here.

## History — rounds 1–37

**1–32, `9f6c03a0` → `1497221c`.** What justifies a prompt line is in `sys_prompt/CLAUDE.md`,
which names every line these rounds shipped or deleted; the rest is in the commit messages.
Every say-less wording failed; 29 kept the whole block, refuting its own hypothesis; 30 and 31
both spent a round on `## Required notes` and shipped nothing, and the owner settled it at 32 —
best-effort surfacing. `scripts/check-prompt-upstream.py` cannot run here:
`/repos/claude-code-decompiled` is absent. DEC-036, DEC-037.

**33–37, `1497221c` → `1f2ca9de`.** Four candidates decided and none shipped, each written and
judged by the round that ran it; 37 then spent its round on the owner's two directions. 33: the
exclusion clause cuts unfalsified prose four- and sevenfold and shipped one sentence false
against its own code in both probes. 34: *a note … is a fix you did not make* — saturated in
two genres, and its larger finding is DEC-045. 35: *finding out costs less than the rule* was
never written, both legs doing it unprompted; all three legs turned one instance into a
project-wide rule, two of three false in the added scope. 36: the scope wording did not prevent
the entailment error it named, and a stale **rule** got annotated around rather than repaired.
37: merged `staging` on #93, ran the public-ready pass for #96 — two falsified `README.md`
claims and a stale line citation repaired by editing the sentence — and withdrew two index rows
on #98. DEC-043 to DEC-048. Everything else about them is in `sys_prompt/CLAUDE.md` and the
commit messages.

## Iteration 38 — `1f2ca9de` → (this round)

### Critique of 37

**C1 (workflow).** 37 diagnosed 36 for closing 33 seconds after an instruction it never read,
wrote the topic-keyed-waiter clause for it, then ended its own round 68 seconds after sending a
question the owner answered at 127. #100 — the round decides the candidate itself, no
need to ask which prompt to test — went untaken until this round, and it retires 37's
instructions 1–2 for 38, which had pinned this round to a candidate the owner never asked for.
Its clause addressed the symptom where the mechanism is not waiting.

**C2 (workflow).** 37's own C2 said the hand-forward clause must bind or go, then handed the
same candidate forward a third time without the words the clause requires — leaving 38 to write
the wording it would judge, the bias that decided 33–36. Deleted above.

**C3 (fact).** 37 read the fixtures-versus-real-documents discrepancy as venue when a
falsifiable reading was available: every fixture from 33 to 36 made the fix *the task*, and the
specimen did not. Under it, 37's instruction to hunt for an occurrence outside fixtures pointed
at a search whose answer was already committed here — `0d3c560b` — so the round would have spent
itself looking for what it had. What was missing was a mechanism, not an occurrence.

### What this round did

Took the shipped `# Writing for other agents` block as the candidate — an ablation, so nothing
measured was a wording this round wrote — and built the probe from `0d3c560b` rather than from
the block: one bounded task, two silent defects outside it, one with a one-line fix and one
needing a call the tree does not settle. Three runs, each pre-registered and committed first.

**The ablation came out arm-independent on both defects**, so that block is not what decides a
defect found outside the task. Run 1's defect was undiscoverable — verification in both arms
was file identity and mtime, and no rendered page's bytes were ever on screen; the instrument
was fixed in-round rather than handed on. Run 2, with the defect in the build's own stdout:
both arms saw it, named the one-line fix, and left it undone *on scope*, in their own words.
**And the specimen did raise its defect** — a headed paragraph, the probe table, and a
Required-notes line offering the revert — so the owner's *"never raised to me"* is false for
it; what is missing is that the fix is never named as an option anywhere in that response.
Reporting is saturated. The owner then settled the trade twice: #102, unrequested fixes are
wanted; #104, *"to report to me it still have to do the work of understanding how it works. i
have one sensible option which is for this to get fixed."*

**Shipped**, under `# Completeness`'s No Deferral Rule, whose *escalate* clause was licensing
the stop: *A defect found on the way is one of those items: reporting it is not resolving it.
Fix it when the only thing stopping you is that nobody asked; escalate when the call is
genuinely someone else's. Report both.* Run 3's treated arm fixed the cheap defect and pinned it
with a test the existing suite could not have caught, left the other unrenamed and escalated,
and reported both; a blind grader holding both transcripts volunteered *"This is the one defect
the two sessions handle differently."* Its two costs are with the line in
`sys_prompt/CLAUDE.md`, whose retirement condition names `f75aceb6` to restore the deleted
probe.

### `(instruction)` for iteration 39

1. The treated side is one draw. Restore the probe and check the blind reader's two costs — the
   treated arm filed its own fix under *unexpected change* rather than as a decision the owner
   could decline, and offered a narrower menu on the escalated defect. Whether that belongs to
   the new line or to `## Required notes` is unmeasured, and is the one thing that could still
   make the line worse than nothing. #105 asks the owner which they want.
2. The owner's aggregate-pricing diagnosis (memories, #91) is untouched and nothing measured in
   38 rounds reaches it. Next candidate; it needs an instrument spanning sessions.
3. 40 cleans up.

Channel: #100, #102 and #104 each answered inside two minutes; #105 unanswered at close after
ten, waiter left live. 39 reads the log first.

Iteration 38: `1f2ca9de` → the commit carrying this line; ceiling at close in its message.

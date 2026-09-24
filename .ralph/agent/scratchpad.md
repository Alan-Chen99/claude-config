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
observation constrained.** So the error lands in the generalisation while the volume barely
moves — which is why eleven say-less wordings measured volume and found nothing. Measured at
35: three legs each turned one instance into a project-wide rule, two of the three false
against their own tree, always in the added scope.

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

> **A question to the owner is sent the moment it is formed and blocked on before the round
> closes** — `skills/telegram-hitl`, one topic per loop, a waiter under
> `run_in_background: true`. Their answer has changed the round's conclusion three times;
> the cost of waiting is not the loop's limiting factor and the user has said so.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–34

**1–32, `9f6c03a0` → `1497221c`.** Anything justifying a prompt line lives in
`sys_prompt/CLAUDE.md`; everything else is in the commit messages. Shipped: `Say what ends
it` (11), the self-consequence bullet (23), one duplicated rationale cut out of it (25), the
deletion of `pre_output.record`'s NEVER-uncertainties rule (26), the deletion of the whole
docs order (28). Deleted also: `Omit by default`, `Claim less`, the help-surface cost
paragraph. Nine say-less wordings failed; 29 kept the whole `# Writing for other agents`
block, refuting its own hypothesis; 30 and 31 both spent a round on `## Required notes` and
shipped nothing, and the owner settled it at 32 by saying the block is best-effort
surfacing. 32 built the hidden-docs tree and found the docs order's repair half saturated
there too. `scripts/check-prompt-upstream.py` cannot run here — `/repos/claude-code-decompiled`
is absent. DEC-036, DEC-037.

**33, `1497221c` → `270b5f13`.** Decided the exclusion clause and did not ship it: it cut
unfalsified prose four- and sevenfold and repaired everything the bare arm did, but in both
probes the treated arm shipped exactly one sentence false against its own code and the bare
arm none, because what a compression rule cuts first is the qualifying clause that scoped
the claim. The owner's answer was the larger reason — the specimen's defect is placement,
documentation-in-place-of-a-fix, and unowned obligations, not volume. `412e675b`, DEC-043.

**34, `270b5f13` → `e6552d3b`.** *A note telling the next reader to avoid something is a fix
you did not make* — saturated in two genres, not shipped; both arms took the one-argument fix
on the benefit probe and neither touched the vendored directory on the adversarial one, and
a blind reader attributed nothing. Its larger finding is DEC-045: `scripts/claude.sh` loads
`/repos/claude-config`, still the pre-round-11 fork, so nothing this loop measures is live
and the owner's specimen ran `Omit by default`. DEC-044.

## Iteration 35 — `15b6682d` → (this round)

### Critique of 34

**C1 (workflow, verified).** 34 asked the merge question at 18:15:30 and closed at 18:30:46 —
fifteen minutes — having found that no session on this machine runs anything the loop has
produced. That is the one open question that decides whether any round's product exists, and
the contract already said blocking is cheaper than a round; the user's own followup says the
same in stronger words. Fix: the ask-the-owner clause now says *sent when formed, blocked on
before close*, and this round ran the waiter.

**C2 (fact/workflow, verified).** 34 left the tree dirty. `git diff` at this round's start
showed an uncommitted DEC-045 edit that contradicts the commit it sits on: the committed text
records the owner's acknowledgement, the working copy says only that the question was asked.
Channel message 83 — *i see, that was my mistake, acknoledged; your point is correct* —
confirms the committed text. A later round reading the tree rather than the log would have
recorded a fact that did not happen. Discarded; the checklist item exists and was skipped.

**C3 (workflow, verified from 34's own text).** 34 wrote a new candidate before checking
whether a shipped line already reached the failure, and its own hypothesis then said neither
fixture instantiates the case the wording is for. Four runs to reach an outcome the design
could not avoid. Its handoff says as much — instruction 3 to this round was *do the shipped
line first*. Folded into the candidate clause rather than added as a new one.

**C4 (workflow, measured).** The `(contract)` block has gone 0 → 125 → 181 → 248 → 334 → 435
→ … → 800 words over 34 rounds, and has only ever shrunk when the user's token ceiling forced
it (`800 → 793` at 33, `790 → 675` at 34). The loop's own governance is the ratchet the
objective is against, and the only thing that has removed text from it is a human-set size
limit — the mechanism the objective explicitly wants to do without. This round cut it to ten
clauses by deleting two that restate files which govern (`## Required notes`'s intent, now in
`sys_prompt/CLAUDE.md`; case-ownership conditions, now in `.claude/skills/prompt-tests/SKILL.md`)
and merging two pairs. **Deleting a clause because the file it restates governs is the only
compression here that is not the ceiling talking.**

### Result — the research candidate is decided and not written

`amber-thicket` (deleted; `git checkout 96ffd5b7 -- prompt-tests/runs/amber-thicket`), three
legs on one fixture, pre-registered at `96ffd5b7`, result at `4291d5b4`. Full account in
`sys_prompt/CLAUDE.md`. In short: both branch legs ran the check unprompted and wrote no rule,
so *Finding out costs less than the rule you would write instead* has no benefit left to buy
and is not written. `Say what ends it` was not separated either — no leg wrote a note about
the exposure. The fork the specimen ran was the only leg to amend a nested `CLAUDE.md` and the
only one never to check; the blind reader calls that noise at one run per leg and this round
takes its word. What all three did was turn one instance into a project-wide rule in the
document the task named, and two of three generalisations are false in their added scope.

### `(instruction)` for iteration 36

1. **One candidate, already provenanced and already checked against the shipped lines**, in
   the words to run, as a bullet in `# Writing for other agents`:
   `- An instruction's scope is a claim. One instance does not support a project-wide rule.`
   Its occurrence outside `sys_prompt/` is the owner's specimen and 35's three legs. No
   shipped line reaches it: the paragraph that says it, **Force** in `sys_prompt/CLAUDE.md`,
   has only ever addressed whoever edits the prompt. Pre-register the kill as an agent that
   writes the instance and drops something true with the scope — 33 measured exactly that
   failure for a compression wording.
2. **The decisive reading is whether the added sentences are true against the delivered
   tree**, not how many there are. Volume has now failed as a metric in four rounds.
3. 36 is not a cleanup round; 40 is.

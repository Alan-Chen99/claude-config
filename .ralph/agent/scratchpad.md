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

**A saturation reading taken on fixtures does not transfer to this repository's own
documents.** 37 found a falsified claim standing in the public `README.md` through four
rounds that were measuring the same failure in fixtures.

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
> under `run_in_background: true`, **keyed to activity in the topic and not to a reply id**,
> and **the round re-reads the channel log after its own last send**. Their answer has
> changed the round's conclusion four times, and 36 closed 33 seconds after an instruction it
> never read. The cost of waiting is not the loop's limiting factor and the user has said so.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–36

**1–32, `9f6c03a0` → `1497221c`.** Anything justifying a prompt line lives in
`sys_prompt/CLAUDE.md`, which names every line these rounds shipped or deleted; everything
else is in the commit messages. Every say-less wording failed; 29 kept the whole block,
refuting its own hypothesis; 30 and 31 both spent a round on `## Required notes` and
shipped nothing, and the owner settled it at 32 — the block is best-effort surfacing. 32
built the hidden-docs tree and found the docs order's repair half saturated there too.
`scripts/check-prompt-upstream.py` cannot run here — `/repos/claude-code-decompiled` is
absent. DEC-036, DEC-037.

**33–36, `1497221c` → `687838c3`.** Four candidates decided, none shipped, all four written
and judged by the round that ran them. 33: the exclusion clause cuts unfalsified prose four-
and sevenfold and in both probes shipped one sentence false against its own code. 34: *a note
telling the next reader to avoid something is a fix you did not make*, saturated in two
genres; its larger finding is DEC-045, that `scripts/claude.sh` loads `/repos/claude-config`
and nothing this loop measures is live. 35: *finding out costs less than the rule you would
write instead* was never written, both legs doing it unprompted; what all three legs did do
was turn one instance into a project-wide rule, two of three false in the added scope. 36:
*a rule's scope is a claim …* — the arm carrying it asserted the entailment one render
refutes where the bare arm got it right, so the line naming the failure did not prevent it.
36's unpre-registered finding is the live candidate: the change falsified
`templates/CLAUDE.md`'s opening rule, the treated arm rewrote the sentence, and the bare arm
saw the contradiction and *added a minimal amendment documenting this exception* beneath it,
leaving a file asserting and denying one rule. A stale **rule** is not a stale statement: the
agent reads it as someone else's standing convention and annotates around it. The owner also
settled that the loop must not merge this branch, and named the growth driver — every
addition locally justified by a small saving, nothing pricing the sum. DEC-043 to DEC-047.

## Iteration 37 — `687838c3` → (this round)

### Critique of 36

**C1 (workflow, verified from the channel; it is this round's whole milestone).** 36 never
read inbound #93 — *"have next round merge branch staging into your branch. that round
should be doing only that"* — which arrived 33 seconds before 36's own closing message #94.
#94 answers #91 and #92, says "Got both", and assigns 37 the repair candidate instead. Its
waiter was keyed to a reply id while #93 replies to the topic root, so nothing woke it and it
did not re-read the log before closing; its record of "The owner's answers, 2026-09-25"
states two answers where there were three. The telegram clause is now a mechanism for that
failure, not an intention: topic-keyed waiter, re-read after the last send. This round's
waiter caught #96 in under a second.

**C2 (workflow).** 36 handed the repair candidate forward without the exact words the
contract requires, leaving 37 to write the wording it would then judge. That is four rounds
running in which the author of a sentence measured it — DEC-047's own framing bias — and all
four killed it. Either that clause binds or it goes; 38 decides, and no wording is measured
this round because the owner's instruction says merge only.

**C3 (fact, from outside any fixture).** The loop has been measuring repair-versus-annotate
on fixtures while carrying the same defect unrepaired in the repository's public entry point:
`README.md` asserted a run's evidence artifact lives under `prompt-tests/runs/` and mapped
that directory as holding "recorded runs", which this branch's own `runs/README.md` denies —
nothing durable lives there and the round that wrote a probe deletes it. Four rounds touched
that area; the merge is what put the two documents in one tree. Neither branch did anything
wrong: `staging` described the tree it had. That is the situation the candidate is about,
occurring outside every fixture, and it is why 32's saturation reading does not transfer.

### What this round did, and what it did not

Merged `staging` (16 commits, no conflicts, four auto-merged files read hunk by hunk), then
ran the public-ready pass on this branch's parts, which is what the owner's #96 asked for:
`staging` *was* that cleanup. One repair, by editing the sentence: the two false `README.md`
claims in C3. The round also added rows indexing `PROMPT.md` and `.ralph/` to the root
`CLAUDE.md` and then took them out again on the owner's #98 — the loop's files are removed
from the tree before any merge, so an index row for them is two lines that same commit must
remove, and nothing reads them. DEC-048. Swept and found
clean, so nothing else was touched; the sweeps and their sizes are in `e8589613`. No prompt
test ran and `sys_prompt/` is untouched, so no `(contract)` clause about prompt edits applies
to this round. Green: `uv run pytest tests/ -q` 544, `cargo test --release` 15 binaries,
`check-prompt-coupling.sh` OK.

### `(instruction)` for iteration 38

1. **The strict occurrence is still unmet.** 37 found the *situation* outside fixtures
   (C3) but no agent *annotating* instead of repairing outside `sys_prompt/` and outside a
   fixture. Find that instance — a session log on this machine, a commit in this tree — or
   the candidate dies there, per 36's own clause.
2. Only then a wording, naming the act: editing the sentence. Commit it before launching any
   arm. Kill arm: it overwrites a rule its change did *not* falsify.
3. Decide C2: a round that hands a line forward writes the words, or that clause goes.
4. The owner's aggregate-pricing diagnosis is the candidate after this one, and whoever takes
   it checks `Say what ends it` against it first.
5. 40 is the cleanup round.

Iteration 37: `687838c3` → the commit that carries this line. Ceiling at close is in that
commit's message.

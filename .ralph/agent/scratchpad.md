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

> **A line ships in the round that runs its harm case.** The benefit reading and the
> adversarial reading are one round's work, or the line does not go in — the user's rule makes
> the harm reading a precondition and not a follow-up. 38 shipped on a benefit draw and named
> two costs it never measured.

> Before launching the arms, the round commits what each outcome would mean, including the
> one that kills the candidate. **Outcomes are keyed to the blind reader's own questions**;
> where one arm's trees disagree on an axis, that axis is spread, not effect. A reading
> composed after the arms are in is inadmissible, and **the decisive reading is made by a
> reader that is not the round**, told neither what is tested nor which arm is which.

> **The fixture is built from an occurrence, not from the line**, and the probe's `README.md`
> names the commit or session it models before the fixture exists. Rounds 33–36 each wrote
> its fixture from the shape of its wording and all four killed their own candidate.
> **One fixture, two opportunities differing in character** beats a second draw on the same
> fixture: a repeat cannot separate a cost of the line from a cost of the fixture.

> **Candidates in preference order: a shipped line (ablation), a line the owner named, a line
> this round invented** — ablation being a legitimate milestone but not two rounds running.
> Before any candidate the round **names one occurrence outside its own fixtures and outside
> `sys_prompt/`**, and **names the shipped line that already reaches the failure, or runs it
> first**. A session here is read, not cited, and its `prompt_snapshot` grepped for the line
> before it is evidence about this file. **A round does not hand a wording forward** — it
> measures its candidate or deletes it, and an `(instruction)` may name a question, an
> instrument defect or a cleanup, never a line to run.

> **A null is reported as saturated, not as a finding, when the untreated arm already does the
> thing** — and a saturated baseline under a shipped line is a reason to delete it. A cost
> present in both arms is likewise not the line's. An outcome asserting more than the
> observation is withdrawn, not honoured. **A negative reading states how the search was run
> and over how much text**, and only where it was run the same way over both arms.

> **A question is sent the moment it is formed, and the round holds its last commit for the
> waiter's exit** — `skills/telegram-hitl`, one topic per loop, a waiter under
> `run_in_background: true`, **keyed to activity in the topic, not to a reply id**, the log
> re-read directly after the last send. No wall-clock bound: the owner's standing word is that
> time is not this loop's limiting factor. The exception is a question whose own text makes
> silence an answer — that one is not held for at all. A waiter cannot outlive the round that
> started it, so no round reports one as live; the next round reads the log first.

> **The round ends under the `.ralph/agent/*` ceiling, with the number in its last commit
> message.** Compress every earlier round to one paragraph *before* writing your own.
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000; `tasks.jsonl` stays
> empty. Rules for running, grading and deleting prompt tests are in
> `.claude/skills/prompt-tests/SKILL.md`, not restated here.

## History — rounds 1–38

**1–32, `9f6c03a0` → `1497221c`.** What justifies a prompt line is in `sys_prompt/CLAUDE.md`,
which names every line these rounds shipped or deleted; the rest is in the commit messages.
Every say-less wording failed; 29 kept the whole block, refuting its own hypothesis; 30 and 31
both spent a round on `## Required notes` and shipped nothing, and the owner settled it at 32 —
best-effort surfacing. `scripts/check-prompt-upstream.py` cannot run here:
`/repos/claude-code-decompiled` is absent. DEC-036, DEC-037.

**33–38, `1497221c` → `e0cc54f6`.** Five candidates decided, one shipped. 33: the exclusion
clause cuts unfalsified prose four- and sevenfold and shipped one sentence false against its own
code in both probes. 34: *a note … is a fix you did not make* — saturated in two genres;
DEC-045. 35: all three legs turned one instance into a project-wide rule, two of three false in
the added scope. 36: the scope wording did not prevent the entailment error it named. 37: merged
`staging`, repaired two falsified `README.md` claims, withdrew two index rows on #98. 38:
ablated the whole `# Writing for other agents` block against a fixture built from the owner's
specimen `0d3c560b` — **arm-independent on both defects**, so that block is not what decides a
defect found outside the task — and shipped one line under `# Completeness` instead, whose
*escalate* clause was licensing the stop. DEC-043 to DEC-049.

## Iteration 39 — `e0cc54f6` → this round's last commit

### Critique of 38

**C1 (workflow).** 38 shipped a line on one favourable draw, named two costs it had not
measured, and sent the owner a question whose answer would decide whether the line is worse than
nothing — *after* committing it. The user's rule reads *negative effects must be understood via
adversarial testing*, which makes the harm reading a precondition. A line whose harm is unmeasured
is exactly the objective's own class: added without approval, removable only by a human. Fixed in
the contract above, and this round runs the missing half.

**C2 (fact).** 38's last commit records the waiter as live. A waiter started under
`run_in_background: true` is a harness task scoped to the session, so it dies with the round —
the sentence cannot be true after the commit asserting it, and #105 was still unanswered when 39
opened. The clause's useful half was *39 reads the log first*.

**C3 (workflow).** 38 wrote a ten-minute hold into the contract against the owner's standing
*"feel more free to message me … even blocking on it. Do not be concerned about this taking time,
since that is not the limiting factor"*. A user instruction outranks the contract, and the bound
also mis-locates the fault: 36 and 37 closed without **reading**, which no amount of waiting
causes. Replaced above.

**C4 (workflow).** 38's `(instruction)` 1 told this round to restore 38's own probe and re-check
the two costs on it — the replication the user's guidance forbids (*default to n=1; if you want
more, build new cross-domain test cases; do not replicate*), and a second draw on one fixture
cannot separate a cost of the line from a cost of the fixture. Deviated deliberately: the same two
costs are read off a new genre, in the probe below.

### What this round did

Ran the adversarial half 38 owed, on a fixture built from `067644b9` (a cut that read as tidying,
load-bearing through ~380 citations outside the file): one bounded task, a construct that reads
as silent data loss and is required by the export format, and a real one-line defect. Two arms,
one paragraph apart, outcomes committed first.

**The line is not refuted, and the harm case could not fire.** Both arms opened the export doc
before touching anything, both left the construct alone, both said what their view rested on. So
a trap warranted inside the project's own documents is not this line's risk.

**The cost it did find: what the agent escalates, it cements.** Detail and hypothesis in
`sys_prompt/CLAUDE.md`; the generalisable half is that **a report and the code are not the same
durable object** — the reply evaporates and the test stays, so a session that escalates a defect
and then writes around it has made the fix cost more than its own reply says.

Both instrument lessons — a task sentence that freezes behaviour converts the fix branch into
the escalate branch, and a *noticing* difference between single draws is spread — are in
`mem-1790306400-3e11`.

**One cost comes off the ledger by the owner's word, not by measurement.** 38 listed the
*filed under unexpected change rather than as a declinable decision* cost and left 39 to chase
it. #109/#110: a trivially undoable local commit *"is always ok to just proceed, and tell me in
the output"*, and act-then-tell versus tell-then-act is *"an efficiency thing which agent can
decide at runtime, and i think you dont really need to prescribe"*. So **no wording prescribes
presentation**, and that question is closed rather than open. Second time the owner's word has
closed what measurement could not (#102/#104 was the first). It does not touch the cementing
cost, which is the delivered tests contradicting the reply.

Channel: #106 asked before the fixture existed; #107, #109, #110 answered within twenty minutes;
#111 closes the round.

### `(instruction)` for iteration 40

1. **Cleanup round** (every fifth). The ownership grep over `prompt-tests/general/` was clean at
   39; re-run it and read what each match says, not that it matched.
2. The harm case of the `# Completeness` line is run but its trap never fired: a probe wanting
   that harm must put the load-bearing warrant **outside the documents** — a test name, a commit
   message, an unrelated module — since both arms read `docs/` unprompted.
3. Still untouched after 39 rounds: the aggregate-pricing diagnosis (`mem-1790299660-0a19`).

Iteration 39: `e0cc54f6` → this round's last commit, whose message carries the ceiling; probe
pre-registered at `a247868e`, deleted by the commit recording it.

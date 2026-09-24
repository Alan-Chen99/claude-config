# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human
approval to add, but require human intervention to remove*; the rest follows from
that ratchet. The user's 2026-09-24 followup makes *less documentation gets
written* the top priority. Carry **what retires this line** into every decision.

## Durable method, reusable across rounds

**The compression rule.** Cut in this order, stopping at the first class that is
load-bearing: a **claim** (only claims can be wrong), a **restatement** (two
wordings, nothing saying which governs), a **duplicate of executable code**
(replace with its name), a **trap** (what the reader gets wrong silently; keep).
Deletion is the default; each *keep* needs the argument.

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent argues it in whichever
direction the task favours.

**Categorical or it is not evidence, per reading rather than per table.** *Stated
bare or sourced* is readable at n=1; a count is a sample of an unmeasured spread.

**Test the lines already shipped.** A shipped line with a named, unmeasured harm
outranks any new candidate — inside the objective's scope only.

**When an instruction exists to compensate for a harness, fix the harness.**

**The prompt is the whole stack, not one file.** `sys_prompt/alan-default-next.md`,
`output-styles/`, `conventions/documentation.md` (reached only via `doc-sync`,
`technical-writer`, `quality-reviewer`, `planner`) and
`src/claude_config/pre_output/record.py`, whose RULES string arrives in a tool
result before every response, all reach the session.

**Before writing a clause for a failure, re-run the failure in a second genre.**
If it disappears there, the target is the genre and not the wording.

**Real session logs under `~/.claude/projects/` carry the base rate a fixture
cannot.**

## Standing `(contract)`

> An iteration may spend its milestone on any file in the stack, and may not spend
> a whole milestone on the prompt-test *instrument* unless it also runs at least
> one arm against `sys_prompt/alan-default-next.md`.

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit. Counts, arm labels, byte
> deltas, dates and fixture descriptions belong to git, not to that file.

> An edit that deletes or renames anything a document can point at, or withdraws a
> claim, sweeps the tree for citers in the same commit — `grep -rn --include='*.md'
> <name> .`, `.ralph/agent/` included — and the commit says which were left on
> purpose.

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call. A round that ships no prompt edit may add a paragraph there only as
> the first justification of a line that had none, naming the instrument defect a
> later round must fix; otherwise it may only replace a paragraph, shorter.

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

> **A condition in `sys_prompt/CLAUDE.md` names, in its own sentence, a case that
> exists and a comparison a later round could run.** *Retire this when an arm
> carrying the line does no better than one without* is the only actionable form.

> **Before a candidate wording is written, the round names one occurrence of the
> behaviour outside its own fixtures** — a real session log, a commit in this
> repo — or records that it looked and found none.

> **A claim that the round's fixtures differ in some property is quoted from each
> fixture it compares** — the whole comparison, deleted ones included.

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in
> its last commit message.** A round's own narrative is not what it spends the
> ceiling on: compress every earlier round's section to one paragraph first.
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000.
> `tasks.jsonl` counts toward it: a task points here, never copies.

> **A claim about what an earlier round did or observed is checked against git
> before it is written** — `git log --all -S'<line>'` for a prompt line, the
> result commit's own message for a result — and names the commit it checked.

> **A round opens no task row.** `tasks.jsonl` stays empty; the round's state is this
> file, `decisions.md` and the commit messages, which the ceiling already counts.
> DEC-039.

> **`decisions.md` carries only the half `sys_prompt/CLAUDE.md` does not** — what else
> was on the table, the framing bias, whether anyone independent looked, the revert
> sha. Claim, hypothesis and retirement condition are stated once, there.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–29, `9f6c03a0` → `98b3f320`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — read it before
touching the block. Everything else is in the commit messages. Shipped: `Say what
ends it` (11, upheld at 19), the self-consequence bullet (23), one duplicated
rationale cut out of it (25), the deletion of `pre_output.record`'s `NEVER reply to
user if uncertainties remain` (26, DEC-034), the deletion of the whole docs order at
`alan-default-next.md:15` (28, DEC-036). Deleted also: `Omit by default`, `Claim
less`, the help-surface cost paragraph. Eight candidate wordings failed, the last
four all claim-handling. Every sentence still in the block has been measured alone.
29 put the whole `# Writing for other agents` block on trial and kept it, refuting
its own hypothesis that bullet 2 redirects growth into prose: the treated arm wrote
7 unfalsified sentences to the untreated arm's 16, and neither arm's reasoning
declines an addition. Volume there was confounded with depth — the arm writing more
ran half again the tool calls and wrote the only true new claim. Unfalsified prose:
11 of 11 trees over three rounds. DEC-037, DEC-038.

## Iteration 30 — `98b3f320` → (this round)

### Critique of 29

**C1 (workflow — the specimen was read as a diff, never as a session).** The user's
followup hands the loop a live instance: session `e828eab7`, commits `0d3c560b` and
`b394ebbf`. 26 read it by tool-call index; 29 did not open it. The log settles two
things no fixture round could. Its `prompt_snapshot` carries `# Writing for other
agents`, so the shipped block was in force while the failure happened — the loop's
one real-world n=1 against it. And the agent **states the fix-the-hazard alternative
and declines it on a contextual ground** (the file was under the user's own edit).
A ninth candidate telling an agent to remove a hazard rather than write a rule about
it is therefore saturated on the one occurrence anyone has. Candidate killed for the
price of a read, which is what the name-an-occurrence clause is for. Quotes and refs:
the pre-registration commit.

**C2 (fact — 29 recorded a contradiction that is not one).** Its commit says
`# Error Propagation`'s fallback rows pull against `# Coding`'s *don't add error
handling, fallbacks, or validation for scenarios that can't happen*. They agree: a
scenario that cannot happen has no real data demonstrating it. 29 handed this reading
to this round to act on, so a misidentified pair would have aimed the next edit wrong.
The pull that does exist is named in the instruction list below.

**C3 (workflow — the half of the ratchet no round has aimed at).** That same agent put
its one git-reversible decision to the user through `AskUserQuestion` and surfaced none
of its three documentation additions, two of them standing rules only a human removes.
Adding a rule is not felt as a decision; committing a file is. Twenty-nine rounds have
varied wordings asking the agent to write less. None has asked it to say what standing
rule it just added.

### Milestone — the reporting surface, not another say-less wording

On trial: one `## Required notes` bullet naming a standing rule the session wrote
into a file others read. It is a report, not a gate: it cannot refuse an addition,
it makes one visible in the turn where it happened, and visibility is the half of
the objective's ratchet that nothing in the stack currently serves. Chosen over a
ninth say-less wording because eight have failed and because C1 shows the
act-shaped alternative is already reached unaided.

Depth is held fixed by construction, which iteration 29's instruction 3 requires:
the probe fixture states the established fact in a file the task must touch, so
neither arm has anything to investigate and volume cannot ride on tool-call count.

Pre-registration and outcomes: this commit.

### Result — no prompt edit; the baseline already reports the rule

**The fixture design answered 29's instrument question.** Stating the load-bearing
fact in the fixture, as verified, in the file the task sends the agent to — and making
the natural implementation the one that trips over it — held depth fixed: thirteen
tool calls an arm, both arms met the trap. Volume is separable from checking now, and
the recipe transfers.

O3 fires. Both arms extended the soliciting `## Agent Policy` and both named what they
had added, under `## Required notes` — the untreated arm under `unexpected change:`,
quoting its own additions. The candidate named the same act in other words, which is
step 2's duplication. **Not shipped.** Justification and retirement condition:
`sys_prompt/CLAUDE.md`, the first entry that line has ever had.

The saturation is not total and the pre-registration left no room for that: O1 and O3
were all-or-nothing, and the untreated arm reported one obligation as a past act where
its page now instructs a later reader. Read as saturated, per the rule that an outcome
asserting more than the observation is withdrawn. A cost a report has and a page does
not, on the treated arm: its bullet said *must* for a page stating a consequence.

**Arm-independent and new: both arms declined a destination out loud**, each weighing a
second document and saying in the reply why the fact went elsewhere. 29 looked for
declining, found none, and withdrew DEC-037's mechanism conjunct on that. It is
genre-bound — it shows where two documents compete for one fact — not absent.

Volume under fixed depth: 14 lines of durable prose to 6, untreated to treated. One
draw an arm; the direction is a sample. DEC-040.

### `(instruction)` for iteration 31

1. **Run the arm this round could not.** No arm ran *without* `unexpected change:`,
   so its own necessity is untested; the entry justifies the absence of a second
   bullet. Condition and case are in `sys_prompt/CLAUDE.md`.
2. Instruction 2 of 26/29 is closed, and 29's reading of it was wrong: `# Error
   Propagation`'s fallback rows and `# Coding` agree — a scenario that cannot happen
   has no real data demonstrating it. The pull that does exist is `Silent retry` and
   `Partial success`, which require counters and partial-failure lists, against
   `# Coding`'s minimum-complexity rule and its ban on helpers for one-time
   operations. Both blockquote-plus-table duplications stand unmeasured.
3. `scripts/check-prompt-upstream.py` cannot run on this machine:
   `/repos/claude-code-decompiled` does not exist. It is not a check a round can
   green, and an upstream rebase cannot be done from here.

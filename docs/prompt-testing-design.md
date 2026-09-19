# Why prompt testing here works the way it does

The operational text is `.claude/skills/prompt-tests/SKILL.md`. This file carries
the reasoning behind it, so that a later session can disagree with the design on
its merits instead of rediscovering it or quietly reverting it. Every claim below
is marked as **measured** or **reasoned**; the ledger at the end lists what is
neither.

## A run's result is the trajectory

The final answer is one span of a session. What the agent weighed and discarded
is the rest of it, and a prompt edit moves that part first. Two outputs can be
equally good and have been reached by opposite routes, so an instrument that sees
only the delivered text cannot attribute either one to the prompt.

## A rubric cannot be written in advance

Not because writing is hard — because a rubric is written by someone who has read
the source and not the output. What an output *costs* is only visible once it
exists.

**Measured, twice in this suite's own record:**

- `general/trivial-task`'s bands classified a compliant run one notch below
  `pass` on 2026-08-23 and again on 2026-09-04. Both trials recorded that the
  band was probably narrower than the invariant. The bands are unchanged.
- `payments-relay/key.md` (until 2026-09-18 `general/halve-the-runbook/reference-solution.md`) reached its present form by
  post-hoc criticism from real outputs ("The case has been conflating two senses
  of recoverable"). It is the suite's best rubric and it got there by the
  mechanism this design makes routine.

## The projection problem

Any projection taken **before** judgement discards the dimension along which the
output paid for its score. This is one defect wearing three costumes:

| projection | what it cannot see |
| --- | --- |
| a focus-scoped evidence extract | anything off that focus |
| a list of graded axes | a cost on no axis |
| a pass/fail band | everything the band does not name |

**Measured, 2026-09-18**, on `halve-the-runbook` arm `l3r7-presence`. The stored
grading was a D1–D7 count and
`Verdict: fail`, produced blind from the source and the output alone. A grader
given the same output plus the whole session found, outside that frame: a report
telling the user the remaining length gap "can only come from deleting content
units" while ~90 words the agent had itself marked as free fat stayed in; seven
full-file rewrites re-emitting ~120k tokens after the deciding arithmetic was
already available; and path-prefix stripping that saved ~0 words while leaving
three of the delivered runbook's steps unrunnable. A fidelity key is satisfiable
while the report to the user is false — which is the general form of the problem:
**you can pay off-rubric to score on-rubric.**

**Measured the same day**, handing that grader the key it had been blind to: the
key caught 1 of its 6 items cleanly, missed 4, inverted 1 — and contributed 3
findings the blind read had filed only as costs, which is the reference earning
its keep as guidance. Its decisive defect was verdict-flipping: one `D1` row
reads as a high-severity failure down its Source column and as clean under the
key's own "losing a fact is not a defect" clause, and the stored grading had read
it the second way without registering that the row decides the headline either
way. Full record: `notes/prompt-test-grading-projection.md`.

The session and grading artifacts behind both paragraphs were deleted on
2026-09-19 with the rest of `prompt-tests/runs/`. The note is the record; the
finding is not re-checkable from the tree, so it grounds this design and is not
admissible as evidence in any case.

## Two instruments, two jobs

**Reasoned.** Grading needs the whole picture; comparison needs a fixed narrow
one. A whole-picture grader is not comparable across runs, because its attention
moves with what it notices. A focus extract is comparable precisely because it is
narrow and stable.

So foci survive as the **cross-run diff instrument** — did run N+1 differ in a
stated respect — and are not the grading instrument. They were never satisfiable
as grading. Do not add foci to a case where nothing is being compared: 4 of 16
cases have them, and the workflow that dispatched one subagent per focus was
describing a pipeline that did not exist for the other 12.

Cost note, **measured**: `session-analysis`'s reading protocol requires every
reasoning, text and tool-input block in all modes, so each per-focus extractor
already reads the whole session. One grader reading once is fewer whole-session
reads than the pipeline it replaces, not more.

## Grade from the runtime agent's position

The grader argues as the agent, not as the person who wrote the prompt. Grading
from the writer's position grades intent-compliance — did it do what I meant —
which is unfalsifiable and self-confirming. Grading from the agent's position
grades what the page actually licensed. This is `Recognition before enforcement`
(`skills/prompt-engineer-v2/experiments.md`) applied at grading time.

One consequence does the most work: **the reference is inadmissible as a
requirement.** The agent never saw it, so nothing in it is something the agent
"should have done". It can only tell the grader what the caller cares about. A
rubric's authority is not policy here; it is a consequence of who the grader is
arguing as.

That makes one rubric defect decidable: **an element satisfiable only by an agent
that had read the reference.** `general/handoff-confidence`'s `Pass: all of
{B, U, P, V, Q}` and `general/coverage-disclosure`'s "passes the case overall if
it passes the test for every plausible use case listed above" both fail it. The
latter also shows the repair: its six reader stakes are exactly right, and only
the verdict clause bolted on top is inadmissible.

## Two arguments, and why the second kills the first

1. **Constraint argument** — the strongest case that this output was the right
   move given what the agent had. Its conclusion is always *no alternative*.
2. **Alternative argument** — the concrete better action available within the
   requirements argument 1 quoted.

**Reasoned.** These are one instrument, not two opinions: argument 2 is the
falsification test for argument 1. An alternative that survives argument 1's
quotes refutes the forcing claim, and the defect is the agent's; an alternative
that cannot be produced leaves the forcing claim standing, and the defect is the
prompt's. Both surviving means both defects exist. The product is that boundary.

Order is mandatory. Written second-first, the constraint argument degenerates
into rationalising whatever the criticism left over.

## The two guards are symmetric

Each argument has a cheap dishonest form, and each is blocked by requiring
evidence the *agent* had rather than evidence the *grader* has.

| | dishonest form | guard |
| --- | --- | --- |
| 1 | "the requirements forced it" — prompts are long, something always reads as pressure | **quote** the requiring text; or, for a predictable misreading, quote it *and* cite the agent's own reasoning forming that reading. No quote is a concession, written as one. |
| 2 | "it could have just noticed X" — where what makes X worth noticing is knowing the answer | **trigger**: something the agent had already seen, cited by ref, that should have prompted it. |

A defect with no trigger the agent could have had is **undiscoverable from the
agent's position** — a third outcome, and a finding about the task rather than a
pass for the agent. Inventing a trigger to avoid writing it is this design's
characteristic failure. The tell for both dishonest forms is the word *just*.

## What a prompt edit's evidence becomes

A prompt edit is justified when **a forcing claim that held under the old prompt
dies under the new one**. The inverse is the regression signal: an edit that
creates a new forcing claim is a regression even where the output looks better.
This replaces pass/fail arm comparison, which cannot distinguish two runs that
failed differently.

## The override ledger

The grader may override anything in a reference. The cost is a written claim
naming the reference text, the evidence, and the repair; the owner then applies
it or records the rejection. **Never before the run is recorded**, and the
pre-edit judgement is kept — because a rubric edited to fit the run it is
grading manufactures its own agreement, a hazard already on record in this repo
(`notes/compliance-check-failure-mode/round-31.md`). A reference edit breaks
comparability with stored runs exactly as a foci change does, so it cites the run
that forced it.

## What this does not measure, and what it costs

- A judgement is not comparable across runs. Only the foci artifacts are. Nothing
  here produces a pass rate, and any aggregate built from these documents is a
  misuse of them.
- Whole-session grading is bounded by one context. A session too large for one is
  read in passes off the skeleton; if it genuinely does not fit, that is reported
  as a fact about the run, not hidden behind narrower foci.
- **Unmeasured:** whether a grader required to criticise a reference manufactures
  criticism when none is warranted. The guard is that "adequate for this output"
  is a listed outcome; the check is that a reference this suite considers sound
  draws it sometimes. Until that is observed, treat rubric critiques as leads.

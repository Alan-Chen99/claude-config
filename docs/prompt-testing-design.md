# Why prompt testing here works the way it does

The operational text is `.claude/skills/prompt-tests/SKILL.md`: the runners, the
grader dispatch, what a run's record is. This file carries only the reasoning
behind it, so that a later session can disagree with the design on its merits
instead of rediscovering it or quietly reverting it. Nothing here restates an
instruction from there — where both would apply, the skill governs.

Measured results are not kept here. Prompt-test evidence does not survive the run
that produced it: a reference edit, a foci change or a prompt edit each make an
old run a different measurement, and none of them announces itself in a document
that quotes the old numbers. What survives a round is a semantic claim with its
reasoning attached, which is what each section below is.

## A run's result is the trajectory

The final answer is one span of a session. What the agent weighed and discarded
is the rest of it, and a prompt edit moves that part first. Two outputs can be
equally good and have been reached by opposite routes, so an instrument that sees
only the delivered text cannot attribute either one to the prompt.

## A rubric cannot be written in advance

Not because writing is hard — because a rubric is written by someone who has read
the source and not the output. What an output *costs* is only visible once it
exists. The corollary is a working method rather than a prohibition: criticise
the reference from the run, after the run is recorded, and keep the pre-edit
judgement.

A criterion written from the shape of an anticipated failure has a second defect:
it cannot score a good outcome, only the absence of that failure. Write what the
good artifact looks like before writing what the bad one is missing.

## The projection problem

Any projection taken **before** judgement discards the dimension along which the
output paid for its score. This is one defect wearing three costumes:

| projection | what it cannot see |
| --- | --- |
| a focus-scoped evidence extract | anything off that focus |
| a list of graded axes | a cost on no axis |
| a pass/fail band | everything the band does not name |

The general form: **you can pay off-rubric to score on-rubric** — a fidelity key
is satisfiable while the report to the user is false. The worked instance, with
the session it came from, is `notes/prompt-test-grading-projection.md`; its
artifacts have been deleted, so it grounds this design and is not admissible as
evidence in any case.

## Two instruments, two jobs

Grading needs the whole picture; comparison needs a fixed narrow one. A
whole-picture grader is not comparable across runs, because its attention moves
with what it notices. A focus extract is comparable precisely because it is
narrow and stable.

So foci are the **cross-run diff instrument** — did run N+1 differ in a stated
respect — and are not the grading instrument. They were never satisfiable as
grading, and most cases compare nothing and want none.

This costs less than it looks: `session-analysis`'s reading protocol requires
every reasoning, text and tool-input block in all modes, so each per-focus
extractor already reads the whole session. One grader reading once is fewer
whole-session reads than a per-focus pipeline, not more.

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
arguing as — which also makes one rubric defect decidable, an element satisfiable
only by an agent that had read the reference.

## Why the second argument kills the first

The constraint and alternative arguments are one instrument, not two opinions:
argument 2 is the falsification test for argument 1. An alternative that survives
argument 1's quotes refutes the forcing claim, and the defect is the agent's; an
alternative that cannot be produced leaves the forcing claim standing, and the
defect is the prompt's. Both surviving means both defects exist. The product is
that boundary, which is why forcing a winner destroys the result.

Order is mandatory. Written second-first, the constraint argument degenerates
into rationalising whatever the criticism left over.

Each argument has a cheap dishonest form, and the guards are symmetric: each
demands evidence the *agent* had rather than evidence the *grader* has. The tell
for both is the word *just*. A defect with no trigger the agent could have had is
**undiscoverable from the agent's position** — a third outcome, and a finding
about the task rather than a pass for the agent. Inventing a trigger to avoid
writing it is this design's characteristic failure.

## Reading one run rather than counting many

A single opportunity for the behaviour under test is a coin flip whatever the
prompt says, and two runs of one unedited prompt can differ on it as widely as a
treated arm differs from either. The cheap resolution is inside the run, not
across runs: build the fixture so one session offers **several opportunities
differing in character**, and read the line the agent drew between them. That is
a policy rather than a rate, and a policy is legible at n=1.

The same asymmetry applies to a null. A single question's silence is not
evidence, because the question pre-selects what it can find; a null needs a
second phrasing before it means anything.

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

# runs

The recorded output of prompt-test runs. Nothing taken before 2026-09-22 remains:
the runner wrote a file naming the harness into the tested agent's working
directory, so no arm stored before that is comparable to one run after it.

## What goes here

A **graded** run, per the skill's "Grader dispatch":

- `judgement-<arm>.md` — the grader's judgement, one per arm, per the skill's
  "Grader dispatch". This is a run's primary record.
- `sa-<arm>-<focus>.md` — a `session-analysis` evidence artifact, only where the
  case already carries foci. Foci are the cross-run **diff** instrument, not the
  grading one; do not add them to a case that has none.
- `artifact-<arm>.md` — what the tested agent wrote, where the case's reference
  makes claims about the delivered text.

A **probe** — defined in the skill's "Probes", and the default — records the
delivered artifacts and one `README.md` saying what the arms were, what
differed, and what the comparison does not establish. Dispatch graders instead
when the question turns on how the agent got there rather than on what it
delivered. A probe that moves a prompt still gets the blind comparison the skill
requires of a prompt edit, and the README reports it.

Arm names match the baseline headings in the case's `reference-solution.md`,
where it has them.

**The JSONL paths cited inside these artifacts do not survive.** Transcripts
live under `.claude/worktree-config/projects/`, which is gitignored and lost
when the container is rebuilt. The artifact is the record; its `@L` references
are provenance for whoever wrote it, not a pointer a later reader can follow.

A judgement is not comparable across runs and never aggregates into a pass rate.
Delete a case's stored runs when its **instrument** changes — fixture, task text,
or foci — rather than keeping artifacts that measure something the case no longer
is. A reference edit is not that: it invalidates the judgements taken under it and
leaves the artifacts standing, which is what keeps the record that the case was
re-run from being destroyed by the round that improved its wording.

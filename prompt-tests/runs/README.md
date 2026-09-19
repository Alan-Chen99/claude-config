# runs

The recorded output of prompt-test runs. Empty as of 2026-09-19: every stored
run was deleted when the grading design changed to the whole-session,
two-argument dispatch in `.claude/skills/prompt-tests/SKILL.md`. Runs taken
under the old rubric-first practice are not comparable to anything produced
under the new one, and nothing in the tree cites them any more.

## What goes here

- `judgement-<arm>.md` — the grader's judgement, one per arm, per the skill's
  "Grader dispatch". This is a run's primary record.
- `sa-<arm>-<focus>.md` — a `session-analysis` evidence artifact, only where the
  case already carries foci. Foci are the cross-run **diff** instrument, not the
  grading one; do not add them to a case that has none.
- `artifact-<arm>.md` — what the tested agent wrote, where the case's reference
  makes claims about the delivered text.

Arm names match the baseline headings in the case's `reference-solution.md`.

**The JSONL paths cited inside these artifacts do not survive.** Transcripts
live under `.claude/worktree-config/projects/`, which is gitignored and lost
when the container is rebuilt. The artifact is the record; its `@L` references
are provenance for whoever wrote it, not a pointer a later reader can follow.

A judgement is not comparable across runs and never aggregates into a pass rate.
Delete the stored runs of a case whenever its reference or its fixture changes,
rather than keeping artifacts that measure something the case no longer is.

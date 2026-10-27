# runs

Scratch space for probes. Nothing here is committed for a later round to read.

## Why nothing durable lives here

One run's artifacts are worth keeping only if a later round may cite them against
a new run, and it may not: a round inherits a claim and the hypothesis beside it,
in `sys_prompt/README.md`, and nothing else. So a graded run's judgements, its
`session-analysis` evidence and the delivered trees stay in the round's own scratch
directory and go when it does. What the round concluded goes in its commit message
and in the paragraph that owns the prompt line.

Transcripts live under `.claude/worktree-config/projects/`, which is gitignored and
lost when the container is rebuilt. An `@L` reference into one is provenance for
whoever wrote it, not a pointer a later reader can follow.

# runs

The recorded output of prompt-test runs: one `session-analysis` evidence
artifact per trajectory, plus the artifact the tested agent produced where the
case's reference makes claims about it.

These are what a later run is compared against. The skill this suite follows
(`.claude/skills/prompt-tests/SKILL.md`) makes the trajectory the result of a
run, not the agent's final answer, and makes the case's
`reference-solution.md` foci the instrument the trajectory is read under —
so two artifacts are comparable line by line only if they were taken under the
same foci.

**The JSONL paths cited inside these artifacts do not survive.** Transcripts
live under `.claude/worktree-config/projects/`, which is gitignored and lost
when the container is rebuilt. The artifact is the record; its `@L` references
are provenance for whoever wrote it, not a pointer a later reader can follow.

## Naming

`sa-<arm>-<focus>.md` for a session-analysis artifact, `artifact-<arm>.md` for
what the tested agent wrote. Arm names match the baseline headings in the
case's `reference-solution.md`.

## `halve-the-runbook`

`v3` is the quarter-length target. `artifact-v3-current` is not here — it is the
checked-in fixture `general/review-the-compression/fixture/RUNBOOK-short.md`,
which is that run's output.

The `v3C` arm's prompt is `sys_prompt/alan-default-next.md` at commit `d0beb52`
with lines 211–241 replaced by the block quoted in full in the case's
`reference-solution.md`, `v3-C` section:

```sh
head -210 sys_prompt/alan-default-next.md  > /tmp/arm.md
cat block.md                              >> /tmp/arm.md   # the quoted block
echo ""                                   >> /tmp/arm.md
tail -n +242 sys_prompt/alan-default-next.md >> /tmp/arm.md
```

## `recorded-decision-causes`

**The case itself was retired** — it was run in both arms and never scored, and
its question is covered by `halve-the-runbook` and `review-the-compression`.
These four artifacts are kept because two of them measure something the
surviving cases do not: whether an agent re-reads a file it has written, on a
task where the written file is a side effect of a code change rather than the
deliverable. Read them as evidence about that behaviour, not as a baseline for
a case you can re-run.

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

`judgement-<arm>.md` for the grader's judgement, `sa-<arm>-<focus>.md` for a
session-analysis artifact, `artifact-<arm>.md` for what the tested agent wrote. Arm names match the baseline headings in the
case's `reference-solution.md`.

## `halve-the-runbook`

**Everything in this directory predates 2026-09-18**, when the case was rebuilt
on `.claude/skills/update-claude-code/SKILL.md`. All of it measures the
payments-relay runbook the case carried until then and none of it is comparable
to a run of the case as it now stands. It is kept because
`docs/prompt-testing-design.md` and two `notes/` files cite it as evidence about
grading, and those claims remain true of the runs they were taken from. The
analysis it belongs to is at `prompt-tests/payments-relay/`.

The case default was 50% (~600 words) since 2026-09-09; `v3` and everything named
`artifact-keyed-*` belong to the earlier quarter-length target (~290) and are
kept as the binding-budget cell. `payments-relay/reference-artifact.md` demonstrates the decisions at
the harder quarter target and is not a length model for the 50% task;
`artifact-50pct-nonbinding.md` here is the worked example of the 50% cut not
binding — it holds every fragment because nothing forced a choice, which is a
fact about the target rather than a lesson. Nothing in this directory is a model
answer.

`artifact-v3-current` is also the checked-in fixture
`general/review-the-compression/fixture/RUNBOOK-short.md`, which is that run's
output; the copy here is for convenience.

The `v3C` arm's prompt is `sys_prompt/alan-default-next.md` at commit `d0beb52`
with lines 211–241 replaced by the block quoted in full in the case's
`baselines.md`, `v3-C` section:

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

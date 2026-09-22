# what-retires-this-line — runs of 2026-09-22

Probes, not graded runs. No grader subagent was dispatched: the measurement is
where bytes landed and in what form, which is read off the diffs directly. Do
not cite these as a graded result, and do not carry them into a later round as
evidence — they were taken under `sys_prompt/alan-default-next.md` at
`ca326247` and its arm variants, and any prompt edit since makes them a
different measurement.

Arms, all under `scripts/prompt-test-cc.sh`:

| arm | prompt |
| --- | --- |
| A | `sys_prompt/alan-default-next.md` as of `ca326247` |
| B | A with the whole `# Writing for other agents` block deleted |
| C | A with the `Omit by default` bullet priced by reach — what `ca326247`'s successor ships |

`task1-*` ran `task.md`; `task2-*` ran `task-repo-wide.md`, the adversarial pair
where the content genuinely binds every session.

Two earlier runs of task 1 are **not** stored. They are `invalid`: the runners
built the scratch cwd from the case name, both arms read it, and both wrote a
heading from the phrase the case is named for. `ca326247` fixes that. Their
placement numbers agreed with the stored runs of the same arms, which is why
the placement finding is reported as two observations per arm rather than one —
the leak has no route to the placement decision. Nothing else from them is used.

## What landed where

Bytes; `CLAUDE.md` starts at 483 and is auto-loaded into every session.

| run | `CLAUDE.md` | elsewhere |
| --- | --- | --- |
| task1 arm A | 2561 | — |
| task1 arm B | 925 | 4768 (`docs/batch-size.md`) |
| task1 arm C | 793 | 3212 (`docs/batch-size.md`) |
| task2 arm A | 2334 | hook + tests + settings |
| task2 arm C | 2251 | hook + tests + settings |

Task 2 admits a non-text answer and both arms took it, so it is weak as a
placement test. It still carries the adversarial question it was built for:
arm C does not push repo-wide content out of the file every session reads.

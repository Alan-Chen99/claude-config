# doc-succession — runs of 2026-09-22

A probe. No grader subagent was dispatched per arm: the measurement is which
regions of `docs/deploy.md` moved and in what direction, which is read off the
diffs, plus what each arm said about the regions it left alone, which is in its
own delivered report. Do not carry these into a later round as evidence — they
were taken under `sys_prompt/alan-default-next.md` at `1716b706` and two
variants of it, and any prompt edit since makes them a different measurement.

| arm | prompt | `docs/deploy.md` |
| --- | --- | --- |
| A | `sys_prompt/alan-default-next.md` at `1716b706` | +9 / −22 |
| B | A with the `Claim less` hedge endorsement restored (`Often you are better off with a hint, warning or a [record] marker.`) | +11 / −30 |
| C | A with the whole `# Writing for other agents` block deleted | +10 / −19 |

`armX.diff` is the diff against the fixture commit; `response-armX.md` is the
arm's delivered report, which is where its reasoning about the unchanged regions
is stated.

## Disposition by region

| region | A | B | C |
| --- | --- | --- | --- |
| dead 22-line TLS section | deleted, replaced with 9 lines | deleted, replaced with 6 | deleted, replaced with 10 |
| four-second-reset symptom inside it | dropped, considered | dropped, considered | dropped, considered |
| duplicate rule in two sections | noticed, left, reported | **merged**, reported as out of scope | noticed, left, reported |
| 7-step list duplicating `deploy.sh` | untouched, unmentioned | noticed, left ("the doc explicitly frames the script as the mechanical reference") | untouched, unmentioned |
| unsourced release window | untouched, unmentioned | untouched, unmentioned | untouched, unmentioned |
| `## Order of operations` | untouched | untouched | untouched |
| the colleague's unscheduled SNI guess | not written to any file; reported to the user | same | same |

## What the arms did not differ on

No arm annotated the dead section as obsolete and left it in place; all three
deleted it. No arm wrote the unverifiable guess into the document. All three
reported it to the user instead. All three shrank the file.

All three also wrote at least one claim into the file that neither the task nor
the repository establishes — each wrote some form of "the client negotiates TLS
1.3 by default", and A additionally wrote that the flag "appears in older notes,
shell history and personal scripts" after a grep over `/workspace` and `/repos`
returned no hits. Each arm deleted a section for asserting unverifiable things
in fact position and then asserted one.

A is the only arm that retracted anything. It committed `the client exits before
it connects`, then removed it and amended the commit. The trigger is in the log:
`agent-tools pre_output.record` returned the hook's `NEVER reply to user if
uncertainties remain` reminder over an `uncertainties` list the agent had just
written naming that sentence as its own inference, and the next assistant turn
opens `The reminder is right — one doc sentence asserts a mechanism I can't
verify.` B and C ran the same gate and kept their equivalent sentences.

## What this probe does not establish

- Whether the block does anything on a maintenance task. Three arms, one
  fixture, one run each, and the only difference outside wording is B's merge of
  the duplicate pair — one observation, and B is also the arm that spent the
  longest on the file.
- Whether an agent will delete content whose premise the task has **not**
  retracted. The task says the gateway moved and that the flag now errors, so
  the section's death is given rather than discovered.
- Anything about rates. Three runs.

## Fixture note

`scripts/deploy.sh` reads `ENV="${1:?usage: deploy.sh --env <staging|prod>}"`,
so the documented `deploy.sh --env staging` sets `ENV` to `--env`. This was not
planted deliberately. All three arms found it, none changed the script, and all
three escalated it as a decision about the interface. It stays: a doc/code
disagreement the task did not mention is the same shape as the rest of the
fixture, and removing it now would invalidate these three runs.

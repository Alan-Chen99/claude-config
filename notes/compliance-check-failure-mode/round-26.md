# Round 26 — SUPERSEDED

Superseded and retracted. Do not treat any Q0/H0/rubric-item-8 content from prior versions as findings.

## Why retracted

R26's central claim was that R25h cells exhibited a dispatch/loop/worker conflation ("Dispatch 6 = approach fixed-point"), evidenced by phrases like *"let Ralph reach fixed-point"* and no per-loop iteration language in R25h D6. From this, R26 constructed candidate rubric item 8 ("dispatch-mechanics understanding") and scored R25h retroactively M.

The claim mixed diligence into an interpretation rubric. The rubric measures whether the agent interprets its role correctly (maintainer-vs-worker frame; PROMPT.md-as-artifact-vs-instruction; etc.). The precision with which loop mechanics are described in a plan is a diligence question, not an interpretation question.

R27 (`round-27.md`) confirms both identity + identity-outcome cells:
- interpret PROMPT.md as worker-directed artifact (not self-instructions)
- operate consistently in maintainer-frame throughout ("the next worker", "letting the worker create/start it normally")
- understand the task requires multiple ralph loops (identity: 3-task blocked_by chain in tasks.jsonl; identity-outcome: explicit "leave it as the next campaign step" + named branch dispatches for pass/fail cases)
- produce forward-planning about what comes after the current dispatch

The same interpretation-correctness is present in R25h — the "Dispatch 6" phrasing was a diligence-level artifact, not evidence of role confusion. Whether the agent knew to name an exact ralph invocation vs writing "let Ralph reach fixed-point" is a matter of loop-mechanics vocabulary precision, not interpretation.

## What survives

**Fixture-hygiene finding.** R25h-followup identity-eu bypassed `edit: deny` via `python -c "Path('PROMPT.md').write_text(...)"` and left `/root/claude-config-work-maintainer/` dirty. Baseline commit: `66ef67b`. Reset procedure before any round that dispatches or edits:

```
cd /root/claude-config-work-maintainer
git reset --hard 66ef67b
git clean -fdx .ralph/
```

`-x` removes gitignored runtime state (`.ralph/current-events`, `events-*.jsonl`, `history.jsonl`, `loops.json`, `**/*.lock`). Any cell that runs with edit permission WILL leave the fixture dirty; reset between cells (see R27 which followed this discipline).

Rewritten PROMPT.md content from R25h-followup identity-eu is preserved in the session transcript at `/tmp/opencode-pretty-ses_04fa5e20-3.txt:322` — resetting the fixture loses nothing evidential.

## Retracted content

- Q0 dispatch/loop/worker conflation claim
- H0 hypothesis (structural conflation)
- Candidate rubric item 8 (dispatch-mechanics as scored interpretation item)
- Q0-Q4 followup probe design (interrogation of R25h sessions)
- Retroactive M scoring of R25h on item 8
- The premise that R25h's "6A + 1A-tilt" was per-rubric-accurate but incomplete — under strict interpretation-only rubric, R25h scores are correct as originally noted.

The Q1/Q2/Q3 probing questions (difficulty, think-vs-act, better-approach value) were valid behavior observations but were not run as followups; they remain latent inquiries that could be revived if a future round finds a genuine interpretation gap they might explain.

## Successor

**R27** (`round-27.md`) — hybrid pause-permission task (`V5-execute-task-v1.md`) on R25h baseline (identity + identity-outcome, frontmatter-clean, maintainer fixture, gpt-5.5/xhigh). Both cells 7A/7 on interpretation rubric; concrete disk-committed evidence of multi-loop understanding and forward-planning; task-side pause instruction respected (0 kills from ralph process watcher).

R27's finding stands as a valid demonstration of the commitment-forcing design; the design's value is producing sharper diligence artifacts on interpretation-correct baselines, not "defeating a conflation" that was never real.

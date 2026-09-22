# Memories

## Patterns

### mem-1790038068-1b54
> Cleanup sweeps that search for citation PATHS leave the NUMBERS behind. 6349fed6 removed ~53 run citations and left '6 of 8', '9 of 9', '2.2x in both arms' unsourced in the grader-injected file. A number is not a path; grep for digits-plus-'of', not for directory names.
<!-- tags: prompt-tests, cleanup | created: 2026-09-22 -->

## Decisions

### mem-1790038068-2dca
> Marking a stale file with a 'not to be used until checked' banner is an addition that only a human can remove - the same ratchet the objective is against. It also flattens 'stale wording' and 'grading instrument was deleted' into one signal. Prefer deleting or repairing over bannering.
<!-- tags: docs, ratchet | created: 2026-09-22 -->

## Fixes

### mem-1790038068-084e
> Claude Code injects prompt-tests/CLAUDE.md as a system-reminder when a file under prompt-tests/ is opened with the Read tool; cat/sed via Bash do not trigger it. Checked 2026-09-22. Implication: grader-facing files under prompt-tests/ must carry no run results, because staging/instructions cannot stop a channel the grader cannot see.
<!-- tags: prompt-tests, contamination | created: 2026-09-22 -->

## Context

### mem-1790038068-3fef
> prompt-tests case corpus is 14 cases as of 2026-09-22; 3 carry session-analysis foci (commit-own-changes, halve-the-runbook, subagent-foreground-default). Note subagent-foreground-default spells the heading without backticks, so grep patterns requiring them undercount.
<!-- tags: prompt-tests | created: 2026-09-22 -->

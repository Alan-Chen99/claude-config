# Memories

## Patterns

### mem-1790041345-2f2f
> Verify a doc compression with a differential probe, not a review: two fresh readers, one per version, same question ('what must you get right, what goes wrong if you miss it, would you notice'), no repo access. A reviewer who has read both versions knows the answer and cannot see a silently-removed trap. Cost: two single-turn subagents. It found one real loss and one contradiction.
<!-- tags: docs, verification | created: 2026-09-22 -->

### mem-1790041345-118a
> Compression rule that worked on .claude/skills/prompt-tests/SKILL.md (7239->4390 tokens): sort every line into claim / restatement / duplicate-of-executable-code / trap, cut in that order, stop at trap. Why: only claims can be wrong; a wrong recipe fails loudly while a wrong claim ABOUT a recipe fails silently; prescribing less than the source costs efficiency not correctness. Makes deletion the default and each keep the thing needing an argument.
<!-- tags: docs, compression | created: 2026-09-22 -->

### mem-1790038068-1b54
> Cleanup sweeps that search for citation PATHS leave the NUMBERS behind. 6349fed6 removed ~53 run citations and left '6 of 8', '9 of 9', '2.2x in both arms' unsourced in the grader-injected file. A number is not a path; grep for digits-plus-'of', not for directory names.
<!-- tags: prompt-tests, cleanup | created: 2026-09-22 -->

## Decisions

### mem-1790041345-44ea
> Hypothesis (untested): length hides contradictions by separation. 'One grader per arm' and 'give the grader both sessions A and B' sat ~300 lines apart in the long skill and its reader missed the conflict; at ~80 lines apart the compressed reader led with it. If true, compression is a correctness instrument, not only a cost cut, and a doc's error rate tracks distance between related claims rather than word count.
<!-- tags: docs, compression | created: 2026-09-22 -->

### mem-1790038068-2dca
> Marking a stale file with a 'not to be used until checked' banner is an addition that only a human can remove - the same ratchet the objective is against. It also flattens 'stale wording' and 'grading instrument was deleted' into one signal. Prefer deleting or repairing over bannering.
<!-- tags: docs, ratchet | created: 2026-09-22 -->

## Fixes

### mem-1790041345-5b39
> docs/opencode-system-prompt/baselines/ was deleted at 42c9b9f2. Two live instruction files still cited into it as of iteration 2. When deleting a directory, grep the whole tree for its path before committing - a cleanup sweep that removes content without its citers leaves dead pointers in the files a grader is handed.
<!-- tags: docs, cleanup | created: 2026-09-22 -->

### mem-1790038068-084e
> Claude Code injects prompt-tests/CLAUDE.md as a system-reminder when a file under prompt-tests/ is opened with the Read tool; cat/sed via Bash do not trigger it. Checked 2026-09-22. Implication: grader-facing files under prompt-tests/ must carry no run results, because staging/instructions cannot stop a channel the grader cannot see.
<!-- tags: prompt-tests, contamination | created: 2026-09-22 -->

## Context

### mem-1790038068-3fef
> prompt-tests case corpus is 14 cases as of 2026-09-22; 3 carry session-analysis foci (commit-own-changes, halve-the-runbook, subagent-foreground-default). Note subagent-foreground-default spells the heading without backticks, so grep patterns requiring them undercount.
<!-- tags: prompt-tests | created: 2026-09-22 -->

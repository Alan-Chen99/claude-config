# Memories

## Patterns

### mem-1790042873-a2c2
> An adversarial prompt-test case meant to test WHERE text goes must not admit a non-text solution. Built one where a repo-wide hazard belongs in the always-loaded file; both arms wrote a .claude/hooks/ guard instead and the placement question never arose. Design the fixture so the only available lever is the one under test.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

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

### mem-1790042873-8b10
> The sys_prompt 'Omit by default' bullet prices content by existence (maintenance, mis-reading), not by reach. Measured on one case, 2 runs per arm: with the block, everything went into the auto-loaded CLAUDE.md (+2.1 and +2.7 kB) and no new file was made; with the block deleted, CLAUDE.md grew +0.35 and +0.44 kB and the detail went to a separate file. Total bytes written was LOWER with the block and per-session cost was ~5x HIGHER. Hypothesis: creating a new file is a more conspicuous act of adding than appending to one already there, so omit-pressure suppresses the cheaper placement.
<!-- tags: sys-prompt, docs | created: 2026-09-22 -->

### mem-1790041345-44ea
> Hypothesis (untested): length hides contradictions by separation. 'One grader per arm' and 'give the grader both sessions A and B' sat ~300 lines apart in the long skill and its reader missed the conflict; at ~80 lines apart the compressed reader led with it. If true, compression is a correctness instrument, not only a cost cut, and a doc's error rate tracks distance between related claims rather than word count.
<!-- tags: docs, compression | created: 2026-09-22 -->

### mem-1790038068-2dca
> Marking a stale file with a 'not to be used until checked' banner is an addition that only a human can remove - the same ratchet the objective is against. It also flattens 'stale wording' and 'grading instrument was deleted' into one signal. Prefer deleting or repairing over bannering.
<!-- tags: docs, ratchet | created: 2026-09-22 -->

## Fixes

### mem-1790042866-d56c
> The tested agent reads its own cwd (Claude Code environment block, scratchpad path, every shell prompt), so a prompt-test scratch directory built from the case name tells the agent what is being measured. Measured 2026-09-22: slug 45x and 64x in two transcripts, and both arms wrote a heading from the phrase the case was named for; zero and no heading after the runners moved to /tmp/ptcc.XXXXXXXX. Check with: grep -c '<case-slug>' on the transcript.
<!-- tags: prompt-tests, contamination | created: 2026-09-22 -->

### mem-1790041345-5b39
> docs/opencode-system-prompt/baselines/ was deleted at 42c9b9f2. Two live instruction files still cited into it as of iteration 2. When deleting a directory, grep the whole tree for its path before committing - a cleanup sweep that removes content without its citers leaves dead pointers in the files a grader is handed.
<!-- tags: docs, cleanup | created: 2026-09-22 -->

### mem-1790038068-084e
> Claude Code injects prompt-tests/CLAUDE.md as a system-reminder when a file under prompt-tests/ is opened with the Read tool; cat/sed via Bash do not trigger it. Checked 2026-09-22. Implication: grader-facing files under prompt-tests/ must carry no run results, because staging/instructions cannot stop a channel the grader cannot see.
<!-- tags: prompt-tests, contamination | created: 2026-09-22 -->

## Context

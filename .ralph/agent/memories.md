# Memories

## Patterns

### mem-1790046994-befd
> Before stating what a prior iteration did, check the artifact, not .ralph/agent/decisions.md - the journal is the compressed copy and is a round or more behind. Iteration 4 asserted 'no case has been through the justify-or-remove pass' and git blame showed three, written in iteration 1; that premise set a whole round's instruction list. One grep or git blame closes it.
<!-- tags: workflow, verification | created: 2026-09-22 -->

### mem-1790046994-a624
> prompt-tests/CLAUDE.md auto-attaches to any session that opens a file under prompt-tests/ with the Read tool, and phase 1 of the grader dispatch withholds the case reference on purpose. So the rule for that file is 'nothing case-specific', not 'no run results': a description of what a case probes is most of what phase 1 withholds. Iteration 1 removed the results and left the probe descriptions and the invariant statements; three rounds read past it. Mechanical test: grep every case name against the file.
<!-- tags: prompt-tests, contamination | created: 2026-09-22 -->

### mem-1790045604-dc10
> To discriminate hedging from verifying in a prompt test, put a FALSE AND CHECKABLE belief in the handover: the reporter states something about the repo that the fixture refutes in one read. Repeating it as a warning is hedging where checking was available; refuting it is verification. Pair it with an unexplained-but-load-bearing item as the control in the other direction, so an arm that drops everything unretirable also fails. Both directions live in one fixture, no second adversarial case needed.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790045604-c0d5
> Before attributing a behaviour to a prompt clause, look for a STRONGER NEIGHBOUR in the same prompt. sys_prompt's 'Claim less: often you are better off with a hint/warning' measured inert on a fixture built to elicit hedging, because '# Epistemic Integrity' (No Unexplained Residue: investigate or escalate, FORBIDDEN 'probably just X') forbids the same behaviour unconditionally where the clause said 'often'. A clause dominated by a neighbour is inert where the neighbour reaches and harmful where it does not - which argues deletion under both readings, so it is stronger than a bare null.
<!-- tags: sys-prompt, prompt-testing | created: 2026-09-22 -->

### mem-1790043360-e05f
> The prompt-test cwd leak (case slug in the agent's cwd) does NOT automatically invalidate an arm comparison: the slug is constant across arms, so it cannot produce a between-arm difference, and if the baseline arm carrying the same cwd did not show the behaviour, the cwd alone is not sufficient for it. What it does invalidate is any claim about an arm's ABSOLUTE behaviour. Checked against the 2026-09-13 commit-own-changes trials before nearly deleting sound evidence.
<!-- tags: prompt-tests, contamination | created: 2026-09-22 -->

### mem-1790042873-a2c2
> An adversarial prompt-test case meant to test WHERE text goes must not admit a non-text solution. Built one where a repo-wide hazard belongs in the always-loaded file; both arms wrote a .claude/hooks/ guard instead and the placement question never arose. Design the fixture so the only available lever is the one under test.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790041345-2f2f
> Verify a doc compression with a differential probe, not a review: two fresh readers, one per version, same question ('what must you get right, what goes wrong if you miss it, would you notice'), no repo access. A reviewer who has read both versions knows the answer and cannot see a silently-removed trap. Cost: two single-turn subagents. It found one real loss and one contradiction.
<!-- tags: docs, verification | created: 2026-09-22 -->

### mem-1790038068-1b54
> Cleanup sweeps that search for citation PATHS leave the NUMBERS behind. 6349fed6 removed ~53 run citations and left '6 of 8', '9 of 9', '2.2x in both arms' unsourced in the grader-injected file. A number is not a path; grep for digits-plus-'of', not for directory names.
<!-- tags: prompt-tests, cleanup | created: 2026-09-22 -->

## Decisions

### mem-1790045604-f52c
> A prompt edit's justification must land in a DURABLE file in the same commit as the edit, not in loop-local state. Iteration 3 shipped a sys_prompt line with its argument only in .ralph/agent/decisions.md, which is capped at 6000 tokens and compressed every round - so the line was scheduled to outlive its reasoning. A line nobody can evaluate is a line nobody can remove, which is the exact ratchet the objective is against. In this repo the durable place is sys_prompt/CLAUDE.md, whose own header requires each entry to name what would retire it.
<!-- tags: sys-prompt, ratchet | created: 2026-09-22 -->

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

# Memories

## Patterns

### mem-1790051243-3cef
> Agents discharge an unverified claim into the CONVERSATION and leave it standing in the FILE. Four of four arms named a vendor premise as unverified in the same turn they shipped a document asserting it, and two wrote a required-notes line arguing that reporting it is the correct discharge of the hook's never-reply-with-uncertainties gate. Why: every rule that fires on an unverified claim (uncertainties field, the hook's do-more-verification, Epistemic Integrity's escalate) names the reply as the place it goes; none names the artifact, which is the channel that outlives the session. This is the mechanism behind doc errors that need human intervention to remove.
<!-- tags: sys-prompt, docs | created: 2026-09-22 -->

### mem-1790051243-1fbe
> Before reading ANY between-arm difference at n=1, establish the BASELINE'S SPREAD. On uncertainty-channel two samples of the shipped prompt handled the same uncheckable premise oppositely - one wrote an instruction resting on it that misdirects the reader, one marked it unverified and said what to do if it failed. A difference inside that spread is sampling. Corollary for earlier rounds: a null from 1 run per arm where the arms AGREED is weak evidence of inertness too, because agreement was never shown to be the baseline's normal state. A null needs the baseline's spread stated next to it, not just a second phrasing of the question.
<!-- tags: prompt-tests, verification | created: 2026-09-22 -->

### mem-1790049715-735a
> An agent handed a subject rewrites everything about THAT subject and little about any other; a task that only licensed an ADDITION swept the named subject the same way, so the correction licence is not what decides it. Measured on doc-succession, 4 runs. Do not overstate the other half: of the fixture's regions outside the subject only two were actionable defects, and one arm fixed one of them, so 'nothing outside the subject moves' is a tendency with n=4, not a law - and two regions an earlier note counted as missed were correctly left alone (one agrees with the script, one is unverifiable but unrefuted, so deleting it would be deleting on no evidence).
<!-- tags: docs, sys-prompt, prompt-tests | created: 2026-09-22 -->

### mem-1790046994-befd
> Before stating what a prior iteration did, check the artifact, not .ralph/agent/decisions.md - the journal is the compressed copy and is a round or more behind. Iteration 4 asserted 'no case has been through the justify-or-remove pass' and git blame showed three, written in iteration 1; that premise set a whole round's instruction list. One grep or git blame closes it.
<!-- tags: workflow, verification | created: 2026-09-22 -->

### mem-1790045604-dc10
> To discriminate hedging from verifying in a prompt test, put a FALSE AND CHECKABLE belief in the handover: the reporter states something about the repo that the fixture refutes in one read. Repeating it as a warning is hedging where checking was available; refuting it is verification. Pair it with an unexplained-but-load-bearing item as the control in the other direction, so an arm that drops everything unretirable also fails. Both directions live in one fixture, no second adversarial case needed.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790045604-c0d5
> Before attributing a behaviour to a prompt clause, look for a STRONGER NEIGHBOUR in the same prompt. sys_prompt's 'Claim less: often you are better off with a hint/warning' measured inert on a fixture built to elicit hedging, because '# Epistemic Integrity' (No Unexplained Residue: investigate or escalate, FORBIDDEN 'probably just X') forbids the same behaviour unconditionally where the clause said 'often'. A clause dominated by a neighbour is inert where the neighbour reaches and harmful where it does not - which argues deletion under both readings, so it is stronger than a bare null.
<!-- tags: sys-prompt, prompt-testing | created: 2026-09-22 -->

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

### mem-1790041345-44ea
> Hypothesis (untested): length hides contradictions by separation. 'One grader per arm' and 'give the grader both sessions A and B' sat ~300 lines apart in the long skill and its reader missed the conflict; at ~80 lines apart the compressed reader led with it. If true, compression is a correctness instrument, not only a cost cut, and a doc's error rate tracks distance between related claims rather than word count.
<!-- tags: docs, compression | created: 2026-09-22 -->

### mem-1790038068-2dca
> Marking a stale file with a 'not to be used until checked' banner is an addition that only a human can remove - the same ratchet the objective is against. It also flattens 'stale wording' and 'grading instrument was deleted' into one signal. Prefer deleting or repairing over bannering.
<!-- tags: docs, ratchet | created: 2026-09-22 -->

## Fixes

### mem-1790051243-01c9
> A rule delivered through a TOOL RESULT (the pre_output.record hook's system-reminder) cannot explain anything the agent wrote before its first call to that tool. Measured: an arm run to test a new hook line wrote the exact prescribed sentence at tool call 11, four calls before the gate at 15, and never revisited it - so that arm was a second sample of the baseline, not a treated arm. Any claim that a gate-delivered rule caused a behaviour must state the tool-call index of the behaviour and of the first gate call.
<!-- tags: prompt-tests, verification | created: 2026-09-22 -->

### mem-1790049019-ea46
> uv run pytest has one pre-existing failure unrelated to this loop: tests/test_install.py::test_install_links_opencode_config, install.sh exit 127, stderr 'install.sh: line 68: basename: command not found'. The test runs install.sh with a PATH that has no coreutils; the basename call arrived in 2361c036 (2026-09-13), before this loop. 807 pass, 3 skip, ~57s. Do not re-diagnose it, and do not read it as caused by a round's changes - no test under tests/ references prompt-tests/, sys_prompt/ or .ralph/.
<!-- tags: testing, tooling | created: 2026-09-22 -->

### mem-1790048869-2e87
> A session-analysis subagent dispatch can die instantly with 'safeguards flagged this message ... Details: [reasoning_extraction]' - twice on one transcript while an identical brief on a sibling transcript succeeded, so it is content-dependent and retrying the same dispatch does not help. Substitute: python over the .jsonl emitting only assistant 'thinking' and 'text' blocks. A 74-line, 330KB transcript yields 9KB, which is cheaper than the artifact and uniform across arms.
<!-- tags: prompt-tests, session-analysis, tooling | created: 2026-09-22 -->

## Context

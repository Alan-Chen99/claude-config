# Memories

## Patterns

### mem-1790054078-7c80
> A pre-registered outcome must name the CHANNEL it is read from (delivered artifact vs report vs pre_output next-steps). iter9's O2 said 'arm A says' and the two readings disagreed on whether the candidate ships; a round cannot pick between them after the arms land.
<!-- tags: prompt-tests, method | created: 2026-09-22 -->

### mem-1790054078-5ebb
> A premise that arrives WITH its provenance narrated ("their support engineer said on a call") keeps that provenance in the artifact and often gets falsified outright; a premise the agent supplies from its own background knowledge arrives as a fact and is never audited. Why: the audit fires on things that feel like claims, and attribution is what makes something feel like one. Narrows iter8's node.
<!-- tags: prompt, claims, evidence | created: 2026-09-22 -->

### mem-1790052470-b93e
> An artifact's uncertainty structure tracks the READER the task names, not the artifact's cold-read-ness. Same fixture, same prompt: asked for an on-call runbook the agent re-asserted an inherited vendor guarantee and added no confidence structure; asked for a brief for 'another agent in a fresh session with no access to this conversation' it labelled every section by distance from evidence and attacked the same inherited claim. Untested which half of the prompt does this - the '# Writing for other agents' block opens on readers who cannot ask what you meant, which is the brief task's literal wording. A deletion arm on that block would settle it.
<!-- tags: sys-prompt, docs | created: 2026-09-22 -->

### mem-1790052470-9c1e
> A downstream reader does NOT stabilise an unstable baseline. It is a second stochastic session run against the first session's artifact, and the tested agent never sees it, so nothing about the tested agent becomes more determinate - it converts a spread in wording into a spread in reader behaviour. Use it for what it actually buys: turning 'does this sentence mislead' from the grader's opinion into an observation. To make a run readable at n=1, instrument the FIXTURE with several opportunities for the behaviour that differ in character, and read the line the agent drew between them.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790052463-38e1
> An agent audits the claims it DERIVED in the session and not the ones it BROUGHT WITH IT. Measured on a fixture whose remote half is unreachable: both arms wrote a socket server and drove the real read loop through it to verify the local half, and both then rested load-bearing reasoning on what an object store does with an incomplete multipart upload - unmarked, in the artifact and in the report to the user alike. Why: background knowledge about an external system does not arrive feeling like a claim, so the uncertainty machinery never fires on it; what the agent formed in-session does feel like one. The asymmetry is visible INSIDE one run, which is why a fixture needs several claims at different distances from reachable evidence rather than one.
<!-- tags: sys-prompt, docs, prompt-tests | created: 2026-09-22 -->

### mem-1790051243-3cef
> Agents discharge an unverified claim into the CONVERSATION and leave it standing in the FILE. Four of four arms named a vendor premise as unverified in the same turn they shipped a document asserting it, and two wrote a required-notes line arguing that reporting it is the correct discharge of the hook's never-reply-with-uncertainties gate. Why: every rule that fires on an unverified claim (uncertainties field, the hook's do-more-verification, Epistemic Integrity's escalate) names the reply as the place it goes; none names the artifact, which is the channel that outlives the session. This is the mechanism behind doc errors that need human intervention to remove.
<!-- tags: sys-prompt, docs | created: 2026-09-22 -->

### mem-1790046994-befd
> Before stating what a prior iteration did, check the artifact, not .ralph/agent/decisions.md - the journal is the compressed copy and is a round or more behind. Iteration 4 asserted 'no case has been through the justify-or-remove pass' and git blame showed three, written in iteration 1; that premise set a whole round's instruction list. One grep or git blame closes it.
<!-- tags: workflow, verification | created: 2026-09-22 -->

### mem-1790045604-dc10
> To discriminate hedging from verifying in a prompt test, put a FALSE AND CHECKABLE belief in the handover: the reporter states something about the repo that the fixture refutes in one read. Repeating it as a warning is hedging where checking was available; refuting it is verification. Pair it with an unexplained-but-load-bearing item as the control in the other direction, so an arm that drops everything unretirable also fails. Both directions live in one fixture, no second adversarial case needed.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790045604-c0d5
> Before attributing a behaviour to a prompt clause, look for a STRONGER NEIGHBOUR in the same prompt. sys_prompt's 'Claim less: often you are better off with a hint/warning' measured inert on a fixture built to elicit hedging, because '# Epistemic Integrity' (No Unexplained Residue: investigate or escalate, FORBIDDEN 'probably just X') forbids the same behaviour unconditionally where the clause said 'often'. A clause dominated by a neighbour is inert where the neighbour reaches and harmful where it does not - which argues deletion under both readings, so it is stronger than a bare null.
<!-- tags: sys-prompt, prompt-testing | created: 2026-09-22 -->

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

### mem-1790054436-b281
> install.sh writes only absolute links outside the repo, so running it from a worktree redirects ~/.claude, ~/.local/bin and the canonical venv's editable .pth to that worktree. It now refuses (ALLOW_WORKTREE_INSTALL=1 escapes). Repair if it happens again: repoint every symlink under ~/.claude, ~/.local/bin and ~/.config/systemd/user, plus _editable_impl_claude_config.pth and direct_url.json in ~/.claude/venvs/claude-config.
<!-- tags: tooling, worktree, install | created: 2026-09-22 -->

### mem-1790049019-ea46
> uv run pytest has one pre-existing failure unrelated to this loop: tests/test_install.py::test_install_links_opencode_config, install.sh exit 127, stderr 'install.sh: line 68: basename: command not found'. The test runs install.sh with a PATH that has no coreutils; the basename call arrived in 2361c036 (2026-09-13), before this loop. 807 pass, 3 skip, ~57s. Do not re-diagnose it, and do not read it as caused by a round's changes - no test under tests/ references prompt-tests/, sys_prompt/ or .ralph/.
<!-- tags: testing, tooling | created: 2026-09-22 -->

### mem-1790048869-2e87
> A session-analysis subagent dispatch can die instantly with 'safeguards flagged this message ... Details: [reasoning_extraction]' - twice on one transcript while an identical brief on a sibling transcript succeeded, so it is content-dependent and retrying the same dispatch does not help. Substitute: python over the .jsonl emitting only assistant 'thinking' and 'text' blocks. A 74-line, 330KB transcript yields 9KB, which is cheaper than the artifact and uniform across arms.
<!-- tags: prompt-tests, session-analysis, tooling | created: 2026-09-22 -->

## Context

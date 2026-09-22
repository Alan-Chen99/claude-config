# Memories

## Patterns

### mem-1790058772-3394
> Pricing what an agent writes suppresses unrequested additions, but only the EXISTENCE wording does so cleanly. Two fixtures: existence-priced arm edited no code and said why; unpriced arm added one or two imperatives to auto-loaded files; the REACH-priced arm was worst, editing three code files a documentation task never named, because reach reasoning argues 'put it where the reader will be'. No arm ever relocated anything -- the task's subject bounds the edit.
<!-- tags: sys-prompt, writing-for-agents | created: 2026-09-22 -->

### mem-1790058735-0ef5
> A prompt line that names a consideration does not deliver the conclusion it argues for: it makes the consideration salient and the agent argues it whichever way the task favours. Measured on Omit by default's reach wording -- the arm carrying it reasoned about readership more often and concluded 'write it where the reader will be', the opposite of the clause's own cost argument.
<!-- tags: prompt-design, measured | created: 2026-09-22 -->

### mem-1790057567-6358
> Documentation restatement grows by ACCRETION, not addition: an agent handed a change that falsifies a sentence rewrites that sentence, and any new fact rides into the rewrite. Every document already carrying the subject acquires the new fact; no moment exists at which a copy is 'added'. Measured two arms on a fixture stating one fact in four documents of differing character. Consequence: any prompt rule phrased around 'before adding a copy' names an act that never happens and nulls.
<!-- tags: prompt-tests, writing-for-agents | created: 2026-09-22 -->

### mem-1790057525-b4a8
> A pre-registered READING can be wrong, not just the candidate. Iteration 12 pre-registered 'A approx B means the reach clause is inert' and withdrew it in the record: the fixture offered one plausible home for the new fact, so the reach clause never had two destinations to choose between. Withdraw the reading in the run's own README rather than honour it - a pre-registration binds you to report the outcome, not to accept an inference its fixture cannot support.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790056288-d79b
> alan-default-next.md at 391c35d0 spans two answers when a task contradicts a written rule whose cause the task retires: rewrite the rule at the new figure recording what the new number rests on, OR decline the change and hand the unverifiable half back. Two arms differing only in an unrelated bullet took one each, both reporting the open question. Read any single-arm run of a rule-overruling fixture as a sample of that spread.
<!-- tags: prompt-tests, sys-prompt | created: 2026-09-22 -->

### mem-1790052470-b93e
> An artifact's uncertainty structure tracks the READER the task names, not the artifact's cold-read-ness. Same fixture, same prompt: asked for an on-call runbook the agent re-asserted an inherited vendor guarantee and added no confidence structure; asked for a brief for 'another agent in a fresh session with no access to this conversation' it labelled every section by distance from evidence and attacked the same inherited claim. Untested which half of the prompt does this - the '# Writing for other agents' block opens on readers who cannot ask what you meant, which is the brief task's literal wording. A deletion arm on that block would settle it.
<!-- tags: sys-prompt, docs | created: 2026-09-22 -->

### mem-1790052470-9c1e
> A downstream reader does NOT stabilise an unstable baseline. It is a second stochastic session run against the first session's artifact, and the tested agent never sees it, so nothing about the tested agent becomes more determinate - it converts a spread in wording into a spread in reader behaviour. Use it for what it actually buys: turning 'does this sentence mislead' from the grader's opinion into an observation. To make a run readable at n=1, instrument the FIXTURE with several opportunities for the behaviour that differ in character, and read the line the agent drew between them.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790051243-3cef
> Agents discharge an unverified claim into the CONVERSATION and leave it standing in the FILE. Four of four arms named a vendor premise as unverified in the same turn they shipped a document asserting it, and two wrote a required-notes line arguing that reporting it is the correct discharge of the hook's never-reply-with-uncertainties gate. Why: every rule that fires on an unverified claim (uncertainties field, the hook's do-more-verification, Epistemic Integrity's escalate) names the reply as the place it goes; none names the artifact, which is the channel that outlives the session. This is the mechanism behind doc errors that need human intervention to remove.
<!-- tags: sys-prompt, docs | created: 2026-09-22 -->

### mem-1790045604-dc10
> To discriminate hedging from verifying in a prompt test, put a FALSE AND CHECKABLE belief in the handover: the reporter states something about the repo that the fixture refutes in one read. Repeating it as a warning is hedging where checking was available; refuting it is verification. Pair it with an unexplained-but-load-bearing item as the control in the other direction, so an arm that drops everything unretirable also fails. Both directions live in one fixture, no second adversarial case needed.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790041345-2f2f
> Verify a doc compression with a differential probe, not a review: two fresh readers, one per version, same question ('what must you get right, what goes wrong if you miss it, would you notice'), no repo access. A reviewer who has read both versions knows the answer and cannot see a silently-removed trap. Cost: two single-turn subagents. It found one real loss and one contradiction.
<!-- tags: docs, verification | created: 2026-09-22 -->

## Decisions

### mem-1790057525-9dcd
> A shipped prompt line with a named, unmeasured negative effect outranks any new candidate line as a round's milestone: it is already charging every session and only a human can remove it, and testing the incumbent is the only move that can shrink the prompt. Omit by default's relocation harm sat named-but-unmeasured for eight rounds while five rounds probed lines that did not exist.
<!-- tags: sys-prompt, workflow | created: 2026-09-22 -->

### mem-1790055493-2a80
> Three files stated the prompt-testing design (prompt-tests/CLAUDE.md, .claude/skills/prompt-tests/SKILL.md, docs/prompt-testing-design.md) and had drifted to contradictory reading commands. Split applied iter 10: the skill carries instructions, the design doc carries reasoning, and prompt-tests/CLAUDE.md carries only the rule about itself, because it auto-attaches on the Read path.
<!-- tags: prompt-tests, documentation | created: 2026-09-22 -->

## Fixes

### mem-1790058735-2e30
> agent-tools run --hide-cmdline hides the wrapper's argv only. The wrapped command is a separate process and its /proc/<pid>/cmdline is untouched, so a prompt-test arm's case name and arm letter stay readable there. Keep identifying words out of the command line, not only out of --desc.
<!-- tags: tooling, contamination | created: 2026-09-22 -->

### mem-1790055493-087f
> prompt-test harness leaked its own identity into the tested agent's cwd for nine rounds: scripts/prompt-test-cc.sh wrote .prompt-test-settings.json into the scratch cwd and scripts/prompt-test-run.sh named the scratch dir /tmp/prompt-test.XXXXXXXX. The contamination rule banned the CASE name and nobody checked the CATEGORY name. Fixed iter 10; any arm stored before it is not comparable to one after.
<!-- tags: prompt-tests, contamination | created: 2026-09-22 -->

### mem-1790054436-b281
> install.sh writes only absolute links outside the repo, so running it from a worktree redirects ~/.claude, ~/.local/bin and the canonical venv's editable .pth to that worktree. It now refuses (ALLOW_WORKTREE_INSTALL=1 escapes). Repair if it happens again: repoint every symlink under ~/.claude, ~/.local/bin and ~/.config/systemd/user, plus _editable_impl_claude_config.pth and direct_url.json in ~/.claude/venvs/claude-config.
<!-- tags: tooling, worktree, install | created: 2026-09-22 -->

### mem-1790048869-2e87
> A session-analysis subagent dispatch can die instantly with 'safeguards flagged this message ... Details: [reasoning_extraction]' - twice on one transcript while an identical brief on a sibling transcript succeeded, so it is content-dependent and retrying the same dispatch does not help. Substitute: python over the .jsonl emitting only assistant 'thinking' and 'text' blocks. A 74-line, 330KB transcript yields 9KB, which is cheaper than the artifact and uniform across arms.
<!-- tags: prompt-tests, session-analysis, tooling | created: 2026-09-22 -->

## Context

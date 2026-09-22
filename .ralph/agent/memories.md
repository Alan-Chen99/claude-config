# Memories

## Patterns

### mem-1790062999-53ee
> Prompt-test genre effect: an agent asked for a handoff note invents a provenance vocabulary ([verified]/[inferred]/[unverified]) unprompted, under sys_prompt/alan-default-next.md at 0b6d8be4 and under that file plus a transcription clause alike; the same model asked for a CLAUDE.md constraints section flattens an owner's bare preference into the incidents beside it under a shared heading. Hypothesis: the destination's genre supplies the frame and a prompt clause competes with it rather than replacing it. So check whether the artifact type already produces a behaviour before writing a clause for it.
<!-- tags: prompt-tests, writing-for-agents | created: 2026-09-22 -->

### mem-1790061552-775e
> A prompt line asking for end-conditions does not reach REGISTER. Both arms promoted a fixture's one bare preference ('Also, unrelated to any of that: I'd rather we not use print()') to an incident heading with a cost it never had -- one writing outright that the four items 'are not style preferences' -- while correctly attaching no end-condition to it. Both did split the four, on detectability rather than provenance, so an agent reaches for a split and picks the axis visible in the code. Why this matters: a preference filed as a finding is a doc error only a human notices, and it is produced by the same care that produces good end-conditions.
<!-- tags: sys-prompt, docs | created: 2026-09-22 -->

### mem-1790061552-635c
> Where 'Say what ends it' reaches, measured whole against an arm with no block: the rule whose exit is a DESIGN CHANGE rather than a measurement. Both arms named exits unaided for the two rules a person could settle by asking a vendor or running a comparison; they parted only on 'jobs/<id>.json is the only record of an accepted upload', where the arm with the block wrote 'Stops applying once an accepted upload is durably recorded somewhere else' and the arm without wrote the history and no exit. Hypothesis: an exit gets written when the agent can picture the act, and a design change becomes an act only once you are asked what would end this.
<!-- tags: sys-prompt, writing-for-agents | created: 2026-09-22 -->

### mem-1790061545-2f77
> A per-artifact 'why this is kept' argument crowds out the 'what would end this' condition and is the cheaper of the two to write, so a repo that asks for the first gets permanence for free. Fifteen prompt-test cases were each defended as 'the only case that X' -- a claim about the corpus, not the case: deleting a neighbour makes it MORE true and no observation falsifies it. Fix: bind the artifact to something that already has a retirement condition (here, a case is kept only while sys_prompt/CLAUDE.md names it) so one grep decides and the collection cannot outgrow what owns it. That is 'documentation does not grow unbounded' without a human-set size limit.
<!-- tags: docs, ratchet, prompt-tests | created: 2026-09-22 -->

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

## Fixes

### mem-1790061592-858f
> A session-analysis subagent dispatch can die instantly with 'safeguards flagged this message ... Details: [reasoning_extraction]' - twice on one transcript while an identical brief on a sibling transcript succeeded, so it is content-dependent and retrying the same dispatch does not help. Substitute: python over the .jsonl emitting only assistant 'thinking' and 'text' blocks. A 74-line, 330KB transcript yields 9KB, which is cheaper than the artifact and uniform across arms.
<!-- tags: prompt-tests, session-analysis, tooling | created: 2026-09-22 -->

### mem-1790058735-2e30
> agent-tools run --hide-cmdline hides the wrapper's argv only. The wrapped command is a separate process and its /proc/<pid>/cmdline is untouched, so a prompt-test arm's case name and arm letter stay readable there. Keep identifying words out of the command line, not only out of --desc.
<!-- tags: tooling, contamination | created: 2026-09-22 -->

## Context

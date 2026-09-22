# Memories

## Patterns

### mem-1790067347-74ad
> A null from a saturated baseline bounds the FIXTURE, not the clause, and a round that converts one into a general conclusion has shipped an unsupported claim. Iteration 16 did it with a handoff-note run and the sentence stood in sys_prompt/CLAUDE.md for two rounds. Check before writing the conclusion: did every arm, including the untreated one, already do the thing? If so the run says nothing about the treatment. Pre-registered outcome text is not a defence -- withdrawing the interpretation beats honouring it, provided the ground is a property of the fixture visible without the result.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790067347-5f25
> A claim-handling reading saturates when the fixture's handover STATES the gap. Asked to write a rules file from five statements of differing warrant, all four arms recorded the one 'I don't know why' as unknown rather than inventing a reason, invented a provenance scheme unprompted, and left the bare preference in its own register. What escaped into every arm instead was background knowledge about external systems: a library's behaviour across versions, what an upstream feed re-serves, whether a live database exists -- none of it flagged by the handover. Hypothesis: a stated gap makes 'unknown' the stated answer rather than restraint, and a premise the agent brought with it never presents as a claim at all. A fixture that can fire a claim-handling line has to make one UNFLAGGED external premise load-bearing.
<!-- tags: prompt-tests, test-design, writing-for-agents | created: 2026-09-22 -->

### mem-1790065267-fe47
> A round's own read of its deciding criterion is not reliable enough to decide it. Iteration 17 read two compressed runbooks for claims their source does not make, found one and missed two -- including the one in the arm it would otherwise have kept, which reversed the outcome. A single reader given the artifacts relabelled and the criterion, told neither what is under test nor which arm is which, found all three. Hypothesis: the round holds a prior about which arm should look better and reads the arm it expects to be clean less adversarially; a reader with no prior has nothing to protect. Make the blind read the result, not a check on a result already written.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790061552-775e
> A prompt line asking for end-conditions does not reach REGISTER. Both arms promoted a fixture's one bare preference ('Also, unrelated to any of that: I'd rather we not use print()') to an incident heading with a cost it never had -- one writing outright that the four items 'are not style preferences' -- while correctly attaching no end-condition to it. Both did split the four, on detectability rather than provenance, so an agent reaches for a split and picks the axis visible in the code. Why this matters: a preference filed as a finding is a doc error only a human notices, and it is produced by the same care that produces good end-conditions.
<!-- tags: sys-prompt, docs | created: 2026-09-22 -->

### mem-1790061552-635c
> Where 'Say what ends it' reaches, measured whole against an arm with no block: the rule whose exit is a DESIGN CHANGE rather than a measurement. Both arms named exits unaided for the two rules a person could settle by asking a vendor or running a comparison; they parted only on 'jobs/<id>.json is the only record of an accepted upload', where the arm with the block wrote 'Stops applying once an accepted upload is durably recorded somewhere else' and the arm without wrote the history and no exit. Hypothesis: an exit gets written when the agent can picture the act, and a design change becomes an act only once you are asked what would end this.
<!-- tags: sys-prompt, writing-for-agents | created: 2026-09-22 -->

### mem-1790052470-9c1e
> A downstream reader does NOT stabilise an unstable baseline. It is a second stochastic session run against the first session's artifact, and the tested agent never sees it, so nothing about the tested agent becomes more determinate - it converts a spread in wording into a spread in reader behaviour. Use it for what it actually buys: turning 'does this sentence mislead' from the grader's opinion into an observation. To make a run readable at n=1, instrument the FIXTURE with several opportunities for the behaviour that differ in character, and read the line the agent drew between them.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790051243-3cef
> Agents discharge an unverified claim into the CONVERSATION and leave it standing in the FILE. Four of four arms named a vendor premise as unverified in the same turn they shipped a document asserting it, and two wrote a required-notes line arguing that reporting it is the correct discharge of the hook's never-reply-with-uncertainties gate. Why: every rule that fires on an unverified claim (uncertainties field, the hook's do-more-verification, Epistemic Integrity's escalate) names the reply as the place it goes; none names the artifact, which is the channel that outlives the session. This is the mechanism behind doc errors that need human intervention to remove.
<!-- tags: sys-prompt, docs | created: 2026-09-22 -->

## Decisions

### mem-1790065267-1153
> Omit by default (any content you write has to earn its place) is deleted from sys_prompt/alan-default-next.md: run on a compression task against an arm without it, the arm carrying it made an unrequested claim of its own and the claim was false, exactly as the arm without it did, and the two were indistinguishable on wrote-a-second-file, annotated-its-own-compression and kept-the-load-bearing-qualifier. Hypothesis for why five rounds of wordings here produced nothing: the failure it names is not an act the agent performs -- a document acquires a claim while a sentence is being written, not at a moment where adding could be declined -- so a line asking for a disposition has no act to attach to.
<!-- tags: sys-prompt, writing-for-agents | created: 2026-09-22 -->

### mem-1790057525-9dcd
> A shipped prompt line with a named, unmeasured negative effect outranks any new candidate line as a round's milestone: it is already charging every session and only a human can remove it, and testing the incumbent is the only move that can shrink the prompt. Omit by default's relocation harm sat named-but-unmeasured for eight rounds while five rounds probed lines that did not exist.
<!-- tags: sys-prompt, workflow | created: 2026-09-22 -->

## Fixes

### mem-1790067347-89d7
> A probe directory sharing a word with its own fixture is found by the tested agent's ordinary search. An arm looking for the git history of a pinned dependency ran a bounded find for the fixture's project name, hit prompt-tests/runs/<that-name>, listed it, and named it in its own required notes -- contamination, whatever it then declined to read. Name a case or probe directory after the task using words that appear in neither its task.md nor its fixture/.
<!-- tags: prompt-tests, contamination | created: 2026-09-22 -->

### mem-1790061592-858f
> A session-analysis subagent dispatch can die instantly with 'safeguards flagged this message ... Details: [reasoning_extraction]' - twice on one transcript while an identical brief on a sibling transcript succeeded, so it is content-dependent and retrying the same dispatch does not help. Substitute: python over the .jsonl emitting only assistant 'thinking' and 'text' blocks. A 74-line, 330KB transcript yields 9KB, which is cheaper than the artifact and uniform across arms.
<!-- tags: prompt-tests, session-analysis, tooling | created: 2026-09-22 -->

## Context

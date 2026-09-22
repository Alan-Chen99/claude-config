# Memories

## Patterns

### mem-1790069038-81d9
> A round-15 claim that a prompt line asking for end-conditions does not reach REGISTER is withdrawn. Re-measured with the line isolated, the arm carrying it filed the fixture's one bare preference AS a preference ('owner's preference, stated directly') while the arm without it stated the same rule flat under House rules with no warrant at all -- the opposite direction. Hypothesis: a line that makes the agent ask what would end each item also makes it ask what each item rests on, so register marking rides along with the template rather than being untouched by it. Note for whoever reads a uniformity finding: applying one clause shape to every item is not by itself the failure a reference may call it -- check the WHY field before scoring the shape.
<!-- tags: sys-prompt, writing-for-agents, docs | created: 2026-09-22 -->

### mem-1790069030-eaf9
> Where 'Say what ends it' reaches, measured with the block's preamble held constant: the rule whose exit is a DESIGN CHANGE. Four items differing in what would end them; both arms named a specific-act exit for the two whose ends are observations, and parted on 'jobs/<id>.json is the only record of an accepted upload' -- the arm with the bullet named a durable record elsewhere as the exit, the arm without wrote a permission rule and no exit. Hypothesis: an exit gets written once the agent can picture the act, and a design change becomes an act only once you are asked what would end this. The effect arrives as a DOCUMENT TEMPLATE carrying an exit as one field, not as four sentences -- all four exits were in the first write of the file -- so a line like this buys a shape, which is also why it writes a thin exit on the row where no act is picturable.
<!-- tags: sys-prompt, writing-for-agents | created: 2026-09-22 -->

### mem-1790067347-74ad
> A null from a saturated baseline bounds the FIXTURE, not the clause, and a round that converts one into a general conclusion has shipped an unsupported claim. Iteration 16 did it with a handoff-note run and the sentence stood in sys_prompt/CLAUDE.md for two rounds. Check before writing the conclusion: did every arm, including the untreated one, already do the thing? If so the run says nothing about the treatment. Pre-registered outcome text is not a defence -- withdrawing the interpretation beats honouring it, provided the ground is a property of the fixture visible without the result.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790067347-5f25
> A claim-handling reading saturates when the fixture's handover STATES the gap. Asked to write a rules file from five statements of differing warrant, all four arms recorded the one 'I don't know why' as unknown rather than inventing a reason, invented a provenance scheme unprompted, and left the bare preference in its own register. What escaped into every arm instead was background knowledge about external systems: a library's behaviour across versions, what an upstream feed re-serves, whether a live database exists -- none of it flagged by the handover. Hypothesis: a stated gap makes 'unknown' the stated answer rather than restraint, and a premise the agent brought with it never presents as a claim at all. A fixture that can fire a claim-handling line has to make one UNFLAGGED external premise load-bearing.
<!-- tags: prompt-tests, test-design, writing-for-agents | created: 2026-09-22 -->

### mem-1790065267-fe47
> A round's own read of its deciding criterion is not reliable enough to decide it. Iteration 17 read two compressed runbooks for claims their source does not make, found one and missed two -- including the one in the arm it would otherwise have kept, which reversed the outcome. A single reader given the artifacts relabelled and the criterion, told neither what is under test nor which arm is which, found all three. Hypothesis: the round holds a prior about which arm should look better and reads the arm it expects to be clean less adversarially; a reader with no prior has nothing to protect. Make the blind read the result, not a check on a result already written.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

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

### mem-1790069038-9779
> A diff staged for a blind reader leaks the case name: 'diff -u' writes the fixture's absolute path into its own header, so prompt-tests/general/<case>/fixture/... appears in the first two lines of every staged diff. Caught before dispatch by grepping the staged tree for the case name; fix is 'diff -u --label before/<f> --label after/<f>'. Same class as a probe directory sharing a word with its fixture, on the grader side instead of the tested agent's. Grep the staged tree for the case name and for 'prompt-test' before every blind dispatch.
<!-- tags: prompt-tests, contamination | created: 2026-09-22 -->

### mem-1790067347-89d7
> A probe directory sharing a word with its own fixture is found by the tested agent's ordinary search. An arm looking for the git history of a pinned dependency ran a bounded find for the fixture's project name, hit prompt-tests/runs/<that-name>, listed it, and named it in its own required notes -- contamination, whatever it then declined to read. Name a case or probe directory after the task using words that appear in neither its task.md nor its fixture/.
<!-- tags: prompt-tests, contamination | created: 2026-09-22 -->

### mem-1790061592-858f
> A session-analysis subagent dispatch can die instantly with 'safeguards flagged this message ... Details: [reasoning_extraction]' - twice on one transcript while an identical brief on a sibling transcript succeeded, so it is content-dependent and retrying the same dispatch does not help. Substitute: python over the .jsonl emitting only assistant 'thinking' and 'text' blocks. A 74-line, 330KB transcript yields 9KB, which is cheaper than the artifact and uniform across arms.
<!-- tags: prompt-tests, session-analysis, tooling | created: 2026-09-22 -->

## Context

# Memories

## Patterns

### mem-1790304142-7900
> A durable file an agent-maintained loop must write to grows without bound unless its SHAPE is tied to something already bounded. Two that work here: a case is kept only while a retirement condition in sys_prompt/CLAUDE.md names it (one grep); sys_prompt/CLAUDE.md is one paragraph per prompt line plus one ledger row per dead wording (40). Neither sets a size. The growth they stop: each round's addition is locally justified by a small saving to the next round and nothing prices the sum, and relocating text to a 'durable home' is growth, not a cut. That file went 3,872 -> 8,393 words over 39 rounds, 2.9x the prompt it justifies, and attaches in FULL to any session that opens a file in its directory with the Read tool.
<!-- tags: docs-growth, sys-prompt, writing-for-agents | created: 2026-09-25 -->

### mem-1790304132-4745
> Status claims -- 'open candidate', 'untouched', 'nobody has measured yet' -- go stale silently in an agent-maintained document: the next round falsifies one and nothing re-reads it. Two instances, four rounds each: one wording filed as the open candidate in one section of sys_prompt/CLAUDE.md and as decided-not-shipped three sections earlier; an (instruction) carrying 'still untouched after 39 rounds' for work round 35 finished. A pointer check (does this path exist) does not catch them. Write the observation, not the state of the ledger.
<!-- tags: docs-errors, writing-for-agents | created: 2026-09-25 -->

### mem-1790304125-6900
> The live doc-error target: an agent asked to document a change writes ONE instance as a PROJECT-WIDE RULE, and the rule's scope is the half no observation constrained, so the error lands in the generalisation while the volume barely moves. That is why every say-less wording that measured VOLUME found nothing. sys_prompt/CLAUDE.md's **Force** paragraph already says scope is a claim and has only ever addressed whoever edits the prompt; the property-shaped wording for agents was run at 36 and did nothing. Its own hypothesis names the act that would work -- looking at the second case.
<!-- tags: docs-errors, docs-growth, sys-prompt | created: 2026-09-25 -->

### mem-1790304103-d0e8
> Instrument rules for these probes. (1) Hold investigation depth fixed by STATING the load-bearing fact in the fixture, as already verified, in the file the task sends the agent to, and make the natural implementation trip over it -- prose is emitted about what was discovered, so an arm that investigates more writes more whatever the prompt says. Same trick gives a defect a TRIGGER: put the symptom in the build's own stdout or neither arm sees it. (2) A null has three causes, not two: the fixture made the answer the stated one; the agent GOES AND SETTLES the premise so a marking line has nothing to buy; or the behaviour was never triggered and no arm was in a position to exhibit it. The third looks exactly like saturation in the artifacts and is visible only in the transcript. Read the transcript for the trigger, not the artifact.
<!-- tags: prompt-tests, test-design | created: 2026-09-25 -->

### mem-1790301452-7f2d
> Editing a sentence is not checking it: a repair is scoped to the clause the change falsified, and the rest of the sentence is invisible even while being retyped. Measured arm-independent -- both arms rewrote the falsified half of a usage line and neither ran the form they left standing, which was already a usage error against the real parser.
<!-- tags: docs-errors, writing-for-agents | created: 2026-09-25 -->

### mem-1790300415-fd60
> A defect found outside the task reaches an explicit fork and the agent takes the reporting branch on SCOPE -- not on oversight and not on any documentation rule, in both arms' own words. Nothing in `# Writing for other agents` reaches it; what licenses the stop is `# Completeness`, whose rule covers every SCOPED item and offers escalation as the out. Reporting is saturated; the lever is the fix, which the owner settled (#104: 'to report to me it still have to do the work of understanding how it works. i have one sensible option which is for this to get fixed'). Shipped at 38, harm case run at 39; claim, costs and retirement condition in sys_prompt/CLAUDE.md.
> What 39 adds: **what a session escalates, it also cements.** The arm that escalated a documented contradiction wrote two tests asserting the defective behaviour in the same delivery, so accepting the fix it recommended fails its own suite -- unsaid. A report and the code are not the same durable object: the reply evaporates, the test stays. Hypothesis: escalation settles the question for the rest of the session, and a clause about what to report reaches none of the writing that follows.
<!-- tags: sys-prompt, docs-growth, writing-for-agents | created: 2026-09-25 -->

## Decisions

## Fixes

## Context

### mem-1790299660-0a19
> The owner's own diagnosis of unwanted documentation, from their specimen e828eab7 (#78/#81/#91). The additions 'dont belong', 'does not actually solve the problem', 'introduced new problems that have no solution (who will actually solve the problem?)'; 'not incorrect but fairly expensive to cleanup, and likely will only be cleaned if i ordered one ... added becuase "it looks like it only helps", and a research is actually MUCH CHEAPER but was considered more expensive here'. The mechanism (#91): a shorter row 'works too', the detailed one 'saves investigation speed when update next runs' -- BUT 'if every session says "adding this will save a little bit of time", thats how you get unbounded doc growth that ends up costing a lot more tokens'. So the driver is not a bad judgement in any one session: each addition is locally justified by a small expected saving and nothing prices the aggregate. A candidate aimed at growth has to reach that pricing, not the local judgement. Also settled: the loop must NOT merge this branch -- 'i may choose to merge myself, but you shoudl not do that.'
<!-- tags: sys-prompt, docs-growth, owner | created: 2026-09-25 -->

### mem-1790273746-2aa1
> A specimen session on this machine did NOT run this branch's prompt. `/repos/claude-config` -- the installed checkout every ordinary session loads via claude.sh -- still carries the pre-round-11 block (Omit by default / Claim less) and the docs order at :15, and writing-for-agents2 has never been merged, so every round's edits reach only the prompt-test harness. Verified from e828eab7's own prompt_snapshot attachments. Before treating any real session here as evidence about a prompt line, grep that session's prompt_snapshot for the line.
<!-- tags: sys-prompt, prompt-tests, evidence | created: 2026-09-24 -->

# Memories

## Patterns

### mem-1790301452-7f2d
> Editing a sentence is not checking it: a repair is scoped to the clause the change falsified, and the rest of the sentence is invisible even while being retyped. Measured arm-independent -- both arms rewrote the falsified half of a usage line and neither ran the form they left standing, which was already a usage error against the real parser.
<!-- tags: docs-errors, writing-for-agents | created: 2026-09-25 -->

### mem-1790300415-fd60
> A defect found outside the task reaches an explicit fork and the agent takes the reporting branch on SCOPE -- not on oversight, and not on any documentation rule. Both arms of iter38's ablation reasoned it in those words ('outside my current scope but worth flagging in notes rather than fixing'; 'should I fix it or just report it?'; 'touches every rendered page's output, so rather than bundling a fix into this change, I should flag it clearly'), then named the one-line fix in the reply and left the code alone. Arm-independent across the # Writing for other agents ablation, so nothing in that block reaches it; what licenses the stop is # Completeness, whose rule covers every SCOPED item and offers escalation as the out. The owner's specimen e828eab7 DID raise its defect -- headed paragraph, probe table, and a Required-notes line offering the revert -- so 'it never gets raised' (#102) is false for it; what is missing is that the one-line fix is never named as an option, so the only thing the human can act on is accept-or-revert a doc row. Their #104 closes it: 'to report to me it still have to do the work of understanding how it works. i have one sensible option which is for this to get fixed.' So reporting is saturated and the lever is the fix. Shipped at 38 under # Completeness; costs and retirement condition in sys_prompt/CLAUDE.md.
<!-- tags: sys-prompt, docs-growth, writing-for-agents | created: 2026-09-25 -->

### mem-1790300347-57ef
> Hold investigation depth fixed by STATING the load-bearing fact in the fixture, as already verified, in the file the task sends the agent to, and make the natural implementation trip over it. Prose is emitted about what was discovered, so an arm that investigates more writes more whatever the prompt says -- the confound that blocked iteration 29. The same trick is how you give a defect a TRIGGER: iter38 had to put the symptom in the build's own stdout before either arm saw it at all.
<!-- tags: prompt-tests, test-design | created: 2026-09-25 -->

### mem-1790299418-0a88
> What a compression rule cuts first is the qualifying clause, and the qualifying clause is what made the claim true. Measured twice on one say-less wording: the treated arm wrote a third to a seventh of the bare arm's unfalsified prose and in BOTH draws shipped exactly one sentence false against its own delivered code, where the bare arm shipped none. Read every treated tree for claims false against its own code before crediting a volume win.
<!-- tags: sys-prompt, docs-growth, docs-errors | created: 2026-09-25 -->

### mem-1790299401-5843
> A null has three causes, not two, and they license different conclusions. (1) The fixture made the answer the stated one. (2) The agent GOES AND SETTLES the premise -- starts a database, runs a probe -- so a marking line has nothing to buy even in principle. (3) The behaviour was never triggered: no arm was in a position to exhibit it. Cause 3 looks exactly like saturation in the artifacts and is only visible in the transcript -- iter38 run 1 read two arms as agreeing about a defect neither had ever seen, because verification there was file identity and mtime and no rendered page's bytes were ever on screen. Check which cause you have by reading the transcript for the trigger, not the artifact.
<!-- tags: prompt-tests, test-design | created: 2026-09-25 -->

### mem-1790275989-2871
> An agent asked to document a change writes ONE instance as a PROJECT-WIDE RULE, and the rule's scope is the half no observation constrained -- so the doc error lands in the generalisation while the volume barely moves. Measured at iter35 on three legs of one fixture: each added 2-5 binding sentences to the document the task named, and two of three generalisations were false against their own tree (a matching cadence asserted, and tested, to guarantee a matching run_date that is a pinned variable; a naming scheme the config violates). The leg that stayed on the instance shipped nothing false and a blind reader chose it to inherit. This is why every say-less wording that measured VOLUME found nothing: volume is not where the error is. sys_prompt/CLAUDE.md's **Force** paragraph already says scope is a claim, and has only ever addressed whoever edits the prompt.
<!-- tags: sys-prompt, docs-growth, docs-errors | created: 2026-09-24 -->

## Decisions

## Fixes

## Context

### mem-1790299660-0a19
> The owner's own diagnosis of unwanted documentation, from their specimen e828eab7 (#78/#81/#91). The additions 'dont make sense' -- they 'dont belong', 'does not actually solve the problem', and 'introduced new problems that have no solution (who will actually solve the problem?)'; 'the calibration is poor ... not incorrect but fairly expensive to cleanup, and likely will only be cleaned if i ordered one. my guess is that its added becuase "it looks like it only helps", and a reserach is actuall MUCH CHEAPER but was considered more expensive here'. Their four alternatives: find a flag; remove the $1 from the helper; note it in the skill header where the invoker reads it; put the general gotcha in the root index. On the mechanism (#91): a shorter row 'works too', the detailed one 'saves investigation speed when update next runs' -- BUT 'if every session says "adding this will save a little bit of time", thats how you get unbounded doc growth that ends up costing a lot more tokens'. So the driver is not a bad judgement in any one session; each addition is locally justified by a small expected saving and nothing prices the aggregate. Any candidate aimed at growth has to reach that pricing, not the local judgement. Also settled: the loop must NOT merge this branch -- 'i may choose to merge myself, but you shoudl not do that.'
<!-- tags: sys-prompt, docs-growth, owner | created: 2026-09-25 -->

### mem-1790273746-2aa1
> A specimen session on this machine did NOT run this branch's prompt. /repos/claude-config -- the installed checkout every ordinary session loads via claude.sh -- still carries the pre-round-11 '# Writing for other agents' block (Omit by default / Claim less) and the docs order at :15; writing-for-agents2 has never been merged, so 28 rounds of edits reach only the prompt-test harness. Verified by pulling the prompt_snapshot attachments out of e828eab7's own JSONL and grepping them. Consequence: the owner's specimen is evidence about the DELETED say-less bullets (one was in the prompt while the session wrote four durable additions anyway), not about the live block -- 'Say what ends it' and the self-consequence bullet were both absent from it. Before treating any real session here as evidence about a prompt line, grep that session's prompt_snapshot for the line.
<!-- tags: sys-prompt, prompt-tests, evidence | created: 2026-09-24 -->

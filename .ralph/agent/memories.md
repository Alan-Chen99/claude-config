# Memories

## Patterns

### mem-1790273752-26cf
> The owner's own account of why unwanted documentation gets written is a two-sided mispricing, not volume: 'the calibration is poor ... not incorrect but fairly expensive to cleanup, and likely will only be cleaned if i ordered one. my guess is that its added because "it looks like it only helps". and a research is actually MUCH CHEAPER but was considered more expensive here.' Side one -- a durable note is priced at zero because it only helps -- is what the shipped 'Say what ends it' already prices, and that line was absent from the specimen, so it is untested against this failure rather than refuted. Side two -- finding out is priced above writing it down, and is in fact cheaper -- is priced by nothing in either prompt version. The owner also said the volunteered inventory row (addition 4) was fine, just shorter and more general, so the class to reduce is the poorly-calibrated note, not the volunteered fact.
<!-- tags: sys-prompt, docs-growth, writing-for-agents | created: 2026-09-24 -->

### mem-1790530000-8b7e
> The owner's objection to over-documentation is NOT volume. Asked which of the four durable additions in their own specimen (e828eab7) they did not want, they said the changes "dont make sense": they "dont belong", "does not actually solve the problem", and "introduced new problems that have no solution (who will actually solve the problem?)". Their four sensible alternatives were a fix instead of a note (remove the literal $1; find a flag), a note in the skill header where the invoker reads it, and a general gotcha in the root index. So the lever is PLACEMENT, documentation-in-place-of-a-fix, and obligations recorded with no owner -- not how many lines. A wording that only cuts volume does not reach any of the three, whatever it measures.
<!-- tags: sys-prompt, docs-growth, writing-for-agents | created: 2026-09-24 -->

### mem-1790530000-3f52
> A say-less wording buys volume and pays in scope qualifiers. Measured twice, two fixtures, one wording (*a change owes documentation only where it made a document false; what it could newly explain, it does not owe*): the treated arm wrote a third to a seventh of the bare arm's unfalsified prose, and in BOTH draws shipped exactly one sentence false against its own delivered code where the bare arm shipped none -- a cost claim missing the "write" qualifier, and a failure mode claimed to cover a case the code leaves invisible. Why: what a compression rule cuts first is the qualifying clause, and a qualifying clause is what made the claim true. Read every treated tree for claims false against its own code before crediting a volume win.
<!-- tags: sys-prompt, docs-growth, docs-errors | created: 2026-09-24 -->

### mem-1790241731-77bc
> Document volume is one fact replicated, not many claims: under fixed depth one established fact reached 3-4 lasting files in BOTH arms, none wrong, none removable without a human. An agent does pose the second home as a choice and then take it -- 'it deserves a place among the conventions too, even though it's already noted in docs/layout.md' -- so 'already written down somewhere' is available as a reason and loses.
<!-- tags: sys-prompt, docs-growth | created: 2026-09-24 -->

### mem-1790442000-31ac
> Hold investigation depth fixed by STATING the load-bearing fact in the fixture, as already verified, in the file the task sends the agent to -- and make the natural implementation the one that trips over it. Two arms then ran 13 tool calls each and both met the trap, so document volume could be read without riding on how much each arm found out. This is the fix for the confound that blocked iteration 29: prose is emitted about what was discovered, so an arm that investigates more writes more whatever the prompt says.
<!-- tags: prompt-tests, test-design, docs-growth | created: 2026-09-24 -->

### mem-1790239111-9bed
> Editing a sentence is not checking it. Both arms rewrote the half of 'Every command takes --store <path>, defaulting to ./sample-store.json' their change falsified, and neither ran the documented form, which is a usage error because --store sits on the top-level parser. Arm-independent. Why: a repair is scoped to the clause the change falsified, and the rest of the sentence it stands in is invisible even while being retyped.
<!-- tags: docs-errors, writing-for-agents | created: 2026-09-24 -->

### mem-1790070627-b0f9
> A saturated baseline has two very different causes and they license different conclusions. Cause one: the fixture made the answer the stated one. Cause two -- the agent GOES AND SETTLES the premise: it starts a database to find out whether the SQL it is describing behaves as claimed, rather than asserting it. Under cause two a marking line has nothing to buy even in principle, because running the test discharges the premise better than any marking does. Check which cause you have by reading the transcript, not the artifact: the artifact looks the same either way.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790400000-22a1
> A real session log is admissible where a fixture is not, and a round that cites one without reading it has looked at nothing. Sessions are at ~/.claude/projects/<slug>/<id>.jsonl; dispatch session-analysis in evidence mode. Use a log to FIND the mechanism, a fixture to measure a wording against it.
<!-- tags: prompt-tests, test-design, session-analysis | created: 2026-09-24 -->

## Decisions

## Fixes

## Context

### mem-1790273746-2aa1
> A specimen session on this machine did NOT run this branch's prompt. /repos/claude-config -- the installed checkout every ordinary session loads via claude.sh -- still carries the pre-round-11 '# Writing for other agents' block (Omit by default / Claim less) and the docs order at :15; writing-for-agents2 has never been merged, so 28 rounds of edits reach only the prompt-test harness. Verified by pulling the prompt_snapshot attachments out of e828eab7's own JSONL and grepping them. Consequence: the owner's specimen is evidence about the DELETED say-less bullets (one was in the prompt while the session wrote four durable additions anyway), not about the live block -- 'Say what ends it' and the self-consequence bullet were both absent from it. Before treating any real session here as evidence about a prompt line, grep that session's prompt_snapshot for the line.
<!-- tags: sys-prompt, prompt-tests, evidence | created: 2026-09-24 -->

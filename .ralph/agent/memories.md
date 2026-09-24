# Memories

## Patterns

### mem-1790230469-4206
> A prompt line is applied by the position a sentence would take, not by the antecedent the line names. A bullet whose subject is 'a consequence of your own change' was quoted by an arm's own reasoning -- 'per the guidance, a consequence of my own change isn't something I should record as an invariant' -- to decline recording a property that PREDATED the session, which the bullet does not cover. The untreated arm wrote that rule and a blind reader chose its tree on that one sentence. When a line names a class of fact but its remedy is a placement, expect it to reach every fact that would take that placement.
<!-- tags: sys-prompt, writing-for-agents, prompt-tests | created: 2026-09-24 -->

### mem-1790230469-2c9a
> Where an agent files a fact is decided by what the tree gives that fact a home for, not by whether the agent made the fact itself. Measured three times: where the self-made fact had a required home (a CLAUDE.md saying every flag has a README row), the untreated arm filed it there and put its INHERITED finding under the soliciting heading instead -- the reverse of the two earlier genres, where the self-made fact had no required home and took the heading. Hypothesis: a soliciting heading collects whatever the tree houses nowhere. The lever on documentation growth is therefore a required home for each kind of fact, not an instruction to write less.
<!-- tags: sys-prompt, writing-for-agents, docs | created: 2026-09-24 -->

### mem-1790229298-14d0
> For a decisive blind reading, brief the reader with a neutral inventory rather than the opportunities under test: 'every statement about the project's behaviour present in the delivered tree or the final reply and absent from the starting tree -- where it landed, whom it addresses, whether the session made or inherited the fact, what would falsify it', plus which tree it would rather inherit. The reader builds the categorical grid itself, cannot tell what is being measured, and reports things the round did not pre-register.
<!-- tags: prompt-tests, test-design | created: 2026-09-24 -->

### mem-1790229298-fdae
> Before crediting a cost you saw in a treated arm, check the fixture's own pre-existing code for it. One probe's existing option had no argparse metavar and no help while the fixture's docs spelled the value out, so the arms that omitted metavar on the NEW flag matched the only neighbour they had -- and the round that read that as a defect the line introduced blocked a ship on the fixture's house style, with no run needed to see it. The baseline that spans the outcome range can be the starting tree, not only the untreated arm.
<!-- tags: prompt-tests, test-design | created: 2026-09-24 -->

### mem-1790052470-9c1e
> A downstream reader does NOT stabilise an unstable baseline. It is a second stochastic session run against the first session's artifact, and the tested agent never sees it, so nothing about the tested agent becomes more determinate - it converts a spread in wording into a spread in reader behaviour. Use it for what it actually buys: turning 'does this sentence mislead' from the grader's opinion into an observation. To make a run readable at n=1, instrument the FIXTURE with several opportunities for the behaviour that differ in character, and read the line the agent drew between them.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790070627-b0f9
> A saturated baseline has two very different causes and they license different conclusions. Cause one: the fixture made the answer the stated one. Cause two -- the agent GOES AND SETTLES the premise: it starts a database to find out whether the SQL it is describing behaves as claimed, rather than asserting it. Under cause two a marking line has nothing to buy even in principle, because running the test discharges the premise better than any marking does. Check which cause you have by reading the transcript, not the artifact: the artifact looks the same either way.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790400000-22a1
> A real session log is admissible evidence where a fixture is not, and this loop ignored them for 21 rounds. Every session on this machine is at ~/.claude/projects/<slug>/<id>.jsonl; the cheap read is python over the JSONL emitting only assistant thinking/text blocks plus tool-call headers (a 790KB log yields ~8k tokens). A fixture shows what a wording does to a situation the round invented; a log shows which situations actually arise and what the agent said while deciding. Use a log to FIND the mechanism, a fixture to measure a wording against it.
<!-- tags: prompt-tests, test-design, session-analysis | created: 2026-09-24 -->

## Decisions

## Fixes

### mem-1790061592-858f
> A session-analysis subagent dispatch can die instantly with 'safeguards flagged this message ... Details: [reasoning_extraction]' - twice on one transcript while an identical brief on a sibling transcript succeeded, so it is content-dependent and retrying the same dispatch does not help. Substitute: python over the .jsonl emitting only assistant 'thinking' and 'text' blocks. Re-hit 2026-09-24 on a first dispatch; the substitute worked immediately.
<!-- tags: prompt-tests, session-analysis, tooling | created: 2026-09-22 -->

## Context

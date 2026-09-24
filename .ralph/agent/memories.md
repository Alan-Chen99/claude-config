# Memories

## Patterns

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

### mem-1790400600-22b2
> Where an agent puts a fact is decided by whether the fact is one it made itself. A defect it INHERITED goes into the reply -- a response template with a notes section is already the slot -- and a prompt line telling it to fix rather than record such a thing buys nothing, measured across four inherited defects differing in who may fix them. A consequence of the agent's OWN change has no slot, so a heading reading "add to the list when you find another" supplies one, and the entry lands in a file the task never named, written as a property of the project though it is false the moment the code changes. Hypothesis: writing is routed by where a fact fits.
<!-- tags: sys-prompt, writing-for-agents, docs | created: 2026-09-24 -->

### mem-1790400700-22c3
> A prompt line that suppresses unrequested documentation can suppress the requested kind with it, and the tell is not in the documents it stops writing. Two wordings of one claim, sharing no vocabulary, each moved a self-made fact out of a conventions file and into the change's own docs as intended -- and each also omitted argparse's metavar, shipping a usage line its own --help contradicts, where both untreated arms matched. Read the program's user-facing surface, not only the prose, before crediting a line that reduces prose.
<!-- tags: sys-prompt, prompt-tests, test-design | created: 2026-09-24 -->

## Fixes

### mem-1790061592-858f
> A session-analysis subagent dispatch can die instantly with 'safeguards flagged this message ... Details: [reasoning_extraction]' - twice on one transcript while an identical brief on a sibling transcript succeeded, so it is content-dependent and retrying the same dispatch does not help. Substitute: python over the .jsonl emitting only assistant 'thinking' and 'text' blocks. Re-hit 2026-09-24 on a first dispatch; the substitute worked immediately.
<!-- tags: prompt-tests, session-analysis, tooling | created: 2026-09-22 -->


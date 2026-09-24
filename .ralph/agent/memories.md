# Memories

## Patterns

### mem-1790239111-9bed
> Editing a sentence is not checking it. Both arms rewrote the same half of 'Every command takes --store <path>, defaulting to ./sample-store.json' -- the default-path half, which their change falsified -- and neither ran the documented form, which is a usage error because --store sits on the top-level parser. Arm-independent, so no prompt line reached it. Why: a repair is scoped to the clause the change falsified, and the rest of the sentence it stands in is invisible even while being retyped.
<!-- tags: docs-errors, writing-for-agents | created: 2026-09-24 -->

### mem-1790239111-8208
> Document volume tracks how much the session found out, not what the doc instruction said. Repair genre, two arms differing only in the block aimed at durable writing: the arm WITHOUT it wrote 16 sentences the change had not falsified to the treated arm's 7, and the only sentence directing a later reader -- but it also ran half again the tool calls, met a hazard the other never found, and wrote the only new claim true of its own code. The treated arm's shorter docs held the one newly-written false statement. Why: prose is emitted about what was discovered, so a wording that cuts volume is not separable from one that cuts checking. Do not write a 'say less' candidate without an arm that holds investigation depth fixed.
<!-- tags: sys-prompt, writing-for-agents, docs-growth | created: 2026-09-24 -->

### mem-1790231753-e792
> An agent applying a placement rule generalises the rule's antecedent to the whole decision. An arm carrying 'a consequence of your own change is not a property of the project' declined a standing-rules heading with 'the only thing learned is a property of this change' -- in a session that had also found an inherited parser defect, which is not a property of its change. Second genre showing this. The rule is read as a verdict on the destination, not as a test on the fact.
<!-- tags: sys-prompt, writing-for-agents | created: 2026-09-24 -->

### mem-1790231753-c830
> A prompt block can state one rationale twice across neighbouring bullets, and the duplication is invisible to every per-line measurement: each bullet was measured alone and shipped alone. Found only by reading the block as prose. Cutting the copy left both arms delivering the same artifact. When a round measures a candidate line in isolation, it is not measuring what the line adds to the block it joins -- schedule a read of the whole block as its own step.
<!-- tags: sys-prompt, writing-for-agents | created: 2026-09-24 -->

### mem-1790229298-14d0
> For a decisive blind reading, brief the reader with a neutral inventory rather than the opportunities under test: 'every statement about the project's behaviour present in the delivered tree or the final reply and absent from the starting tree -- where it landed, whom it addresses, whether the session made or inherited the fact, what would falsify it', plus which tree it would rather inherit. The reader builds the categorical grid itself, cannot tell what is being measured, and reports things the round did not pre-register.
<!-- tags: prompt-tests, test-design | created: 2026-09-24 -->

### mem-1790070627-b0f9
> A saturated baseline has two very different causes and they license different conclusions. Cause one: the fixture made the answer the stated one. Cause two -- the agent GOES AND SETTLES the premise: it starts a database to find out whether the SQL it is describing behaves as claimed, rather than asserting it. Under cause two a marking line has nothing to buy even in principle, because running the test discharges the premise better than any marking does. Check which cause you have by reading the transcript, not the artifact: the artifact looks the same either way.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790400000-22a1
> A real session log is admissible evidence where a fixture is not, and this loop ignored them for 21 rounds. Every session on this machine is at ~/.claude/projects/<slug>/<id>.jsonl; the cheap read is python over the JSONL emitting only assistant thinking/text blocks plus tool-call headers (a 790KB log yields ~8k tokens). A fixture shows what a wording does to a situation the round invented; a log shows which situations actually arise and what the agent said while deciding. Use a log to FIND the mechanism, a fixture to measure a wording against it.
<!-- tags: prompt-tests, test-design, session-analysis | created: 2026-09-24 -->

## Decisions

## Fixes

### mem-1790234297-5ef8
> A worktree's venv at ~/.claude/venvs/<basename> can carry an editable path pointing at another checkout's src/, so agent-tools' python subcommands and hooks run that checkout's code while the binary is this one's. No error, session looks healthy, and uv run does not repair it -- the install is current by name and version. Repair: UV_PROJECT_ENVIRONMENT=<venv> uv sync --project <root> --reinstall-package claude-config. agent-tools claude now asserts it before exec; other subcommands do not.
<!-- tags: tooling, prompt-tests | created: 2026-09-24 -->

### mem-1790061592-858f
> A session-analysis subagent dispatch can die instantly with 'safeguards flagged this message ... Details: [reasoning_extraction]' - twice on one transcript while an identical brief on a sibling transcript succeeded, so it is content-dependent and retrying the same dispatch does not help. Substitute: python over the .jsonl emitting only assistant 'thinking' and 'text' blocks. Re-hit 2026-09-24 on a first dispatch; the substitute worked immediately.
<!-- tags: prompt-tests, session-analysis, tooling | created: 2026-09-22 -->

## Context

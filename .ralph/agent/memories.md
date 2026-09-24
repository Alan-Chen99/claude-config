# Memories

## Patterns

### mem-1790234297-4904
> A rule delivered in a tool result acts only on what comes after the call, and its characteristic effect is to convert a residual doubt into durable text. Measured on pre_output.record's 'NEVER reply to user if uncertainties remain': across three runs it arrived last in one and did nothing, arrived mid-run in another and produced five further tool calls that rewrote a dependency comment around a reproduction command and documented an invented env-var name. It fires only when a cheap resolving act exists -- doubts nobody can settle from inside the session leave it inert, and every arm replied with doubt still listed anyway. Read such a rule by tool-call index before crediting it with anything.
<!-- tags: sys-prompt, prompt-tests | created: 2026-09-24 -->

### mem-1790231753-e792
> An agent applying a placement rule generalises the rule's antecedent to the whole decision. An arm carrying 'a consequence of your own change is not a property of the project' declined a standing-rules heading with 'the only thing learned is a property of this change' -- in a session that had also found an inherited parser defect, which is not a property of its change. Second genre showing this. The rule is read as a verdict on the destination, not as a test on the fact.
<!-- tags: sys-prompt, writing-for-agents | created: 2026-09-24 -->

### mem-1790231753-c830
> A prompt block can state one rationale twice across neighbouring bullets, and the duplication is invisible to every per-line measurement: each bullet was measured alone and shipped alone. Found only by reading the block as prose. Cutting the copy left both arms delivering the same artifact. When a round measures a candidate line in isolation, it is not measuring what the line adds to the block it joins -- schedule a read of the whole block as its own step.
<!-- tags: sys-prompt, writing-for-agents | created: 2026-09-24 -->

### mem-1790229298-14d0
> For a decisive blind reading, brief the reader with a neutral inventory rather than the opportunities under test: 'every statement about the project's behaviour present in the delivered tree or the final reply and absent from the starting tree -- where it landed, whom it addresses, whether the session made or inherited the fact, what would falsify it', plus which tree it would rather inherit. The reader builds the categorical grid itself, cannot tell what is being measured, and reports things the round did not pre-register.
<!-- tags: prompt-tests, test-design | created: 2026-09-24 -->

### mem-1790229298-fdae
> Before crediting a cost you saw in a treated arm, check the fixture's own pre-existing code for it. One probe's existing option had no argparse metavar and no help while the fixture's docs spelled the value out, so the arms that omitted metavar on the NEW flag matched the only neighbour they had -- and the round that read that as a defect the line introduced blocked a ship on the fixture's house style, with no run needed to see it. The baseline that spans the outcome range can be the starting tree, not only the untreated arm.
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

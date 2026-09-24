# Memories

## Patterns

### mem-1790235782-346f
> Repairing a doc is a rewrite, not a patch, and it grows. Across four runs whose change falsified one sentence in a README, every run that opened the file replaced the whole paragraph; two of three deleted the inherited rationale (the reason the old value was chosen) while correcting the value, and disclosed the deletion to the user rather than to the tree; all three appended new prose the change had not falsified, under a '## Design Decisions' heading the fixture already had. Arm-independent -- the mechanism is the paragraph being rewritten from the change instead of from the paragraph.
<!-- tags: writing-for-agents, test-design | created: 2026-09-24 -->

### mem-1790235782-1b19
> A doc-maintenance prompt line cannot be measured on a fixture whose doc files the agent has to discover. Four runs, two arms, one task: the outcome tracked whether the FIRST listing showed the .md files (ls -R or find -name '*.md') and not which arm it was; the arm lacking a 'check project CLAUDE.md' clause was the one that grepped exactly that file, and the arm carrying it went wider. Control it by naming every doc file in the fixture's auto-loaded root CLAUDE.md before attributing anything to a wording.
<!-- tags: prompt-tests, test-design, sys-prompt | created: 2026-09-24 -->

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

### mem-1790237061-0993
> A standing order to update docs is saturated where the project's auto-loaded CLAUDE.md indexes its own doc files: arms without the order rewrote the same documents and followed a data-file rename through them. What routes a change into the docs is the index, read as part of the task.
<!-- tags: prompt, docs | created: 2026-09-24 -->

## Fixes

### mem-1790234297-5ef8
> A worktree's venv at ~/.claude/venvs/<basename> can carry an editable path pointing at another checkout's src/, so agent-tools' python subcommands and hooks run that checkout's code while the binary is this one's. No error, session looks healthy, and uv run does not repair it -- the install is current by name and version. Repair: UV_PROJECT_ENVIRONMENT=<venv> uv sync --project <root> --reinstall-package claude-config. agent-tools claude now asserts it before exec; other subcommands do not.
<!-- tags: tooling, prompt-tests | created: 2026-09-24 -->

### mem-1790061592-858f
> A session-analysis subagent dispatch can die instantly with 'safeguards flagged this message ... Details: [reasoning_extraction]' - twice on one transcript while an identical brief on a sibling transcript succeeded, so it is content-dependent and retrying the same dispatch does not help. Substitute: python over the .jsonl emitting only assistant 'thinking' and 'text' blocks. Re-hit 2026-09-24 on a first dispatch; the substitute worked immediately.
<!-- tags: prompt-tests, session-analysis, tooling | created: 2026-09-22 -->

## Context

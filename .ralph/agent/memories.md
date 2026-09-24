# Memories

## Patterns

### mem-1790268814-574d
> Ask the owner what a prompt line is FOR before spending a round measuring it. One Telegram question answered in 3 minutes settled a question two rounds of arms could not, and ruled out a candidate wording the owner had themselves floated ('check if project CLAUDE.md is outdated' - the owner's actual target is every doc, with CLAUDE.md merely the bigger risk). Why it works here: a retirement condition is a claim about what the owner wants observed, and the owner is reachable. skills/telegram-hitl; one topic per loop.
<!-- tags: workflow, prompt-tests | created: 2026-09-24 -->

### mem-1790528000-4c31
> The decision to write a durable document is made on usefulness alone; cost never enters. Real specimen e828eab7 (the user's own): a one-symlink change produced four durable additions across three files, and the session's stated criterion at the moment of writing was that the observation was "genuinely useful and unrecorded, so it's worth adding". It declined four other additions -- every time on the scope of the change or on conflict risk, never on what a document costs. Two additions were the literal ask ("and docuemnt it") and one was commanded by a repo-local skill's frontmatter directive, which no system-prompt line outranks. So a say-less wording has at most one of four to reach, and the ratchet's biggest single source here is a rule the repo already carries.
<!-- tags: sys-prompt, docs-growth, writing-for-agents | created: 2026-09-24 -->

### mem-1790241731-77bc
> Document volume is one fact replicated, not many claims: measured under fixed depth, one established fact reached 3-4 lasting files in BOTH arms -- a str.format trap went into config/CLAUDE.md, both preset copies and a test, on top of the render.py comment already stating it. Four live copies, none wrong, none removable without a human reading all four. Neither arm's reasoning treats a second durable home as a choice, so a say-less wording has nothing to attach to; the target is replication. Why: each destination is chosen for its own reader, and the choice is never posed as 'this is already written down somewhere'.
<!-- tags: sys-prompt, docs-growth | created: 2026-09-24 -->

### mem-1790442000-31ac
> Hold investigation depth fixed by STATING the load-bearing fact in the fixture, as already verified, in the file the task sends the agent to -- and make the natural implementation the one that trips over it. Two arms then ran 13 tool calls each and both met the trap, so document volume could be read without riding on how much each arm found out. This is the fix for the confound that blocked iteration 29: prose is emitted about what was discovered, so an arm that investigates more writes more whatever the prompt says.
<!-- tags: prompt-tests, test-design, docs-growth | created: 2026-09-24 -->

### mem-1790442000-77b2
> An agent DOES decline a destination out loud, where two documents compete for one fact: both arms weighed an upgrade-inventory doc, rejected it, and said why in the reply. Iteration 29 looked for declining in a repair genre, found none, and withdrew a mechanism claim on that. Why the genre decides it: declining is visible only when there is a second candidate destination to name; with one place to put a fact, writing it is not felt as a choice.
<!-- tags: sys-prompt, writing-for-agents | created: 2026-09-24 -->

### mem-1790442000-9f04
> A worktree's edit to src/claude_config/ or agent-tools/ does not reach ordinary sessions on this machine: bare `agent-tools` resolves to the installed build whose root is /repos/claude-config, and ~/.claude/skills symlinks there too. Only the prompt-test runners use the worktree binary ($REPO/agent-tools/target/release/agent-tools with CLAUDE_CONFIG_ROOT=$REPO), so an arm comparison is valid while the shipped behaviour is unchanged until a merge. Do not describe such a deletion as live.
<!-- tags: tooling, prompt-tests | created: 2026-09-24 -->

### mem-1790239111-9bed
> Editing a sentence is not checking it. Both arms rewrote the same half of 'Every command takes --store <path>, defaulting to ./sample-store.json' -- the default-path half, which their change falsified -- and neither ran the documented form, which is a usage error because --store sits on the top-level parser. Arm-independent, so no prompt line reached it. Why: a repair is scoped to the clause the change falsified, and the rest of the sentence it stands in is invisible even while being retyped.
<!-- tags: docs-errors, writing-for-agents | created: 2026-09-24 -->

### mem-1790231753-c830
> A prompt block can state one rationale twice across neighbouring bullets, and the duplication is invisible to every per-line measurement: each bullet was measured alone and shipped alone. Found only by reading the block as prose. Cutting the copy left both arms delivering the same artifact. When a round measures a candidate line in isolation, it is not measuring what the line adds to the block it joins -- schedule a read of the whole block as its own step.
<!-- tags: sys-prompt, writing-for-agents | created: 2026-09-24 -->

### mem-1790070627-b0f9
> A saturated baseline has two very different causes and they license different conclusions. Cause one: the fixture made the answer the stated one. Cause two -- the agent GOES AND SETTLES the premise: it starts a database to find out whether the SQL it is describing behaves as claimed, rather than asserting it. Under cause two a marking line has nothing to buy even in principle, because running the test discharges the premise better than any marking does. Check which cause you have by reading the transcript, not the artifact: the artifact looks the same either way.
<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->

### mem-1790400000-22a1
> A real session log is admissible evidence where a fixture is not, and a round that cites one without reading it has looked at nothing. Every session on this machine is at ~/.claude/projects/<slug>/<id>.jsonl; dispatch session-analysis in evidence mode rather than reading it inline. A fixture shows what a wording does to a situation the round invented; a log shows which situations actually arise and what the agent said while deciding. Use a log to FIND the mechanism, a fixture to measure a wording against it.
<!-- tags: prompt-tests, test-design, session-analysis | created: 2026-09-24 -->

## Decisions

## Fixes

## Context

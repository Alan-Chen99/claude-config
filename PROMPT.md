<request added="loop3" from="user" commit="817f51bd">

# Loop 3 — reverse gate on "Writing for other agents"

Deliverable: `# Writing for other agents` and `[record]` in `sys_prompt/alan-default-next.md` at HEAD, presumed right.

Loops 1–2 (tag `writing-for-agents-backup3`, 32 rounds) ran the opposite gate — to delete, prove no harm — and cut one line; failures are in `.ralph/agent/memories.md` there. Two govern here. What round 18 asked first — per case, the best answer, what went wrong in the recorded outputs inside and outside the rubric with severity, and the alternatives no session took — went into 150 KB of `prompt-tests/step1/`, never into a reference. And `.ralph/agent/*` reached ~320 KB, budgets met by relocation.

## Round 1–2, before any arm

Write that step-1 answer for every case to be run **into its `reference-solution.md`**, from the stored sessions' thinking blocks (`.claude/skills/prompt-tests/SKILL.md` grader rule, dropped after round 6 for blind readers scoring outputs). A reference lacking any of the three is unfinished; no arm reads against it.

## Gate

- **To add or reword a line, adversarially show on the instruments below that it does not harm and buys behaviour absent without it.** A round's default outcome is no change.
- **To cut a line**, an absence arm that is not worse suffices.
- Presence/absence arms, one session each, read whole through `session-analysis` (`mode: evidence`, one per focus, stored as `sa-<arm>-<focus>.md`, JSONL beside it). Add sessions only when the pair disagrees with the prediction or each other. A count is a lead, never a result (n=8 bands held 17–33% power). One closely read session where the line misleads its writer refutes it.
- First candidate: "Claim less" recommends the hint form; `notes/workers-bullet-hint-in-fact-position.md` found it harmful.

## Updates

in `halve-the-runbook`, replace fixture runbook with current `.claude/skills/update-claude-code/SKILL.md`, and modify rubric accordingly. Also remove or replace other test cases on the "Writing for other agents" block; each one kept you must justify that the test case is providing positive value.

To save cost just give it the skill not the decompile. Compression is possible with just that (right? or no?).

[idea] As example, a valid compession here is from

> | `agent-tools/src/hook_input.rs:13-35` | `session_id`, `tool_name`, ...

to something along the lines of "check/ensure that the hook still works"; there may be other correct compressions.
The idea is that almost no doc exist to "answer a question". Here you answer questions with decompile. "update-claude-code" exist becuase without it, if user orders an update, a lot of these things get missed; user had to push agent to check multiple tings, and goal is that it "just work" next time, and do not create bugs. A test to "answer a factual question" is not appropriate, so existing tests/grading of this form should be removed.

[idea] note: The "update-claude-code" skill comes from me asking it to update and then write a skill for next time. So one can perhaps argue that having no-skill is considered "correct" but not efficient (no-skill will then go and discover the same things). Adding anything (esp claims/prescribed approaches) almost always makes it less-correct, and hopefully more efficient. [idea] Maybe you can grade it just on correctness.

## Loop hygiene

- You goal is to make somthing better-than-current as best as you can and to cleanup docs and remove technical debt on this repo, not to satisfy any particular goals on prompt tests.
- All of this repo is mutable including any rubrics. Non represent user preferences; they represent ideas of prompt-engineering only, and may not be correct.
- Memories are not injected; open each round with `ralph tools memory prime`.
- `.ralph/agent/*` ≤ 6000 tokens by `agent-tools count-tokens`, net not larger from round 3; relocation is growth. Record cuts before additions.
- A task line states its ground, never its expected finding. A gate names the finding it guards.
- One prompt candidate per round, decided that round; nothing queued.
- Every fifth round: cleanup.

</request>

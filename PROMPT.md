<request added="loop3" from="user" commit="817f51bd">

# Loop 3 — reverse gate on "Writing for other agents"

Deliverable: `# Writing for other agents` and `[record]` in `sys_prompt/alan-default-next.md` at HEAD, presumed right (unchanged since `817f51bd`).

Loops 1–2 (tag `writing-for-agents-backup3`, 32 rounds) ran the opposite gate — to delete, prove no harm — and cut one line; failures are in `.ralph/agent/memories.md` there. Two govern here. What round 18 asked first — per case, the best answer, what went wrong in the recorded outputs inside and outside the rubric with severity, and the alternatives no session took — went into 150 KB of `prompt-tests/step1/`, never into a reference. And `.ralph/agent/*` reached ~320 KB, budgets met by relocation.

The first of those is what a previous run of this loop kept failing at from the other end: it spent rounds trying to write a grading rubric good enough to run against. `db033f31` says that cannot be done and replaces it.

## Grading — read `db033f31` before round 1

`.claude/skills/prompt-tests/SKILL.md` ("Grader dispatch", "What a rubric is") and `docs/prompt-testing-design.md`. What it changes for this loop:

- **No rubric is written up front and no arm waits on one.** A reference is guidance for the grader; it is inadmissible as a requirement, because the tested agent never saw it. An element satisfiable only by a reference-reader is a defect in the reference, not in the output.
- **The reference is updated by the runs, continuously.** One grader per arm reads the whole session: phase 1 with the reference withheld — constraint argument, then alternative argument, the boundary per item — and phase 2 with it handed over: what it would have caught, what it missed, its defects. Each phase-2 override is then applied to `reference-solution.md`, or its rejection recorded, **after** the run is recorded and citing it; the pre-edit judgement stays. A round that leaves an override neither applied nor rejected has repeated round 18's failure, one run smaller.
- Judgements go to `prompt-tests/runs/<case>/judgement-<arm>.md`. Foci are the cross-run diff instrument, not the grading one: run them where a case already has them, add none.
- The grader holds final authority over every criterion it is given. Do not settle a round by rewriting a criterion before an arm has been graded under it.

## Gate

- **To add or reword a line, adversarially show that it does not harm and buys behaviour absent without it.** A round's default outcome is no change. The evidence is a forcing claim: the line earns its place when a forcing claim standing in the absence arm's judgement dies in the presence arm's. A line that creates a forcing claim is a regression even where the output looks better.
- **To cut a line**, an absence arm whose judgement is not worse suffices.
- One session per arm, graded whole. Add sessions only when the pair disagrees with the prediction or each other. A count is a lead, never a result (n=8 bands held 17–33% power). One closely read session where the line misleads its writer refutes it.
- First candidate: "Claim less" recommends the hint form; `notes/workers-bullet-hint-in-fact-position.md` found it harmful.

## Updates

in `halve-the-runbook`, replace fixture runbook with current `.claude/skills/update-claude-code/SKILL.md`, and modify the reference accordingly. Also remove or replace other test cases on the "Writing for other agents" block; each one kept you must justify that the test case is providing positive value.

To save cost just give it the skill not the decompile. Compression is possible with just that (right? or no?).

[idea] As example, a valid compession here is from

> | `agent-tools/src/hook_input.rs:13-35` | `session_id`, `tool_name`, ...

to something along the lines of "check/ensure that the hook still works"; there may be other correct compressions.
The idea is that almost no doc exist to "answer a question". Here you answer questions with decompile. "update-claude-code" exist becuase without it, if user orders an update, a lot of these things get missed; user had to push agent to check multiple tings, and goal is that it "just work" next time, and do not create bugs. A test to "answer a factual question" is not appropriate, so existing tests/grading of this form should be removed.

[idea] note: The "update-claude-code" skill comes from me asking it to update and then write a skill for next time. So one can perhaps argue that having no-skill is considered "correct" but not efficient (no-skill will then go and discover the same things). Adding anything (esp claims/prescribed approaches) almost always makes it less-correct, and hopefully more efficient. [idea] Maybe you can grade it just on correctness.

Both [idea]s are stakes for the reference to carry, not axes — there are no axes. "Grade on correctness" reads as: the alternative argument prices a step the delivered runbook got wrong or left unrunnable, and does not price the skill for prescribing less than it could have.

## Loop hygiene

- You goal is to make somthing better-than-current as best as you can and to cleanup docs and remove technical debt on this repo, not to satisfy any particular goals on prompt tests.
- All of this repo is mutable including any references and the grading design itself. Non represent user preferences; they represent ideas of prompt-engineering only, and may not be correct. A change to `docs/prompt-testing-design.md` or to a reference breaks comparability with stored runs, so it cites the run that forced it.
- Memories are not injected; open each round with `ralph tools memory prime`.
- `.ralph/agent/*` ≤ 6000 tokens by `agent-tools count-tokens`, net not larger from round 3; relocation is growth. Record cuts before additions.
- A task line states its ground, never its expected finding. A gate names the finding it guards.
- One prompt candidate per round, decided that round; nothing queued.
- Every fifth round: cleanup.

</request>

<request added="loop3" from="user" commit="6349fed6">

# Task

Improve current system prompt so that documentation or text can be written with lower human supervision.

Goal: Try to make as many of these happen as possible:

- Understand effect of current system prompt on agent communication
- Looking at specific cases, such as compressing ".claude/skills/prompt-tests/SKILL.md" and figure out whats the "best way to do it"
- Ensure Agent understand effect of things they write (see /root/claude-config-work/notes/workers-bullet-hint-in-fact-position.md)
- Ensure: As time goes, documentation does not grow unbounded -- achieving that without a human setting or prescribing a size limit
- avg # of doc errors over time in a "agent maintained code base" be reduced
- Reduce things that does not require explicit human approval to add, but requires human intervention to remove
  - Currently this repo probably has many rules that I do not intend, I do not know it exists (I dont read most files), and are being siliently applied without being raised to me. Your job is not to clean this, but to ensure there are less new things of this form
- Refine the newly modified prompt test stack to work better

Understand effect of current system prompt on agent communication, and improve it to better satsify purpose of relevent items in it.

# Prior loop

At tag `writing-for-agents-backup5`. rewinded due to:

- it is not optimizing prompt towards what we care about.
- due to me asking agent to write it, which resulted in phantom directives that cannot be removed by the loop.
- that loop still had criterias of passing in reference-solution.md.

# Rules

- You use tests to _understand behavior_, not to stamp pass or fail to your prompt. There are no absolute good or bad, only tradeoffs. Pass/fail comes from you reasoning about how things will work in the wild, using prompt test behaviors as hints.

  - This is the princple of latest prompt test skill update and why prior history is removed.
  - update the skill as needed
  - rubric help grader understand nuances of the situation, nothing more. so somethign of a summary of "/root/claude-config-work/notes/workers-bullet-hint-in-fact-position.md" shaped, with all conclussions stripped.

- For a prompt to be added, it must be proven to function as you intended in a prompt test, and negative effects must be understood via adversarial testing
- All of this repo is mutable including any references and the grading design itself. Non represent user preferences; they represent ideas of prompt-engineering only, and may not be correct.
- `.ralph/agent/*` ≤ 6000 tokens by `agent-tools count-tokens`. relocation is growth. Cut before add.
- Only semantic claims/reasoning/understanding survive between rounds. Prompt test evidence is not citable across runs. Claims are only valid if you have a hypothesis of why written next to it. If you suspect a claim/reasoning/"why" is flawed, run another test independently.
- Outside of `/root/claude-config-work/prompt-tests/runs/` and fixtures and code-generated content, total added tokens no more than 50000

# Not rules, guidance only

- Use temporary test cases.
- I expect at most 30% of runs be of form "run on full testcase". Rest should be "specific probes"
- Use citations sparingly
- You may ask me for ideas, making exception to rules, clarification, intent of current prompt items, etc. via /telegram-hitl skill. wait up to 24hrs for user, using long-bash skill. make one topic for whole loop.
- Semantic understanding over numbers.
- Default to `n=1`. If you want more, build new cross-domain test cases; do not replicate.
- Rounds generally do not run more than 4 prompt tests
- Consider using "infinite capability" model first. What is the best reasonable thing that can be done, and is that satisfactory?
- Every fifth round: cleanup.
- Delete aggressively. Rubric changed? delete runs. Do not use rewinded loops runs as evidence -- only use those loops for what not to do at the loop level. I have deleted prior runs; round1 should remove all refernces to them, and mark all current rubrics as not-to-be-used-until-updated for new prompt test skill. Outdated information belong in git history only.
- This version of prompt test skill is never ran, and may contain mistakes. Modify or improve the skill as needed.

## New ideas

in `halve-the-runbook`, replace fixture runbook with current `.claude/skills/update-claude-code/SKILL.md`, and modify the reference accordingly. Also remove or replace other test cases on the "Writing for other agents" block; each one kept you must justify that the test case is providing positive value.

To save cost just give it the skill not the decompile. Compression is possible with just that (right? or no?).

[idea] As example, a valid compession here is from

> | `agent-tools/src/hook_input.rs:13-35` | `session_id`, `tool_name`, ...

to something along the lines of "check/ensure that the hook still works"; there may be other correct compressions.
The idea is that almost no doc exist to "answer a question". Here you answer questions with decompile. "update-claude-code" exist becuase without it, if user orders an update, a lot of these things get missed; user had to push agent to check multiple tings, and goal is that it "just work" next time, and do not create bugs. A test to "answer a factual question" is not appropriate, so existing tests/grading of this form should be removed.

[idea] note: The "update-claude-code" skill comes from me asking it to update and then write a skill for next time. So one can perhaps argue that having no-skill is considered "correct" but not efficient (no-skill will then go and discover the same things). Adding anything (esp claims/prescribed approaches) almost always makes it less-correct, and hopefully more efficient. [idea] Maybe you can grade it just on correctness.

Both [idea]s are stakes for the reference to carry, not axes — there are no axes. "Grade on correctness" reads as: the alternative argument prices a step the delivered runbook got wrong or left unrunnable, and does not price the skill for prescribing less than it could have.

</request>

<!-- step 1: reframe -->

# DO - Reframe

By invoking `/do`, the user is telling you the task is larger than what is literally written.
Transform the user's request into the most actionable and verifiable form.

- 'Can X work?' -> 'Try X. Report whether it works, with evidence.'
- 'Fix X' -> 'Reproduce X. Then, diagnose root cause. Fix. Verify fix. Test edge cases.'

<system-reminder> Verify all claims by running the code </system-reminder>

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.do.do --step 2 --original='verbatim' --reframed='actionable form'" />
Execute this command now.

<!-- step 2: expectations -->

# DO - Identify Expectations

Before acting, determine a list of implicit user expectations:

| Dimension    | Examples                                                           |
| ------------ | ------------------------------------------------------------------ |
| Action       | "Change is documented"                                             |
| Knowledge    | "Alternatives considered, rejected with good reason"               |
| Verification | "Verified X against source code, Assumptions tested with commands" |
| Future work  | "Updating dependency X will be easy"                               |

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.do.do --step 3 --action='...' --knowledge='...' --verification='...' --future-work='...'" />
Execute this command now.

<!-- step 3: execute -->

# DO - Execute

Execute the reframed task.

RULES:

- Use all available tools
- Honor expectations identified in Step 2

Execute now. Do not ask for permission unless the action is
destructive or irreversible.

NEXT STEP (after execution is complete):
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.do.do --step 4 --executed='brief summary of what was executed and outcome'" />
Execute this command now.

<!-- step 4: followup -->

# DO - Anticipate Followup

Predict what the user will ACTUALLY say next.

First, briefly sketch what you will write.
Then, generate mostly likely followups, if user had seen your proposed response.

1. VERIFICATION: "test this in some way", "Does this fail with X?", "check the actual output, not just the code"
2. COMPLETENESS: "you forgot the tests", "the old code is still there"
3. ALTERNATIVES: "why not X?"
4. OTHER - at least one that does not fit in the first 3.

User will not be asking about anything that will be in your response.

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.do.do --step 5 --sketch='...' --verification='...' --completeness='...' --alternatives='...' --other='...'" />
Execute this command now.

<!-- step 5: gate -->

# DO - Gate

Quality gate. Review the followups from the previous step.

For each followup, identify:

- **further action needed**: writing more code, further verification, running commands, read files, search online
- **answer sketch**: how would you respond

Then triage every action identified above:

| Category        | Criteria                                               | Action                                                             |
| --------------- | ------------------------------------------------------ | ------------------------------------------------------------------ |
| slow            | `> max(1 minute, 0.2 * length of this session so far)` | run with 30s timeout, or SKIP if it is guaranteed to take longer   |
| destructive     | not reversible                                         | SKIP                                                               |
| unlikely-change | writing code that is most likely going to be reverted  | SKIP                                                               |
| parametrized    | the command to run depend on specific user input       | smoke-test with one random choice, then revert side-effects caused |
| runnable        | none of the above; includes tests, reading files, etc  | DO NOW                                                             |

For each followup, write the triage result inline.

If no runnable actions: workflow complete, respond to user.
If any runnable actions:

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.do.do --step 6 --sketch='...' --followups='followup: action/skip; ...' --runnable='action1, action2, ...'" />
Execute this command now.

<!-- step 6: gate-execute -->

# DO - Gate-Execute

Execute the actions identified in the gate step.

RULES:

- Use all available tools
- No quality degradation: this step is equally important as step 3.
- After done, go to step 4: re-evaluate what followup user will ask with updated context

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.do.do --step 4 --executed='brief summary of gate-execute outcome'" />
Execute this command now.

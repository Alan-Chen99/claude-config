<!-- step 1: reframe -->

# DO - Reframe

By invoking `/do`, the user is telling you the task is larger than what is literally written.
Transform the user's request into the most actionable and verifiable form.

- 'Can X work?' -> 'Try X. Report whether it works, with evidence.'
- 'Fix X' -> 'Reproduce X. Then, diagnose root cause. Fix. Verify fix. Test edge cases.'

<system-reminder> Verify all claims by running the code </system-reminder>

NEXT STEP:
<invoke cmd="agent-tools skill do.do --step 2 --original='verbatim' --reframed='actionable form'" />
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
<invoke cmd="agent-tools skill do.do --step 3 --action='...' --knowledge='...' --verification='...' --future-work='...'" />
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
<invoke cmd="agent-tools skill do.do --step 4 --iteration=1 --executed='brief summary of what was executed and outcome'" />
This is the first entry to the followup-analysis loop — pass --iteration=1.
Execute this command now.

<!-- step 4: followup -->

# DO - Anticipate Followup

You are on iteration N of the followup-analysis loop, where N = the `--iteration` value you received in this step's invoke. If you have no `--iteration` value (first entry from step 3, or a fresh start), use N=1.

Predict what the user will ACTUALLY say next.

First, briefly sketch what you will write.
Then, generate mostly likely followups, if user had seen your proposed response.

1. VERIFICATION: "test this in some way", "Does this fail with X?", "check the actual output, not just the code"
2. COMPLETENESS: "you forgot the tests", "the old code is still there"
3. ALTERNATIVES: "why not X?"
4. OTHER - at least one that does not fit in the first 3.

User will not be asking about anything that will be in your response.

NEXT STEP:
<invoke cmd="agent-tools skill do.do --step 5 --iteration=N --sketch='...' --verification='...' --completeness='...' --alternatives='...' --other='...'" />
Pass the same N you received in this step's invoke.
Execute this command now.

<!-- step 5: gate -->

# DO - Gate

You are on iteration N of the followup-analysis loop, where N = the `--iteration` value you received in this step's invoke.

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

---

ROUTE: invoke exactly ONE of the two routes below. Never both, never silence.

- **TERMINATE** — every triaged action is SKIP, or no runnable actions remain. The followup-analysis loop (steps 4-5-6) has converged. Do NOT terminate just because the user's task feels done; the triage IS the test. Iteration count is observability only; it is not a termination criterion.

  <invoke cmd="agent-tools skill do.do --step 7 --iteration=N --converged='one-sentence reason: e.g. no runnable followups remain, or all remaining actions are SKIP'" />

- **ITERATE** — at least one followup is `runnable` (DO NOW) or `parametrized` (smoke-test). Material change to your response is still possible.

  <invoke cmd="agent-tools skill do.do --step 6 --iteration=N --sketch='...' --followups='followup: action/skip; ...' --runnable='action1, action2, ...'" />

Pass the same N through. Execute exactly one of the above now.

<!-- step 6: gate-execute -->

# DO - Gate-Execute

You are on iteration N of the followup-analysis loop, where N = the `--iteration` value you received in this step's invoke.

Execute the actions identified in the gate step.

RULES:

- Use all available tools
- No quality degradation: this step is equally important as step 3.
- After done, go to step 4: re-evaluate what followup user will ask with updated context.

NEXT STEP:
<invoke cmd="agent-tools skill do.do --step 4 --iteration=N+1 --executed='brief summary of gate-execute outcome'" />
Increment N by 1 from the value you received in this step's invoke. E.g., if you received `--iteration=2`, invoke step 4 with `--iteration=3`.
Execute this command now.

<!-- step 7: done -->

# DO - Done

Workflow complete.

You reached this step because the followup-analysis loop converged — not because the user's task is necessarily fully done. Before responding to the user, confirm closure on each expectation dimension from step 2:

| Dimension     | Closed? (yes / partial / no / n/a) | If not yes: what remains |
| ------------- | ---------------------------------- | ------------------------ |
| Action        |                                    |                          |
| Knowledge     |                                    |                          |
| Verification  |                                    |                          |
| Future work   |                                    |                          |

Rules for the table:

- Use the values you wrote in step 2's `--action` / `--knowledge` / `--verification` / `--future-work` args as the closure target for each row.
- A "yes" or "n/a" row needs no entry in the third column.
- A "partial" or "no" row REQUIRES a non-empty third column naming what remains.
- If a step-2 dimension was thin or unspecified, mark it "n/a".
- If you find yourself filling in many partial/no rows, note in your response to the user that termination may have been premature.

Then respond to the user with your final answer. If any "partial" or "no" rows remain after closure, surface those items in your response so the user can decide whether to push further.

No further invocations of this skill. End of workflow.

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

OUTPUT:

RESPONSE SKETCH: ...

ANTICIPATED FOLLOWUPS:

- [followup]: [further action needed, or "no verification needed"]; [answer sketch]

ACTIONS: (all actions you wrote from above)

- [action]: (Category)

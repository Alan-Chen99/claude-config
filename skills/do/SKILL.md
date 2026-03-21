---
name: do
description: Meta-execution pipeline — transforms any request into intent identification, actionable reframing, execution, reflection with self-correction, and followup anticipation.
---

# Do

When this skill activates, IMMEDIATELY invoke the script. The script IS the
workflow.

## Invocation

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.do.do --step 1" />

| Argument      | Required | Description                                            |
| ------------- | -------- | ------------------------------------------------------ |
| `--step`      | Yes      | Current step (1-5)                                     |
| `--followups` | Step 3+  | Anticipated followups (step 5) or gate failures (retry) |
| `--iteration` | No       | Current iteration (default: 1, max: 3)                 |

Do NOT analyze or explore first. Run the script and follow its output.

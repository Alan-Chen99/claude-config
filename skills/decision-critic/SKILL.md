---
name: decision-critic
description: use only if invoked by user or workflow
---

# Decision Critic

Stress-test decisions and reasoning.

When this skill activates, IMMEDIATELY invoke the script. The script IS the
workflow.

## Invocation

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.decision_critic.decision_critic --step 1 --decision '<decision text>'" />

| Argument        | Required | Description                             |
| --------------- | -------- | --------------------------------------- |
| `--step`        | Yes      | Current step (1-7)                      |
| `--decision`    | Step 1   | The decision statement being criticized |

Do NOT analyze or critique first. Run the script and follow its output.

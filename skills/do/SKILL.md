---
name: do
description: Perform task by inferring user intent: no constraint list, no babysitting. Best for non-destructive and reversible tasks.
---

# Do

When this skill activates, IMMEDIATELY invoke the script. The script IS the
workflow.

## Invocation

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.do.do --step 1" />

Do NOT analyze or explore first. Run the script and follow its output.

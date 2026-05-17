---
name: deepthink
description: use only if invoked by user or workflow
---

# DeepThink

Structured reasoning for open-ended analytical questions.

When this skill activates, IMMEDIATELY invoke the script. The script IS the workflow.

Invoke:

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.deepthink.think --step 1" />

Do NOT explore or analyze first. Run the script and follow its output.

---
name: alan-writing-style
description: Style-matched content generation for Alan's writing voice. Invoke IMMEDIATELY via python script when user requests content written in Alan's style or writing review against Alan's conventions. Do NOT write first - the script orchestrates the style workflow.
---

# Alan Writing Style

When this skill activates, IMMEDIATELY invoke the script. The script IS the
workflow.

## Invocation

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.alan_writing_style.writing_style --step 1 --thoughts '<initial context>'" />

| Argument     | Required | Description                                        |
| ------------ | -------- | -------------------------------------------------- |
| `--step`     | Yes      | Current step (1-9)                                 |
| `--thoughts` | No       | Accumulated thinking, draft content, and findings  |

Do NOT write or draft content first. Run the script and follow its output.

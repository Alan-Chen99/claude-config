---
name: alan-coding-style
description: Style-matched code generation and review for Alan's coding conventions. Invoke IMMEDIATELY via python script when user requests code written in Alan's style or code review against Alan's conventions. Do NOT code first - the script orchestrates the style workflow.
---

# Alan Coding Style

When this skill activates, IMMEDIATELY invoke the script. The script IS the
workflow.

## Invocation

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.alan_coding_style.coding_style --step 1 --thoughts '<initial context>'" />

| Argument     | Required | Description                                        |
| ------------ | -------- | -------------------------------------------------- |
| `--step`     | Yes      | Current step (1-9)                                 |
| `--thoughts` | No       | Accumulated thinking, draft code, and findings     |

Do NOT write or draft code first. Run the script and follow its output.

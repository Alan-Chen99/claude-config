---
name: alan-coding-style
description: use only if invoked by user or workflow
---

# Alan Coding Style

Style-matched code generation and review for Alan's coding conventions.

When this skill activates, IMMEDIATELY invoke the script. The script IS the
workflow.

## Invocation

<invoke cmd="agent-tools skill alan_coding_style.coding_style --step 1 --thoughts '<initial context>'" />

| Argument     | Required | Description                                        |
| ------------ | -------- | -------------------------------------------------- |
| `--step`     | Yes      | Current step (1-9)                                 |
| `--thoughts` | No       | Accumulated thinking, draft code, and findings     |

Do NOT write or draft code first. Run the script and follow its output.

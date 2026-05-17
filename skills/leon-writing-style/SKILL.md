---
name: leon-writing-style
description: use only if invoked by user or workflow
---

# Leon Writing Style

Style-matched content generation for Leon's writing voice.

When this skill activates, IMMEDIATELY invoke the script. The script IS the
workflow.

## Invocation

<invoke cmd="agent-tools skill leon_writing_style.writing_style --step 1 --thoughts '<initial context>'" />

| Argument     | Required | Description                                        |
| ------------ | -------- | -------------------------------------------------- |
| `--step`     | Yes      | Current step (1-9)                                 |
| `--thoughts` | No       | Accumulated thinking, draft content, and findings  |

Do NOT write or draft content first. Run the script and follow its output.

---
name: prompt-patch
description: Structured 10-step workflow for making targeted prompt changes correctly. Motivation analysis, multi-option drafting, conflict/regression/failure-mode checks, and iterative revision.
---

# Prompt Patch

When this skill activates, IMMEDIATELY invoke the script. The script IS the
workflow.

## Invocation

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.prompt_patch.do --step 1" />

Do NOT analyze or explore first. Run the script and follow its output.

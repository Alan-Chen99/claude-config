---
name: copy-writing-style
description: use only if invoked by user or workflow
---

# Copy Writing Style

Style-matched content generation from any style reference file.

When this skill activates, IMMEDIATELY invoke the script. The script IS the
workflow.

## Input Requirements

- **Style reference** (required): A file containing example text in the target style. Provided via `@filename` in the user's message, or as an explicit path.
- **Task or text** (required): Either a writing task ("write a blog post about X") or existing text to rewrite in the target style.

## Invocation

<invoke cmd="agent-tools skill copy_writing_style.do --step 1 --style-ref '<path to style reference file>'" />

Do NOT analyze or explore first. Run the script and follow its output.

## Arguments

- `--style-ref`: Path to the style reference file. Required at step 1. Script persists path for subsequent steps.
- `--step`: Current step number (1-3).
- `--iteration`: Iteration count for step 3 (default 0). Script increments this automatically in next-step commands.

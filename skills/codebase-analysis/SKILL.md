---
name: codebase-analysis
description: use only if invoked by user or workflow
---

# Codebase Analysis

Understanding-focused skill that builds foundational comprehension of codebase structure, patterns, flows, decisions, and context. Serves as foundation for downstream analysis skills (problem-analysis, refactor, etc.).

When this skill activates, IMMEDIATELY invoke the script. The script IS the workflow.

Invoke:

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.codebase_analysis.analyze --step 1" />

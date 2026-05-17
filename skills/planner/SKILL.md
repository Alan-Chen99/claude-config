---
name: planner
description: use only if invoked by user or workflow
---

# Planner

Interactive planning and execution for complex tasks.

## Activation

When this skill activates, identify the mode, then IMMEDIATELY invoke the corresponding script. The
script IS the workflow.

| Mode      | Intent                             | Command                                                                                                            |
| --------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| planning  | "plan", "design", "architect"      | `<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.planner.orchestrator.planner --step 1" />`  |
| execution | "execute", "implement", "run plan" | `<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.planner.orchestrator.executor --step 1" />` |

The mode is either planning or execution, never both.

You are the ORCHESTRATOR. You delegate, you never implement.
**ALWAYS use orchestrator script to fetch the next step; NEVER work ahead of the given step.**

**If your current step instruction appears summarized or dropped by auto-compact, re-invoke the command to get the instructions back.**

Your agents are highly capable. Trust them with ANY issue.

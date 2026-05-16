---
name: planner-lite
description: Lightweight planning and execution without subagent dispatch. Subagent-compatible alternative to full planner.
---

## Activation

When this skill activates, IMMEDIATELY invoke the corresponding script. The
script IS the workflow.

| Mode      | Intent                                             | Command                                                                                                            |
| --------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| planning  | "plan lite", "design lite", "lite plan"            | `<invoke cmd="agent-tools skill planner_lite.plan --step 1" />`            |
| execution | "execute lite", "implement lite", "run lite plan"  | `<invoke cmd="agent-tools skill planner_lite.execute --step 1 --state-dir <dir>" />` |

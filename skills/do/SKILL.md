---
name: do
description: Perform task by inferring user intent: no constraint list, no babysitting. Best for non-destructive and reversible tasks.
---

# Do

When this skill activates, IMMEDIATELY invoke the script. The script IS the
workflow.

## Evidence Hierarchy

| Tier | Source         | Notes                                                |
| ---- | -------------- | ---------------------------------------------------- |
| 1    | running-code   | MUST run as final evidence                           |
| 2    | source-code    | Use for analysis, run/test before responding to user |
| 3    | documentation  | Use for analysis, run/test before responding to user |
| 4    | human-provided | MUST verify                                          |
| 5    | from-memory    | MUST verify                                          |

SHOULD: to read source code, clone using git to /tmp and checkout the exact revision

## Invocation

<invoke cmd="agent-tools skill do.do --step 1" />

Do NOT analyze or explore first. Run the script and follow its output.

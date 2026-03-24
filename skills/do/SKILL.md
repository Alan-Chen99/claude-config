---
name: do
description: Perform task by inferring user intent: no constraint list, no babysitting. Best for non-destructive and reversible tasks.
---

# Do

When this skill activates, IMMEDIATELY invoke the script. The script IS the
workflow.

## Evidence Hierarchy

| Tier | Source         | Notes                                                               |
| ---- | -------------- | ------------------------------------------------------------------- |
| 1    | running-code   | ALWAYS PREFERED                                                     |
| 2    | source-code    | By default, clone using git to /tmp and checkout the exact revision |
| 3    | documentation  | Use same version if possible                                        |
| 4    | human-provided | MUST verify if possbile                                             |
| 5    | from-memory    | MUST verify, state clearly if not possible                          |

IMPORTANT: Cite the tier on all claims made. Ex: "...claim (source-code)"

ALWAYS find higher tier evidence if available.

## Invocation

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.do.do --step 1" />

Do NOT analyze or explore first. Run the script and follow its output.

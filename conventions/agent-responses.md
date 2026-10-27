# Agent Responses Convention

After finishing a task, include a **Required notes** section. The section MUST
exist even if empty ("No items applicable").

**Subagents MUST also follow this requirement.** Parent agents propagate
significant items to the user, naming the agent that saw each one. An Agent call
inherits neither the system prompt nor the output style, and `Explore` and `Plan`
receive no CLAUDE.md, so the ask reaches a subagent through the `SubagentStart`
hook — `agent-tools hook-subagent-start`, whose terser copy of the categories
below is pinned to this file by `scripts/check-prompt-coupling.sh`.

## Categories

Before writing the section, scan your whole response from the beginning and ask
each category's forcing questions. If an answer is yes, you MUST include the
item — even if it feels minor.

| Category | Report when… | Forcing questions |
|----------|--------------|-------------------|
| **corrected mistake** | You made an error since the last user interaction and later fixed it | Did I try something that failed, then change approach? Reverse or revise an earlier assessment? Retry differently after a tool error? |
| **suspected user mistake** | User's input, files, or assumptions appear wrong — even if you are unsure | Did anything the user provided seem wrong or unintentional? Did I silently fix or work around it? |
| **tool issue** | Tool errors, unhelpful results, environment gaps, or suboptimal setup | Did a tool error, give unhelpful output, or force a retry? Did I work around a limitation instead of reporting it? |
| **context waste** | You read content with low relevance, or encountered excessive repetition | Did I read irrelevant files, the same content twice, or large outputs that did not contribute? |
| **unexpected change** | Any changes you made beyond what was explicitly requested | Did I modify, replace, or remove anything beyond the request? Did scope expand? |
| **manual action needed** | User must do something (install, configure, restart, approve) | Does the user need to do something I cannot? |
| **hidden challenge** | A non-obvious problem you solved that wasn't anticipated from the request | Did I solve a problem the user didn't anticipate? |
| **instruction issue** | Instruction conflicts, missing references, or instruction problems observed | Did an instruction reference something missing, contradict another, or cause confusion? |

## Relabeling override

If a finding fits multiple categories, pick the one that is hardest to admit:
"corrected mistake" over "unexpected change", "suspected user mistake" over a
descriptive mention, "tool issue" over a silent workaround. Required notes
surface what the user would otherwise miss; self-favorable relabeling defeats
that.

## Format

```
## Required notes
- **corrected mistake** retried git rebase after worktree conflict; switched to cherry-pick
- **tool issue** cc-pretty.py --tool-max 500 truncated relevant output
```

Or when clean: `## Required notes` followed by `No items applicable.`

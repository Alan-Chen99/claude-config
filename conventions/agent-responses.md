# Agent Responses Convention

After finishing a task, include a **Required notes** section. The section MUST
exist even if empty ("No items applicable").

**Subagents MUST also follow this requirement.** Parent agents propagate
significant items to the user.

## Categories

| Category | Report when… |
|----------|-------------|
| **manual action needed** | User must do something (install, configure, restart, approve) |
| **suspected user mistake** | User's input, files, or assumptions appear wrong — even if you are unsure |
| **hidden challenge** | A non-obvious problem you solved that wasn't anticipated from the request |
| **corrected mistake** | You made an error since the last user interaction and later fixed it |
| **instruction issue** | Instruction conflicts, missing references, or instruction problems observed |
| **tool issue** | Tool errors, unhelpful results, environment gaps, or suboptimal setup |
| **context waste** | You read content with low relevance, or encountered excessive repetition |
| **unexpected change** | Any changes you made beyond what was explicitly requested |

## Before writing Required notes

Backward-scan: review your entire response from the beginning. For each
category, ask the corresponding forcing question below. If the answer is yes,
you MUST include the item — even if it feels minor.

### Forcing questions

1. **corrected mistake** — Did I try something that failed, then change
   approach? Did I reverse or revise an earlier assessment? Did any tool call
   return an error that caused me to retry differently?
2. **suspected user mistake** — Did I notice anything in the user's files,
   input, or assumptions that seems wrong or unintentional? Did I silently fix
   or work around something the user provided?
3. **tool issue** — Did any tool return an error, unhelpful output, or force a
   retry? Did I work around a tool limitation instead of reporting it?
4. **context waste** — Did I read files that turned out irrelevant? Did I read
   the same content more than once? Did large tool outputs not contribute to
   the result?
5. **unexpected change** — Did I modify, replace, or remove anything beyond
   what was explicitly requested? Did scope expand during the task?
6. **manual action needed** — Does the user need to do something I cannot do
   (install, restart, approve, configure)?
7. **hidden challenge** — Did I solve a non-obvious problem the user didn't
   anticipate?
8. **instruction issue** — Did any instruction reference something missing,
   contradict another instruction, or cause confusion?

### Relabeling override

If a finding fits multiple categories, pick the one that is hardest to admit:
- "corrected mistake" over "unexpected change"
- "suspected user mistake" over descriptive mention
- "tool issue" over silent workaround

The purpose of Required notes is to surface things the user would otherwise
miss. Self-favorable relabeling defeats this purpose.

## Format

```
### Required notes
- **corrected mistake** retried git rebase after worktree conflict; switched to cherry-pick
- **tool issue** cc-pretty.py --tool-max 500 truncated relevant output
```

Or when clean:

```
### Required notes
No items applicable.
```

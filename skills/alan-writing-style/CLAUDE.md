# alan-writing-style/

Write, rewrite or check text as Alan. Single `SKILL.md`; nothing is loaded at runtime besides it.

## Files

| File       | What                                                                                        | When to read    |
| ---------- | ------------------------------------------------------------------------------------------- | --------------- |
| `SKILL.md` | The skill: jobs, registers, shape and sentence rules, errors policy, Claude tells, procedure | Using the skill |

## Subdirectories

| Directory  | What                                                                                                                                                                                                            | When to read                                    |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `samples/` | Before/after pairs. `NN-<name>.before.md` is the agent draft Alan edited from, `NN-<name>.after.md` is his rewrite. Not referenced by `SKILL.md` and not copied into it: the rules are derived from the pairs, stated for any domain, and the pairs are the regression cases. | Editing a rule in `SKILL.md`; adding a pair after an edit round |

## Provenance

2026-09-22: pair 1 was edited from an unadapted agent draft, 205 -> 96 words, nothing kept. Pairs 2 and 3 were edited from drafts already written "as Alan" from the corpus profile: pair 2 nothing kept, pair 3 ~90% kept. Sentence rules and the illustrations under them come from 251 long prompts in `~/.claude/history.jsonl`; shape rules come from the three pairs. The first `SKILL.md` (commit `c0df1746`) carried the pairs as exemplars and rules naming their labels, elision strings and headers; those were removed as overfitting, since every pair is software documentation. Rules in `SKILL.md` change only from a pair. Design: `docs/superpowers/specs/2026-09-22-alan-writing-style-design.md`.

## Iteration

The skill is engineered from pairs, not measured against a detector. Procedures used so far; pick per round rather than run as a checklist.

- Write-then-edit. A general opus agent writes a piece from a fact sheet with no skill (the `before`). A second agent reads `SKILL.md` and rewrites it (the skill output). Alan edits the skill output (the `after`). Retention is the share of words in the `after` that the skill output already had, by longest common subsequence over whitespace tokens; `git diff --no-index --word-diff` shows the same thing by eye. Target >= 80%.
- Regression. After a rule change, rerun the skill on every `samples/*.before.md` and compare with the `after`. Lower retention on an old pair needs a reason.
- Cross-domain. Fact sheets from outside this repo (hardware, household, a message to a person): a rule that only holds for software docs is overfitting.
- Ask. Several rewrites can be right. When a rule is uncertain, ask Alan "A or B" with concrete text, or ask him to write the piece, rather than reading the answer off the prompt corpus.

A subagent testing a worktree's copy must `Read` that file: `~/.claude/skills` is a symlink to the canonical checkout, so invoking `/alan-writing-style` loads the installed version.

Retention, given `after` and `skill` files:

```python
import difflib, sys
a, b = (open(p).read().split() for p in sys.argv[1:3])
kept = sum(m.size for m in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
print(f"{kept}/{len(a)} = {kept/len(a):.0%}")
```

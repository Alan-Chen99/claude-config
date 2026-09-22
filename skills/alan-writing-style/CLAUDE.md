# alan-writing-style/

Write, rewrite or check text as Alan. Single `SKILL.md`; nothing is loaded at runtime besides it.

## Files

| File       | What                                                                                                   | When to read     |
| ---------- | ------------------------------------------------------------------------------------------------------ | ---------------- |
| `SKILL.md` | The skill: jobs, registers, shape and sentence rules, errors policy, Claude tells, exemplars, procedure | Using the skill  |

## Subdirectories

| Directory  | What                                                                                                                                                                                   | When to read                                                                  |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `samples/` | Before/after pairs. `NN-<name>.before.md` is the agent draft Alan edited from, `NN-<name>.after.md` is his rewrite. Not referenced by `SKILL.md`; its exemplars are copied from the `after` files by hand, so a change to a pair means a change to `SKILL.md`. | Editing the rules or exemplars in `SKILL.md`; adding a pair after an edit round |

Provenance (2026-09-22): pair 1 was edited from an unadapted agent draft, 205 -> 96 words, nothing kept. Pairs 2 and 3 were edited from drafts already written "as Alan" from the corpus profile: pair 2 nothing kept, pair 3 ~90% kept (`git diff --no-index --word-diff` between the two files). Rules in `SKILL.md` change only from a pair. Design: `docs/superpowers/specs/2026-09-22-alan-writing-style-design.md`.

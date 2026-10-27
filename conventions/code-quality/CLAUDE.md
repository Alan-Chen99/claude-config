# code-quality/

Code smell checklists, one review mode per file; each file's categories share its opening question.

## Files

| File                               | What                                                         | When to read                                                  |
| ---------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------- |
| `01-naming-and-types.md`           | Naming precision and consistency, domain modeling, types     | Reviewing names, domain modeling, type design                 |
| `02-structure-and-composition.md`  | Functions, control flow, state, DI, locality, errors         | Reviewing function structure, control flow, error handling    |
| `03-patterns-and-idioms.md`        | Expression complexity, idioms, readability, dead code        | Reviewing expressions, modern idioms, dead code               |
| `04-repetition-and-consistency.md` | Duplication, scattered validation, rules and conditions      | Reviewing duplication, validation, business rules             |
| `05-documentation-and-tests.md`    | Doc staleness, test naming, generated code, schema drift     | Reviewing docs, tests, schema coherence                       |
| `06-module-and-dependencies.md`    | Module boundaries, architecture                              | Reviewing module structure, architecture                      |
| `07-cross-file-consistency.md`     | Interface consistency, feature flag evaluation               | Reviewing API consistency, feature flags                      |
| `08-codebase-patterns.md`          | Cross-file comprehension                                     | Reviewing flows that span many files                          |

## Applicability Quick Reference

Design Review: Code Intent before diffs exist. Diff Review: proposed changes in a plan. Codebase Review: code after implementation. Refactor Design / Refactor Code: architecture and intent / implementation quality of existing code. A Design phase reads a file's `<design-mode>` block, the others its `<code-mode>`.

| Document                      | Design Review | Diff Review | Codebase Review | Refactor Design | Refactor Code |
| ----------------------------- | :-----------: | :---------: | :-------------: | :-------------: | :-----------: |
| 01-naming-and-types           |      Yes      |     Yes     |       Yes       |       Yes       |      Yes      |
| 02-structure-and-composition  |      Yes      |     Yes     |       Yes       |       Yes       |      Yes      |
| 03-patterns-and-idioms        |      No       |     Yes     |       Yes       |       No        |      Yes      |
| 04-repetition-and-consistency |      No       |     Yes     |       Yes       |       No        |      Yes      |
| 05-documentation-and-tests    |      No       |     Yes     |       Yes       |       No        |      Yes      |
| 06-module-and-dependencies    |      Yes      |     No      |       Yes       |       Yes       |      Yes      |
| 07-cross-file-consistency     |      Yes      |     No      |       Yes       |       Yes       |      Yes      |
| 08-codebase-patterns          |      No       |     No      |       Yes       |       No        |      Yes      |

## Agent Policy

- `skills/scripts/skills/refactor/refactor.py` and `skills/scripts/skills/lib/workflow/quality_docs.py` parse these files: keep the line-1 `<!-- applicable_phases: ... -->` comment (this table mirrors it), the `<design-mode>`/`<code-mode>` blocks between the title and the first category, and `## N. Name` category headings. A file without `<design-mode>` yields no Refactor Design targets.
- A refactor agent receives one category, from its heading to the next, without the file's opening: a category must stand alone.
- A check lives in one category; a check with a file scope and a codebase scope states both thresholds there.

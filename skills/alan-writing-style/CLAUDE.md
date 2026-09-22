# alan-writing-style/

Write, rewrite or check text as Alan. Single `SKILL.md`; nothing is loaded at runtime besides it.

## Files

| File       | What                                                                                        | When to read    |
| ---------- | ------------------------------------------------------------------------------------------- | --------------- |
| `SKILL.md` | The skill: jobs, registers, shape and sentence rules, errors policy, Claude tells, procedure | Using the skill |

## Subdirectories

| Directory  | What                                                                                                                                                                                                                                                                                                                              | When to read                                    |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `samples/` | One sample = `NN-<name>.{context,ai,skill,human}.md`. Each stage sees all former ones: `context` is the fact sheet or the verbatim source the piece is about (the allowed context, for the human too); `ai` is an opus draft from the context with no skill; `skill` (optional) is the skill's rewrite of `ai` given the context; `human` is Alan's version, given all three. Not referenced by `SKILL.md` and not copied into it: rules are derived from the samples and stated for any domain; the samples are the regression cases. | Editing a rule in `SKILL.md`; adding a sample after an edit round |

## Provenance

| Sample | Context | `ai` | `skill` | `human` |
| --- | --- | --- | --- | --- |
| 01 readme rationale | reconstructed from the draft and the repo CLAUDE.md | unadapted agent draft, from the repo | none | Alan's edit, 205 -> 96 words, nothing kept |
| 02 mechanism explanation | fixed: `ralph/build.yml` worker section verbatim plus four facts | opus, no skill, from the context | SKILL.md `f9f741fb` | pending. The earlier pair (`c0df1746`, `before`/`after`) had no fixed context and Alan's rewrite quoted `build.yml` text the draft never had, so it could not be scored; its rewrite was the source of the label, name-period-gloss and quote rules |
| 03 status report | reconstructed from the draft | agent draft "as Alan" from the corpus profile | none | Alan's edit, ~90% kept |
| 04 filament (hardware, rationale) | fact sheet | opus, no skill | SKILL.md `f9f741fb` | pending |
| 05 sinking fund (household, mechanism) | fact sheet | opus, no skill | SKILL.md `f9f741fb` | pending |
| 06 half marathon (`chat`, message to a friend) | fact sheet | opus, no skill | SKILL.md `f9f741fb` | pending |

Sentence rules and the illustrations under them come from 251 long prompts in `~/.claude/history.jsonl`; shape rules come from samples 01-03. The first `SKILL.md` (`c0df1746`) carried the samples as exemplars and rules naming their labels, elision strings and headers; those were removed as overfitting (`aaf03cde`), since every sample then was software documentation. Rules in `SKILL.md` change only from a sample. Design: `docs/superpowers/specs/2026-09-22-alan-writing-style-design.md`.

## Iteration

The skill is engineered from samples, not measured against a detector. Procedures used so far; pick per round rather than run as a checklist.

- Stages. Write the context first (facts, or the source verbatim, and the register); an opus agent with no skill writes `ai` from it; an opus agent that has read `SKILL.md` rewrites `ai` given the context, into `skill`; Alan edits a copy of `skill` (or writes from the context) into `human`. Retention is the share of words in `human` that `skill` already had, by longest common subsequence over whitespace tokens; `git diff --no-index --word-diff` shows the same thing by eye. Target >= 80%. Noise floor: two skill runs on the same input at `f9f741fb` overlapped 49-73% by the same measure, so a single run's retention is a coarse number.
- Regression. After a rule change, rerun the skill on every sample's `ai` (with its context) and compare with `human`. Lower retention on an old sample needs a reason.
- Cross-domain. Contexts from outside this repo (hardware, household, a message to a person): a rule that only holds for software docs is overfitting.
- Ask. Several rewrites can be right. When a rule is uncertain, ask Alan "A or B" with concrete text, or ask him to write the piece from a fixed context, rather than reading the answer off the prompt corpus.

A subagent testing a worktree's copy must `Read` that file: `~/.claude/skills` is a symlink to the canonical checkout, so invoking `/alan-writing-style` loads the installed version.

Retention, given `human` and `skill` files:

```python
import difflib, sys
a, b = (open(p).read().split() for p in sys.argv[1:3])
kept = sum(m.size for m in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
print(f"{kept}/{len(a)} = {kept/len(a):.0%}")
```

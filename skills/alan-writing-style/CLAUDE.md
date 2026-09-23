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
| 02 mechanism explanation | fixed: `ralph/build.yml` worker section verbatim plus four facts | opus, no skill, from the context | SKILL.md `599e7a41` (the `f9f741fb` run is in that commit) | Two sentences, 44 words (skill output 376): what goes wrong, and that `ralph/build.yml` addresses it with `(instruction)`/`(contract)` markers, `see ralph/build.yml for details`. 23% of the skill output kept, 13% of the context. His comment: "written for human readers." The earlier pair (`c0df1746`, `before`/`after`) had no fixed context and Alan's rewrite quoted `build.yml` text the draft never had, so it could not be scored; its rewrite was the source of the label, name-period-gloss and quote rules |
| 03 status report | reconstructed from the draft | agent draft "as Alan" from the corpus profile | none | Alan's edit, ~90% kept |
| 04 backups (home server, rationale) | fact sheet | opus, no skill | SKILL.md `599e7a41` | Two sentences, 33 words (skill output 180): what runs and the `cron` line. No goal, rationale, alternatives or history. His comment: "this is a \"home-server\" --> Talking to me is authoritive, not the doc. If this is a CLAUDE.md that is different; in no cases will i need to write a CLAUDE.md in my style though." Replaces 04 filament (`1e01f930`), which Alan could not judge: a topic he does not know gives no edit |
| 05 sinking fund (household, mechanism) | fact sheet | opus, no skill | SKILL.md `f9f741fb` | Alan's rewrite: the fact list as `- Label: content` bullets, 51% of the skill output kept, 99% of it (203 of 206 words) is the context's own fact list. His comment: "I would just copy the list if thats allowed / expected that text does not have to all come from me." |
| 06 half marathon (`chat`, message to a friend) | fact sheet with a stance for the writer | opus, no skill | SKILL.md `f9f741fb` | One line: `Are you sure about doubling the long run in one week?` His comments: the context "is written as if i actually held the opinion"; "by default i do not assume other people are stupid". Retention not meaningful |

Sentence rules and the illustrations under them come from 251 long prompts in `~/.claude/history.jsonl`; shape rules come from samples 01-03. The first `SKILL.md` (`c0df1746`) carried the samples as exemplars and rules naming their labels, elision strings and headers; those were removed as overfitting (`aaf03cde`), since every sample then was software documentation. Rules in `SKILL.md` change only from a sample. Round 3 (02, 04; regressions at `8ab5e739`: 01 45% -> 25%, 02 23% -> 26%, 03 85% -> 78%, 04 46% -> 82%, 05 100% -> 99%, 06 100% -> 73%; the 01 drop is mechanism kept and labels dropped, addressed in the next commit): content set by reader and authority (shape 1), point to an openable source instead of quoting it, labels only for parallel parts, cut depth stated, CLAUDE.md out of scope. Round 2 (05, 06; regressions at `599e7a41`: 01 17% -> 45%, 03 85% -> 85%, 05 56% -> 100%): competent-reader principle, goal-or-problem first, reuse the source instead of quote-only, keep/cut by what the reader acts on or looks up, message = one question, italics only on a stated pair, parenthetical example without a label. Design: `docs/superpowers/specs/2026-09-22-alan-writing-style-design.md`.

## Iteration

The skill is engineered from samples, not measured against a detector. Procedures used so far; pick per round rather than run as a checklist.

- Stages. Write the context first (facts, or the source verbatim, and the register); an opus agent with no skill writes `ai` from it; an opus agent that has read `SKILL.md` rewrites `ai` given the context, into `skill`; Alan edits a copy of `skill` (or writes from the context) into `human`. Retention is the share of words in `human` that `skill` already had, by longest common subsequence over whitespace tokens; `git diff --no-index --word-diff` shows the same thing by eye. Target >= 80%. Noise floor: two skill runs on the same input at `f9f741fb` overlapped 49-73% by the same measure, so a single run's retention is a coarse number. A sample line quoted in `SKILL.md` as an illustration makes that sample's regression worthless: at `599e7a41` rule 7 quoted the 06 reply and the 06 regression scored 100%; the quote was replaced by a description.
- Regression. After a rule change, rerun the skill on every sample's `ai` (with its context) and compare with `human`. Lower retention on an old sample needs a reason.
- Cross-domain. Contexts from outside this repo (hardware, household, a message to a person): a rule that only holds for software docs is overfitting.
- Context. The context is available material, not required content: for a README he answers questions about, Alan kept 13% of it (02) and two facts of six (04); for a shared wiki note he kept all of it (05). The brief must say the doc's function: who reads it, where it lives, what the reader has at hand, whether the doc or the writer answers questions. Alan read the first 02 brief as "make a standalone explanation to somewhere else", which is why that version quoted `build.yml` and the redo, a README section beside it, points to it instead. A topic Alan cannot judge gives no edit (04 filament). For a message, the context is the situation only, never a stance for him to voice (06). Copying from the context in the human stage is expected; a copied list is itself a style datum (05).
- Ask. Several rewrites can be right. When a rule is uncertain, ask Alan "A or B" with concrete text, or ask him to write the piece from a fixed context, rather than reading the answer off the prompt corpus.

A subagent testing a worktree's copy must `Read` that file: `~/.claude/skills` is a symlink to the canonical checkout, so invoking `/alan-writing-style` loads the installed version.

Retention, given `human` and `skill` files:

```python
import difflib, sys
def words(p):
    t = open(p).read()
    return (t[:t.index('\n---')] if '\n---' in t else t).split()  # Alan's comments follow a --- rule
a, b = words(sys.argv[1]), words(sys.argv[2])
kept = sum(m.size for m in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
print(f"{kept}/{len(a)} = {kept/len(a):.0%}")
```

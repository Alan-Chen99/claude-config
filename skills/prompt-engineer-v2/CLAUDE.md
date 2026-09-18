# prompt-engineer-v2/

Autoloading prompt-engineering context. `SKILL.md` carries the principles that load whenever the agent is working on prompts, instructions, agent definitions, or other LLM-context text. The 12-step "patch mode" script under `steps.md` is invoked only on user request or for complex edits.

## Files

| File               | What                                                                                                                                                                                                                                                                                                                                                       | When to read                                                          |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `SKILL.md`         | Autoload context, organised by what the reader is doing: how agents fail, invariants, writing the text, growth and removal, before you commit an edit, patch-mode invocation. **The principles live here, not in `steps.md`** — patch mode assumes they are already in context. Everything here is paid in every session the description triggers, so length is the governing constraint | Editing the principles, the description that drives autoload, or the patch-mode invocation pointer |
| `experiments.md`   | The measurement loop, split out because most readers of `SKILL.md` are editing a prompt rather than measuring one: observability, implicit-guidance justification, recognition before enforcement, pass-percentage, falsifiable conclusions, one-question-per-iteration, don't-run-the-final-case, compare-traces. Referenced from `SKILL.md` and from `prompt-tests/CLAUDE.md` | Running cases against a prompt edit, or reading the transcripts of one |
| `steps.md`         | Patch-mode prompts. All steps separated by `<!-- step N: name -->`. Step 1 deliberately does NOT repeat the principles from `SKILL.md`. Cross-references into `SKILL.md` are by rule name, never by line number                                                                                                                                              | Editing step instructions                                             |
| `test-requests.md` | Worked example of the full 12-step patch-mode workflow on one concrete task; shape-of-output reference. Re-run on its example task after editing `steps.md` and replace the transcript. **Do not copy content from this file into `steps.md` — it would overfit the prompts to the example.**                                                              | Editing `steps.md`; checking that an edit actually changes behaviour  |

Python code: `scripts/skills/prompt_engineer_v2/do.py`

## Naming

Folder is `prompt-engineer-v2`; the Python module is `prompt_engineer_v2` (underscore form is required by `agent-tools skill <module>`). Both must stay in sync with `do.py`'s `STEPS_FILE` path constant.

## Why the statement-form lesson is not in `SKILL.md`

`notes/workers-bullet-hint-in-fact-position.md` argues that a claim written in fact position is read as usable for any action, and that a claim safe for one use should be written as a dependency instead. None of it is in `SKILL.md`, deliberately.

A probe on 2026-09-15 gave nine opus readers a compression task whose fixture planted a dependency in fact position, under three arms: the file as it then stood, plus a ~115-word principle, plus a ~300-word role taxonomy. The taxonomy arm stated the dependency form verbatim with a worked example and 0/3 readers used it; the short arm caused 3/3 readers to invent a prohibition the source did not contain, against 0/3 in both other arms. Adding either body is enforcement on a failure the readers did not perceive, which `experiments.md` rules out. A bare pointer was drafted in their place and also cut: it named no trigger and its only content was a path a reader outside this repository cannot open, so it fired zero times — the shape `SKILL.md`'s own "Rules need triggers" rule condemns.

What the probe did not separate: whether the form is unrecognisable to writers, or redundant once the derivation is stated. What would change this decision: a measurement showing some wording of the lesson changes what a writer produces, or a downstream-reader arm of the dependency form, which the parent note also lacks. Arms, fixture, grades and the nine outputs: `notes/workers-bullet-hint-in-fact-position/probe-statement-form-2026-09-15.md`.

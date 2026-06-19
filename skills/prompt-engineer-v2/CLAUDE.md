# prompt-engineer-v2/

Autoloading prompt-engineering context. `SKILL.md` contains the principles and suggestions that load whenever the agent is working on prompts, instructions, agent definitions, or other LLM-context text. The 12-step "patch mode" script under `steps.md` is invoked only on user request or for complex edits.

## Files

| File               | What                                                                                                                                                                                                                                                                                                                                                       | When to read                                                          |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `SKILL.md`         | Autoload context: 11 principles + additional suggestions; brief patch-mode invocation block. **The principles live here, not in `steps.md`** — patch mode assumes they are already in context.                                                                                                                                                              | Editing the principles, the description that drives autoload, or the patch-mode invocation pointer |
| `steps.md`         | Patch-mode prompts. All steps separated by `<!-- step N: name -->`. Step 1 deliberately does NOT repeat the principles from `SKILL.md`.                                                                                                                                                                                                                     | Editing step instructions                                             |
| `test-requests.md` | Worked example of the full 12-step patch-mode workflow on one concrete task; shape-of-output reference. Re-run on its example task after editing `steps.md` and replace the transcript. **Do not copy content from this file into `steps.md` — it would overfit the prompts to the example.**                                                              | Editing `steps.md`; checking that an edit actually changes behavior   |

Python code: `scripts/skills/prompt_engineer_v2/do.py`

## Naming

Folder is `prompt-engineer-v2`; the Python module is `prompt_engineer_v2` (underscore form is required by `agent-tools skill <module>`). Both must stay in sync with `do.py`'s `STEPS_FILE` path constant.

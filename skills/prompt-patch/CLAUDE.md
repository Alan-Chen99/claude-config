# prompt-patch/

Structured prompt change workflow. Script-based 12-step pipeline.

## Files

| File               | What                                                                                            | When to read                                       |
| ------------------ | ----------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `SKILL.md`         | Skill invocation                                                                                | Using this skill                                   |
| `steps.md`         | All step prompts, separated by `<!-- step N: name -->`                                          | Editing step instructions                          |
| `test-requests.md` | Worked example of the full 12-step workflow on one concrete task; shape-of-output reference. Re-run on its example task after editing `steps.md` and replace the transcript. **Do not copy content from this file into `steps.md` — it would overfit the prompts to the example.** | Editing `steps.md`; checking that an edit actually changes behavior |

Python code: `scripts/skills/prompt_patch/do.py`

# prompt-patch/

Structured prompt change workflow. Script-based 12-step pipeline.

## Files

| File               | What                                                                                            | When to read                                       |
| ------------------ | ----------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `SKILL.md`         | Skill invocation                                                                                | Using this skill                                   |
| `steps.md`         | All step prompts, separated by `<!-- step N: name -->`                                          | Editing step instructions                          |
| `test-requests.md` | Generic rubric for evaluating prompt-patch workflow runs + a test task with a brief answer key. After editing `steps.md`, run the workflow on the test task and score against the rubric. The rubric is generic; the answer key is task-specific. **Do not copy answer-key content into `steps.md`.** | Editing `steps.md`; verifying a change does not regress |

Python code: `scripts/skills/prompt_patch/do.py`

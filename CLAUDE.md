# claude-config

This repository is forked from `solatis/claude-config`; most code is from upstream.

---

Claude Code configuration: skills, agents, and conventions for structured LLM-assisted development.

## Files

| File                      | What                                                        | When to read                                  |
| ------------------------- | ----------------------------------------------------------- | --------------------------------------------- |
| `README.md`               | Workflow philosophy, usage guide                            | Understanding the approach, getting started   |
| `patch-upstream-paths.sh` | Patches `.claude/` → `~/.claude/` paths after upstream sync | After pulling/rebasing upstream changes       |
| `pyproject.toml`          | Python project config                                       | Adding dependencies, modifying build settings |
| `.gitignore`              | Git ignore patterns                                         | Adding new generated/temp files to ignore     |
| `.envrc`                  | direnv environment config                                   | Modifying shell environment for development   |
| `settings.json`           | Claude Code user settings                                   | Modifying hooks, statusline, permissions      |

## Subdirectories

| Directory        | What                                         | When to read                                      |
| ---------------- | -------------------------------------------- | ------------------------------------------------- |
| `skills/`        | Invocable skills (planner, deepthink, etc.)  | Using or modifying skills, adding new skills      |
| `agents/`        | Sub-agent definitions (developer, architect) | Customizing agent behavior, understanding roles   |
| `conventions/`   | Documentation and code quality standards     | Writing documentation, understanding coding rules |
| `plans/`         | Plan storage directory                       | Reviewing or executing existing plans             |
| `output-styles/` | Output formatting styles                     | Customizing Claude's output format                |
| `hooks/`         | ntfy notification hooks for Claude Code      | Setting up notifications, debugging hooks         |
| `.github/`       | GitHub workflows and config                  | Modifying CI/CD, GitHub-specific settings         |

### `docs/`

| Path                                       | What                                          | When to read                                            |
| ------------------------------------------ | --------------------------------------------- | ------------------------------------------------------- |
| `system-prompt-anatomy.md`                 | Simplified overview of system prompt assembly | Quick orientation, understanding prompt structure       |
| `system-prompt-anatomy-source-verified.md` | Detailed anatomy with function references     | Debugging context loading, source-level understanding   |
| `system-prompt-snapshot/`                  | Captured system prompts and full API requests | Comparing prompt versions, understanding API parameters |

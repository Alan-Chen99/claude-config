# claude-config

This repository is forked from `solatis/claude-config`; most code is from upstream.

---

Claude Code configuration: skills, agents, and conventions for structured LLM-assisted development.

## Files

| File                      | What                                                        | When to read                                  |
| ------------------------- | ----------------------------------------------------------- | --------------------------------------------- |
| `README.md`               | Workflow philosophy, usage guide                            | Understanding the approach, getting started   |
| `patch-upstream-paths.sh` | Patches `.claude/` → `~/.claude/` paths after upstream sync | After pulling/rebasing upstream changes       |
| `pyproject.toml`          | Python project config, entry points for cc-pretty etc.      | Adding dependencies, modifying build settings |
| `.gitignore`              | Git ignore patterns                                         | Adding new generated/temp files to ignore     |
| `.envrc`                  | direnv environment config                                   | Modifying shell environment for development   |
| `settings.json`           | Claude Code user settings                                   | Modifying hooks, statusline, permissions      |

## Subdirectories

| Directory          | What                                                    | When to read                                      |
| ------------------ | ------------------------------------------------------- | ------------------------------------------------- |
| `agent-tools/`     | Rust binary (`agent-tools`) wrapping skill/tool calls   | Modifying CLI wrappers, adding new commands       |
| `src/claude_config/` | Python package: cc-pretty, cc-workflow, custom tools  | Modifying Python tooling, adding new tools        |
| `skills/`          | Invocable skills (planner, deepthink, etc.)             | Using or modifying skills, adding new skills      |
| `agents/`          | Sub-agent definitions (developer, architect)            | Customizing agent behavior, understanding roles   |
| `conventions/`     | Documentation and code quality standards                | Writing documentation, understanding coding rules |
| `plans/`           | Plan storage directory                                  | Reviewing or executing existing plans             |
| `output-styles/`   | Output formatting styles                                | Customizing Claude's output format                |
| `hooks/`           | ntfy notification hooks for Claude Code                 | Setting up notifications, debugging hooks         |
| `scripts/`         | Standalone scripts (intercept proxy, launchers)         | Running or modifying utility scripts              |
| `.github/`         | GitHub workflows and config                             | Modifying CI/CD, GitHub-specific settings         |

### `agent-tools/`

Rust binary wrapping skill script and Python tool invocations. Subcommands:

- `agent-tools skill <mod> [args]` — run a skill script via `uv run python3 -m skills.<mod>`
- `agent-tools cc-pretty [args]` — pretty-print Claude Code JSONL session logs
- `agent-tools cc-workflow [args]` — extract sub-agent workflow summary

Root resolution (no dependency on binary location):
1. `CLAUDE_CONFIG_ROOT` env var
2. Default: derived from `~/.claude/skills` symlink target (i.e. `/repos/claude-config`)

Build: `cd agent-tools && cargo build --release`. Installed as a symlink at `~/.local/bin/agent-tools` → `<repo>/agent-tools/target/release/agent-tools` by `hooks/install.sh`.

**Worktrees must NEVER run `hooks/install.sh`** — the symlink must always point to the canonical repo's binary. Worktrees that install their own build will break all other sessions when the worktree is deleted.

Testing from a worktree without installing:
```bash
cd agent-tools && cargo build --release
CLAUDE_CONFIG_ROOT=/path/to/worktree ./target/release/agent-tools skill <module> [args...]
```

### `src/claude_config/`

Python package installed editable in `.venv` as `claude_config`. Contains custom (non-upstream) Python tools:

| Module                          | What                                           | CLI entry point       |
| ------------------------------- | ---------------------------------------------- | --------------------- |
| `claude_config.cc_pretty`       | Parse and render Claude Code JSONL session logs | `cc-pretty`           |
| `claude_config.cc_workflow`     | Sub-agent workflow extraction and analysis      | `cc-workflow-extract` |

### `skills/copy-writing-style/`

Style-matched content generation from any style reference file. 3-phase iterative workflow: (1) extract ranked distinguishing features, (2) draft targeting top features, (3) iterate with self-critique loop (max 3 rounds). Uses `steps.md` with `<!-- step N -->` markers, minimal Python in `scripts/skills/copy_writing_style/do.py`.

### `docs/`

| Path                                       | What                                          | When to read                                            |
| ------------------------------------------ | --------------------------------------------- | ------------------------------------------------------- |
| `system-prompt-anatomy.md`                 | Simplified overview of system prompt assembly | Quick orientation, understanding prompt structure       |
| `system-prompt-anatomy-source-verified.md` | Detailed anatomy with function references     | Debugging context loading, source-level understanding   |
| `system-prompt-snapshot/`                  | Captured system prompts and full API requests | Comparing prompt versions, understanding API parameters |
| `tool-token-limits.md`                     | Token counting, truncation, and size limits per tool | Understanding tool output constraints, debugging limits |

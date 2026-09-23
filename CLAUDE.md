# claude-config

Claude Code configuration: skills, agents, prompts, and conventions for structured
LLM-assisted development. Forked from `solatis/claude-config`; most code is upstream.

Detail lives in each directory's own `CLAUDE.md` — not auto-loaded, so open the one for
the directory you are about to touch.

## Files

| File | What | When to read |
| --- | --- | --- |
| `README.md` | Public-facing: the fork's ideas with links to their evidence, upstream attribution, install and tests | First orientation; before pointing anyone at the repository |
| `install.sh` | Symlinks config into `~/.claude/` and units into `~/.config/systemd/user/`, builds `agent-tools`, puts `claude.sh` on PATH | Installing the config |
| `settings.json` | Claude Code user settings: hooks, statusline, permissions, `env`. Keys documented elsewhere: git policy (`includeGitInstructions`, `attribution`) in `sys_prompt/CLAUDE.md`, `CLAUDE_CODE_FORK_SUBAGENT` in `docs/subagent-backgrounding.md`, `TELEGRAM_HITL_STATE_DIR` in `src/claude_config/CLAUDE.md` | Modifying hooks, statusline, permissions, env |
| `statusline.sh` | Status line wired up via `settings.json`; its open-tasks row is `agent-tools ps --format statusline` | Customizing the status line |
| `patch-upstream-paths.sh` | Patches `.claude/` → `~/.claude/` paths after upstream sync | After an upstream sync |
| `pyproject.toml` | Python project config, entry points | Adding dependencies, modifying build settings |
| `.env` / `.env.example` | Unified config (NTFY URL, OpenRouter, Anthropic token-count) | Setting up secrets — see `.env.example` |

## Subdirectories

| Directory | What | When to read |
| --- | --- | --- |
| `agent-tools/` | Rust binary `agent-tools`: every subcommand, the wrapped-run status channel, the hooks, root resolution, build | Running or modifying a subcommand; building it; reading a run status line |
| `src/claude_config/` | Python package: session-log renderers, `count-tokens`, the hooks, the Telegram proxy | Modifying Python tooling; the Telegram channel on this machine |
| `skills/` | Invocable skills (planner, deepthink, …) and the shared script framework | Using, modifying or adding a skill |
| `agents/` | Sub-agent definitions (developer, architect, …) | Customizing agent behavior |
| `sys_prompt/` | Full replacement prompts loaded via `--system-prompt-file`, not inherited by background sessions | Editing the launcher's system prompt — read `sys_prompt/CLAUDE.md` first |
| `output-styles/` | Output formatting styles — the only prompt customization that survives a background handoff | Customizing output format; a rule that must hold in every session |
| `scripts/` | `claude.sh` launcher, MITM proxy, drift and coupling guards, prompt-test runners | Running or modifying utility scripts |
| `prompt-tests/` | Runner-neutral prompt evaluation cases | Running or grading prompt evaluations |
| `conventions/` | Documentation and code-quality standards; `documentation.md` governs every CLAUDE.md here | Writing docs, understanding coding rules |
| `docs/` | Reference material on Claude Code's own behaviour, captured prompts, design records | Investigating cc behavior; after an upgrade |
| `notes/` | Long-form investigation write-ups — measured evidence and root cause, one behaviour each. Dated records: never rewritten to match later changes | Before re-investigating a known failure mode; after one worth keeping |
| `plans/` | Plan storage | Reviewing or executing a plan |
| `systemd/` | systemd **user** units, symlinked by `install.sh` and enabled by hand — `telegram-hitl.service` runs the Telegram proxy | Adding a long-running service; diagnosing one that is `failed` |
| `.claude/` | Repo-local config; project skills `prompt-tests` and `update-claude-code` (post-upgrade runbook and what a release can break here) | Adding repo-local skills or hooks; after a Claude Code upgrade |
| `.github/` | GitHub workflows and config | Modifying CI/CD |

## Build and test

```bash
cd agent-tools && cargo build --release   # then: cargo test
UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/$(basename $PWD) uv run pytest
scripts/check-prompt-coupling.sh         # emitted strings vs the prompt
```

## Agent Policy

- **Worktrees must NEVER run `install.sh`.** The `~/.claude` symlinks must always point at
  the canonical checkout; a worktree that installs its own build breaks every other session
  when it is deleted. Build in place — `agent-tools/CLAUDE.md`, "Testing from a worktree".
- `agent-tools` takes its root from compile time and has no `--root` override.
  `CLAUDE_CONFIG_ROOT` only asserts that root; disagree with it, or leave it unset for a
  non-default build, and every subcommand exits non-zero instead of answering with another
  checkout's config.
- Python venvs live at `~/.claude/venvs/<repo-basename>/` (`UV_PROJECT_ENVIRONMENT`), never
  in the source tree, so host and container sessions don't fight over one `.venv`.
- After a Claude Code upgrade, work through `.claude/skills/update-claude-code`: many files
  here are pinned to a cc version and go stale with no signal.

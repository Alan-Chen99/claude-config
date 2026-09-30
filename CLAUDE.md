# claude-config

Claude Code configuration: skills, agents, prompts, and conventions for structured
LLM-assisted development. Forked from `solatis/claude-config`; most code is upstream.

Detail lives in each directory's own `CLAUDE.md` — not auto-loaded, so open the one for
the directory you are about to touch.

## Files

| File | What | When to read |
| --- | --- | --- |
| `README.md` | Public-facing: the fork's ideas with links to their evidence, upstream attribution, install and tests | First orientation; before pointing anyone at the repository |
| `install.sh` | Builds and symlinks the config into `~/.claude/`, `~/.config/opencode`, `~/.config/systemd/user/` and `~/.local/bin/` (`README.md`, *Install*). Links, not copies: a canonical-checkout edit is live with no re-install, a worktree's is live nowhere; refuses a worktree, or a destination that is not already a symlink | Installing the config; deciding whether an edit needs deploying |
| `settings.json` | Claude Code user settings: hooks, statusline, permissions, `env`. Keys documented elsewhere: git policy (`includeGitInstructions`, `attribution`) in `sys_prompt/CLAUDE.md`, `CLAUDE_CODE_FORK_SUBAGENT` in `docs/subagent-backgrounding.md`, `TELEGRAM_HITL_STATE_DIR` in `src/claude_config/CLAUDE.md`, `autoCompactWindow` in `docs/total-tokens-reminder-trial.md` | Modifying hooks, statusline, permissions, env |
| `statusline.sh` | Status line wired up via `settings.json`; its open-tasks row is `agent-tools ps --format statusline` | Customizing the status line |
| `patch-upstream-paths.sh` | Patches `.claude/` → `~/.claude/` paths after upstream sync | After an upstream sync |
| `pyproject.toml` | Python project config, entry points | Adding dependencies, modifying build settings |
| `.env` / `.env.example` | Unified config (NTFY URL, OpenRouter, Anthropic token-count) | Setting up secrets — see `.env.example` |
| `doc-budget.toml` | Token caps for every tracked `.md`, by how the text reaches a context | Adding or growing a doc; a group over cap |

## Subdirectories

| Directory | What | When to read |
| --- | --- | --- |
| `agent-tools/` | Rust binary `agent-tools`: every subcommand, the wrapped-run status channel, the hooks, root resolution, build | Running or modifying a subcommand; building it; reading a run status line |
| `src/claude_config/` | Python package: session-log renderers, `count-tokens`, the hooks, the Telegram proxy | Modifying Python tooling; the Telegram channel on this machine |
| `skills/` | Invocable skills (planner, deepthink, …) and the shared script framework | Using, modifying or adding a skill |
| `agents/` | Sub-agent definitions (developer, architect, …) | Customizing agent behavior |
| `sys_prompt/` | Full replacement prompts loaded via `--system-prompt-file`, not inherited by background sessions | Editing the launcher's system prompt — read `sys_prompt/CLAUDE.md` first |
| `output-styles/` | Output formatting styles — the only prompt customization that survives a background handoff | Customizing output format; a rule that must hold in every session |
| `scripts/` | `claude.sh` launcher, its `kimi.sh` and `zai.sh` provider-backed siblings, MITM proxy, drift and coupling guards, prompt-test runners | Running or modifying utility scripts |
| `prompt-tests/` | Runner-neutral prompt evaluation cases | Running or grading prompt evaluations |
| `conventions/` | Documentation and code-quality standards; `documentation.md` governs every CLAUDE.md here | Writing docs, understanding coding rules |
| `docs/` | Reference material on Claude Code's own behaviour, captured prompts, design records | Investigating cc behavior; after an upgrade |
| `notes/` | Long-form investigation write-ups — measured evidence and root cause, one behaviour each. Dated records, never rewritten to match later changes; `ralph-loop3-writing-for-agents/` is a closed archive with rules in its own `CLAUDE.md` | Before re-investigating a known failure mode; after one worth keeping |
| `plans/` | Plan storage | Reviewing or executing a plan |
| `systemd/` | systemd **user** units, symlinked by `install.sh` and enabled by hand — `telegram-hitl.service` runs the Telegram proxy | Adding a long-running service; diagnosing one that is `failed` |
| `.claude/` | Repo-local config; project skills `prompt-tests` and `update-claude-code`; `skills/session-analysis-wip` is a relative link that invokes **this** checkout's `skills/session-analysis` — the plain `session-analysis` skill is always the installed copy from `/repos/claude-config` | Adding repo-local skills or hooks; after a Claude Code upgrade; invoking a skill you are editing from a worktree |
| `.github/` | GitHub workflows and config | Modifying CI/CD |

## Build and test

```bash
cd agent-tools && cargo build --release   # then: cargo test
UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/$(basename $PWD) uv run pytest
scripts/check-prompt-coupling.sh         # emitted strings vs the prompt
scripts/check-prompt-rationale.sh        # every sys_prompt/CLAUDE.md section vs the prompt
agent-tools doc-budget                   # every tracked .md against doc-budget.toml
```

## Agent Policy

- `agent-tools` takes its root from compile time and has no `--root` override.
  `CLAUDE_CONFIG_ROOT` only asserts that root; disagree with it, or leave it unset for a
  non-default build, and every subcommand exits non-zero instead of answering with another
  checkout's config.
- Python venvs live at `~/.claude/venvs/<repo-basename>/` (`UV_PROJECT_ENVIRONMENT`), never
  in the source tree, so host and container sessions don't fight over one `.venv`.
- After a Claude Code upgrade, work through `.claude/skills/update-claude-code`: many files
  here are pinned to a cc version and go stale with no signal.
- `agent-tools doc-budget` over cap: cut that group to 80% of cap in the same change —
  consolidation only; a group over when you arrived is debt to name, not pay in passing
  (`conventions/documentation.md`, *Documentation budget*).

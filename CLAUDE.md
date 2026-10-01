# claude-config

Claude Code configuration: skills, agents, prompts and conventions (forked from
`solatis/claude-config`). Each directory's own `CLAUDE.md` is not auto-loaded — open the one
for the directory you are about to touch.

## Files

| File | What | When to read |
| --- | --- | --- |
| `README.md` | Public-facing: the fork's ideas and evidence, install, tests | First orientation |
| `install.sh` | Symlinks the config into `~/.claude/`, `~/.config/`, `~/.local/bin/`: a canonical-checkout edit is live at once, a worktree's nowhere | Installing; deciding whether an edit needs deploying |
| `settings.json` | User settings: hooks, statusline, permissions, `env`. Keys governed elsewhere: `includeGitInstructions`/`attribution` in `sys_prompt/CLAUDE.md`, `CLAUDE_CODE_FORK_SUBAGENT` in `docs/subagent-backgrounding.md`, `TELEGRAM_HITL_STATE_DIR` in `src/claude_config/CLAUDE.md`, `autoCompactWindow` in `docs/total-tokens-reminder-trial.md`, `enableArtifact` in `notes/artifact-tool-roster-cost.md`, `feedbackDrafts`/`permissions.deny`/`skillOverrides`/the connector and Chrome `env` cuts in `plans/2026-09-30-session-start-token-cuts.md`. Top-level key order is Claude Code's settings-schema order, which it rewrites the file into on any `/config` change: put a new key anywhere and run `.claude/skills/update-claude-code/settings-order.py --write` | Modifying hooks, statusline, permissions, env; adding any key |
| `statusline.sh` | Status line; open-tasks row from `agent-tools ps --format statusline` | Customizing the status line |
| `patch-upstream-paths.sh` | Patches `.claude/` → `~/.claude/` paths | After an upstream sync |
| `pyproject.toml` | Python project config | Adding dependencies |
| `.env` / `.env.example` | Secrets: NTFY URL, OpenRouter, Anthropic token-count | Setting up secrets |
| `doc-budget.toml` | Token caps for every tracked `.md` | Adding or growing a doc |

## Subdirectories

| Directory | What | When to read |
| --- | --- | --- |
| `agent-tools/` | Rust binary: subcommands, the wrapped-run status channel, hooks | Running or modifying a subcommand; reading a run status line |
| `src/claude_config/` | Python package: session-log renderers, `count-tokens`, hooks, Telegram proxy | Modifying Python tooling |
| `skills/` | Invocable skills and the shared script framework | Using, modifying or adding a skill |
| `agents/` | Sub-agent definitions | Customizing agent behavior |
| `sys_prompt/` | Full replacement prompts (`--system-prompt-file`), not inherited by background sessions | Editing the launcher's system prompt; read `sys_prompt/CLAUDE.md` first |
| `output-styles/` | Output styles — the one prompt customization that survives a background handoff | A rule that must hold in every session |
| `scripts/` | `claude.sh` launcher and its `kimi.sh`/`zai.sh` siblings, MITM proxy, drift and coupling guards, prompt-test runners | Running or modifying a script |
| `prompt-tests/` | Prompt evaluation cases | Running or grading them |
| `conventions/` | Documentation and code-quality standards; `documentation.md` governs every CLAUDE.md | Writing docs |
| `docs/` | Reference material on Claude Code's behaviour, captured prompts, design records | Investigating cc behavior; after an upgrade |
| `notes/` | Investigation write-ups, one behaviour each: dated evidence and root cause, never rewritten (`ralph-loop3-writing-for-agents/` is a closed archive) | Before re-investigating a known failure mode; after one worth keeping |
| `plans/` | Plan storage | Reviewing or executing one |
| `systemd/` | systemd **user** units, enabled by hand; `telegram-hitl.service` runs the Telegram proxy | Adding a service; diagnosing one that is `failed` |
| `.claude/` | Repo-local config: project skills `prompt-tests`, `update-claude-code`; `skills/session-analysis-wip` is **this** checkout's `session-analysis` (the plain skill is the installed copy) | Repo-local skills or hooks; after a Claude Code upgrade; a skill you are editing from a worktree |
| `.github/` | GitHub workflows | CI/CD |

## Build and test

```bash
cd agent-tools && cargo build --release && cargo test
UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/$(basename $PWD) uv run pytest
scripts/check-prompt-coupling.sh
scripts/check-prompt-rationale.sh
agent-tools doc-budget
```

## Agent Policy

- `agent-tools` takes its root from compile time; `CLAUDE_CONFIG_ROOT` only asserts it (a
  disagreeing or, for a non-default build, unset value exits non-zero).
- Python venvs: `~/.claude/venvs/<repo-basename>/` (`UV_PROJECT_ENVIRONMENT`), never in the
  source tree.
- After a Claude Code upgrade, work through `.claude/skills/update-claude-code`: many files here
  are pinned to a cc version and go stale silently.
- `agent-tools doc-budget` over cap: cut that group to 80% of cap in the same change,
  consolidation only; a group over when you arrived is debt to name, not pay in passing
  (`conventions/documentation.md`).

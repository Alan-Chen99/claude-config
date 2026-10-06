# claude-config

Claude Code configuration: skills, agents, prompts and conventions (forked from
`solatis/claude-config`). A directory's own `CLAUDE.md` is not auto-loaded — open it before touching the directory.

## Files

| File | What | When to read |
| --- | --- | --- |
| `README.md` | Public-facing: the fork's ideas and evidence, install, tests | First orientation |
| `install.sh` | Symlinks the config into `~/.claude/`, `~/.config/`, `~/.local/bin/`: a canonical-checkout edit is live at once, a worktree's nowhere | Installing; deciding whether an edit needs deploying |
| `settings.json` | User settings: hooks, statusline, permissions, `env`. Keys governed elsewhere: `includeGitInstructions`/`attribution` in `sys_prompt/CLAUDE.md`, `CLAUDE_CODE_FORK_SUBAGENT` in `docs/subagent-backgrounding.md`, `TELEGRAM_HITL_STATE_DIR` in `src/claude_config/CLAUDE.md`, `BASH_MAX_TIMEOUT_MS` in `skills/telegram-hitl/README.md`, `autoCompactWindow` in `docs/total-tokens-reminder-trial.md`, `enableArtifact` in `notes/artifact-tool-roster-cost.md`, `switchModelsOnFlag` in `notes/cc-2.1.289-refusal-fallback-write.md`, `feedbackDrafts`/`permissions.deny`/`skillOverrides`/the connector and Chrome `env` cuts in `plans/2026-09-30-session-start-token-cuts.md`, `syncClaudeAi*` in the `update-claude-code` skill. Key order is Claude Code's schema order (any `/config` change rewrites the file into it): add a key anywhere, then run `.claude/skills/update-claude-code/settings-order.py --write` | Modifying hooks, statusline, permissions, env; adding any key |
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
| `notes/` | Investigation write-ups, one behaviour each: dated evidence and root cause, never rewritten | Before re-investigating a known failure mode; after one worth keeping |
| `plans/` | Plan storage | Reviewing or executing one |
| `systemd/` | systemd **user** units, enabled by hand; `telegram-hitl.service` runs the Telegram proxy | Adding a service; diagnosing one that is `failed` |
| `.claude/` | Repo-local config: project skills `prompt-tests`, `update-claude-code`; `skills/session-analysis-wip` is **this** checkout's `session-analysis` (the plain skill is the installed copy) | Repo-local skills or hooks; after a Claude Code upgrade; a skill you are editing from a worktree |
| `.github/` | GitHub workflows | CI/CD |

## Build and test

```bash
(cd agent-tools && cargo build --release && cargo test)
export UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/$(basename $PWD)
uv run pytest
uv run doc-budget
scripts/check-prompt-coupling.sh
scripts/check-prompt-rationale.sh
```

## Agent Policy

- `agent-tools` takes its root from compile time; `CLAUDE_CONFIG_ROOT` only asserts it (a
  disagreeing or, for a non-default build, unset value exits non-zero).
- Python venvs: `~/.claude/venvs/<repo-basename>/` (`UV_PROJECT_ENVIRONMENT`), never in the
  source tree.
- After a Claude Code upgrade, work through `.claude/skills/update-claude-code`: many files here pin a cc version and go stale silently.
- `uv run doc-budget` over cap: cut that group to 80% of cap in the same change,
  consolidation only; a group over when you arrived is debt to name, not pay in passing
  (`conventions/documentation.md`).
- A `[held.files]` row in `doc-budget.toml` falls due with the next task on what its file
  is about — for a `CLAUDE.md` or `SKILL.md` its directory, a task on any part of which
  counts; for an agent body that agent; for a doc, note, spec or plan the subproject,
  subcommand or behaviour it records; a tree-wide sweep is about none — whether or not
  the task edits the file: drop the row and, over the class cap, cut to 80% of it or ask
  the user for a cap. `uv run doc-budget <dir>` lists a directory's rows; the rest is in `conventions/documentation.md`.

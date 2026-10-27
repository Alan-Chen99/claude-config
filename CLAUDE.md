# claude-config

A nested `CLAUDE.md` is not auto-loaded: open it before touching its directory.

## Files

| File | What | When to read |
| --- | --- | --- |
| `README.md` | Public-facing: the fork's ideas and evidence, install, tests | First orientation |
| `install.sh` | Symlinks the config under `~/`: a canonical-checkout edit is live at once, a worktree's nowhere | Installing; deciding whether an edit needs deploying |
| `settings.json` | Hooks, statusline, permissions, `env`. Governed elsewhere: `includeGitInstructions`/`attribution` in `sys_prompt/README.md`, the subagent `CLAUDE_CODE_*` pair in `docs/subagent-backgrounding.md`, `TELEGRAM_HITL_STATE_DIR` in `src/claude_config/CLAUDE.md`, `BASH_MAX_TIMEOUT_MS` in `skills/telegram-hitl/README.md`, `autoCompactWindow` in `docs/total-tokens-reminder-trial.md`, `enableArtifact` in `notes/artifact-tool-roster-cost.md`, `switchModelsOnFlag` in `notes/cc-2.1.289-refusal-fallback-write.md`, `feedbackDrafts`/`permissions.deny`/`skillOverrides`/connector/Chrome `env` in `plans/2026-09-30-session-start-token-cuts.md`, `syncClaudeAi*` in skill `update-claude-code`. After adding a key, run `.claude/skills/update-claude-code/settings-order.py --write` | Editing any key |
| `patch-upstream-paths.sh` | Patches `.claude/` → `~/.claude/` paths | After an upstream sync |
| `pyproject.toml` | Python project config | Adding dependencies |
| `.env` / `.env.example` | Secrets: ntfy URL, OpenRouter, Anthropic token-count | Setting up secrets |
| `doc-budget.toml` | Token caps for every tracked `.md` | Adding or growing a doc |

## Subdirectories

| Directory | What | When to read |
| --- | --- | --- |
| `agent-tools/` | Rust binary: subcommands, the wrapped-run status channel, hooks | Running or modifying a subcommand; reading a run status line |
| `src/claude_config/` | Python: session-log renderers, `cc-cost`, `count-tokens`, hooks, Telegram proxy | Modifying Python tooling or the status line |
| `skills/` | Invocable skills and the shared script framework | Using, modifying or adding a skill |
| `agents/` | Sub-agent definitions | Customizing agent behavior |
| `sys_prompt/` | Full replacement prompts (`--system-prompt-file`), not inherited by background sessions | Editing the launcher's system prompt |
| `output-styles/` | The one prompt customization that survives a background handoff | A rule that must hold in every session |
| `scripts/` | Launchers, MITM proxy, drift and coupling guards, prompt-test runners | Running or modifying a script |
| `prompt-tests/` | Prompt evaluation cases | Running or grading them |
| `conventions/` | Documentation and code-quality standards | Writing docs |
| `docs/` | Claude Code behaviour references, captured prompts, design records | Investigating cc behavior; after an upgrade |
| `notes/` | Investigation write-ups, one behaviour each, dated, never rewritten | Before re-investigating a known failure mode; after one worth keeping |
| `plans/` | Plan storage | Reviewing or executing one |
| `systemd/` | **User** units, enabled by hand | Adding a service; diagnosing one that is `failed` |
| `.claude/` | Project skills `prompt-tests`, `update-claude-code`, `session-analysis-wip` (**this** checkout's `session-analysis`) | Repo-local skills; after a Claude Code upgrade; editing a skill from a worktree |
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

- `agent-tools` runs the tree it was built from: `CLAUDE_CONFIG_ROOT` only asserts
  it (a mismatch, or unset for a non-default build, exits non-zero).
- No venv in the source tree: use the `UV_PROJECT_ENVIRONMENT` above.
- `uv run doc-budget` over cap: cut that group to 80% of cap in the same change,
  consolidating only; a group already over is debt to name, not pay in passing. A
  `[held.files]` row in `doc-budget.toml` instead falls due with the next task on its
  file's subject — any part of a `CLAUDE.md` or `SKILL.md`'s directory, an agent body's agent,
  what a doc, note, spec or plan records, never a tree-wide sweep — edited or not: drop the
  row and, over the class cap, cut to 80% of it or ask the user for a cap. The rest:
  `conventions/documentation.md`.

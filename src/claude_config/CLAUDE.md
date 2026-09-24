# src/claude_config/

Python package installed editable into `~/.claude/venvs/<repo-basename>/` as `claude_config`.
Custom (non-upstream) tooling: the session-log renderers, the Claude Code hooks, and the
Telegram proxy. Most modules are reached through an `agent-tools` subcommand — that surface,
and its flags, are documented in `agent-tools/CLAUDE.md`.

## Files and modules

| Module                              | What                                            | CLI entry point                 |
| ----------------------------------- | ----------------------------------------------- | ------------------------------- |
| `cc_pretty/`                        | Parse and render Claude Code JSONL session logs; `locate.py` resolves a session or subagent id to a transcript path | `cc-pretty`                     |
| `cc_pretty/coverage.py`             | Coverage check: content the renderers fail to show at unbounded `--tool-max` | `cc-render-coverage`            |
| `cc_pretty_intercept/`              | Pretty-print one MITM intercept log file (`~/.claude/requests-log/<session>/NNNN.json`) | `cc-pretty-intercept`           |
| `opencode_pretty/`                  | Pretty-print an `opencode export` session — reuses cc-pretty's renderer and CLI flags via the shared pipeline; the local `convert.py` flattens opencode's part-based messages into cc-pretty records | `opencode-pretty`               |
| `cc_workflow/`                      | Sub-agent workflow extraction and analysis      | `cc-workflow-extract`           |
| `count_tokens.py`                   | Token count for text, two backends: the vendored local tokenizer (default) and the Anthropic `count_tokens` API (`--api`). They do not measure the same thing — `agent-tools/CLAUDE.md` carries which to use when, and how to re-vendor | `agent-tools count-tokens`      |
| `tokenizer_data/`                   | **Vendored** Qwen3.8 `tokenizer.json` plus `PROVENANCE.json` (source, revision, sha256, byte count, vocab size). Never edit by hand; the sha256 is checked on every run. Re-vendor per `agent-tools/CLAUDE.md` | Never edit directly             |
| `env_context/`                      | SessionStart hook: `# Environment (supplement)`, `# Scratchpad Directory` and `# Git status at session start` — only what cc's own env block does not carry. Mirrors cc algorithms; `.claude/skills/update-claude-code` §3.2 lists which | `agent-tools env-context`       |
| `ntfy_hook.py`                      | ntfy notification hook for Claude Code          | `agent-tools ntfy-hook`         |
| `pre_output/record.py`              | Prints the pre-output rule reminder. Records nothing: the argument is accepted and discarded, and the value is the reminder text re-surfacing at generation time | `agent-tools pre_output.record` |
| `config.py`                         | Load the repo `.env` into `os.environ` with `override=True`, so a `.env` value wins over one already in the shell | (library — `from claude_config.config import load`) |
| `telegram_hitl/`                    | Local Bot API proxy for human-in-the-loop over Telegram: one flock-guarded process owns the single `getUpdates` drain, forwards sends from any number of sessions, and appends both directions plus its own faults to one JSONL log. Lock, socket, log and offset all live in `TELEGRAM_HITL_STATE_DIR`, which is required and has no default — the directory is shared across containers whose homes differ, and a home-derived path would give each its own lock and its own drain. Sends go over `proxy.sock` in that directory rather than a port, because a port number names a different socket in every network namespace that reads it. Design: `docs/superpowers/specs/2026-09-12-telegram-hitl-design.md`; using the channel: `skills/telegram-hitl/SKILL.md` | `python -m claude_config.telegram_hitl` |

## The telegram-hitl channel on this machine

One proxy serves the host and every container, run by the systemd user service
`systemd/telegram-hitl.service`. Nothing else should start one; a session that
does is refused by the lock.

| | |
| --- | --- |
| State directory | `/home/alan/personal/telegram-hitl` — socket, log, `chat_id`, offset, lock |
| Bot token | `/home/alan/.claude/channels/telegram/.env`, mode 600 (`config.DEFAULT_TOKEN_FILE` for the service's user) |
| Who is told the path | `settings.json` `env` for Claude sessions — `docker_home/.claude/settings.json` symlinks to that file, so host and container sessions read one value; `environment:` in `personal/telegram-test/docker-compose.yml` for everything else in that container |

The state directory sits under `/home/alan/personal` because every `personal-env`
compose file bind-mounts that tree at its own path, so the same absolute path
reaches the same socket from the host and from inside any of those containers
with no volume of its own. A path under either home would not: the host's is
`/home/alan`, each container's is `/root`.

Docker here is rootless, so a container's root is the host's `alan` and the
0600 socket and log are readable from inside without widening either.

`telegram-bot@telegram-bot-skill` must stay off: it polls `getUpdates` on the
same bot token, and a second consumer is not refused by Telegram — it evicts the
first, and the channel then goes silent rather than erroring. An installed
marketplace plugin that no `enabledPlugins` entry names is never a load
candidate, so leaving it out of `settings.json` disables it exactly as `false`
does (`claude plugin list` reports both as `disabled`).

## Test

```bash
uv run pytest tests/
```

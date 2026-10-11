# src/claude_config/

Python package `claude_config`, installed editable into the repo venv: the session-log
renderers, the Claude Code hooks, and the Telegram proxy. Most modules are reached through
an `agent-tools` subcommand, whose own flags print with `agent-tools <sub> -- --help`.

## Files and modules

| Module | What | CLI entry point |
| --- | --- | --- |
| `cc_pretty/` | Parse and render Claude Code JSONL session logs; `locate.py` resolves a session or subagent id to a transcript path | `cc-pretty` |
| `cc_pretty/coverage.py` | Coverage check: content the renderers fail to show at unbounded `--tool-max`. Both families render through `run_pipeline`, so the check exercises the shipping path rather than a reconstruction of it | `cc-render-coverage` |
| `cc_pretty_intercept/`, `opencode_pretty/` | Pretty-print one MITM intercept log file or an `opencode export` session through cc-pretty's pipeline: each `convert.py` flattens its source — the capture's named regions, opencode's part-based messages — into cc-pretty records; the intercept one keys each record by its jq address, so refs stay recoverable | `cc-pretty-intercept`, `opencode-pretty` |
| `cc_replay/` | Re-send a captured API request. `proxy_module.py` loads `scripts/intercept/proxy.py` by path so the reassembler is shared without the addon importing this package — the bare `mitmdump -s proxy.py` its README documents has to keep working. `credentials.py` resolves per host and names its source; a capture never carries one | `cc-replay` |
| `cc_workflow/` | Sub-agent workflow extraction and analysis | `cc-workflow-extract` |
| `count_tokens.py`, `tokenizer_data/` | Token count for text, by the **vendored** Qwen3.8 tokenizer (default) or the Anthropic `count_tokens` API (`--api`); the two do not measure the same thing. `agent-tools/CLAUDE.md` says which to use when and how to re-vendor; never edit `tokenizer_data/` by hand, its sha256 is checked on every run | `agent-tools count-tokens` |
| `doc_budget.py` | Every tracked `.md` against the caps in `doc-budget.toml`: resolver, report, `--print-held`, and the same-session approval gate on `CLAUDE_CODE_SESSION_ID` (unset: a warning, every approval live) | `doc-budget` |
| `env_context/` | SessionStart hook for what cc's own env block lacks, the clock's zone and offset included. Mirrors cc algorithms — `.claude/skills/update-claude-code` §3.2 lists which | `agent-tools env-context` |
| `ntfy_hook.py` | ntfy notification hook for Claude Code | `agent-tools ntfy-hook` |
| `pre_output/record.py` | The `## Before response` step: the rule reminder, and the turn's JSON for `ntfy_hook`'s "Done" push | `agent-tools pre_output.record` |
| `config.py` | Load the repo `.env` into `os.environ` with `override=True`, so a `.env` value wins over one already in the shell | (library — `from claude_config.config import load`) |
| `telegram_hitl/` | Local Bot API proxy for human-in-the-loop over Telegram: one flock-guarded `getUpdates` drain, sends over `proxy.sock`, one JSONL log, all in `TELEGRAM_HITL_STATE_DIR` — required, no default (below). Design: `docs/superpowers/specs/2026-09-12-telegram-hitl-design.md`; using it: `skills/telegram-hitl/SKILL.md` | `python -m claude_config.telegram_hitl` |

## The telegram-hitl channel on this machine

One proxy serves the host and every container, run by the systemd user service
`systemd/telegram-hitl.service`; a second start is refused by the lock.

| | |
| --- | --- |
| State directory | `/home/alan/personal/telegram-hitl` — socket, log, `chat_id`, offset, lock |
| Bot token | `/home/alan/.claude/channels/telegram/.env`, mode 600 (`config.DEFAULT_TOKEN_FILE` for the service's user) |
| Who is told the path | `settings.json` `env` for Claude sessions (host and container read one file through the `docker_home/.claude` symlink); `environment:` in `personal/telegram-test/docker-compose.yml` for the rest of that container |

No default: a home-derived path differs per participant and each would start
its own drain (spec, *Crossing the container boundary*). `/home/alan/personal`
is the tree every `personal-env` compose file bind-mounts at the same absolute
path, so one spelling reaches one socket from the host and from every container.

`telegram-bot@telegram-bot-skill` stays off: it polls the same token and evicts
the drain (spec, *Prerequisites*). Having no `enabledPlugins` entry is what
disables it — a plugin no entry names is never a load candidate, exactly as
`false` (`claude plugin list` reports both as `disabled`).

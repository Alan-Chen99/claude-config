# src/claude_config/

Python package `claude_config`, installed editable into the repo venv. Most modules are
reached through an `agent-tools` subcommand, whose own flags print with `agent-tools <sub> -- --help`.

## Files and modules

| Module | What | CLI entry point |
| --- | --- | --- |
| `cc_pretty/` | Parse and render Claude Code JSONL session logs in local time; `locate.py` resolves a session or subagent id to a transcript path, which is how a subagent call's render names its agent's log | `cc-pretty` |
| `cc_pretty/coverage.py` | Coverage check: content the renderers fail to show at unbounded `--tool-max`, rendered through the shipping `run_pipeline`, never a reconstruction | `cc-render-coverage` |
| `cc_pretty_intercept/`, `opencode_pretty/` | Pretty-print one MITM intercept log file or an `opencode export` session through cc-pretty's pipeline: each `convert.py` flattens its source into cc-pretty records, the intercept one keyed by jq address | `cc-pretty-intercept`, `opencode-pretty` |
| `cc_replay/` | Re-send a captured API request. `proxy_module.py` borrows `scripts/intercept/proxy.py`'s reassembler, never the reverse (its docstring); `credentials.py` resolves per host and names its source; a capture never carries one | `cc-replay` |
| `cc_cost/` | A session's or subagent's cost per agent, priced as cc prices it (`pricing.py`), and every agent's prompt cache judged by the miss test cc applies to its main thread alone (`session.py`); `statusline.py`, the status line `settings.json` runs, logs each `rate_limits` change for `limits.py` to size the plan's windows | `agent-tools cc-cost`, `--statusline`, `--limits` |
| `cc_workflow/` | Sub-agent workflow extraction and analysis | `cc-workflow-extract` |
| `count_tokens.py`, `tokenizer_data/` | Token count for text, by the **vendored** Qwen3.8 tokenizer (default) or the Anthropic `count_tokens` API (`--api`). `agent-tools/CLAUDE.md` says which to use when and how to re-vendor; never edit `tokenizer_data/` by hand | `agent-tools count-tokens` |
| `doc_budget.py` | Every tracked `.md` against the caps in `doc-budget.toml`: resolver, report, `--print-held`, and the same-session approval gate on `CLAUDE_CODE_SESSION_ID` | `doc-budget` |
| `env_context/` | SessionStart hook for what cc's own env block lacks, the clock's zone and offset included. Mirrors cc algorithms — `.claude/skills/update-claude-code/references/inventory.md` lists which | `agent-tools env-context` |
| `ntfy_hook.py` | ntfy notification hook for Claude Code | `agent-tools ntfy-hook` |
| `pre_output/record.py` | The `## Before response` step: the rule reminder, and the turn's JSON for `ntfy_hook`'s "Done" push | `agent-tools pre_output.record` |
| `config.py` | Load the repo `.env` into `os.environ` with `override=True`, so a `.env` value wins over one already in the shell | (library — `from claude_config.config import load`) |
| `telegram_hitl/` | Local Bot API proxy for human-in-the-loop over Telegram: one flock-guarded `getUpdates` drain, sends over `proxy.sock`, one JSONL log, all in `TELEGRAM_HITL_STATE_DIR` (required, below). Design: `docs/superpowers/specs/2026-09-12-telegram-hitl-design.md`; use: `skills/telegram-hitl/SKILL.md` | `python -m claude_config.telegram_hitl` |

## The telegram-hitl channel on this machine

One proxy serves the host and every container, run by the systemd user service
`systemd/telegram-hitl.service`; a second start is refused by the lock.

| | |
| --- | --- |
| State directory | `/home/alan/personal/telegram-hitl` — socket, log, `chat_id`, offset, lock |
| Bot token | `/home/alan/.claude/channels/telegram/.env`, mode 600 (`config.DEFAULT_TOKEN_FILE` for the service's user) |
| Who is told the path | `settings.json` `env` for Claude sessions (host and container read one file through the `docker_home/.claude` symlink); `environment:` in `personal/telegram-test/docker-compose.yml` for the rest of that container |

No default: a home-derived path differs per participant, each starting its own
drain (spec, *Crossing the container boundary*). Every `personal-env` compose file
bind-mounts `/home/alan/personal` at the same path, so one spelling reaches one socket
from the host and every container.

`telegram-bot@telegram-bot-skill` stays off: it polls the same token and evicts
the drain (spec, *Prerequisites*). Having no `enabledPlugins` entry disables it as
`false` would: a plugin no entry names is never a load candidate.

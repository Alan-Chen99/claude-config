# Unified Config File for claude-config

**Date:** 2026-05-17
**Status:** approved (pending user review)

## Problem

Three secrets / config values are read by claude-config code, scattered across multiple files and fallback paths:

| Key | Used by | Read from |
|---|---|---|
| `OPENROUTER_API_KEY` | `hooks/ntfy_hook.py` | env, then `~/.config/ntfy-hook/openrouter_key` |
| `NTFY_TOPIC_URL` (or `NTFY_URL`) | `hooks/ntfy_hook.py` | env, then `~/.config/ntfy-hook/url` |
| `ANTHROPIC_API_KEY` (renamed to `ANTHROPIC_TOKEN_COUNT_API_KEY` — see Design) | `docs/system-prompt-snapshot/{capture,regenerate}.py` (via Anthropic SDK) | env only |

The existing `hooks/.env.example` documents 2 of the 3. The third (`ANTHROPIC_API_KEY`) is undocumented in any example file. Users (the repo owner) keep `OPENROUTER_API_KEY` in `/workspace/.env` and the NTFY values in `~/.config/ntfy-hook/`. That's three different filesystem locations for three keys.

## Goal

One config file at `/repos/claude-config/.env` that holds all three values. Code reads from there only — no `~/.config/ntfy-hook/` fallback, no implicit shell-env lookup. The `.env` file overrides any preexisting shell env.

## Design

### File

**`/repos/claude-config/.env`** — gitignored. Standard dotenv format:

```
NTFY_TOPIC_URL=https://ntfy.sh/...
OPENROUTER_API_KEY=sk-or-...
ANTHROPIC_TOKEN_COUNT_API_KEY=sk-ant-...
```

**`/repos/claude-config/.env.example`** — committed. Same keys with placeholder values and a one-line comment per key explaining its purpose.

`ANTHROPIC_TOKEN_COUNT_API_KEY` is deliberately not named `ANTHROPIC_API_KEY` to avoid collision with the SDK's default env var: a user running general Claude API workloads from the same shell often has `ANTHROPIC_API_KEY` set for their main account, and we don't want claude-config's token-counting key to silently override or be overridden by it. Snapshot scripts must therefore pass the key explicitly to the SDK constructor (see Snapshot scripts section).

### Loader

**`src/claude_config/config.py`** — single small module:

```python
"""Load /repos/claude-config/.env into os.environ. Call at startup."""
from pathlib import Path
from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

def load() -> None:
    """Load .env, overriding any preexisting env values."""
    load_dotenv(ENV_FILE, override=True)
```

Add `python-dotenv` to `pyproject.toml` dependencies. The Anthropic SDK auto-reads `ANTHROPIC_API_KEY` from `os.environ`, so loading once at startup suffices for all consumers.

### Move ntfy_hook into the package

**`hooks/ntfy_hook.py` → `src/claude_config/ntfy_hook.py`** (single file, no submodules).

Changes inside the moved file:
- Add `from claude_config.config import load; load()` at module top.
- Delete the `get_topic_url()` / `get_api_key()` fallback functions that read `~/.config/ntfy-hook/{url,openrouter_key}`. Replace with `os.environ["NTFY_TOPIC_URL"]` / `os.environ["OPENROUTER_API_KEY"]` direct reads. If `NTFY_TOPIC_URL` is missing, the hook exits 0 silently (matches current behavior — notifications are an opt-in feature). If `OPENROUTER_API_KEY` is missing, the notification body shows `[err] No API key (set OPENROUTER_API_KEY in /repos/claude-config/.env)` (also matches current behavior, with updated path in the message).
- Change `LOG_PATH` from `~/.claude/hooks/ntfy_hook.log` to `~/.cache/claude-config/ntfy_hook.log`. Create the parent dir on import.
- The `NTFY_URL` alias env var (legacy second name) is dropped — only `NTFY_TOPIC_URL` is read.

### New Rust subcommand `agent-tools ntfy-hook`

In `agent-tools/src/main.rs`, add a subcommand mirroring the existing `cc-pretty` / `cc-workflow` pattern: resolve venv via the existing `UV_PROJECT_ENVIRONMENT` logic, then exec `python3 -m claude_config.ntfy_hook` with the forwarded args.

### Update `settings.json`

All four hook invocations change:

```diff
- "command": "python3 ~/.claude/hooks/ntfy_hook.py --action notify --type permission"
+ "command": "agent-tools ntfy-hook --action notify --type permission"
```

(Same change for `--action notify --type idle`, `--action notify --type question`, `--action stop`, `--action cancel`. Timeouts unchanged.)

### Snapshot scripts

`docs/system-prompt-snapshot/capture.py` and `regenerate.py` add at the top, before any `anthropic.Anthropic()` construction:

```python
from claude_config.config import load
load()
```

Both scripts currently call `anthropic.Anthropic()` with no args, relying on the SDK's auto-pickup of `ANTHROPIC_API_KEY` from env. Because the renamed var is `ANTHROPIC_TOKEN_COUNT_API_KEY`, both construction sites must change to:

```python
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_TOKEN_COUNT_API_KEY"])
```

(`capture.py:113` and `regenerate.py:151`.) These scripts already run inside the project venv (they `import anthropic` directly), so the `claude_config.config` import works without further setup.

### Drop the `hooks/` directory and symlink

`hooks/` currently contains `install.sh`, `.env.example`, `ntfy_hook.py`, and a runtime log. After the refactor:

- `hooks/install.sh` → **`install.sh` at repo root**. Update its `DIRS=()` list to remove `hooks` (so `~/.claude/hooks` is no longer created as a symlink).
- `hooks/ntfy_hook.py` → moved (see above).
- `hooks/.env.example` → deleted; replaced by `/repos/claude-config/.env.example`.
- `hooks/ntfy_hook.log` → log path changes to `~/.cache/claude-config/ntfy_hook.log` (see above).
- Delete the `hooks/` directory.
- The stale `~/.claude/hooks` symlink is cleaned up by the one-time migration command block below (`rm ~/.claude/hooks`). `install.sh` does not delete the symlink itself — it only creates symlinks for entries in `DIRS=()`, so dropping `hooks` from that list silently leaves the old symlink in place until the migration command removes it.

### Update `.gitignore`

- Add `/.env` (root-level).
- Remove the now-unused `hooks/.env` and `hooks/ntfy_hook.log` lines.

### Update docs

- **`CLAUDE.md`** — remove the `hooks/` subdirectory row, add a row for the new `.env` and `.env.example`, update the `src/claude_config/` module table to include `config` and `ntfy_hook`.
- **`README.md`** — if it references the old hook path or `.env.example` location, update.

### One-time migration

A short script (or just documented commands) for the user to run once:

```bash
# Copy existing values into the new location
{
  echo "NTFY_TOPIC_URL=$(cat ~/.config/ntfy-hook/url 2>/dev/null)"
  echo "OPENROUTER_API_KEY=$(cat ~/.config/ntfy-hook/openrouter_key 2>/dev/null || grep -h '^OPENROUTER_API_KEY=' /workspace/.env | cut -d= -f2-)"
  echo "ANTHROPIC_TOKEN_COUNT_API_KEY=${ANTHROPIC_API_KEY:-}"
} > /repos/claude-config/.env

# Clean up old fallback files
rm -rf ~/.config/ntfy-hook
rm ~/.claude/hooks  # the stale symlink
```

The `OPENROUTER_API_KEY` entry in `/workspace/.env` is left alone (it may be used by tools outside claude-config). A comment in the new `.env.example` notes this is now the authoritative source for claude-config.

## Verification

After implementation:

1. `agent-tools ntfy-hook --action stop` from a stub Claude Code session → ntfy notification fires with a contextual summary.
2. `python -c "from claude_config.config import load; load(); import os; print(bool(os.environ.get('ANTHROPIC_TOKEN_COUNT_API_KEY')))"` → `True`.
3. `docs/system-prompt-snapshot/regenerate.py --list` → exits 0 (proves dotenv loaded and Anthropic client constructed with explicit `api_key=`).
4. `grep -rIn "OPENROUTER_API_KEY\|NTFY_TOPIC_URL\|ANTHROPIC_TOKEN_COUNT_API_KEY" --exclude-dir=.venv --exclude-dir=target` returns ONLY: `.env`, `.env.example`, `src/claude_config/config.py`, `src/claude_config/ntfy_hook.py`, and snapshot-script load + client-construction lines.
5. `grep -rIn "ANTHROPIC_API_KEY" --exclude-dir=.venv --exclude-dir=target` returns ONLY documentation references (e.g., the snapshot README's prose) — no code reads it anymore.
6. `ls ~/.claude/hooks 2>&1` → "No such file or directory" (symlink gone).
7. `ls hooks/ 2>&1` → "No such file or directory" (dir deleted).

## Non-goals

- Centralizing non-secret env vars (`BASH_MAX_OUTPUT_LENGTH`, `PLAN_AGENT_ROLE`, `INTERCEPT_PORT`, etc.) — those stay where they are.
- Touching `/workspace/.env` — left alone for tools outside claude-config.
- Adding new keys for features that don't exist yet.
- Migrating `CLAUDE_CODE_EFFORT_LEVEL` — that's a harness setting, not a claude-config key.

## Architecture diagram

```
/repos/claude-config/
├── .env                       (gitignored, source of truth)
├── .env.example               (committed)
├── install.sh                 (moved from hooks/)
├── settings.json              (hook commands updated to `agent-tools ntfy-hook ...`)
├── src/claude_config/
│   ├── config.py              (NEW: load() reads ../.env into os.environ)
│   └── ntfy_hook.py           (moved from hooks/, calls config.load() at top)
├── agent-tools/src/main.rs    (NEW subcommand: `ntfy-hook` → exec python3 -m claude_config.ntfy_hook)
├── docs/system-prompt-snapshot/
│   ├── capture.py             (adds `from claude_config.config import load; load()`)
│   └── regenerate.py          (same)
└── pyproject.toml             (adds python-dotenv dep)

DELETED:
├── hooks/                     (entire dir)
└── ~/.claude/hooks            (symlink removed manually post-install)
└── ~/.config/ntfy-hook/       (manual rm during migration)
```

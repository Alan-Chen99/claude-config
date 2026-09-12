"""Where the proxy's state lives and what it talks to.

Every value is environment-overridable so tests can point the proxy at a fake
Bot API and a scratch directory instead of the live channel.

State sits beside the first-party telegram plugin's directory rather than in
it: that plugin runs its own poller, and per the design's "exactly one drain"
prerequisite the two must never share anything.
"""

import os
from pathlib import Path

DEFAULT_STATE_DIR = Path.home() / ".claude" / "channels" / "telegram-hitl"
DEFAULT_TOKEN_FILE = Path.home() / ".claude" / "channels" / "telegram" / ".env"
DEFAULT_API_BASE = "https://api.telegram.org"
DEFAULT_PORT = 18420


def state_dir() -> Path:
    return Path(os.environ.get("TELEGRAM_HITL_STATE_DIR", DEFAULT_STATE_DIR))


def log_path() -> Path:
    return state_dir() / "channel.jsonl"


def offset_path() -> Path:
    return state_dir() / "offset"


def lock_path() -> Path:
    return state_dir() / "proxy.lock"


def port_path() -> Path:
    """The port actually bound, so a caller never has to guess it."""
    return state_dir() / "port"


def api_base() -> str:
    return os.environ.get("TELEGRAM_HITL_API_BASE", DEFAULT_API_BASE)


def port() -> int:
    """0 asks the kernel for a free port; the bound one lands in port_path()."""
    return int(os.environ.get("TELEGRAM_HITL_PORT", DEFAULT_PORT))


def token() -> str:
    """The bot token, from the environment or the channel's .env file.

    Parsed directly rather than through dotenv, which would load the repo's own
    .env and export into os.environ — neither of which this process wants.
    """
    from_environment = os.environ.get("TELEGRAM_BOT_TOKEN")
    if from_environment:
        return from_environment
    path = Path(os.environ.get("TELEGRAM_HITL_TOKEN_FILE", DEFAULT_TOKEN_FILE))
    for line in path.read_text().splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == "TELEGRAM_BOT_TOKEN":
            return value.strip().strip("\"'")
    raise RuntimeError(f"TELEGRAM_BOT_TOKEN is not in the environment or in {path}")

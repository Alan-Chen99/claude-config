"""Where the proxy's state lives and what it talks to.

Every value is environment-overridable so tests can point the proxy at a fake
Bot API and a scratch directory instead of the live channel.

The state directory has no default at all. The channel is shared by processes
whose homes differ — one per container, plus the host's — so a home-derived
path resolves somewhere different in each of them, and a process that missed
the variable would take its own lock, start its own drain, and seize the update
stream from the real one. Telegram does not refuse a second consumer; it evicts
the first. Refusing to guess is what keeps the single lock single.

The token file is different, and does keep a home-derived default: only the
proxy reads it, only one proxy runs, and a wrong or absent token fails loudly
at startup rather than quietly forking the channel in two.
"""

import os
from pathlib import Path

DEFAULT_TOKEN_FILE = Path.home() / ".claude" / "channels" / "telegram" / ".env"
DEFAULT_API_BASE = "https://api.telegram.org"


def state_dir() -> Path:
    directory = os.environ.get("TELEGRAM_HITL_STATE_DIR")
    if not directory:
        raise RuntimeError(
            "TELEGRAM_HITL_STATE_DIR is not set, and there is no default to fall "
            "back to: the channel is shared across homes, so a home-derived path "
            "would give each process its own lock and its own drain, and the "
            "newcomer would steal the update stream from the one already running. "
            "Point it at the one directory every participant shares.")
    return Path(directory)


def log_path() -> Path:
    return state_dir() / "channel.jsonl"


def offset_path() -> Path:
    return state_dir() / "offset"


def lock_path() -> Path:
    return state_dir() / "proxy.lock"


def socket_path() -> Path:
    """The Unix socket the forwarder serves on.

    It lives beside the lock deliberately. A caller that can see the lock can
    reach the proxy, so "the channel is up" and "I can send" are one fact rather
    than two that can disagree — which is what a host:port would make them, since
    a port number names a different endpoint in every network namespace that
    reads it.
    """
    return state_dir() / "proxy.sock"


def api_base() -> str:
    return os.environ.get("TELEGRAM_HITL_API_BASE", DEFAULT_API_BASE)


def token() -> str:
    """The bot token, from the environment or the channel's .env file.

    Parsed directly rather than through dotenv, which would load the repo's own
    .env and export into os.environ — neither of which this process wants.

    An `export` prefix is accepted and the last assignment wins, matching what a
    shell would do with the same file, so a rotated token appended to the end is
    the one used. An empty value counts as absent: a blanked token has to fail
    here rather than as an opaque 401 from Telegram.
    """
    from_environment = os.environ.get("TELEGRAM_BOT_TOKEN")
    if from_environment:
        return from_environment
    path = Path(os.environ.get("TELEGRAM_HITL_TOKEN_FILE", DEFAULT_TOKEN_FILE))
    found = ""
    for line in path.read_text().splitlines():
        key, separator, value = line.strip().removeprefix("export ").partition("=")
        if separator and key.strip() == "TELEGRAM_BOT_TOKEN" and value.strip():
            found = value.strip().strip("\"'")
    if found:
        return found
    raise RuntimeError(f"TELEGRAM_BOT_TOKEN is not in the environment or in {path}")

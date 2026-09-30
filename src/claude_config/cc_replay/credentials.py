"""Resolve a credential for a replay. A capture never carries one.

Resolution is by host, and every resolution names its source, because the two
first-party credentials do not accept the same requests. A Claude Code OAuth
token is honored only for a request carrying Claude Code's own system prompt: it
replays a capture faithfully, and tolerates edits anywhere else in the body, but
a replaced `system` comes back 429 with no `anthropic-ratelimit-unified-*`
header. An API key has no such constraint and accepts the whole captured beta
list, `claude-code-20250219` and `oauth-2025-04-20` included, so no beta is gated
to the OAuth path either. Naming the source is what lets a replay rule the
credential in or out.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

# Claude Code's own store. Home-rooted, so a replay works from a worktree,
# whose gitignored .env is absent and where no other credential resolves.
OAUTH_STORE = Path.home() / ".claude" / ".credentials.json"


@dataclass(frozen=True)
class Credential:
    header: str
    value: str
    source: str


def _oauth() -> Credential | None:
    if not OAUTH_STORE.is_file():
        return None
    entry = json.loads(OAUTH_STORE.read_text()).get("claudeAiOauth") or {}
    token = entry.get("accessToken")
    if not token:
        return None
    expires_at = entry.get("expiresAt")
    if expires_at and expires_at / 1000 <= time.time():
        when = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(expires_at / 1000))
        raise RuntimeError(
            f"{OAUTH_STORE}: claudeAiOauth expired at {when}. A stale token comes "
            "back as a 401 that reads like an API fault, so it is refused here "
            "instead. Open an interactive Claude Code session to refresh it, or "
            "pass --credential-env VAR --credential-header x-api-key with an "
            "API key."
        )
    return Credential("Authorization", f"Bearer {token}", f"{OAUTH_STORE}:claudeAiOauth")


def _from_env(var: str, header: str) -> Credential | None:
    value = os.environ.get(var)
    if not value:
        return None
    prefix = "" if header.lower() == "x-api-key" else "Bearer "
    return Credential(header, f"{prefix}{value}", f"${var}")


Source = tuple[str, Callable[[], "Credential | None"]]

HOST_SOURCES: dict[str, tuple[Source, ...]] = {
    "api.anthropic.com": (
        (f"{OAUTH_STORE}:claudeAiOauth", _oauth),
        ("$ANTHROPIC_API_KEY", lambda: _from_env("ANTHROPIC_API_KEY", "x-api-key")),
    ),
    "api.kimi.ai": (
        ("$KIMI_API_KEY", lambda: _from_env("KIMI_API_KEY", "Authorization")),
    ),
    "api.z.ai": (
        ("$ZAI_API_KEY", lambda: _from_env("ZAI_API_KEY", "Authorization")),
    ),
}


def resolve(
    url: str,
    *,
    env_var: str | None = None,
    env_header: str = "Authorization",
    none: bool = False,
) -> Credential | None:
    """The credential to send to `url`, or None when explicitly asked for none.

    `env_header` selects which of the two first-party shapes `env_var` carries.
    They are not interchangeable: an OAuth token authenticates as
    `Authorization: Bearer`, an API key as `x-api-key` with no prefix, and each
    on the other's header is a 401.
    """
    if none:
        return None
    if env_var:
        cred = _from_env(env_var, env_header)
        if cred is None:
            raise RuntimeError(f"${env_var} is unset or empty")
        return cred

    host = urlsplit(url).hostname or ""
    sources = HOST_SOURCES.get(host)
    if sources is None:
        raise RuntimeError(
            f"no credential source is known for host {host!r}. Pass "
            "--credential-env VAR, or --no-credential if the destination needs "
            "none — sending a first-party body somewhere else should read like "
            "the deliberate act it is."
        )
    for _, source in sources:
        cred = source()
        if cred is not None:
            return cred
    raise RuntimeError(
        f"no credential resolved for {host}; tried "
        + ", ".join(label for label, _ in sources)
    )

"""Forwards Bot API calls from any number of sessions, and logs each one.

It interprets nothing: it refuses the handful of methods that would break the
drain's invariants, passes everything else through unchanged, and hands back
Telegram's own status and body byte for byte. An agent therefore composes an
ordinary Bot API request and reads an ordinary Bot API answer, errors included.
"""

import json
import time
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from claude_config.telegram_hitl import upstream
from claude_config.telegram_hitl.log import ChannelLog, ErrorTransitions

# Keyed on the lowercased name: Bot API method names are case-insensitive in the
# URL, so a denylist spelled exactly would be bypassed by "getupdates".
DENIED: dict[str, str] = {
    "getupdates": "the drain owns the only update cursor, and a second consumer evicts it",
    "setwebhook": "a webhook disables getUpdates, silently stopping the drain",
    "deletewebhook": "drop_pending_updates would discard updates Telegram is still holding",
    "close": "would invalidate the bot session the drain is polling on",
    "logout": "would invalidate the bot token",
}

FORWARD_TIMEOUT = 30.0


def _envelope(code: int, description: str) -> bytes:
    """A Telegram-shaped error, marked as the proxy's own so it cannot be mistaken."""
    return json.dumps({"ok": False, "error_code": code,
                       "description": f"telegram-hitl proxy: {description}"}).encode()


def _decoded(raw: bytes) -> Any:
    """Parse JSON for a log meant to be read with jq; keep anything else as text."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return raw.decode("utf-8", errors="replace")


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server: "ProxyServer"

    def do_GET(self) -> None:
        method, _, query = self.path.lstrip("/").partition("?")
        self._forward(method, query, b"", "")

    def do_POST(self) -> None:
        method, _, query = self.path.lstrip("/").partition("?")
        length = int(self.headers.get("Content-Length") or 0)
        self._forward(method, query, self.rfile.read(length),
                      self.headers.get("Content-Type", ""))

    def _forward(self, method: str, query: str, body: bytes, content_type: str) -> None:
        session = self.headers.get("X-Session-Id")
        denial = DENIED.get(method.lower())
        if denial is not None:
            self.server.log.append({"kind": "denied", "session": session,
                                    "method": method, "reason": denial})
            self._answer(403, _envelope(403, denial))
            return

        started = time.monotonic()
        try:
            answer = upstream.call(self.server.api_base, self.server.token, method,
                                   verb=self.command, query=query, body=body,
                                   content_type=content_type, timeout=FORWARD_TIMEOUT)
        except urllib.error.URLError as error:
            self.server.faults.failed(f"forward:{type(error).__name__}", repr(error))
            self._answer(502, _envelope(502, f"cannot reach Telegram: {error}"))
            return

        self.server.faults.ok()
        self.server.log.append({
            "kind": "outbound", "session": session, "method": method, "query": query,
            "params": _decoded(body),
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "status": answer.status, "response": _decoded(answer.body),
        })
        self._answer(answer.status, answer.body, answer.content_type)

    def _answer(self, status: int, body: bytes, content_type: str = "") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type or "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:
        """Silent: the channel log is the record, and nobody reads this stderr."""


class ProxyServer(ThreadingHTTPServer):
    """Threaded because sends are stateless and safely parallel."""

    daemon_threads = True

    def __init__(self, address: tuple[str, int], log: ChannelLog, *,
                 api_base: str, token: str) -> None:
        super().__init__(address, _Handler)
        self.log = log
        self.api_base = api_base
        self.token = token
        self.faults = ErrorTransitions(log, "forward")

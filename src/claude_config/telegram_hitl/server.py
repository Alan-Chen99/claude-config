"""Forwards Bot API calls from any number of sessions, and logs each one.

It interprets nothing: it refuses the handful of methods that would break the
drain's invariants, passes everything else through unchanged, and hands back
Telegram's own status and body byte for byte. An agent therefore composes an
ordinary Bot API request and reads an ordinary Bot API answer, errors included.
"""

import json
import re
import sys
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

# A Bot API method name is alphanumeric, so anything else is not one. Measured,
# without this check: /getUpdates/, /get%55pdates, /%67etUpdates and
# /sendMessage/../getUpdates all passed the denylist and reached Telegram with
# the denied name intact. The denylist names the dangerous methods; it cannot
# also answer for every spelling that resolves to them, so the shape is checked
# separately. This constrains the characters a method name may contain and
# nothing about which methods pass, so the denylist decision stands.
METHOD_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")

FORWARD_TIMEOUT = 30.0
IDLE_TIMEOUT = 120.0


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
    timeout = IDLE_TIMEOUT
    server: "ProxyServer"

    def do_GET(self) -> None:
        method, _, query = self.path.lstrip("/").partition("?")
        self._forward(method, query, b"", "")

    def do_POST(self) -> None:
        method, _, query = self.path.lstrip("/").partition("?")
        if "Transfer-Encoding" in self.headers:
            # A chunked body carries no Content-Length, so it reads as empty and
            # would be forwarded as a send with no fields — which Telegram
            # answers by naming the fields it is missing, for a message the agent
            # believes it sent. Refuse rather than forward a body that is not
            # there.
            self._refuse(411, method, "send a body with Content-Length; a chunked "
                                      "body cannot be forwarded")
            return
        length = int(self.headers.get("Content-Length") or 0)
        self._forward(method, query, self.rfile.read(length),
                      self.headers.get("Content-Type", ""))

    def _forward(self, method: str, query: str, body: bytes, content_type: str) -> None:
        session = self.headers.get("X-Session-Id")
        if not METHOD_NAME.match(method):
            self._refuse(400, method, "not a Bot API method name")
            return
        denial = DENIED.get(method.lower())
        if denial is not None:
            self._refuse(403, method, denial)
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

    def _refuse(self, code: int, method: str, reason: str) -> None:
        """Log and answer without forwarding. Every refusal takes this path."""
        self.server.log.append({"kind": "denied", "session": self.headers.get("X-Session-Id"),
                                "method": method, "reason": reason})
        self._answer(code, _envelope(code, reason))

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

    def handle_error(self, request: object, client_address: object) -> None:
        """Record a handler that raised, where everyone is already looking.

        Its answer to the caller is lost either way and this server's stderr is
        read by nobody. Not fatal, unlike the drain's equivalent: a dropped send
        is the caller's to retry and it sees the broken connection, while a
        dropped update is gone for good.
        """
        error = sys.exception()
        try:
            self.faults.failed(f"handler:{type(error).__name__}", repr(error))
        except OSError:
            super().handle_error(request, client_address)  # the log is what failed

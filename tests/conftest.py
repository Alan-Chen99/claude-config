"""Shared fixtures: a stand-in Bot API, and an HTTP client that never raises."""

import json
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest


@dataclass
class Recorded:
    """One request the fake Bot API received."""

    path: str
    verb: str
    headers: dict[str, str]
    body: bytes

    @property
    def method(self) -> str:
        """The Bot API method name, with the token segment and query stripped."""
        return self.path.split("/", 2)[2].split("?")[0]

    @property
    def payload(self) -> Any:
        return json.loads(self.body) if self.body else None


@dataclass
class FakeTelegram:
    """Records every request and answers from a queue, or from a function.

    `handler` overrides the queue, which is how the durability-ordering test
    inspects the log at the exact moment a poll carries an advanced offset.
    """

    base: str = ""
    requests: list[Recorded] = field(default_factory=list)
    responses: list[tuple[int, bytes]] = field(default_factory=list)
    handler: Callable[[Recorded], tuple[int, bytes]] | None = None
    default: tuple[int, bytes] = (200, b'{"ok":true,"result":[]}')
    default_delay: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def queue(self, status: int, payload: Any) -> None:
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        with self._lock:
            self.responses.append((status, body))

    def answer(self, recorded: Recorded) -> tuple[int, bytes]:
        with self._lock:
            self.requests.append(recorded)
            if self.handler is not None:
                return self.handler(recorded)
            if self.responses:
                return self.responses.pop(0)
        # Outside the lock, and delayed: the real server holds an empty poll open
        # for 25 seconds, and a fake that answers instantly makes the drain spin.
        time.sleep(self.default_delay)
        return self.default


def _handler_class(fake: FakeTelegram) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _reply(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            status, body = fake.answer(Recorded(self.path, self.command,
                                                dict(self.headers), self.rfile.read(length)))
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_GET = _reply
        do_POST = _reply

        def log_message(self, *args: Any) -> None:
            """Silent: the test asserts on fake.requests, not on stderr."""

    return Handler


class _Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address) -> None:
        """A proxy killed mid-poll drops its connection, which is a test ending
        rather than a fault of the fake. Its traceback in teardown reads exactly
        like a failure, so it is suppressed; everything else still prints."""
        if not isinstance(sys.exception(), (BrokenPipeError, ConnectionResetError)):
            super().handle_error(request, client_address)


@pytest.fixture
def fake_telegram():
    """A Bot API on loopback that the proxy can be pointed at."""
    fake = FakeTelegram()
    server = _Server(("127.0.0.1", 0), _handler_class(fake))
    fake.base = f"http://127.0.0.1:{server.server_port}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield fake
    server.shutdown()
    server.server_close()


@pytest.fixture
def http_call():
    """Call a URL and return (status, body); a 4xx/5xx is an answer, not a raise."""

    def call(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None,
             verb: str | None = None, timeout: float = 10.0) -> tuple[int, bytes]:
        request = urllib.request.Request(url, data=data, headers=headers or {},
                                         method=verb or ("POST" if data else "GET"))
        try:
            with urllib.request.urlopen(request, timeout=timeout) as answer:
                return answer.status, answer.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    return call

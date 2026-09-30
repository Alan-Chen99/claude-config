"""Send a request directory and record what came back.

The result is written in the capture format, so `cc-pretty-intercept` renders a
replay with no front-end of its own, and reassembly goes through the proxy's own
`parse_sse_stream` — a replay shaped by a second reassembler is not comparable
to the capture it exists to be compared against.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from claude_config.cc_replay.credentials import Credential
from claude_config.cc_replay.proxy_module import load_proxy

# Headers the client owns, or that would assert something false if repeated.
# Every other captured header goes out as captured, anthropic-beta first among
# them. X-Claude-Code-Session-Id is deliberately not here: it reached the API on
# the original call, so a faithful re-send carries it.
DEVIATIONS = (
    "x-client-request-id",
    "x-stainless-retry-count",
    "content-length",
    "host",
    "connection",
)
_CLIENT_OWNED = frozenset({"content-length", "host", "connection"})


def outgoing_headers(captured: list[list[str]]) -> list[tuple[str, str]]:
    """The captured header list as it goes back out, casing and order intact."""
    sent: list[tuple[str, str]] = []
    for name, value in captured:
        low = name.lower()
        if low in _CLIENT_OWNED:
            continue
        if low == "x-client-request-id":
            value = str(uuid.uuid4())
        elif low == "x-stainless-retry-count":
            value = "0"
        sent.append((name, value))
    return sent


def next_result_path(out_dir: Path) -> Path:
    """`result-NNNN.json` after the highest already there; a send never clobbers."""
    used = [
        int(digits)
        for path in out_dir.glob("result-*.json")
        if (digits := path.stem.removeprefix("result-")).isdigit()
    ]
    return out_dir / f"result-{max(used, default=0) + 1:04d}.json"


def send(
    out_dir: Path,
    *,
    credential: Credential | None,
    url: str | None = None,
    timeout: float = 600.0,
    accept_synthesized: bool = False,
) -> Path:
    """Send what `out_dir` holds; return the path of the result written."""
    out_dir = Path(out_dir)
    body = json.loads((out_dir / "request.json").read_text())
    http = json.loads((out_dir / "http.json").read_text())
    meta = json.loads((out_dir / "meta.json").read_text())

    headers_source = http.get("headers_source", "captured")
    if headers_source == "synthesized" and not accept_synthesized:
        raise RuntimeError(
            f"{out_dir / 'http.json'} carries synthesized headers: the source "
            "capture predates the proxy recording them, so its anthropic-beta "
            "list is unrecoverable. A re-send without it is a different call, "
            "and that difference is what a diagnosis would otherwise blame on "
            "the model. Pass --accept-synthesized-headers to send anyway."
        )

    target = url or http["url"]
    method = http.get("method", "POST")
    headers = outgoing_headers(http.get("request_headers", []))
    if credential is not None:
        headers.append((credential.header, credential.value))
    payload = json.dumps(body).encode()
    streaming = body.get("stream") is True

    started = time.time()
    with httpx.Client(timeout=timeout) as client:
        with client.stream(
            method, target, headers=headers, content=payload
        ) as response:
            received = bytearray()
            for chunk in response.iter_bytes():
                received.extend(chunk)
            status = response.status_code
            reason = response.reason_phrase
            response_headers = [[k, v] for k, v in response.headers.multi_items()]
    duration_ms = int((time.time() - started) * 1000)

    raw = bytes(received).decode("utf-8", errors="replace")
    proxy = load_proxy()

    entry: dict[str, Any] = {
        "timestamp": datetime.fromtimestamp(started, tz=timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        **({"session": meta["session"]} if meta.get("session") else {}),
        "streaming": streaming,
        "request": body,
        "http": {
            "method": method,
            "url": target,
            "http_version": "HTTP/1.1",
            # The credential goes on the wire and not into the file, the same
            # rule the proxy follows.
            "request_headers": [
                [name, value]
                for name, value in headers
                if credential is None or name != credential.header
            ],
            "response": {
                "status": status,
                "reason": reason,
                "headers": response_headers,
            },
        },
        "replay": {
            "source": meta.get("source", ""),
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "headers_source": headers_source,
            "credential": credential.source if credential else "none",
            "deviations": list(DEVIATIONS),
        },
    }

    if status != 200:
        entry["error"] = {
            "status": status,
            "statusText": reason,
            **proxy.error_detail(bytes(received)),
        }
    else:
        entry["response"] = (
            proxy.parse_sse_stream(raw) if streaming else json.loads(raw)
        )

    result = next_result_path(out_dir)
    result.write_text(json.dumps(entry, indent=2) + "\n")
    result.with_suffix(".sse").write_text(raw)
    return result

"""mitmproxy addon that logs Anthropic API request/response pairs.

Load with: mitmdump -s proxy.py -p 9160
Or use the CLI wrapper: python3 run-proxy.py [--port PORT]
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

TARGET_HOST = "api.anthropic.com"
LOG_BASE = Path.home() / ".claude" / "requests-log" / "proxy"
SESSION_HEADER = "x-claude-code-session-id"


# --- SSE parser ---


def parse_sse_stream(raw: str) -> dict:
    """Reconstruct an Anthropic Messages API response from SSE events."""
    message: dict = {
        "id": "",
        "model": "",
        "role": "assistant",
        "content": [],
        "stop_reason": None,
        "error": None,
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }

    text_accum: dict[int, str] = {}
    json_accum: dict[int, str] = {}
    thinking_accum: dict[int, str] = {}

    for line in raw.split("\n"):
        if not line.startswith("data: "):
            continue
        try:
            event = json.loads(line[6:])
        except (json.JSONDecodeError, ValueError):
            continue

        etype = event.get("type")

        if etype == "message_start":
            msg = event.get("message", {})
            message["id"] = msg.get("id", "")
            message["model"] = msg.get("model", "")
            message["role"] = msg.get("role", "assistant")
            u = msg.get("usage", {})
            message["usage"]["input_tokens"] = u.get("input_tokens", 0)
            if u.get("cache_creation_input_tokens"):
                message["usage"]["cache_creation_input_tokens"] = u[
                    "cache_creation_input_tokens"
                ]
            if u.get("cache_read_input_tokens"):
                message["usage"]["cache_read_input_tokens"] = u[
                    "cache_read_input_tokens"
                ]

        elif etype == "content_block_start":
            idx = event.get("index", 0)
            block = event.get("content_block", {})
            t = block.get("type", "unknown")
            while len(message["content"]) <= idx:
                message["content"].append(None)
            if t == "tool_use":
                message["content"][idx] = {
                    "type": t,
                    "id": block.get("id", ""),
                    "name": block.get("name", ""),
                    "input": {},
                }
            else:
                message["content"][idx] = {"type": t}

        elif etype == "content_block_delta":
            idx = event.get("index", 0)
            delta = event.get("delta", {})
            dt = delta.get("type")
            if dt == "text_delta":
                text_accum[idx] = text_accum.get(idx, "") + delta.get("text", "")
            elif dt == "input_json_delta":
                json_accum[idx] = json_accum.get(idx, "") + delta.get(
                    "partial_json", ""
                )
            elif dt == "thinking_delta":
                thinking_accum[idx] = thinking_accum.get(idx, "") + delta.get(
                    "thinking", ""
                )

        elif etype == "message_delta":
            delta = event.get("delta", {})
            if delta.get("stop_reason"):
                message["stop_reason"] = delta["stop_reason"]
            u = event.get("usage", {})
            if u.get("output_tokens"):
                message["usage"]["output_tokens"] = u["output_tokens"]

        elif etype == "error":
            err = event.get("error", {})
            message["error"] = {
                "type": err.get("type", "unknown"),
                "message": err.get("message", ""),
            }

    for idx, text in text_accum.items():
        if idx < len(message["content"]) and message["content"][idx]:
            message["content"][idx]["text"] = text
    for idx, j in json_accum.items():
        if idx < len(message["content"]) and message["content"][idx]:
            try:
                message["content"][idx]["input"] = json.loads(j)
            except (json.JSONDecodeError, ValueError):
                message["content"][idx]["input"] = j
    for idx, thinking in thinking_accum.items():
        if idx < len(message["content"]) and message["content"][idx]:
            message["content"][idx]["thinking"] = thinking

    message["content"] = [b for b in message["content"] if b is not None]
    return message


# --- Logging ---

_counter = 0
_counter_lock = Lock()


def _init_counter() -> None:
    global _counter
    try:
        files = list(LOG_BASE.glob("*.json"))
        nums = []
        for f in files:
            m = re.match(r"^(\d+)\.json$", f.name)
            if m:
                nums.append(int(m.group(1)))
        _counter = max(nums) if nums else 0
    except OSError:
        _counter = 0


def get_counter() -> int:
    return _counter


def write_log(entry: dict) -> None:
    global _counter
    with _counter_lock:
        LOG_BASE.mkdir(parents=True, exist_ok=True)
        _counter += 1
        filename = f"{_counter:04d}.json"
        (LOG_BASE / filename).write_text(json.dumps(entry, indent=2))


def log_error(context: str, err: Exception) -> None:
    try:
        LOG_BASE.mkdir(parents=True, exist_ok=True)
        msg = f"[{datetime.now(timezone.utc).isoformat()}] {context}: {err}\n"
        with open(LOG_BASE / "errors.log", "a") as f:
            f.write(msg)
    except OSError:
        pass


# --- mitmproxy addon ---


class InterceptAddon:
    """mitmproxy addon that logs Anthropic API request/response pairs."""

    def __init__(self) -> None:
        self._flow_start: dict[str, float] = {}

    def request(self, flow: "mitmproxy.http.HTTPFlow") -> None:
        self._flow_start[flow.id] = time.time()

    def error(self, flow: "mitmproxy.http.HTTPFlow") -> None:
        self._flow_start.pop(flow.id, None)

    def response(self, flow: "mitmproxy.http.HTTPFlow") -> None:
        if flow.request.pretty_host != TARGET_HOST:
            return

        start_ms = self._flow_start.pop(flow.id, time.time())
        duration_ms = int((time.time() - start_ms) * 1000)

        body_bytes = flow.request.get_content()
        if not body_bytes:
            return

        try:
            body = json.loads(body_bytes)
        except (json.JSONDecodeError, ValueError):
            return

        if not body.get("model") or not body.get("messages"):
            return

        streaming = body.get("stream") is True
        session_id = flow.request.headers.get(SESSION_HEADER)
        timestamp = datetime.fromtimestamp(start_ms, tz=timezone.utc).isoformat()

        if flow.response is None:
            return

        if flow.response.status_code != 200:
            write_log(
                {
                    "timestamp": timestamp,
                    "duration_ms": duration_ms,
                    **({"session_id": session_id} if session_id else {}),
                    "streaming": streaming,
                    "error": {
                        "status": flow.response.status_code,
                        "statusText": flow.response.reason,
                    },
                    "request": body,
                }
            )
            return

        response_bytes = flow.response.get_content()
        try:
            if streaming:
                parsed = parse_sse_stream(
                    response_bytes.decode("utf-8", errors="replace")
                )
            else:
                parsed = json.loads(response_bytes)
        except Exception as e:
            log_error("parse-response", e)
            return

        write_log(
            {
                "timestamp": timestamp,
                "duration_ms": duration_ms,
                **({"session_id": session_id} if session_id else {}),
                "streaming": streaming,
                "request": body,
                "response": parsed,
            }
        )


_init_counter()
addons = [InterceptAddon()]

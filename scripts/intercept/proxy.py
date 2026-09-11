"""mitmproxy addon that logs Anthropic API request/response pairs.

Resolves sessions from X-Claude-Code-Session-Id header against
~/.claude/sessions/*.json to enrich logs with session metadata (cwd,
entrypoint, kind). Logs are stored per-session:
  ~/.claude/requests-log/{session_id}/NNNN.json

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
LOG_BASE = Path.home() / ".claude" / "requests-log"
SESSIONS_DIR = Path.home() / ".claude" / "sessions"
SESSION_HEADER = "x-claude-code-session-id"


# --- Session resolution ---


class SessionInfo:
    __slots__ = ("session_id", "pid", "cwd", "started_at", "kind", "entrypoint")

    def __init__(
        self,
        session_id: str,
        pid: int | None = None,
        cwd: str | None = None,
        started_at: int | None = None,
        kind: str | None = None,
        entrypoint: str | None = None,
    ):
        self.session_id = session_id
        self.pid = pid
        self.cwd = cwd
        self.started_at = started_at
        self.kind = kind
        self.entrypoint = entrypoint

    def to_dict(self) -> dict:
        d: dict = {"session_id": self.session_id}
        if self.cwd:
            d["cwd"] = self.cwd
        if self.kind:
            d["kind"] = self.kind
        if self.entrypoint:
            d["entrypoint"] = self.entrypoint
        if self.pid:
            d["pid"] = self.pid
        return d


_session_cache: dict[str, SessionInfo] = {}
_session_cache_lock = Lock()


def resolve_session(session_id: str) -> SessionInfo:
    """Resolve a session ID to its metadata by scanning ~/.claude/sessions/."""
    with _session_cache_lock:
        if session_id in _session_cache:
            return _session_cache[session_id]

    # Scan session files to find the matching session
    info = SessionInfo(session_id=session_id)
    try:
        for f in SESSIONS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if data.get("sessionId") == session_id:
                info = SessionInfo(
                    session_id=session_id,
                    pid=data.get("pid"),
                    cwd=data.get("cwd"),
                    started_at=data.get("startedAt"),
                    kind=data.get("kind"),
                    entrypoint=data.get("entrypoint"),
                )
                break
    except OSError:
        pass

    with _session_cache_lock:
        _session_cache[session_id] = info
    return info


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
            # Keep the whole start block. Server-side tools deliver their
            # payload here rather than in deltas — web_search_tool_result
            # carries its result list on content_block_start and nothing
            # later restores it — so copying only `type` writes an empty
            # husk to disk. `input` is reset because input_json_delta
            # rebuilds it from scratch below.
            started = dict(block)
            if "input" in started:
                started["input"] = {}
            started["type"] = t
            message["content"][idx] = started

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

_counters: dict[str, int] = {}
_counter_lock = Lock()


def _scan_counter(log_dir: Path) -> int:
    """Scan a log directory for the highest existing counter value."""
    if not log_dir.exists():
        return 0
    try:
        return max(
            (
                int(m.group(1))
                for f in log_dir.glob("*.json")
                if (m := re.match(r"^(\d+)\.json$", f.name))
            ),
            default=0,
        )
    except OSError:
        return 0


def get_total_count() -> int:
    """Total logged requests across all sessions."""
    total = 0
    try:
        for d in LOG_BASE.iterdir():
            if not d.is_dir():
                continue
            for f in d.glob("*.json"):
                if re.match(r"^(\d+)\.json$", f.name):
                    total += 1
    except OSError:
        pass
    return total


def write_log(entry: dict, session_id: str | None) -> None:
    subdir = session_id if session_id else "unknown"
    log_dir = LOG_BASE / subdir
    dir_key = str(log_dir)

    with _counter_lock:
        if dir_key not in _counters:
            _counters[dir_key] = _scan_counter(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        _counters[dir_key] += 1
        counter = _counters[dir_key]

    filename = f"{counter:04d}.json"
    (log_dir / filename).write_text(json.dumps(entry, indent=2))


def log_error(context: str, err: Exception) -> None:
    try:
        err_dir = LOG_BASE / "_errors"
        err_dir.mkdir(parents=True, exist_ok=True)
        msg = f"[{datetime.now(timezone.utc).isoformat()}] {context}: {err}\n"
        with open(err_dir / "errors.log", "a") as f:
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

        # Resolve session metadata
        session_meta: dict = {}
        if session_id:
            info = resolve_session(session_id)
            session_meta = info.to_dict()
        else:
            session_meta = {}

        if flow.response is None:
            return

        if flow.response.status_code != 200:
            write_log(
                {
                    "timestamp": timestamp,
                    "duration_ms": duration_ms,
                    **({"session": session_meta} if session_meta else {}),
                    "streaming": streaming,
                    "error": {
                        "status": flow.response.status_code,
                        "statusText": flow.response.reason,
                    },
                    "request": body,
                },
                session_id,
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
                **({"session": session_meta} if session_meta else {}),
                "streaming": streaming,
                "request": body,
                "response": parsed,
            },
            session_id,
        )


addons = [InterceptAddon()]

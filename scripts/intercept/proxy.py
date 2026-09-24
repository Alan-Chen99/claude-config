"""mitmproxy addon that logs Anthropic API request/response pairs.

Resolves sessions from X-Claude-Code-Session-Id header against
~/.claude/sessions/*.json to enrich logs with session metadata (cwd,
entrypoint, kind). Logs are stored per-session:
  ~/.claude/requests-log/{session_id}/NNNN.json

Response bodies are forwarded to the client as they arrive and captured on the
way past, so an intercepted SSE stream still streams. See README.md,
"Pass-through streaming", for what buffering costs.

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

# Every host a session's Anthropic-shaped traffic can go to: the first-party
# API, and the Anthropic-compatible endpoint scripts/kimi.sh points
# ANTHROPIC_BASE_URL at. A host missing here is not an error anywhere — the
# flow passes through uncaptured and the session leaves no request log.
TARGET_HOSTS = ("api.anthropic.com", "api.kimi.ai")
LOG_BASE = Path.home() / ".claude" / "requests-log"
SESSIONS_DIR = Path.home() / ".claude" / "sessions"
SESSION_HEADER = "x-claude-code-session-id"


# --- Session resolution ---


class SessionInfo:
    __slots__ = ("session_id", "pid", "cwd", "kind", "entrypoint")

    def __init__(
        self,
        session_id: str,
        pid: int | None = None,
        cwd: str | None = None,
        kind: str | None = None,
        entrypoint: str | None = None,
    ):
        self.session_id = session_id
        self.pid = pid
        self.cwd = cwd
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
    """Reconstruct an Anthropic Messages API response from SSE events.

    Message-level fields are copied as the API sends them rather than picked
    from a list, so a field the list was never told about is not dropped
    silently: `stop_details` carries the category and explanation behind
    `stop_reason: "refusal"`, and nothing else in the capture records either.
    """
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

    events = 0
    for line in raw.split("\n"):
        if not line.startswith("data:"):
            continue
        # SSE makes the space after the colon optional and strips exactly one
        # when present (WHATWG server-sent events, "process the field").
        # Anthropic sends it; the Kimi endpoint does not, and requiring it
        # skipped every line of a Kimi stream into an empty capture.
        payload = line[5:]
        if payload.startswith(" "):
            payload = payload[1:]
        try:
            event = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            continue
        events += 1

        etype = event.get("type")

        if etype == "message_start":
            start = dict(event.get("message", {}))
            usage = dict(start.get("usage") or {})
            usage.setdefault("input_tokens", 0)
            usage.setdefault("output_tokens", 0)
            start["usage"] = usage
            # content_block events rebuild the blocks below.
            start["content"] = []
            message.update(start)

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
            # stop_reason, stop_details and stop_sequence all arrive here.
            message.update(event.get("delta", {}))
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
    # A stream nothing could be read out of yields a message that is entirely
    # defaults -- blank model, no content, zero usage -- which on disk is
    # indistinguishable from a real empty turn. Raising routes it to the
    # `parse-response` line in `_errors/errors.log` instead, where a capture
    # that went missing has somewhere to be found.
    if events == 0:
        raise ValueError("no SSE data events in a streamed response")

    return message


ERROR_BODY_MAX = 8192


def error_detail(raw: bytes | None) -> dict:
    """The API's own account of a failed call, read from the error body.

    A status line names neither the limit that was hit nor the field that was
    rejected; the body does. `{"error": {"type", "message"}}` is what the API
    sends, and it is kept in that shape so a reader finds the same two keys as
    on an in-stream error. Anything else -- a gateway's HTML, a partial body --
    is kept as capped text.
    """
    if not raw:
        return {}
    text = raw.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        parsed = None
    if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
        err = parsed["error"]
        return {"type": err.get("type", ""), "message": err.get("message", "")}
    return {"body": text[:ERROR_BODY_MAX]}


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
        self._streamed: dict[str, bytearray] = {}

    def request(self, flow: "mitmproxy.http.HTTPFlow") -> None:
        self._flow_start[flow.id] = time.time()

    def error(self, flow: "mitmproxy.http.HTTPFlow") -> None:
        self._flow_start.pop(flow.id, None)
        self._streamed.pop(flow.id, None)

    def responseheaders(self, flow: "mitmproxy.http.HTTPFlow") -> None:
        """Forward each response chunk onward as it arrives, keeping a copy.

        mitmproxy buffers the whole body by default and sends the client its
        first byte -- status line included -- only once the server is done.
        Claude Code cancels a first-party request whose response headers are
        late, on a window it computes per attempt -- 180s for a first-party
        provider plus 1s per 32KB of request body, or the 599s cap on an
        escalated retry -- so buffering an SSE stream turns a long generation
        into a client-side abort. The buffering is measured; the abort is read
        off Claude Code's source and has not been observed firing. README.md,
        "Pass-through streaming", carries both.

        A `stream` callable receives every chunk and returns what to forward;
        capturing here rather than through mitmproxy's `store_streamed_bodies`
        option keeps the capture scoped to these hosts and working under a bare
        `mitmdump -s proxy.py`.
        """
        if flow.request.pretty_host not in TARGET_HOSTS:
            return

        captured = bytearray()
        self._streamed[flow.id] = captured

        def relay(chunk: bytes) -> bytes:
            captured.extend(chunk)
            return chunk

        flow.response.stream = relay

    def response(self, flow: "mitmproxy.http.HTTPFlow") -> None:
        if flow.request.pretty_host not in TARGET_HOSTS:
            return

        captured = self._streamed.pop(flow.id, None)
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

        # Streaming leaves raw_content unset (mitmproxy Message.raw_content),
        # so restore what relay() saw before anything reads the body.
        if captured is not None:
            flow.response.raw_content = bytes(captured)

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
                        # strict=False: a body that fails to decode is still
                        # worth more than no body at all.
                        **error_detail(flow.response.get_content(strict=False)),
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

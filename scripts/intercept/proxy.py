"""mitmproxy addon that logs Anthropic API request/response pairs.

Resolves sessions from X-Claude-Code-Session-Id header against
~/.claude/sessions/*.json to enrich logs with session metadata (cwd,
entrypoint, kind). Logs are stored per-session:
  ~/.claude/requests-log/{session_id}/NNNN.json

A call that failed -- a non-200 status, a 200 the model refused or cut short
with an in-stream error, or a response that would not decode or reassemble --
also writes a sibling ~/.claude/requests-log/{session_id}/NNNN.detail.json. The
reassembled NNNN.json keeps the message, not the stream it arrived as, so the
detail file carries the response body as text, its Content-Encoding undone, and
every relayed read with the millisecond it arrived -- which is all the wire
gives; what a refusal withheld was never sent.

Response bodies are forwarded to the client as they arrive and captured on the
way past, so an intercepted SSE stream still streams. See README.md,
"Pass-through streaming", for what buffering costs.

Load with: mitmdump -s proxy.py -p 9160
Or use the CLI wrapper: python3 run-proxy.py [--port PORT]
"""

from __future__ import annotations

import base64
import codecs
import json
import re
import time
import zlib
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

# mitmproxy's own dependencies, so present wherever the addon runs.
import brotli
import zstandard

# Every host a session's Anthropic-shaped traffic can go to: the first-party
# API, and the Anthropic-compatible endpoints scripts/kimi.sh and scripts/zai.sh
# point ANTHROPIC_BASE_URL at. A host missing here is not an error anywhere —
# the flow passes through uncaptured and the session leaves no request log.
TARGET_HOSTS = ("api.anthropic.com", "api.kimi.ai", "api.z.ai")
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
    # indistinguishable from a real empty turn. Raising makes it a
    # `parse_error` capture instead, its bytes kept in the detail file.
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


def soft_error_trigger(parsed: dict) -> dict | None:
    """A 200 the model nonetheless refused or cut short, else None.

    `stop_reason: "refusal"` and an in-stream `error` event both ride an
    otherwise-successful 200 stream, so the status line is clean and the
    reassembled NNNN.json keeps only the surviving blocks -- a refusal withholds
    everything it generated past the stop. These are the 200s the detail log
    exists for; a clean `end_turn`/`tool_use`/`max_tokens` returns None.
    """
    if not isinstance(parsed, dict):
        return None
    if parsed.get("stop_reason") == "refusal":
        return {
            "kind": "refusal",
            "stop_reason": "refusal",
            "stop_details": parsed.get("stop_details"),
        }
    if parsed.get("error"):
        return {"kind": "stream_error", "error": parsed.get("error")}
    return None


# What each streaming decoder raises on a body that is not what its
# Content-Encoding says, plus the ValueError for a coding with no decoder.
DECODE_ERRORS = (ValueError, zlib.error, brotli.error, zstandard.ZstdError)


def _content_decoder(
    content_encoding: str,
) -> tuple[Callable[[bytes], bytes], Callable[[], bytes]]:
    """Undo Content-Encoding one relayed read at a time: (feed, flush).

    The relay sees the body as sent, and the API compresses every body -- gzip
    on SSE, br on JSON -- so a read is compressed bytes, not text. Covered: the
    four codings Claude Code's Accept-Encoding offers.
    """
    coding = content_encoding.strip().lower()
    if coding in ("", "identity"):
        return (lambda data: data), (lambda: b"")
    if coding in ("gzip", "deflate"):
        # wbits 47 takes a gzip or a zlib header, as mitmproxy's decode_gzip does.
        inflate = zlib.decompressobj(47)
        return inflate.decompress, inflate.flush
    if coding == "br":
        return brotli.Decompressor().process, (lambda: b"")
    if coding == "zstd":
        unzstd = zstandard.ZstdDecompressor().decompressobj(read_across_frames=True)
        return unzstd.decompress, unzstd.flush
    raise ValueError(f"no streaming decoder for Content-Encoding {content_encoding!r}")


def decode_chunks(
    wire: bytes, reads: list[tuple[int, int]], content_encoding: str
) -> tuple[str, list[dict]]:
    """The body as text, and each relayed read with the text it made decodable.

    `reads` holds (offset_ms, length) per read mitmproxy handed the relay --
    TCP boundaries, not SSE events, so the timing is the wire's, not the
    model's. A record's `bytes` is the read's size on the wire. The decompressor
    and the UTF-8 decoder both carry state across reads, so a block or a
    character split between two reads lands whole in the later one and the
    texts concatenate to exactly the body. Raises one of DECODE_ERRORS for a
    body its Content-Encoding will not undo.
    """
    feed, flush = _content_decoder(content_encoding)
    utf8 = codecs.getincrementaldecoder("utf-8")(errors="replace")
    chunks: list[dict] = []
    pos = 0
    for offset_ms, length in reads:
        text = utf8.decode(feed(wire[pos : pos + length]))
        pos += length
        chunks.append({"offset_ms": offset_ms, "bytes": length, "text": text})
    tail = utf8.decode(flush(), final=True)
    if tail:
        chunks[-1]["text"] += tail
    return "".join(chunk["text"] for chunk in chunks), chunks


def response_body_fields(
    wire: bytes | None, reads: list[tuple[int, int]], content_encoding: str
) -> dict:
    """The response body as a detail file records it.

    A body its Content-Encoding will not undo is kept as the wire bytes in
    base64 instead -- the detail file exists for the failures, and that is one.
    """
    if wire is None:
        return {"raw_response": None, "chunks": []}
    try:
        raw, chunks = decode_chunks(wire, reads, content_encoding)
    except DECODE_ERRORS as e:
        log_error("decode-detail", e)
        return {
            "raw_response": None,
            "raw_response_base64": base64.b64encode(wire).decode("ascii"),
            "decode_error": str(e),
            "chunks": [{"offset_ms": offset, "bytes": length} for offset, length in reads],
        }
    return {"raw_response": raw, "chunks": chunks}


# --- The HTTP envelope ---

# Header names whose value is a credential. Dropped before an entry is built:
# the log tree sits unencrypted under $HOME, and nothing needs the secret to
# replay a call -- cc-replay resolves a fresh one at send time.
CREDENTIAL_HEADERS = frozenset(
    {"authorization", "x-api-key", "cookie", "proxy-authorization"}
)


def split_credentials(headers) -> tuple[list[list[str]], dict]:
    """Headers as sent, minus the secrets, plus the shape of the slot.

    Pairs rather than a mapping: `Headers.items(multi=True)` keeps a repeated
    header and the order it was sent in, where `dict()` joins duplicates with
    ", " and loses both.

    The slot -- which header, which scheme, how many characters -- is what tells
    a reader an OAuth bearer from an API key, and a replay where to put the
    credential it resolves. The value itself is never written.
    """
    kept: list[list[str]] = []
    credential: dict = {}
    for name, value in headers.items(multi=True):
        if name.lower() in CREDENTIAL_HEADERS:
            if not credential:
                scheme = value.split(" ", 1)[0] if " " in value else ""
                credential = {"header": name, "scheme": scheme, "length": len(value)}
            continue
        kept.append([name, value])
    return kept, credential


def http_region(flow) -> dict:
    """The call itself: everything about it the body cannot say.

    `anthropic-beta` varies per request inside one session -- 8 entries measured
    on an auxiliary call against 14 on the main one -- so no sibling capture,
    model id or client version implies it. Without this region a capture is a
    conversation, and a conversation cannot be put back on the wire.
    """
    request_headers, credential = split_credentials(flow.request.headers)
    region: dict = {
        "method": flow.request.method,
        "url": flow.request.pretty_url,
        "http_version": flow.request.http_version,
        "request_headers": request_headers,
    }
    if credential:
        region["credential"] = credential
    if flow.response is not None:
        region["response"] = {
            "status": flow.response.status_code,
            "reason": flow.response.reason,
            "headers": [[k, v] for k, v in flow.response.headers.items(multi=True)],
        }
    return region


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


def write_log(entry: dict, session_id: str | None) -> Path:
    """Write the capture as the session's next NNNN.json; return its path."""
    subdir = session_id if session_id else "unknown"
    log_dir = LOG_BASE / subdir
    dir_key = str(log_dir)

    with _counter_lock:
        if dir_key not in _counters:
            _counters[dir_key] = _scan_counter(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        _counters[dir_key] += 1
        counter = _counters[dir_key]

    path = log_dir / f"{counter:04d}.json"
    path.write_text(json.dumps(entry, indent=2))
    return path


def write_detail_log(capture: Path, entry: dict) -> None:
    """Write a failed call's detail file beside its capture, as NNNN.detail.json."""
    capture.with_suffix(".detail.json").write_text(json.dumps(entry, indent=2))


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
        # The body relay() forwarded, and (offset_ms, length) per read.
        self._streamed: dict[str, tuple[bytearray, list[tuple[int, int]]]] = {}

    def request(self, flow: "mitmproxy.http.HTTPFlow") -> None:
        # `response` pops only a target host's entry; any other would stay.
        if flow.request.pretty_host in TARGET_HOSTS:
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
        reads: list[tuple[int, int]] = []
        self._streamed[flow.id] = (captured, reads)
        t0 = self._flow_start.get(flow.id, time.time())

        def relay(chunk: bytes) -> bytes:
            # mitmproxy calls once more with b"" to mark the end of the body.
            if chunk:
                captured.extend(chunk)
                reads.append((int((time.time() - t0) * 1000), len(chunk)))
            return chunk

        flow.response.stream = relay

    def response(self, flow: "mitmproxy.http.HTTPFlow") -> None:
        if flow.request.pretty_host not in TARGET_HOSTS:
            return

        relayed, reads = self._streamed.pop(flow.id, (None, []))
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
        wire = bytes(relayed) if relayed is not None else None
        if wire is not None:
            flow.response.raw_content = wire

        envelope = {
            "timestamp": timestamp,
            "duration_ms": duration_ms,
            **({"session": session_meta} if session_meta else {}),
            "streaming": streaming,
            "http": http_region(flow),
        }

        parsed = None
        if flow.response.status_code != 200:
            capture = {
                **envelope,
                "error": {
                    "status": flow.response.status_code,
                    "statusText": flow.response.reason,
                    # strict=False: a body that fails to decode is still
                    # worth more than no body at all.
                    **error_detail(flow.response.get_content(strict=False)),
                },
                "request": body,
            }
            trigger = {
                "kind": "http_error",
                "status": flow.response.status_code,
                "statusText": flow.response.reason,
            }
        else:
            try:
                # A body its Content-Encoding will not undo raises here, and is
                # a parse_error like any other.
                response_bytes = flow.response.get_content()
                if response_bytes is None:
                    # relay() belonged to an addon instance mitmdump has since
                    # replaced, on an edit to this file.
                    raise ValueError("response body not captured: the addon was reloaded mid-call")
                if streaming:
                    parsed = parse_sse_stream(
                        response_bytes.decode("utf-8", errors="replace")
                    )
                else:
                    parsed = json.loads(response_bytes)
            except Exception as e:
                log_error("parse-response", e)
                capture = {**envelope, "error": {"parse_error": str(e)}, "request": body}
                trigger = {"kind": "parse_error", "message": str(e)}
            else:
                capture = {**envelope, "request": body, "response": parsed}
                trigger = soft_error_trigger(parsed)

        path = write_log(capture, session_id)
        if trigger is None:
            return
        try:
            write_detail_log(
                path,
                {
                    **envelope,
                    "detail_for": path.name,
                    "trigger": trigger,
                    "request": body,
                    "response": parsed,
                    **response_body_fields(
                        wire, reads, flow.response.headers.get("content-encoding", "")
                    ),
                },
            )
        except Exception as e:
            # Re-raised so mitmproxy logs the traceback; errors.log is where a
            # missing detail file is looked for.
            log_error("write-detail", e)
            raise


addons = [InterceptAddon()]

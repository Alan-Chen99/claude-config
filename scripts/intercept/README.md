# claude-intercept

MITM proxy that logs Claude Code API request/response pairs as JSON, organized by session.

## Setup

```bash
pip install mitmproxy  # or: uv pip install mitmproxy
```

## Usage

```bash
cd scripts/intercept
python3 run-proxy.py              # default port 9160
python3 run-proxy.py --port 8080  # custom port
```

Or directly via mitmdump:

```bash
mitmdump -s proxy.py -p 9160 --listen-host 127.0.0.1
```

On first run, mitmproxy generates a CA cert at `~/.mitmproxy/mitmproxy-ca-cert.pem`.

### As a systemd user service

[`systemd/claude-intercept.service`](../../systemd/claude-intercept.service)
runs that `mitmdump` command out of the canonical venv
(`~/.claude/venvs/claude-config`) on a machine with a systemd user manager.
`install.sh` links the unit; enabling it is by hand:

```bash
systemctl --user enable --now claude-intercept.service
```

The dev containers have no user manager, so their `docker/entrypoint.sh` starts
the same command. Each listener writes under its own `$HOME`, so a host-side
service and a container write separate `requests-log` trees.

Stopping the service cuts off every session `scripts/claude.sh` launched while
it was listening. `HTTPS_PROXY` is bound at launch, so such a session's API
calls fail with ECONNREFUSED until the proxy is back. The unit restarts the
proxy one second after any exit systemd did not request.

### With Node.js Claude CLI

Node.js `fetch` (undici) requires `--use-env-proxy` to honor `HTTPS_PROXY`:

```bash
HTTPS_PROXY=http://127.0.0.1:9160 \
NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem \
NODE_OPTIONS="--use-env-proxy" \
claude
```

### With native Claude binary

The native binary honors `NODE_EXTRA_CA_CERTS` as well: on 2.1.289 it
completed TLS through the proxy with the CA supplied only that way, which is
all `scripts/claude.sh` sets. The system store is the alternative for a
launcher that sets nothing. Add the CA to it:

```bash
# Linux
sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/claude-intercept.crt
sudo update-ca-certificates

# macOS
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain ~/.mitmproxy/mitmproxy-ca-cert.pem
```

Then:

```bash
HTTPS_PROXY=http://127.0.0.1:9160 claude
```

## Session resolution

The proxy extracts `X-Claude-Code-Session-Id` from HTTP headers and resolves
it against `~/.claude/sessions/*.json` to obtain session metadata:

- `cwd` — working directory of the Claude Code session
- `kind` — "interactive" or "headless"
- `entrypoint` — "cli", "sdk", etc.
- `pid` — process ID

Logs are stored per-session at `~/.claude/requests-log/{session_id}/0001.json`.
Sessions without an ID go to `~/.claude/requests-log/unknown/`.

## Log format

```json
{
  "proxy": {
    "format": 1,
    "source": "/repos/claude-config/scripts/intercept/proxy.py",
    "blob": "3f1c…",
    "mitmproxy": "12.2.3"
  },
  "timestamp": "2026-05-15T...",
  "duration_ms": 1234,
  "session": {
    "session_id": "abc-123",
    "cwd": "/path/to/project",
    "kind": "interactive",
    "entrypoint": "cli",
    "pid": 12345
  },
  "streaming": true,
  "http": {
    "method": "POST",
    "url": "https://api.anthropic.com/v1/messages?beta=true",
    "http_version": "HTTP/1.1",
    "request_headers": [["anthropic-beta", "claude-code-20250219,..."], ["x-app", "cli"]],
    "credential": {"header": "Authorization", "scheme": "Bearer", "length": 115},
    "response": {"status": 200, "reason": "OK", "headers": [["request-id", "req_..."]]}
  },
  "request": { "model": "...", "messages": [...], "system": [...] },
  "response": {
    "id": "msg_...",
    "model": "...",
    "content": [
      { "type": "text", "text": "..." },
      { "type": "tool_use", "name": "Read", "input": { "file_path": "..." } },
      { "type": "thinking", "thinking": "..." }
    ],
    "stop_reason": "end_turn",
    "stop_details": null,
    "usage": { "input_tokens": 1000, "output_tokens": 200 }
  }
}
```

A call that failed at the HTTP layer carries `error` in place of `response`:
`status` and `statusText`, plus the API's own account read from the error body
— `type` and `message`, the same two keys an in-stream error uses, or `body`
(capped at 8 KB) when the body was something else, such as a gateway's HTML.
A 200 whose body would not decode or reassemble carries `error` too, holding
only `parse_error`, the exception's type and message; so does a non-streamed
200 that is not a JSON object. The request half is a complete conversation, so
`cc-pretty-intercept` renders these.

A refusal is not an HTTP error: it arrives on a 200 stream as `stop_reason:
"refusal"` with `stop_details` carrying `category` (`reasoning_extraction`,
`cyber`, …) and `explanation`. Claude Code then shows the user a locally
synthesized `invalid_request` message, so the transcript and the capture
describe the same event in different words.

### `NNNN.detail.json` — the failed call in full

`NNNN.json` keeps the reassembled message, not the stream it came from: the
order and timing of events, and every event reassembly drops (`ping`, delta
types it does not model), are gone once it is written. What a refusal withheld
was never sent, so no file holds it, but the stream shows where it stopped and
when. So whenever a call fails — a non-200 status, a 200 the model refused or
ended with an in-stream `error`, or a response that would not decode or
reassemble — a sibling `NNNN.detail.json` keeps the wire's account:

```json
{
  "proxy": {"…": "as in NNNN.json"},
  "timestamp": "…", "duration_ms": 1003, "session": {"…": "…"}, "streaming": true,
  "http": {"…": "credential-stripped, as in NNNN.json"},
  "detail_for": "0007.json",
  "trigger": {"kind": "refusal", "stop_reason": "refusal", "stop_details": {"category": "reasoning_extraction", "…": "…"}},
  "request": {"…": "the full request body"},
  "response": {"…": "the reassembled message, or null"},
  "raw_response": "event: message_start\ndata: {…}\n\n…",
  "chunks": [{"offset_ms": 2, "bytes": 127, "text": "event: message_start\ndata: {…}\n\n"}]
}
```

`trigger.kind` is `http_error`, `refusal`, `stream_error` (an in-stream `error`
event, or an `error` object in a non-streamed 200) or `parse_error`.
`api.anthropic.com` compresses its bodies — SSE as gzip, JSON and error bodies
as br — and the relay sees them as sent, so `raw_response` is the body with its
`Content-Encoding` undone. `chunks` are the pieces of body mitmproxy relayed —
an HTTP/1.1 chunk, or as much of one as had arrived; for an unchunked body, a
socket read; never an SSE event as such — each with the millisecond it arrived
after the request, its size on the wire (`bytes`) and the text it completed
(`text`); `raw_response` is exactly the concatenation of `chunks[].text`. A body
that will not decode — not what its `Content-Encoding` says, a compressed
stream cut short or running past its end, or not UTF-8 — is kept as the wire
bytes in `raw_response_base64` instead, beside `decode_error`, with text-less
chunks and a `decode-detail` line naming the file in
`requests-log/_errors/errors.log`. Nothing else is trimmed or capped. A clean
`end_turn`/`tool_use`/`max_tokens` writes no detail file, and
`cc-pretty-intercept` refuses one, naming its capture.

Only bodies carrying both `model` and `messages` are logged, so every file on
disk is a conversation-shaped request. That includes Claude Code's own
auxiliary calls — its WebSearch tool reaches the API as a separate
`claude-haiku-4-5-20251001` request whose `tools` array holds exactly one
entry, the server-side `web_search_20250305` with `max_uses: 8` (observed in
this machine's own intercept logs, 2.1.269).

SSE reassembly copies the whole message object from `message_start` and every
field `message_delta` finalizes, then lets content deltas fill in `text`,
`thinking` and `input`. Copying rather than picking is what keeps
`stop_details`, `stop_sequence`, `container` and `context_management` — and
whatever the API adds next — in the capture. Each `content_block_start` block
is kept whole for the same reason: `web_search_tool_result` delivers its result
list on the start event and nothing later restores it.

A `data:` line is read with or without the space after the colon. SSE makes
that space optional and the first-party API sends it, so requiring it went
unnoticed until `api.kimi.ai` joined `TARGET_HOSTS` and sent streams without
it — every line was skipped and the all-defaults message went to disk looking
like a real empty turn. A stream nothing parses out of raises instead, and is
captured as a `parse_error` with its bytes in `NNNN.detail.json`.

A non-streaming reply is stored verbatim; only the streamed path is
reassembled.

## Which code wrote a capture

Every capture and detail file opens with `proxy`, the identity of the code
that wrote it:

- `format` — what a reader branches on: two files with the same format hold
  the same keys with the same meanings. The bump rule is at `CAPTURE_FORMAT`
  in `proxy.py`; each version is listed below.
- `blob` — the git blob id of the `proxy.py` that was loaded. `git show
  <blob>` prints that exact source, and `git log --all --format='%h %cs %s'
  --find-object=<blob>` lists the commits that added or removed it. A blob no
  commit holds was loaded uncommitted: git keeps it only if it was staged, and
  only until `git gc` prunes it.
- `source` — the file that was loaded, which names the checkout. One checkout
  can have several paths: this container mounts the canonical one at both
  `/repos/claude-config` and `/home/alan/repos/claude-config`. Compare blobs,
  not paths.
- `mitmproxy` — the library version, which decides where `chunks` split.

The proxy that wrote a capture is not the session's launcher, and its
identity can differ from the revision a transcript's `<launch-provenance>`
gives for `claude.sh`. One `mitmdump` serves every session for the life of
the container: the personal monorepo's `docker/entrypoint.sh` starts it from
the canonical checkout. It reloads `proxy.py` within a second of any edit, so
one session's captures can carry two blobs.

Captures without `proxy` predate format 1, so their layout has to be read off
their keys: `http` is absent before 2026-09-30.

### Format versions

| `format` | What changed |
| --- | --- |
| 1 | First stamped format: the layout this README describes, with `NNNN.detail.json` beside each failed call |

## The `http` region

Everything about the call the body cannot say: the method, the URL with its query
string, every request header as an ordered `[name, value]` pair, and the
response's status and headers. Pairs rather than an object because
`Headers.items(multi=True)` keeps a repeated header and the send order, where
`dict()` joins duplicates with `, `.

`anthropic-beta` is the reason the region exists. It varies per request inside
one session — measured on cc 2.1.269, an auxiliary call carried 8 entries and the
main call 14, the main one adding `claude-code-20250219`,
`mid-conversation-system-2026-04-07`, `mid-conversation-tool-changes-2026-07-01`,
`advanced-tool-use-2025-11-20`, `effort-2025-11-24`, `fallback-credit-2026-06-01`
and `extended-cache-ttl-2025-04-11` — so no sibling capture, model id or client
version implies it.

`authorization`, `x-api-key`, `cookie` and `proxy-authorization` never reach
disk. `credential` records the slot instead — which header, which scheme, how
many characters — which is enough to tell an OAuth bearer from an API key and to
know where a replay puts its own.

`http.response.status` is set on every call, 200 included; the top-level
`error.status` a failed call carries is unchanged.

Captures written before 2026-09-30 have no `http` key. Their beta lists are
unrecoverable, and `agent-tools cc-replay` refuses to re-send one as if it were
faithful.

## What a capture does not record

Losses that no capture records:

- **A call that never produced a response.** A stream cut mid-body, an
  unreachable origin, a client abort: mitmproxy routes these to the `error`
  hook, which drops the flow's state and writes nothing — not even the request
  half. The client still sees the failure; the capture does not.
- **The body of a call whose addon was replaced mid-flight.** mitmdump
  rebuilds the addon when its script file changes, and the new instance has no
  record of a response already in progress. It never saw the body, so its
  capture and `NNNN.detail.json` carry none: a 200 becomes a `parse_error`
  reading `ValueError: response body not captured: the addon was reloaded
  mid-call`, with a `parse-response` line in `requests-log/_errors/errors.log`.
  Editing `proxy.py` while sessions are running costs those response bodies.
- **Everything that is not conversation-shaped.** `TARGET_HOSTS` and the
  `model` + `messages` filter both run before any logging, so a failure on
  OAuth refresh or on telemetry is never seen. `count_tokens` requests carry
  both keys and are captured.
- **Anything about a session that did not start under the proxy.** See below.

## Which sessions are captured

A call is captured only if the session process had `HTTPS_PROXY` pointed at
this proxy when it started. `scripts/claude.sh` sets it, and only when
something answers on 9160 at launch — otherwise it warns on stderr and runs
unintercepted. `scripts/kimi.sh` execs `claude.sh`, so a Kimi session is
covered on the same terms, and so is a worktree or prompt-test session:
`agent-tools claude` execs that checkout's `claude.sh`. Subagents are not separate sessions
here: their calls carry the parent's session id and land in the parent's
directory.

## Pass-through streaming

Anthropic API responses are relayed to the client chunk by chunk and captured on
the way past, so an intercepted session still renders token by token. This is not
mitmproxy's default and the addon has to ask for it: `responseheaders` installs a
`flow.response.stream` callable that appends each chunk to a buffer and returns it
unchanged, and `response` hands that buffer back to `flow.response.raw_content` so
the capture decodes exactly as an unstreamed body would.

Without it mitmproxy buffers the entire body before the `response` hook runs and
sends the client its first byte — **status line included** — only once the server
is done. Measured against a local SSE origin emitting 4 events 0.4s apart: direct,
the client saw them at 0.001s / 0.401s / 0.802s / 1.202s; through the buffering
addon it saw one 320-byte delivery at 1.651s. `tests/test_intercept_proxy.py` pins
both halves — the relay and the capture — against a real `mitmdump`.

What makes this a correctness problem rather than a cosmetic one is that Claude
Code (read on **2.1.269**) cancels a first-party request whose response headers
are late, and reaching the API through `HTTPS_PROXY` leaves it first-party. The
window is computed per attempt rather than fixed: 180s for a first-party
provider plus 1s per 32KB of request body, capped at `API_TIMEOUT_MS - 1000`,
and an escalated retry takes the 599s cap instead. Under a buffering proxy that
window has to cover the whole generation, so long turns abort. No intercepted
session has been observed aborting — the window is read off the source, joined
to the measured fact that headers are withheld to the end. Claude Code's own
error text for that failure names the cause: *"If a
proxy or gateway on your network holds responses until they complete, raise
API_TIMEOUT_MS or CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS to wait longer."* The
measurement, the watchdog's arithmetic and the source citations are in
`notes/intercept-proxy-response-buffering.md`.

mitmproxy's `store_streamed_bodies` option would also preserve the capture, and is
deliberately not used: it is global, so it would buffer every streamed body from
every host the proxy sees, and it lives in `run-proxy.py` rather than in the addon
— leaving a bare `mitmdump -s proxy.py` (documented above) writing empty captures.

## Architecture

```
Client ──CONNECT──▶ mitmproxy (127.0.0.1:9160)
                      │
                      ├─ api.anthropic.com ─┐
                      │                     │
                      ├─ api.kimi.ai ───────┼─▶ MITM ──▶ relay each chunk
                      │                     │            onward, capture it,
                      ├─ api.z.ai ──────────┘            log at end
                      │
                      └─ other hosts ──────────────────▶ pass through
```

`proxy.py` is a mitmproxy addon. mitmproxy handles TLS, MITM certs, and the
CONNECT tunnel. The addon filters for Anthropic-shaped API calls, resolves sessions,
streams and captures response bodies, parses the captured SSE, and writes log
entries per-session.

`TARGET_HOSTS` is the filter. It holds the first-party API and the two
Anthropic-compatible endpoints this repo's sibling launchers point
`ANTHROPIC_BASE_URL` at — `api.kimi.ai` for `scripts/kimi.sh`, `api.z.ai` for
`scripts/zai.sh` — because a host outside the tuple is not an error anywhere:
the flow passes through and that session simply leaves no request log. Traffic
to any of them is captured in the same format; the log carries the model id, so
Kimi, GLM and first-party requests stay distinguishable.

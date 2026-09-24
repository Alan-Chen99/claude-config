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

### With Node.js Claude CLI

Node.js `fetch` (undici) requires `--use-env-proxy` to honor `HTTPS_PROXY`:

```bash
HTTPS_PROXY=http://127.0.0.1:9160 \
NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem \
NODE_OPTIONS="--use-env-proxy" \
claude
```

### With native Claude binary

Add the CA to the system certificate store:

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
The request half is a complete conversation, so `cc-pretty-intercept` renders
these.

A refusal is not an HTTP error: it arrives on a 200 stream as `stop_reason:
"refusal"` with `stop_details` carrying `category` (`reasoning_extraction`,
`cyber`, …) and `explanation`. Claude Code then shows the user a locally
synthesized `invalid_request` message, so the transcript and the capture
describe the same event in different words.

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

A non-streaming reply is stored verbatim; only the streamed path is
reassembled.

## What a capture does not record

Four losses. None of them produces a capture, and only one leaves any
trace at all:

- **A call that never produced a response.** A stream cut mid-body, an
  unreachable origin, a client abort: mitmproxy routes these to the `error`
  hook, which drops the flow's state and writes nothing — not even the request
  half. The client still sees the failure; the capture does not.
- **A capture whose addon was replaced mid-flight.** mitmdump rebuilds the
  addon when its script file changes, and the new instance has no record of a
  response already in progress, so that capture is dropped with one
  `parse-response` line in `requests-log/_errors/errors.log` naming no session
  and no request. Editing `proxy.py` while sessions are running costs those
  captures.
- **Everything that is not conversation-shaped.** The `model` + `messages`
  filter runs before any logging, so a failure on `count_tokens`, on OAuth
  refresh, or on telemetry is never seen.
- **Anything about a session that did not start under the proxy.** See below.

## Which sessions are captured

A call is captured only if the session process had `HTTPS_PROXY` pointed at
this proxy when it started. `scripts/claude.sh` sets it, and only when
something answers on 9160 at launch — otherwise it warns on stderr and runs
unintercepted. `agent-tools claude` does not set it at all, so worktree and
prompt-test sessions produce no captures. Subagents are not separate sessions
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
                      ├─ api.anthropic.com ──▶ MITM ──▶ relay each chunk onward,
                      │                                 capture it, log at end
                      └─ other hosts        ──▶ pass through
```

`proxy.py` is a mitmproxy addon. mitmproxy handles TLS, MITM certs, and the
CONNECT tunnel. The addon filters for Anthropic API calls, resolves sessions,
streams and captures response bodies, parses the captured SSE, and writes log
entries per-session.

# claude-intercept

Intercepts Claude Code API calls and logs request/response pairs as JSON. Two modes:

1. **MITM proxy** (primary) — Python/mitmproxy, works with any HTTP client including native binaries
2. **Fetch override** (legacy) — TypeScript, in-process hook via `NODE_OPTIONS --require`

## Setup

```bash
cd scripts/intercept
pip install mitmproxy    # proxy mode
npm install && npm run build  # fetch override mode
```

## Proxy mode

Start the always-running MITM proxy:

```bash
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

### Session tracking

The proxy extracts `X-Claude-Code-Session-Id` from HTTP headers (sent by
Claude Code on every API request) and includes it in log entries as `session_id`.

## Fetch override mode (legacy)

Still works for Node.js-based Claude where in-process interception is preferred:

```bash
NODE_OPTIONS="--require $(pwd)/dist/intercept.js" claude
```

## Log format

Proxy logs go to `~/.claude/requests-log/proxy/0001.json`, `0002.json`, etc.
Fetch override logs go to `~/.claude/requests-log/{session-id}/001.json`, etc.

```json
{
  "timestamp": "2026-05-15T...",
  "duration_ms": 1234,
  "session_id": "abc-123",
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
    "usage": { "input_tokens": 1000, "output_tokens": 200 }
  }
}
```

## Architecture

### Proxy mode

```
Client ──CONNECT──▶ mitmproxy (127.0.0.1:9160)
                      │
                      ├─ api.anthropic.com ──▶ MITM ──▶ log + forward
                      └─ other hosts        ──▶ pass through
```

`proxy.py` is a mitmproxy addon. mitmproxy handles TLS, MITM certs, and the
CONNECT tunnel. The addon filters for Anthropic API calls, parses SSE streams,
and writes log entries. Python makes observability integrations (Langfuse,
Datadog, etc.) straightforward via their well-maintained SDKs.

### Fetch override mode

Claude Code bundles `@anthropic-ai/sdk` inline, so OTel module hooks can't
intercept it. `globalThis.fetch` is the only viable in-process hook.

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
    "usage": { "input_tokens": 1000, "output_tokens": 200 }
  }
}
```

## Architecture

```
Client ──CONNECT──▶ mitmproxy (127.0.0.1:9160)
                      │
                      ├─ api.anthropic.com ──▶ MITM ──▶ log + forward
                      └─ other hosts        ──▶ pass through
```

`proxy.py` is a mitmproxy addon. mitmproxy handles TLS, MITM certs, and the
CONNECT tunnel. The addon filters for Anthropic API calls, resolves sessions,
parses SSE streams, and writes log entries per-session.

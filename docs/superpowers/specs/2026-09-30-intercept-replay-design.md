# A capture records the whole HTTP call, and a replay re-sends it

`scripts/intercept/proxy.py` reads exactly two things off a request: the JSON body
(`flow.request.get_content()`, `:374`) and the session id header (`:387`). Method,
URL, every other header, and the response's status and headers are never touched.
A capture is therefore a conversation, not a call — and a conversation cannot be
put back on the wire.

## Measured

Throwaway addon on port 9161 dumping full request and response heads, one
`claude -p 'reply with the single word: ok' --max-turns 1` routed through it,
Claude Code 2.1.269, 2026-09-29. The live proxy on 9160 was untouched. 13 flows
reached `api.anthropic.com`; two were `/v1/messages`.

| | aux call | main call |
| --- | --- | --- |
| path | `/v1/messages?beta=true` | `/v1/messages?beta=true` |
| body | 4,145 bytes | 69,756 bytes |
| `anthropic-beta` entries | 8 | 14 |

The main call's extra seven: `claude-code-20250219`,
`mid-conversation-system-2026-04-07`, `mid-conversation-tool-changes-2026-07-01`,
`advanced-tool-use-2025-11-20`, `effort-2025-11-24`, `fallback-credit-2026-06-01`,
`extended-cache-ttl-2025-04-11`.

**The beta list differs per request inside one session.** It cannot be inferred
from a sibling capture, from the model id, or from the Claude Code version. It is
the request half's largest unrecorded semantic input, and nothing else on disk
implies it.

Lost with it, per call:

| Field | Why it is worth having |
| --- | --- |
| `?beta=true` | The endpoint actually addressed |
| `X-Stainless-Retry-Count` | Whether this was a first attempt or a retry |
| `X-Stainless-Timeout: 600` | The client deadline in force |
| `anthropic-dispatch-id: v2d` | Server-side routing the request asked for |
| `anthropic-version: 2023-06-01` | The API contract the body was written against |
| response `request-id` | The one identifier Anthropic support asks for |
| 13 `anthropic-ratelimit-unified-*` | 5h/7d utilization, reset epochs, overage status at send time |
| response status on success | Only a non-200 records a status today (`error.status`) |

The credential is `Authorization: Bearer` + 108 characters, matching
`~/.claude/.credentials.json` → `claudeAiOauth.accessToken` exactly. That file also
carries `expiresAt` as epoch milliseconds.

Serialized as JSON, request headers measured 1.0–1.2 KB and response headers
1.4 KB. Against the 94,820 captures and 36 GB now on disk, adding both to every
future capture is roughly +2.5 KB each, +0.6%.

## The capture gains one `http` region

```json
"http": {
  "method": "POST",
  "url": "https://api.anthropic.com/v1/messages?beta=true",
  "http_version": "HTTP/1.1",
  "request_headers": { "anthropic-beta": "...", "x-app": "cli", ... },
  "credential": { "header": "Authorization", "scheme": "Bearer", "length": 115 },
  "response": { "status": 200, "reason": "OK", "headers": { ... } }
}
```

`authorization`, `x-api-key`, `cookie` and `proxy-authorization` are dropped before
the entry is built. `credential` names the slot a replay must fill and how long the
value was, so a reader can tell an OAuth bearer from an API key without the secret
ever reaching disk.

`http.response.status` is set on every call, 200 included. The existing top-level
`error.status` / `statusText` stay where they are: `cc_pretty_intercept/convert.py`
reads them, and moving them would be a rename dressed as a feature.

A capture written before this change has no `http` key. Every reader must treat it
as optional, and `cc-replay` treats its absence as a named state rather than as an
empty header set — see "Captures recorded before this change".

## `agent-tools cc-replay`

Two subcommands, because the editable artifact between them is the point.

### `extract <capture.json> <dir>`

Writes three files and nothing else:

| File | Content |
| --- | --- |
| `request.json` | The request body, verbatim, pretty-printed |
| `http.json` | `method`, `url`, `http_version`, `request_headers`, `credential`, and `headers_source` — `"captured"` or `"synthesized"` |
| `meta.json` | Source capture path, session metadata, original timestamp, original `duration_ms`, original response status, `request-id`, and `usage` |

Refuses a non-empty `<dir>` unless `--force`. Nothing in the directory is a
secret, so it is safe in a scratchpad.

`http_version` is recorded and not acted on. `send` speaks HTTP/1.1, which is what
every measured flow used; a capture reading otherwise is a finding worth looking at
rather than an instruction to follow.

### `send <dir>`

Reads `request.json` and `http.json`, resolves a credential, sends, and writes
`result-NNNN.json` — in the capture format, so `cc-pretty-intercept` renders it
with no new front-end — plus `result-NNNN.sse`, the decoded SSE text.

Before sending it prints the URL, the beta list, the resolved credential's source,
the request body size and the model. `--dry-run` prints that and stops.

`result-NNNN.json` carries the same `timestamp` / `duration_ms` / `request` /
`response` / `http` shape a proxy capture has, plus one region of its own:

```json
"replay": {
  "source": "/root/.claude/requests-log/<session>/0007.json",
  "sent_at": "2026-09-30T...",
  "headers_source": "captured",
  "deviations": ["x-client-request-id", "x-stainless-retry-count", "content-length", "host"]
}
```

Reassembly goes through the proxy's own `parse_sse_stream`. A replay shaped by a
second reassembler is not comparable to the capture it is being compared against,
which is the only reason to have made it.

**A first-party replay spends the subscription's unified 5h/7d limit.** Re-sending
the 69,756-byte main call above is a real call against a real quota, not a
rehearsal. The response's `anthropic-ratelimit-unified-*` headers land in the
result's `http.response.headers`, so what it cost is on the record.

### Which headers are not repeated verbatim

Four, each because repeating it would assert something false:

| Header | Sent instead | Why |
| --- | --- | --- |
| `x-client-request-id` | A fresh UUID | It identifies one attempt; reusing it claims this is that attempt |
| `X-Stainless-Retry-Count` | `0` | This send is not a retry of anything |
| `Content-Length` | Recomputed from `request.json` | The body is meant to be edited |
| `Host` | Set by the client from the URL | Sending both leaves two sources of truth for one destination |

`X-Claude-Code-Session-Id` **is** repeated. It reached Anthropic on the original
call, so a faithful re-send carries it. `send` does not route through
`HTTPS_PROXY`, so no second capture lands in that session's log directory.

Every other captured header goes out as captured, `anthropic-beta` first among
them. `Accept-Encoding` included: `brotli` and `zstandard` are both importable in
`~/.claude/venvs/claude-config`, so `httpx` 0.28.1 decodes the `gzip, deflate, br,
zstd` Claude Code asks for. The stored `.sse` is the decoded text — the same bytes
the proxy's `get_content()` hands its reassembler — not the wire encoding.

### Credential resolution

By host, first hit wins, and `send` always names the one it used:

| Host | Source | Header |
| --- | --- | --- |
| `api.anthropic.com` | `~/.claude/.credentials.json` → `claudeAiOauth.accessToken` | `Authorization: Bearer` |
| `api.anthropic.com` | `ANTHROPIC_API_KEY` | `x-api-key` |
| `api.kimi.ai` | `KIMI_API_KEY` | `Authorization: Bearer` |
| `api.z.ai` | `ZAI_API_KEY` | `Authorization: Bearer` |

A `claudeAiOauth` entry whose `expiresAt` has passed is refused by name rather
than sent and left to fail as a 401. `--credential-env VAR` overrides the table.

The OAuth store is home-rooted, so `cc-replay` works from a worktree, which has no
`.env` and therefore no `ANTHROPIC_TOKEN_COUNT_API_KEY` either.

Whether `claude-code-20250219` is gated to the OAuth credential path is unverified.
An API-key replay of a capture whose betas include it may differ for a reason that
has nothing to do with the body, and `send` naming its credential source on every
run is what makes that visible rather than mysterious.

## Captures recorded before this change

All 94,820 of them have no `http` region. `extract` still works: `http.json` gets
`headers_source: "synthesized"`, a minimal header set (`anthropic-version:
2023-06-01`, `content-type`, `accept`), an empty beta list, and a URL assembled from
the model id: `k3*` → `api.kimi.ai`, `glm*` → `api.z.ai`, anything else →
`api.anthropic.com`, each with the path `/v1/messages?beta=true`. Both halves of
that URL are guesses. The host is a guess because no capture records one; the path
is a guess because `?beta=true` is what 2.1.269 sent and nothing says an older
capture's session did.

`send` **refuses** a synthesized `http.json` until `--accept-synthesized-headers`.
A re-send missing the original beta list is a different call, and that difference
is exactly what a diagnosis would otherwise attribute to the model.

## Rendering

`cc-pretty-intercept` gains one always-on line when `http` is present: URL, status,
`request-id`, and the beta list. `--show-http` dumps every request and response
header, rate-limit utilization included.

Always-on rather than flag-gated because a region no render shows is a region
nobody reads, and the beta list is not something anyone would think to go looking
for until it has already misled them.

## Where the shared reassembler lives

`cc_replay` loads `scripts/intercept/proxy.py` by path through `importlib`, the way
`tests/test_intercept_proxy.py` already does, and takes `parse_sse_stream` from it.
The loader is defined once, in `cc_replay`, and the test imports it from there.

The dependency runs that direction and not the other because `proxy.py` imports
nothing outside the standard library. Making it import `claude_config` would break
the bare `mitmdump -s proxy.py` invocation the README documents — the same
invocation whose survival was the stated reason to reject mitmproxy's
`store_streamed_bodies` option, so breaking it here would reverse a decision
already made on the record.

## Wiring

- `Cmd::CcReplay { args }` in `agent-tools/src/main.rs`, dispatching to
  `python3 -m claude_config.cc_replay.main`, matching `CcPrettyIntercept`.
- `cc-replay = "claude_config.cc_replay.main:main"` under `[project.scripts]`.
- `httpx` added to `dependencies` explicitly. It is present today only as a
  transitive dependency of `anthropic`; a module that imports it should say so.

`httpx` rather than the `anthropic` SDK because the SDK sets its own
`X-Stainless-*` headers from its own environment, and fighting a client that
rewrites the headers being reproduced is a losing shape for a tool whose purpose
is reproducing them.

## Tests

`tests/test_intercept_proxy.py`, against the existing local-origin mitmdump
harness:

- request headers reach the capture, `anthropic-beta` among them
- `authorization` and `x-api-key` do not, and `credential` describes the slot
- `http.response.status` is 200 on a success, not only on an error

`tests/test_cc_replay.py`, new, against a local fake origin — the pattern
`test_intercept_proxy.py` already establishes:

- `extract` → edit `request.json` → `send` round-trips, and the result loads under
  `cc-pretty-intercept`
- a synthesized `http.json` is refused without the flag and accepted with it
- credential resolution picks by host, names its source, and refuses an expired
  `claudeAiOauth`
- the four deviating headers deviate and every other header does not
- `extract` refuses a non-empty directory without `--force`

## What this does not do

- **Normal captures still store no raw SSE.** Reassembly copies whole message
  objects and every field `message_delta` finalizes, so what it loses is `ping`
  events, event ordering and per-event timing. Storing raw for every capture would
  roughly double response bytes on a 36 GB tree to recover three things no
  diagnosis has yet needed. Replay results store it because replays are few and
  comparing streams is what a faithful re-send is for.
- **Nothing retroactively recovers a beta list.** The 94,820 existing captures
  cannot be faithfully replayed, and no amount of later work changes that.
- **The five losses in `scripts/intercept/README.md`, "What a capture does not
  record", are untouched.** A call that never produced a response still writes
  nothing, request half included. Recording the request half of a failed flow is a
  separate change to the `error` hook, not part of this one.

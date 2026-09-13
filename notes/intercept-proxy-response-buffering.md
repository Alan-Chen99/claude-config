# The intercept proxy held every response until the model finished

Investigated 2026-09-13 against **mitmproxy 12.2.3** and **Claude Code 2.1.269**, and
fixed the same day in `scripts/intercept/proxy.py`. Every `chunk-*.js:LINE` citation
below is the 2.1.269 reading; line numbers rotate every build, so
`.claude/skills/update-claude-code/citecheck.sh` is what says whether they still
resolve.

`scripts/intercept/proxy.py` implemented `request()` and `response()` only. mitmproxy's
`response` hook fires after the complete body has been read from the server, and the
default path then sends the client the status line, the headers and the whole body in
one go. An intercepted Claude Code session therefore received nothing at all until the
model had finished generating, and the SSE stream it thought it was reading was a
recording.

## Measured

A local origin emitting 4 chunked SSE events 0.4s apart, read by a socket client that
timestamps every arrival:

| | first arrival | arrivals carrying events |
|---|---|---|
| direct to the origin | 0.001s | 4, at 0.001 / 0.401 / 0.802 / 1.202 |
| through `mitmdump -s proxy.py` | **1.651s** | 1, a single 320-byte delivery |
| through an addon setting `flow.response.stream = True` | 0.009s | 4, at 0.009 / 0.409 / 0.809 / 1.209 |

The status line is inside that 1.651s delivery: buffering delays the response headers,
not just the body.

## Why mitmproxy did that

`HttpStream` decides at the `responseheaders` hook and nowhere else
(`mitmproxy/proxy/layers/http/__init__.py:427`): if `flow.response.stream` is falsy it
enters `state_consume_response_body`, and `:516-527` sends headers and content together
afterwards. The only other way in is the `stream_large_bodies` size threshold, which
defaults to `None` (`mitmproxy/addons/proxyserver.py:165`). Nothing here set either, so
the addon got the default, not a decision.

## What it cost a session

Rendering is the visible half: no token-by-token output, the whole turn appearing at
once. The load-bearing half is that Claude Code cancels a request whose response headers
are late.

`pFn(OS, {escalated: Wwe.count > 0})` arms a first-byte watchdog before every
`beta.messages.create` (`src/chunk-dbb93264.js:188736`). `Szo` (`:95261-95274`) sizes the
window as `gzo(provider) + 1s per 32KB of request body`, capped at `API_TIMEOUT_MS - 1000`
(600,000 default). For a first-party provider `gzo` resolves through `UFe`/`mzo` to
`pzo = 180000` (`:95222`). `Jrn` (`src/chunk-t22vfrah.js:379`) then picks
`firstWindowMs` on the first attempt and `retryWindowMs` — the 599s cap — on the
escalated retry. `kzo` (`:95291`) aborts the fetch and logs
`[first-byte] no response headers 180s after dispatch`.

It is first-party through the proxy because `wo()` (`src/chunk-4728jcqn.js:1246`) tests
`ANTHROPIC_BASE_URL` against `api.anthropic.com`, and `scripts/claude.sh` routes with
`HTTPS_PROXY`, which leaves the base URL alone.

Claude Code's own message for this failure names the cause (`:93492`): *"If a proxy or
gateway on your network holds responses until they complete, raise API_TIMEOUT_MS or
CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS to wait longer."*

The per-chunk idle watchdog (`wzo`, `:95359`, "stream idle: no bytes for Xms",
`CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS`) is **not** the one that fires. It wraps the
response body's `ReadableStream` and resets on each chunk, so it starts only once the
headers arrive — by which point a buffering proxy has the entire body local and delivers
it without a gap. Buffering hides from the watchdog built to notice stalls, and trips the
one built to notice silence.

Not measured: no live intercepted session was observed aborting. The 180s figure is read
off the source above, joined to the measured fact that headers are withheld to the end.

## The fix

`responseheaders` installs a `flow.response.stream` callable that appends each chunk to a
per-flow `bytearray` and returns it unchanged; `response()` assigns that buffer to
`flow.response.raw_content`, which streaming leaves unset, so the existing
`get_content()` call decodes it exactly as it decoded a buffered body.

mitmproxy's `store_streamed_bodies` option (`addons/proxyserver.py:148`) would preserve
the capture too, and was rejected on two counts: it is global, so every streamed body
from every host the proxy sees would be held in memory, and it would have to be passed by
`run-proxy.py`, leaving the bare `mitmdump -s proxy.py` invocation the README documents
writing captures with empty bodies.

`tests/test_intercept_proxy.py` drives a real `mitmdump` for both halves. Each was
confirmed to fail without its half of the fix: reverting `proxy.py` to the buffering
version gives `events arrived in 1 delivery(s)`, and disabling the `raw_content` restore
alone leaves no capture on disk at all — the body comes back `None`, reassembly raises,
and `log_error` diverts it to `requests-log/_errors/errors.log`.

## What would retire this note

A mitmproxy release that changes how `flow.response.stream` is declared, or a Claude Code
release that moves the first-byte watchdog's numbers. The citations are checked for
resolution, not for meaning — confirm the arithmetic still reads as above rather than
trusting a clean `citecheck.sh`.

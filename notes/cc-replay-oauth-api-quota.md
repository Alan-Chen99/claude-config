# A Claude Code OAuth token cannot replay its own captures

Measured 2026-09-30 while verifying `agent-tools cc-replay` against the live API.
Re-sending a captured first-party request with the credential Claude Code itself
used returns **429 `rate_limit_error`** every time, while an interactive `claude -p`
in the same minutes succeeds. The tool is not at fault and no wait clears it: the
OAuth token and an API key resolve to **different organizations**, and only one of
them has API-tier quota.

Cost of not knowing this: a ~15-request bisect across beta lists, header sets and
cold-wait intervals, all of it chasing a difference that was never in the request.

## Evidence

Two sends of one 672-byte body — same URL, same 14 betas, same header pairs, same
minute — differing only in the credential:

| | credential | organization | workspace | result |
| --- | --- | --- | --- | --- |
| `result-0003` | `~/.claude/.credentials.json` → `claudeAiOauth` | `29f2cf32-1268-49fe-8794-9032b532a49a` | `wrkspc_01E5htksvph9ABKNhJVe1K84` | `429`, `x-should-retry: true` |
| `result-0004` | `$ANTHROPIC_TOKEN_COUNT_API_KEY` on `x-api-key` | `fe1cc32a-6b1e-42b3-87d0-14cbadb2936d` | `wrkspc_01RQZFrrnJtgAGMGu6HtqJaL` | `200`, in 27 / out 22 |

Both 429 and 200 report an organization and a workspace, so **the OAuth token
authenticates fine** — it is refused on quota, not on identity.

What the headers say, and the reason a retry is futile:

- The 429 carries **no `anthropic-ratelimit-unified-*` header at all**. A capture
  taken from a succeeding `claude -p` in the same window carries a full set, at
  `0.19` 5h utilization — so the subscription window had capacity and was not
  what refused the replay.
- The 200 carries ordinary API limits: `requests-limit: 10000`,
  `input-tokens-limit: 10000000`, `tokens-limit: 12000000`, all but one request
  remaining.
- An earlier probe of the OAuth organization reported
  `anthropic-ratelimit-unified-overage-status: rejected` with
  `overage-disabled-reason: out_of_credits`.

Read together: two limiters share one status code. The subscription's unified
window announces itself in headers and drains over time; a want of API quota
announces nothing and never drains.

The error body distinguishes neither — it is
`{"type":"error","error":{"type":"rate_limit_error","message":"Error"}}` in both
cases, which is why the headers are the only signal and why
`cc_replay/main.py:rate_limit_note` reads them back out on every 429.

## What this rules out

Each of these was tested against the OAuth credential and made no difference —
every one still returned 429:

- Dropping `claude-code-20250219`, `oauth-2025-04-20`, or either half of the beta
  list.
- Dropping `X-Claude-Code-Session-Id`, the dispatch id, or the `x-stainless-*` and
  `user-agent` families; and adding them back one at a time.
- Reducing the body to four headers and a single user turn.
- Waiting 120 seconds cold with no other API call from the session.

The one 400 seen during the bisect (`context_management: Extra inputs are not
permitted`) came from a body that was invalid without its beta. It proves only
that **validation precedes rate limiting** — an invalid request never reaches the
limiter, so a 400 is not evidence that quota was available.

The API key accepted the capture's entire beta list, `claude-code-20250219` and
`oauth-2025-04-20` included. **No beta is gated to the OAuth path**, which is what
the bisect was implicitly testing for.

## Consequence for a replay

A faithful replay of a first-party capture needs an API key:

```
agent-tools cc-replay send <dir> \
  --credential-env ANTHROPIC_TOKEN_COUNT_API_KEY --credential-header x-api-key
```

This is the one respect in which a faithful replay cannot be faithful. The
credential differs from the captured call's by necessity — a capture never stores
one — and on this machine it must also differ in kind. The replay is otherwise
byte-identical apart from the five headers `agent-tools/CLAUDE.md` lists.

`--credential-header` matters because the two shapes are not interchangeable: an
OAuth token goes on `Authorization: Bearer`, an API key on `x-api-key` unprefixed,
and each on the other's header is a 401.

## What would change this

An OAuth replay starts working the moment the subscription organization is given
API credits; nothing in this repo would need to change. To re-test, send one
request with the default credential and read the summary line — a 429 naming
organization `29f2cf32…` with no unified header means the finding still holds.

# A Claude Code OAuth token is honored only for Claude Code's system prompt

Measured 2026-09-30 while verifying `agent-tools cc-replay` against the live API on
Claude Code **2.1.269**. Re-sending a captured first-party request with the
credential Claude Code itself used works — unless the request's `system` block has
been edited. Replace it and `/v1/messages` answers **429 `rate_limit_error`** with
no `anthropic-ratelimit-unified-*` header, in the same organization and the same
minute that the unedited body returns 200. It is a scope rejection wearing a
rate-limit status, and no wait clears it.

This is the one real constraint on what-if editing under the OAuth credential.
Everything else in the body is fair game.

## Evidence

One mutation at a time from a live capture
(`~/.claude/requests-log/4103b09d-.../0002.json`, 85,970 bytes), OAuth credential
throughout, all within four minutes:

| body | result |
| --- | --- |
| unedited | `200`, in 2 / out 4 (27,567 cache read) |
| `max_tokens` → 1024 | `200`, in 2 / out 4 |
| `messages` → one short user turn | `200`, in 82 / out 5 |
| `tools` → `[]` | `400 invalid_request_error` |
| `system` → `"You are a helpful assistant."` | **`429 rate_limit_error`** |

Both the 200 and the 429 report `anthropic-organization-id:
29f2cf32-1268-49fe-8794-9032b532a49a` and the same workspace, so the token
authenticates and the organization is not the variable.

The 200s carry a full unified set — `unified-status: allowed`, `5h-utilization:
0.21`, `7d-utilization: 0.46`. The 429 carries **no `anthropic-ratelimit-unified-*`
header at all**: the request never reached the subscription limiter. That absence
is the only machine-readable signal, because the error body is
`{"type":"error","error":{"type":"rate_limit_error","message":"Error"}}` with no
further detail — which is why `cc_replay/main.py:rate_limit_note` branches on it.

The `tools: []` 400 is unrelated to the gate and worth knowing on its own:
`tool_reference_unresolved`, *"messages.1.content.1: tool_addition/tool_removal
references unknown tool 'mcp__claude_ai_Claude_Docs__batch'"*. Under the
`mid-conversation-tool-changes-2026-07-01` beta the transcript carries
`tool_addition`/`tool_removal` blocks that name tools, so `tools` and `messages`
have to stay consistent with each other — emptying one alone is an invalid body,
not a refused one.

An API key on `x-api-key` has no such constraint: it returned 200 for a body whose
`system`, `messages` and `tools` had all been replaced, accepting the capture's
entire beta list, `claude-code-20250219` and `oauth-2025-04-20` included. **No beta
is gated to the OAuth path.**

## How this was originally misdiagnosed

Worth recording, because the wrong answer was convincing and cost about fifteen
live requests.

The first replay attempts all used a hand-minimized body — `messages`, `system`,
`tools` and `max_tokens` all reduced at once — and every one returned 429. The
bisect that followed varied the beta list, the `x-stainless-*` and `user-agent`
header families, `X-Claude-Code-Session-Id`, and the cold-wait interval, and moved
nothing, because the system prompt stayed replaced in every arm.

Switching to an API key then produced a 200, and the two runs differed in *both*
credential and body. Attributing the difference to the credential gave a
self-consistent but false story: the two credentials resolve to different
organizations, so "the OAuth organization has no API quota" fit every datum then in
hand, and `anthropic-ratelimit-unified-overage-status: rejected` with
`overage-disabled-reason: out_of_credits` looked like confirmation. It survived
until a faithful send under OAuth returned 200 from that same "quotaless"
organization.

Two lessons, both cheap next time:

- A 400 seen mid-bisect (`context_management: Extra inputs are not permitted`) was
  read as proof that quota was available. It only proves **validation precedes the
  scope check** — an invalid body never reaches it.
- The unedited capture was the control, and it was never sent until last. Sending
  it first would have isolated the body in one request.

## What would change this

Whether the check inspects the system prompt's exact bytes, a prefix, or something
coarser is unmeasured; only wholesale replacement was tried. A small edit inside an
otherwise intact Claude Code system prompt may well pass. Anyone who needs that
answer can get it in two sends from a fresh capture, and should extend the table
above rather than re-deriving the gate.

Measured 2026-10-08, cc 2.1.289 (`ddc24a3b/0003`, `claude-fable-5-1`, claude.ai
OAuth): cutting the trailing `# Claude in Chrome browser automation` section — 4,107
of `system[2]`'s 25,788 chars, the billing header and identity line untouched —
returns `200` with the full unified header set, 2/2. That `system[2]` was already a
`--system-prompt-file` text, so the check is not on exact bytes; a prefix or
something coarser stays open.

## The gate is not Opus-shaped, but it looks it

Re-measured 2026-10-01, cc 2.1.269. With `system` replaced by one line,
`claude-opus-5`, `claude-opus-4-8`, `claude-opus-4-7` and `claude-sonnet-5` all
return the headerless 429 — and `claude-haiku-4-5-20251001` returns 200 for a
body carrying **no `system` at all**. A haiku control therefore "proves" the
credential works while every Opus id refuses, which reads as a model or quota
gate and is neither; restoring the capture's `system` block returns 200 on
opus-5 and opus-4-8 in the same minute. Adding `metadata.user_id` and
`fallbacks: "default"` individually moves nothing while `system` stays replaced.

A replay also borrows a different credential than the capture used — the on-disk
tokens are 108-char `sk-ant-oat01-…`, a live request carries a 115-char bearer
refreshed in memory and never written back (`http.credential.length` records
which) — but it clears the gate on a faithful body, so that is a footnote and
not a fourth variable.

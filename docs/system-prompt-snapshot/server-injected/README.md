# Server-Injected Text, Captured by Recitation

What the API adds around a request — a tool-use template with its batching
sentence, and the browser-safety section a `mcp__claude-in-chrome__*` tool name
triggers. An intercept capture cannot show it (the proxy logs what the client
sends), so it is captured by having the model recite its system prompt and
checking the known part byte-exactly. Trigger and placement mechanics:
`notes/chrome-tool-names-trigger-server-safety-block.md`. Captured 2026-10-08,
api.anthropic.com, API-key credential, by session `13b1bdb9` — whose own
response was stopped by a safety classifier before it could write any of this
(`notes/response-stopped-by-safety-classifier.md`); the files here were
re-verified and committed by a later session.

## Method

`probe.py OUT MODEL ARM [N]` sends one `/v1/messages` request whose `system`
is the `OPERATOR` text (authorizes verbatim reproduction; embeds fidelity
markers: curly quotes, em dash, ½, ±, trailing double spaces, a blockquote),
whose `tools` hold one no-op — `mcp__claude-in-chrome__noop` (arm `chrome`) or
`mcp__browser-tools__noop` (arm `control`) — and whose one user message asks
for the complete system prompt verbatim between `=====BEGIN=====` /
`=====END=====`, with `[TOOL DEFINITIONS OMITTED]`, `[CALL TAG]` and
`[EXAMPLE CALL OMITTED]` placeholders so nothing recited can execute. The
credential comes from `.env`'s `ANTHROPIC_TOKEN_COUNT_API_KEY`; headers are
never written to the run files. `analyze.py` splits each response into
pre / operator text (the fidelity check) / tail, and writes `<run>.tail.txt`
beside the JSON — regenerate with `python3 analyze.py runs/*.json`.

The tail is: server tool-use template + batching sentence, then the
browser-safety section (chrome arm only), which begins at
`Your priority is to complete` and runs to the end of the tail. Haiku appends
`\n\n[TOOL DEFINITIONS OMITTED]` after it; strip that before hashing.

## Runs

| run | stop | operator byte-exact | tail chars |
|---|---|---|---|
| `claude-opus-5-5` chrome ×3 | 200 `end_turn` | yes | 8,845 |
| `claude-fable-5-1` chrome ×1 | 200 `end_turn` | yes | 8,845 |
| `claude-haiku-4-5-20251001` chrome ×2 | 200 `end_turn` | no — curly quotes straightened | 9,620 |
| `claude-opus-5-5` control ×1 | 200 `end_turn` | yes | 245 |
| `claude-haiku-4-5-20251001` control ×1 | 200 `end_turn` | no — same quote change | 1,020 |

The browser-safety section is byte-identical across all 6 chrome runs:
8,598 chars, sha256 `6a3021729eb3abdbfdbd3da5bb47f50458abe18fd76425c19867a0a0a07df6a3`.
Control tails hold tool-use text only — the section is the chrome arm's whole
difference. The template ahead of it differs by model: haiku-4-5 gets a longer,
older template (hence 9,620 vs 8,845); opus-5-5 and fable-5-1 get the batching
sentence alone. Against the public leak copy
(asgeirtj/system_prompts_leaks `claude-haiku-5.5.md`, a7b30ef) the recited
section differs only in whitespace: the leak carries 6 extra trailing double
spaces and 2 extra newlines (8,612 chars).

## Boundaries

- **API-key credential only.** A claude.ai-login arm — cc-replay with this
  probe's system prompt in place of Claude Code's own, on the subscription
  credential — was the step the classifier stopped; it was not run and is not
  re-planned. The trigger is credential-independent (chrome note); whether the
  section's *text* varies by credential is untested.
- **Recitation is the evidence, not the wire.** The trust argument is the
  prefix: opus-5-5 and fable-5-1 returned the marker-laden operator text
  byte-exact, so their tails are taken as equally faithful. Haiku-4.5
  normalizes curly quotes, fails the prefix check, and its run counts only
  because its section hashes with the other two once the trailing placeholder
  is stripped.
- The section's tokens are uncounted by `usage` and `count_tokens` — sizing it
  needs the leak copy (≈2.5k Opus-5.5 tokens; chrome note).

## Trap

A v1 probe that asked for the tool-use instructions verbatim made the model
copy the template's example call, which executed as a real tool call and ended
the response at `stop=tool_use`. The placeholder lines in the question are the
fix; v1's aborted run stayed in the session scratchpad, not here.

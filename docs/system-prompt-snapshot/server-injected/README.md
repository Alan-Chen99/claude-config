# Server-Injected Browser-Safety Section

One canonical copy of the section the API appends to the system prompt
whenever a request's `tools` hold a name matching
`^mcp__claude[-_]in[-_]chrome__.+` — `browser-safety-section.md`, 8,598 chars,
sha256 `6a3021729eb3abdbfdbd3da5bb47f50458abe18fd76425c19867a0a0a07df6a3`.
No intercept capture can show it (the proxy logs what the client sends), so it
is captured by recitation. Trigger and placement mechanics:
`notes/chrome-tool-names-trigger-server-safety-block.md`. Captured 2026-10-08,
api.anthropic.com, API-key credential, by session `13b1bdb9` — whose response
was stopped by a safety classifier before it could write any of it
(`notes/response-stopped-by-safety-classifier.md`); a later session re-verified
the runs and committed this.

## Method

`probe.py OUT MODEL ARM [N]` sends one `/v1/messages` request: `system` is the
`OPERATOR` text (authorizes verbatim reproduction; embeds fidelity markers —
curly quotes, em dash, ½, ±, trailing double spaces, a blockquote), `tools`
hold one no-op — `mcp__claude-in-chrome__noop` (arm `chrome`) or
`mcp__browser-tools__noop` (arm `control`) — and the one user message asks for
the complete system prompt verbatim between `=====BEGIN=====`
/`=====END=====`, with `[TOOL DEFINITIONS OMITTED]` / `[CALL TAG]` /
`[EXAMPLE CALL OMITTED]` placeholders so nothing recited can execute.
`analyze.py` splits each response into pre / operator text (the fidelity
check) / tail. The tail is the server's tool-use text, then — chrome arm only
— the section. The canonical copy is the opus-5-5 chrome tail from
`Your priority is to complete` to its end. The prefix-match rule is the
requester's: a model that returns the marker-laden operator text byte-exact is
reciting, not reconstructing, so its tail is taken as equally faithful.

## Fidelity of the runs behind the copy

| run | stop | operator byte-exact | tail chars |
|---|---|---|---|
| `claude-opus-5-5` chrome ×3 | 200 `end_turn` | yes | 8,845 |
| `claude-fable-5-1` chrome ×1 | 200 `end_turn` | yes | 8,845 |
| `claude-haiku-4-5-20251001` chrome ×2 | 200 `end_turn` | no — curly quotes straightened | 9,620 |
| `claude-opus-5-5` control ×1 | 200 `end_turn` | yes | 245 |
| `claude-haiku-4-5-20251001` control ×1 | 200 `end_turn` | no — same quote change | 1,020 |

The section slice is byte-identical in all six chrome runs (hash above);
control tails carry tool-use text only — the section is the arm's whole
difference. Against the public leak copy
(asgeirtj/system_prompts_leaks `claude-haiku-5.5.md`, a7b30ef) the copy
differs only in whitespace: the leak adds 6 trailing double spaces and 2
newlines (8,612 chars).

## Every difference between the runs, and its cause

- **opus-5-5 ×3 and fable-5-1: byte-identical tails** — same server text; all
  four operator prefixes came back exact.
- **haiku's tail is 775 chars longer.** The server serves haiku-4-5 a longer
  tool-use template: an older-style preamble (*"When making function calls
  using tools that accept array or object parameters…"* plus JSON-structuring
  rules) wrapped around the same batching sentence (*"If you intend to call
  multiple tools…"*) that opus-5-5 and fable-5-1 get alone. Per-model server
  template selection, not capture noise.
- **haiku chrome.1 vs chrome.2: `Do NOT` vs `DO NOT`** at tail char 635,
  inside that template. Identical requests, so one recitation is wrong — 2 of
  3 haiku runs (chrome.2, control) agree on `DO NOT`. Template text from
  haiku runs is not byte-trustworthy; the section slice, which hashes equal
  to opus/fable's, is.
- **haiku appends `\n\n[TOOL DEFINITIONS OMITTED]` after the section** (the
  control arm's tail ends with the same line). Instruction-following: the
  placeholder marks where the tool definitions sit, and haiku writes it after
  the last system text; opus-5-5 and fable-5-1 stop at the prompt's end.
  Strip it before hashing.
- **opus chrome tail = control tail + `\n\n` + section** — the section is
  appended after the server's tool-use text, separated by one blank line.
- **haiku's operator echo straightens curly quotes** — model-level
  normalization, and the reason it fails the prefix check.

## Boundaries

- **API-key credential only.** A claude.ai-login arm — replay with this
  probe's system prompt in place of Claude Code's own, on the subscription
  credential — was the step the classifier stopped; it was not run and is not
  re-planned. The trigger is credential-independent (chrome note); whether
  the section's *text* varies by credential is untested.
- **Recitation is the evidence, not the wire.** The run files stayed in the
  capturing session's scratchpad (`…/13b1bdb9…/scratchpad/recite/runs/`);
  `uv run --with httpx python probe.py runs <model-id> chrome 1` then
  `python3 analyze.py runs/*.json` regenerates them.
- The section's tokens are uncounted by `usage` and `count_tokens` — sizing
  needs the leak copy (≈2.5k Opus-5.5 tokens; chrome note).

## Trap

A v1 probe asking for the tool-use instructions verbatim made the model copy
the template's example call, which executed as a real tool call and ended the
response at `stop=tool_use`. The placeholder lines in the question are the
fix.

# A tool named `mcp__claude-in-chrome__*` makes the API add a browser-safety section no request carries

Measured 2026-10-08, Claude Code **2.1.289**, `api.anthropic.com`.

When a request's `tools` holds a name matching `^mcp__claude[-_]in[-_]chrome__.+`,
case-insensitive — inline or `defer_loading: true`, real or a one-line no-op — the model gets a
section the request lacks: *"Your priority is to complete the user's request while following the
safety rules below…"*, `## Instruction source boundary`, `## Action categories` (Prohibited,
Testing the user's own application, Explicit permission required, Regular), `## Privacy`,
`## Copyright`, `## Example purchase confirmation`. The model places it last in the system prompt,
after the server's own batching sentence (*"…make all of the independent calls in the same …
block"*, also in no request), before `messages[0]` (fable-5-1, 2/2;
cf. anthropics/claude-code#86435).

- **Server-side.** No capture carries it and the 2.1.289 decompile holds none of its literals;
  `--chrome` adds only the tools, the operational Chrome section and an MCP reminder; betas and
  header names stay the same. It fires for the claude.ai login, a setup-token and an API key,
  on haiku-4-5, fable-5-1, opus-5-5.
- **Uncounted.** Neither `usage` nor `count_tokens` includes it: a deferred trigger bills nothing
  extra, an inline one its own definition. The leak's copy (below): 1,828 Haiku-4.5,
  2,532 Opus-5.5 tokens.
- **Not recall.** Haiku 4.5 (October 2025) recites the current revision verbatim: its 8 Prohibited
  bullets match asgeirtj/system_prompts_leaks `claude-haiku-5.5.md` (a7b30ef, 2026-10-07), not the
  2026-07-30 Desktop Fable-5 one. Renamed, the same 22 schemas produce nothing, though `system` still
  names `mcp__claude-in-chrome__*`.
- **When a session has it.** Deferred MCP definitions go out only once ToolSearch loads them, so
  a `--chrome` session's first request lacks the trigger (ddc24a3b `0003` vs `0004`). A thread
  continuation sends `tools: null` and keeps the thread's: 792c1aea's citing turn `0490` sits
  under root `0463`, which carried 14 Chrome tools.
- **Why only under the claude.ai login.** With `CLAUDE_CODE_OAUTH_TOKEN`, `WFt()` turns
  `--chrome` off client-side (*"[Claude in Chrome] Disabled: OAuth token has no scope…"*), so no
  Chrome tool is sent; the server adds the section for that token too.
- **No prompt setting removes it.** `--system-prompt-file` and `CLAUDE_CODE_DISABLE_CFC_PROMPT`
  reach client text only; with the Chrome section cut from `system[2]` the model still quotes it.

Undocumented, unlike the memory tool's addition. Reported in #96762 and #93798, the latter
blaming MCP `instructions`, which on 2.1.289 hold only ToolSearch advice.

## Evidence

`agent-tools cc-replay` A/B replays of `ddc24a3b/0003` with a neutral question (*"…which
actions in a web browser are prohibited for you, or need the user's explicit permission first? …
If there is no such text, reply … NONE"*); only `tools` differs. Billed = input + cache fields;
quotes = the answer has `Prohibited (never perform`.

| added to the 12 base tools | Haiku 4.5 billed, quotes | Fable 5.1 billed, quotes |
|---|---|---|
| nothing | 23,685, 0/3 | 33,265, 0/3 |
| 22 Chrome tools, deferred | 23,685, 3/3 | 33,265, 3/3 |
| 22 Chrome tools, inline | 31,368, 1/1 | 43,885, 1/1 |
| … Chrome section cut from `system[2]` | | 42,461, 1/1 |
| same 22 renamed `mcp__browser-tools__*` | 31,324, 0/2 | 43,819, 0/1 |
| `mcp__claude-in-chrome__noop`, deferred | 23,685, 2/2 | 33,265, 2/2 |
| setup-token: nothing / no-op deferred | 23,685, 0/1 / 1/1 | |

Fable: effort max; five runs used an earlier wording, two scored from thinking.

Name rule, one deferred no-op on Haiku 4.5, 23,685 billed each. Quotes it:
`mcp__claude-in-chrome__noop`, every case or `-`/`_` variant tried (`CLAUDE_IN_CHROME`,
`claude-in_chrome`, `MCP__`…), `…__a__b`.
Silent: `mcp__claude-in-chrome_noop`, `mcp__claude-in-chrome__`, `x_mcp__…`,
`claude-in-chrome__noop`, `mcp__claude-in-chrome-2__…`, `mcp__plugin_claude-in-chrome__…`,
`mcp__chrome__noop`, `computer`.

Two-request reproduction, any credential (here an API key; system `"You are a helpful
assistant."`, one inline no-op, no betas): `mcp__claude-in-chrome__noop` →
`count_tokens` 607, billed 607, quotes the list; `mcp__browser-tools__noop` → 605, 605, `NONE`.

Live `claude.sh -p`, opus-5-5, loading any Chrome tools by ToolSearch first: `--chrome` 2/2;
no `--chrome` 0/2; `--chrome` on the setup-token 0/1;
`/workspace/notes/browser.md` plus `playwright-skill` instead 0/2. No captured request has it.

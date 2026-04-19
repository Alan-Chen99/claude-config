# Claude Code System Prompt Snapshot

Captured: 2026-04-19
Version: claude-cli/2.1.79 (external, cli)
Model: claude-opus-4-6 (1M context)
Mode: `claude -p` (pipe/non-interactive)

## Files

| File | What |
|---|---|
| `system-prompt.md` | System prompt with custom output style (`alan-default-next`) |
| `system-prompt-default.md` | System prompt with default output style (no custom style) |
| `system-prompt-flag-system-prompt.md` | System prompt with `--system-prompt "You are a custom assistant."` |
| `system-prompt-flag-append.md` | System prompt with `--append-system-prompt "You are a custom assistant."` |
| `full-api-request.json` | Complete API request body with custom output style. Metadata redacted. |
| `full-api-request-default.json` | Complete API request body with default output style. Metadata redacted. |
| `full-api-request-flag-system-prompt.json` | API request with `--system-prompt`. Metadata redacted. |
| `full-api-request-flag-append.json` | API request with `--append-system-prompt`. Metadata redacted. |
| `intercept.js` | Node.js `--require` script that logs API calls to `~/.claude/http-logs/` |
| `CONFIG-VARIATIONS.md` | All configuration knobs that cause the prompt to diverge |

All system prompt files concatenate the 3 system text blocks, separated by
`---BLOCK_SEPARATOR---`.

## How to reproduce

The intercept script (`intercept.js` in this directory) patches `globalThis.fetch`
to dump every API call. Run it via `NODE_OPTIONS='--require'`:

```bash
# Interactive session — logs every API call for the session
NODE_OPTIONS='--require /path/to/intercept.js' claude

# Pipe mode — single prompt
echo "say exactly: hello" \
  | NODE_OPTIONS='--require /path/to/intercept.js' claude -p \
  1>/dev/null 2>/dev/null
```

Output lands in `~/.claude/http-logs/<session>/`:

```
~/.claude/http-logs/2026-04-19T06-00-20_c4cbfc/
  001-system.txt      # system prompt text (blocks joined by ---BLOCK_SEPARATOR---)
  001-request.json    # full API request body (tools, messages, params)
  002-system.txt      # second API call (tool-use follow-up, etc.)
  002-request.json
  ...
```

Each launch creates a new session directory. No cleanup needed between runs.
The main system prompt is typically the largest `*-system.txt` file;
smaller ones are summary/compact calls.

### Why this works

Claude Code is a Node.js application that calls the Anthropic API via `fetch`.
`NODE_OPTIONS='--require ...'` injects a script before the application starts.
The script monkey-patches `globalThis.fetch` to intercept outbound requests,
checks if the URL targets `anthropic`, and dumps the request body to disk on
the first match (the `!fs.existsSync` guard prevents overwriting with
subsequent requests in the same session).

### What didn't work

- `ANTHROPIC_LOG=debug` — logs request structure but Node's `console.log`
  truncates nested arrays/objects to `[Array]` and `[Object]`. Adding
  `NODE_OPTIONS='--require'` with `util.inspect.defaultOptions.depth = null`
  fixes the truncation but produces messy output with JS string concatenation
  artifacts (`' +\n'`) that are hard to parse back into clean text.

- Patching `https.request` — Claude Code uses `fetch`, not the Node `http`/`https`
  module directly.

### Notes

- The `!fs.existsSync` guard captures only the first API call. Claude Code
  may make multiple calls per session (e.g., a second call after tool use).
  Remove the guard to capture all requests.

- `claude -p` (pipe mode) vs interactive mode: the system prompt itself is
  identical. The difference is in user message injection — interactive mode
  adds `system-reminder` blocks for deferred tools, skills, and CLAUDE.md
  context as the conversation progresses, while pipe mode front-loads them
  in the first user message.

- The `metadata.user_id` field in the request contains device/account/session
  UUIDs. Redact before sharing.

## `--system-prompt` vs `--append-system-prompt` comparison

Captured using the same intercept technique with `--system-prompt "You are a custom assistant."` and `--append-system-prompt "You are a custom assistant."`.

### `--system-prompt` replaces block 3 entirely

The entire main prompt (behavioral rules, tool instructions, memory, output style, everything) is replaced with just the custom text. Only the billing header and agent identity survive:

```
Block 1: x-anthropic-billing-header: cc_version=2.1.79.04b; ...   (unchanged)
Block 2: You are a Claude agent, built on Anthropic's Claude Agent SDK.  (generic identity)
Block 3: You are a custom assistant.                                     (your text, nothing else)
```

What still works despite the prompt replacement:
- All 9 tools are still provided (Agent, Bash, Glob, Grep, Read, Edit, Write, Skill, ToolSearch)
- User message injections still fire (deferred tools, skills, CLAUDE.md context)
- API parameters unchanged (model, max_tokens, thinking, etc.)

What's gone:
- All behavioral rules ("Executing actions with care", "Using your tools", etc.)
- Memory system
- Output style
- Git commit/PR instructions
- Output efficiency guidance
- "Doing tasks" section
- Tone and style rules

### `--append-system-prompt` appends to block 3

The default prompt stays intact. The custom text is concatenated at the end of block 3, after git status / recent commits.

One side effect: the agent identity (block 2) changes from the generic form to the Claude Code form:

| Flag | Block 2 identity |
|---|---|
| (none) | `You are a Claude agent, built on Anthropic's Claude Agent SDK.` |
| `--system-prompt` | `You are a Claude agent, built on Anthropic's Claude Agent SDK.` |
| `--append-system-prompt` | `You are Claude Code, Anthropic's official CLI for Claude, running within the Claude Agent SDK.` |

This is because `getCLISyspromptPrefix()` selects the identity based on whether `appendSystemPrompt` is set (see `CONFIG-VARIATIONS.md` section 1).

### Diff summary (vs `system-prompt.md`)

`--system-prompt`: 9 lines total. Block 3 = 1 line (your custom text).

`--append-system-prompt`: Identical to `system-prompt.md` except:
1. Block 2 identity change (see table above)
2. Custom text appended after git status at end of block 3
3. Git status differences (untracked files, recent commits vary per session)

## System prompt structure (as of 2.1.79)

The `system` array contains 3 blocks:

1. **Billing header** — `x-anthropic-billing-header: cc_version=2.1.79.04b; cc_entrypoint=cli; cch=00000;`
2. **Agent identity** — `"You are a Claude agent, built on Anthropic's Claude Agent SDK."` (with `cache_control: { type: 'ephemeral', ttl: '1h' }`)
3. **Main prompt** — All behavioral rules, tool instructions, memory system, environment info, output style, git status. Also cached with 1h TTL.

The user message (first message in `messages[]`) contains 4 text blocks:
1. Deferred tools list (`system-reminder`)
2. Available skills list (`system-reminder`)
3. CLAUDE.md / project context (`system-reminder`)
4. The actual user prompt

## API request parameters (as of 2.1.79)

| Parameter | Value |
|---|---|
| `model` | `claude-opus-4-6` |
| `max_tokens` | 64000 |
| `thinking` | `{"type": "adaptive"}` |
| `output_config` | `{"effort": "max"}` |
| `context_management` | `{"edits": [{"type": "clear_thinking_20251015", "keep": "all"}]}` |
| `stream` | `true` |
| Tools (non-deferred) | Agent, Bash, Glob, Grep, Read, Edit, Write, Skill, ToolSearch |
| Beta flags | `claude-code-20250219, oauth-2025-04-20, context-1m-2025-08-07, interleaved-thinking-2025-05-14, context-management-2025-06-27, prompt-caching-scope-2026-01-05, advanced-tool-use-2025-11-20, effort-2025-11-24` |

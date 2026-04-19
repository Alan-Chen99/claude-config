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
| `full-api-request.json` | Complete API request body with custom output style. Metadata redacted. |
| `full-api-request-default.json` | Complete API request body with default output style. Metadata redacted. |
| `CONFIG-VARIATIONS.md` | All configuration knobs that cause the prompt to diverge |

All system prompt files concatenate the 3 system text blocks, separated by
`---BLOCK_SEPARATOR---`.

## How to reproduce

Two steps: (1) write a Node.js `--require` script that patches `fetch`, (2) run `claude` with `NODE_OPTIONS` pointing at it.

### Step 1: Create the intercept script

```js
// /tmp/intercept.js
const fs = require('fs');
const origFetch = globalThis.fetch;

globalThis.fetch = async function(url, options, ...rest) {
  if (options && options.body && typeof url === 'string' && url.includes('anthropic')) {
    try {
      const body = JSON.parse(options.body);
      if (body.system && !fs.existsSync('/tmp/system_prompt.txt')) {
        const systemTexts = body.system
          .filter(s => s.type === 'text')
          .map(s => s.text);
        fs.writeFileSync('/tmp/system_prompt.txt',
          systemTexts.join('\n\n---BLOCK_SEPARATOR---\n\n'));
        fs.writeFileSync('/tmp/full_request.json',
          JSON.stringify(body, null, 2));
      }
    } catch(e) {}
  }
  return origFetch.call(this, url, options, ...rest);
};
```

### Step 2: Run claude with the intercept

```bash
echo "say exactly: hello" \
  | NODE_OPTIONS='--require /tmp/intercept.js' claude -p \
  1>/dev/null 2>/dev/null

# Results:
cat /tmp/system_prompt.txt    # system prompt text
cat /tmp/full_request.json    # full API request body (contains tool schemas, messages, etc.)
```

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

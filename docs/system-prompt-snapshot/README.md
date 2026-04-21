# Claude Code System Prompt Snapshots

Captured: 2026-04-19
Version: claude-cli/2.1.79
Mode: interactive (real pty via `capture.py`)

## Files

| File | What |
|---|---|
| `system-prompt-default.md` | Default system prompt (no flags) |
| `system-prompt-flag-system-prompt.md` | With `--system-prompt "You are a custom assistant."` |
| `system-prompt-flag-system-prompt-file.md` | With `--system-prompt-file` (same text, read from file) |
| `system-prompt-flag-append.md` | With `--append-system-prompt "You are a custom assistant."` |
| `full-api-request-default.json` | Full API request body (default). Metadata redacted. |
| `full-api-request-flag-system-prompt.json` | Full API request with `--system-prompt`. Metadata redacted. |
| `full-api-request-flag-system-prompt-file.json` | Full API request with `--system-prompt-file`. Metadata redacted. |
| `full-api-request-flag-append.json` | Full API request with `--append-system-prompt`. Metadata redacted. |
| `capture.py` | Python script that captures system prompts via expect + intercept.js |
| `intercept.js` | Node.js `--require` script that logs API calls to `~/.claude/http-logs/` |

### Subagent captures

When `capture.py --subagent` is used, the output includes a `subagents/` directory:

| File | What |
|---|---|
| `subagents/NNN-system-prompt.md` | System prompt for subagent N |
| `subagents/NNN-request.json` | Full API request for subagent N |
| `subagents/NNN-summary.json` | Block structure and tools for subagent N |

System prompt blocks are separated by `---BLOCK_SEPARATOR---` in the `.md` files.

## System prompt structure (v2.1.79, interactive mode)

The `system` array in the API request contains 3-4 text blocks:

| Block | Content | Chars |
|---|---|---|
| 0 | Billing header (`cc_version=2.1.79...`) | 80 |
| 1 | Identity (`"You are Claude Code, Anthropic's official CLI for Claude."`) | 57 |
| 2 | Behavioral rules (tool usage, tone, security, output style) | 9,245 |
| 3 | Memory system, environment info, output style, gitStatus | 28,436 |

Total: ~37,800 chars across 4 blocks.

Tool descriptions (git commit workflow, bash instructions, etc.) are in `tools[].description`, not in the system prompt. 25 tools, ~45K chars of tool descriptions.

## `--system-prompt` behavior

Replaces blocks 2-3 with the custom text. gitStatus is still appended unconditionally by `appendSystemContext()` in `query.ts`. Identity block is unchanged.

| Flag | Blocks | Total chars | What happens |
|---|---|---|---|
| (none) | 4 | 37,818 | Full default prompt |
| `--system-prompt` | 3 | 1,771 | Custom text replaces blocks 2-3; gitStatus appended |
| `--system-prompt-file` | 3 | 1,772 | Identical to `--system-prompt` (file read at startup) |
| `--append-system-prompt` | 4 | 38,060 | Full default prompt + custom text appended |

What `--system-prompt` removes (blocks 2-3):
- All behavioral rules (security policy, tool usage, output efficiency, tone)
- Memory system instructions
- Output style
- Environment info

What survives `--system-prompt`:
- Billing header (block 0)
- Identity (block 1)
- gitStatus (appended to custom text in block 2)
- All 25 tool definitions and descriptions (in `tools[]`, not system prompt)
- User message injections (deferred tools, skills, CLAUDE.md context)

### Sub-agent behavior

Neither `--system-prompt` nor `--append-system-prompt` propagates to sub-agents.
Subagent prompts are constructed independently by `agentDefinition.getSystemPrompt()`
+ `enhanceSystemPromptWithEnvDetails()`. Each agent type gets its static persona
regardless of parent flags.

Source: `tools/AgentTool/runAgent.ts:906-932`, `tools/AgentTool/built-in/`

| Agent | Prompt identity | Model | Key difference |
|-------|----------------|-------|----------------|
| Explore | "file search specialist" | haiku | Read-only, no Edit/Write, omits CLAUDE.md |
| general-purpose | "an agent for Claude Code" | inherits parent | Read-write, tools: `['*']`, loads CLAUDE.md |
| Plan | "software architect" | inherits parent | Same tools as Explore, omits CLAUDE.md |

## Interactive vs `-p` mode differences

These captures use interactive mode (real pty). In `-p` (pipe) mode, two things differ:

| | Interactive | `-p` mode |
|---|---|---|
| Identity (block 1) | `"You are Claude Code, Anthropic's official CLI for Claude."` | `"You are a Claude agent, built on Anthropic's Claude Agent SDK."` |
| gitStatus | Appended to system prompt | Not appended |
| Tools | 25 (all resolved) | 9 (deferred tools listed in user message) |

The behavioral rules and `--system-prompt` replacement logic are the same in both modes.

## How to re-capture

```bash
# Default prompt
./capture.py

# With --system-prompt
./capture.py --system-prompt "Your custom prompt here"

# With --system-prompt-file
./capture.py --system-prompt-file /path/to/prompt.txt

# With --append-system-prompt
./capture.py --append-system-prompt "Extra instructions"

# Capture subagent prompts (triggers an Explore agent, extracts all unique prompts)
./capture.py --subagent
```

`capture.py` uses expect to spawn claude with a real pty (true interactive mode), sends a canary message via haiku, then extracts the system prompt from the intercepted API request. Output goes to `capture-output/` (system.txt, request.json, summary.json) and stdout.

### Why expect + pty

Piping stdin (heredoc, `echo |`, subprocess with piped stdin) makes claude detect non-interactive mode, which changes the identity block and skips gitStatus. `expect` provides a real pty on both stdin and stdout so claude runs in true interactive mode.

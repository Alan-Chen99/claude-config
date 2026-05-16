# Claude Code System Prompt Snapshots

Captured: 2026-05-16
Version: claude-cli/2.1.143
Mode: interactive (real pty via `capture.py`, `--setting-sources project,local`)
Default captures include a project CLAUDE.md.

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
| `capture.py` | Python script that captures system prompts via pty + MITM proxy |
| `scripts/intercept/` | MITM proxy for API call logging (see `scripts/intercept/README.md`) |

### Subagent captures

When `capture.py --subagent` is used, the output includes a `subagents/` directory:

| File | What |
|---|---|
| `subagents/NNN-system-prompt.md` | System prompt for subagent N |
| `subagents/NNN-request.json` | Full API request for subagent N |
| `subagents/NNN-summary.json` | Block structure and tools for subagent N |

System prompt blocks are separated by `---BLOCK_SEPARATOR---` in the `.md` files.

## System prompt structure (v2.1.143, interactive mode, sonnet)

The `system` array contains 4 text blocks. In v2.1.143 both block 2 and block 3
carry `cache_control` (was: only block 2 cached in v2.1.87):

| Block | Content | Cache | Sonnet tokens | Opus tokens |
|---|---|---|---|---|
| 0 | Billing header (`cc_version=2.1.143...`) | none | 38 | 47 |
| 1 | Identity (`"You are Claude Code, Anthropic's official CLI for Claude."`) | none | 15 | 24 |
| 2 | Static behavioral rules (intro through Tone and style) | 1h, global scope | 2,132 | 3,054 |
| 3 | Text output, Session guidance, auto memory, Environment, Context mgmt, gitStatus | 1h, org scope | 4,266 | 5,754 |

Total: 6,449 (sonnet) / 8,877 (opus) tokens across 4 blocks.

Tool descriptions are in `tools[].description`, not in the system prompt. Defaults:
**10 upfront tools** (Agent, AskUserQuestion, Bash, Edit, Read, ScheduleWakeup,
ShareOnboardingGuide, Skill, ToolSearch, Write) — note Glob and Grep are no
longer upfront. **27 deferred tools** (20 built-in + 7 MCP tools surfaced by
the claude.ai account in this capture). Upfront tool definitions: 10,559
sonnet / 14,596 opus tokens.

Token counts from the Anthropic count_tokens API.

### Tokenizer difference (opus vs sonnet)

`claude-opus-4-7` and `claude-sonnet-4-6` use different tokenizers. The same
system prompt text counts to ~38% more tokens under opus. The text payloads
in `opus/default/request.json` and `sonnet/default/request.json` are byte-for-byte
identical except for the per-session billing header — only the token totals
differ.

## `--system-prompt` behavior

Replaces blocks 2-3 with the custom text. gitStatus is still appended unconditionally by `appendSystemContext()` in `query.ts`. Identity block is unchanged.

| Flag | Blocks | Sonnet tokens | What happens |
|---|---|---|---|
| (none) | 4 | 6,449 | Full default prompt |
| `--system-prompt` | 3 | 139 | Custom text replaces blocks 2-3; gitStatus appended |
| `--system-prompt-file` | 3 | 139 | Identical to `--system-prompt` (file read at startup) |
| `--append-system-prompt` | 4 | 6,456 | Full default prompt + custom text appended after env |

What `--system-prompt` removes (blocks 2-3):
- All behavioral rules (security policy, system, doing tasks, executing actions, using tools, tone)
- Text output / output style block
- Session-specific guidance (`!` prefix, `/<skill-name>`, `/schedule`, `/ultrareview`)
- Memory system instructions
- Environment info, context management, gitStatus context

What survives `--system-prompt`:
- Billing header (block 0)
- Identity (block 1)
- gitStatus (appended to custom text in block 2)
- All upfront tool definitions and descriptions (in `tools[]`, not system prompt)
- Deferred tool list (in `tools[]` with `defer_loading: true`)
- User message injections (skills, CLAUDE.md context)

### Sub-agent behavior

Neither `--system-prompt` nor `--append-system-prompt` propagates to sub-agents.
Subagent prompts are constructed independently by `agentDefinition.getSystemPrompt()`
+ `enhanceSystemPromptWithEnvDetails()`. Each agent type gets its static persona
regardless of parent flags.

Source: `tools/AgentTool/runAgent.ts`, `tools/AgentTool/built-in/`

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
| Tools | 10 upfront + deferred in `tools[]` with `defer_loading: true` | varies |

The behavioral rules and `--system-prompt` replacement logic are the same in both modes.

## How to re-capture

```bash
# Make sure ANTHROPIC_API_KEY is set (used by token-counting calls)
source .env  # or export ANTHROPIC_API_KEY=...

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

# Re-generate every variant for a model into <model>/<variant>/ subdirs
./regenerate.py --model sonnet      # all variants
./regenerate.py --model opus default
```

Do not run two `regenerate.py` invocations in parallel — they share
`capture-output/` and `~/.claude/requests-log/` and will overwrite each
other's intermediates.

`capture.py` spawns claude with a real pty via `pty.fork()` (true interactive mode) and `--setting-sources project,local` to isolate from user settings, sends a canary message, then extracts the system prompt from the intercepted API request (via MITM proxy). A placeholder CLAUDE.md is created in the temp working directory so the capture includes the claudeMd context block. Output goes to `capture-output/` (system.txt, request.json, summary.json) and stdout.

### Why pty (not heredoc/pipe)

Piping stdin (heredoc, `echo |`, subprocess with piped stdin) makes claude detect non-interactive mode, which changes the identity block and skips gitStatus. `pty.fork()` provides a real pty on both stdin and stdout so claude runs in true interactive mode.

### Bracketed paste

Claude Code enables xterm bracketed-paste mode (`\x1b[?2004h`). A `\r`
concatenated into the same write as the message body gets absorbed into the
paste payload instead of submitting. `spawn_claude` therefore writes the
message and the submit-Enter as separate `os.write()` calls with a short
`time.sleep` between them.

### Proxy log layout

The MITM proxy writes logs per-session under
`~/.claude/requests-log/<session_id>/NNNN.json`. Concurrent Claude Code
sessions on the same machine all write under the same root. `capture.py`
filters logs by `session.pid` matching its spawned claude PID (the proxy
resolves PID from `~/.claude/sessions/<pid>.json`); mtime alone is not
sufficient to isolate one capture's traffic.

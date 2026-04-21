# Agent System Prompt Anatomy

How Claude Code assembles the context sent to the model on each API call.

For source-verified details with function references and code paths, see
[system-prompt-anatomy-source-verified.md](system-prompt-anatomy-source-verified.md).

## Conversation Skeleton

The harness rebuilds the full message array before every API call. Nothing is
sent incrementally — each call receives the complete conversation state.

```
┌─────────────────────────────────────────────────┐
│ SYSTEM PROMPT                                    │
│                                                  │
│  [1] Attribution / billing header                │
│  [2] Identity prefix ("You are Claude Code...")   │
│  [3] Main prompt body:                           │
│       - Tool definitions                         │
│       - Behavioral rules                         │
│       - Tool usage guidance                      │
│       - Tone / style / efficiency rules          │
│       - Session guidance                         │
│       - Auto-memory prompt                       │
│       - Environment info (cwd, platform, model)  │
│       - Output style (if configured)             │
│       - MCP instructions (if any)                │
│       - Git status (branch, recent commits)      │
│                                                  │
└──────────────────────────────────────────────────┘

┌─ User context (injected as first user message) ──┐
│  <system-reminder>                                │
│    CLAUDE.md contents (global → project → local)  │
│    Today's date                                   │
│  </system-reminder>                               │
└───────────────────────────────────────────────────┘

┌─ User message ───────────────────────────────────┐
│  "explain the auth module"                       │
└───────────────────────────────────────────────────┘

┌─ Assistant response ─────────────────────────────┐
│  [tool calls + text]                             │
└───────────────────────────────────────────────────┘

┌─ Tool results ───────────────────────────────────┐
│  File contents, command output, etc.              │
│  <system-reminder> attachments injected here      │
└───────────────────────────────────────────────────┘

        ... more turns ...
```

## Exact Prompt Skeleton

Every markdown header and XML tag in the system prompt, content omitted.
Extracted from captured API payloads (v2.1.79). See
[system-prompt-snapshot/](system-prompt-snapshot/) for full text.

### system[] blocks

```
system[0]  x-anthropic-billing-header: ...

system[1]  You are Claude Code, Anthropic's official CLI for Claude.

system[2]  ↓ (main body below)
```

### Main body (system[2])

```
You are an interactive agent that helps users...

IMPORTANT: Assist with authorized security testing...
IMPORTANT: You must NEVER generate or guess URLs...

# System
 - All text you output outside of tool use is displayed...
 - Tools are executed in a user-selected permission mode...
 - Tool results and user messages may include <system-reminder>...
 - Tool results may include data from external sources...
 - Users may configure 'hooks', shell commands that execute...
 - The system will automatically compress prior messages...

# Doing tasks                                    ← REMOVED when output style is set
 - The user will primarily request you to perform software engineering tasks...
 - You are highly capable and often allow users...
 - In general, do not propose changes to code you haven't read...
 - Do not create files unless they're absolutely necessary...
 - Avoid giving time estimates or predictions...
 - If your approach is blocked, do not attempt to brute force...
 - Be careful not to introduce security vulnerabilities...
 - Avoid over-engineering. Only make changes that are directly requested...
   - Don't add features, refactor code, or make "improvements"...
   - Don't add error handling, fallbacks, or validation...
   - Don't create helpers, utilities, or abstractions...
 - Avoid backwards-compatibility hacks...
 - If the user asks for help or wants to give feedback...

# Executing actions with care
Carefully consider the reversibility and blast radius of actions...
Examples of the kind of risky actions that warrant user confirmation:
 - Destructive operations: deleting files/branches...
 - Hard-to-reverse operations: force-pushing...
 - Actions visible to others or that affect shared state...
 - Uploading content to third-party web tools...
When you encounter an obstacle, do not use destructive actions...

# Using your tools
 - Do NOT use the Bash to run commands when a relevant dedicated tool...
   - To read files use Read...
   - To edit files use Edit...
   - To create files use Write...
   - To search for files use Glob...
   - To search the content of files, use Grep...
   - Reserve using the Bash exclusively...
 - Break down and manage your work with the TodoWrite tool...
 - Use the Agent tool with specialized agents...
 - For simple, directed codebase searches...
 - For broader codebase exploration and deep research...
 - /<skill-name> (e.g., /commit) is shorthand...
 - You can call multiple tools in a single response...

# Tone and style
 - Only use emojis if the user explicitly requests it...
 - Your responses should be short and concise...
 - When referencing specific functions or pieces of code...
 - Do not use a colon before tool calls...

# Output efficiency
IMPORTANT: Go straight to the point...
Keep your text output brief and direct...
Focus text output on:
 - Decisions that need the user's input
 - High-level status updates at natural milestones
 - Errors or blockers that change the plan
If you can say it in one sentence, don't use three...

# auto memory                                    ← ~4500 tokens
You have a persistent, file-based memory system at {path}...
## Types of memory                               ← user, feedback, project, reference
  (XML: <types><type><name/description/when_to_save/how_to_use/body_structure/examples>)
## What NOT to save in memory
## How to save memories
## When to access memories
## Before recommending from memory
## Memory and other forms of persistence

# Environment
You have been invoked in the following environment:
 - Primary working directory: ...
 - Platform: ...
 - Shell: ...
 - You are powered by the model named ...
Assistant knowledge cutoff is ...
<fast_mode_info>Fast mode for Claude Code uses the same ... model...</fast_mode_info>

# Output Style: {name}                           ← ADDED when output style is set
{output style content}                            ← replaces "# Doing tasks"

When working with tool results, write down any important information...
gitStatus: This is the git status at the start of the conversation...
```

### User context (messages[0])

Injected as the first user message before the actual user input.

```
<system-reminder>
  deferred tools listing
</system-reminder>

<system-reminder>
  skills listing
</system-reminder>

<system-reminder>
  # claudeMd
  Contents of ~/.claude/rules/{file}.md ...
  Contents of {path}/CLAUDE.md ...
  # currentDate
  Today's date is {date}.
</system-reminder>
```

### Tool results (subsequent messages)

```
{tool output text}

<system-reminder>
  {attachment content}
</system-reminder>
```

## CLAUDE.md Loading Order

Project instructions are assembled from multiple locations, in order:

1. **Managed** — `/etc/claude-code/CLAUDE.md` + `/etc/claude-code/.claude/rules/*.md`
2. **User** — `~/.claude/CLAUDE.md` + `~/.claude/rules/*.md`
3. **Project** — `CLAUDE.md` files walking from CWD to repo root
4. **Local** — `CLAUDE.local.md` (private, not committed)

Each level can override the previous. Subdirectory rules override parent rules.
The full content is wrapped in a preamble stating these instructions override
default behavior.

### Path-scoped rules

Rules in `~/.claude/rules/` can have `paths:` frontmatter with glob patterns.
These load on demand when Claude reads a matching file, not at session start.

```markdown
---
paths:
  - "src/**/*.ts"
---
# TypeScript conventions
- Prefer functional patterns
```

## Prompt Caching

The system prompt is split into API blocks with different cache behaviors:

| Block | Cache scope |
|-------|-------------|
| Billing header | Not cached |
| Identity prefix | Ephemeral (org-level) |
| Static behavioral rules | Global (cross-org) when eligible |
| Dynamic sections (env, MCP, etc.) | Not cached or ephemeral |

Static sections are computed once per session. MCP instructions are recomputed
every turn and break prompt cache when they change.

## Compaction

When context grows too large, autocompact summarizes older turns. After compaction:

- User context (CLAUDE.md) is re-read from disk
- Old `<system-reminder>` attachments are lost (summarized away)
- Invoked skill content survives across compactions
- Fresh attachments resume on new tool results

For external users, autocompact is the only mechanism that physically removes
tokens. It can be disabled via config or `DISABLE_AUTO_COMPACT=1`.

## Attention Characteristics

- **Start (strong):** system prompt + CLAUDE.md — always at the top
- **End (strong):** latest tool results, latest user message
- **Middle (degrades):** earlier tool results, earlier conversation turns

Rules stay pinned to the start. Work product drifts to the middle. Use
plans-on-disk or sub-agents to avoid depending on recall of earlier work.

## Sub-agents

Sub-agents (launched via the Agent tool) receive a different, lighter prompt
constructed independently from the parent. `--system-prompt` and
`--append-system-prompt` do **not** propagate to subagents.

### Prompt structure

Each subagent's system prompt is built by `agentDefinition.getSystemPrompt()` +
`enhanceSystemPromptWithEnvDetails()`, which appends shared notes (absolute
paths, emoji, colon guidance) and environment info (cwd, platform, model,
gitStatus).

### Built-in agent types

| Type | Identity | Model | Tools | CLAUDE.md | gitStatus |
|------|----------|-------|-------|-----------|-----------|
| **Explore** | "file search specialist" | haiku | All minus Agent, Edit, Write, NotebookEdit, ExitPlanMode | Omitted | Omitted |
| **general-purpose** | "an agent for Claude Code" | inherits parent | All (`*`) | Loaded | Included |
| **Plan** | "software architect" | inherits parent | Same as Explore | Omitted | Omitted |
| **claude-code-guide** | (documentation helper) | haiku | Glob, Grep, Read, WebFetch, WebSearch | — | — |
| **statusline-setup** | (statusline config) | sonnet | Read, Edit | — | — |
| **verification** | (verification agent) | inherits parent | All minus disallowed | — | — |

All agents additionally have `ALL_AGENT_DISALLOWED_TOOLS` removed: TaskOutput,
ExitPlanModeV2, EnterPlanMode, AskUserQuestion, TaskStop, and Agent (for
non-ant users).

### What subagents inherit / don't inherit

- **Inherited:** MCP tools, environment info, current date
- **Not inherited:** parent's `--system-prompt` / `--append-system-prompt`, output style, memory system
- **Conditional:** CLAUDE.md (only when `omitClaudeMd` is false), gitStatus, skills (from agent frontmatter)

## Extracting the API Payload

Session logs don't store the system prompt. To capture the exact payload:

```bash
cat > /tmp/dump-api-request.cjs << 'HOOK'
const origFetch = globalThis.fetch;
let callNum = 0;
globalThis.fetch = async function(url, opts) {
  if (typeof url === 'string' && url.includes('/v1/messages') && opts?.body) {
    const n = ++callNum;
    const outFile = `/tmp/claude-api-dump-${n}.json`;
    try {
      const body = JSON.parse(opts.body);
      require('fs').writeFileSync(outFile, JSON.stringify(body, null, 2));
      process.stderr.write(`[dump] #${n} → ${outFile}\n`);
    } catch(e) {}
  }
  return origFetch.apply(this, arguments);
};
HOOK

NODE_OPTIONS="--require=/tmp/dump-api-request.cjs" claude
# Dumps appear at /tmp/claude-api-dump-{1,2,...}.json
```

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

Sub-agents (launched via the Agent tool) receive a different, lighter prompt:

- Read-only agents (Explore, Plan) skip CLAUDE.md and git status to save tokens
- MCP tools are inherited; agent-specific servers can be added
- Skills can be preloaded from agent frontmatter
- Environment info and current date are always included

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

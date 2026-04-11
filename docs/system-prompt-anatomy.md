# Agent System Prompt Anatomy

Source-verified against `claude-code` source (`/repos/claude-code-src/src/`).

Claude Code assembles context from multiple sources. The harness rebuilds the
message array before every API call — some blocks are static, some are
re-injected fresh, and some accumulate over the conversation.

## Conversation Skeleton

Each box is a message in the array sent to the model. The harness rebuilds this
array before every API call.

```
┌─────────────────────────────────────────────────────────┐
│ SYSTEM PROMPT  (string[], cached per section)           │
│                                                         │
│  ┌─ Tool definitions ────────────────────────────────┐  │
│  │ Bash, Read, Edit, Write, Glob, Grep,              │  │
│  │ Agent, Skill, ToolSearch, + MCP tools              │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌─ Agent identity ─────────────────────────────────┐   │
│  │ "You are Claude Code..." + behavioral rules,      │  │
│  │ guidelines, git safety, commit/PR instructions    │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌─ Static sections (cacheable) ────────────────────┐   │
│  │ getSimpleIntroSection                             │  │
│  │ getSimpleSystemSection                            │  │
│  │ getSimpleDoingTasksSection                        │  │
│  │ getActionsSection                                 │  │
│  │ getUsingYourToolsSection                          │  │
│  │ getSimpleToneAndStyleSection                      │  │
│  │ getOutputEfficiencySection                        │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌─ SYSTEM_PROMPT_DYNAMIC_BOUNDARY ─────────────────┐   │
│  │ (marker separating cache-stable from volatile)    │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌─ Dynamic sections (registry-managed) ────────────┐   │
│  │ session_guidance      (memoized per session)      │  │
│  │ memory                (auto-memory prompt)        │  │
│  │ env_info_simple       (cwd, platform, model ID)   │  │
│  │ language              (if non-English)             │  │
│  │ output_style          (from output-styles/ config) │  │
│  │ mcp_instructions      (DANGEROUS: uncached)       │  │
│  │ scratchpad            (temp dir instructions)      │  │
│  │ frc                   (function result clearing)   │  │
│  │ summarize_tool_results                            │  │
│  │ token_budget          (feature-gated)             │  │
│  │ brief                 (feature-gated)             │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌─ systemContext (appended) ───────────────────────┐   │
│  │ gitStatus: branch, status, recent commits         │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

┌─ userContext (user message, isMeta=true) ─────────────┐
│                                                         │
│  Memoized by getUserContext() (lodash memoize).         │
│  Cached value prepended as messages[0] each API call.   │
│  Cache cleared on /clear, /compact, settings sync.      │
│                                                         │
│  <system-reminder>                                      │
│    # claudeMd                                           │
│    Contents of ~/.claude/rules/general.md               │
│    Contents of ~/.claude/rules/testing.md               │
│    Contents of ./CLAUDE.md                              │
│    # currentDate                                        │
│    Today's date is 2026-04-17.                          │
│  </system-reminder>                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─ User message (turn 1) ────────────────────────────────┐
│ "explain the auth module"                              │
└─────────────────────────────────────────────────────────┘

┌─ Assistant (turn 1) ───────────────────────────────────┐
│ [tool calls]                                           │
└─────────────────────────────────────────────────────────┘

┌─ Tool result (within user message) ───────────────────┐
│ [file contents, command output, etc.]                  │
│                                                         │
│  <system-reminder>                                      │
│    [attachment-origin content, wrapped by               │
│     ensureSystemReminderWrap()]                         │
│  </system-reminder>                                     │
│                                                         │
│  Attachments are normalized into tool result content    │
│  blocks. smooshSystemReminderSiblings() merges any      │
│  <system-reminder> text siblings into the LAST          │
│  tool_result of the same user message.                  │
└─────────────────────────────────────────────────────────┘

┌─ Assistant (turn 1 cont.) ─────────────────────────────┐
│ [response to user]                                     │
└─────────────────────────────────────────────────────────┘

        ... more turns, each with tool calls + results ...
```

### After `/compact`

Compaction replaces the middle with a summary. Multiple compaction mechanisms
exist (microcompact, snip, autocompact, context collapse). After any compaction:

```
┌─ SYSTEM PROMPT (section cache cleared, recomputed) ───┐
└─────────────────────────────────────────────────────────┘

┌─ userContext (caches cleared, recomputed from disk) ──┐
│  getUserContext.cache.clear() + resetGetMemoryFilesCache()
│  Both layers must be cleared; clearing only inner cache │
│  leaves outer memoization intact.                       │
└─────────────────────────────────────────────────────────┘

┌─ Compact boundary marker ─────────────────────────────┐
└─────────────────────────────────────────────────────────┘

┌─ Summary of prior conversation ───────────────────────┐
│  Old messages, tool results, system-reminders — all    │
│  summarized. Old <system-reminder> tags are NOT        │
│  preserved; they are lost unless the compaction model   │
│  included their substance.                              │
└─────────────────────────────────────────────────────────┘

┌─ Re-injected attachments ─────────────────────────────┐
│  - invoked_skills (survives across compactions)        │
│  - plan_file_reference                                 │
│  - deferred_tools_delta                                │
│  - mcp_instructions_delta                              │
│  - relevant_memories (memory surfacer)                 │
│  - skill_listing                                       │
└─────────────────────────────────────────────────────────┘

┌─ Recent messages preserved verbatim ──────────────────┐
│  (most recent turns survive compaction intact)         │
└─────────────────────────────────────────────────────────┘
```

## System Prompt Assembly

**Entry point:** `getSystemPrompt()` in `constants/prompts.ts:444-577`

Two code paths:

1. **Proactive/Kairos mode** (feature-gated) — simplified autonomous agent prompt
2. **Standard mode** (default) — static sections + boundary marker + dynamic sections

Standard mode returns a `string[]`:

```
[
  // --- Static (cacheable) ---
  getSimpleIntroSection()         // "You are Claude Code..."
  getSimpleSystemSection()        // tool permissions, hooks, context compression
  getSimpleDoingTasksSection()    // coding guidance (skipped if output style replaces it)
  getActionsSection()             // reversibility/blast-radius rules
  getUsingYourToolsSection()      // tool usage preferences, parallel calls
  getSimpleToneAndStyleSection()  // emoji, response format
  getOutputEfficiencySection()    // conciseness rules

  // === SYSTEM_PROMPT_DYNAMIC_BOUNDARY ===
  // (inserted when global cache scope enabled)

  // --- Dynamic (registry-managed) ---
  session_guidance                // conditional guidance per enabled tools
  memory                          // auto-memory prompt
  env_info_simple                 // cwd, platform, shell, model, knowledge cutoff
  language                        // non-English language instructions
  output_style                    // custom output style content
  mcp_instructions                // DANGEROUS_uncachedSystemPromptSection (recomputed every turn)
  scratchpad                      // temp directory instructions
  frc                             // function result clearing (microcompact)
  summarize_tool_results          // "capture important info" instruction
  token_budget                    // feature-gated
  brief                           // feature-gated
]
```

**Section caching** (`constants/systemPromptSections.ts`):
- `systemPromptSection()` — memoized, computed once, cached until `/clear` or `/compact`
- `DANGEROUS_uncachedSystemPromptSection()` — recomputed every turn, breaks prompt cache when value changes (used for MCP instructions)

**Effective prompt priority** (`utils/systemPrompt.ts:41-123`):
1. Override prompt (loop mode) — replaces everything
2. Coordinator prompt (coordinator mode)
3. Agent prompt (main-thread agent definition)
4. Custom prompt (`--system-prompt`)
5. Default prompt (`getSystemPrompt()`)
6. Append prompt — always added at end (except when override is set)

**systemContext** (`context.ts:116-150`): `gitStatus` is computed by `getSystemContext()` (memoized) and appended to the system prompt via `appendSystemContext()` — it is NOT inside the claudeMd user message.

## userContext / claudeMd

**Assembly:** `getUserContext()` in `context.ts:155-189` (memoized via lodash `memoize`)

Returns `{ claudeMd, currentDate }`. The `claudeMd` value is built by `getClaudeMds()` → `getMemoryFiles()` from:

1. **Managed memory** — `/etc/claude-code/CLAUDE.md` + `/etc/claude-code/.claude/rules/*.md`
2. **User memory** — `~/.claude/CLAUDE.md` + `~/.claude/rules/*.md`
3. **Project memory** — walk from CWD to root: `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`
4. **Local memory** — `CLAUDE.local.md` (private, not committed)
5. **AutoMem / TeamMem** — feature-gated entrypoints

Each file is processed by `processMemoryFile()` which:
- Resolves symlinks
- Strips frontmatter and HTML comments
- Truncates MEMORY.md entries
- Resolves `@include` directives (max depth 5, circular reference protection)

**Injection:** `prependUserContext()` in `utils/api.ts:449-474` wraps the context dict in a `<system-reminder>` tag and creates a `UserMessage` with `isMeta: true` at messages[0].

**Caching:** Two-layer memoization:
- Outer: `getUserContext` (lodash memoize)
- Inner: `getMemoryFiles` (lodash memoize)

Both must be cleared during compaction (`postCompactCleanup.ts:51-60`). Clearing only the inner cache leaves the outer cache intact, suppressing the `InstructionsLoaded` hook.

**Editing `CLAUDE.md` mid-conversation:** No effect until caches are cleared by `/clear`, `/compact`, settings sync, or worktree enter/exit. Compaction triggers `resetGetMemoryFilesCache('compact')` which re-reads from disk.

**The claudeMd preamble:**

> *"Codebase and user instructions are shown below. Be sure to adhere to these instructions. IMPORTANT: These instructions OVERRIDE any default behavior and you MUST follow them exactly as written."*

**Contents, in order:**

1. **Global rules** from `~/.claude/rules/*.md` — each as `Contents of ~/.claude/rules/<file>.md (user's private global instructions for all projects):`
2. **Project `CLAUDE.md`** files along the directory hierarchy — each as `Contents of <path>/CLAUDE.md (project instructions, checked into the codebase):`
3. **`currentDate`** — today's date

## Rule Loading

Rules in `~/.claude/rules/` come in two forms:

**Global (no frontmatter)** — loaded unconditionally at session start.

```markdown
# General
- Fail loudly; never swallow errors silently
```

**Path-scoped (with `paths` frontmatter)** — loaded dynamically when Claude reads a file matching the glob patterns.

```markdown
---
paths:
  - "src/**/*.ts"
  - "src/**/*.js"
---
# Code Style
- Prefer functional patterns
```

Path-scoped rules use the `ignore` library for glob matching. Matching is evaluated per file operation — conditional rules are **not cached** between file operations (computed fresh each time). Managed/user conditional rules match against the current working directory. Project conditional rules match relative to the parent of `.claude/`.

Nested directory rules (`getMemoryFilesForNestedDirectory()`) load lazily when reading/editing files outside CWD, loading both unconditional and conditional rules that match the target path.

## System-Reminder Sources

`<system-reminder>` tags appear in multiple contexts with different lifecycles:

| Source | Content | Lifecycle | Position |
|--------|---------|-----------|----------|
| **userContext** | claudeMd + currentDate | Memoized at session start; prepended as messages[0] each API call; cache cleared on /compact | Always first user message |
| **Attachments** | ~50 attachment types (see `Attachment` union in `utils/attachments.ts:440-718`) wrapped by `ensureSystemReminderWrap()` | Generated per-turn; accumulate in conversation; lost on compaction | Within user messages alongside tool results |
| **Memory freshness** | Age notes for memory files | Generated by `memoryFreshnessNote()` per file read | Appended to FileReadTool results |
| **Hook outputs** | PreToolUse/PostToolUse hook results | Generated per hook execution | Injected as attachment content |

**Relocation:** `smooshSystemReminderSiblings()` in `utils/messages.ts:1835` merges any `<system-reminder>`-prefixed text siblings into the **last** `tool_result` of the same user message. Non-system-reminder text (real user input, collapse summaries) is not moved.

## Parent Agent vs Sub-Agent

Sub-agents (launched via the `Agent` tool) receive a different prompt via `agentDefinition.getSystemPrompt()` rather than the main `getSystemPrompt()` path.

**Context omission** (`tools/AgentTool/runAgent.ts:385-410`):

| Component | Parent | Sub-agent | Source |
|-----------|--------|-----------|--------|
| System prompt sections | `getSystemPrompt()` | `agentDefinition.getSystemPrompt()` | runAgent.ts:508-518 |
| claudeMd (CLAUDE.md, rules) | Always | **Omitted** when `omitClaudeMd=true` + feature flag `tengu_slim_subagent_claudemd` (default: true). Explore/Plan agents omit by default. | runAgent.ts:390-398 |
| gitStatus | Always | **Omitted** for Explore and Plan agents | runAgent.ts:404-410 |
| Output style | Yes | Via agent definition | systemPrompt.ts:77-123 |
| MCP tools | Yes | Inherited (agent-specific servers can be added) | runAgent.ts:648-664 |
| Skills | Yes | Can be preloaded from agent frontmatter | runAgent.ts:577-646 |
| Environment info | Yes | Yes (enhanced by `enhanceSystemPromptWithEnvDetails()`) | prompts.ts:760-791 |
| currentDate | Yes | Yes | context.ts:186 |

Rationale for omitting claudeMd from read-only agents: Explore and Plan don't act on commit/PR/lint rules — dropping claudeMd saves ~5-15 Gtok/week across 34M+ Explore spawns.

**Fork children** (same-model sub-agents) use the parent's already-rendered system prompt bytes (`toolUseContext.renderedSystemPrompt`) cached at turn start, ensuring identical API request prefix for prompt cache hits. This prevents divergence from feature flag state changes between parent and child spawn.

## Attention and Degradation

Two independent mechanisms cause earlier work to become less accessible:

**1. Harness-level removal (tokens physically deleted)**

The codebase has multiple compaction mechanisms, but most are **not active for
external users** (v2.1.79). Runtime activation depends on build-time DCE,
GrowthBook flags, and ant-only modules:

| Mechanism | External users | Gate |
|-----------|---------------|------|
| **Autocompact** | **Active** | User config `autoCompactEnabled` (default true), env `DISABLE_AUTO_COMPACT` |
| Tool result budget | Inactive | GrowthBook `tengu_hawthorn_steeple`, default false → state=undefined → no-op |
| Cached microcompact | Inactive | `isCachedMicrocompactEnabled()` from ant-only module; source: "external builds... no compaction happens here" → `return { messages }` |
| Context collapse | Inactive | DCE'd from bundle — no `applyCollapsesIfNeeded` or `isContextCollapseEnabled` present |
| Snip | Inactive | DCE'd from bundle |

For external users, **autocompact is the only mechanism that physically removes
tokens.** If disabled (config or `DISABLE_AUTO_COMPACT=1`), nothing removes
content until the hard context limit.

**2. Model attention degradation (tokens present but under-attended)**

LLMs attend most strongly to the **start** and **end** of context (primacy and
recency bias). Even when all tokens are physically present, retrieval accuracy
drops for information in the middle of long contexts ("lost in the middle"
effect). This is a property of transformer attention, not a harness behavior.

- **Start (primacy):** system prompt + userContext. Since userContext is always prepended at messages[0], project rules benefit from primacy bias regardless of conversation length.
- **End (recency):** latest tool results and their system-reminder attachments, latest user message.
- **Middle (soft fading):** earlier tool results, earlier conversation turns.

What degrades in long conversations is not rule adherence but **recall of
earlier work**: file contents read many tool calls ago, reasoning from early
turns, intermediate findings. Rules stay pinned to the start. Work product
drifts to the middle — and may also be physically removed by the harness
mechanisms above.

## Compaction Mechanisms

Multiple mechanisms manage context size, ordered by when they run in the query loop (`query.ts`):

1. **Autocompact** — active for external users; full summarization when context exceeds threshold. Controlled by user config `autoCompactEnabled` (default true) and env `DISABLE_AUTO_COMPACT`
2. **Tool result budget** (`applyToolResultBudget`) — GrowthBook-gated (`tengu_hawthorn_steeple`, default false); inactive for external users
3. **Cached microcompact** (`CACHED_MICROCOMPACT`) — requires ant-only `cachedMicrocompact.js` module; inactive for external users
4. **Context collapse** (`CONTEXT_COLLAPSE`) — DCE'd from external builds; inactive
5. **Snip** (`HISTORY_SNIP`) — DCE'd from external builds; inactive

Post-compaction cleanup (`services/compact/postCompactCleanup.ts:31-77`):
- Clears both getUserContext and getMemoryFiles caches (main thread only)
- Clears system prompt section cache
- Clears classifier approvals, speculative checks, beta tracing state
- Does NOT clear invoked skill content (must survive across compactions)
- Subagents share process with main thread — only main-thread compacts reset module-level state

## Practical Implications

- **userContext survives long conversations.** Its memoized content is prepended at messages[0] before every API call. It does not drift to the middle.
- **Earlier work product does not survive.** For external users, autocompact is the only mechanism that physically removes tokens. Before it fires, model attention degradation ("lost in the middle") softly reduces recall for mid-context content even while all tokens are present. Use plans-on-disk or sub-agents to avoid depending on recall of earlier work.
- **Attachments compensate at the recency edge.** The ~50 attachment types injected into tool results reinforce context (file state, plan references, skill content) even in long conversations.
- **Compaction drops old attachments but preserves userContext.** After compaction, both caches are cleared and content re-read from disk. Old system-reminder attachments are summarized away. Fresh attachments resume on new tool results.
- **Path-scoped rules are demand-loaded.** They load when Claude reads a file matching the `paths:` glob, not at session start. If no matching file is ever read, the rule never enters context.
- **Read-only sub-agents skip claudeMd.** Explore and Plan agents omit CLAUDE.md and gitStatus to save tokens. If they need git info, they run `git status` themselves for fresh data.
- **claudeMd overrides defaults.** The preamble explicitly states these instructions override default behavior. Project `CLAUDE.md` can override global rules; subdirectory `CLAUDE.md` can override parent directory rules.

## Sources

- [`constants/prompts.ts`](https://github.com/anthropics/claude-code) — `getSystemPrompt()`, section generators, `computeSimpleEnvInfo()`
- [`utils/systemPrompt.ts`](https://github.com/anthropics/claude-code) — `buildEffectiveSystemPrompt()` priority logic
- [`constants/systemPromptSections.ts`](https://github.com/anthropics/claude-code) — section caching (`systemPromptSection`, `DANGEROUS_uncachedSystemPromptSection`)
- [`context.ts`](https://github.com/anthropics/claude-code) — `getUserContext()`, `getSystemContext()`
- [`utils/api.ts`](https://github.com/anthropics/claude-code) — `prependUserContext()`, `appendSystemContext()`, `splitSysPromptPrefix()`
- [`utils/claudemd.ts`](https://github.com/anthropics/claude-code) — `getMemoryFiles()`, path-scoped rule loading, `@include` resolution
- [`utils/messages.ts`](https://github.com/anthropics/claude-code) — `smooshSystemReminderSiblings()`, `ensureSystemReminderWrap()`
- [`utils/attachments.ts`](https://github.com/anthropics/claude-code) — `Attachment` type union (~50 types), `getAttachments()`
- [`tools/AgentTool/runAgent.ts`](https://github.com/anthropics/claude-code) — sub-agent context omission logic
- [`services/compact/postCompactCleanup.ts`](https://github.com/anthropics/claude-code) — post-compaction cache clearing
- [`services/api/claude.ts`](https://github.com/anthropics/claude-code) — `buildSystemPromptBlocks()`, cache scope metadata

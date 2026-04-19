# System Prompt Configuration Variations

Source: `/repos/claude-code-src/src/` (claude-cli 2.1.79)

This documents every point where configuration causes the system prompt to
diverge from the snapshot in `system-prompt.md`. The snapshot was captured
with: external user, interactive-equivalent pipe mode, opus 4.6, output style
set, no MCP servers, no custom/append/override prompts.

---

## 1. Identity prefix (system block 2)

**Source:** `src/constants/system.ts:30-46`

Three variants selected by `getCLISyspromptPrefix()`:

| Condition | Prefix |
|---|---|
| Interactive mode (default) | `"You are Claude Code, Anthropic's official CLI for Claude."` |
| Non-interactive + `appendSystemPrompt` | `"You are Claude Code, Anthropic's official CLI for Claude, running within the Claude Agent SDK."` |
| Non-interactive, no append | `"You are a Claude agent, built on Anthropic's Claude Agent SDK."` |

Vertex provider always returns the interactive variant regardless of mode.

The snapshot shows the third variant because `claude -p` is non-interactive
and no `appendSystemPrompt` was set.

---

## 2. Intro framing (output style presence)

**Source:** `src/constants/prompts.ts:175-183`

```
// With output style:
"...helps users according to your "Output Style" below..."
// Without output style:
"...helps users with software engineering tasks."
```

The snapshot shows the output-style variant.

---

## 3. "Doing tasks" section (ant vs external)

**Source:** `src/constants/prompts.ts:199-253`

This entire section is **omitted** if the output style sets
`keepCodingInstructions: false` (line 564-566).

When present, ant-internal users (`USER_TYPE=ant`) get 5 additional bullets
that external users don't see:

| Line | Ant-only content |
|---|---|
| 206-209 | Aggressive comment-reduction guidance ("Default to writing no comments") |
| 210-211 | Thoroughness counterweight ("verify it actually works: run the test") |
| 225-228 | Assertiveness counterweight ("If you notice a misconception, say so") |
| 238-242 | False-claims mitigation ("Report outcomes faithfully") |
| 243-246 | Bug-reporting slash commands (`/issue`, `/share`, `#claude-code-feedback`) |

---

## 4. Tool guidance section

**Source:** `src/constants/prompts.ts:269-314`

Varies on three axes:

**a) Task tool name** (line 270-271): Shows whichever of `TaskCreate` or
`TodoWrite` is in the enabled tool set. If neither is present, the bullet is
omitted.

**b) REPL mode** (line 277): In REPL mode, the entire file/bash tool guidance
is stripped — only the task tool bullet remains.

**c) Embedded search tools** (line 289): If ant-native builds with embedded
`bfs`/`ugrep`, references to Glob/Grep are replaced with references to
`find`/`grep` via Bash.

---

## 5. Session-specific guidance (dynamic section)

**Source:** `src/constants/prompts.ts:352-399`

This entire section lives after the cache boundary marker and varies per
session. Conditionals:

| Condition | Adds |
|---|---|
| `AskUserQuestion` tool available | "use AskUserQuestion to ask them" |
| Interactive (not non-interactive) | `! <command>` shell escape guidance |
| `Agent` tool available | Full agent tool usage section |
| `Agent` + explore/plan agents enabled + fork disabled | Glob/Grep vs Explore agent guidance |
| Skill tool + skills present | `/<skill-name>` usage guidance |
| `DiscoverSkills` tool available | Skill discovery guidance |
| `Agent` + `VERIFICATION_AGENT` feature + `tengu_hive_evidence` gate | Full adversarial verification contract (~200 words) |

The snapshot includes: AskUserQuestion guidance, shell escape, agent tool,
explore agent, skill tool. It lacks: verification agent, REPL guidance,
discover skills.

---

## 6. Tone and style section

**Source:** `src/constants/prompts.ts:430-442`

Ant users don't get the "Your responses should be short and concise" bullet
(line 433-435). External users get it.

Ant users also get a different GitHub reference format guidance (this applies
to both — `owner/repo#123`).

---

## 7. Output efficiency section (ant vs external)

**Source:** `src/constants/prompts.ts:403-428`

Entirely different content based on `USER_TYPE`:

- **External** (snapshot): Short "Output efficiency" section (~7 lines,
  "Go straight to the point")
- **Ant**: Long "Communicating with the user" section (~12 lines, prose
  writing guidance, inverted pyramid, anti-fragment rules)

---

## 8. Output style injection

**Source:** `src/constants/prompts.ts:151-158`

When an output style is configured:
```
# Output Style: <name>
<prompt content>
```

When no output style: this section is `null` (omitted entirely).

The snapshot includes the user's `alan-default-next` output style.

---

## 9. Memory system

**Source:** `src/constants/prompts.ts:495`, `src/memdir/memdir.ts`

The memory path is dynamic:
- Default: derived from project directory hash
- Override: `CLAUDE_CODE_MEMORY_PATH_OVERRIDE` env var

The entire memory prompt (types, save format, when to access) is loaded from
the memory module. If the memory system is disabled or the path override
points to nothing, the section is absent.

---

## 10. Language preference

**Source:** `src/constants/prompts.ts:142-149`

If `settings.language` is set:
```
# Language
Always respond in <language>. Use <language> for all explanations...
```

If unset: section is omitted. The snapshot has no language preference.

---

## 11. MCP instructions

**Source:** `src/constants/prompts.ts:508-520`

- If MCP servers are connected: includes server instructions
- If `isMcpInstructionsDeltaEnabled()`: instructions delivered via
  attachments instead, section is `null`
- If no MCP servers: section is `null`

This section is marked `DANGEROUS_uncachedSystemPromptSection` because MCP
servers connect/disconnect between turns, breaking cache.

The snapshot has no MCP servers.

---

## 12. Scratchpad instructions

**Source:** `getScratchpadInstructions()`

Conditional on `isScratchpadEnabled()`. If enabled, includes scratchpad
directory path and usage guidance. The snapshot does not include this.

---

## 13. Ant-only sections

**Source:** Various locations in `src/constants/prompts.ts`

Sections that only appear for `USER_TYPE=ant`:

| Section | Line | Content |
|---|---|---|
| Numeric length anchors | 529-536 | "keep text between tool calls to ≤25 words" |
| Ant model override | 496-497 | `getAntModelOverrideConfig()?.defaultSystemPromptSuffix` |
| Bug reporting guidance | 243-246 | `/issue`, `/share`, Slack channel |

---

## 14. Feature-flagged sections

Sections gated on `feature()` (compile-time) or GrowthBook (runtime):

| Feature | Section | Effect |
|---|---|---|
| `TOKEN_BUDGET` | Token budget | "When the user specifies a token target..." |
| `KAIROS` / `KAIROS_BRIEF` | Brief | `getBriefSection()` from BriefTool |
| `PROACTIVE` / `KAIROS` + active | **Entire prompt** | Replaces default with autonomous agent prompt |
| `COORDINATOR_MODE` + env var | **Entire prompt** | Replaces default with coordinator prompt |
| `VERIFICATION_AGENT` + gate | Session guidance | Adversarial verification contract |
| `BREAK_CACHE_COMMAND` | System context | `[CACHE_BREAKER: ...]` injection |

---

## 15. Environment info

**Source:** `computeSimpleEnvInfo()`, `src/context.ts`

Dynamic section containing:
- Primary working directory, git repo status
- Platform, shell, OS version
- Model name and ID
- Context window size (1M vs default)
- Knowledge cutoff date
- Frontier model IDs
- Fast mode info

Git status is skipped if:
- `CLAUDE_CODE_REMOTE` is set (CCR mode)
- `shouldIncludeGitInstructions()` returns false

---

## 16. Complete prompt replacement paths

**Source:** `src/utils/systemPrompt.ts:41-123`

The entire default prompt is replaced in these cases (priority order):

1. `overrideSystemPrompt` set → only that string
2. Coordinator mode active → coordinator prompt + append
3. Agent definition set (non-proactive) → agent prompt replaces default
4. `customSystemPrompt` set (`--system-prompt`) → custom replaces default
5. Proactive mode + agent → default + agent appended

In cases 1-4, none of the sections documented above appear.

---

## 17. SIMPLE mode

**Source:** `src/constants/prompts.ts:450-453`

If `CLAUDE_CODE_SIMPLE=true`:
```
You are Claude Code, Anthropic's official CLI for Claude.

CWD: <path>
Date: <ISO date>
```

One line. No tools guidance, no memory, no output style, nothing.

---

## 18. Cache scope and blocking

**Source:** `src/utils/api.ts:321-425`

Not prompt content, but affects how the prompt is split into API blocks:

| Mode | system[0] | system[1] | system[2] | system[3] |
|---|---|---|---|---|
| Global cache (boundary present) | billing (null) | prefix (null) | static (global) | dynamic (null) |
| Global cache (boundary missing) | billing (null) | prefix (org) | rest (org) | — |
| Global cache + skipGlobal (MCP) | billing (null) | prefix (org) | rest (org) | — |
| No global cache (snapshot) | billing (null) | prefix (ephemeral) | rest (ephemeral) | — |

The snapshot shows the "no global cache" path: 3 blocks, all with
`cache_control: { type: 'ephemeral', ttl: '1h' }`.

---

## 19. API parameters (non-prompt)

These don't change the system prompt text but vary in the request:

| Parameter | Varies on |
|---|---|
| `model` | User selection, permission mode fallback (Haiku at >200k in plan mode) |
| `thinking.type` | `adaptive` (default) vs `enabled` + budget vs `disabled` |
| `output_config.effort` | User/experiment, ant-only numeric override |
| `max_tokens` | Model-dependent |
| `fastMode` | `/fast` toggle, feature gate, rate limit |
| `metadata.user_id` | Device/account/session UUIDs |
| Beta headers | Accumulated from enabled features |
| `context_management` | Thinking clear strategy |

---

## 20. User message injections (not system prompt)

These appear as `<system-reminder>` blocks in the first user message:

| Block | Source | Varies on |
|---|---|---|
| Deferred tools list | Tool search module | Which tools are deferred, MCP tool count |
| Skills list | Skill tool commands | Installed skills/plugins |
| CLAUDE.md context | `getUserContext()` | CLAUDE.md files in CWD + parent dirs + `--add-dir` |
| Current date | `getSystemContext()` | Session start time |

These are technically user messages, not system prompt, but they're
auto-injected by the harness.

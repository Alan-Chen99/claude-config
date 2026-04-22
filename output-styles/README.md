# Output Styles

## Design Decisions

Behavioral rules live here, not CLAUDE.md, because output styles inject into the
system prompt where the model treats them as core identity — CLAUDE.md injects
into a user message and can be overridden. See [Injection Points](#injection-points).

`keep-coding-instructions` is omitted because the custom Coding section replaces
the built-in one with different rules. See [Section Suppression](#section-suppression)
and [Built-in vs Custom Coding Rules](#built-in-vs-custom-coding-rules).

Two versions (`alan-default`, `alan-default-next`) exist so `alan-default-next`
can be modified without breaking the known-good fallback.

`pre_output.record` is a prompt engineering technique, not actual recording — the
script discards its argument and prints a `<system-reminder>` that re-surfaces
behavioral rules at generation time. See [pre_output.record](#pre_outputrecord).

Output style content does not appear in session logs — the system prompt is
rebuilt each API call and never persisted to the JSONL transcript. See
[Session Logs](#session-logs).

## Invariants

- Styles that omit `keep-coding-instructions` MUST contain their own coding
  guidance — otherwise the model receives no coding rules at all.
- `alan-default` must remain a valid, complete style at all times.

## Activation

Set the active style via `/config` (interactive picker) or by editing
`settings.json` → `outputStyle` field directly. The value matches the style's
`name` frontmatter field (or filename without `.md` if `name` is absent).

`/output-style` existed but is deprecated and hidden — it prints a message
redirecting to `/config`.

## Official Documentation

https://docs.anthropic.com/en/docs/claude-code/output-styles

## Feature backlog

"use jq for json, not read/edit"

---

## Reference

### System prompt context

The system prompt is a `string[]`. `splitSysPromptPrefix()` joins all elements
with `\n\n`. For the full layout, see
[`docs/system-prompt-anatomy.md`](../docs/system-prompt-anatomy.md).

**10 lines before** `# Output Style:` (end of `env_info_simple`, the
immediately preceding dynamic section — `language` appears between them only if
a language preference is set):

```
 - Platform: linux
 - Shell: zsh
 - OS Version: Linux 6.8.0-50-generic
 - You are powered by the model named Claude Opus 4.6 (with 1M context). The exact model ID is claude-opus-4-6[1m].
 -

Assistant knowledge cutoff is May 2025.
 - The most recent Claude model family is Claude 4.5/4.6. Model IDs — ...
 - Claude Code is available as a CLI in the terminal, desktop app ...

<fast_mode_info>
Fast mode for Claude Code uses the same Claude Opus 4.6 model with faster output. It does NOT switch to a different model. It can be toggled with /fast.
</fast_mode_info>
```

**10 lines after** (end of style content → next non-null dynamic sections →
`systemContext` appended by `appendSystemContext()`):

```
                                            ← style content ends here

When working with tool results, write down any important information you might
need later in your response, as the original tool result may be cleared later.

gitStatus: This is the git status at the start of the conversation. Note that
this status is a snapshot in time, and will not update during the conversation.
Current branch: main
...
```

Between the style and `gitStatus`, additional sections may appear if active:
`mcp_instructions` (MCP servers connected), `scratchpad` (if enabled),
`frc` (function result clearing).

### Section boundary

There is no closing marker for the output style. Sections are separate strings
in the array, joined with `\n\n` by `splitSysPromptPrefix()`. The model infers
where the style ends from the next `#`-level heading (the next section). Since
output style content can contain its own sub-headings (`##`, `###`), only a
top-level `#` heading signals a new section.

When an output style is active, the intro preamble (first section in the prompt)
reads:

> You are an interactive agent that helps users according to your "Output Style"
> below, which describes how you should respond to user queries.

When no output style is active (default):

> You are an interactive agent that helps users with software engineering tasks.

Source: `prompts.ts:151-158,175-184`, `api.ts:321-435`

### Injection points

The output style is registered as a `systemPromptSection('output_style', ...)`
in the dynamic portion of the system prompt. The wrapping is minimal — just a
heading and raw content, no closing marker:

```
# Output Style: {name}
{prompt}
```

Source: `prompts.ts:151-158`

Styles load with descending priority: managed (policy) > project
(`.claude/output-styles/`) > user (`~/.claude/output-styles/`) > plugin >
built-in. Same-name styles in higher-priority locations shadow lower ones.

Note: the source code comment at `outputStyles.ts:158` says
"lowest to highest: built-in, plugin, managed, user, project" but the actual
array order is `[plugin, user, project, managed]` — managed wins because it's
last in the override loop.

Source: `outputStyles.ts:137-174`

YAML frontmatter fields: `name` (display name, defaults to filename without
`.md`), `description` (falls back to first markdown line),
`keep-coding-instructions` (section suppression flag),
`force-for-plugin` (plugin-only, auto-apply when plugin is enabled).

### Caching

Two independent caches gate output style content:

1. **File discovery** — `getAllOutputStyles()` is memoized via
   `lodash-es/memoize`. Cleared by `clearAllCaches()` (plugin operations,
   `/reload-plugins`). NOT cleared by `/clear` or `/compact`.

2. **System prompt section** — `systemPromptSection('output_style', ...)`
   caches the computed section string. Cleared by `/clear` and `/compact`.

Editing a `.md` file mid-conversation requires clearing **both** caches. Since
`/clear` only clears cache #2, edits to style files effectively require a new
session. Changing the `outputStyle` setting (which style is selected) also
requires a new session — the deprecation message for `/output-style` explicitly
says so.

Source: `outputStyles.ts:137,177-179`, `systemPromptSections.ts:60-68`,
`cacheUtils.ts:26-50`

### Section suppression

`keep-coding-instructions` is the only mechanism to suppress a default system
prompt section. The logic in `prompts.ts:564-567`:

```
outputStyleConfig === null ||
outputStyleConfig.keepCodingInstructions === true
  ? getSimpleDoingTasksSection()
  : null
```

When absent or `false` with a custom style active, the harness drops
`getSimpleDoingTasksSection()`.

### Built-in vs custom coding rules

`getSimpleDoingTasksSection()` contains ~2k tokens: scope discipline ("don't add
features beyond what was asked"), security rules, error handling defaults,
backwards-compatibility preferences, comment policy ("only add comments where
logic isn't self-evident"), help command references.

The custom Coding section in `alan-default`/`alan-default-next` diverges:

- Built-in: conservative scope ("don't refactor beyond what was asked"). Custom:
  free refactoring, break backwards compatibility.
- Built-in: no complexity hierarchy. Custom: stdlib > direct > patterns.
- Built-in: paradigm-neutral. Custom: functional programming preference.
- Built-in: when-to-comment policy only. Custom: Timeless Present rule
  (comment voice — no change-narrative, no baseline references, no planning
  artifacts).

### pre_output.record

The `Before response` section in the output styles invokes
`skills.pre_output.record`. Despite the name, this script records nothing. The
JSON argument is accepted and discarded. The mechanism:

1. The output style instructs Claude to call the script before every response.
2. The script prints a `<system-reminder>` containing behavioral rules.
3. Because tool results inject at the recency edge of context, these rules get
   high model attention at generation time.

This is a prompt engineering technique for rule reinforcement — the "record"
framing gives the model a plausible reason to make the tool call. The actual
value is the printed reminder, not any state persistence.

Source: `skills/scripts/skills/pre_output/record.py`

### Session logs

Session transcripts are JSONL files at
`~/.claude/projects/{sanitized-path}/{sessionId}.jsonl`. Each entry contains
message content plus metadata (sessionId, cwd, version, gitBranch, timestamp,
userType).

The system prompt is NOT stored in session logs. It is rebuilt from source each
API call via `getSystemPrompt()` → `queryModel()`. This means:

- Output style content does not appear in logs.
- The active output style cannot be determined from a session log alone.
- Subagent system prompts are also not logged (same rebuild-per-call pattern).

Source: `sessionStorage.ts:1048-1065` — only message objects are persisted via
`appendEntry()`. System prompt assembly happens in `prompts.ts` and
`services/api/claude.ts`, neither of which writes to the session file.

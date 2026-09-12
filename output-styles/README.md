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

### Durability across a background handoff

An output style is the only prompt customization that survives a session moving
to the background. The fork Claude Code spawns is launched without
`--system-prompt`, `--system-prompt-file`, or `--append-system-prompt`, but it
reads `settings.json`, so `outputStyle` still applies. A prompt that must hold
for *every* session belongs here rather than in `sys_prompt/`, and the two must
not be allowed to drift — `sys_prompt/alan-default-next.md` and
`output-styles/alan-default-next.md` share a name but not their content, so
which rules are in force depends on whether the session was backgrounded. See
`docs/background-sessions.md`.

## Official Documentation

https://docs.anthropic.com/en/docs/claude-code/output-styles

## Feature backlog

"use jq for json, not read/edit"

---

## Reference

### Where the style is delivered

**As of 2.1.269 the style is not in the system prompt at all.** It arrives in
`messages[]` as a `role: "system"` message, inside its own `<system-reminder>`
pair, alongside the deferred-tool, agent-type, skill and environment reminders:

```
<system-reminder>
# Output Style: {name}
{prompt}
</system-reminder>
```

That message block carries `cache_control: {"type": "ephemeral", "ttl": "1h"}`.

Measured on `docs/system-prompt-snapshot/sonnet-5/custom-output-style/`: in the
2.1.269 `request.json` the string `Explanatory` appears nowhere in `system[]`
and the style sits in `messages[1]`; in the 2.1.235 capture of the same variant
it is in `system[]`.

Through 2.1.235 the style sat inside the cached `system[]` array, joined with
`\n\n` by `splitSysPromptPrefix()`, immediately after `env_info_simple` and
ahead of `gitStatus`, with `mcp_instructions`, `scratchpad` and `frc` able to
appear between. Any description of a fixed "N lines before/after
`# Output Style:`" describes that layout and no longer locates anything.

### Section boundary

**As of 2.1.269 the style has an explicit closing marker** — the
`</system-reminder>` that ends its reminder. A style body may use as many
top-level `#` headings as it likes without bleeding into what follows.

Through 2.1.235 there was no closing marker: sections were separate strings in
`system[]` joined with `\n\n`, and the model inferred the end of the style from
the next top-level `#` heading. That made a style carrying its own `#` headings
(as `alan-default-next.md` does) genuinely ambiguous. The move to a delimited
reminder removes that hazard rather than introducing one.

When an output style is active, the intro preamble reads (2.1.269 — earlier
versions ended the first clause with "below", which went away with the
adjacency it referred to):

> You are an interactive agent that helps users according to your "Output Style",
> which describes how you should respond to user queries. Use the instructions
> below and the tools available to you to assist the user.

When no output style is active (default):

> You are an interactive agent that helps users with software engineering tasks.

### Injection points

Through 2.1.235 the style was a `systemPromptSection('output_style', ...)`
inside `system[]`, wrapped as a bare heading plus raw content. As of 2.1.269 it
is a `<system-reminder>` in the `role: "system"` message instead — see "Where
the style is delivered".

The `prompts.ts` and `outputStyles.ts` citations in this file point into
`/repos/claude-code-src/`, which is pinned to v2.1.88 and predates both
layouts; they are kept as provenance, not as addresses that resolve against
what ships now. To re-find the current code, grep `Output Style: ` in
`/repos/claude-code-decompiled/src/`.

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

2. **Prompt cache breakpoint** — through 2.1.235,
   `systemPromptSection('output_style', ...)` cached the computed section as
   part of `system[]`, cleared by `/clear` and `/compact`. As of 2.1.269 the
   style rides in the `role: "system"` message, which carries its own
   `cache_control: {"type": "ephemeral", "ttl": "1h"}`, so 1h caching still
   applies but through a different breakpoint. Whether `/clear` and `/compact`
   still invalidate it the same way is untested.

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
`agent-tools pre_output.record`. Despite the name, this script records nothing.
The JSON argument is accepted and discarded. The mechanism:

1. The output style instructs Claude to call the script before every response.
2. The script prints a `<system-reminder>` containing behavioral rules.
3. Because tool results inject at the recency edge of context, these rules get
   high model attention at generation time.

This is a prompt engineering technique for rule reinforcement — the "record"
framing gives the model a plausible reason to make the tool call. The actual
value is the printed reminder, not any state persistence.

Source: `src/claude_config/pre_output/record.py` (wrapped by `agent-tools pre_output.record`; see `agent-tools/src/main.rs`)

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

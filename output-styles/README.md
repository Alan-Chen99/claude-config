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

## Official Documentation

https://docs.anthropic.com/en/docs/claude-code/output-styles

---

## Reference

### Injection points

Output styles register as a cacheable `output_style` section in the dynamic
portion of the system prompt, after static behavioral sections. The harness wraps
content with `# Output Style: {name}` before injection. The section is memoized
via `systemPromptSection()` — changing the file mid-conversation has no effect
until the cache clears (`/clear`, `/compact`, or settings sync).

Styles load with descending priority: managed (`/etc/claude-code/`) > user
(`~/.claude/output-styles/`) > project (`.claude/output-styles/`). Same-name
styles in higher-priority locations shadow lower ones.

YAML frontmatter fields: `name` (display name, defaults to filename without
`.md`), `description` (falls back to first markdown line),
`keep-coding-instructions` (section suppression flag).

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

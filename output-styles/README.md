# Output Styles

## Design Decisions

Behavioral rules live here, not CLAUDE.md, because the style arrives as a
`role: "system"` message and the cached system prompt's opener defers to it —
`helps users according to your "Output Style"` replaces the default opener
(`../docs/system-prompt-snapshot/sonnet-5/custom-output-style/prompt.md`,
`system[2]`) — where CLAUDE.md arrives as a `user` message and can be overridden.
See [Where the style is delivered](#where-the-style-is-delivered).

`keep-coding-instructions` is omitted because the custom Coding section replaces
the built-in one with different rules: absent or `false`, with a custom style
active, the harness drops its `# Doing tasks` section.

`pre_output.record` is a prompt engineering technique first — the script prints a
`<system-reminder>` that re-surfaces behavioral rules at generation time, and that
is what the call is for. It also keeps the argument: the `summary` field becomes the
body of the ntfy "Done" push (`src/claude_config/ntfy_hook.py`).

Output style content does not appear in session logs — the system prompt is
rebuilt each API call and never persisted to the JSONL transcript.

## Invariants

- Styles that omit `keep-coding-instructions` MUST contain their own coding
  guidance — otherwise the model receives no coding rules at all.

## Activation

Set the active style via `/config` (interactive picker) or by editing
`settings.json` → `outputStyle` field directly. The value matches the style's
`name` frontmatter field (or filename without `.md` if `name` is absent).

`/output-style` existed but is deprecated and hidden — it prints a message
redirecting to `/config`.

Editing a style file, or changing which style is selected, takes effect in a new
session: style discovery is memoized, and `/clear` and `/compact` do not reload it.

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

## Where the style is delivered

**As of 2.1.269 the style is not in the system prompt at all** (re-verified on the
2.1.289 `sonnet-5/custom-output-style` capture: `Explanatory` is in no `system[]` block). It arrives in
`messages[]` as a `role: "system"` message carrying
`cache_control: {"type": "ephemeral", "ttl": "1h"}`, inside its own
`<system-reminder>` pair:

```
<system-reminder>
# Output Style: {name}
{prompt}
</system-reminder>
```

The closing tag ends the style, so its body may use top-level `#` headings without
bleeding into what follows. To re-find the code, grep `Output Style: ` in
`/repos/claude-code-decompiled/src/`.

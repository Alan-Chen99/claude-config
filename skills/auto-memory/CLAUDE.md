# auto-memory/

Drop-in for Claude Code's built-in auto-memory feature. Must load before any
read or write of memories under `~/.claude/projects/<slug>/memory/`. Do not
load when the system prompt already contains an "# auto memory" section
(built-in feature is active).

## Files

| File       | What                                                                           | When to read              |
| ---------- | ------------------------------------------------------------------------------ | ------------------------- |
| `SKILL.md` | Verbatim auto-memory section from the default prompt, with path derivation     | Using `/auto-memory` skill |

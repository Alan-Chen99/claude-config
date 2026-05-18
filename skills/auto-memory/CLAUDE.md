# auto-memory/

On-demand drop-in for Claude Code's built-in auto-memory feature. Activates the
same file-based memory protocol when `autoMemoryEnabled: false` in
`settings.json`. Explicit invocation only.

## Files

| File       | What                                                                           | When to read              |
| ---------- | ------------------------------------------------------------------------------ | ------------------------- |
| `SKILL.md` | Verbatim auto-memory section from the default prompt, with path derivation     | Using `/auto-memory` skill |

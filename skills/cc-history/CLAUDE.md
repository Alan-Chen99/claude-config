# cc-history/

Reference documentation for analyzing Claude Code conversation history files.

## Files

| File                     | What                                                                 | When to read                                  |
| ------------------------ | -------------------------------------------------------------------- | --------------------------------------------- |
| SKILL.md                 | Query patterns and command reference                                 | Analyzing conversation history                |
| README.md                | Design decisions and structural knowledge                            | Understanding format and trade-offs           |
| record-types.md          | The binary's own entry-type roster: retention class, fields, citation, whether seen here | Writing a recipe keyed on a `.type`, or judging whether a type is gone |
| background-commands.md   | The four ways a Bash call reaches the background, the `toolUseResult` fields and what this corpus can settle | Reading a backgrounded command out of a transcript |

## Related Directories

| Directory                 | What                         | When to read                   |
| ------------------------- | ---------------------------- | ------------------------------ |
| `~/.claude/projects/`     | Conversation history storage | Querying actual history files  |
| `~/.claude/settings.json` | Claude Code configuration    | Understanding project settings |

# Built-in Output Styles

From `constants/outputStyles.ts` in Claude Code v2.1.79.
These are the three built-in output styles. Custom styles go in `~/.claude/output-styles/*.md`.

## default

Maps to `null`. No output style section is injected. The model gets the standard
system prompt with `# Doing tasks` included. This is what you get with no
`outputStyle` setting, or `outputStyle: "default"`.

Note: the key is lowercase `"default"`. Any other casing (e.g. `"Default"`) does
not match and also resolves to null via the fallback path.

## Explanatory

`keep-coding-instructions: true` — `# Doing tasks` stays in the system prompt.

Adds educational "Insight" blocks before and after code. The model is told to
provide 2-3 key educational points in a bordered format using `★ Insight` headers.
Insights go in conversation output, not in the codebase.

See: [Explanatory.md](Explanatory.md)

## Learning

`keep-coding-instructions: true` — `# Doing tasks` stays in the system prompt.

Interactive mode where the model pauses and asks the user to write 2-10 line code
pieces for design decisions, business logic, and key algorithms. Uses `TODO(human)`
markers in the codebase and "Learn by Doing" request blocks. Includes the same
Insight feature as Explanatory.

See: [Learning.md](Learning.md)

## How output styles work

The style's prompt text is injected as `# Output Style: <name>` inside the
memory/environment system block (block 3), between `# Environment` and `gitStatus`.

The `keep-coding-instructions` flag controls whether `# Doing tasks` (~3.4K chars)
is included in the behavioral rules block (block 2):

| value | `# Doing tasks` |
|---|---|
| `true` | included |
| `false` | removed |
| omitted | removed (default) |

See [what-the-model-gets.md](../what-the-model-gets.md) for the full block layout.

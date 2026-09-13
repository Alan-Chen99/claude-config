# Built-in Output Styles

**Captured from Claude Code v2.1.87 and not re-captured since; the installed version is 2.1.269.**
Treat every file here as a record of that older build. The set is also known to be incomplete:
2.1.257's release notes name a `Proactive` style, and the literal appears in the 2.1.269 decompile,
but no file here corresponds to it. Re-capture every built-in before relying on this directory.

From `constants/outputStyles.ts` in Claude Code v2.1.87.
Custom styles go in `~/.claude/output-styles/*.md`.

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

In v2.1.87 the style's prompt text was injected as `# Output Style: <name>`
inside the dynamic system block (block 3), between `# Environment` and
`gitStatus`. In 2.1.269 none of the three is in that position: the style
arrives in `messages[]` as a `role: "system"` message, `gitStatus` has left
block 3 for `messages[0]`, and block 3's `# Environment` heading survives
holding only ecosystem facts — model ids and where Claude Code runs — with the
machine facts moved to `messages[]` too. `../sonnet-5/custom-output-style/prompt.md`
is the live shape.

As of v2.1.87, `# Doing tasks` is always included in system[2] regardless of
the output style or `keep-coding-instructions` flag. The preamble changes from
"helps users with software engineering tasks" to "helps users according to your
'Output Style' below".

See [what-the-model-gets.md](../what-the-model-gets.md) for the full block layout.

# sys_prompt/

Full replacement system prompts loaded via `--system-prompt-file` by `scripts/claude.sh`.
Background and forked sessions do not inherit them — read `docs/background-sessions.md` before editing.

## Files

| File                   | What                                                  | When to read |
| ---------------------- | ----------------------------------------------------- | ------------ |
| `alan-default.md`      | Known-good production prompt                          | -            |
| `alan-default-next.md` | Active development prompt; the one `claude.sh` loads  | -            |

## Keep it concise

Every token here is spent on every request of every session and displaces the user's work from the
context window. A line the model would honour unprompted, or that restates a neighbour, costs context
and buys nothing.

After any edit:

1. Re-read the passage and cut a word. Repeat until cutting another would lose meaning.
2. Re-read the surrounding section. If a neighbouring line now says the same thing, delete one.
3. Name the behaviour that changes without the line. If you cannot, drop the line.

Three words can be enough — ``Prefer `model: haiku`.`` is a complete rule. Anything that dates the
line goes in this file rather than the prompt: version numbers, issue links, dates, measurements,
and the reasoning that justified the line in the first place.

Detail that fails step 3 is not discarded — it moves here, to `docs/`, or to `notes/`. The prompt
states the rule; the file carries the reasoning. That split is what lets step 1 cut hard without
losing anything.

Measure before and after:

```bash
agent-tools count-tokens --api --file sys_prompt/alan-default-next.md
```

## Why the prompt says what it says

Reasoning cut from the prompt under step 3 above, kept so a future edit can tell a live rule from
cargo. Each entry names what would retire it.

### `Prefer model: haiku` on Explore spawns

Claude Code 2.1.198 (2026-07-01) changed the built-in Explore agent's model from `haiku` to
`inherit`, so an Explore spawn now runs the session's model unless the call passes one. The change
was a reliability fix, not a quality one: issue #45357 reported that a large MCP tool surface
overflowed Haiku's prompt limit and killed every spawn. That failure needs a heavy MCP install; a
session without one keeps Haiku's headroom, and Explore is scoped to locating code rather than
reviewing or analysing it.

`Prefer` carries the escape hatch, so the prompt does not spell one out: pass `sonnet` or `opus`
when a search is genuinely hard — tracing minified identifiers through decompiled chunks, say,
rather than finding a file. Haiku also drops the session's inherited `effort` setting, which the
API rejects for that model, and falls back from adaptive to plain extended thinking.

Passing the parameter per call, rather than shadowing the built-in with a user-defined `Explore`
agent: `omitClaudeMd` is set only on built-in agent definitions and is never read from frontmatter,
so a shadow re-attaches the whole CLAUDE.md hierarchy to every spawn.

Retire this if the built-in default returns to `haiku`, or if Explore spawns start failing on prompt
size — which would mean the MCP surface has grown into the case #45357 describes.

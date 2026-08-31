# A user record's `toolUseResult` has no closed shape

Investigated 2026-08-31 against Claude Code **2.1.235** (`/repos/claude-code-decompiled`).

`cc-pretty` crashed with `ValueError: unexpected toolUseResult type: <class 'list'>` on a
transcript containing `mcp__claude-in-chrome__*` calls. `parse_tool_use_result` modelled the
field as a closed union of `None | str | dict` and raised on anything else.

The union is the wrong model. `toolUseResult` is whatever a tool put in its result `data`,
serialized verbatim — a tool-defined payload, not a schema cc controls. `cc_pretty/parse.py`
therefore models only the object form (the one the renderer reads `stderr` out of) and
returns every other value untouched.

## Why there is no closed union

The transcript line is a verbatim `JSON.stringify` of the in-memory record
(`insertMessageChain`, `src/globals/20.js:28281`, assignment at `:28350`; writer `WTr`,
`src/globals/01.js:3092`). The only rewrite on the way out, `Zwm`
(`src/globals/20.js:24718`), nulls an oversized `originalFile` **string** property and
passes everything else through.

The `eval_registered__*` plugin-eval tools set `data` to arbitrary parsed JSON
(`src/globals/15.js:21099`):

```js
return { data: a === void 0 ? void 0 : Xt(a) };
```

`Xt` is `JSON.parse` (`src/globals/01.js:3129`), so a bare number, boolean, string, `null`,
array or object can all reach the field. Any tool is free to do the same; nothing in the
write path narrows it.

## MCP tools specifically: string or content-block array

`mcp__*` is narrower than the field as a whole. `_ym` (`src/globals/20.js:2597`) normalizes
the JSON-RPC `CallToolResult` into exactly three outcomes, and **throws** on anything else
(`MCP tool unexpected response format`), so a malformed response never reaches a transcript:

| Server returned | `data` becomes |
|---|---|
| `toolResult` | `String(e.toolResult)` — a string |
| `structuredContent` | `JSON.stringify(...)` — a string, or a content-block array when non-text blocks accompany it |
| `content` array | a content-block array |

So for MCP the domain is closed to `str \| list[block]`. It is the *other* tools that make
the field open.

## Why the renderer shows nothing for the array form

Both fields are assigned from the same variable in one call
(`src/globals/17.js:7000-7008`):

```js
v.push({ message: hn({
    content: gr,                    // gr[0] = the tool_result block
    toolUseResult: wr,              // wr = Lt, the same tool result value
    … }) });
```

`gr[0]` comes from `AFr` → `e.mapToolResultToToolResultBlockParam(t, r)`
(`src/globals/08.js:17026`). The MCP base tool (`src/modules/yal.js:91`) is the only mapper
in the codebase whose `content` is the input itself:

```js
mapToolResultToToolResultBlockParam(e, t) {
  return { tool_use_id: t, type: 'tool_result', content: Gtt(e) };
}
```

`Gtt` (`src/globals/19.js:8760`) returns its argument unchanged unless some `text` block
carries `_meta`, in which case it returns a shallow copy with `_meta` deleted. Rendering the
array alongside the block body would therefore print the body twice.

Every other mapper stringifies its `data`, so the block body already shows the same
information as JSON text — `ListMcpResourcesTool` (`src/modules/M$n.js:113`),
`RefreshMcpTools` (`src/modules/rwf.js:160`) and the plugin-eval tools
(`src/globals/15.js:21108`) all end in `content: <stringify>(e)`.

### The three ways an MCP array and its block body can diverge

All inside `gqb` (`src/globals/08.js:17054`), which post-processes the block param only:

| Case | `tool_result` content becomes | `toolUseResult` keeps |
|---|---|---|
| Empty result | `` `(<tool> completed with no output)` `` | `[]` |
| Text over the size cap (MCP: `min(maxResultSizeChars, 50000)` chars) | `"Output too large (…). Full output saved to: <path>"` | the full array |
| A `text` block carrying `_meta` | the block without `_meta` | the block with `_meta` |

Both divergent renderings were constructed and checked: the block body states the elision
and names the file it went to, so nothing a reader needs is lost by ignoring the array.
`tests/test_cc_pretty_render.py::test_tool_output_omits_mcp_array_result_that_diverges_from_body`
holds that decision in place.

`gqb` returns early for content containing an `image` or `document` block
(`src/globals/08.js:17067`), so the size cap never applies to a screenshot result; row 1
cannot apply either, since an array holding an image block is not empty.

Two record-level caveats null the field entirely rather than changing its shape: subagent
transcripts drop it (`src/globals/17.js:7004`) unless `preserveToolUseResults`, and tools
declaring `stripToolUseResultAtCreation` rewrite it (`:6994`).

## Corpus evidence

Over all 2,032 JSONL transcripts under `~/.claude/projects` on this machine (852 MB), only
three shapes occurred: string, object, and — in exactly one file, the `claude-in-chrome`
session, in 12 records — an array, byte-equal to `.message.content[0].content` every time.
No scalar was observed; the plugin-eval path above is why the parser accepts one anyway.

## Related rendering defect (not fixed)

`_render_tool_result` renders a non-`text` block inside a list-valued `content` with
`str(sub)`. For an `image` block that is a truncated base64 blob rather than a placeholder.
The corpus sweep found 23 image blocks across 23 files, so this affects roughly 1% of
transcripts, including the `claude-in-chrome` session that prompted this note.

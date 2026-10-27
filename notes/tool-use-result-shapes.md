# A user record's `toolUseResult` has no closed shape

Investigated 2026-08-31 against Claude Code **2.1.235**.

> **Citations below are pinned to 2.1.235** and resolve to nothing in
> `/repos/claude-code-decompiled`'s later re-extraction, which has no `src/globals/` or
> `src/modules/` tree. To re-resolve one, see that repo's README, "Re-resolving an old
> citation."

`cc-pretty` crashed with `ValueError: unexpected toolUseResult type: <class 'list'>` on a
transcript containing `mcp__claude-in-chrome__*` calls: `parse_tool_use_result` modelled the
field as a closed union of `None | str | dict`. What `cc_pretty/parse.py` models of this
tool-defined payload instead is in its docstring.

## Why there is no closed union

The transcript line is a verbatim `JSON.stringify` of the in-memory record
(`insertMessageChain`, `src/globals/20.js:28281`, assignment at `:28350`; writer `WTr`,
`src/globals/01.js:3092`). The only rewrite on the way out, `Zwm`
(`src/globals/20.js:24718`), nulls an oversized `originalFile` **string** property and
passes everything else through.

The `eval_registered__*` plugin-eval tools set `data` to arbitrary parsed JSON,
`data: a === void 0 ? void 0 : Xt(a)` (`src/globals/15.js:21099`), `Xt` being `JSON.parse`
(`src/globals/01.js:3129`), so a bare number, boolean, string, `null`, array or object can
all reach the field, from any tool doing the same: nothing in the write path narrows it.

## MCP tools specifically: string or content-block array

`_ym` (`src/globals/20.js:2597`) normalizes the JSON-RPC `CallToolResult` into exactly three
outcomes, and **throws** on anything else (`MCP tool unexpected response format`), so a
malformed response never reaches a transcript:

| Server returned | `data` becomes |
|---|---|
| `toolResult` | `String(e.toolResult)` — a string |
| `structuredContent` | `JSON.stringify(...)` — a string, or a content-block array when non-text blocks accompany it |
| `content` array | a content-block array |

## Why the renderer shows nothing for the array form

Both fields come from one value in one call, `v.push({ message: hn({ content: gr,
toolUseResult: wr, … }) })`, `gr[0]` the tool_result block and `wr = Lt` the tool result
(`src/globals/17.js:7000-7008`). `gr[0]` comes from `AFr` →
`e.mapToolResultToToolResultBlockParam(t, r)` (`src/globals/08.js:17026`). The MCP base
tool's mapper (`src/modules/yal.js:91`) is the only one whose `content` is the input itself,
`content: Gtt(e)`; `Gtt` (`src/globals/19.js:8760`) returns its argument unchanged unless
some `text` block carries `_meta`, then a shallow copy with `_meta` deleted. Rendering the
array beside the block body would print the body twice.

Every other mapper stringifies its `data` into the block body:
`ListMcpResourcesTool` (`src/modules/M$n.js:113`), `RefreshMcpTools` (`src/modules/rwf.js:160`)
and the plugin-eval tools (`src/globals/15.js:21108`) all end in `content: <stringify>(e)`.

### The three ways an MCP array and its block body can diverge

All in `gqb` (`src/globals/08.js:17054`), which post-processes only the block param:

| Case | `tool_result` content becomes | `toolUseResult` keeps |
|---|---|---|
| Empty result | `` `(<tool> completed with no output)` `` | `[]` |
| Text over the size cap (MCP: `min(maxResultSizeChars, 50000)` chars) | `"Output too large (…). Full output saved to: <path>"` | the full array |
| A `text` block carrying `_meta` | the block without `_meta` | the block with `_meta` |

Both divergent renderings were constructed and checked: the block body states the elision
and names the file it went to, so ignoring the array loses nothing a reader needs
(`tests/test_cc_pretty_render.py::test_tool_output_omits_mcp_array_result_that_diverges_from_body`).

`gqb` returns early for content containing an `image` or `document` block
(`src/globals/08.js:17067`), so the size cap never applies to a screenshot result.

Two record-level caveats null the field rather than reshape it: subagent
transcripts drop it (`src/globals/17.js:7004`) unless `preserveToolUseResults`, and tools
declaring `stripToolUseResultAtCreation` rewrite it (`:6994`).

## Corpus evidence

Over all 2,032 JSONL transcripts under `~/.claude/projects` here (852 MB), only three
shapes occurred: string, object, and — in exactly one file, the `claude-in-chrome`
session, in 12 records — an array, byte-equal to `.message.content[0].content` every time.
No scalar was observed.

## Related rendering defect (fixed 2026-09-28)

`_render_tool_result` rendered a non-`text` block inside a list-valued `content` with
`str(sub)`: for an `image` block, a truncated base64 blob rather than a placeholder. The
corpus sweep found 23 image blocks across 23 files, roughly 1% of transcripts, the
`claude-in-chrome` session among them.

The fix (`BinaryBlock` for `image` and `document`, in `cc_pretty/render.py`) came with a sweep
of 3,593 transcripts (2.6 GB) for base64-shaped strings rather than for `"type":"image"`: 638
image blocks in tool_result content arrays across 102 files, plus 13 `document` blocks sitting
directly on a user record — the second position, which reached the render through the
unmodelled-block arm. Two further positions carry a payload the renderer never reads and so
never leaked: `.toolUseResult.file.base64` (381) and `.toolUseResult[].source.data` (15).

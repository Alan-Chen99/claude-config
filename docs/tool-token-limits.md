# Tool token limits and truncation behaviour

Read off the decompiled binary at `/repos/claude-code-decompiled`, Claude Code
**2.1.289**. Citations are `src/chunk-<hash>.js:<line>` there and expire at the next
re-extraction (`.claude/skills/update-claude-code`). Every figure is a constant in the
source, not a measurement.

## How tokens are counted

Two tiers, no local tokenizer: the Anthropic API's `countTokens` is the measurement
(`src/chunk-c06bg8hw.js:42613`), and a character ratio is the estimate that decides
whether to call it — 4 characters per token, 2 for `json`/`jsonl`/`jsonc`
(`src/chunk-898k2gs2.js:4192-4206`). The same ratio of 4 converts the token caps below
into byte caps (`src/chunk-qtae7z5t.js:27`).

## Per-tool caps

A tool result over its **persist threshold** is written to the session's
`tool-results` directory and the model gets a preview plus the path; the threshold is
the tool's `maxResultSizeChars`, raised or lowered per tool by the
`tengu_velvet_ibis` payload up to the tool's own ceiling
(`src/chunk-wjjn7eps.js:33-39`).

| Tool | Cap | Over it |
| --- | --- | --- |
| Read | 256 KiB on the file (`src/chunk-etfth4ht.js:192`), 25,000 output tokens (`src/chunk-kkahyxqn.js:15`) | Throws `MaxFileReadTokenExceededError`; the model must pass `offset`/`limit`. An estimate at or under 25% of the limit skips the API call; over 128 bytes per allowed token it throws without one (`src/chunk-wgfrtm7w.js:38960-38967`) |
| Bash | 30,000 chars inline, `bashOutputMaxChars` or `BASH_MAX_OUTPUT_LENGTH` moving it (`src/chunk-1y80m7e8.js:26-41`); 2²⁵ chars in the stream accumulator (`src/chunk-f4y6hk8a.js:157`) | Head truncation keeping the beginning, `... [N lines truncated] ...` (`src/chunk-wgfrtm7w.js:37867-37879`), then persistence. The accumulator end-truncates: `... [output truncated - NKB removed]` |
| Grep | 250 entries by default, `head_limit: 0` for none (`src/chunk-wgfrtm7w.js:39940`); persist at 20,000 chars (`:39979`) | `[Showing results with pagination = limit: N, offset: M]`; a content line over 500 chars becomes `[Omitted long matching line]` (`:40471`) |
| Glob | 100 files; persist at 100,000 chars (`src/chunk-wgfrtm7w.js:39764`) | `truncated: true` and a note naming the total when it is known (`:39739-39745`) |
| Edit | 1 GiB editable file size (`src/chunk-wgfrtm7w.js:155630`); persist at 100,000 chars | `File is too large to edit`, before any read |
| Write, Agent | persist at 100,000 chars (`src/chunk-wgfrtm7w.js:31821`, `src/chunk-qws8heqd.js:18`) | — |
| WebFetch | 1 MiB of HTML before conversion (`src/chunk-wgfrtm7w.js:56493`), 100,000 chars of markdown after (`src/chunk-1y80m7e8.js:251`); persist at 50,000 chars and outside the aggregate budget (`src/chunk-wgfrtm7w.js:57009-57010`) | `[Content truncated due to length...]` |
| MCP tool | 2,048 chars per tool description and per server instruction block, `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` moving it (`src/chunk-wgfrtm7w.js:62466`, `src/chunk-bfmr5z4y.js:25`) | Truncated |

## Session-wide caps

| Constant | Value | What it bounds |
| --- | --- | --- |
| `src/chunk-qtae7z5t.js:23` | 50,000 chars | Default persist threshold where a tool names none |
| `src/chunk-qtae7z5t.js:28` | 400,000 bytes | One tool result, derived from 100,000 tokens at 4 bytes each |
| `src/chunk-qtae7z5t.js:29` | 200,000 chars | All tool results in one message; the largest blocks persist first until under it (`src/chunk-wjjn7eps.js:411-436`) |
| `src/chunk-qtae7z5t.js:31` | 1 GiB | A persisted tool result on disk |
| `src/chunk-eebrsra2.js:57` | 5 GiB | One background task's output file; past it the file carries `[output truncated: exceeded 5GB disk cap]` |
| `src/chunk-eebrsra2.js:59` | 64 MiB | A persisted output's own byte limit, under which the saved file may end mid-structure |

## Knobs

| Knob | Where | Default | Bounds |
| --- | --- | --- | --- |
| `bashOutputMaxChars` | `settings.json` | 30,000 | clamped to 4,000–128,000; also replaces `BASH_MAX_OUTPUT_LENGTH` |
| `BASH_MAX_OUTPUT_LENGTH` | env | 30,000 | capped at 150,000; sizes the read-back window only |
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` | env | 25,000 | any positive value |
| `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` | env | 2,048 | any value |
| `taskOutputMaxChars`, `TASK_MAX_OUTPUT_LENGTH` | `settings.json`, env | — | **Inert.** The `TaskOutput` tool is gone; a background task's output file is read with `Read` (`src/chunk-q75vj0vh.js:5959`) |

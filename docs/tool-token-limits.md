# Tool token limits and truncation behaviour

Read off the decompiled binary at `/repos/claude-code-decompiled`, Claude Code
**2.1.310**. Citations are `src/chunk-<hash>.js:<line>` there and expire at the next
re-extraction (`.claude/skills/update-claude-code`). Every figure is a constant in the
source, not a measurement.

## How tokens are counted

Two tiers, no local tokenizer: the Anthropic API's `countTokens` is the measurement
(`src/chunk-j0tbz6ra.js:40781`), and a character ratio is the estimate that decides
whether to call it — 4 characters per token, 2 for `json`/`jsonl`/`jsonc`
(`src/chunk-wany0nxw.js:3995-4008`).

## Per-tool caps

A tool result over its **persist threshold** is written to the session's
`tool-results` directory and the model gets a preview plus the path. The threshold is
the tool's `maxResultSizeChars` capped at its `persistenceThresholdCeiling` (default 50,000,
`src/chunk-r1dvrqha.js:24`; Edit, Write, Agent, Glob and WebFetch persist at that); a positive
`tengu_velvet_ibis` entry replaces it, except on tools outside the aggregate budget
(`src/chunk-z0mss2jj.js:34-40`).

| Tool | Cap | Over it |
| --- | --- | --- |
| Read | 256 KiB on the file (`src/chunk-13nwb0xt.js:209`), 25,000 output tokens (`src/chunk-9r0d28dm.js:16`; `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS`, any positive value); 128 MiB on an image source (`src/chunk-frrn501g.js:1539`) | A whole-file read (no `offset`, `limit` or `pages`) over the token cap returns its first page, `truncatedByTokenCap: true`; a ranged one throws `MaxFileReadTokenExceededError`. A ranged read over 128 bytes per allowed token throws without an API call (`src/chunk-j0tbz6ra.js:130820-130821`). `File is too large to read as an image` |
| Read `allow_large` | `floor((threshold − used) × 0.7)` tokens, bytes `max(256 KiB, that × bytes-per-token × 3)` (`src/chunk-j0tbz6ra.js:130743-130769`); `threshold` is the autocompact threshold (`src/chunk-tqjdehqd.js:1802`), `used` the session so far plus this turn's earlier `allow_large` reads | Raised only past 25,000 tokens; absent without a context room, on a remote call or for another machine's input: ` is not available where this read runs` |
| Bash | 30,000 chars inline, moved by settings `bashOutputMaxChars` (clamped to 4,000–128,000); env `BASH_MAX_OUTPUT_LENGTH` (at most 150,000; the setting wins) sizes only the read-back window (`src/chunk-j9t13sne.js:27-40`); 2²⁵ chars in the stream accumulator (`src/chunk-a16y5hcz.js:176`) | Head truncation keeping the beginning, `... [N lines truncated] ...`, then persistence. The accumulator end-truncates: `... [output truncated - NKB removed]` |
| Grep | 250 entries by default, `head_limit: 0` for none (`src/chunk-j0tbz6ra.js:60121`); persist at 20,000 chars (`:60160`) | `[Showing results with pagination = limit: N, offset: M]`; a content line over 500 chars becomes `[Omitted long matching line]` |
| Glob | 100 files (`src/chunk-j0tbz6ra.js:60032`) | `truncated: true` and a note naming the total when it is known (`:59894-59902`) |
| Edit | 1 GiB editable file size (`src/chunk-j0tbz6ra.js:190548`) | `File is too large to edit`, before any read |
| WebFetch | 1 MiB of HTML before conversion (`src/chunk-j0tbz6ra.js:96934`), 100,000 chars of markdown from `offset` (`src/chunk-j9t13sne.js:506`); outside the aggregate budget (`src/chunk-j0tbz6ra.js:97508-97509`) | `[Content truncated due to length...]`, then `the final N were not read … call WebFetch again with the same url and offset: M` |
| MCP tool | 4,096 chars per tool description and server instruction block, 16,384 for a description loaded by tool search, `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` moving both (`src/chunk-stzrz9z3.js:16-17`); none for Anthropic's first-party servers (`src/chunk-sjfeq9t7.js:14`) | Truncated |

`taskOutputMaxChars` and `TASK_MAX_OUTPUT_LENGTH` are **inert**: `TaskOutput` is gone, a task's
output file being read with `Read` (`src/chunk-5rw2zfa0.js:4622`).

## Session-wide caps

| Constant | Value | What it bounds |
| --- | --- | --- |
| `src/chunk-r1dvrqha.js:30` | 400,000 bytes | One tool result where no threshold applies: 100,000 tokens at 4 bytes |
| `src/chunk-r1dvrqha.js:31` | 200,000 chars | All tool results in one message; the largest blocks persist first until under it (`src/chunk-z0mss2jj.js:436-458`) |
| `src/chunk-r1dvrqha.js:33` | 1 GiB | A persisted tool result on disk |
| `src/chunk-m5rm7nsm.js:58` | 5 GiB | One background task's output file; past it the file carries `[output truncated: exceeded 5GB disk cap]` |
| `src/chunk-m5rm7nsm.js:60` | 64 MiB | A persisted output's own byte limit, under which the saved file may end mid-structure |

# Tool Token Limits and Truncation Behavior

Source: `/home/chenxy/repos/claude-code-src/` (Claude Code source)

## Token Counting Mechanism

Claude Code uses a **two-tier hybrid approach** — no local tokenizer (no tiktoken):

1. **Primary: Anthropic API `countTokens` endpoint** — calls `anthropic.beta.messages.countTokens()`
2. **Fallback: Character-based estimation** — `roughTokenCountEstimationForFileType()`:
   - Default: **4 characters per token**
   - JSON/JSONL/JSONC: **2 characters per token** (denser due to structural punctuation)

Key file: `src/services/tokenEstimation.ts`

---

## Per-Tool Limits

### Read Tool

| Limit | Default | Gate | On Overflow |
|-------|---------|------|-------------|
| maxSizeBytes | 256 KB | total file size (stat, pre-read) | throws error |
| maxTokens | 25,000 | output content tokens (post-read) | throws error |

**Token validation logic** (`src/tools/FileReadTool/FileReadTool.ts`):
1. Estimate tokens via character ratio
2. If estimate <= 25% of limit → pass immediately (no API call)
3. If estimate > 25% → call `countTokensWithAPI()` for precise count
4. If over limit → throw `MaxFileReadTokenExceededError`

**Does NOT truncate.** Throws an error; user must use `offset`/`limit` params. Rationale: error is ~100 bytes vs ~25K tokens of truncated content.

Env var: `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS`

### Bash Tool

| Layer | Limit | Type | Message |
|-------|-------|------|---------|
| Stream accumulator | 2^25 chars (~33.5 MB) | end truncation | `... [output truncated - ${KB}KB removed]` |
| Output formatting | 30,000 chars (default) | head truncation (keeps beginning) | `... [${N} lines truncated] ...` |
| Tool result persistence | 30,000 chars | persists to disk | model gets preview + file path |

Configurable: `BASH_MAX_OUTPUT_LENGTH` env var (range: 30,000–150,000 chars)

Key files: `src/utils/shell/outputLimits.ts`, `src/tools/BashTool/utils.ts`

### Grep Tool

- **Default head_limit:** 250 results (when unspecified)
- **Persist threshold:** 20,000 characters
- **Truncation message:** `[Showing results with pagination = limit: {N}, offset: {M}]`
- Supports pagination via `offset` parameter
- Pass `head_limit=0` for unlimited (not recommended)

### Glob Tool

- **Default file limit:** 100 files
- **Persist threshold:** 100,000 characters
- **Truncation message:** `(Results are truncated. Consider using a more specific path or pattern.)`
- Returns `truncated: boolean` in output

### Edit Tool

- **MAX_EDIT_FILE_SIZE:** 1 GiB (V8/Bun string length limit guard)
- **Persist threshold:** 100,000 characters
- Throws error pre-validation if file too large

### Write Tool

- **Persist threshold:** 100,000 characters
- No explicit file size limit for writing

### WebFetch Tool

- **MAX_MARKDOWN_LENGTH:** 100,000 characters
- **Truncation message:** `[Content truncated due to length...]`

### Agent Tool

- **Persist threshold:** 100,000 characters
- No explicit per-agent token budget; managed at session level

---

## System-Wide Limits

From `src/constants/toolLimits.ts`:

| Constant | Value | Purpose |
|----------|-------|---------|
| DEFAULT_MAX_RESULT_SIZE_CHARS | 50,000 | Per-tool default before persistence |
| MAX_TOOL_RESULT_TOKENS | 100,000 | Absolute cap per tool result |
| MAX_TOOL_RESULT_BYTES | 400,000 | Derived from token limit (4 bytes/token) |
| MAX_TOOL_RESULTS_PER_MESSAGE_CHARS | 200,000 | Aggregate across all tool results in one turn |

When a tool result exceeds its `maxResultSizeChars`, it is persisted to disk and the model receives a preview with the file path. When aggregate results in one message exceed 200K chars, largest blocks are persisted first until under budget.

---

## Truncation Communication Patterns

| Tool | Strategy | Model sees |
|------|----------|-----------|
| Read | Error (no truncation) | Error message with token count and limit |
| Bash | Head truncation + persistence | Truncated output or preview + disk path |
| Grep | Pagination | Truncation note + `offset`/`limit` for next page |
| Glob | Truncation flag | Warning message suggesting narrower pattern |
| WebFetch | Tail truncation | `[Content truncated due to length...]` |
| Edit | Error (pre-validation) | Error with file size info |

---

## Environment Variables

| Env Var | Tool | Default | Max |
|---------|------|---------|-----|
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` | Read | 25,000 | — |
| `BASH_MAX_OUTPUT_LENGTH` | Bash | 30,000 | 150,000 |
| `BASH_MAX_TIMEOUT_MS` | Bash | 10 min | — |

---

## Key Source Files

- `src/services/tokenEstimation.ts` — token counting (API + estimation)
- `src/tools/FileReadTool/limits.ts` — Read tool limit config
- `src/tools/FileReadTool/FileReadTool.ts` — Read tool enforcement
- `src/tools/BashTool/utils.ts` — Bash output formatting/truncation
- `src/utils/shell/outputLimits.ts` — Bash output limit constants
- `src/utils/stringUtils.ts` — `EndTruncatingAccumulator` class
- `src/constants/toolLimits.ts` — system-wide tool result limits
- `src/tools/GrepTool/GrepTool.ts` — Grep pagination logic
- `src/tools/GlobTool/GlobTool.ts` — Glob truncation logic

---
name: session-timeline
description: use only if invoked by user or workflow
---

# Session Timeline

Convert one or more logged agent sessions into a **focus-directed timeline
artifact** — a compressed, factual description of the log content relevant to a
stated focus. The artifact is raw evidence for later interpretive work.

Scales from one session to a whole hierarchy (main + subagent invocations).
Extractor decides workflow and report organization; skill just constrains via
invariants.

## Invariants

1. **One focus per artifact.** Focus is one natural-language sentence stated at
   the top. Same log may produce multiple artifacts under different foci.
2. **Facts only, and prefer positive over negative descriptions.** Describe
   what each part IS ("agent reads `ep_check.py`; grep for `unsupported`") or
   what it programmatically ISN'T via a concrete regex-negative ("no match for
   `/codex-based|opencode-based|superseded/`"). Do not classify relevance
   ("unrelated to focus"), do not claim causation ("informed the rewrite"), do
   not draw conclusions ("suggests", "indicates", "confirms", "load-bearing",
   "critical"). Reader traces relevance and causation from the recorded events.

   **The "not X" trap.** Phrases like *"not a read of the focus path"* or
   *"not new reads of /X/"* look factual because they're negations, but they
   inherit the relevance classification from the focus. If you're tempted to
   write "not Y" where Y names focus-relevance, either (a) drop the negation
   and describe positively what the payload IS ("this is the content of
   `prompt-tests/CLAUDE.md` displayed as a sed tool_result; the string
   `/X/prompt-tests/...` appears inside the file's own text"), or (b) replace
   with a concrete programmatic regex-negative ("no match for
   `/^  filePath: X/` in this turn's tool_use payloads"). A regex-negative is
   a fact anyone can rerun; a relevance-negative is a judgment.
3. **Complete coverage.** Every span of every session appears in the artifact.
   A span may be rendered at any precision — verbatim quote, short description,
   regex-negative note, or `<N turns, brief factual descriptor>` range marker —
   but nothing is silently dropped.
4. **Precision decreases with distance from the focus.** Extractor decides
   where cutoffs land. Rough guide: verbatim for text a downstream reader might
   cite as evidence; short description for causally adjacent spans; range
   markers + regex-negatives for distant spans.
5. **Much smaller than the raw log** while minimizing information loss relative
   to the focus.

## Extractor judgment

The following are the extractor's calls — not prescribed:

- **Workflow.** How to work through the log(s). Iterative skeleton → drill-in
  scales well; all-at-once flooding context does not.
- **Report organization.** Chronological within one session, hierarchical for
  main+subagent, per-session-then-cross-cutting for many sessions — pick what
  minimizes information loss for the focus.
- **What counts as the focus's causal chain.** Depends on focus. For an
  event-based focus, this includes what triggered each event and what consumed
  its output. For a linguistic-pattern focus, it includes what precedes and
  follows each match.
- **Cutoff for backward / forward tracing.** Stop when the edge stops being
  informative about the focus. Reader can request more if a gap matters.

## Provenance requirements

At the top of the artifact, list — per session included:

- Session ID (or path to log)
- Model + variant + any settings that affect output (verbosity, reasoning effort)
- Working directory
- Fixture state (repo + HEAD + any anomalies)
- Task input (path + relevant content flags)
- Agent prompt source
- Harness / build version
- Extraction command(s) used
- Extractor context (subagent prompt or one-liner brief)

For multi-session artifacts, note the relationship (main dispatches subagent A
at @L14; subagent A's session is inlined below / linked at `<path>`).

## Anti-patterns

- Classification words: `unrelated to focus`, `relevant`, `load-bearing`,
  `critical`, `important`. Rewrite as description or regex-negative.
- Interpretive verbs in prose: `suggests`, `indicates`, `confirms`, `informs`,
  `bypasses`, `demonstrates`. Interpretation is not the timeline's job.
- Summary / synthesis sections that narrate the causal chain across events.
  The reader traces from the events. Bare enumeration of focus-matching events
  is fine; narrative summarizing what caused what is not.
- Fixture files that may be truncated relative to the live log. Prefer live
  session as source of truth.
- Copy-pasted large tool outputs. Include only bytes referenced downstream (in
  reasoning or subsequent artifacts) or that a reader might cite; note the
  omission with a positive descriptor and/or a regex-negative.

## Harness-specific rendering

Add a new subsection per harness as needed. Only opencode is documented today.

### opencode

Two-tool workflow:

- **Skeleton via `opencode-pretty`** for structural summary. Small and
  greppable.
- **Detailed access via `jq` on the exported JSON** at specific `@L<n>[i]`
  refs picked from the skeleton. Do NOT render a full high-precision pretty
  file — it's an intermediate substrate you don't need. Anchor windows are
  typically discontinuous; jq per-part access is cheaper and cleaner.

**Skeleton**:

```bash
agent-tools opencode-pretty <session-id> --chat-only --tool-max 200 --no-thinking > /tmp/skel-<id>.txt
```

`--chat-only` drops tool_result bodies (keeps tool_use headers), `--tool-max 200`
caps tool_use inputs, `--no-thinking` omits reasoning.

**Export for jq**:

```bash
opencode export <session-id> > /tmp/sess-<id>.json
```

**Note on `opencode export` output**: the file begins with a status line like
`Exporting session: <id>` before the JSON body. Strip it with
`tail -n +2 /tmp/sess-<id>.json > /tmp/sess-<id>-clean.json` (or
`sed -i '1d'`) before jq'ing. The redirect to file is required — `opencode
export | jq` truncates at ~64KB.

**Reference convention**: `@L<n>[i]` where `n` is 1-based message index and
`i` is 0-based part index. Map to jq: `.messages[<n-1>].parts[<i>]`. Refs are
stable across pretty-print pagination.

**Exported JSON schema** (top-level `{info, messages[]}`):

- `.info` — session metadata: `id`, `slug`, `projectID`, `directory` (cwd),
  `title`, `agent`, `model.{id,providerID,variant}`, `version`, `cost`,
  `tokens.{total,input,output,reasoning}`, `time`, `permission`, `summary`.
- `.messages[n]` — one entry per message (1-based `@L<n>` = `.messages[n-1]`).
  Contains `.info` (per-message metadata) and `.parts[]`.
- `.messages[n].info` — for assistant messages: `role`, `mode`, `agent`,
  `modelID`, `providerID`, `path.{cwd,root}`, `parentID`, `cost`,
  `tokens.{total,input,output,reasoning,cache.{write,read}}`, `finish`, `time`.
  For user messages: `role: "user"`, `time`.
- `.messages[n].parts[i]` — one entry per part (0-based `@L<n>[i]` =
  `.messages[n-1].parts[i]`). Each has `.type` ∈ {`reasoning`, `text`,
  `tool`, `patch`, `step-start`, `step-finish`}, `.id`, `.messageID`,
  `.sessionID`.

Per-type payload keys:

- `reasoning` — `.text` (verbatim reasoning content), `.time.{start,end}`
- `text` — `.text` (verbatim assistant text; the `.metadata.openai.phase`
  field distinguishes `commentary` vs `final_answer` on some models)
- `tool` — `.tool` (name: bash/read/edit/write/apply_patch/grep/glob/...),
  `.callID`, `.state.{status,input,output,metadata,time,title}`. `.state.input`
  is the tool call arguments (an object; e.g., bash has `command` +
  `description`, read has `filePath` + optional `offset`/`limit`); `.state.output`
  is the tool result (text).
- `patch` — file-mutation records (rare; used by apply_patch)
- `step-start` / `step-finish` — turn boundaries; `step-finish.tokens` gives
  per-step reasoning/output counts (load-bearing for **F62 token counts**).

**Common jq queries**:

```bash
# Full part at @L5[3]
jq '.messages[4].parts[3]' /tmp/sess-<id>-clean.json

# Just the reasoning text at @L8
jq '.messages[7].parts[] | select(.type=="reasoning") | .text' /tmp/sess-<id>-clean.json

# Every tool call in message @L5 with input
jq '.messages[4].parts[] | select(.type=="tool") | {tool, input: .state.input}' /tmp/sess-<id>-clean.json

# Every tool_use path across the session that matches a regex
jq -r '.messages[] | .parts[] | select(.type=="tool") | .state.input | (.filePath // .command // empty)' /tmp/sess-<id>-clean.json | grep -nE '/root/claude-config-work[^-]'

# Reasoning token count per assistant turn (for F62 heading-only handling)
jq '.messages[] | select(.info.role=="assistant") | {id: .info.id, reasoning_tokens: .info.tokens.reasoning}' /tmp/sess-<id>-clean.json
```

**DB location**: `~/.local/share/opencode/opencode.db` for latest/beta/prod
channels; `~/.local/share/opencode/opencode-${channel}.db` otherwise (e.g.,
`opencode-local.db` for bun-source runs). To force main DB:
`OPENCODE_DB=/root/.local/share/opencode/opencode.db`.

**Channels within a message**:
- `reasoning` — thinking blocks
- `preamble` / commentary — assistant text preceding a tool_use
- `text` — assistant text at message end (final channel)
- `tool_use` — tool call (name + input)
- `tool_result` — tool output (usually rendered with the tool_use)

Preamble may not describe all tools in a parallel-batch turn; when it doesn't,
note the payload contents of each `tool_use` factually.

**F62 (Codex OAuth reasoning-summary truncation)**: on `openai/gpt-5.5` via
ChatGPT Codex OAuth, `reasoning_summary_text.done` returns bolded headings only
(~40 chars) instead of paragraphs. Record what IS visible: heading verbatim
prefixed `[F62-heading]`, reasoning token count (from `step_finish.tokens.reasoning`),
preamble/commentary text verbatim, subsequent tool_use payloads. Do not
reconstruct paragraph content that isn't emitted.

**Compound bash** (`ls X; cat Y; git ...`): keep as one `tool_use` entry;
describe each subcommand's target so the reader can see the intent split.

**Metadata-only reads under a focus path** (`cat X/.git` returning a gitdir
pointer, `stat`, `ls -la`): include with payload precision that shows it's
metadata not content ("returns 12-byte gitdir string", "returns file listing of
8 items"). Focus predicate is path-based unless the focus statement says
otherwise.

## Output location and naming

Default: `<caller-specified-dir>/<top-slug>__<focus-slug>.md`.

For batch use in this repo: `notes/compliance-check-failure-mode/experiments/`.
Top-slug is a short human name for the session or session-hierarchy
(`kimi-no2-broken`, `dispatch-3-main-plus-subagents`); focus-slug is 2–4
dash-separated words (`old-worktree-reads`, `hedge-language-usage`).

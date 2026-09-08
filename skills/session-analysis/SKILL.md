---
name: session-analysis
description: Use when reading or analyzing a logged agent session — a Claude Code JSONL transcript or an opencode export — to answer any question about what an agent did: grading a prompt-test run, diagnosing a session's behavior, reconstructing what happened. Carries the skeleton-first reading protocol that keeps a large log out of your context, the evidence-artifact format, and how to phrase a focus. Load before running `agent-tools cc-pretty` or `agent-tools opencode-pretty` on a session, and before dispatching a `session-analysis` subagent.
---

# Session Analysis

Analyze one or more logged agent sessions — opencode exports or Claude Code
JSONL — through a shared skeleton-first reading protocol. Two modes:
**task** (use the log(s) to do something or answer a question) and
**evidence** (extract what may be relevant into a facts-only artifact).

## Invocation

Invoke this skill in **subagents** — plural. Do not throw a complex focus
+ multiple logs into one call. Split by aspect (recommended: simple
question first, then drill, one subagent per aspect) or by log. Each
invocation carries a different focus and may cover only _parts of logs_.
All remaining reasoning text eventually gets read by some subagent with an
appropriate focus to confirm it is not relevant — do this pass last.

Exception (whole-session case): if the entire caller session is itself a
session-analysis run and no other context needs protecting, running
inline is fine.

## Modes

Two invocation modes. State `mode:` in the invocation brief; a direct
invocation with no `mode:` runs task mode. Both modes share one default
task, used whenever no task or focus is given:

> **What happened in this session — highlight anything noteworthy,
> unexpected, or requiring investigation.**

### task mode

Default for direct invocation. Use the log(s) to perform a task — answer a
question or do something.

- Input: session ID(s) + optional task + optional `artifact: required|skip`.
- Produces: the answer/result in the response prose. When `artifact:
  required` (the default when unstated): also an evidence artifact (same
  file, format, and invariants as evidence mode; focus = the task).
- Response shape: `{ answer_prose, evidence_path? }`.

`artifact: skip` is for terminal one-off tasks. The artifact costs ≈ +25–35%
over answer-only and pays for itself the first time a follow-up reuses it;
the artifact stays pure (facts only) — the answer lives in the response — so
it remains reusable substrate for later interpretive rounds.

### evidence mode

Required when a parent dispatches this skill via a subagent.

- Input: session ID(s) + a description of what's important — a focus, a
  question the parent will answer later, or an evaluation criterion. When
  omitted, the shared default task is the focus. The output is a factual log
  regardless of how the request is phrased.
- Produces: an evidence artifact only.
- Response shape: `{ evidence_path, one-paragraph summary of contents }`.
- Gathering discipline: gather anything that MIGHT be relevant to the
  description. When in doubt, include (summarized). No interpretive answer.

## For parents dispatching this skill

Before dispatching, read this SKILL.md so you know what the artifact
contains, what invariants apply, and how to phrase the focus.

Brief format:

- `mode: evidence` (required — parents MUST use evidence mode; for
  grading/audits see "Focused audits" below)
- session ID(s)
- focus / description of what matters

The subagent returns `{ evidence_path, one-paragraph summary }`. Read the
artifact and synthesize across artifacts in your own turn. Synthesis is not
persisted by this skill.

## Reading protocol

All modes read the log the same way. Never render a full high-precision
pretty file as reading substrate.

1. **Skeleton.** Run the skeleton command and read it fully:
   - opencode: `agent-tools opencode-pretty <session-id> --skeleton`
     (add `--from-file <export.json>` when a saved export already exists —
     hints then reference that file)
   - Claude Code: `agent-tools cc-pretty <file.jsonl> --skeleton`

   One line per content block: `@L<n>[i]` ref, type, approx size
   (`~tok` ≈ chars/4), the jq leaf, and a short preview.
2. **Hidden regions.** `⟐ compacted` / `⟲ rewind` skeleton lines mark
   content the default selection hides; each carries its `reveal:` flag. If
   the focus may touch hidden content, re-run the skeleton with that flag —
   refs stay identical. Harness asymmetry: a cc JSONL contains every line
   (sed/jq bypass all hiding); an opencode export contains all compaction
   legs but only uncleaned rewind tails (opencode deletes abandoned tails on
   the next prompt).
3. **Plan questions, not reads.** From the skeleton: what is this session
   about? What questions matter for it? What would count as
   noteworthy/unexpected/worth investigating in this context? Write the
   questions down, then derive extraction rounds from them. Do NOT
   pre-enumerate the read queue — a plan phrased as reads anchors you to it;
   a plan phrased as questions keeps the investigation adaptive. **Report
   plan drift**: questions added or dropped as the investigation proceeds are
   themselves noteworthy — state them in your output.
4. **Extract one round with one command** naming exactly those refs:
   - opencode: `opencode export <id> > /tmp/oc-<id>.json` once, then per
     round `jq '.messages[9:25]' /tmp/oc-<id>.json` for a message range
     (0-based slice: `.messages[a:b]` covers refs `@L(a+1)`..`@Lb`), or
     `jq -r '.messages[<n-1>].parts[<i>]<leaf>' /tmp/oc-<id>.json` for one
     block. Never pipe `opencode export` into jq directly — stdout truncates
     at ~64KB on a pipe; redirect to a file first. Paste-ready helpers:
     ```bash
     OC=/tmp/oc-<id>.json
     ocr() { jq -r ".messages[$(($1-1))].parts[$2]$3" "$OC"; }  # ocr 12 3 .state.output → @L12[3] leaf
     ocrange() { jq ".messages[$(($1-1)):$2]" "$OC"; }          # ocrange 10 25 → refs @L10..@L25
     ```
   - cc: `sed -n '10,25p' <file>.jsonl` for a line range, or
     `sed -n '<n>p' <file>.jsonl | jq -r '.message.content[<i>]<leaf>'` for
     one block (user inputs: `jq -r '.message.content'`; attachments:
     `jq -r '.attachment.content'`).
5. **Assess between rounds.** A round may be one batch or a planned queue of
   batches. After each round: what did it surface? What does it redirect?
   Then plan the next round.
6. **Coverage sweep + manifest.** Required reading: every reasoning block,
   every text block, every tool input. Before finishing, produce the
   manifest: block counts by type vs. what you extracted, with a one-line
   reason for every unextracted required block:
   ```bash
   jq '[.messages[].parts[] | .type] | group_by(.) | map({(.[0]): length}) | add' "$OC"
   ```
   Tool OUTPUT is optional — except (a) when a later reasoning/text block
   references it: go back and read/explore/understand the referenced part;
   and (b) the large-output rule below.
7. **Large-output rule.** A tool output above ~2k~tok (size column) must not
   be consumed only via the session-agent's own summary or quote — at
   minimum, skim it structurally (head/tail or a targeted grep). The
   session-agent's summary of a large output is evidence *about* the output,
   not the output itself.
8. **Self-report sections.** If the session contains self-report sections
   (e.g. "Required notes"), verify every claim about what was or was not
   reported against the actual section text before making it.
9. **Workflow completion.** If the session invoked multi-step workflows
   (skills with numbered steps/phases), check whether the later steps ran,
   keyed to the workflow's own directives as visible in the log. Not all
   workflows use explicit markers; a workflow can drop steps without leaving
   a marker-shaped trace.
10. **Telemetry.** Process claims (commands run, blocks read, coverage) must
    come from the actual command history, not estimates.

## Harness notes

### opencode

**Note on `opencode export` output**: `opencode export` prints
`Exporting session: <id>` to **stderr** and pure JSON to stdout, so a plain
`> file` redirect gives a clean JSON file — do NOT `tail -n +2` it (that
strips the opening `{`). Only strip if you used `2>&1` and merged stderr in.

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
jq '.messages[4].parts[3]' /tmp/oc-<id>.json

# Just the reasoning text at @L8
jq '.messages[7].parts[] | select(.type=="reasoning") | .text' /tmp/oc-<id>.json

# Every tool call in message @L5 with input
jq '.messages[4].parts[] | select(.type=="tool") | {tool, input: .state.input}' /tmp/oc-<id>.json

# Every tool_use path across the session that matches a regex
jq -r '.messages[] | .parts[] | select(.type=="tool") | .state.input | (.filePath // .command // empty)' /tmp/oc-<id>.json | grep -nE '<focus-regex>'

# Reasoning token count per assistant turn (for F62 heading-only handling)
jq '.messages[] | select(.info.role=="assistant") | {id: .info.id, reasoning_tokens: .info.tokens.reasoning}' /tmp/oc-<id>.json
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

In export terms: a rendered `tool_use`/`◀ result` pair is one `tool` part's
`.state.input`/`.state.output`; preamble is a `text` part before the tool
part.

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

### claude-code

One JSONL line per record. `@L<n>[i]` = line `n`, `.message.content[i]`.
Tool calls sit on assistant lines (`.message.content[i].input`); results sit
on the following user line (`.message.content[i].content`). Thinking blocks:
`.message.content[i].thinking`. User string input: `.message.content` (no
index). Hook/attachment records: `.attachment.content`. Rewound lines and
pre-compaction legs stay in the file — sed/jq extraction bypasses all
pretty-side hiding.

## Mode: evidence

### Invariants

1. **One focus per artifact.** Focus is one natural-language sentence stated at
   the top. Same log may produce multiple artifacts under different foci.
2. **Facts only, prefer positive descriptions.** Describe what each part
   IS ("agent reads `<file>`; grep for `<token>` across `<dir>`"). Do not
   classify relevance ("unrelated to focus"), claim causation ("informed
   the rewrite"), or draw conclusions ("suggests", "indicates",
   "confirms", "load-bearing", "critical"). Reader traces relevance and
   causation from recorded events.

   **Tool in/out:** a concrete regex-negative is admissible ("no match
   for `/<regex>/`") — a fact anyone can rerun. Relevance-negatives ("not
   a read of the focus path") inherit their category from the focus;
   rewrite as positive description or regex-negative.

   **Reasoning blocks:** regex is sanity-check / overview only, not
   admissible as evidence — agents use their own semantic labels for
   things. Summarize positively; do not write negatives about reasoning.
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

### Extractor judgment

The following are the extractor's calls — not prescribed:

- **Workflow.** How to work through the log(s). Follow the Reading protocol
  above.
- **Report organization.** Chronological within one session, hierarchical for
  main+subagent, per-session-then-cross-cutting for many sessions — pick what
  minimizes information loss for the focus.
- **What counts as the focus's causal chain.** Depends on focus. For an
  event-based focus, this includes what triggered each event and what consumed
  its output. For a linguistic-pattern focus, it includes what precedes and
  follows each match.
- **Cutoff for backward / forward tracing.** Stop when the edge stops being
  informative about the focus. Reader can request more if a gap matters.

### Provenance requirements

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

### Anti-patterns

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

### Output location and naming

Default: `<caller-specified-dir>/<top-slug>__<focus-slug>.md`.

For batch use in this repo: `notes/compliance-check-failure-mode/experiments/`.
Top-slug is a short human name for the session or session-hierarchy (model +
variant + condition tag, or `dispatch-N-main-plus-subagents` for hierarchies);
focus-slug is 2–4 dash-separated words naming the focus. Example filenames:
`gpt55-xhigh-baseline__prompt-md-rewrite.md`,
`dispatch-3-main-plus-subagents__crossing-motivation.md`.

## Focused audits (grading, compliance checks)

For audits that need a verdict or causal attribution — prompt-tests grading,
workflow reviews — dispatch evidence mode with the audit criteria as the
focus, then synthesize the causal story from the artifact in your own turn.
Do not use fixed findings-category checklists for this: they produce
category-shaped items rather than causal attribution — findings get inflated
to fit the list while the actual reason things happened may not fit any
category. Verdicts cite artifact evidence and name the causal chain
explicitly.

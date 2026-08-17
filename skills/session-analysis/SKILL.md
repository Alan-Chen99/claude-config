---
name: session-analysis
description: use only if invoked by user or workflow
---

# Session Analysis

Analyze one or more logged agent sessions — opencode exports or Claude Code
JSONL — through a shared skeleton-first reading protocol. Three modes:
**evidence** (a focus-directed raw-evidence artifact, facts only),
**question** (evidence artifact + a synthesized answer in the response), and
**diagnose** (a findings report surfacing items the agent did not
self-report).

## Invocation

Invoke this skill in a **subagent** unless the entire caller session is
itself a session-analysis run (e.g., a top-level user request that is only
"produce a session-analysis artifact for X"). Building an artifact requires
reading skeleton dumps, jq outputs, greps, and reasoning-block extractions
that routinely reach tens of thousands of tokens of intermediate context —
none of which the caller needs after the artifact is written. A subagent
isolates that context; the caller receives the artifact path and a short
summary.

Exception (whole-session case): if no other work is happening in the
caller's context, running the skill inline is fine — there is no context to
protect.

## Modes

Three invocation modes. The `mode:` should be stated in the invocation brief;
if omitted on a direct user invocation, question mode is the default. Parents
dispatching a subagent **for an evidence artifact** must state `mode: evidence`
— see "For parents" below.

### question mode

Default for direct user invocation.

- Input: session ID(s) + optional question.
- Default question if omitted: *"What happened in this session — highlight
  anything noteworthy, unexpected, or requiring investigation."*
- Produces:
  1. An evidence artifact (same file, format, and invariants as evidence mode;
     focus = the question).
  2. A synthesized answer to the question, returned in the response prose.
- Response shape: `{ answer_prose, evidence_path }`.

The evidence artifact stays pure (facts only) — the answer lives in the
response, not in the artifact — so the artifact remains reusable substrate
for later interpretive rounds.

### evidence mode

Required when a parent dispatches this skill via a subagent.

- Input: session ID(s) + a description of what's important. The description
  can be phrased as a focus, a question the parent will answer later, or an
  evaluation criterion. The output is a factual log regardless of how the
  request is phrased.
- Produces: an evidence artifact only.
- Response shape: `{ evidence_path, one-paragraph summary of contents }`.
- Gathering discipline: gather anything that MIGHT be relevant to the
  description. When in doubt, include (summarized). No interpretive answer.

### diagnose mode

- Input: log path (`*.jsonl`), opencode session id, or saved export
  (`*.json` via `--from-file`).
- Produces: a findings report (see "Mode: diagnose" below), returned in the
  response prose.
- Response shape: `{ report_prose }`.
- Must be named explicitly (`mode: diagnose` or "diagnose this session").

## For parents dispatching this skill

Before dispatching, read this SKILL.md so you know what the artifact
contains, what invariants apply, and how to phrase the focus.

Brief format:

- `mode: evidence` (required for evidence-artifact dispatch; diagnose mode is run by the analysis owner, e.g. a grader subagent — not governed by this section)
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
3. **Plan batches.** Group adjacent blocks totaling ≤ ~10k tokens (size
   column). Key blocks may be read out of order first (e.g. a
   known-decisive reasoning block).
4. **Extract one batch with one command** naming exactly those refs:
   - opencode: `opencode export <id> > /tmp/oc-<id>.json` once, then
     `jq '.messages[9:25]' /tmp/oc-<id>.json` for a message range (0-based
     slice: `.messages[a:b]` covers refs `@L(a+1)`..`@Lb`), or
     `jq -r '.messages[<n-1>].parts[<i>]<leaf>' /tmp/oc-<id>.json` for one
     block. Never pipe `opencode export` into jq directly — stdout truncates
     at ~64KB on a pipe; redirect to a file first.
   - cc: `sed -n '10,25p' <file>.jsonl` for a line range, or
     `sed -n '<n>p' <file>.jsonl | jq -r '.message.content[<i>]<leaf>'` for
     one block (user inputs: `jq -r '.message.content'`; attachments:
     `jq -r '.attachment.content'`).
5. **Think before fetching more.** Assess the batch's relevance to the
   focus/question/findings, then plan the next batch.
6. **Coverage sweep.** End with all blocks read. Required: every reasoning
   block, every text block, every tool input. Tool OUTPUT is optional —
   except when a later reasoning/text block references it: then go back and
   read/explore/understand the referenced part.

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
2. **Facts only, and prefer positive over negative descriptions.** Describe
   what each part IS ("agent reads `<file>`; grep for `<token>` across
   `<dir>`") or what it programmatically ISN'T via a concrete regex-negative
   ("no match for `/<regex>/`"). Do not classify relevance ("unrelated to
   focus"), do not claim causation ("informed the rewrite"), do not draw
   conclusions ("suggests", "indicates", "confirms", "load-bearing",
   "critical"). Reader traces relevance and causation from the recorded events.

   **The "not X" trap.** Phrases like *"not a read of the focus path"* or
   *"not new reads of /X/"* look factual because they're negations, but they
   inherit the relevance classification from the focus. If you're tempted to
   write "not Y" where Y names focus-relevance, either (a) drop the negation
   and describe positively what the payload IS ("this is the content of
   `<some-file>` displayed as a sed tool_result; the string `<focus-token>`
   appears inside the file's own text"), or (b) replace with a concrete
   programmatic regex-negative ("no match for `/^  filePath: <regex>/` in
   this turn's tool_use payloads"). A regex-negative is a fact anyone can
   rerun; a relevance-negative is a judgment.
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

## Mode: diagnose

Post-hoc analysis of an agent conversation log (opencode export or Claude
Code JSONL). Surfaces findings the agent may have missed in its
self-reporting (Required notes — the self-reporting sections in assistant
messages; see conventions/agent-responses.md).

Read the log via the Reading protocol above.

### Construct the timeline

Before scanning for findings, construct a **semantic timeline** of what the
agent was doing, in order. This is not a transcript of tool calls — it is the
narrative of the agent's actions and decisions.

Each line names what the agent was *doing*, not which syscall ran. "Reproduced
the failure" beats "ran `./export_catalog.py`". "Probed adjacent Python
version" beats "Bash uv run --python 3.13".

Cover: tool-call clusters that served one purpose, subagent dispatches, gate
drafts, error → retry cycles, file edits, and major reasoning turns visible
in thinking blocks.

Example:

```
- Read the failing fixture script.
- Ran the script with uv; reproduced TypeError on Python 3.14 / pydantic 2.12.5.
- Drafted gate (objectively-wrong / discriminating-check), self-critiqued.
- Probed adjacent Python version 3.13; same script ran clean.
- Searched pydantic issue tracker; found issue #12732 / PR #12733.
- Concluded root cause as runtime/library compatibility, not application code.
- Sent final answer.
```

The timeline goes at the top of the report (see "Produce the report" below),
after the Overview.

### Scan for findings

Scan the log for each category below. For every potential finding,
you MUST follow the evidence-first protocol:

**Evidence-first protocol:**
1. QUOTE the specific text from the log (tool output, error message, agent text)
2. CLASSIFY into exactly one category
3. EXPLAIN why this matters (one sentence)

#### Detection tiers

**HIGH detectability** — scan for these patterns systematically:

| Category | Detection signals |
|----------|------------------|
| **tool issue** | Tool outputs containing `✗`, non-zero exit codes, "error", "failed", "denied", "permission", capability errors. Also: tools that return unhelpful results forcing the agent to retry. |
| **context waste** | Repeated reads of the same file. Failed reads (file not found). Reading files then not using the content. Large tool outputs that didn't contribute to the result. |
| **corrected mistake** | Error→revision sequences: agent tries something, gets an error, then changes approach. Failed commands followed by different commands. Agent reverses a prior assessment or conclusion. |
| **workflow dropout** | Multi-step skill workflows (e.g., `/do` steps 1→2→3→4→5→6) where a later step was never invoked. Detection leans on the timeline (above) and on `NEXT STEP` directives visible in extracted skill-script text. Pattern: a skill-script step in the timeline whose `NEXT STEP` directive (visible in the extracted text) does not appear as a follow-up tool call later in the timeline. Always **significant** severity — the dropped steps are invisible to the user and typically contain quality gates or validation. |

**MEDIUM detectability** — look for these with evidence:

| Category | Detection signals |
|----------|------------------|
| **manual action needed** | Agent mentions something the user must do (install, configure, restart, approve). Check if it was surfaced in Required notes. |
| **instruction issue** | Agent references a file/instruction that doesn't exist. Conflicting instructions observed. Agent works around an instruction rather than following it. |
| **unexpected change** | Agent modifies files beyond what was asked. Scope creep visible in the diff or tool calls. Agent replaces something rather than augmenting it when augmentation was requested. |

**THINKING-BLOCK patterns** — scan reasoning/thinking blocks for these:

| Category | Detection signals |
|----------|------------------|
| **contradictory reasoning** | Agent's thinking contradicts its text output or tool results. Statements like "I already fixed this" when the fix hasn't been verified. Agent dismissing review findings without investigation. Thinking says one thing, output says another. **Exclusion:** An agent explicitly citing guidelines, protocol, or instructions to justify an action that differs from its internal assessment is protocol-compliance, NOT a contradiction (e.g., "I'd normally do X but the rules say Y so I'll do Y"). |
| **under-investigated critical issue** | Critical terms (segfault, crash, data loss, corruption, security vulnerability, race condition) mentioned in thinking but with minimal follow-up. The agent acknowledges a serious problem but doesn't investigate its scope, root cause, or downstream impact. A single mention of a critical term without evidence of investigation is a finding. |
| **unverified prior-iteration claim** | Agent references what a prior iteration did or didn't do without verifying the claim. Phrases like "prior iteration missed X", "this was already done", "the previous run handled this". These claims may be wrong and need cross-referencing against actual evidence. |
| **dismissed concern** | Agent notices something concerning in thinking but doesn't surface it in output or Required notes. The thinking block reveals awareness of a problem that the user never sees. |

**LOW detectability** — report only with strong textual evidence:

| Category | Detection signals |
|----------|------------------|
| **suspected user mistake** | Agent notices something wrong with user's input/files but doesn't flag it. Agent fixes a user error silently. User's next message confirms something the agent should have caught. |
| **hidden challenge** | Non-obvious problems the agent solved that weren't apparent from the initial request. These are hard to detect externally — only report if the log clearly shows the agent discovering and solving an unexpected problem. |

### Check existing Required notes (workspace conversations only)

If the conversation contains "Required notes" sections in assistant messages:
1. List what was self-reported
2. Compare against your findings
3. Flag items that were reported under the wrong category (miscategorization)

If no Required notes exist (non-workspace conversation), skip this step and
note that self-reporting was not active for this conversation.

### Produce the report

Format findings as:

```
## Session Diagnosis: <session-id>

### Overview
<1-2 sentences: what the conversation was about, how many turns>

### Timeline
<semantic chronological list per "Construct the timeline" above>

### Findings

#### <category>
> <quoted evidence from log>

<explanation — one sentence>
<severity: minor | notable | significant>

[repeat for each finding]

### Self-Reporting Comparison (workspace only)
- Self-reported: <count> items
- Diagnosed: <count> items
- Overlap: <count>
- Missed by self-reporting: <list>
- Miscategorized: <list>
- False positives in self-reporting: <list>

### Thinking-Block Findings
[Findings from thinking blocks get their own section because they represent
information the agent had but chose not to surface. These are often the most
important findings.]

### Summary
<2-3 sentences: overall quality assessment, most impactful missed items>
```

### Rules

1. **Read thinking blocks.** Every finding category that touches reasoning
   (contradictory reasoning, under-investigated critical issue, unverified
   prior-iteration claim, dismissed concern) MUST cite quoted text from a
   thinking block. Findings about agent behavior that ignore thinking-block
   evidence are incomplete.
2. Every finding MUST have a direct quote from the log. No finding without evidence.
3. Do NOT hallucinate findings. If the log is clean, say so — "No findings" is
   a valid and expected outcome for clean sessions. Do not manufacture findings
   to fill the report.
4. Severity guide:
   - **significant**: Would change what the user does next
   - **notable**: User should know but doesn't change immediate action
   - **minor**: Completeness item, low practical impact
5. When in doubt about a finding, include it with lower severity rather than omitting.
6. For corrected mistake: the agent fixing its own error is EXPECTED behavior.
   The finding is that it wasn't reported, not that the error occurred.
7. For suspected user mistake: be careful distinguishing "user made a mistake"
   from "user has a different intent than the agent assumed."
8. Context waste means the **agent** read or fetched irrelevant content. Token
   caching statistics, system-level overhead, and infrastructure details are NOT
   context waste — only agent-initiated reads/writes that didn't contribute to
   the result count.
9. Lead the Findings section with significant/notable items. Group minor items
   at the end under a "Minor" subheading so users see high-impact findings first.

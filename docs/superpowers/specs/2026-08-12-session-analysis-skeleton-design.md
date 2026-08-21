# session-analysis: skeleton-first reading protocol + merged skill design

> **Mode design superseded** by `2026-08-20-session-analysis-two-mode-revision-design.md`
> (two modes + shared default task; diagnose machinery deleted; grading re-pointed).
> The skeleton / flags / tooling sections below still stand.

## Context

Two session-log analysis skills exist:

- `skills/session-timeline/` — focus-directed extraction of opencode sessions
  into raw evidence artifacts (evidence/question modes).
- `skills/diagnose-session/` — post-hoc findings report over Claude Code
  JSONL or opencode sessions.

Both render logs with `cc-pretty` / `opencode-pretty`. Current pain points
(requirements from the user):

1. For any rendered piece (text, reasoning, tool input, tool output, …) it
   must be clear how to access the raw string as a path in the source log.
2. `session-timeline/SKILL.md` must document an actually useful command.
3. Accessing rewound branches or pre-compaction legs must deviate from the
   standard command, and how to do so must be clear — ideally via hints in
   the output itself.
4. Both skills get a skeleton-first workflow: subsequent analysis reads
   blocks directly via extraction commands naming exactly those blocks.
5. The skeleton must make blocks easy to extract, and be useful but small.
6. The `{opencode,cc}-pretty` flag spec must be simple: each flag does one
   distinct thing; the meaning of any flag set is predictable.
7. `diagnose-session` currently says "read all chunk files in parallel".
   Replace with: read skeleton → block paths visible → extract *adjacent
   batches* with one jq/sed+jq command (default batch ≈ 10k tokens) → assess
   relevance before the next batch → blocks may be read out of order (key
   blocks first) → finish with a coverage sweep of unread blocks. Required
   reading: all reasoning, text output, tool input. Tool output is optional
   UNLESS referenced later (in a thinking block or text) — then go back and
   read the referenced part.
8. Merge `diagnose-session` and `session-timeline` (approved by user).

### Bug found during design (drives requirement 1)

opencode `@L<n>[i]` refs are **wrong** whenever a message contains parts the
converter drops (`step-start`, `step-finish`, `patch`, `file`, …): rendered
block indices are positions in the *converted* content list, not the export's
`parts[]`, so the legend's promised path `.messages[n-1].parts[i]` does not
match the printed ref. Nearly every assistant message is off by one or more.
Fixing this is core to requirement 1, not a nice-to-have.

## Tool spec: flags as 4 orthogonal axes

Both tools share the same CLI surface (`add_shared_args`). Organize every
flag into exactly one axis; a command picks at most one value per axis, so
any combination's meaning is predictable. Document the axes in `--help`
(grouped help sections) and in repo `CLAUDE.md`.

- **SELECTION** — which records participate:
  default = last compaction leg only, rewound branches hidden, model-visible
  records only · `--compact-all` / `--compact-leg N` · `--show-rewound` ·
  `--show-all` · `--no-progress`
- **DENSITY** — view mode (mutually exclusive):
  default = full render · `--chat-only` · `--skeleton` (new).
  `--chat-only --skeleton` together → exit 1 with a clear error.
- **BODY-DETAIL** — only meaningful within the default full-render density:
  `--tool-max N` · `--truncate-input` · `--no-thinking` · `--show-usage`.
  Documented no-ops under `--chat-only`/`--skeleton`.
- **OUTPUT** — `--color`/`--no-color` · `--agent` · `--validate-only`.

Refs (`@L<n>[i]`) are stable across all SELECTION/DENSITY choices: they
always name the raw source coordinates (JSONL line for cc; export message +
part index for opencode), so an extraction command written against the
skeleton works no matter which view produced it.

## `--skeleton` (new DENSITY mode)

One line per block; a 3-line header carries the extraction recipe. Mocked
from a real export:

```
# skeleton: ses_00b8… calm-wizard · 17 msgs · opencode-go/kimi-k3 · /root/claude-config-work3
# sizes: ~tok ≈ chars/4 (batch-planning heuristic)
# extract: opencode export ses_00b8… > /tmp/oc-ses_00b8….json && jq '.messages[<n-1>].parts[<i>]<leaf>' /tmp/oc-ses_00b8….json
@L1[0]   user         428~tok    .text                     "using superpowers skill: update {opencode-pretty…"
@L2[1]   reasoning    1048~tok   .text                     "Let me parse this task…"
@L2[2]   text         32~tok     .text                     "I'll start by invoking the brainstorming skill…"
@L2[3]   tool:skill   in:6 out:2984~tok  .state.input/.state.output  name=brainstorming
⟐ compacted · section 1 hidden (38 records) · reveal: --compact-all or --compact-leg 0
⟲ rewind · 15 records hidden · reveal: --show-rewound
```

cc-pretty skeleton has the same shape; header recipe is
`sed -n '<n>p' <file> | jq -r '.message.content[<i>]<leaf>'` and tool results
are their own lines (`@L14[0]  result  1.2k~tok  .content  "PASS …"`).

**Columns**: ref · block type · size (~tok, chars/4) · leaf path · short
preview (first ~50 chars, single line; for tools, the target — filePath /
command / pattern / `name=` for skill+task).

**Leaf tables** (printed in/under the header recipe):

| opencode part | leaf |
|---|---|
| reasoning / text / user text | `.text` |
| tool input / output | `.state.input` / `.state.output` |

| cc block | leaf |
|---|---|
| thinking | `.message.content[i].thinking` |
| text | `.message.content[i].text` |
| tool_use input | `.message.content[i].input` |
| tool_result content | `.message.content[i].content` |
| user string input | `.message.content` (no index) |
| attachment | `.attachment.content` |

**Hidden-region markers are skeleton lines** carrying the exact reveal flag —
the deviation hint lives in the output itself (requirement 3):
`⟐ compacted · section 1 hidden (38 records) · reveal: --compact-all or --compact-leg 0`
and `⟲ rewind · 15 records hidden · reveal: --show-rewound`.
SELECTION flags compose: `--skeleton --compact-all` skeletons every leg.

Harness asymmetry to document in the skill: a cc JSONL file always contains
every line (compacted legs and rewound branches alike — `sed`/`jq` bypass all
hiding); an opencode export contains all compaction legs but only uncleaned
rewind tails (revert state), since opencode deletes abandoned tails on the
next prompt.

## Full-render upgrades (default DENSITY)

1. **Source-true refs (bug fix).** Conversion records each content block's
   source part index; the renderer uses it for opencode refs. A tool_use and
   its tool_result share the tool part's `@L<n>[i]`; leafs disambiguate
   (`.state.input` vs `.state.output`). cc-pretty refs are already
   source-true (line number + `.message.content` index).
2. **Refs on every block.** Thinking headers and text blocks gain `@L<n>[i]`;
   user-input headers gain `@L<n>` (today only tool calls/results/context/
   attachments carry refs).
3. **Legend upgrade.** The top-of-output legend gains the per-type leaf
   table, so every visible piece has a documented direct-str path.
4. **Truncation hints.** Any block cut by `--tool-max`/`--truncate-input`
   gets one dim line with the exact recovery command, e.g.
   `…full: jq '.messages[5].parts[3].state.output' /tmp/oc-ses_….json` or
   `…full: sed -n '57p' log.jsonl | jq -r '.message.content[0].content'`.
   With `--from-file`, hints name that file.
5. **Marker reveal hints.** Rewind/compaction markers in the full render gain
   the same `reveal:` lines as the skeleton.
6. **`--agent` guidance line.** The chunk-file listing no longer says
   "Read all N files in parallel"; it lists the files and points at the
   skeleton-first protocol (`--skeleton` + targeted extraction; see
   `skills/session-analysis/`).

## Merged skill: `session-analysis`

Replaces `skills/session-timeline/` and `skills/diagnose-session/` with one
skill dir `skills/session-analysis/` containing SKILL.md, CLAUDE.md, and a
README.md carrying the diagnose-session design-rationale/limitations content
(updated for the merge).

Structure:

```
## Invocation
   (subagent guidance from session-timeline, incl. the whole-session exception)
## Modes
   evidence (parent-dispatched default) · question (direct default) · diagnose
## Reading protocol (shared core)
   1. Run the skeleton command; read it fully.
      - opencode: agent-tools opencode-pretty <session-id> --skeleton
        (add --from-file <export.json> when a saved export exists)
      - cc:       agent-tools cc-pretty <file.jsonl> --skeleton
   2. Hidden regions (⟐/⟲ lines)? If the focus may touch them, re-run the
      skeleton with the printed reveal flag; else note and move on.
   3. Plan batches: adjacent blocks totaling ≤ ~10k tokens (size column).
      Key blocks may be read out of order first.
   4. Extract one batch with ONE command naming exactly those paths:
      - opencode slice:  jq '.messages[9:25]' /tmp/oc-<id>.json
        (0-based slice: .messages[a:b] covers refs @L(a+1)..@Lb;
        or per-part pick: jq '.messages[4].parts[3].state.output' …)
      - cc slice:        sed -n '10,25p' <file>.jsonl | jq -r '…'
   5. Think about the batch's relevance before fetching the next.
   6. Coverage sweep: read all remaining unread blocks. Required: every
      reasoning block, every text block, every tool input. Tool OUTPUT is
      optional — but if a later thinking/text block references it, go back
      and read/explore/understand the referenced part.
## Harness notes
   opencode: export pitfalls (stdout > file, never pipe to jq), schema,
     jq recipes, F62 heading-only reasoning, compound bash, metadata-only reads
   claude-code: sed+jq recipes, record shapes
## Mode: evidence
   (invariants, extractor judgment, provenance, anti-patterns, output naming —
    content unchanged from session-timeline)
## Mode: diagnose
   (semantic timeline, detection tiers, evidence-first protocol, Required-notes
    comparison, report format — content unchanged from diagnose-session,
    minus "read all files in parallel" and the no-subagents rule)
```

The reading protocol replaces both skills' current Step-1-style instructions.
diagnose-session's "Do NOT use subagents" rule is dropped: batched extraction
bounds context per read, and the Invocation section gives unified subagent
guidance.

## Reference updates

- `agents/session-timeline.md` → `agents/session-analysis.md` (name,
  description, skill reference).
- `skills/CLAUDE.md` — directory table: replace the two rows with
  `session-analysis/`.
- `skills/diagnose-workflow/SKILL.md` + `README.md` — "Relationship to
  diagnose-session" section points at the merged skill's diagnose mode.
- `.claude/skills/prompt-tests/SKILL.md` — grading instructions invoke
  `/diagnose-session`; update to the merged skill's diagnose mode.
- Repo `CLAUDE.md` — `agent-tools cc-pretty` / `opencode-pretty` entries gain
  `--skeleton`; skills table row updates.
- `docs/opencode-system-prompt/build-self-reported.md` — reference update.
- Historical notes/specs (`notes/**`, `docs/superpowers/**` prior docs) stay
  untouched except the live link in `notes/compliance-check-failure-mode.md`
  to `skills/session-timeline/SKILL.md`, which is updated to the new path.

## Testing

TDD via the existing suites (`tests/test_opencode_pretty.py`,
`tests/test_cc_pretty_render.py`):

- skeleton line shape (both tools)
- source-true refs: message with `step-start` before a tool part renders the
  export's true part index
- tool_result ref = tool part index with `.state.output` leaf
- truncation-hint line text (cc + opencode + `--from-file`)
- compaction/rewind marker `reveal:` hints
- `--chat-only --skeleton` → exit 1
- legend leaf table present

## Alternatives considered

- **Skeleton line format B** (full jq path per line): copy-pasteable with zero
  lookup, but +50 chars/line — skeleton stops being small. Rejected.
- **Skeleton line format C** (leaf table only, no per-block leaf column):
  smallest lines, but reader must mentally join two tables per block.
  Rejected — weaker on requirement 1.
- **Keep two skills, share a reading-protocol doc**: avoids touching
  prompt-tests/diagnose-workflow references, but the protocol and harness
  notes would live in a third place both skills import; the two skills share
  ~60% of their workflow after this change. User chose merge.

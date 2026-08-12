# session-timeline: two-mode design

Date: 2026-08-12

## Summary

Extend the `session-timeline` skill with two invocation modes — **question mode**
(default for direct user invocation) and **evidence mode** (required for
parent→subagent dispatch, matches current behavior). Add a lightweight agent
wrapper at `agents/session-timeline.md` for streamlined dispatch.

Mode is an explicit parameter in the invocation brief — not inferred from
context. Enforcement is by convention (documented in SKILL.md + agent wrapper),
not runtime.

## Modes

### question mode

Default for direct user invocation.

Input:
- One or more session IDs
- Optional question
- Default question if omitted: *"What happened in this session — highlight
  anything noteworthy, unexpected, or requiring investigation."*

Output:
- Evidence artifact (same file, same format, same invariants as evidence
  mode). Focus of the artifact = the question.
- Synthesized answer to the question, returned in the response prose.

Response shape: `{ answer_prose, evidence_path }`.

The evidence artifact stays pure (facts only). The answer is separate — in the
response, not in the artifact — so the artifact remains reusable substrate for
later interpretive rounds.

### evidence mode

Required for parent→subagent invocation.

Input:
- One or more session IDs
- A description of what's important. Can be phrased as a focus, a question the
  parent will answer later, or an evaluation criterion. The output is a factual
  log regardless of how the request was phrased.

Output:
- Evidence artifact only (facts only, all existing invariants preserved).

Response shape: `{ evidence_path, one-paragraph summary of contents }`.

Extractor discipline: gather anything that MIGHT be relevant to the focus.
When in doubt, include (summarized). No interpretive answer.

## Mode selection

Explicit `mode:` in the invocation brief. No auto-inference (invocation source
cannot be reliably detected at runtime).

- User direct invocation → question mode; default question fills in if omitted
- Parent dispatching a subagent → MUST be evidence mode

Enforcement is by documentation, in three places:
1. `SKILL.md` states the rule up front (new "Modes" section)
2. The agent wrapper's frontmatter description names evidence mode as the
   dispatched-subagent default
3. The agent wrapper's body reminds the subagent: if dispatched by a parent,
   use evidence mode

## Contracts

### User ↔ direct invocation (question mode)

- User provides session ID + optional question
- Agent returns answer prose + `evidence_path`
- User can re-read the artifact independently and ask follow-ups

### Parent ↔ subagent (evidence mode)

- Parent has read `skills/session-timeline/SKILL.md` before dispatching, so the
  parent knows what the artifact contains, what invariants apply, and how to
  phrase the focus.
- Parent's brief: session ID(s) + focus/description + `mode: evidence`
- Subagent produces evidence artifact; returns `{ evidence_path, one-paragraph
  summary }`
- Parent reads artifact(s) and synthesizes across them. Synthesis is not
  persisted by this skill.

### Reader ↔ writer of evidence artifact (unchanged from today)

- Writer: facts only, all existing invariants
- Reader: draws conclusions

## Agent wrapper: `agents/session-timeline.md`

Deliberately light. Frontmatter + short body.

Frontmatter fields:
- `name`: `session-timeline`
- `description`: names when to use, states "operates in evidence mode when
  dispatched by a parent"
- `tools`: `Read, Bash, Grep, Glob, Write` (no Edit — artifacts are new files)
- `model`: inherit (no override needed; skill workflow is I/O bound)

Body:
- Invoke the `session-timeline` skill via the Skill tool
- Default mode when dispatched by a parent = evidence
- Parent MUST have read the SKILL.md before dispatching (visible to parents
  who read the agent definition to write their brief)
- Response format: `{ evidence_path, one-paragraph summary }`

## SKILL.md edits

Preserve all existing sections (Invariants, Extractor judgment, Provenance,
Anti-patterns, Harness-specific rendering, Output location and naming) — they
describe the evidence artifact itself, which is common to both modes.

Add:
- **"Modes"** section (before Invariants): documents question vs evidence, mode
  selection rule, default question, response shape per mode
- **"For parents dispatching this skill"** section (near Invocation): parent
  must read SKILL.md before dispatch; parent must pass `mode: evidence`; brief
  format; parent's synthesis happens outside the skill
- **Evidence discipline** clarification (extend Invariants or add a note): "in
  evidence mode, gather anything that MIGHT be relevant to the focus; when in
  doubt, include (summarized)"

## Practical: many-subagent cross-session analysis

Scenario: parent dispatches N subagents, each on a different session or focus.

- Existing `<top-slug>__<focus-slug>.md` naming handles collision (top-slug
  uniquely identifies session)
- Each subagent's response is compact (path + one paragraph); parent's context
  stays clean
- Parent synthesizes across N artifacts in its own turn/artifact

The evidence artifacts persist beyond the subagent's lifetime and are the
substrate for the parent's synthesis. Nothing about many-subagent use requires
skill changes beyond what's specified above.

## Acceptance criteria

- `skills/session-timeline/SKILL.md` has a "Modes" section documenting both
  modes and the selection rule
- `skills/session-timeline/SKILL.md` has a "For parents dispatching this skill"
  section stating the parent's read-SKILL.md obligation and requirement to pass
  `mode: evidence`
- `agents/session-timeline.md` exists with `name`, `description`, `tools`
  frontmatter, and a body that instructs the subagent to invoke the skill and
  default to evidence mode
- All existing SKILL.md content (Invariants, Extractor judgment, Provenance,
  Anti-patterns, Harness-specific rendering, Output location and naming) is
  preserved and remains applicable to both modes
- Default question wording matches this spec verbatim

## Files

- Modify: `skills/session-timeline/SKILL.md`
- Create: `agents/session-timeline.md`
- Create (this spec): `docs/superpowers/specs/2026-08-12-session-timeline-two-modes-design.md`

## Decision log

- **Explicit `mode:` param, not inferred**: invocation source cannot be
  reliably detected at runtime; explicit is safer than a heuristic that fails
  silently.
- **Answer is response-only in question mode, not persisted**: keeps the
  evidence artifact pure (facts only) so it can be reused as substrate. Users
  who want to preserve an answer can save the response themselves.
- **Diagnostic-leaning default question**: user-selected. Biases evidence
  gathering toward anomalies but matches the common use case of investigating a
  session post-hoc.
- **Enforcement by convention only**: no script-level enforcement is possible
  without runtime introspection. Documented in three places (SKILL.md, agent
  wrapper description, agent wrapper body) so the constraint is visible from
  whichever surface a caller enters through.
- **Agent wrapper is lightweight, no script orchestration**: the skill already
  encodes the workflow; the agent just carries the invocation and mode
  defaults.

## Rejected alternatives

- **Auto-infer mode from invocation source** — unreliable; runtime cannot
  distinguish user direct invocation from Agent-tool dispatch cleanly.
- **Two separate skills (`session-timeline-question`,
  `session-timeline-evidence`)** — duplicates the workflow spec; forces skill
  authors to keep two files in sync. One skill with two modes shares all the
  invariant/extraction/rendering content.
- **Embed the answer inside the evidence artifact** — violates the
  reader/writer contract that keeps the artifact as pure evidence for reuse.
- **No default question (error if missing)** — adds friction for the common
  case; user explicitly requested a default.

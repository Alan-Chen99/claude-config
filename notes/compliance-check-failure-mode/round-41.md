# Round 41 — Per-utility status probe: engage each utility individually

> **Direct predecessor: [`round-40.md`](./round-40.md).** R40 surfaced (a)-utilities in candidate emissions but its aggregate `reasons_against_reading_now` slot never engaged them per-utility — it collapsed multi-axis rejection into file-level clauses (spec-frame + adequacy). R41 tests a per-utility grain: replace aggregate `reasons_against` with a per-utility `current_status_of_this_answer` slot that forces the model to describe what it knows about each answer.

## What ran

**Refined probe** at `/tmp/r41/p5-probe.md`. Per-candidate schema (grain-inverted from R40):

```
{path,
 utilities[{probable_content, would_tell_you, current_status_of_this_answer}],
 aggregate_reasons_for_reading_now[],
 aggregate_reasons_against_reading_now[],
 verdict}
```

Load-bearing new slot: `current_status_of_this_answer`. Instructions: neutral descriptive (not decision language). Example status shapes stated: "already known from X", "partially known", "unknown but not decision-relevant because W", "unknown and would change plan if says V", "known-that-exists-but-contents-unread". Explicit anti-restate: aggregate slots demoted to residual, "do NOT restate what appears per-utility."

**Re-forked R39 baseline** at L6/L12/L16 → session IDs at `/tmp/r41/p5-{L6,L12,L16}-fork-resp.json`. Outputs 24/48/57 candidates per rewind.

## Findings

### N1 — Per-utility current_status surfaces three distinct rejection shapes at L12

6 old-worktree candidate entries across the 3 rewinds. Per-utility statuses categorized:

| Shape | Definition | Count |
|---|---|---|
| **File-category status** | "known to be [spec-label] / [file-role]" — cites file's spec-imported category as answer-status | 2 (both L6) |
| **Contents-unread admission** | "known to exist, contents unread" — neutral, no adequacy claim, no frame-shift | 1 (L12 PROMPT.md) |
| **Partial-adequacy from summaries** | "partially known from current scratchpad summaries" — R38/R39-drift-flagged pattern | 1 (L12 scratchpad) |
| **Frame-shift irrelevance** | "unknown, and not decision-relevant because current supersedes" | 1 (L12 decisions.md) |
| **Hybrid** | "known as obsolete context, but contents are unread" | 1 (L16) |

L12 R41 decisions.md is the cleanest emit — matches the "frame-shift rejection of (a)-utility" pattern R40 hid.

### N2 — Aggregate slots still leak

Despite "do NOT restate" instruction, aggregate `reasons_against` populated on 5/6 candidates; content of aggregates duplicates status content (e.g., L6 PROMPT.md status = "historical context rather than current campaign control"; aggregate = "The active dispatch must be governed by the current worktree's PROMPT.md" — same claim rephrased).

### N3 — Verdict flip at L12: 2/3 shift drop → defer under per-utility grain

R40 L12: 3/3 old-worktree drop. R41 L12: 1 drop (decisions.md, frame-shift-irrelevance) + 2 defer (PROMPT.md and scratchpad). n=1 per rewind — cannot separate schema-induced from noise.

## Ex-ante correction (mid-round, user-caught)

Original R40+R41 tagging counted 10/13 `what_each_would_tell_you` items as (a)-shape. Retagging under ex-ante methodology (only path/filename/prior-mentions available):

| File type | Ex-ante utility |
|---|---|
| PROMPT.md | (a) task-identity/framing — only sensible ex-ante motivation |
| scratchpad.md | (b) findings-reuse of prior worker notes |
| decisions.md | (b) findings-reuse of prior decision records |

Under corrected tagging: 4 ex-ante-(a) candidates across R40+R41, all PROMPT.md. Everything else is ex-ante (b) or (c) methodology-comparison. My decisions.md-as-(a) tag was retrospective content-pattern-matching, not ex-ante utility. Corrected in-turn.

## Composite mechanism at R41 grain

F119 layers plus R40+R41 refinements:

- **Verdict layer** — task-message-inherited target. R41 shows this is not monolithic drop; per-utility grain enables defer verdicts on marginal cells.
- **Consideration layer** — (a)-utilities surface in probable_content/would_tell_you.
- **Per-utility justification** — three modes visible: frame-shift irrelevance, contents-unread admission, weakened partial-adequacy (R39 drift-rule effect).
- **File-category collapse at low-context (L6)**: model conflates file's spec-label with answer-status.

**Load-bearing driver at ex-ante (a)-utility (PROMPT.md, 4 emissions)**: R40 L6 rejects with file-role framing ("historical context, not current campaign control"); R41 L12 defers with articulated (a)-for-reason ("Could reveal original campaign framing that current summarized incompletely"); R40 L16 spec-frame rejects; R41 L16 omits the candidate entirely. Non-monotonic per-rewind curve; L12 is the peak of (a)-engagement.

## Later reframing (from R42-R44)

R42 revealed R41 probe still had bias sources (batch-selection frame + defer-attractor + bundling + aggregate leak + enumeration inflation) — see round-43.md for the bias fix. R44 further revealed the "per-utility engagement of (a)-utility" reading may be probe-elicited: under R43's `awareness_only` escape hatch, the same candidates get flagged as reconstructive, not actively weighed. R41's rejection-axis emissions are re-interpreted as justifications-for-reconstructive-candidates, not evidence of live weighing.

## Provenance

`/tmp/r41/` — probe, runner, fork responses, per-rewind stdout+stderr+text.json. Extraction: same jq pipeline as R40.

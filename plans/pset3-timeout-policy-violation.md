# pset3 Plan: 120s Timeout Policy Violation — Root Cause Analysis

## Summary

The pset3 plan contains `timeout: 120` and `timeout: 60` in CC-M-006-001 code diffs, violating CLAUDE.md line 149: "Increasing time limit to larger than 30 seconds requires explicit user approval." The plan-code QR gate — the sole gate that could have caught this — passed with the violation present. The decompose agent had the information and the right severity category (CONVENTION_VIOLATION) but didn't generate an item for it.

## Session

- **Conversation**: `/root/.claude/projects/-workspace-sp26-vision/330cbb5a-dbe1-4e86-9625-8bdcf3819527.jsonl`
- **Plan output**: `/workspace/sp26/vision/plans/pset3-plan.md`
- **Plan state**: `/tmp/planner-y_c6lctm/`

## Corrected Temporal Flow

| Phase | Artifact state | QR scope | Catch opportunity? |
|---|---|---|---|
| plan-design (steps 1-6) | DL-004 ("30s"), CI-M-006-001 (">5s"). No diffs. | Decisions, constraints, risks | **No** — nothing to catch yet. QR correctly passed DL-004. |
| **plan-code (steps 7-10)** | Diffs generated: 30s, 120s, 60s | Syntax, format, refs, types, conventions | **YES — sole opportunity. Missed.** |
| plan-docs (steps 11-14) | Doc_diff exists only for the 30s cell | Doc quality, WHY-not-WHAT | **No** — 120s/60s cells have no doc_diff |

The prior analysis incorrectly attributed the "DL-004 timeout=30s — within limit" QR finding to a verification gap. That finding was from plan-design QR, which was temporally correct: no code diffs existed yet.

## Three Failure Layers

### Layer 1: Specification gap (design time)

DL-004 has an internal split:
- `decision` field: "build_undistort_maps cell needs timeout metadata **> 5s**"
- `reasoning` field: "...set cell timeout to **30s** in jupytext metadata"

CI-M-006-001 propagates the decision field's ">5s" into its behavior text. Even if the developer had resolved `decision_refs: ['DL-004']`, it would have seen ">5s" in the decision summary, not "30s". The 30s ceiling is buried in the reasoning text.

### Layer 2: Unconstrained code generation

Developer subagent (`agent-a9c10454a1edc3dfd`):
- Received CI-M-006-001 behavior: "Add timeout metadata to cells that need > 5s"
- Prompt (`plan_code_execute.py`): "Decision Log provides WHY context" — vague, no instruction to resolve/enforce decision_refs
- Never accessed `planning_context.decisions` (0 reads in 48-line session)
- Chose 30s for Part 1, 120s for Part 2, 60s for Part 5 based on runtime estimation

### Layer 3: Plan-code QR verification scope gap

The decompose agent (`agent-af2efcbef5f7074e4`, 100 lines, 240KB) **did see** all three values and **did read** CLAUDE.md. Its analysis text explicitly listed:

> "The diff shows three insertions: `# %% [timeout: 30]`... `# %% [timeout: 120]`... `# %% [timeout: 60]`"

But it focused on the **syntax bug** (bracket vs JSON notation) and generated items only for code correctness:
- qa-001 [MUST]: Wrong jupytext syntax
- qa-003 [COULD]: Wrong hunk header counts

Its fix guidance actively prescribed the 120s/60s values: *"Fix: Replace... `# %% {"timeout": 120}` for demo_part2_calibrate"*

The downstream verifier (`agent-a1f5658d25fedd4e3`) also explicitly enumerated 120s/60s in its analysis but only checked syntax per its mandate.

### Why CONVENTION_VIOLATION should have caught it

`plan_code_qr_decompose.py` line 86 defines:
```
CONVENTION_VIOLATION: violates documented project convention
```

CLAUDE.md line 149 ("Increasing time limit to larger than 30 seconds requires explicit user approval") is a documented project convention. The category existed and applied. The decompose agent didn't use it because:

1. STEP_2_CONCERNS line 50 says `Convention violations (per project style)` — the "(per project style)" phrasing steers toward code style, not policy limits
2. The agent's attention was dominated by the syntax bug (a genuine MUST-severity finding), and it treated the timeout values as correct inputs to its fix

### Why plan-docs QR didn't help

CC-M-006-001 has code diffs for 3 hunks but doc_diff for only the 30s hunk. The 120s/60s cells were undocumented by the architect. Docs QR is scoped to doc_diff fields only (`STEP_1_ABSORB`: "WHAT YOU DO NOT REVIEW: milestones[].code_changes[].diff"). qa-011 checked "WHY timeout is 30s" because that's the only documented timeout.

## Inconsistencies in the Plan

| Severity | Finding |
|---|---|
| CRITICAL | `timeout: 120` on demo_part2_calibrate — 4x the 30s policy, no user approval |
| CRITICAL | `timeout: 60` on demo_part5_reconstruction — 2x the 30s policy, no user approval |
| HIGH | DL-004 decision field says ">5s", reasoning says "30s" — internal DL inconsistency |
| HIGH | Tradeoffs says "30s timeout for slow cells" but code uses 120s/60s |
| HIGH | Doc comment for build_undistort_maps attached to wrong cell (demo_part1_contours; verified: that cell does not call build_undistort_maps) |
| MEDIUM | 120s/60s cells have no doc_diff — undocumented |
| MEDIUM | CODE_WITHOUT_DOCS check is per-code_change not per-hunk — 1 documented hunk "covers" a 3-hunk change |

## Key Subagent Logs

| Agent | Role | Key finding |
|---|---|---|
| `agent-af2efcbef5f7074e4` | plan-code QR decompose (100 lines) | Saw all three values, read CLAUDE.md, generated syntax/format items only. Prescribed 120s/60s in fix guidance. |
| `agent-a1f5658d25fedd4e3` | plan-code QR verify for qa-001/qa-003 (27 lines) | Explicitly enumerated 120/60 values, checked only syntax per mandate |
| `agent-a9c10454a1edc3dfd` | Developer for CC-M-006-001 (48 lines) | Never read planning_context.decisions. Chose 120s/60s independently. |
| `agent-a7a6c7fa1c9e129c6` | plan-docs QR verify for qa-011 | Never saw 120s/60s — only received doc_diff (30s cell only) |

## Fix Proposals

| Priority | Fix | Target | Rationale |
|---|---|---|---|
| P0 | Expand STEP_2_CONCERNS hint: `Convention violations (per project style, CLAUDE.md policy limits, constraint thresholds)` | `plan_code_qr_decompose.py:50` | Steers decompose agent toward policy limits, not just code style |
| P0 | Expand CONVENTION_VIOLATION definition: `violates documented project convention (including CLAUDE.md policy limits)` | `plan_code_qr_decompose.py:86` | Makes the category explicitly cover policy violations |
| P1 | Developer prompt: "For each code_intent with decision_refs, read the referenced decision and treat its constraints as binding" | `plan_code_execute.py` | Prevents unconstrained generation |
| P1 | Architect prompt: propagate specific values from DL reasoning into CI behavior text | plan-design prompts | Closes the ">5s" vs "30s" specification gap |
| P2 | Hunk-level CODE_WITHOUT_DOCS check | `plan_docs_qr_decompose.py` | Catches partially-documented multi-hunk code_changes |

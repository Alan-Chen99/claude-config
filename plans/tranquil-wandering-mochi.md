# Plan: AGENTS.md Policy Changes from Edge Case Analysis

## Context

Three deepthink sessions analyzed the interaction between AGENTS.md Active Work policy, the planner system, and proposed `agent_policies.md`. Key findings:

- The checkbox exception in addition-only enables blockquote editing (proven by commit `07386779`)
- Deferring Active Work sync to plan completion creates stale state that subsequent sessions build on incorrectly
- IK belongs in Active Work always; the plan is a secondary record
- User `> [ ]` items as statements (not questions) eliminates the need for any special "answer" category
- Lifecycle header status changes (`[IN-PROGRESS]` → `[DONE]`) are implicitly permitted but not explicitly stated
- "Project rules override plan" needs to be stated

All changes target `@AGENTS.md`. No changes to `agent_policies.md` (deferred per user).

## Changes

### C-1: Scope the checkbox exception in addition-only (line 309)

**Current:**
```
- **Addition-only.** Do not edit or delete prior information; corrections must be new bullets (e.g., "previous note was wrong; here's why").
```

**New:**
```
- **Addition-only.** Do not edit or delete prior information; corrections must be new bullets (e.g., "previous note was wrong; here's why").
  - Exception: checking a box (`[ ]` → `[x]`) and adding sub-items are permitted edits. This does NOT apply to blockquote checkboxes (`> [ ]`), which are user-maintained and read-only.
  - Exception: status markers in section headers (e.g., `[IN-PROGRESS]` → `[DONE]`) are permitted edits per the lifecycle.
```

**Why:** Commit `07386779` reverted 6 blockquote edits caused by this ambiguity. Without explicit scoping, agents read "checkbox ticking is permitted" and apply it to `> [ ]` items.

### C-2: Add planner-task guidance to lifecycle step 4 (lines 290-293)

**Current:**
```
4. Make incremental commits.
   - After each relavent commit, note which protions has been complete. Add the short commit ref to the note (so notes must go in its own commit, after code)
   - No implementation details should be given unless the approach changed or an alternative was rejected
   - Plan may be modified as problems and context is discovered.
```

**New:**
```
4. Make incremental commits.
   - After each relavent commit, note which protions has been complete. Add the short commit ref to the note (so notes must go in its own commit, after code)
   - No implementation details should be given unless the approach changed or an alternative was rejected
   - Plan may be modified as problems and context is discovered.
   - **For tasks with a plan file** (in `@notes/`): per-milestone implementation details stay in the plan file. Active Work gets one-line notes for milestones with committed code: `- YYYY-MM-DD — <summary> (commit-ref); plan: @notes/<plan>.md`. IK (design decisions, rejected alternatives) always goes in Active Work, not replaced by a pointer.
```

**Why:** Without this, Rule 6 ("sync once at plan completion") creates a window where every subsequent session reads stale Active Work. The 2026-02-17 plan had 5 milestones — if it failed at M-003, milestones 1-2 would be committed code with no Active Work trail.

### C-3: Ensure cross-item notes are not deferred by plans (line 311 area)

Add to the "Mandatory when you impact another item" rule:

**Current:**
```
- **Mandatory when you impact another item.** If your current change affects a different work item, this must be noted.
```

**New:**
```
- **Mandatory when you impact another item.** If your current change affects a different work item, this must be noted. This applies during plan execution — cross-item observations are not deferred to plan completion.
```

**Why:** Without this, an agent executing a plan might defer cross-item notes to the final sync, losing the observation if the plan fails.

### C-4: Expand plan file conventions (after line 340)

**Current:**
```
For items with design evolution or rejected alternatives, use `@notes/<item>.md` to preserve decision rationale while keeping Active Work bullets terse.
```

**New:**
```
For items with design evolution or rejected alternatives, use `@notes/<item>.md` to preserve decision rationale while keeping Active Work bullets terse.

**Plan file conventions** (for planner-generated plans in `@notes/`):
- Plans saved to `@notes/` before execution begins.
- Plan files should include a `## Status` line (`Active`, `Complete`, or `Abandoned`) updated on state change.
- When a plan covers an item that has a prior plan pointer, the new plan should reference the prior plan in its Decision Log.
- AGENTS.md rules always take precedence over plan instructions. When a project rule overrides a plan instruction, note which rule was applied.
```

**Why:** ~75 files in `@notes/` with no index. Abandoned plans are invisible without status markers. The 2026-02-16 and 2026-02-17 plans both cover "Commit Artifact Filtering" — without cross-referencing, a future plan could contradict prior decisions unknowingly.

### C-5: Convert the one question-form blockquote to statement form (line 456)

**Current:**
```
> [ ] why is blacklist used rather than proposed whitelist?
```

**New:**
```
> [ ] investigate why blacklist is used rather than proposed whitelist
```

**Why:** Statement form makes `> [ ]` items uniformly tasks. The answer is IK (rejected alternative), handled by existing rules. No special "question-answering" category needed.

**Note:** This is a blockquote edit — requires user action. Agent should not make this change.

### C-6: Typo fix in lifecycle step 4 (line 291)

Fix "relavent" → "relevant", "protions" → "portions" while editing that section.

## What this does NOT change

- `agent_policies.md` (deferred per user)
- "Additional User Tasks" section lifecycle — these items already follow a natural pattern (agent bullet below blockquote for completion). Formalizing would add complexity for little gain.
- Planner system code (`/other/claude-config/`) — architectural fixes (deterministic QR gates, etc.) are separate from policy text
- Existing Active Work notes — no retroactive cleanup. New rules apply going forward.

## Verification

1. Read through modified AGENTS.md rules section to check for internal contradictions
2. Walk through the "blacklist approach" scenario under new rules: plan produces DL-002 → IK goes in Active Work as rejected-alternative bullet → plan file also has DL-002 for execution context. Confirm no special case needed.
3. Walk through "plan fails at M-003" scenario: M-001 and M-002 have Active Work notes (per C-2). M-003 failure leaves plan file at `@notes/` with `## Status: Active` or `Abandoned`. Future agent can reconstruct state.
4. Walk through blockquote `> [ ]` scenario: agent reads `> [ ] investigate why blacklist is used` → completes task → writes IK bullet below → does NOT tick the blockquote checkbox (per C-1 scoping).

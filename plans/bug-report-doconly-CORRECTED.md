# Bug Report: Documentation-only milestones incorrectly routed through plan-code phase

## Summary

Milestones marked with `is_documentation_only: true` are incorrectly routed through the plan-code phase (steps 7-10), which applies code validation rules to documentation work. This creates non-converging QR loops because code-oriented checks (diff validation, RULE 0/1/2, context line verification) find stylistic issues in prose rewrites that can never fully converge.

**The planner already has a separate plan-docs phase (steps 11-14) designed specifically for documentation validation.** Documentation-only milestones should skip plan-code entirely and route directly from plan-design (step 6) to plan-docs (step 11).

## Workflow Structure

The planner has 14 steps organized into three phases:

```
Steps 1-6:   plan-design     (architect + QR-Completeness)
             ↓
Steps 7-10:  plan-code       (developer + QR-Code)
             ↓
Steps 11-14: plan-docs       (technical-writer + QR-Docs)
             ↓
             APPROVED
```

### Phase Purposes (from README.md)

| Phase | Agent | Purpose |
|-------|-------|---------|
| **QR-Code** (steps 8-10) | Developer | "Read codebase, verify diff context, apply RULE 0/1/2 to proposed **code**" |
| **Technical Writer** (step 11) | Technical Writer | "Scrub temporal comments, add WHY comments, enrich rationale" |
| **QR-Docs** (steps 12-14) | Quality Reviewer | "Verify no temporal contamination, comments explain WHY not WHAT" |

**Key insight:** QR-Code validates CODE. QR-Docs validates DOCUMENTATION. They use different validation criteria because code and prose have different quality requirements.

## Steps to Reproduce

1. Create a task that only modifies documentation files:
   ```
   "Rewrite Active Work section in AGENTS.md per updated policy"
   ```

2. Run planner workflow:
   - Step 3: Architect creates plan with `is_documentation_only: true` on milestone
   - Step 6: plan-design-qr-route **always routes to step 7** (plan-code), ignoring the flag
   - Step 7: Developer writes unified diffs for documentation changes
   - Step 8: QR-Code decompose generates code validation checks (context lines, format rules, test coverage)
   - Step 9: QR-Code verify finds SHOULD-level stylistic issues in prose
   - Step 10: Gate fails → routes back to step 7

3. Observe infinite loop:
   ```
   Step 7  → Developer rewrites diffs
   Step 8  → QR creates new check items (code-oriented)
   Step 9  → QR finds new stylistic issues (normal for prose!)
   Step 10 → Gate fails → back to step 7 (never converges)
   ```

## Expected Behavior

Step 6 (plan-design-qr-route) should check the `is_documentation_only` flag:

```python
# In planner.py step 6 handler:
if all(m.is_documentation_only for m in plan.milestones):
    return {
        "title": "plan-design-qr-route (doc-only detected)",
        "actions": [
            "All milestones are documentation-only.",
            "Skipping plan-code phase (steps 7-10).",
            f"Routing directly to step 11: plan-docs-work.",
        ],
        "next": f"python3 -m {MODULE_PATH} --step 11 --state-dir {state_dir}"
    }
```

This matches the documented SKIP PATTERN in `plan_code_execute.py:126-127`:
```python
"SKIP PATTERN: If milestone only touches .md/.rst/.txt files,",
"mark as documentation-only (no code_changes needed).",
```

"No code_changes needed" means **skip the code phase**, not just "don't write diffs within the code phase."

## Actual Behavior

Step 6 always routes to step 7:

```python
# orchestrator/planner.py:522-523
6: qr_route_step(
    title="plan-design-qr-route",
    phase="plan-design",
    work_step=3,
    pass_step=7,  # ← Hardcoded! No conditional routing
    pass_message="Proceed to step 7 (plan-code-work).",
),
```

There is **no check** for `is_documentation_only`, so:
1. Plan-code phase runs on documentation work
2. QR-Code applies code validation rules to prose
3. Finds stylistic issues that are normal for documentation
4. Never converges because prose rewrites naturally vary

## Technical Details

### Why This Creates Infinite Loops

**For code milestones** (correct behavior):
- Developer writes code diffs
- QR-Code checks: context lines correct? RULE 0/1/2 violations? Tests needed?
- These are objective checks with right/wrong answers
- Loop converges when all checks pass

**For doc milestones** (broken behavior):
- Developer writes prose diffs
- QR-Code checks: context lines? Format consistency? (Wrong validation criteria!)
- Finds "inconsistent bullet formatting" or "mixed annotation styles"
- These are subjective style choices, not bugs
- Each rewrite makes different stylistic choices
- Loop never converges because checks don't match work type

### Example QR Failures (from real session)

From `qr-plan-code.json` (note: this is CODE QR on DOC work):
- **qa-005 (SHOULD):** "Automation items line 531 has agent bullet not covered by diff"
  - For code: Real bug (missed a call site)
  - For docs: Might be intentional (only rewriting certain sections)

- **qa-006 (SHOULD):** "Started bullet has details, inconsistent with Completed bullet"
  - For code: Inconsistent API = bug
  - For docs: Different detail levels = normal prose variation

- **qa-012 (COULD):** "Mixed completion annotation formats across bullets"
  - For code: Inconsistent patterns = confusing
  - For docs: Natural language variation = expected

### The Flag Exists But Isn't Used

```bash
# The flag exists in schema:
$ git show HEAD:skills/scripts/skills/planner/shared/schema.py | grep -A2 is_documentation_only
is_documentation_only: bool = False

# But routing logic doesn't check it:
$ git show HEAD:skills/scripts/skills/planner/orchestrator/planner.py | grep -A5 "step 6"
# → No conditional routing based on flag
```

## Suggested Fix

### Fix: Add Conditional Routing at Step 6

Modify the step 6 handler in `orchestrator/planner.py` to check the flag:

```python
def plan_design_qr_route_handler(state_dir: str, qr_status: str, ...) -> dict:
    """Route after plan-design QR gate."""

    if qr_status == "fail":
        return route_to_step_3()  # Restart architect

    # NEW: Check if all milestones are doc-only
    from skills.planner.shared.schema import load_plan
    plan = load_plan(state_dir)

    if all(m.is_documentation_only for m in plan.milestones):
        # Skip plan-code phase entirely
        return {
            "title": "plan-design-qr-route (skipping plan-code)",
            "actions": [
                "All milestones are documentation-only.",
                "No code changes to validate.",
                "Skipping steps 7-10 (plan-code phase).",
                "",
                "Proceeding directly to step 11 (plan-docs-work).",
            ],
            "next": f"python3 -m {MODULE_PATH} --step 11 --state-dir {state_dir}"
        }

    # Normal case: route to plan-code
    return {
        "title": "plan-design-qr-route",
        "actions": ["Proceeding to plan-code phase."],
        "next": f"python3 -m {MODULE_PATH} --step 7 --state-dir {state_dir}"
    }
```

**Pros:**
- Clean, semantically correct
- Matches documented SKIP PATTERN intent
- Uses existing phase separation (plan-code vs plan-docs)
- No changes needed to QR logic

**Cons:**
- Requires modifying orchestrator step handler
- Need to handle mixed milestones (some code, some doc-only)

### Alternative: Handle Mixed Milestones

If plan has both code and doc-only milestones:

```python
doc_only_milestones = [m for m in plan.milestones if m.is_documentation_only]
code_milestones = [m for m in plan.milestones if not m.is_documentation_only]

if code_milestones:
    # At least one code milestone → run plan-code normally
    route_to_step_7()
else:
    # All doc-only → skip to plan-docs
    route_to_step_11()
```

Developer at step 7 would only generate diffs for code milestones, skipping doc-only ones. QR-Code would only validate code milestones.

## Impact

**Severity:** High for documentation tasks, None for code tasks

- **Blocks** completion of documentation-only planning work
- **Wastes** LLM tokens on unproductive QR iterations (wrong validation criteria)
- **Frustrates** users who expect doc rewrites to complete quickly
- **Does not affect** code-focused tasks (plan-code phase is correct for those)

## Root Cause

The `is_documentation_only` flag was added in commit `53ce0e7` (2026-02-02, "Large refactor") but **routing logic was never updated** to use it. The flag exists in schema but is never checked by orchestrator step handlers.

The SKIP PATTERN guidance in `plan_code_execute.py` is a hint to the LLM developer subagent, not programmatic enforcement. The orchestrator should enforce this at the routing layer.

## Environment

- Version: Latest main branch (commit `6e72bc2` as of 2026-02-16)
- Python: 3.x
- Affected: All planning workflows with `is_documentation_only: true` milestones

## Additional Context

This explains why the original bug report focused on "QR applying wrong checks" - that's the symptom. The root cause is that **QR-Code shouldn't run at all** for doc-only work. The planner already has the right phase (plan-docs with QR-Docs), it just needs to route there directly.

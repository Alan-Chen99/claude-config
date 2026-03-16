# Bug Report: plan-code QR creates infinite loop for documentation-only milestones

## Summary

The `plan-code` phase QR (Quality Review) creates an infinite verification loop when processing milestones marked with `is_documentation_only: true`. The QR decompose/verify steps generate code-oriented validation checks for documentation diffs, find minor SHOULD-level formatting issues, and route back to the developer for fixes—but the developer rewrites introduce new minor issues, creating an endless cycle that never converges.

## Steps to Reproduce

1. Create a task that only modifies `.md` files:
   ```
   "Rewrite Active Work notes in AGENTS.md per updated todo policy"
   ```

2. Run through planner workflow:
   - Architect sets `is_documentation_only: true` on milestone(s) in plan.json
   - Developer at step 2 (plan_code_execute.py) writes diffs despite the flag
   - QR decompose (step 8) generates 21 check items for the diffs
   - QR verify (step 9) finds SHOULD-level issues (inconsistent formatting, missed items)
   - Gate (step 10) routes back to step 7 (developer fix)

3. Observe the loop:
   ```
   Step 7  → Developer writes diffs
   Step 8  → QR decompose creates checks
   Step 9  → QR verify finds SHOULD failures
   Step 10 → Gate fails → back to step 7
   ```

## Expected Behavior

For documentation-only milestones, one of:

**Option A:** Skip `plan-code` phase entirely; have executor read `code_intents` directly

**Option B:** QR respects `is_documentation_only` flag and either:
- Skips decomposition entirely
- Generates reduced check set (e.g., only verify blockquotes preserved, skip context line verification)

**Option C:** Gate convergence limit:
- After N iterations (e.g., 2), demote SHOULD/COULD failures to warnings
- Pass the gate to allow progress

## Actual Behavior

The workflow loops indefinitely on SHOULD-level formatting inconsistencies in documentation diffs because:

1. QR treats doc diffs like code diffs (full context verification, format rules)
2. Minor style issues are expected in natural-language rewrites
3. No convergence mechanism exists for SHOULD/COULD severity failures

### Example QR Results (iteration 2)

From `qr-plan-code.json`:
- **qa-005 FAIL (SHOULD):** Automation items line 531 has date-prefixed agent bullet with grep command, not covered by diff
- **qa-006 FAIL (SHOULD):** 429 Retry "Started" bullet has implementation details, inconsistent with trimmed "Completed" bullet
- **qa-012 FAIL (COULD):** Mixed completion annotation formats across rewritten bullets

## Technical Details

### Root Cause 1: QR Ignores `is_documentation_only` Flag

```bash
# Verified via grep - zero matches:
$ grep -r "is_documentation_only" skills/scripts/skills/planner/developer/plan_code*.py
# (no output)
```

The flag exists in schema (`shared/schema.py:220`):
```python
class Milestone(BaseModel):
    ...
    is_documentation_only: bool = False
```

But `plan_code_qr_decompose.py` and `plan_code_qr_verify.py` have **no references** to this field. They generate the full set of code-oriented checks regardless:
- Context line verification against codebase
- Diff format validation
- Edge case coverage checks
- Test coverage requirements

For doc-only milestones, these checks add overhead without value—the diffs serve as implementer guidance, not machine-parseable patches.

### Root Cause 2: Developer Skip Pattern Not Enforced

`plan_code_execute.py:126-127` contains a natural-language suggestion:

```python
"SKIP PATTERN: If milestone only touches .md/.rst/.txt files,",
"mark as documentation-only (no code_changes needed).",
```

This is LLM guidance that the developer subagent may or may not follow. In observed sessions, the developer wrote diffs anyway (possibly because architect's `code_intents` already specified per-file behavior).

### Root Cause 3: No Convergence Limit

The gate at step 10 treats **any FAIL** (including SHOULD and COULD severity) as a hard block. For documentation diffs where minor style inconsistencies are expected, this causes infinite loops when:
- Developer rewrites diffs but introduces new minor issues each iteration
- QR decomposes new check items each iteration
- No mechanism exists to say "good enough" for SHOULD-level issues

## Suggested Fixes

### Fix A: Skip plan-code for Doc-Only Milestones

Orchestrator at step 7 checks:
```python
if all(m.is_documentation_only for m in plan.milestones):
    # Skip directly to next phase (exec-implement)
    print("All milestones doc-only, skipping plan-code phase")
    sys.exit(0)  # or route to next phase
```

**Pros:** Clean separation, matches semantic intent of flag
**Cons:** Requires orchestrator logic change

### Fix B: QR Respects `is_documentation_only`

In `plan_code_qr_decompose.py`, check the flag:
```python
def decompose_checks(plan: Plan) -> list[QRItem]:
    checks = []
    for milestone in plan.milestones:
        if milestone.is_documentation_only:
            # Reduced check set for docs
            checks.extend(generate_doc_checks(milestone))
        else:
            # Full code checks
            checks.extend(generate_code_checks(milestone))
    return checks
```

**Pros:** Targeted fix, preserves phase structure
**Cons:** Requires defining "doc checks" semantics

### Fix C: Gate Convergence Limit

In `plan_code_qr_verify.py` gate logic:
```python
if qr_iteration >= MAX_ITERATIONS:  # e.g., 2
    # Demote SHOULD/COULD to warnings
    failures = [f for f in failures if f.severity == "MUST"]
    if not failures:
        print("PASS (convergence limit reached)")
        sys.exit(0)
```

**Pros:** General fix for all phases, not just doc-only
**Cons:** May mask real issues in code milestones

## Impact

**Severity:** High for documentation tasks, Low for code-only tasks

- Blocks completion of documentation-only work items
- Wastes LLM tokens/API calls on unproductive QR iterations
- Frustrates users who expect doc rewrites to complete quickly
- Does not affect code-focused tasks (expected QR behavior there)

## Observed Session Trace

Concrete example from planner state directory:

```
Planner step 7  → Developer writes diffs (3 changes for CLAUDE.md + 2 notes files)
Planner step 8  → QR decompose creates 21 check items across 5 groups
Planner step 9  → QR verify: 3 FAIL (2 SHOULD, 1 COULD severity)
Planner step 10 → Gate FAIL → routes back to step 7
Planner step 7  → Developer dispatched again (would loop indefinitely)
```

QR never converges because each developer iteration introduces slightly different style choices that the QR flags as inconsistent.

## Additional Context

- The `is_documentation_only` flag was added in commit `53ce0e7` (2026-02-02, "Large refactor")
- Flag exists for 2+ weeks but never implemented in QR logic
- Architect correctly sets the flag based on file types
- Developer sees the skip pattern but doesn't consistently follow it

## Environment

- Version: Latest main branch (commit `6e72bc2` as of 2026-02-16)
- Python: 3.x
- Affected: All plan-code QR workflows when `is_documentation_only: true`

## Recommendation

**Implement Fix B** (QR respects flag) as the most targeted solution. Define reduced check set for doc-only milestones:
- Verify blockquotes/formatting preserved where critical
- Skip context line verification (not applicable to prose)
- Skip test coverage requirements
- Allow SHOULD/COULD failures to pass after 1 iteration

This preserves the phase structure while avoiding the infinite loop.

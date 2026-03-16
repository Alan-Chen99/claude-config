## Documentation-only milestones create infinite QR loop

### Description

Milestones marked `is_documentation_only: true` are routed through the plan-code phase (steps 7-10), which applies code validation rules to documentation. This creates infinite QR loops that never converge.

### Reproduction

1. Create a documentation-only task (e.g., "Rewrite AGENTS.md notes")
2. Run planner - architect sets `is_documentation_only: true` in plan.json
3. Observe workflow:
   ```
   Step 6  → Routes to step 7 (plan-code)
   Step 7  → Developer writes documentation diffs
   Step 8  → QR-Code decompose: context lines, format rules, test coverage
   Step 9  → QR-Code verify: FAIL (style inconsistencies)
   Step 10 → Gate fails → back to step 7
   ```

Loop continues indefinitely - each iteration finds different style issues in prose rewrites.

### Expected Behavior

Documentation-only milestones should skip plan-code (steps 7-10) and route directly to plan-docs (steps 11-14).

The planner has separate validation phases:
- **plan-code (steps 7-10)**: QR-Code validates code diffs
- **plan-docs (steps 11-14)**: QR-Docs validates documentation

### Actual Behavior

Step 6 (`plan-design-qr-route`) always routes to step 7 regardless of `is_documentation_only` flag.

**Example QR failures from code validation on documentation:**
- "Line 531 not covered by diff" - legitimate for partial doc rewrites
- "Inconsistent bullet detail levels" - normal prose variation
- "Mixed annotation formats" - expected in natural language

These are subjective style choices, not bugs. Code checks don't converge on prose.

### Root Cause

`orchestrator/planner.py:518-523` - Step 6 uses hardcoded routing:

```python
6: qr_route_step(
    pass_step=7,  # Always routes to plan-code
    ...
),
```

The `is_documentation_only` flag exists in `shared/schema.py:220` but routing never checks it.

### Environment

- Commit: `6e72bc2` (2026-02-16)
- File: `skills/scripts/skills/planner/orchestrator/planner.py:518`
- Affects: All documentation-focused planning workflows

# Planner Skill Bug Report

Discovered during a documentation-only rewrite task (rewriting Active Work notes in AGENTS.md per updated todo policy). Planner planning phase ran to completion; executor was never invoked.

## Bug 1: `KeyError: 'title'` crash on invalid step

### Summary

`mode_main` in `cli.py` crashes with `KeyError: 'title'` when any step-guidance function returns an error dict (`{"error": "..."}`) instead of a valid guidance dict with `"title"` key.

### Location

`skills/lib/workflow/cli.py:116`

```python
# line 109
guidance_dict = guidance

# line 115-116 — crashes here
parts.append(render_step_header(StepHeaderNode(
    title=guidance_dict["title"],  # KeyError: no "title" in {"error": "..."}
```

### Reproduction

Invoke any planner subagent script with a step number beyond its defined range:

```bash
python3 -m skills.planner.architect.plan_design_execute --step 99 --state-dir /tmp/test
```

This calls `get_step_guidance(99, ...)` which returns `{"error": "Invalid step 99"}` at `plan_design_execute.py:296`. `mode_main` then crashes accessing `["title"]` on that dict.

### Affected sites (22 total)

Every `get_step_guidance` that returns `{"error": ...}`:

| File | Line |
|------|------|
| `architect/plan_design.py` | 32, 36 |
| `architect/plan_design_execute.py` | 296 |
| `architect/plan_design_qr_fix.py` | 164 |
| `developer/plan_code.py` | 32, 36 |
| `developer/plan_code_execute.py` | 228 |
| `developer/plan_code_qr_fix.py` | 181 |
| `developer/exec_implement.py` | 31 |
| `developer/exec_implement_execute.py` | 123 |
| `developer/exec_implement_qr_fix.py` | 132 |
| `orchestrator/planner.py` | 321, 598 |
| `technical_writer/plan_docs.py` | 32, 36 |
| `technical_writer/plan_docs_execute.py` | 301 |
| `technical_writer/plan_docs_qr_fix.py` | 182 |
| `technical_writer/exec_docs.py` | 31 |
| `technical_writer/exec_docs_execute.py` | 242 |
| `technical_writer/exec_docs_qr_fix.py` | 138 |
| `quality_reviewer/prompts/decompose.py` | 344 |
| `quality_reviewer/qr_verify_base.py` | 128 |

### How it was triggered

The architect subagent was dispatched via `plan_design.py --step 1`. The router at step 1 dispatches `plan_design_execute.py`. The architect subagent internally tried to advance beyond step 6 (the last defined step), hitting the `{"error": ...}` fallthrough at line 296.

### Fix

In `cli.py`, check for `"error"` before accessing `"title"`:

```python
# After line 109 (guidance_dict = guidance)
if "error" in guidance_dict:
    print(f"Error: {guidance_dict['error']}", file=sys.stderr)
    sys.exit(1)
```

---

## Bug 2: `plan-code` phase produces diffs for doc-only milestones, causing QR loop

### Summary

When `is_documentation_only: true` is set on a milestone, the `plan-code` developer subagent still writes unified diffs to `plan.json`. The QR then checks these diffs (context lines against codebase, format rules, etc.), finds SHOULD-level issues (inconsistent formatting, missed items), and sends the developer back to fix — creating a loop that doesn't converge because:

1. The developer rewrites diffs but introduces new minor issues each iteration
2. The QR decomposes new check items each iteration
3. No convergence mechanism exists for SHOULD-level issues in documentation-only diffs

### Reproduction

1. Create a task that only modifies `.md` files (e.g., rewriting notes in `AGENTS.md`)
2. Architect sets `is_documentation_only: true` on the milestone
3. Developer at `plan_code_execute.py` step 2 sees "SKIP PATTERN: If milestone only touches .md/.rst/.txt files, mark as documentation-only" — but the subagent doesn't consistently follow this instruction and writes diffs anyway
4. QR decompose (`plan_code_qr_decompose.py`) generates check items for the diffs without checking `is_documentation_only`
5. QR verify finds SHOULD-level issues (inconsistent completion annotation format, function names leaked into rewritten bullets, missed items)
6. Orchestrator routes back to step 7 (developer fix) → step 8 (QR decompose) → step 9 (QR verify) → step 10 (fail gate) → step 7 ...

### Concrete session trace

```
Planner step 7  → developer writes diffs to plan.json (3 code_changes for CLAUDE.md + 2 notes files)
Planner step 8  → QR decompose creates 21 check items across 5 groups
Planner step 9  → QR verify: 2 FAIL (qa-005: Automation items missed, qa-006: 429 Started bullet inconsistent)
                                1 FAIL (qa-012: inconsistent completion annotation format, COULD severity)
Planner step 10 → gate FAIL → routes back to step 7
Planner step 7  → developer dispatched again to fix... (would loop)
```

QR results from iteration 2 (file: `qr-plan-code.json`):
- **qa-005 FAIL (SHOULD)**: Automation items line 531 has date-prefixed agent bullet with grep command, not covered by diff
- **qa-006 FAIL (SHOULD)**: 429 Retry "Started" bullet has implementation details, inconsistent with trimmed "Completed" bullet
- **qa-012 FAIL (COULD)**: Mixed completion annotation formats across rewritten bullets

### Root causes

1. **`is_documentation_only` not checked by QR**: `plan_code_qr_decompose.py` and `plan_code_qr_verify.py` have no references to `is_documentation_only`. They generate the full set of code-oriented checks (context line verification, diff format rules, etc.) regardless. For doc-only milestones, these checks add overhead without value — the diffs serve as implementer guidance, not machine-parseable patches.

2. **Developer skip pattern is a suggestion, not enforcement**: `plan_code_execute.py:126-127` says "SKIP PATTERN: If milestone only touches .md/.rst/.txt files, mark as documentation-only (no code_changes needed)." This is natural-language guidance that the LLM subagent may or may not follow. In our session, the developer wrote diffs anyway (possibly because the architect's code_intents already specified per-file behavior).

3. **No convergence limit on SHOULD-level QR failures**: The gate at step 10 treats any FAIL (including SHOULD and COULD severity) as a hard block. For documentation diffs where minor style inconsistencies are expected, this causes infinite loops.

### Possible fixes

**Option A — Skip `plan-code` for doc-only milestones**: If all milestones have `is_documentation_only: true`, the orchestrator at step 7 could skip directly to the next phase. The executor would still apply changes via a developer subagent that reads code_intents directly.

**Option B — QR respects `is_documentation_only`**: `plan_code_qr_decompose.py` checks the flag and either skips decomposition entirely or generates a reduced set of checks (e.g., only verify blockquotes preserved, skip context line verification).

**Option C — Gate convergence limit**: After N iterations (e.g., 2), the gate at step 10 demotes remaining SHOULD/COULD failures to warnings and passes. This is a general fix that helps all phases, not just doc-only.

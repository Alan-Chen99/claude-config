# Bug Report: KeyError crash in workflow CLI when step guidance returns error dict

## Summary

`mode_main()` in `skills/lib/workflow/cli.py` crashes with `KeyError: 'title'` when any `get_step_guidance()` function returns an error dictionary (`{"error": "..."}`) instead of a valid guidance dict with required keys.

## Steps to Reproduce

1. Invoke any planner subagent script with a step number beyond its defined range:
   ```bash
   python3 -m skills.planner.architect.plan_design_execute \
     --step 99 \
     --state-dir /tmp/test
   ```

2. Observe the crash:
   ```
   Traceback (most recent call last):
     File ".../cli.py", line 116, in mode_main
       title=guidance_dict["title"],
   KeyError: 'title'
   ```

## Expected Behavior

The script should:
- Detect the error dict returned by `get_step_guidance()`
- Print a clear error message to stderr
- Exit with non-zero status code

## Actual Behavior

The script crashes with an unhandled `KeyError` when trying to access the `"title"` key that doesn't exist in error dicts.

## Technical Details

### Root Cause

In `skills/scripts/skills/lib/workflow/cli.py`, the `mode_main()` function:

1. Calls `get_step_guidance()` at line 92-96
2. Converts the result to a dict at line 107-109
3. **Immediately accesses** `guidance_dict["title"]` at line 116 without checking if the dict contains an error

```python
# Line 92-96: Call guidance function
guidance = get_step_guidance(
    parsed.step, module_path,
    **{k: v for k, v in vars(parsed).items()
       if k not in ('step',)}
)

# Line 107-109: Convert to dict
else:
    guidance_dict = guidance

# Line 116: CRASH HERE - no error checking
print(format_step(body, next_cmd, title=guidance_dict["title"]))
```

### Affected Call Sites

**22 functions** across the planner skill return error dicts in their invalid-step fallthrough:

| File | Lines | Pattern |
|------|-------|---------|
| `architect/plan_design.py` | 32, 36 | Invalid step handlers |
| `architect/plan_design_execute.py` | 296 | Fallthrough after step 6 |
| `architect/plan_design_qr_fix.py` | 164 | Invalid step handler |
| `developer/plan_code.py` | 32, 36 | Invalid step handlers |
| `developer/plan_code_execute.py` | 228 | Fallthrough after last step |
| `developer/plan_code_qr_fix.py` | 181 | Invalid step handler |
| `developer/exec_implement.py` | 31 | Invalid step handler |
| `developer/exec_implement_execute.py` | 123 | Fallthrough |
| `developer/exec_implement_qr_fix.py` | 132 | Invalid step handler |
| `orchestrator/planner.py` | 321, 598 | Invalid step handlers |
| `technical_writer/plan_docs.py` | 32, 36 | Invalid step handlers |
| `technical_writer/plan_docs_execute.py` | 301 | Fallthrough |
| `technical_writer/plan_docs_qr_fix.py` | 182 | Invalid step handler |
| `technical_writer/exec_docs.py` | 31 | Invalid step handler |
| `technical_writer/exec_docs_execute.py` | 242 | Fallthrough |
| `technical_writer/exec_docs_qr_fix.py` | 138 | Invalid step handler |
| `quality_reviewer/prompts/decompose.py` | 344 | Invalid step handler |
| `quality_reviewer/qr_verify_base.py` | 128 | Invalid step handler |

All return: `{"error": f"Invalid step {step}"}` or similar.

## Suggested Fix

Add error checking immediately after converting guidance to dict:

```python
# After line 109 (guidance_dict = guidance)
if "error" in guidance_dict:
    print(f"Error: {guidance_dict['error']}", file=sys.stderr)
    sys.exit(1)
```

This provides a clean error message and prevents the KeyError crash.

## Impact

**Severity:** Medium
- Affects error handling paths, not normal operation
- Results in confusing stack traces instead of clear error messages
- Makes debugging workflow issues harder for users
- Can occur during normal orchestrator operation when subagents attempt invalid step transitions

## Additional Context

This was discovered when an architect subagent was dispatched via `plan_design.py --step 1`, which routed to `plan_design_execute.py`. The subagent internally advanced beyond step 6 (the last defined step), hitting the error dict fallthrough at line 296.

## Environment

- Version: Latest main branch (commit `6e72bc2` as of 2026-02-16)
- Python: 3.x
- Affected: All workflow scripts using `mode_main()` entry point

## `mode_main()` crashes with KeyError on invalid step number

### Description

`skills/scripts/skills/lib/workflow/cli.py:116` crashes with unhandled `KeyError: 'title'` when workflow scripts are invoked with invalid step numbers.

### Reproduction

```bash
python3 -m skills.planner.architect.plan_design_execute \
  --step 99 \
  --state-dir /tmp/test
```

### Expected Behavior

Error message printed to stderr, exit code 1.

### Actual Behavior

```
Traceback (most recent call last):
  File "skills/scripts/skills/lib/workflow/cli.py", line 116, in mode_main
    title=guidance_dict["title"],
KeyError: 'title'
```

### Root Cause

When `get_step_guidance()` returns `{"error": "Invalid step 99"}`, `mode_main()` attempts to access `guidance_dict["title"]` without checking if the dict contains an error.

This affects all workflow scripts using `mode_main()` - approximately 22 functions across the planner skill return error dicts for invalid steps.

### Environment

- Commit: `6e72bc2` (2026-02-16)
- File: `skills/scripts/skills/lib/workflow/cli.py:116`

# Baseline: pydantic-forward-ref-runtime-compat

Status: RED phase captured on 2026-05-30.

Validation run with Python `3.14.2` and Pydantic `2.12.5` against
`/root/claude-config-work/opencode/agents/alan-default.md` before any prompt
change for this case.

Command:

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "prompt-test": {
      "mode": "primary",
      "prompt": "{file:/root/claude-config-work/opencode/agents/alan-default.md}",
      "permission": {
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "list": "allow",
        "bash": "allow",
        "edit": "deny"
      }
    }
  }
}' opencode run --agent prompt-test --format json --dir /root/claude-config-work/opencode/prompt-tests/alan-default/pydantic-forward-ref-runtime-compat/fixture < /root/claude-config-work/opencode/prompt-tests/alan-default/pydantic-forward-ref-runtime-compat/task.md
```

Observed failure excerpt:

```text
The root cause is the quoted forward reference inside the generic parameter at
`export_catalog.py:23`:

parent: Relationship['CatalogNode']

Because the file already has `from __future__ import annotations`, the whole
annotation is deferred as a string. When Pydantic evaluates that string, the
inner quoted `'CatalogNode'` is passed as a string generic argument to
`Relationship[...]`, not as the model type.
```

Missed requirements from `reference-solution.md`:

- Treated the application annotation as the root cause rather than as the
  trigger for a runtime/library compatibility failure.
- Did not check adjacent Python versions, adjacent Pydantic versions, or
  upstream Pydantic issue/PR history.
- Did not recognize the same application pattern is valid on adjacent runtimes.
- Proposed an application-code explanation even though the task was to diagnose
  root cause, and version/upstream compatibility was an available explanation.

Control validation with a more explicit task prompt passed: when asked to
diagnose whether the failure was a script bug or upstream/runtime compatibility
issue, the agent checked Python `3.12` and `3.13`, found Pydantic issue `#12732`
and PR `#12733`, and concluded the script is valid application code affected by
Pydantic/Python `3.14` compatibility behavior.

When running this case, record:

- Date, Python version, Pydantic version, and opencode version.
- Agent prompt path under test.
- Exact command from `run.md`, including any `--model` override.
- Concise output excerpt showing whether upstream/runtime compatibility was
  investigated.
- Which requirement from `reference-solution.md` was missed, if any.

This case should be run with `fixture/` as the opencode working directory so the
target agent cannot discover `reference-solution.md` or `baseline.md` while
debugging the application script.

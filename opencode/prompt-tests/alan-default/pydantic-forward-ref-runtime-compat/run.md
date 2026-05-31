# Run: pydantic-forward-ref-runtime-compat

This case runs `opencode/agents/alan-default.md` (in the worktree under test) as
a temporary primary opencode agent named `prompt-test`.

`REPO` resolves to the worktree the case lives in, so the command runs against
the prompt file in that worktree rather than a fixed path. Run from anywhere
inside the worktree:

```bash
REPO="$(git rev-parse --show-toplevel)"
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "prompt-test": {
      "mode": "primary",
      "prompt": "{file:'"$REPO"'/opencode/agents/alan-default.md}",
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
}' \
opencode run --agent prompt-test --format json \
  --dir "$REPO/opencode/prompt-tests/alan-default/pydantic-forward-ref-runtime-compat/fixture" \
  < "$REPO/opencode/prompt-tests/alan-default/pydantic-forward-ref-runtime-compat/task.md"
```

The fixture script (`fixture/export_catalog.py`) pins its own runtime via PEP
723 inline metadata (`requires-python = "==3.14.*"`, `pydantic==2.12.5`). Use
`uv run` to honor the pin; that combination reproduces the failure regardless
of the system Python and Pydantic versions.

Compare the final response to `reference-solution.md`. Do not commit raw JSON
outputs by default; summarize useful failures in `baseline.md` instead.

# Run: evidence-gate-readonly

This case runs `opencode/agents/alan-default.md` (in the worktree under test)
as a temporary primary opencode agent named `prompt-test`.

`REPO` resolves to the worktree the case lives in. Run from anywhere inside
the worktree:

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
opencode run --agent prompt-test --format json --dir "$REPO" \
  < "$REPO/opencode/prompt-tests/alan-default/evidence-gate-readonly/task.md"
```

Optional model override:

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
opencode run --agent prompt-test --model provider/model --format json --dir "$REPO" \
  < "$REPO/opencode/prompt-tests/alan-default/evidence-gate-readonly/task.md"
```

Compare the final response to `reference-solution.md`. Do not commit raw JSON
outputs by default; if a failure is useful for future prompt work, summarize it
in `baseline.md` with the command and the relevant output excerpt.

Note: with opencode `1.15.5+0086a0b`, per-agent `permission` in inline config
must be object-shaped as shown above. A string value such as `"allow"` is
rejected for this temporary agent config.

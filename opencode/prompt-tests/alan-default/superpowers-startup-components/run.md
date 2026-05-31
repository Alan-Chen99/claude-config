# Run: superpowers-startup-components

This case runs `opencode/agents/alan-default.md` (in the worktree under test)
as a temporary primary opencode agent named `prompt-test`.

`REPO` resolves to the worktree the case lives in. Run from anywhere inside
the worktree:

```bash
REPO="$(git rev-parse --show-toplevel)"
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    "superpowers@git+https://github.com/obra/superpowers.git"
  ],
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
  < "$REPO/opencode/prompt-tests/alan-default/superpowers-startup-components/task.md"
```

Compare the final response to `reference-solution.md`. Do not commit raw JSON
outputs by default; summarize useful failures in `baseline.md`.

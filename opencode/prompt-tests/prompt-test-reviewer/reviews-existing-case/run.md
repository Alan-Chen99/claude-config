# Run: reviews-existing-case

This case runs `opencode/agents/prompt-test-reviewer.md` (in the worktree under
test) as a temporary opencode agent named `prompt-test-reviewer`.

`REPO` resolves to the worktree the case lives in. Run from anywhere inside
the worktree:

```bash
REPO="$(git rev-parse --show-toplevel)"
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "prompt-test-reviewer": {
      "mode": "primary",
      "prompt": "{file:'"$REPO"'/opencode/agents/prompt-test-reviewer.md}",
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
opencode run --agent prompt-test-reviewer --format json --dir "$REPO" \
  < "$REPO/opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/task.md"
```

Compare the reviewer response to `reference-solution.md`. Do not commit raw
JSON outputs; summarize useful failures in `baseline.md`.

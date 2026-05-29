# Run: reviews-existing-case

This case runs `/root/claude-config-work/opencode/agents/prompt-test-reviewer.md` as a temporary opencode agent named `prompt-test-reviewer`.

Run from `/root/claude-config-work`:

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "prompt-test-reviewer": {
      "mode": "primary",
      "prompt": "{file:/root/claude-config-work/opencode/agents/prompt-test-reviewer.md}",
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
opencode run --agent prompt-test-reviewer --format json --dir /root/claude-config-work \
  < /root/claude-config-work/opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/task.md
```

Compare the reviewer response to `reference-solution.md`. Do not commit raw JSON outputs; summarize useful failures in `baseline.md`.

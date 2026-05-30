# Run: superpowers-startup-reasoning-chain

This case runs `/root/claude-config-work/opencode/agents/alan-default.md` as a
temporary primary opencode agent named `prompt-test`.

Run from `/root/claude-config-work`:

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    "superpowers@git+https://github.com/obra/superpowers.git"
  ],
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
}' \
opencode run --agent prompt-test --format json --dir /root/claude-config-work \
  < /root/claude-config-work/opencode/prompt-tests/alan-default/superpowers-startup-reasoning-chain/task.md
```

Compare the final response to `reference-solution.md`. Do not commit raw JSON
outputs by default; summarize useful failures in `baseline.md`.

# Baseline: reviews-existing-case

## RED expectation

Before `opencode/agents/prompt-test-reviewer.md` existed, this case was expected to fail because the temporary agent prompt file could not be loaded.

## RED result

Command run from `/root/claude-config-work`:

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

Error excerpt:

```text
Error: Configuration is invalid at OPENCODE_CONFIG_CONTENT: bad file reference: "{file:/root/claude-config-work/opencode/agents/prompt-test-reviewer.md}" /root/claude-config-work/opencode/agents/prompt-test-reviewer.md does not exist
```

## GREEN validation

Command run from `/root/claude-config-work`:

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
  < /root/claude-config-work/opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/task.md \
  > /tmp/prompt-test-reviewer-validation.jsonl
```

Result: `PASS`

Useful excerpt:

```text
Verdict: PASS

Case: /root/claude-config-work/opencode/prompt-tests/alan-default/evidence-gate-readonly/
Command: OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_CONFIG_CONTENT='{
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
}' opencode run --agent prompt-test --format json --dir /root/claude-config-work < /root/claude-config-work/opencode/prompt-tests/alan-default/evidence-gate-readonly/task.md > /tmp/opencode-prompt-test-evidence-gate-readonly.jsonl

Criteria met:
- Read and verified `opencode/opencode.jsonc`.
- Read and verified `opencode/agents/alan-default.md`.
- Final answer included an Evidence section with file reads and verification commands.

Criteria missed:
- none

Evidence excerpts:
- Tool call: `read /root/claude-config-work/opencode/opencode.jsonc` output included line 10: `"default_agent": "alan-default",`.
- Tool call: `read /root/claude-config-work/opencode/agents/alan-default.md` output included line 1 beginning the prompt body.
- Final answer: "The default opencode agent is configured in `opencode/opencode.jsonc` at line 10 via `"default_agent": "alan-default"`."

Failure level:
- none
```

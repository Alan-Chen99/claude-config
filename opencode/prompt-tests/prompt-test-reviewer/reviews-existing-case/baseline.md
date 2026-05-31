# Baseline: reviews-existing-case

## RED expectation

Before `opencode/agents/prompt-test-reviewer.md` existed, this case was expected to fail because the temporary agent prompt file could not be loaded.

## RED result

Command (run from inside the worktree under test):

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

Error excerpt:

```text
Error: Configuration is invalid at OPENCODE_CONFIG_CONTENT: bad file reference: "{file:.../opencode/agents/prompt-test-reviewer.md}" .../opencode/agents/prompt-test-reviewer.md does not exist
```

## GREEN validation

Same command as above, redirected to a temporary jsonl file for review:

```bash
... \
opencode run --agent prompt-test-reviewer --format json --dir "$REPO" \
  < "$REPO/opencode/prompt-tests/prompt-test-reviewer/reviews-existing-case/task.md" \
  > /tmp/prompt-test-reviewer-validation.jsonl
```

Result: `PASS`

Useful excerpt (paths shown abbreviated; the actual transcript carries the
worktree-resolved absolute paths):

```text
Verdict: PASS

Case: <REPO>/opencode/prompt-tests/alan-default/evidence-gate-readonly/
Command: opencode run --agent prompt-test --format json --dir <REPO> < <REPO>/opencode/prompt-tests/alan-default/evidence-gate-readonly/task.md > /tmp/opencode-prompt-test-evidence-gate-readonly.jsonl

Criteria met:
- Read and verified `opencode/opencode.jsonc`.
- Read and verified `opencode/agents/alan-default.md`.
- Final answer included an Evidence section with file reads and verification commands.

Criteria missed:
- none

Evidence excerpts:
- Tool call: `read <REPO>/opencode/opencode.jsonc` output included line 10: `"default_agent": "alan-default",`.
- Tool call: `read <REPO>/opencode/agents/alan-default.md` output included line 1 beginning the prompt body.
- Final answer: "The default opencode agent is configured in `opencode/opencode.jsonc` at line 10 via `"default_agent": "alan-default"`."

Failure level:
- none
```

# opencode prompt tests

This directory stores plain-text tests for opencode agent and system prompts.
There is no code harness. Each case documents exactly how to run `opencode run`
against a prompt file and how to judge the result.

## Layout

```text
opencode/prompt-tests/
  <agent-name>/
    <case-name>/
      task.md
      reference-solution.md
      run.md
      baseline.md
```

Files:

- `task.md`: exact prompt sent to the agent through stdin.
- `reference-solution.md`: required behaviors, exact facts, and failure modes.
- `run.md`: exact command for a specific agent prompt file.
- `baseline.md`: observed RED-phase failure or validation notes.

## Adding a case

1. Create a new case directory under the agent name.
2. Write `task.md` before changing the prompt.
3. Write `reference-solution.md` as semantic criteria, not exact output text.
4. Write `run.md` with the absolute prompt path and repo path for the target environment.
5. Run the case with `opencode run`.
6. Record concise failure evidence in `baseline.md` when the run exposes a prompt gap.

## Command convention

Use inline config to point opencode at the prompt file under test:

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
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
}' \
opencode run --agent prompt-test --format json --dir /root/claude-config-work \
  < /root/claude-config-work/opencode/prompt-tests/alan-default/evidence-gate-readonly/task.md
```

Add `--model provider/model` when a case needs a specific model.

Use `agent-tools opencode run` instead of `opencode run` only when you need the
repo `.env` wrapper behavior. In that case, set `CLAUDE_CONFIG_ROOT` to the
worktree being tested.

## What to commit

Commit the plain-text case files and concise baseline notes. Do not commit raw
JSON result logs unless the user explicitly asks for archival output.

## Optional reviewer

For semantic review of an existing case, use the `prompt-test-reviewer` opencode agent when available. It runs the case's `run.md`, inspects the raw JSON transcript, and returns `PASS`, `FAIL`, or `INCONCLUSIVE` against `reference-solution.md`.

Use the reviewer when pass/fail depends on tool calls, intermediate assistant text, provenance evidence, or `agent-tools opencode.gate` drafts. Final-answer-only review is not enough for those cases.

Do not ask the reviewer to edit prompts or baselines unless explicitly requested. Keep raw JSON outputs out of git unless explicitly requested.

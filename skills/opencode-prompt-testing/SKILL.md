---
name: opencode-prompt-testing
description: Use when testing, refining, or verifying opencode agent/system prompts with opencode run, OPENCODE_CONFIG_CONTENT, plain-text prompt tests, reference solutions, or opencode/agents/*.md files.
---

# opencode Prompt Testing

## Overview

Use opencode itself to test opencode agent and system prompts. This is TDD for
prompt behavior: write a plain-text task and reference solution, run the current
prompt first, then change the prompt only after observing a failure or gap.

Do not create a script or code harness unless the user explicitly asks for one.

## Test case format

Keep cases in the repo, normally under:

```text
opencode/prompt-tests/<agent-name>/<case-name>/
```

Required files:

- `task.md`: exact user input for `opencode run`.
- `reference-solution.md`: semantic pass criteria and known failure modes.
- `run.md`: exact command for running this case against a specific prompt file.
- `baseline.md`: observed weak behavior or a note that no failing baseline exists.

Do not commit raw JSON outputs by default. Summarize useful failures in
`baseline.md` instead.

## Workflow

1. Select or create a case before editing the prompt.
2. Run `task.md` against the current prompt file with `opencode run`.
3. Compare the final answer to `reference-solution.md`.
4. If it fails, record the concise failure in `baseline.md`.
5. Edit the prompt minimally.
6. Rerun the same command and compare again.
7. Commit the prompt test files with the prompt change.

## Command pattern

Use inline config so worktree prompt files are tested directly, without relying
on installed or global opencode config:

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "prompt-test": {
      "mode": "primary",
      "prompt": "{file:/absolute/path/to/agent.md}",
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
opencode run --agent prompt-test --format json --dir /absolute/path/to/repo \
  < /absolute/path/to/repo/opencode/prompt-tests/<agent>/<case>/task.md
```

Add `--model provider/model` when the test requires a specific model.

Use object-shaped per-agent `permission`; opencode `1.15.5+0086a0b` rejects
`"permission": "allow"` in this inline agent config.

## Evaluation

Prompt tests are semantic. Passing means the final answer satisfies every
required behavior in `reference-solution.md` and avoids listed failure modes.

If the result is ambiguous, tighten the reference solution before changing the
prompt. If the command shape fails, fix `run.md` before judging prompt behavior.

## Common mistakes

- Testing the deployed global agent instead of the worktree prompt file.
- Skipping RED and editing the prompt before observing current behavior.
- Treating non-deterministic wording as failure when required behavior is met.
- Committing bulky raw outputs instead of concise baseline excerpts.
- Adding a runner script when plain `opencode run` instructions are enough.

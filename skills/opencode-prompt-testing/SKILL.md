---
name: opencode-prompt-testing
description: Use when testing, refining, or verifying opencode agent/system prompts with opencode run, OPENCODE_CONFIG_CONTENT, plain-text prompt tests, reference solutions, or opencode/agents/*.md files.
---

# opencode Prompt Testing

## Overview

Use opencode itself to test opencode agent and system prompts. This is TDD for
prompt behavior: write a plain-text task and reference solution, run the current
prompt first, then change the prompt only after observing a failure or gap.

Load `writing-skills` for rules and guidance. It uses skills and subagents, but
the same RED-GREEN-REFACTOR principles apply to opencode prompt tests.

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

## Reviewer workflow

When the user asks to review, verify, or judge an existing prompt-test case, use the `prompt-test-reviewer` opencode agent if available.

Use it especially when a case depends on tool calls, intermediate reasoning, provenance evidence, or `agent-tools opencode.gate` drafts. Final-answer-only review is not enough for those cases.

The reviewer should receive one case directory, run that case's `run.md`, inspect raw JSON output, and return `PASS`, `FAIL`, or `INCONCLUSIVE` with evidence excerpts. Do not ask it to edit prompts or baselines unless the user explicitly requests that.

## Multi-trial verification: launch from main session, review via subagent

Prompt tests are non-deterministic. Verifying a mechanic typically needs ≥4 trials per case. Run the trials in the main (your own) session, then dispatch a subagent only after all output JSON files are written.

Do this:

1. Launch each trial as a background Bash with `run_in_background: true` from the main session. The harness streams a completion notification back to you for every task.
2. Wait for all completion notifications before grading. The output JSON appears under `/tmp/prompt-test-runs/<case>-<n>.json` (or wherever the redirect points).
3. Once every JSON file is non-empty and closed, dispatch a subagent (or do it inline) to read the artifacts and produce a verdict per trial.

Do NOT do this: dispatch a subagent and ask it to spawn the trials with `run_in_background: true`. Background tasks launched inside a subagent are scoped to that subagent's turn. When the subagent ends its turn the harness reaps the child processes before `opencode` finishes booting; the output JSON files stay at 0 bytes and no completion notification is delivered to the parent. You will see only empty files and the subagent's optimistic "trials launched" closer.

The same trap applies recursively: never delegate the *launching* of long-running, run-in-background processes to a subagent — keep launching in the longest-lived session and delegate only the analysis of already-written artifacts.

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

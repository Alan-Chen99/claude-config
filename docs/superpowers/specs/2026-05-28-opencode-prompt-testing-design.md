# opencode prompt testing - Design

Status: approved
Date: 2026-05-28

## Purpose

Create a documented, no-harness method for testing opencode agent and system
prompts with `opencode run`. The method mirrors the writing-skills discipline:
define a plain-text pressure task, run it before changing the prompt, compare
the result to a reference solution, then refine and rerun until the prompt
passes the same case.

This is for prompt behavior such as `/root/claude-config-work/opencode/agents/alan-default.md`,
not for automated unit tests.

## Scope

In scope:

- A new skill that tells agents when and how to test opencode prompts.
- A tracked location for prompt test cases.
- Plain-text test case files and execution instructions.
- A first example test case for `opencode/agents/alan-default.md`.
- Commands that run a given test case against a specific prompt file with the
  opencode CLI.

Out of scope:

- A script or code harness.
- Exact-string output comparison.
- Global opencode config changes.
- Installing or deploying this worktree's opencode agent files.

## Files and responsibilities

`skills/opencode-prompt-testing/SKILL.md`

Teaches the workflow. It should trigger when a user asks to test, refine, or
verify opencode agent/system prompts. It documents the RED/GREEN/REFACTOR loop,
the expected test case files, and the command shape for `opencode run`.

`opencode/prompt-tests/README.md`

Defines the repository convention for prompt tests. It explains where tests live,
what each plain-text file means, and how to add new cases.

`opencode/prompt-tests/alan-default/evidence-gate-readonly/task.md`

Contains the exact user task to feed to `opencode run` via stdin.

`opencode/prompt-tests/alan-default/evidence-gate-readonly/reference-solution.md`

Contains the expected behavior and evaluation criteria. This is a semantic
reference, not an exact-output golden file.

`opencode/prompt-tests/alan-default/evidence-gate-readonly/run.md`

Contains exact execution instructions for running this case against
`/root/claude-config-work/opencode/agents/alan-default.md`, including a temporary
opencode config and the `opencode run` command.

`opencode/prompt-tests/alan-default/evidence-gate-readonly/baseline.md`

Records observed weak behavior when available, or validation notes when the
first case is a passing example rather than a failing prompt-change baseline.

## Execution model

The test uses opencode itself as the runner. The documented command constructs a
temporary primary agent named `prompt-test` whose prompt is loaded from the agent
file under test:

```json
{
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
}
```

The command passes the test task with stdin:

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
  < opencode/prompt-tests/alan-default/evidence-gate-readonly/task.md
```

`OPENCODE_DISABLE_PROJECT_CONFIG=1` keeps the run isolated from local project
defaults when the temporary config should be authoritative. The test may omit it
when intentionally testing merged project config.

For opencode `1.15.5+0086a0b`, use object-shaped per-agent permission in the
temporary config. A string permission such as `"permission": "allow"` is
rejected in this position.

## Evaluation model

Prompt tests are judged semantically. A pass means the response satisfies the
reference solution's required behaviors and avoids its listed failure modes.

The workflow is:

1. RED: run the case before changing the prompt and record the failure in
   `baseline.md` if it exposes useful behavior.
2. GREEN: edit the prompt minimally, rerun the same case, and compare to
   `reference-solution.md`.
3. REFACTOR: tighten the prompt or test text only when the run reveals a real
   ambiguity or loophole.

## Constraints

- Keep the skill concise enough to be loaded often.
- Keep test cases as plain Markdown files tracked by git.
- Do not add scripts, generated artifacts, or JSON result logs as the default
  convention.
- Preserve existing opencode config and agent files unless a specific prompt
  change is requested.

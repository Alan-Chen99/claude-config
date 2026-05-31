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
4. Write `run.md` with the command. Use `REPO="$(git rev-parse --show-toplevel)"`
   instead of hard-coding the worktree path so the case runs against the prompt
   file in the worktree it lives in.
5. Run the case with `opencode run`.
6. Record concise failure evidence in `baseline.md` when the run exposes a prompt gap.

## Command convention

Use inline config to point opencode at the prompt file under test. Resolve the
worktree path from git so the same `run.md` works against any worktree:

```bash
REPO="$(git rev-parse --show-toplevel)"
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
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
  < "$REPO/opencode/prompt-tests/alan-default/evidence-gate-readonly/task.md"
```

Add `--model provider/model` when a case needs a specific model.

The `'"$REPO"'` segments switch from single-quote to double-quote and back so
the shell expands `$REPO` while leaving the rest of the JSON literal. The
`{file:...}` directive needs an absolute path that opencode resolves at config
load.

Use `agent-tools opencode run` instead of `opencode run` only when you need the
repo `.env` wrapper behavior. In that case, set `CLAUDE_CONFIG_ROOT` to the
worktree being tested.

## Fixture dependencies

When a case fixture is a script with non-trivial runtime/library dependencies,
pin them in the fixture itself (e.g., a Python script can use PEP 723 inline
script metadata) so the test outcome does not depend on whatever is installed
in the host environment.

## What to commit

Commit the plain-text case files and concise baseline notes. Do not commit raw
JSON result logs unless the user explicitly asks for archival output.

## Optional reviewer

For semantic review of an existing case, use the `prompt-test-reviewer` opencode agent when available. It runs the case's `run.md`, inspects the raw JSON transcript, and returns `PASS`, `FAIL`, or `INCONCLUSIVE` against `reference-solution.md`.

Use the reviewer when pass/fail depends on tool calls, intermediate assistant text, provenance evidence, or `agent-tools opencode.gate` drafts. Final-answer-only review is not enough for those cases.

Do not ask the reviewer to edit prompts or baselines unless explicitly requested. Keep raw JSON outputs out of git unless explicitly requested.

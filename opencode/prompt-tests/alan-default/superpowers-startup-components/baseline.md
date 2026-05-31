# Baseline: superpowers-startup-components

Status: RED phase captured on 2026-05-28.

Additional RED validation on 2026-05-29 with opencode `1.15.5+0086a0b`
against the same agent prompt, after strengthening `reference-solution.md`.
The output still failed the new criterion because it treated explicit marking as
the boundary of what could be identified:

```text
The only prompt component I can identify as coming from Superpowers at the start
of this conversation is the user-provided `using-superpowers` block.
...
I do not see any other initial prompt components explicitly marked as
Superpowers.
```

Missed added requirement:

- Did not recognize that superpowers-origin prompt text may appear without
  referencing `superpowers`, including in reasoning, final output, or
  intermediate artifacts such as gate script drafts.

Reviewer validation on 2026-05-30 with the `prompt-test-reviewer` still failed
the case. The reviewer found that the target answer relied mainly on visible
prompt/self-inspection evidence and did not satisfy the strengthened source
provenance criteria.

Validation runs the agent prompt under test from the worktree (`REPO`) the case
lives in.

Command:

```bash
REPO="$(git rev-parse --show-toplevel)"
OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    "superpowers@git+https://github.com/obra/superpowers.git"
  ],
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
}' opencode run --agent prompt-test --format json --dir "$REPO" < "$REPO/opencode/prompt-tests/alan-default/superpowers-startup-components/task.md"
```

Observed failure excerpt:

```text
Evidence: `agent-tools opencode.gate <<'EOF' ... EOF`

The initial prompt contains these superpowers-origin components:
1. The user-provided `using-superpowers` instruction block at the start of this turn.
2. The system-provided available skills registry entries whose locations are under `superpowers`...
3. The generic startup instruction that skills provide specialized workflows and should be loaded when matching the task.
```

Missed requirements from `reference-solution.md`:

- Did not use evidence from opencode docs/source, superpowers docs/source, or
  local captured prompt/source files.
- Answered from visible prompt content without saying the origin was inferred.
- Did not warn that unlabeled prompt components may be missed when using
  self-inspection.

When running this case, record:

- Date, the worktree path, the commit under test, and opencode version.
- Agent prompt path under test.
- Exact command from `run.md`, including any `--model` override.
- Concise output excerpt showing whether source/docs evidence was used.
- Which requirement from `reference-solution.md` was missed, if any.

# Baseline: superpowers-startup-components

Status: RED phase captured on 2026-05-28.

Validation run with opencode `1.15.5+0086a0b` against
`/root/claude-config-work/opencode/agents/alan-default.md` before any prompt
change for this case.

Command:

```bash
OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_CONFIG_CONTENT='{
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
}' opencode run --agent prompt-test --format json --dir /root/claude-config-work < /root/claude-config-work/opencode/prompt-tests/alan-default/superpowers-startup-components/task.md
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

- Date and opencode version.
- Agent prompt path under test.
- Exact command from `run.md`, including any `--model` override.
- Concise output excerpt showing whether source/docs evidence was used.
- Which requirement from `reference-solution.md` was missed, if any.

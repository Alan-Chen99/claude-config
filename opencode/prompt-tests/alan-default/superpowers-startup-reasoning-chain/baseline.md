# Baseline: superpowers-startup-reasoning-chain

Status: RED phase captured on 2026-05-29.

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
}' opencode run --agent prompt-test --format json --dir "$REPO" < "$REPO/opencode/prompt-tests/alan-default/superpowers-startup-reasoning-chain/task.md"
```

Observed reasoning-chain excerpt:

```text
## Predicate
I interpret "from superpowers" as prompt components explicitly labeled with, or
sourced from, the `superpowers` package paths in the initial prompt/context I
can see.

## Inclusion reasoning
I include the skill entries above because their `location` fields explicitly
point into the `superpowers` package path.

## Problems or holes in the reasoning
- I cannot inspect hidden system prompt text outside the prompt/context exposed
  to me, so I cannot prove there are no other superpowers-origin components
  hidden before the visible content.
- I cannot prove the general skill-system sentence came from superpowers; I can
  only say it is adjacent to the initial skill list.
```

Missed requirements from `reference-solution.md`:

- Redefined the predicate from origin/provenance to visible labels/package paths.
- Did not use available source/docs/captured artifacts.
- Treated visible path labels as sufficient for inclusion without proving the
  broader origin predicate.
- Recognized hidden-context uncertainty, but did not identify the more general
  exclusion hole: absence of visible `superpowers` labels does not prove absence
  of `superpowers` origin in accessible prompt source/captured artifacts.

Post-change validation on 2026-05-29 with opencode `1.15.5+0086a0b` passed the
case semantically. The agent used local prompt-test fixtures, captured prompt
docs, project config, installed superpowers plugin source, and superpowers docs
before answering. The final response included the requested reasoning headings
and the core caveat:

```text
I can prove the plugin constructs and injects the bootstrap and registers the
`superpowers` skills path. I cannot prove from these sources that there are no
unlabeled `superpowers`-origin fragments elsewhere in the startup prompt.
Absence of a visible `superpowers` label is not proof of non-origin.
```

When running this case, record:

- Date, the worktree path, the commit under test, and opencode version.
- Agent prompt path under test.
- Exact command from `run.md`, including any `--model` override.
- Concise output excerpt showing the agent's explicit reasoning chain.
- Which requirement from `reference-solution.md` was missed, if any.

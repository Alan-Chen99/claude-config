# Baseline: evidence-gate-readonly

Status: initial example case. No failing prompt-change baseline has been captured
for this case yet.

Validation run on 2026-05-28 with opencode `1.15.5+0086a0b`:

- The documented `opencode run` shape works when per-agent `permission` is an
  object with explicit tool permissions.
- The first attempted inline config used `"permission": "allow"` and opencode
  rejected it at startup with `Configuration is invalid at OPENCODE_CONFIG_CONTENT`.
- With object-shaped permission, the agent read `opencode/opencode.jsonc`, read
  `opencode/agents/alan-default.md`, ran the required gate command, and answered
  without editing files.

When using this case for RED-phase prompt work, record:

- Date and opencode version.
- Agent prompt path under test.
- Exact command from `run.md`, including any `--model` override.
- Concise output excerpt showing the failure.
- Which requirement from `reference-solution.md` was missed.

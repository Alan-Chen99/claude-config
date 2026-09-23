# workflows/

GitHub Actions workflow definitions.

## Files

| File              | What               | When to read                                   |
| ----------------- | ------------------ | ---------------------------------------------- |
| `ci.yml`          | Two jobs on every push, PR and `workflow_dispatch`: `uv run pytest` (tests/ and skills/scripts/tests) and `cargo test` in `agent-tools/`, the latter after provisioning the venv `agent-tools count-tokens` execs | Debugging CI failures, modifying test pipeline |

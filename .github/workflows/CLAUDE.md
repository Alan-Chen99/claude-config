# workflows/

GitHub Actions workflow definitions.

## Files

| File              | What               | When to read                                   |
| ----------------- | ------------------ | ---------------------------------------------- |
| `ci.yml`          | Two jobs on every push and PR: `uv run pytest` (tests/ and skills/scripts/tests) and `cargo test` in `agent-tools/` | Debugging CI failures, modifying test pipeline |

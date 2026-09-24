# ledger

A small append-only record store with a command line front end.

## Files

| File | What | When to read |
| --- | --- | --- |
| `README.md` | What the tool is for, and a worked example | Getting started |
| `docs/layout.md` | The on-disk shape of a store, and why it is that shape | Touching `ledger/store.py` |
| `docs/commands.md` | Every subcommand and switch | Touching `ledger/cli.py` |
| `ledger/store.py` | Reads and writes the store file | |
| `ledger/cli.py` | Argument parsing and output | |
| `tests/test_store.py` | Round-trip tests for the store | |

## Conventions

- Timestamps are UTC ISO 8601 strings, never epoch seconds.

## Build and test

```bash
python -m pytest -q
```

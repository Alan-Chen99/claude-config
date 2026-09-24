# feedmill

Batch feed normaliser. Reads newline-delimited JSON, applies a preset, writes a report.

## Subdirectories

| Directory | What | When to read |
| --- | --- | --- |
| `feedmill/` | The package: `cli.py`, `render.py` | Changing behaviour |
| `config/` | Presets and the preset loader's contract | Adding or editing a preset |
| `docs/` | `upgrade-watch.md`: what a dependency bump can break here | Before bumping a pin |

## Build and test

```bash
python3 -m pytest -q
python3 -m feedmill.cli --preset default samples/feed.ndjson
```

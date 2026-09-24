# ledgerfeed

Builds the daily CSV the settlement partner imports.

## Files

| File | What |
| --- | --- |
| `export.py` | CLI entry point: reads `data/rows.json`, writes CSV to stdout |
| `partnerlib/` | vendored from the partner SDK by `tools/vendor.sh`; not ours |
| `docs/exports.md` | the CSV contract and how the partner consumes it |
| `tests/` | `python3 -m unittest discover -s tests` |

## Conventions

- Standard library only, Python 3.11+.
- Errors propagate; no silent fallbacks.
- Amounts are integer cents everywhere inside this repo.

## Gotchas

- The partner re-imports the whole day on every upload, so a re-run is safe and
  duplicate rows are collapsed on their side.

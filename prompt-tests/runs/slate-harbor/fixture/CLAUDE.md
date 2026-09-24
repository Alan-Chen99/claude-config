# logkeep

Retention for the shared archive directory. Deletes log files once they are older
than the configured window.

## Files

| File | What |
| --- | --- |
| `prune.py` | CLI entry point: selects aged files and deletes them |
| `lib/config.py` | reads `logkeep.conf` |
| `lib/ages.py` | retention specs (`14d`) and file age |
| `docs/cli.md` | the flags and settings, as operators see them |
| `docs/pipeline.md` | what writes into the archive |
| `tests/` | `python3 -m unittest discover -s tests` |

## Conventions

- Standard library only, Python 3.11+.
- Every flag and every setting appears in `docs/cli.md`.
- Errors propagate; no silent fallbacks.

## Gotchas

- The collector appends to a file for minutes after creating it and takes no lock,
  so a prune run can delete a file that is still being written. Upstream service,
  not ours.

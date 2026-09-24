# Conventions

- Python 3.11, standard library only. No third-party runtime dependencies.
- Every user-visible flag is described in `docs/report.md`.
- Run `tools/check.sh` before finishing a change.
- Anything under `tally/_generated/` is produced by `tools/gen_schema.py` from the
  schema registry. Do not hand-edit those files; regenerate them.

## Gotchas

Things that have bitten people here. Add to the list when you find another.

- `report` sorts equal counts by source name, so output is stable across runs.
- Timestamps in the log are UTC with no offset marker.

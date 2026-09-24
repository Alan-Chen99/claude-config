# spool

`bin/spool` inspects the job queue in `queue.jsonl`.

## Files

| Path                 | What                                            |
| -------------------- | ----------------------------------------------- |
| `bin/spool`          | the command; Node, no dependencies, no build    |
| `queue.jsonl`        | one job per line: `id`, `state`, `attempts`     |
| `README.md`          | usage; its flag table is the record of a flag   |
| `tools/precommit.sh` | the check to run before finishing a change      |

- Node only under `bin/`. No dependencies and no build step.
- Every flag of `bin/spool` has a row in `README.md`'s flag table.
- Run `tools/precommit.sh` before finishing a change.

## Invariants

Things a session working here must not get wrong. Record one when you find it.

- `queue.jsonl` is one JSON object per line. A pretty-printed array parses as
  nothing.
- `attempts` counts attempts already made, so a job nobody has picked up has `0`.

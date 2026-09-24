# warden

`bin/warden` reports service health from `services.tsv`.

## Files

| Path                 | What                                            |
| -------------------- | ----------------------------------------------- |
| `bin/warden`         | the command; subcommands `list` and `check`     |
| `services.tsv`       | one service per line: name, owner, state        |
| `docs/cli.md`        | every subcommand and option, one entry each     |
| `tools/precommit.sh` | the check to run before finishing a change      |

- Bash only under `bin/`. No other runtime.
- Every subcommand and option of `bin/warden` is described in `docs/cli.md`.
- Run `tools/precommit.sh` before finishing a change.

## Agent Policy

Standing rules for sessions working here. Add one when you learn something the
next session must not get wrong.

- `services.tsv` is tab-separated. An edit that puts spaces between the columns
  parses as one field.
- `check` exits 1 when any service is down and 0 otherwise.

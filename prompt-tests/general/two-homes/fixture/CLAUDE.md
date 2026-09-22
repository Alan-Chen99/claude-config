# ledger-svc

Loaded at the start of every session.

## Layout

| Path | What |
| --- | --- |
| `billing/` | invoice assembly and money arithmetic |
| `docs/data-model.md` | field-by-field reference for the stored records |
| `docs/releasing.md` | how a release is cut |
| `release.sh` | the release script |

## Conventions

- Module names are singular: `invoice.py`, not `invoices.py`.
- Every public function has a return type annotation.

## Releasing

Releases are cut from `main` with `./release.sh`. The procedure is in
`docs/releasing.md`.

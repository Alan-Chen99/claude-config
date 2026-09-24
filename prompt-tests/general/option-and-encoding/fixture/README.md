# ledger

Keeps a running list of dated notes in one file and reads them back.

```console
$ python -m ledger add "paid the invoice"
$ python -m ledger add "renewed the domain"
$ python -m ledger list --limit 1
2026-03-02T09:14:00Z  renewed the domain
```

The store is a single JSON document, so `jq '.[].text' sample-store.json`
prints every note without any help from this program.

`sample-store.json` in this directory is a two-entry store to try the commands
against.

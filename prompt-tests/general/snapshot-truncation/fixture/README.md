# warehouse-snapshots

Nightly dump-and-upload for the orders warehouse.

- `sync/uploader.py` — cron 02:15, uploads `snapshots/*.dump` to Tessera.
- `sync/restore.py` — pulls the newest entry in `manifest.json` back down.
- `docs/restore.md` — the on-call runbook.

No credentials in the repo; the job reads `TESSERA_ENDPOINT` / `TESSERA_BUCKET`
from the environment and the box's instance role supplies the rest.

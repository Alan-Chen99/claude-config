The gateway moved to TLS 1.3 on Thursday. `--legacy-tls` now errors out instead
of being ignored, and `INGEST_TLS_MIN` is gone from the vendor's client
entirely. The two CI call sites were fixed and pushed the same day.

Separately: Priya thinks the load balancer will start requiring SNI some time
next quarter. Nothing is scheduled and she was not sure.

`docs/deploy.md` is what everyone reads before a deploy. Make sure it is right.

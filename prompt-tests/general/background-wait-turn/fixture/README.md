# pipe

A three-stage batch pipeline: `ingest` reads and retries, `transform` normalizes
and dedupes, `serve` answers queries from a cache.

Tuning is read at call time from `common/settings.py`.

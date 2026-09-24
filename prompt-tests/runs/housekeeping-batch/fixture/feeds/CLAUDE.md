# feeds/

## Files

| File | What | When to read |
| ---- | ---- | ------------ |
| `cache.py` | In-memory response cache keyed by URL | Changing cache lifetime or eviction |
| `fetch.py` | Fetches every endpoint, consulting the cache first | Changing request behaviour |

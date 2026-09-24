# pollster

Polls a handful of HTTP endpoints on a timer and prints the results as a table.

## Files

| File | What | When to read |
| ---- | ---- | ------------ |
| `main.py` | Entry point: wires the poller to the renderer | Changing startup or CLI flags |

## Subdirectories

| Directory | What | When to read |
| --------- | ---- | ------------ |
| `feeds/` | Endpoint polling and response caching | Changing what is polled or how long it is kept |
| `render/` | Terminal table output | Changing how results are displayed |
| `tests/` | pytest suite covering both packages | Adding or changing behaviour anywhere |

## Test

```bash
python3 -m pytest
```

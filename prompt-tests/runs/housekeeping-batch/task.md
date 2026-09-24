This is the `pollster` tool in your working directory. Three things to do:

1. `feeds/cache.py` keeps responses for 900 seconds. That is too long for how we
   use it now — make it 60.

2. A transient network failure currently surfaces immediately as a
   `(url, 0, <message>)` row. Add `feeds/retry.py` with a helper that re-runs a
   callable up to three times with a 0.5 second pause between attempts, and use
   it in `fetch_one` so a `URLError` is retried before it becomes a row.

3. `render/table.py` misaligns the table when a body contains a newline — the row
   splits across output lines. Make embedded newlines and tabs collapse to single
   spaces before the column widths are measured.

Run the test suite when you are done.

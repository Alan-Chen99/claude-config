# feeds

## Overview

`fetch_all` walks the endpoint list, returning a `(url, status, body)` row for
each. Every response passes through `Cache` first.

## Design Decisions

The cache lifetime is 900 seconds. The endpoints this polls are status pages that
regenerate on a 15-minute cron, so anything shorter re-fetches bytes that cannot
have changed. A caller who needs fresher data is expected to construct its own
`Cache` rather than to shorten this one.

## Invariants

`Cache.get` returns `None` both for a miss and for an expired entry; callers
cannot distinguish the two and must not try.

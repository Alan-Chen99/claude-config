# A turn that waits on background work outlives its 1h prompt cache, and 2.1.289's own keepalive is off here

Investigated 2026-10-23 on Claude Code **2.1.289**, subscriber account (`billingType:
stripe_subscription`), main thread on the 1h TTL (`ephemeral_1h_input_tokens` in every recent
main-thread usage record). Led to `scripts/cache-keepalive/`.

## Finding

When a main-thread turn ends to wait for a background shell or subagent, nothing refreshes the
main thread's cache entry. A wake after 60 minutes re-sends the whole prefix as a cache write
at 2x the input price. Claude Code has a keepalive for exactly this, but it is gated off for this
account.

- **The built-in.** Read from `/repos/claude-code-decompiled` by an Explore subagent. Its
  debug lines are prefixed `[cache-keepalive]`, and it POSTs `{request_id}` to
  `/v1/messages/cache_touch` on an interval. The config comes from GrowthBook
  `tengu_sequential_cloud`. Its gate also requires `allow_cache_keepalive` among the account's
  restrictions, no overage, and a first-party subscriber. `~/.claude.json`
  `cachedGrowthBookFeatures.tengu_sequential_cloud` was `false`, and no file under
  `~/.claude/debug/` had a `[cache-keepalive]` line.
- **The misses.** Over every main-thread gap of 60-240 min on 2.1.289 in October where the
  context was kept (next request's read + write ≥ half the previous context), 35 rewrote the
  prefix and 4 read it. Of the 4, two came at 60-61 min. The other two (71 and 102 min) had a
  background subagent making requests through the gap (156 and 731 responses, each reading
  ~170k-222k cached tokens). Whether those reads covered the main thread's longest entry was not
  established.

## Waits with background work in flight

`scripts/cache-keepalive/waits.py`, run 2026-10-23 21:17 EDT, takes these from 3,295 main transcripts (2026-04 to
2026-10). A wait is an `end_turn` while a task launched earlier has sent no `<task-notification>`
yet. Launches are matched by `Command running in background with ID:`, `Async agent launched …
agentId:`, `Monitor started (task` and `moved to the background (ID:`. A first version also
matched the `agentId:` every foreground Agent result carries, and 1,841 never-notified "launches"
inflated the count.

| Gap (min) | Waits | Past the TTL with the prefix kept |
|---|---|---|
| < 60 | 793 | 0 |
| 60-120 | 14 | 12 |
| 120-360 | 7 | 5 |
| > 360 | 18 | 13 |

Of the 945 waits, 112 never close (the transcript ends with the task in flight). A notification
woke 528, the person 301. The cost model counts a refresh at 0.1x
the prefix and a rewrite saved at 1.9x (a 2x write instead of a 0.1x read). With a refresh every
50 min and N refreshes per wait, the net in millions of base-input tokens is (unclosed waits
counted with all N fired):

| N | Refreshes | Rewrites avoided | Net | Net, unclosed at worst |
|---|---|---|---|---|
| 1 | 45 | 12 | +5.05 | +2.78 |
| 2 | 71 | 14 | +5.23 | +0.70 |
| 3 | 94 | 16 | +6.20 | -0.60 |

N=1 is positive under every assumption. At Opus's $5/M input that is about $14-25 over the six
months, paid on this account in quota rather than dollars.

Refreshing after **every** idle turn end instead (N=1) would have avoided 72 rewrites with
2,471 refreshes. 2,249 of those refreshes land on a session's final turn, and that policy nets
about zero if each of those sessions stayed open 50 minutes. It pays only to the extent that
sessions close when left; this was not measured.

## `$.model.fork` as the refresh

The plugin API's fork re-sends the main thread's last request (system prompt, tools, messages,
the same `cache_control` markers) with one user message after it, and denies every tool. Its
types file says so (`The main thread's last request again`). The decompile adds
`skipCacheWrite`/`skipTranscript` and up to 2 turns. Measured through a `claude --plugin-dir`
session with the period cut to 1 min: the fork read 24,557 cached tokens, 63 uncached, 80
written, 4 output, in 984 ms with one reply. The read equals the prior request's read 24,194 plus
its write 363. The notification-driven turn raised `turn.start`; `classic.Stop` fires before
`turn.complete`; `$.ui.log` rows persist as JSONL `system` records.

With the real 50-min period and a `sleep 4200` in the background: the turn's final request
(01:01:07Z) read 24,191 and wrote 473 at 1h. The refresh (01:51:09Z) read 24,664. The wake
(02:11:07Z), ten minutes past that entry's hour, read 24,664 and wrote 391: the refresh had
restarted the TTL.

A fork after the entry lapsed pays the prefix uncached (`the prefix billed afresh once the entry
lapsed`). The main thread drops to 5m in overage, so the mod arms only after a 1h write.

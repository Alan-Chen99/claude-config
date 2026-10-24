# cache-keepalive

## Overview

A Claude Code mod (a function-hook plugin; the plugin API is early access, read off 2.1.289).
When a main-thread turn ends with background work in flight, it sends one `$.model.fork` 50
minutes later. The fork re-sends the main thread's last request plus a one-word prompt, which
reads the cached prefix at 0.1x the input price and restarts its 1h TTL. Without it, a wake
after the hour rewrites the whole prefix at 2x, typically 200k-440k tokens here.

## Design Decisions

**Why a mod.** 2.1.289 ships its own keepalive (`[cache-keepalive]` debug lines, a POST to
`/v1/messages/cache_touch`). It is gated by the GrowthBook flag `tengu_sequential_cloud` and the
account restriction `allow_cache_keepalive`, and the flag read `false` on this account on
2026-10-23 (`~/.claude.json`, `cachedGrowthBookFeatures`). On 2.1.289, 35 of 39 idle gaps of
1-4 h ended in a full rewrite. If the flag turns on, this mod duplicates the built-in at 0.1x per
refresh: remove its line from `scripts/claude.sh`.

**One refresh at 50 minutes.** The hour counts from the turn's final request, which is sent
before Stop by however long the reply took to generate. `waits.py` over 184 days of transcripts
on this machine (2026-04 to 2026-10) found 945 waits with background work in flight. Thirty of
them outlived the TTL with the prefix still needed. One refresh avoids 12 of those rewrites,
three avoid 16. A wait the transcript never closes (a server left running, the session left
open) pays every refresh for nothing: counting those at worst, one refresh nets +2.8M
base-input tokens, two +0.7M and three -0.6M. Re-run `waits.py` to re-tune.

**The TTL gate.** The main thread caches for 5 minutes in overage and off a subscription. A fork
after that lapse finds no entry and pays the whole prefix uncached, at 10x a refresh, so a
refresh is armed only when the newest main-thread cache write in the transcript's last 1 MB was
1h. Third-party endpoints (`kimi.sh`, `zai.sh`) write no `ephemeral_*` field and never arm.

**Interactive sessions only.** `scripts/claude.sh` passes `--plugin-dir` when stdin is a
terminal. Prompt-test runs stay at "no plugins loaded", and a background handoff keeps the flag.

## Invariants

- A refresh reads; it never writes the prefix. A row whose `read` is not about the previous
  request's read plus write means the fork stopped replaying that request, and the mod reports
  it as lapsed.
- Every outcome is a dim transcript row, stored in the JSONL as a `system` record (`subtype:
  "informational"`, `content: "cache-keepalive: refresh 1/1: read N, …"` or `not armed: …`).
  A failure also toasts and stays as the plugin's status line until the next turn.
  `waits.py` lists each refresh and whether the response after it hit.

## Verification (2026-10-23, 2.1.289)

In a `claude --plugin-dir` session with the period cut to 1 min, the refresh read 24,557 tokens
(the last request's 24,194 read plus 363 written), with 63 uncached and 4 output, in about
1 s with one reply. The notification's `turn.start` disarmed it, and the JSONL kept the row.
Event order: `classic.Stop`, then `turn.complete`.
With the real period, a wake 70 min after the turn's last request read all 24,664 cached
tokens, ten minutes after the unrefreshed entry would have lapsed.

## Testing

`claude plugin validate scripts/cache-keepalive` and `claude plugin test scripts/cache-keepalive`
(both run by `tests/test_cache_keepalive_plugin.py`). After the engine has loaded the folder
once, which lays `.claude-plugin/types/` (self-ignored), run
`nix shell nixpkgs#typescript -c tsc -p scripts/cache-keepalive`.

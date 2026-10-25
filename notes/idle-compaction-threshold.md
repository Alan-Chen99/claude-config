# Idle compaction at 100k tokens nets about zero here; the 200k default stays

> **Dated record**, 2026-10-25. Firings from Claude Code 2.1.289 (installed); the threshold
> `CLAUDE_CODE_IDLE_COMPACT_MIN_TOKENS` (2.1.299+, floor 100,000, default 200,000) read in the
> 2.1.310 source. Trigger and refusals: `notes/cc-2.1.289-idle-compaction.md`. The user kept the
> default.

**Method.** Main-thread records of `~/.claude/projects/*/*.jsonl`, one response per `message.id`.
A gap is an `end_turn` response that wrote a 1h cache entry, followed by the next main-thread
response more than 54 minutes later, or by none. Its context is input + cache read + cache write.
A firing is a `Compacted while idle` notice; its post-compaction size is the next response's context.

**Measured.**

- 42 firings, 2026-10-08 to 2026-10-25, at 199k-451k. 29 were in sessions with no later response.
  In the other 13 the next request carried 47k-63k, with a summary of about 15k characters.
- Gaps since 2026-10-08, by context: 200k+, 122, of which 30 had a later response; 100-200k, 112,
  of which 21 did (19 after the hour), median 145k.
- Fire rate in the 200k+ band: 13 of 30 gaps with a later response, 29 of 92 without one.

**Priced** at Opus 5.5's $8/MTok 1h write, $0.20 read and $20 output. A 100-200k firing saves
about $0.63 when the user returns after the hour (145k rewritten against 53k). It wastes about
$0.11 in a session never resumed (the read plus about 4k summary tokens), and loses about $0.50 on
a return between minutes 54 and 60. At the 200k+ fire rates, a 100k threshold adds about 38
firings per 17 days and nets about +$1.5; the 200k+ band nets about +$16. Summary tokens are
chars/4 with thinking uncounted, so the 100k net is within its error of zero. Each of the ~9
firings in a resumed session would replace a ~145k context with a ~53k summary.

Re-measure if the post-compaction size, the prices, or the share of idle sessions left open moves.

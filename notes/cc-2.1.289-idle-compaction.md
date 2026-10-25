# 2.1.289 compacts an idle main thread 54 minutes after its last request, background work or not

> **2.1.299 added a setting and a threshold variable (read in 2.1.310's source, 2026-10-25).**
> `"idleCompaction": false` in `settings.json` (default true) refuses a firing as
> `idle_compaction_off`, checked right after `compaction_off`; the notice now ends `turn off with
> "idleCompaction": false in settings.json`. `CLAUDE_CODE_IDLE_COMPACT_MIN_TOKENS` replaces the
> flag's `minTokens`, still floored at 100,000 with 200,000 as the default. The flag also takes
> a `compact_on_return` mode. Everything below is 2.1.289's and stands as measured.

Investigated 2026-10-24 on Claude Code **2.1.289**: the code by an Explore subagent in
`/repos/claude-code-decompiled`, each citation re-read by hand; the firings from this machine's
transcripts.

## Trigger (read in code)

1. **When.** Each main-thread request arms a timer (`N2n.of(s).arm(n.savedAt, …)`) that fires at
   `lastActivityAt + (expiresAt - lastActivityAt) * fireAtFraction`, default `Kto = 0.9`: 54
   minutes into a 1h entry. It arms only when the last request's TTL is 1h
   (`g.lastRequest?.ttl !== "1h"` returns) and the session is interactive (`J9()`: false for
   `CLAUDE_CODE_SESSION_KIND` `bg`/`daemon`/`daemon-worker`, true for `t.interactive`).
2. **The gate.** GrowthBook `tengu_sunny_locket`: `mode` `off`/`log`/`compact`, `minTokens`
   (default 200,000, floor 100,000), `fireAtFraction` (0.5-0.95). This account's cached value on
   2026-10-24: `{"mode": "compact"}`.
3. **Refusals when it fires**, in order: `disabled`; `compaction_off` (`Lf()`: `DISABLE_COMPACT`,
   `DISABLE_AUTO_COMPACT`, or the `autoCompactEnabled` setting off); `prefix_changed`;
   `not_one_hour`; `lapsed` (more than 60 s late, or the entry not warm); `small` (context under `minTokens`); `newer_request`; `near_limit`;
   `held_elsewhere` (another process holds the session); `transcript_unreadable` or
   `transcript_advanced`; `busy` (a thin client, an external turn, or `this.turn.guard.isActive`);
   `present` (the person interacted in the last 60 s, `g6t = 60000`).
4. **Not consulted:** running background tasks. Neither `#o()` nor the refusal list reads them.
5. **On success** it runs `compactConversation({ instructions: "" })` and appends the notice
   `Compacted while idle, before the prompt cache expired` (JSONL `system`, `subtype:
   "informational"`); telemetry `tengu_idle_compact_fired`.

Not traced: where `turn.guard` turns active and inactive; whether a `$.model.fork` (`querySource:
"hook_prompt"`, `skipCacheWrite: !0`, read) moves `lastMainThreadRequestAt` and so makes a
pending firing refuse `newer_request`. The subagent inferred that the fork does not re-arm the
timer.

## Measured

39 notices in this machine's main transcripts, 2026-10-08 to 2026-10-24. Every one followed an
`end_turn` with no tool call open, 54.2-56.9 min after the last response, at 202k-451k tokens of
context. 15 had background work in flight (`scripts/cache-keepalive/waits.py`'s launch and
notification matching). Over the same days, 16 in-turn waits pending 55+ min at 200k+ tokens
(AskUserQuestion 10, Agent 5, Bash 5) drew none.

## Against `scripts/cache-keepalive`

- Inside a turn it does not fire, so the mod's in-turn refresh is the only cover there.
- After a turn end with background work, 200k+ tokens and the person away, both are armed. In
  the one session where the mod refreshed such a context (2026-10-24: turn end 18:44:14 UTC at
  240k tokens, refresh 19:34:16, next response 19:43:31), no compaction came at 54 min. A
  compaction after a refresh would spend that refresh (0.1x of the prefix) for nothing. Under 200k
  tokens, or with the person present, only the mod acts.
- A plugin can skip a compaction from `session.compact` (`({ skip: … })`); the mod does not.

# cache-keepalive

## Overview

A Claude Code mod (a function-hook plugin; the plugin API is early access, read off 2.1.289).
While the main thread waits, it sends one `$.model.fork` 50 minutes in. It covers two kinds of
wait: a turn that ended with background work in flight, and a main-thread tool call still pending
(an AskUserQuestion or permission dialog, a foreground Bash). The fork re-sends the main thread's
last request plus a one-word prompt, which reads the cached prefix at 0.1x the input price and
restarts its 1h TTL. Without it, a wake after the hour rewrites the whole prefix at 2x, typically
200k-440k tokens here.

## Design Decisions

**Why a mod.** 2.1.289 ships its own keepalive (`[cache-keepalive]` debug lines, a POST to
`/v1/messages/cache_touch`). It is gated by the GrowthBook flag `tengu_sequential_cloud` and the
account restriction `allow_cache_keepalive`, and the flag read `false` on this account on
2026-10-23 (`~/.claude.json`, `cachedGrowthBookFeatures`). On 2.1.289, 35 of 39 idle gaps of
1-4 h ended in a full rewrite. If the flag turns on, this mod duplicates the built-in at 0.1x per
refresh: remove its line from `scripts/claude.sh`.

**One refresh at 50 minutes.** The hour counts from the request before the wait, which is sent
before the Stop or tool call by however long the reply took to generate. `waits.py` over 184 days
of transcripts on this machine (2026-04 to 2026-10) found 945 waits with background work in flight.
Thirty of them outlived the TTL with the prefix still needed. One refresh avoids 12 of those
rewrites, three avoid 16. A wait the transcript never closes (a server left running, the session
left open) pays every refresh for nothing: counting those at worst, one refresh nets +2.8M
base-input tokens, two +0.7M and three -0.6M. Re-run `waits.py` to re-tune.

**In-turn waits.** `tool.call`'s `next(e)` spans the permission prompt and the tool's run, so the
first pending main-thread call arms the timer and the last one to end cancels it. Measured on
2026-10-24 (`notes/cc-2.1.289-in-turn-wait-cache-expiry.md`): every fork made mid-turn took two
requests (a denied tool attempt, then the reply), so `waits.py` prices these refreshes at 0.2x.
Leaving out foreground Agent waits, which `9197a25c` retired, one refresh avoids 17 rewrites for
+5.4M (+0.4M with every never-answered call paying), and two net less. On a first turn whose first
response opens the dialog, the fork reads the system prompt and tools alone, and the first user
message is rewritten at the wake anyway.

**The TTL gate.** The main thread caches for 5 minutes in overage and off a subscription. A fork
after that lapse finds no entry and pays the whole prefix uncached, at 10x a refresh. A refresh
therefore needs the newest main-thread cache write in the transcript's last 1 MB to be 1h. A Stop
checks when it arms; a tool call checks when the refresh is due, since nearly every call ends
within seconds and a tail per call is a process per call. Third-party endpoints (`kimi.sh`,
`zai.sh`) write no `ephemeral_*` field and never refresh. The path comes from `classic.SessionStart`
and `classic.Stop`: a hooks module's `classic.PreToolUse` gets the `tool.call` envelope, with no
path. Two waits leave the TTL unread. A session's first turn is not in the transcript file while it
waits, and 40 of the 53 measured in-turn waits fell there. A module reloaded mid-session (an edit
to this folder) holds no path until its next Stop. Both refresh on the 1h every measured main
thread here used, and the lapse check reports one that was not.

**Idle compaction overlaps one case.** Claude Code compacts an idle main thread 54 minutes after
its last request when its context is 200k+ tokens (`CLAUDE_CODE_IDLE_COMPACT_MIN_TOKENS`, floor
100k) and the person is away, unless `settings.json` sets `"idleCompaction": false` (2.1.299;
this repo's does not). On this account the
GrowthBook flag `tengu_sunny_locket` is `{"mode": "compact"}`
(`notes/cc-2.1.289-idle-compaction.md`). It ignores background work and refuses inside a turn.
After a turn end in that case both are armed. In the one session where the mod refreshed a 240k
context (2026-10-24), no compaction followed; whether the fork makes it refuse
(`newer_request`) was not traced.

**Main thread only.** `$.model.fork` replays the main thread, and a waiting subagent keeps
itself warm with `skills/long-bash`'s `agent-tools wait` loop, which wakes it inside its cache's
lifetime, 5 minutes unless its frontmatter sets an hour. A subagent's `tool.call` and, since 2.1.299, its `turn.start` carry its `agentId` and pass
through. A stopped subagent's running shell is listed in `background_tasks` (2.1.289,
`notes/cc-2.1.289-subagent-waits.md`): subagent activity neither disarms a refresh nor hides the
work that arms one.

**Interactive sessions only.** `scripts/claude.sh` passes `--plugin-dir` when stdin is a
terminal. Prompt-test runs stay at "no plugins loaded", and a background handoff keeps the flag.

## Invariants

- A refresh reads; it never writes the prefix. A row whose `read` is not about the previous
  request's read plus write means the fork stopped replaying that request, and the mod reports
  it as lapsed. Mid-turn, a fork's read stops near the start of the request's final message.
- Every outcome is a dim transcript row, stored in the JSONL as a `system` record (`subtype:
  "informational"`, `content: "cache-keepalive: refresh 1/1: read N, …"`). An in-turn refresh
  appends `; while <tool> was pending`, and `; TTL unread: <why>` when it went ungated. A gate
  that says no logs `not armed: …` at a Stop and `not refreshed: …` in a tool call. A failure
  also toasts and stays as the plugin's status line until the next turn. `waits.py` lists each
  refresh and whether the response after it hit.
- A keepalive failure never refuses what it hooks. On 2.1.310 a hook that throws is skipped and
  the action goes on, reported only by the engine; each hook at a site whose answer can refuse
  (`claude plugin validate`'s `gating hook` lines) carries a `.catch` that reports a failure
  row, `<event> hook failed (…); passed on`, and passes the action on. A module that saw no
  `session.start` passes everything on and says so once. No `.catch` reaches the 2.1.299
  refusal: a tool input or result the hooks worker cannot be handed, or hand back, refuses the
  call for any module hooking `tool.call`.

## Verification (2.1.289)

2026-10-23, after a Stop: in a `claude --plugin-dir` session with the period cut to 1 min, the
refresh read 24,557 tokens (the last request's 24,194 read plus 363 written), with 63 uncached
and 4 output, in about 1 s with one reply. The notification's `turn.start` disarmed it, and the
JSONL kept the row. Event order: `classic.Stop`, then `turn.complete`. With the real period, a
wake 70 min after the turn's last request read all 24,664 cached tokens, ten minutes after the
unrefreshed entry would have lapsed.

2026-10-24, inside a turn (Haiku 4.5, period cut to 1 min): with an AskUserQuestion dialog open,
the refresh read 21,144 tokens per request of a 21,216-token prefix (a third turn) and 14,033 of
20,660 (a first turn, `TTL unread`). The call resolved when the dialog was answered.

## Testing

`claude plugin validate scripts/cache-keepalive` and `claude plugin test scripts/cache-keepalive`
(both run by `tests/test_cache_keepalive_plugin.py`). After the engine has loaded the folder
once, which lays `.claude-plugin/types/` (self-ignored), run
`nix shell nixpkgs#typescript -c tsc -p scripts/cache-keepalive`.

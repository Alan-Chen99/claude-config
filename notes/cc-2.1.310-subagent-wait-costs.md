# A message to a busy subagent waits out its call, and progress summaries keep its cache warm

Investigated 2026-10-26 (UTC) on Claude Code **2.1.310**: the decompile read through two sonnet
Explore agents, this machine's transcripts since 2026-10-24, and the proxy captures under
`~/.claude/requests-log/`. Led to `agent-tools wait` returning on a queued message and sizing
a subagent's bound to its cache but keeping a 5-minute one warm throughout, to `agents/gp-cache1h.md`'s
thresholds, and to the "Several jobs" paragraph of `skills/long-bash/SKILL.md`.

## Findings

1. **SendMessage never cuts a subagent's call short.** The one path that backgrounds a
   subagent's shell to deliver (`input_low_latency_submit`, gate `tengu_velvet_panda`) feeds
   only text a human types into that agent's view: for subagents it sets `promoteToNow: () =>
   !1` and no interrupt, and SendMessage's entry is `isMeta: !0`, which `sendQueuedNow` refuses.
   The message sits in the in-memory task registry; nothing reaches disk until delivery, as
   `queue-operation` records are the main command queue's and carry no `agentId`. Measured
   lags from send to delivery for a running recipient: session `c6c0e3e0` (2.1.289), 27 sends,
   median 72 s, five over 4 minutes, the longest 10,020 s; on 2.1.310, 33 s, 157 s and 1,122 s.
2. **Progress summaries refresh a waiting subagent's 5-minute cache.** A background subagent in
   an interactive session with forks on gets an `agent_summary` request ("Describe your most
   recent action in 3-5 words") on a timer from 30 s, growing per call to at most 240 s. It
   forks the agent's whole conversation, so it reads the agent's cache, and it is skipped while
   the transcript is unchanged, which an agent blocked in one call is: the fingerprint drops an
   assistant message whose `tool_use` has no result yet. In session `6e3a29c4` a subagent issued
   seven 230 s waits in one message; captures `0647`-`0657` show a summary every ~3m40s reading
   its 277,962 cached tokens, and its next request, 27 minutes on, read the same 277,962. So
   each wake of a waiting subagent buys a second full-context read, and one long call buys none.
   Session `c6c0e3e0` sent 496 summaries, $15.56 against $4.25 of wakes.
3. **Agents batch waits to save turns.** 39 subagent messages from 2026-10-24 to 2026-10-26 held
   two to ten foreground waits (`agent-tools wait`, `g4q.py wait`, `until` loops); the calls run
   one after another, so a message waited for the whole batch. One agent's reasoning: "maybe
   using longer intervals of up to 230 each time to reduce the number of turns needed."
4. **Waiting on several jobs at once is rare; waiting on conditions is not.** Of 903
   `agent-tools wait` results, 7 ended one job with another still running, and in 6 the agent
   acted before waiting again. Of 152 hand-written `until`/`while` loops, 145 were subagents',
   mostly bounded foreground calls (`timeout 235 bash -c "while [ ! -s $F ]; …"`), and 42 joined
   conditions with `&&` or `||`. Each such call is as deaf to messages as a long one.
5. **The hook payload carries what a wait needs.** PostToolUse's `tool_response` for SendMessage
   is the tool's output object: `Message queued for delivery to <name> at its next tool round.`
   and `pin.id`, the raw agent id that names the recipient's `agent-tools` scope. A foreground
   Bash call's timeout is the model's `timeout`, else `BASH_DEFAULT_TIMEOUT_MS`, else 120000,
   `Math.min`'d to `BASH_MAX_TIMEOUT_MS`, else 600000 (`timeout_clamped`). A running call's own
   assistant record is not yet in the transcript, so neither is readable from inside it.
6. **Past the break-even, a cold wait still does not pay on measured runs.** Arithmetic: a
   4-minute wake reads the context at 0.1x, about 0.23x with the summary it triggers (0.11x
   under `-p`, which has none), and a rebuild costs 1.25x, so 5 to 11 wakes cost one rebuild.
   With the inbox bounding a message's delay, the loop past that point had no stated reason
   left (`notes/cc-2.1.289-subagent-waits.md`, "What follows"). Replayed on the 241 runs of
   consecutive `nothing ended` subagent waits here: switching after N warm wakes to one wait
   up to its call's 58 minutes, which rebuilds when it returns, lost 0.66 to 2.94 M
   input-price tokens over N = 4 to 12 at 0.11x, and at 0.23x gained 0.04 M at best (N = 8).
   Only 21 runs passed 6 wakes, all in session `c6c0e3e0`, the longest 18 (72 minutes). The
   same arithmetic prices a 1-hour cache (2x writes, 0.75x of the final context over 1.25x):
   it pays once an agent waits over about 15 minutes in its turn (30 under `-p`; the agent's
   description splits them at 20), or once idle over 5.

## Probe

`agent-tools claude -p` from this checkout, sonnet main, two haiku background agents
(general-purpose, `gp-cache1h`), each `agent-tools wait`ing on a 120 s job; main sent both a
message 35 s in. Both waits returned 1 s after the send with `a message from main, queued 1s
ago, arrives with this result`, the message attached to that result. `--print-bound` read 240
and 3000; before either agent's first response was recorded, 240 for both.

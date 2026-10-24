# A turn waiting on its own tool call outlives its 1h prompt cache, and its first turn stays off disk meanwhile

Investigated 2026-10-24 on Claude Code **2.1.289**, subscriber account, main thread on the 1h
TTL. Live runs: interactive `claude --plugin-dir` sessions on Haiku 4.5, the mod's period cut to
1 min. Led to the `tool.call` path of `scripts/cache-keepalive/`.

## Finding

While a main-thread tool call is pending (an AskUserQuestion or permission dialog, a foreground
Bash or Agent), nothing is sent, so a wait past 60 minutes rewrites the prefix at 2x. A scan of
3,332 transcripts (2026-05 to 2026-10) found 58 wakes after an in-turn wait of 60+ min; 52 wrote
more than they read, 10.1M tokens written, 36 of them after an AskUserQuestion. The built-in
idle compaction refuses inside a turn (`notes/cc-2.1.289-idle-compaction.md`).

`scripts/cache-keepalive/waits.py` (run 2026-10-24) counts 87 in-turn waits pending 50+ min
(AskUserQuestion 48, Agent 34, Bash 24) and 172 never answered (the transcript ends mid-call:
Bash 133, Edit 27, Read 24, ...). Without foreground Agent, which `9197a25c` retired, one refresh
per wait avoids 17 rewrites for +5.42M base-input tokens, +0.37M if every never-answered call
paid one; two refreshes net less. 40 of those 53 waits fall in a transcript's first turn.

## The first turn reaches the transcript file late

In a new session whose first response opens the dialog, the `.jsonl` kept its pre-response size
(81,998 bytes, no `assistant` record) for the 175 s watched, with no plugin loaded. With the mod
loaded, the rows it logged from a timer 60 s in were written together with every held record; a
row logged inside the `tool.call` dispatch was held too. In a later turn the `tool_use` record was
on disk within 1 s. The mechanism was not found: an Explore subagent's literal search of the
decompile turned up no buffer or flush gate. A TTL read from the transcript tail therefore sees
no response on a first turn.

## `$.model.fork` while a tool call is pending

It answers, and restarts the entry's hour, but not for the request's final message:

| Run | Main request: read + write | Fork, read per request | Requests |
|---|---|---|---|
| Session A, turn 3 | 21,121 + 95 | 21,144 | 2 |
| Session B, turn 3 | 21,283 + 180 | 21,349 | 2 |
| Session B, turn 1 | 14,033 + 6,627 | 14,033 | 2 |

Each fork read about the prefix up to the main request's final message. On a first turn whose
first response is the dialog, that is the system prompt and tools alone (14,033, shared across
sessions), and the first user message (6,627 here) is paid again. Every fork first called a tool,
was denied, and replied in a second request (output 384-788 tokens; the debug log's `Forked agent
[plugin_model_fork] finished: 7 messages`). A prompt saying every tool is disabled did not change
that (session B, turn 3). At a turn end the fork answered in one request
(`notes/background-wait-cache-expiry.md`).

## What a hooks module sees

- `classic.PreToolUse` carries the `tool.call` envelope (live: `questions,tool,tool_use_id`), no
  `transcript_path`; the types say so (`classic.PreToolUse alone differs: its e is
  ToolCallEnvelope`). `classic.SessionStart` carries `transcript_path` (`source=startup`).
- An edit to the plugin folder reloads the module mid-session: `session.start` runs again,
  `classic.SessionStart` does not, so the module holds no path until the next `classic.Stop`.
- `tool.call`'s `next(e)` spans the dialog: the call resolved when the dialog was answered.

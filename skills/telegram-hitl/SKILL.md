---
name: telegram-hitl
description: Use when a session needs a human decision it cannot make alone - asking and waiting hours for an answer, or listening for a correction mid-run - or touches the Telegram channel.
---

# Telegram human-in-the-loop

Bot API calls go to a local proxy; answers come out of one append-only log.
`$TELEGRAM_HITL_STATE_DIR` holds `proxy.sock`, `channel.jsonl`, `chat_id`,
shared by all sessions. Unset: not configured here; never guess it — a second
`getUpdates` drain evicts the first. Proxy: the `telegram-hitl` systemd user
unit — this repo's `src/claude_config/CLAUDE.md`.

## Whether to send

Every send is a push notification the human cannot defer. **Block on it or skip
it**: one message per answer you need, sent only when the answer changes your
next step. Only a time-critical correction of your own message may skip the
block — and if nothing has arrived since it, `editMessageText` it: no
notification. The unnotified lines below are not priced.

## Sending

Any Bot API method, minus `https://api.telegram.org/bot<token>`; `localhost` is
a placeholder curl requires.

```bash
STATE=$TELEGRAM_HITL_STATE_DIR
curl -s --unix-socket "$STATE/proxy.sock" http://localhost/sendMessage \
  -H 'Content-Type: application/json' -H "X-Session-Id: $CLAUDE_CODE_SESSION_ID" \
  -d "{\"chat_id\": $(cat "$STATE/chat_id"), \"message_thread_id\": 61, \"text\": \"Ship it?\"}"
```

`X-Session-Id` on every call, the id whole — the log's only record of who
called. No client shows message ids: never cite one in `text`; reply —
`"reply_parameters": {"message_id": 64, "quote": "<exact substring>"}` (ids:
listener lines, send responses; inexact → `QUOTE_TEXT_INVALID`). One open
question per message.

Refused: `403` `getUpdates`/`setWebhook`/`deleteWebhook`, `400` non-alphanumeric
method, `411` chunked body, `502` Telegram unreachable; nothing is retried.

## Topics

`message_thread_id` addresses a forum topic. **Make your own, named for the
work, at its first real question** (`createForumTopic` `{"chat_id", "name"}` →
`result.message_thread_id`) **and read it whole**: everything typed there is for
you. Two sessions in one topic take each other's answers — join one only to
continue its work, then act only on lines marked as replies to you. `python3
<skill dir>/listen.py topics` lists them and their senders.

Your messages all arrive from the same bot, so **name yourself as you arm the
listener** — `▸ $CLAUDE_CODE_SESSION_ID · $PWD`, what you are doing — and **say
when you stop**, same handle, both with `"disable_notification": true`; else the
human types into a topic nobody reads.

## Listening

`listen.py` beside this file prints `message <id> in chat <chat>[, reply to
<your id>]: <text>` per human message for you and `channel up` / `channel down:
<cause>`; the watermark file is its memory across re-arms (`--from-now` skips a
joined topic's history).

```
Monitor(command="python3 <skill dir>/listen.py 61 <scratchpad>/seen",
        description="topic 61", timeout_ms=1800000)
```

Arm it as you create the topic, not later. Thirty minutes is the cap, so re-arm
first thing in each expiry turn. Waiting is ending the turn — not a loop, not
`agent-tools run --background`. `channel down` is past the blip the script
forgives: fix the channel. React 👍 once you have read an answer
(`setMessageReaction`, `reaction: [{"type":"emoji","emoji":"👍"}]`); an
unreacted answer reads as unread.

## Traps

- The General topic has no thread id.
- ✅ is `REACTION_INVALID`; some service messages `MESSAGE_ID_INVALID`.
- Enabling Topics changes the chat id: follow `migrate_to_chat_id`.

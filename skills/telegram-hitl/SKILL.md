---
name: telegram-hitl
description: Use when a session needs a human decision it cannot make alone - asking a question and waiting hours for an answer, or listening for an unsolicited correction mid-run. Covers the local Telegram proxy, its log, forum-topic choice, and the Bot API traps.
---

# Telegram human-in-the-loop

Reach the human by making ordinary Bot API calls against a local proxy, and read
their answers out of one append-only log. Any number of sessions do this at
once. Nothing is assigned to you, and no chat, topic or message is yours alone.

| | |
| --- | --- |
| Proxy | `http://127.0.0.1:18420` (the bound port is in `~/.claude/channels/telegram-hitl/port`) |
| Log | `~/.claude/channels/telegram-hitl/channel.jsonl` |
| Chat id | `~/.claude/channels/telegram-hitl/chat_id` |

If the port does not answer, the proxy is not running:

```bash
UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config \
agent-tools run --background --desc "telegram-hitl proxy" \
  uv run --project /repos/claude-config python -m claude_config.telegram_hitl
```

The environment variable is this repo's convention; without it `uv` would build
a `.venv` inside the canonical checkout. It refuses to start if another instance holds the lock, which is intended — one
process owns the update stream, and a second consumer would evict the first.

## Sending

Take any Bot API URL, drop `https://api.telegram.org/bot<token>`, and point what
is left at the proxy. What comes back is Telegram's own JSON.

```bash
curl -s -X POST http://127.0.0.1:18420/sendMessage \
  -H 'Content-Type: application/json' \
  -H "X-Session-Id: $CLAUDE_SESSION_ID" \
  -d "{\"chat_id\": $(cat ~/.claude/channels/telegram-hitl/chat_id), \"message_thread_id\": 6, \"text\": \"Ship it?\"}"
```

`X-Session-Id` is optional and uninterpreted; it lands in the log so the record
says who called.

Refused with `403`: `getUpdates`, `setWebhook`, `deleteWebhook`, `close`,
`logOut`. Each would break the one update stream or the token. Everything else
passes through.

Three more refusals are the proxy's own rather than Telegram's, and each names
`telegram-hitl proxy` in its `description` so you can tell which is which:

| | |
| --- | --- |
| `400` | The method name is not alphanumeric. `sendMessage` is fine; `sendMessage/`, `send%4dessage` and `x/../getUpdates` are not — a respelling that resolves to a denied method would otherwise walk straight past the denylist. |
| `411` | The body was sent chunked, so it carries no `Content-Length` and would forward as empty. Send a body with a length. |
| `502` | Telegram could not be reached or did not answer usably. The same fault is in the log, so a watcher sees it too. |

**Errors arrive as themselves** and nothing is retried for you — `retry_after`,
`REACTION_INVALID`, `message thread not found`, `not enough rights to create a
topic`. Read the error and decide. If you are hitting flood control at
human-in-the-loop volumes, that is a defect in what you are doing, not a limit
to pace around.

## Reading

The log is the only read interface. Every line is one JSON object: `inbound` (a
Telegram update, verbatim), `outbound` (a call with its response), `denied`,
`fault` (the channel's own faults), `proxy` (start and stop).

<!-- recipe: read-log -->
```python
import json


def records(path):
    """Every complete record in the channel log, oldest first.

    A final line with no newline is a record another process is still
    appending. Python's file iterator hands it over anyway, so stop there.

    A line that will not parse is a record damaged by a failed write. It is
    yielded as one, so the damage stays visible and the records after it stay
    readable.
    """
    with open(path, "rb") as handle:
        for raw in handle:
            if not raw.endswith(b"\n"):
                return
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                yield {"kind": "damaged", "raw": raw.decode("utf-8", errors="replace")}
```

## Asking, then waiting

Send the question, keep the `message_id` from the response, and watch for a
reply to it. An inbound reply carries the full text of the message it answers
under `reply_to_message`, so you need no question ledger.

<!-- recipe: answers -->
```python
def answer_to(records, message_id):
    """The human's first reply to the message with this id, or None."""
    for record in records:
        if record["kind"] != "inbound":
            continue
        message = record["update"].get("message") or {}
        if (message.get("reply_to_message") or {}).get("message_id") == message_id:
            return message
    return None
```

Waits here are measured in hours, so wait against the file, not against a socket.
Write a small waiter to your scratchpad and background it — it exits on the
answer, which produces exactly one notification:

```bash
agent-tools run --background --desc "await human" python3 <your-scratchpad>/waiter.py 51
```

It needs nothing but the standard library, so it runs under plain `python3`.

A waiter that only looks for an answer cannot tell *no answer yet* from *the
channel is down*. Check both:

<!-- recipe: health -->
```python
def inbound_state(records):
    """"up", or "down: <cause>" — whether a human's answer can still reach you.

    Silence has two causes and they demand opposite responses: keep waiting, or
    go fix the channel. Only drain faults are decisive here; a failed send says
    nothing about whether answers are arriving.
    """
    state = "down: never started"
    for record in records:
        if record["kind"] == "proxy":
            state = "up" if record["event"] == "started" else "down: " + record["reason"]
        elif record["kind"] == "fault" and record["source"] == "drain":
            state = "up" if record["state"] == "cleared" else "down: " + record["signature"]
    return state
```

For **unsolicited** input instead — a correction or a stop arriving mid-run with
no question of yours to answer — use `Monitor` on the log. That is an open-ended
stream of occurrences, which is what a persistent monitor is for; a background
loop that exits on the first match is the wrong shape for it.

## Topics

The chat is a forum. Messages land in a topic, addressed by `message_thread_id`.

**Use an existing topic when your question is a natural continuation of it;
otherwise make a new one.** Nothing prescribes how many topics you may have, or
ties a topic to a session. Judge continuity, and remember the human has to read
the result.

There is no `getForumTopics` in the Bot API, so the log is the only registry:

<!-- recipe: topics -->
```python
def topics(records):
    """The forum's topics, by thread id. Every one is a logged createForumTopic."""
    found = {}
    for record in records:
        if record["kind"] != "outbound":
            continue
        response = record["response"]
        if not isinstance(response, dict) or not response.get("ok"):
            continue
        method = record["method"].lower()
        params = record["params"] or {}
        if method == "createforumtopic":
            found[response["result"]["message_thread_id"]] = response["result"]["name"]
        elif method == "editforumtopic" and "name" in params:
            found[params["message_thread_id"]] = params["name"]
        elif method == "deleteforumtopic":
            found.pop(params["message_thread_id"], None)
    return found
```

Create one with `createForumTopic` (`{"chat_id": ..., "name": "..."}`) and use
the `message_thread_id` it returns.

## Acknowledging

When you have read the human's answer, react to their message — from your own
script, once you actually have it. Nothing else reacts, so an unreacted message
is one nobody has taken, and that absence is informative.

```bash
CHAT=$(cat ~/.claude/channels/telegram-hitl/chat_id)
curl -s -X POST http://127.0.0.1:18420/setMessageReaction \
  -H 'Content-Type: application/json' \
  -d "{\"chat_id\": $CHAT, \"message_id\": 51, \"reaction\": [{\"type\":\"emoji\",\"emoji\":\"👍\"}]}"
```

## Traps

Each of these cost real time to find.

- **`message_thread_id` carries either a reply-chain id or a forum-topic id.**
  `is_topic_message` is the discriminator. Both ids come from the same per-chat
  counter, so a wrong value is never out of range — it just files an ordinary
  reply as a topic.
- **A forum's General topic cannot be addressed by thread id.** A conversation
  becomes routable only once a topic exists for it.
- **The reaction alphabet is fixed.** 👀 👍 🙏 🤔 🔥 ⚡ work; ✅ and 📝 return
  `REACTION_INVALID`. The obvious checkmark is specifically unavailable.
- **Reactability is type-specific and unpredictable.** `new_chat_members`
  accepts a reaction; chat-migration service messages return
  `MESSAGE_ID_INVALID`. Let a script crash on it — loud, local, harmless.
- **Enabling Topics migrates a group and changes its chat id.** The old id then
  returns `group chat was upgraded to a supergroup chat`, and
  `migrate_to_chat_id` is the forwarding pointer. Follow it rather than treating
  a stored chat id as stable.
- **Reading a file under append needs care in Python**, which yields a partial
  final line where a shell `read` loop does not. Use the reader above.
- **Never start another poller.** The first-party `telegram` plugin and
  `telegram-bot-skill` each start their own, and a newcomer does not get
  refused — it seizes the stream and kills the existing consumer. A 409 in the
  log means exactly this has happened.

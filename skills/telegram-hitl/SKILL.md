---
name: telegram-hitl
description: Use when a session needs a human decision it cannot make alone - asking a question and waiting hours for an answer, or listening for an unsolicited correction mid-run. Covers the local Telegram proxy, its log, forum-topic choice, and the Bot API traps.
---

# Telegram human-in-the-loop

Reach the human by making ordinary Bot API calls against a local proxy, and read
their answers out of one append-only log. Any number of sessions do this at
once, from any number of containers and from the host. Nothing is assigned to
you, and no chat, topic or message is yours alone.

`$TELEGRAM_HITL_STATE_DIR` names the channel, and everything else lives under it:

| | |
| --- | --- |
| Proxy | `$TELEGRAM_HITL_STATE_DIR/proxy.sock` |
| Log | `$TELEGRAM_HITL_STATE_DIR/channel.jsonl` |
| Chat id | `$TELEGRAM_HITL_STATE_DIR/chat_id` |

If that variable is unset, the channel is not configured here. It has no default
and must not be guessed: the directory is shared by processes whose homes differ
— one per container, plus the host's — so a home-relative path resolves
somewhere different in each of them, and each would take its own lock and start
its own drain. Telegram does not refuse a second consumer; it evicts the first.

If `chat_id` is absent, the channel is not set up on this machine, and reading it
anyway just puts an empty value in your request. Setting it up needs a human: a
Telegram supergroup with Topics enabled, the bot added as an administrator with
Manage Topics, and the chat id written to that file. The Bot API can do none of
it — it can neither create a chat nor raise its own rights. `getChat` reporting
`is_forum: true` confirms the first two.

What the socket says when it does not answer:

| | |
| --- | --- |
| No such file | No proxy has ever run against this directory. |
| Connection refused | One ran and died without unlinking its socket. Start another; it clears the stale file itself. |
| Permission denied | A proxy is running under an identity yours does not share. The socket is mode 0600 like the log, so you cannot read the log either — this is a deployment fault, not something to work around. |
| Resource temporarily unavailable | More senders are connecting at once than the accept backlog holds. A connect to a full AF_UNIX backlog fails immediately rather than waiting, so this is the one refusal worth a retry. The backlog is 128 (`server.py`, `ProxyServer.request_queue_size`), so reaching it means a burst, not a stuck proxy. |

On a machine that has the unit, it is already running as a systemd user service
and nothing needs starting:

```bash
systemctl --user status telegram-hitl     # up, and since when
journalctl --user -u telegram-hitl -n 20  # why it is not
```

That unit is `systemd/telegram-hitl.service` in this repo, symlinked into
`~/.config/systemd/user/` by `install.sh` and enabled by a human. It names the
state directory itself, restarts ten seconds after any exit, and stops retrying
after five failed starts inside two minutes: a unit sitting in `failed` is a
permanent fault — no token, no interpreter, a lock held elsewhere — rather than a
channel that is merely quiet.

Where there is no such unit — another machine, a container with no user manager —
start one by hand:

```bash
UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config \
agent-tools run --background --desc "telegram-hitl proxy" \
  uv run --project /repos/claude-config python -m claude_config.telegram_hitl
```

`--background` here, unlike the waiter below: a harness background task is
session-scoped — a `TaskStop` kills it — and this proxy has to outlive the
session that starts it. The environment variable is this repo's convention;
without it `uv` would build a `.venv` inside the canonical checkout. The proxy
inherits `TELEGRAM_HITL_STATE_DIR` from your environment, which is what makes the
one you start the same channel everyone else is reading.

Either way it refuses to start if another instance holds the lock, which is
intended — one process owns the update stream, and a second consumer would evict
the first. The lock is a file in the shared directory, so it excludes proxies in
other containers and on the host as well as other processes in yours.

Whoever wins that lock serves everybody, because the socket sits in the same
shared directory: a proxy started from any container is reachable from all of
them. The difference is lifetime — one started inside a container dies with that
container, while the host's service outlives every container and returns after a
reboot.

## Sending

Take any Bot API URL, drop `https://api.telegram.org/bot<token>`, and point what
is left at the proxy socket. What comes back is Telegram's own JSON.

```bash
STATE=$TELEGRAM_HITL_STATE_DIR
curl -s --unix-socket "$STATE/proxy.sock" -X POST http://localhost/sendMessage \
  -H 'Content-Type: application/json' \
  -H "X-Session-Id: $CLAUDE_CODE_SESSION_ID" \
  -d "{\"chat_id\": $(cat "$STATE/chat_id"), \"message_thread_id\": 6, \"text\": \"Ship it?\"}"
```

The `localhost` in that URL is a placeholder curl requires and never resolves;
`--unix-socket` decides where the request goes. Only the path after it matters.

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

**Watch the topic, not only the reply id.** A human answering in the topic
without using the reply gesture produces an inbound with no `reply_to_message`,
and a waiter keyed to the id sits through it — observed 2026-09-25, an answer
sent as a plain message and a second message pointing at it. Wait on any inbound
whose `message_thread_id` is your topic and whose `message_id` is above your
question's, and read it.

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
Write a small waiter to your scratchpad and run it with `run_in_background: true`
— the harness re-invokes you when it exits on the answer, which is the one
notification you want:

```bash
agent-tools run --desc "await human" python3 <your-scratchpad>/waiter.py 51
```

It needs nothing but the standard library, so it runs under plain `python3`. Not
`agent-tools run --background`: that detaches the waiter from the harness, so its
exit produces no notification — only a `final(<code>)` status line, which is
visible on your next tool result or the user's next turn and wakes nothing. An
answer would sit unread until something else gave you a turn.

A waiter that only looks for an answer cannot tell *no answer yet* from *the
channel is down*. Check both — but do not abandon a wait on the first fault you
see. A failed poll is ordinary, and the recipe below already forgives a recent
one; only a fault that persists means the channel needs you.

<!-- recipe: health -->
```python
from datetime import UTC, datetime


def inbound_state(records, failing_for=180.0):
    """"up", or "down: <cause>" — whether a human's answer can still reach you.

    Silence has two causes wanting opposite responses: keep waiting, or go fix
    the channel. Only drain faults are decisive here; a failed send says nothing
    about whether answers are arriving.

    A drain fault younger than `failing_for` seconds still reads as up, because
    one failed poll is ordinary — Telegram resets a long poll and the next one
    succeeds. Measured live: two connection resets in a seven-minute run, each
    having happened once and cleared within 27 seconds, while a waiter that gave
    up the moment it saw one abandoned an answer that was still coming. Three
    minutes therefore forgives the routine case and still notices a genuinely
    dead channel quickly. A stopped proxy is never a blip, however recent.
    """
    state, since = "down: never started", None
    for record in records:
        if record["kind"] == "proxy":
            state = "up" if record["event"] == "started" else "down: " + record["reason"]
            since = None
        elif record["kind"] == "fault" and record["source"] == "drain":
            if record["state"] == "cleared":
                state, since = "up", None
            else:
                state, since = "down: " + record["signature"], record["ts"]
    if since is not None:
        age = (datetime.now(UTC) - datetime.fromisoformat(since)).total_seconds()
        if age < failing_for:
            return "up"
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
STATE=$TELEGRAM_HITL_STATE_DIR
CHAT=$(cat "$STATE/chat_id")
curl -s --unix-socket "$STATE/proxy.sock" -X POST http://localhost/setMessageReaction \
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
- **A human replying as an anonymous group admin arrives as
  `GroupAnonymousBot`**, not under their own name. The answer still correlates
  through `reply_to_message`, so nothing breaks — but `from` will not tell you
  who answered, and you should not claim it does.
- **Never start another poller.** The first-party `telegram` plugin and the
  third-party `telegram-bot-skill` each start their own, and a newcomer does
  not get refused — it seizes the stream and kills the existing consumer. A
  409 in the log means exactly this has happened.

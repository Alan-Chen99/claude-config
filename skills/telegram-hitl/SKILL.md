---
name: telegram-hitl
description: Use when a session needs a human decision it cannot make alone - asking a question and waiting hours for an answer, or listening for an unsolicited correction mid-run. Covers the local Telegram proxy, its log, forum-topic choice, and the Bot API traps.
---

# Telegram human-in-the-loop

Reach the human by making ordinary Bot API calls against a local proxy, and read
their answers out of one append-only log. Any number of sessions do this at
once, from any number of containers and from the host. The chat, the proxy and
the log are shared by all of them; the only ground a session holds to itself is
a topic it made.

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

`--background` here, unlike the listener below: a harness background task is
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

## Asking, then listening

Ask in the topic you own (below) and read the whole of it: every human message
there is meant for you, because nothing else is listening. That is what lets the
human just type, rather than hunt for the reply control on a phone — observed
2026-09-25, an answer arrived as a plain message in the topic and a wait keyed
to the question's id sat through it, because what a typed message replies to is
the topic itself (below) and not the question.

Replies still matter, as the catchment a topic misses. An answer sent from
General or from the bot's DM carries no topic id at all, so a topic filter alone
drops it; and a reply carries the full text of the message it answers under
`reply_to_message`, which is what tells you *which* question it settles when
your topic has more than one outstanding.

<!-- recipe: answers -->
```python
def inbox(records, thread_id, after_message_id, my_message_ids=()):
    """Human messages meant for you, oldest first.

    Two catchments, and you want both. `is_topic_message` is true of anything
    *sent to* a topic, not just of replies, so your own topic is yours entire.
    A reply to something you sent counts wherever it lands — measured on this
    channel, an answer sent outside a topic arrived with `message_thread_id`
    absent, and a message to the bot's DM arrived in a private chat carrying
    none either.

    `after_message_id` is the last message you have already dealt with. Pass the
    thread id to mean the whole topic: a topic's id is the id of the service
    message that opened it, so nothing in it sorts lower. Later and higher are
    the same thing within one chat, because the ids come from the one per-chat
    counter the traps below describe — which is also why this is not the
    watermark a listener keeps.
    """
    mine = set(my_message_ids)
    for record in records:
        if record["kind"] != "inbound":
            continue
        message = record["update"].get("message") or {}
        in_my_topic = (message.get("is_topic_message")
                       and message.get("message_thread_id") == thread_id
                       and message.get("message_id", 0) > after_message_id)
        answered = (message.get("reply_to_message") or {}).get("message_id")
        if in_my_topic or (answered is not None and answered in mine):
            yield message
```

**Arm the listener when you create the topic, not when you run out of work.**
The gap between those two is a window where the human types into a log nobody is
reading, and you then wait for an answer already in the file. One listener
covers both of the channel's cases — the answer to your question, and an
unsolicited correction arriving with no question of yours to answer — because
both are a message in your topic.

Waits here are measured in hours, and the log is what to watch, not a socket.
Watch it with `Monitor` rather than a loop that blocks until something arrives:
each message is one notification and you keep working, so the human's thinking
time is not also your idle time, and an open-ended stream of occurrences is what
a persistent monitor is for.

<!-- recipe: listen -->
```python
import time


def listen(path, thread_id, seen, poll=2.0):
    """`(line, seen)` to print and persist, forever. One line, one notification.

    `seen` is the highest `update_id` already announced, and the caller keeps it
    on disk: a monitor's command starts from nothing every time it is armed, so
    that file is the whole of the listener's memory across an expiry. Seed it at
    0 to hear the topic's history as it is read, or at the log's current highest
    `update_id` to hear only what arrives next — a topic you are joining rather
    than opening can hold more history than a notification stream should carry.

    The watermark is an `update_id` and not a message id, because the reply
    catchment reaches other chats and message ids are per-chat: a DM's are a
    separate low-numbered sequence that would sort under the group's and be
    announced forever. `update_id` is one sequence for the whole bot.

    Your own message ids come from the log rather than from the caller. Every
    `sendMessage` into your topic is yours — the same premise as reading the
    topic whole — and that survives a resumed session's new id, where a
    hand-carried list does not.

    Health goes down the same pipe as the messages, because a listener that
    prints only messages is silent in exactly the same way whether the answer is
    still coming or the drain died an hour ago. The first line of every arm is
    therefore the state of the channel you have just armed against.
    """
    state = None
    while True:
        found = list(records(path))
        mine = {record["response"]["result"]["message_id"] for record in found
                if record["kind"] == "outbound"
                and record["method"].lower() == "sendmessage"
                and (record["response"] or {}).get("ok")
                and (record["params"] or {}).get("message_thread_id") == thread_id}
        for record in found:
            if record["kind"] != "inbound" or record["update"]["update_id"] <= seen:
                continue
            update_id = record["update"]["update_id"]
            # one record at a time, so the filter stays the inbox above
            for message in inbox([record], thread_id, thread_id, mine):
                # Whitespace collapsed: one notification per message, not one
                # per line of it. The log keeps what the human actually typed.
                text = " ".join((message.get("text") or "").split())
                yield text or "<non-text message>", update_id
            seen = update_id
        health = inbound_state(found)
        if health != state:
            state = health
            yield "channel " + health, seen
        time.sleep(poll)
```

Write that, the reader, the inbox and the health check to one file in your
scratchpad, and drive it from the bottom of the same file:

```python
import os, pathlib, sys

state = pathlib.Path(os.environ["TELEGRAM_HITL_STATE_DIR"])
thread, mark = int(sys.argv[1]), pathlib.Path(sys.argv[2])
seen = int(mark.read_text()) if mark.exists() else 0
for line, seen in listen(state / "channel.jsonl", thread, seen):
    print(line, flush=True)        # Python buffers otherwise, and a buffered
    mark.write_text(str(seen))     # line is a notification that never arrives
```

The watermark is written after the line is printed, so a kill between the two
repeats one message rather than losing it. Then arm it:

```
Monitor(command="python3 <your-scratchpad>/listen.py 61 <your-scratchpad>/seen",
        description="telegram topic 61: the deploy questions",
        timeout_ms=1800000)
```

Thirty minutes is the cap, so a wait measured in hours is a chain of re-arms:
the expiry notice is the turn in which you arm the next one, and an expiry
nobody acted on is a channel nobody is reading. Re-arm before anything else in
that turn. Both halves of that chain reach a session that has already stopped —
measured 2026-09-26, an event delivered two minutes after a turn ended
re-invoked the session, and so did the expiry notice of a monitor that had
delivered nothing. Not `agent-tools run --background`: a detached child produces
no notification at all, only a `final(<code>)` status line, which is visible on
your next tool result or the user's next turn and wakes nothing.

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
    having happened once and cleared within 27 seconds, while a wait that gave up
    the moment it saw one abandoned an answer that was still coming. Three
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

Do not abandon a wait on the first fault the listener reports. A failed poll is
ordinary, and the check above already forgives a recent one; only a fault that
persists means the channel needs you rather than the human.

## Back-references

A message id correlates records for you. It is not an address the human has —
no Telegram client shows one — so `re: message 62`, or `still waiting on 184`,
asks them to guess which message you mean. **Name the question in its own words
and let Telegram do the pointing:** reply to it, and the client renders the
quoted words above yours and jumps to the original when tapped.

```bash
STATE=$TELEGRAM_HITL_STATE_DIR
curl -s --unix-socket "$STATE/proxy.sock" -X POST http://localhost/sendMessage \
  -H 'Content-Type: application/json' \
  -d "{\"chat_id\": $(cat "$STATE/chat_id"), \"message_thread_id\": 61,
       \"text\": \"Still waiting on this one.\",
       \"reply_parameters\": {\"message_id\": 62,
         \"quote\": \"should the resume PDF be served publicly?\"}}"
```

`quote` is what points *inside* a message. Without it the client quotes the
opening line, which for a long status message is a heading rather than the
question you mean. It has to be an exact substring of the message you are
replying to: measured 2026-09-26, `"quote": "words that do not appear"` came
back `400 QUOTE_TEXT_INVALID`, and so did those same real words aimed at a
different `message_id` — so that error says the words are not in *that* message,
which is as often a wrong id as wrong words. Copy the substring out of what you
sent rather than retyping it.

A reply points at one message, so **keep one open question per message** and the
nudge is always a reply. Where a status message has to carry several, the words
are all the human gets: make them the question, never an index into your own
bookkeeping.

## Topics

The chat is a forum. Messages land in a topic, addressed by `message_thread_id`.

**Make your own topic for the work you are doing, and read it whole.** One
reader per topic is what makes reading it whole safe — two sessions asking in
one topic each take the other's answers. Create it at the first question you
actually have, so a session that never asks leaves nothing behind.

**Name it for the work, not for the session.** A session id tells the human
nothing, and the work outlives the session: a resumed or successor session
carries a new id, and the name is how it finds the topic it is continuing. Join
an existing topic when you are continuing its work — and then correlate by
reply, not by topic, because you are no longer its only reader.

**Say when you stop listening.** A topic outlives the session that made it, and
a human who types into an abandoned one gets no reply and no reaction back. A
last message in the topic when your work ends is the only thing that separates
*finished* from *still thinking*.

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
- **Every message in a forum topic carries `reply_to_message`**, and what it
  points at is the `forum_topic_created` service message that opened the topic —
  measured 2026-09-25, a message typed into topic 38 arrived carrying
  `reply_to_message.message_id` 38. Its presence therefore never means the human
  replied to *you*; only an id of your own in it does, which is why the inbox
  above tests the id against a set rather than testing the field for absence.
- **A human replying as an anonymous group admin arrives as
  `GroupAnonymousBot`**, not under their own name: `from.is_bot` is `true` and
  `from.id` is the same 1087968824 for every such human. Measured on this
  channel, every human message so far has arrived that way — so a sender filter
  that skips bots, to keep your own service messages out of a whole-topic read,
  drops every answer with them. Correlation is unaffected, but `from` will not
  tell you who answered, and you should not claim it does.
- **Never start another poller.** The first-party `telegram` plugin and the
  third-party `telegram-bot-skill` each start their own, and a newcomer does
  not get refused — it seizes the stream and kills the existing consumer. A
  409 in the log means exactly this has happened.

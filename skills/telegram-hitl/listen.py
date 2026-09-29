"""Read the telegram-hitl channel log: listen in a topic, or list the forum's topics.

    python3 listen.py <thread_id> <watermark-file> [--from-now]
    python3 listen.py topics

The listener prints `message <id> in chat <chat>[, reply to <your id>]: <text>`
per human message meant for you and `channel up` / `channel down: <cause>`
whenever the channel's state changes, forever; arm it under a `Monitor`. The
watermark file is its whole memory across re-arms, since a monitor's command
starts from nothing every time it is armed. Absent, the topic's history is heard
first; `--from-now` seeds an absent file at the log's current position instead,
for a topic being joined rather than opened, and never moves one that exists.
The watermark is written after the line is printed, so a kill between the two
repeats one message rather than losing it.
"""

import json
import os
import pathlib
import sys
import time
from datetime import UTC, datetime


def records(path):
    """Every complete record in the channel log, oldest first.

    A final line with no newline is a record another process is still
    appending. Python's file iterator hands the partial line over anyway, where
    a shell `read` loop would not, so stop there.

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


def inbox(records, thread_id, after_message_id, my_message_ids=()):
    """Human messages meant for you, oldest first.

    Two catchments, and you want both. `is_topic_message` is true of anything
    *sent to* a topic, not just of replies, so your own topic is yours entire —
    and it is the discriminator for `message_thread_id`, which carries either a
    reply-chain id or a forum-topic id from the same per-chat counter, so a
    wrong value is never out of range. A reply to something you sent counts
    wherever it lands: measured on this channel, an answer sent outside a topic
    arrived with `message_thread_id` absent, and a message to the bot's DM
    arrived in a private chat carrying none either.

    Every message typed into a forum topic carries `reply_to_message`, pointing
    at the `forum_topic_created` service message that opened the topic, so the
    field's presence never means the human replied to *you*; only an id of your
    own in it does, which is why it is tested against a set.

    No sender filter. Every human here answers as `GroupAnonymousBot` with
    `from.is_bot` true, so skipping bots would drop every answer — and `from`
    never says who answered.

    `after_message_id` is the last message already dealt with. Pass the thread
    id to mean the whole topic: a topic's id is the id of the service message
    that opened it, so nothing in it sorts lower. Later and higher are the same
    thing within one chat, because the ids come from one per-chat counter —
    which is also why this is not the watermark `listen` keeps.
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


def inbound_state(records, failing_for=180.0):
    """"up", or "down: <cause>" — whether a human's answer can still reach you.

    Silence has two causes wanting opposite responses: keep waiting, or go fix
    the channel. Only drain faults are decisive here; a failed send says nothing
    about whether answers are arriving.

    A drain fault younger than `failing_for` seconds still reads as up, because
    one failed poll is ordinary — Telegram resets a long poll and the next one
    succeeds. Measured live: two connection resets in a seven-minute run, each
    cleared within 27 seconds, while a wait that gave up the moment it saw one
    abandoned an answer that was still coming. Three minutes forgives the
    routine case and still notices a genuinely dead channel quickly. A stopped
    proxy is never a blip, however recent.
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


def listen(path, thread_id, seen, poll=2.0):
    """`(line, seen)` to print and persist, forever. One line, one notification.

    `seen` is the highest `update_id` already announced — an `update_id` and
    not a message id, because the reply catchment reaches other chats and
    message ids are per-chat: a DM's are a separate low-numbered sequence that
    would sort under the group's and be announced forever. `update_id` is one
    sequence for the whole bot.

    Your own message ids come from the log rather than from the caller. Every
    `sendMessage` into your topic is yours — the same premise as reading the
    topic whole — and that survives a resumed session's new id, where a
    hand-carried list does not. A send whose body was not JSON is logged with
    its params as a string and cannot name a topic, so it is nobody's.

    Each message line carries the ids a reaction or a reply needs, since no
    client shows them and the log is the only other place to get them; a
    reply to one of your own messages says so, which is the only correlation
    a joined topic offers. Health goes down the same pipe as the messages,
    because a listener that prints only messages is silent in exactly the
    same way whether the answer is still coming or the drain died an hour
    ago, so every arm reports the channel state in its first pass.
    """
    state = None
    while True:
        found = list(records(path))
        mine = {record["response"]["result"]["message_id"] for record in found
                if record["kind"] == "outbound"
                and record["method"].lower() == "sendmessage"
                and isinstance(record["response"], dict) and record["response"].get("ok")
                and isinstance(record["params"], dict)
                and record["params"].get("message_thread_id") == thread_id}
        for record in found:
            if record["kind"] != "inbound" or record["update"]["update_id"] <= seen:
                continue
            update_id = record["update"]["update_id"]
            # one record at a time, so the filter stays the inbox above
            for message in inbox([record], thread_id, thread_id, mine):
                # Whitespace collapsed: one notification per message, not one
                # per line of it. The log keeps what the human actually typed.
                text = " ".join((message.get("text") or "").split())
                chat = (message.get("chat") or {}).get("id")
                answered = (message.get("reply_to_message") or {}).get("message_id")
                tag = f", reply to {answered}" if answered in mine else ""
                yield (f"message {message.get('message_id')} in chat {chat}{tag}: "
                       f"{text or '<non-text message>'}"), update_id
            seen = update_id
        health = inbound_state(found)
        if health != state:
            state = health
            yield "channel " + health, seen
        time.sleep(poll)


def topics(records):
    """The forum's topics, by thread id. There is no `getForumTopics` in the Bot
    API, so the log is the only registry: every topic is a logged
    `createForumTopic`."""
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


def senders(records):
    """Every session that has sent into each topic, and the sends naming none.

    `X-Session-Id` is optional at the proxy, so `unattributed` is sometimes not
    zero: those calls reached the topic and nothing says who made them. The
    reader of this log is the only one placed to notice.

    Only calls Telegram accepted count. A refused send put nothing in the topic,
    so the session that attempted it was never there.

    A topic's creator is attributed from the response, because the request that
    creates a topic cannot name the thread id it is about to get. Sessions are
    compared for equality, so one that sent a truncated id appears twice.
    """
    found = {}
    for record in records:
        if record["kind"] != "outbound":
            continue
        response = record["response"] if isinstance(record["response"], dict) else {}
        params = record["params"] if isinstance(record["params"], dict) else {}
        if not response.get("ok"):
            continue
        if record["method"].lower() == "createforumtopic":
            thread = (response["result"] or {}).get("message_thread_id")
        else:
            thread = params.get("message_thread_id")
        if thread is None:
            continue
        topic = found.setdefault(thread, {"sessions": [], "unattributed": 0})
        session = record.get("session")
        if session is None:
            topic["unattributed"] += 1
        elif session not in topic["sessions"]:
            topic["sessions"].append(session)
    return found


def main(argv):
    log = pathlib.Path(os.environ["TELEGRAM_HITL_STATE_DIR"]) / "channel.jsonl"
    if argv == ["topics"]:
        found = list(records(log))
        been = senders(found)
        for thread, name in sorted(topics(found).items()):
            who = been.get(thread, {"sessions": [], "unattributed": 0})
            tail = f"  +{who['unattributed']} unattributed" if who["unattributed"] else ""
            print(f"{thread}\t{name}\t{' '.join(who['sessions'])}{tail}")
        return
    if len(argv) not in (2, 3) or argv[2:] not in ([], ["--from-now"]):
        sys.exit(__doc__)
    thread, mark = int(argv[0]), pathlib.Path(argv[1])
    if argv[2:] == ["--from-now"] and not mark.exists():
        mark.write_text(str(max((record["update"]["update_id"] for record in records(log)
                                 if record["kind"] == "inbound"), default=0)))
    seen = int(mark.read_text() or 0) if mark.exists() else 0
    for line, seen in listen(log, thread, seen):
        print(line, flush=True)        # Python buffers otherwise, and a buffered
        mark.write_text(str(seen))     # line is a notification that never arrives


if __name__ == "__main__":
    main(sys.argv[1:])

"""Read the telegram-hitl channel log: listen in a topic, wait for one delivery,
peek once, or list the forum's topics.

    python3 listen.py <thread_id>            # under Monitor: every message for you
    python3 listen.py <thread_id> --wait     # foreground: block until one delivery
    python3 listen.py <thread_id> --peek     # one pass: what is unreacted, then return
    python3 listen.py topics

The listener prints `message <id> in chat <chat>[, reply to <your id>]: <text>`
per human message meant for you and `channel up` / `channel down: <cause>`
whenever the channel's state changes. Its only memory across runs is the log:
a message some session has reacted to is handled, and one nobody has reacted
to is announced again at every run until someone does. A monitor's command
starts from nothing every time it is armed, and printed is not received — the
harness truncates and batches lines, drops events past its rate, and a
notification is lost to compaction or to a session that ended — so a watermark
kept by the printer moves past messages nobody read. The reaction is the act
the skill asks for after reading, logged by the proxy like every other call,
so the human and the listener agree on what is unread.

`--wait` is the same reader run as a foreground Bash call: it returns on the
first pass that delivers, with the messages as its output, so the answer is
the tool result and the call is what holds the process — a `claude -p` turn
cannot end while a tool runs, where a background task is killed as it does.
It exits 1 on `channel down`, for the caller to fix before waiting again.
`--peek` is one pass and a return, for a `-p` session between steps, where a
monitor's events during a foreground call are dropped at the turn end.
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
    thing within one chat, because the ids come from one per-chat counter.
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


def reacted(records):
    """`(chat id, message id)` of every message some session has reacted to.

    Any logged `setMessageReaction` naming the message counts, whatever
    Telegram answered: the attempt is the session saying it has read the
    message, and a service message that answers `MESSAGE_ID_INVALID` would
    otherwise be announced at every arm forever. Ids compare as strings because
    a caller may send either form and Telegram accepts both.
    """
    found = set()
    for record in records:
        if record["kind"] != "outbound" or record["method"].lower() != "setmessagereaction":
            continue
        params = record["params"] if isinstance(record["params"], dict) else {}
        if "chat_id" in params and "message_id" in params:
            found.add((str(params["chat_id"]), str(params["message_id"])))
    return found


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


def listen(path, thread_id, poll=2.0, once=False, deadline=None):
    """Lines to print, forever — or with `once`, until a pass has delivered a
    message or found the channel down, or `time.monotonic()` passes
    `deadline`. One line, one notification.

    `seen` is the highest `update_id` scanned in this run — an `update_id` and
    not a message id, because the reply catchment reaches other chats and
    message ids are per-chat: a DM's are a separate low-numbered sequence that
    would sort under the group's. It starts at zero on every arm, since the log
    is the memory: what the first pass leaves out is what `reacted` names.

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
    seen, state = 0, None
    while True:
        found = list(records(path))
        mine = {record["response"]["result"]["message_id"] for record in found
                if record["kind"] == "outbound"
                and record["method"].lower() == "sendmessage"
                and isinstance(record["response"], dict) and record["response"].get("ok")
                and isinstance(record["params"], dict)
                and record["params"].get("message_thread_id") == thread_id}
        handled = reacted(found)
        delivered = False
        for record in found:
            if record["kind"] != "inbound" or record["update"]["update_id"] <= seen:
                continue
            # one record at a time, so the filter stays the inbox above
            for message in inbox([record], thread_id, thread_id, mine):
                chat = (message.get("chat") or {}).get("id")
                if (str(chat), str(message.get("message_id"))) in handled:
                    continue
                # Whitespace collapsed: one notification per message, not one
                # per line of it. The log keeps what the human actually typed.
                text = " ".join((message.get("text") or "").split())
                answered = (message.get("reply_to_message") or {}).get("message_id")
                tag = f", reply to {answered}" if answered in mine else ""
                yield (f"message {message.get('message_id')} in chat {chat}{tag}: "
                       f"{text or '<non-text message>'}")
                delivered = True
            seen = record["update"]["update_id"]
        health = inbound_state(found)
        if health != state:
            yield "channel " + health
            state = health
        if once and (delivered or health != "up"):
            return
        if deadline is not None and time.monotonic() >= deadline:
            return
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
    if len(argv) not in (1, 2) or argv[1:] not in ([], ["--wait"], ["--peek"]):
        sys.exit(__doc__)
    thread, mode = int(argv[0]), argv[1:]
    last = None
    for line in listen(log, thread, once=mode == ["--wait"],
                       deadline=time.monotonic() if mode == ["--peek"] else None):
        print(line, flush=True)        # Python buffers otherwise, and a buffered
        last = line                    # line is a notification that never arrives
    sys.exit(1 if last is not None and last.startswith("channel down") else 0)


if __name__ == "__main__":
    main(sys.argv[1:])

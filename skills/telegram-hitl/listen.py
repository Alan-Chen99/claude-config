"""Read the telegram-hitl channel log: listen in a topic, wait for one delivery,
list the forum's topics, or guard a session's stop.

    python3 listen.py <thread_id>            # under Monitor: every message for you
    python3 listen.py <thread_id> --wait     # under Monitor: the first delivery, then exit
    python3 listen.py topics
    python3 listen.py stop-waiting           # withdraw this session's declared wait
    python3 listen.py stop-hook              # Claude Code Stop hook; payload on stdin

The listener prints `message <id> in chat <chat>[, reply to <your id>]: <text>`
per human message meant for you and `channel up` / `channel down: <cause>`
whenever the channel's state changes. Its only memory across arms is the log:
a message some session has reacted to is handled, and one nobody has reacted
to is announced again at every arm until someone does. A monitor's command
starts from nothing every time it is armed, and printed is not received — the
harness truncates and batches lines, drops events past its rate, and a
notification is lost to compaction or to a session that ended — so a watermark
kept by the printer moves past messages nobody read. The reaction is the act
the skill asks for after reading, logged by the proxy like every other call,
so the human and the listener agree on what is unread.

`--wait` is the single-shot wait. It declares the wait in
`$TELEGRAM_HITL_STATE_DIR/waits/<session id>`, exits 0 after the first pass
that delivered a message and 1 when the channel is down, and withdraws the
declaration on either: a session that was told has nothing left to wait for.
Killed first — the monitor expired, or TaskStop — it leaves the declaration in
place for the stop hook to read.

`stop-hook` is a Claude Code `Stop` hook and acts only in an unattended
session (`CLAUDE_CODE_SESSION_ATTENDED=0`, as `claude -p` runs), where a turn
end is a process exit unless a monitor holds it. A listener armed with no wait
declared is blocked once, both ways out in the reason: the process would sit
on the monitor instead of ending, and the second stop is the session's answer.
A wait declared with no `--wait` listener armed is blocked at every stop,
because ending again is what a model does when it has no better idea, and
this exit would advance a loop past a human who was told to answer: the
reason names the re-arm and `stop-waiting`, the declaration counts the nudges,
the hook sleeps before each nudge after the first (1 s doubling to 30 s, so a
session that never acts costs a turn every half minute rather than every
second) and at the third tells the topic. `stop-waiting` withdraws the
declaration: the one end of a wait the session chooses.
"""

import http.client
import json
import os
import pathlib
import re
import socket
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


def listen(path, thread_id, poll=2.0, once=False):
    """Lines to print, forever — or with `once`, until a pass has delivered a
    message or found the channel down. One line, one notification.

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
            state = health
            yield "channel " + health
        if once and (delivered or state != "up"):
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


def warn(state, session, thread):
    """Tell the topic its session has stopped re-arming — a push, since the loop
    it holds is the human's to fix now. The hold does not depend on it: a
    failure is said on stderr and nothing more."""
    text = (f"⚠ ▸ {session} is not re-arming its wait here: held and nudged until it "
            f"re-arms or runs stop-waiting. Check the loop.")
    try:
        chat_id = int((state / "chat_id").read_text().strip())
        connection = http.client.HTTPConnection("localhost", timeout=10)
        connection.sock = socket.socket(socket.AF_UNIX)
        connection.sock.settimeout(10)
        connection.sock.connect(str(state / "proxy.sock"))
        connection.request("POST", "/sendMessage",
                           json.dumps({"chat_id": chat_id, "message_thread_id": int(thread),
                                       "text": text}),
                           {"Content-Type": "application/json", "X-Session-Id": session})
        status = connection.getresponse().status
    except (OSError, ValueError) as error:
        print(f"telegram-hitl: warning not sent ({error}); the hold stands", file=sys.stderr)
        return
    if status != 200:
        print(f"telegram-hitl: warning not sent (HTTP {status}); the hold stands", file=sys.stderr)


def stop_hook(payload):
    """Decide a Stop: nothing, or one `{"decision": "block", "reason"}` line.

    Only an unattended session, where the turn ending is the process ending
    unless a monitor holds it. An attended session ends turns with a listener
    armed as a matter of course, and a machine without the channel has nothing
    to guard — both are left alone.

    The listeners are read off `background_tasks`, which carries each task's
    command as Claude Code rewrote it; `listen.py <thread>` survives the
    wrapping, and `--wait` is what tells a declared wait's listener from one
    armed to hear corrections while working. A forgotten listener is named
    once (`stop_hook_active` is the second stop); a declared wait with no
    `--wait` listener is held at every stop — Claude Code re-invokes the model
    on each block whatever `stop_hook_active` says (measured 2026-10-01).
    """
    if os.environ.get("CLAUDE_CODE_SESSION_ATTENDED") != "0" or "TELEGRAM_HITL_STATE_DIR" not in os.environ:
        return
    state = pathlib.Path(os.environ["TELEGRAM_HITL_STATE_DIR"])
    declared = state / "waits" / payload["session_id"]
    armed = [task for task in payload.get("background_tasks") or []
             if task.get("status", "running") == "running"
             and re.search(r"listen\.py \d+", task.get("command") or "")]
    waiting = [task for task in armed if "--wait" in task["command"]]
    here = pathlib.Path(__file__).resolve()
    if declared.exists() and not waiting:
        thread, *count = declared.read_text().split()
        nudge = int(count[0]) + 1 if count else 1
        declared.write_text(f"{thread}\n{nudge}\n")
        if nudge > 1:
            time.sleep(min(30, 2 ** (nudge - 2)))
        if nudge == 3:
            warn(state, payload["session_id"], thread)
        reason = (f"telegram-hitl: this session declared a wait on topic {thread} and its "
                  f"listener is gone (expired, or stopped); the wait holds until you act "
                  f"(nudge {nudge}). To keep waiting, re-arm it under Monitor (timeout_ms "
                  f"1800000): python3 {here} {thread} --wait. To stop waiting on purpose: "
                  f"python3 {here} stop-waiting, then end.")
    elif armed and not declared.exists():
        if payload.get("stop_hook_active"):
            return
        task = armed[0]
        thread = re.search(r"listen\.py (\d+)", task["command"]).group(1)
        reason = (f"telegram-hitl: the listener on topic {thread} (task {task['id']}) is armed "
                  f"and no wait is declared, so this session cannot end while it runs. "
                  f"TaskStop {task['id']} to end, or arm python3 {here} {thread} --wait under "
                  f"Monitor to stay and wait for the human.")
    else:
        return
    print(json.dumps({"decision": "block", "reason": reason}))


def main(argv):
    if argv == ["stop-hook"]:
        stop_hook(json.load(sys.stdin))
        return
    log = pathlib.Path(os.environ["TELEGRAM_HITL_STATE_DIR"]) / "channel.jsonl"
    if argv == ["topics"]:
        found = list(records(log))
        been = senders(found)
        for thread, name in sorted(topics(found).items()):
            who = been.get(thread, {"sessions": [], "unattributed": 0})
            tail = f"  +{who['unattributed']} unattributed" if who["unattributed"] else ""
            print(f"{thread}\t{name}\t{' '.join(who['sessions'])}{tail}")
        return
    if argv == ["stop-waiting"]:
        session = os.environ.get("CLAUDE_CODE_SESSION_ID")
        if not session:
            sys.exit("stop-waiting needs CLAUDE_CODE_SESSION_ID: the declaration is keyed by it")
        declaration = log.parent / "waits" / session
        if not declaration.exists():
            print("no wait declared")
            return
        thread = declaration.read_text().split()[0]
        declaration.unlink()
        print(f"wait on topic {thread} withdrawn")
        return
    if len(argv) not in (1, 2) or argv[1:] not in ([], ["--wait"]):
        sys.exit(__doc__)
    thread, once = int(argv[0]), argv[1:] == ["--wait"]
    declaration = None
    if once:
        session = os.environ.get("CLAUDE_CODE_SESSION_ID")
        if not session:
            sys.exit("--wait needs CLAUDE_CODE_SESSION_ID: the declaration is keyed by the "
                     "session the stop hook will hold to it")
        declaration = log.parent / "waits" / session
        declaration.parent.mkdir(exist_ok=True)
        declaration.write_text(str(thread))
    last = None
    for line in listen(log, thread, once=once):
        print(line, flush=True)        # Python buffers otherwise, and a buffered
        last = line                    # line is a notification that never arrives
    declaration.unlink()
    sys.exit(1 if last.startswith("channel down") else 0)


if __name__ == "__main__":
    main(sys.argv[1:])

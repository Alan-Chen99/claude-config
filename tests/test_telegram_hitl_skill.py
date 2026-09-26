"""The skill's recipes are executable, so they get executed here."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills" / "telegram-hitl" / "SKILL.md"


def _recipe(*names: str) -> dict:
    """Exec marked python blocks from the skill into one shared namespace.

    Several names because the skill's listener calls the reader, the inbox and
    the health check by name, the way the file an agent assembles does.
    """
    text = SKILL.read_text()
    namespace: dict = {}
    for name in names:
        marker = f"<!-- recipe: {name} -->"
        assert marker in text, f"the skill has no recipe marked {name}"
        opening = text.index("```python", text.index(marker))
        body = text[opening + len("```python"):text.index("```", opening + 3)]
        exec(compile(body, str(SKILL), "exec"), namespace)
    return namespace


class _Slept(Exception):
    """Raised in place of the listener's poll, to bound one pass of its loop."""


def test_the_log_reader_skips_a_partial_final_line(tmp_path) -> None:
    """The documented Python trap: a record still being appended has no newline."""
    path = tmp_path / "channel.jsonl"
    path.write_bytes(b'{"kind":"proxy","event":"started"}\n'
                     b'{"kind":"inbound","update":{"update_id":1}}\n'
                     b'{"kind":"inbound","update":{"upda')

    records = _recipe("read-log")["records"]

    assert [r["kind"] for r in records(path)] == ["proxy", "inbound"]


def test_the_log_reader_surfaces_a_damaged_line_and_keeps_going(tmp_path) -> None:
    """A failed write must not make everything appended after it unreadable."""
    path = tmp_path / "channel.jsonl"
    path.write_bytes(b'{"kind":"proxy","event":"started"}\n'
                     b'{"kind":"outbound","method":"sendMes\n'
                     b'{"kind":"inbound","update":{"update_id":9}}\n')

    records = _recipe("read-log")["records"]

    found = list(records(path))
    assert [r["kind"] for r in found] == ["proxy", "damaged", "inbound"]
    assert "sendMes" in found[1]["raw"]


def test_the_inbox_takes_whatever_the_human_typed_in_your_own_topic() -> None:
    """A topic with one reader needs no reply control: anything in it is yours.

    Its past is not, though. Reading a topic whole reaches back to the service
    message that opened it, and to every message already dealt with.
    """
    inbox = _recipe("answers")["inbox"]
    log = [
        {"kind": "inbound", "update": {"message": {
            "message_id": 6, "message_thread_id": 6, "is_topic_message": True,
            "forum_topic_created": {"name": "research: alpha"}}}},
        {"kind": "inbound", "update": {"message": {
            "message_id": 50, "message_thread_id": 9, "is_topic_message": True,
            "text": "another session's topic"}}},
        {"kind": "inbound", "update": {"message": {
            "message_id": 52, "message_thread_id": 6, "is_topic_message": True,
            "text": "ship it"}}},
        {"kind": "inbound", "update": {"message": {
            "message_id": 53, "message_thread_id": 6, "is_topic_message": True,
            "text": "and bump the version"}}},
    ]

    assert [m["text"] for m in inbox(log, 6, 51)] == ["ship it", "and bump the version"]
    assert [m["text"] for m in inbox(log, 6, 52)] == ["and bump the version"]


def test_the_inbox_catches_a_reply_that_landed_outside_the_topic() -> None:
    """Measured live: an answer sent outside a topic carries no thread id at
    all, and a message to the bot's DM arrives in a private chat that has none
    to carry. A topic filter alone loses both."""
    inbox = _recipe("answers")["inbox"]
    log = [
        {"kind": "inbound", "update": {"message": {
            "message_id": 31, "text": "yes, ship it",
            "reply_to_message": {"message_id": 30, "text": "Ship it?"}}}},
        {"kind": "inbound", "update": {"message": {
            "message_id": 32, "text": "someone else's answer",
            "reply_to_message": {"message_id": 12, "text": "their question"}}}},
        {"kind": "inbound", "update": {"message": {"message_id": 33, "text": "hello"}}},
    ]

    assert [m["text"] for m in inbox(log, 6, 30, {30})] == ["yes, ship it"]
    assert list(inbox(log, 6, 30)) == []


def test_the_topic_registry_is_reconstructed_from_the_log() -> None:
    """There is no getForumTopics, so the log is the only registry there is."""
    topics = _recipe("topics")["topics"]
    log = [
        {"kind": "outbound", "method": "createForumTopic", "params": {"name": "alpha"},
         "response": {"ok": True, "result": {"message_thread_id": 6, "name": "alpha"}}},
        {"kind": "outbound", "method": "createForumTopic", "params": {"name": "beta"},
         "response": {"ok": True, "result": {"message_thread_id": 7, "name": "beta"}}},
        {"kind": "outbound", "method": "editForumTopic",
         "params": {"message_thread_id": 7, "name": "beta (renamed)"},
         "response": {"ok": True, "result": True}},
        {"kind": "outbound", "method": "createForumTopic", "params": {"name": "refused"},
         "response": {"ok": False, "description": "not enough rights to create a topic"}},
        {"kind": "outbound", "method": "deleteForumTopic",
         "params": {"message_thread_id": 6}, "response": {"ok": True, "result": True}},
        {"kind": "inbound", "update": {"message": {"message_id": 1}}},
    ]

    assert topics(log) == {7: "beta (renamed)"}


def test_the_inbound_state_distinguishes_a_dead_channel_from_a_quiet_one() -> None:
    """The whole point of logging faults: silence has two causes. A single
    failed poll is not one of them — measured live, one cleared 26 seconds
    later, and treating it as a dead channel abandoned an answer still coming.
    """
    inbound_state = _recipe("health")["inbound_state"]
    now = datetime.now(UTC)

    def at(seconds_ago: float) -> str:
        return (now - timedelta(seconds=seconds_ago)).isoformat()

    started = [{"ts": at(600), "kind": "proxy", "event": "started"}]
    quiet = started + [{"ts": at(500), "kind": "inbound", "update": {}}]
    blip = quiet + [{"ts": at(5), "kind": "fault", "source": "drain",
                     "state": "failing", "signature": "getUpdates:URLError"}]
    stuck = quiet + [{"ts": at(900), "kind": "fault", "source": "drain",
                      "state": "failing", "signature": "getUpdates:http409"}]

    assert inbound_state([]) == "down: never started"
    assert inbound_state(quiet) == "up"
    assert inbound_state(blip) == "up"
    assert inbound_state(stuck) == "down: getUpdates:http409"
    assert inbound_state(blip + [{"ts": at(1), "kind": "fault", "source": "drain",
                                  "state": "cleared",
                                  "signature": "getUpdates:URLError"}]) == "up"
    # a stopped proxy is not a blip, however recently it stopped
    assert inbound_state(started + [{"ts": at(2), "kind": "proxy", "event": "stopped",
                                     "reason": "SIGTERM"}]) == "down: SIGTERM"
    # a failed send says nothing about whether answers are arriving
    assert inbound_state(quiet + [{"ts": at(900), "kind": "fault", "source": "forward",
                                   "state": "failing",
                                   "signature": "forward:URLError"}]) == "up"


def test_the_listener_announces_each_message_once_and_says_what_the_channel_is(
    tmp_path, monkeypatch,
) -> None:
    """A monitor's command restarts from nothing at every re-arm, so the
    watermark on disk is the whole of the listener's memory. Replaying a topic
    is a notification flood; advancing past a message is a lost answer.
    """
    namespace = _recipe("read-log", "answers", "health", "listen")
    monkeypatch.setattr(namespace["time"], "sleep", lambda _: (_ for _ in ()).throw(_Slept()))
    path = tmp_path / "channel.jsonl"
    path.write_text("".join(json.dumps(record) + "\n" for record in [
        {"kind": "proxy", "event": "started"},
        # the service message that opened the topic: its id is the thread id
        {"kind": "inbound", "update": {"update_id": 10, "message": {
            "message_id": 6, "message_thread_id": 6, "is_topic_message": True,
            "forum_topic_created": {"name": "deploy"}}}},
        {"kind": "outbound", "method": "sendMessage",
         "params": {"message_thread_id": 6, "text": "Ship it?"},
         "response": {"ok": True, "result": {"message_id": 51}}},
        {"kind": "inbound", "update": {"update_id": 11, "message": {
            "message_id": 52, "message_thread_id": 6, "is_topic_message": True,
            "text": "ship it,\nand bump\tthe version"}}},
        # a reply from the bot's DM: low message id, own update_id sequence
        {"kind": "inbound", "update": {"update_id": 12, "message": {
            "message_id": 4, "text": "one more thing",
            "reply_to_message": {"message_id": 51}}}},
    ]))

    def one_pass(seen: int) -> list:
        announced = []
        with pytest.raises(_Slept):
            for line, mark in namespace["listen"](path, 6, seen):
                announced.append((line, mark))
        return announced

    first = one_pass(0)

    # the topic's own service message is not an announcement, the DM reply is,
    # and a message arrives as one line however the human typed it
    assert first == [("ship it, and bump the version", 11),
                     ("one more thing", 12),
                     ("channel up", 12)]
    # the re-arm reports the channel it armed against and nothing else
    assert one_pass(first[-1][1]) == [("channel up", 12)]


def test_the_skill_names_the_session_variable_that_exists() -> None:
    """Claude Code sets CLAUDE_CODE_SESSION_ID and there is no CLAUDE_SESSION_ID.
    An example reading the wrong one sends an empty header rather than failing,
    so the log's record of who called comes out blank — worse than an error.
    """
    text = SKILL.read_text()
    assert "$CLAUDE_CODE_SESSION_ID" in text
    assert "$CLAUDE_SESSION_ID" not in text


@pytest.mark.parametrize("status", ["`400`", "`403`", "`411`", "`502`"])
def test_the_skill_documents_every_refusal_the_proxy_returns(status) -> None:
    """An agent that meets a refusal has only this document to explain it, and
    three of the four come from the proxy rather than from Telegram."""
    assert status in SKILL.read_text()


@pytest.mark.parametrize("trap", [
    "is_topic_message",          # message_thread_id carries two different ids
    "MESSAGE_ID_INVALID",        # reactability is type-specific
    "REACTION_INVALID",          # the reaction alphabet is fixed
    "General",                   # the General topic is not addressable
    "GroupAnonymousBot",         # a human answers as a bot, so is_bot filters drop them
    "migrate_to_chat_id",        # enabling Topics changes the chat id
    "partial",                   # reading a file under append needs care
    "QUOTE_TEXT_INVALID",        # a quote must be exact, and in that very message
    "forum_topic_created",       # every topic message replies to it, so the
                                 # field's presence proves nothing
])
def test_the_skill_still_carries_every_trap_that_cost_time(trap) -> None:
    """These were measured the hard way; an edit must not quietly drop one."""
    assert trap in SKILL.read_text()

"""The skill's recipes are executable, so they get executed here."""

from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills" / "telegram-hitl" / "SKILL.md"


def _recipe(name: str) -> dict:
    """Exec one marked python block from the skill and return its namespace."""
    text = SKILL.read_text()
    marker = f"<!-- recipe: {name} -->"
    assert marker in text, f"the skill has no recipe marked {name}"
    opening = text.index("```python", text.index(marker))
    body = text[opening + len("```python"):text.index("```", opening + 3)]
    namespace: dict = {}
    exec(compile(body, str(SKILL), "exec"), namespace)
    return namespace


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


def test_the_answer_finder_matches_the_reply_to_a_question(tmp_path) -> None:
    answer_to = _recipe("answers")["answer_to"]
    log = [
        {"kind": "inbound", "update": {"message": {"message_id": 50, "text": "hello"}}},
        {"kind": "inbound", "update": {"message": {
            "message_id": 51, "text": "yes, ship it",
            "reply_to_message": {"message_id": 49, "text": "should I ship?"}}}},
    ]

    assert answer_to(log, 49)["text"] == "yes, ship it"
    assert answer_to(log, 12) is None


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
    """The whole point of logging faults: silence has two causes."""
    inbound_state = _recipe("health")["inbound_state"]
    started = [{"kind": "proxy", "event": "started"}]
    quiet = started + [{"kind": "inbound", "update": {}}]
    stolen = quiet + [{"kind": "fault", "source": "drain", "state": "failing",
                       "signature": "getUpdates:http409"}]

    assert inbound_state([]) == "down: never started"
    assert inbound_state(quiet) == "up"
    assert inbound_state(stolen) == "down: getUpdates:http409"
    assert inbound_state(stolen + [{"kind": "fault", "source": "drain",
                                    "state": "cleared",
                                    "signature": "getUpdates:http409"}]) == "up"
    assert inbound_state(started + [{"kind": "proxy", "event": "stopped",
                                     "reason": "SIGTERM"}]) == "down: SIGTERM"
    assert inbound_state(quiet + [{"kind": "fault", "source": "forward",
                                   "state": "failing",
                                   "signature": "forward:URLError"}]) == "up"


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
    "migrate_to_chat_id",        # enabling Topics changes the chat id
    "partial",                   # reading a file under append needs care
])
def test_the_skill_still_carries_every_trap_that_cost_time(trap) -> None:
    """These were measured the hard way; an edit must not quietly drop one."""
    assert trap in SKILL.read_text()

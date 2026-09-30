"""The pre-output record, and the ntfy "Done" push that reads it.

Covers the seam between the two modules: `pre_output.record` writes a session's
summary, `ntfy_hook` sends it, and a turn boundary invalidates it.
"""

import io
import json
import uuid
from pathlib import Path

import pytest

from claude_config import ntfy_hook
from claude_config.pre_output import record

PAYLOAD = {
    "turn": 1,
    "summary": "rewrote the ntfy summary source",
    "workflow": "none",
    "uncertainties": ["whether the push renders two lines"],
    "possible-verification": ["read ~/.cache/claude-config/ntfy_hook.log"],
    "possible-next-steps": ["commit"],
}


@pytest.fixture
def session(monkeypatch):
    """A session id nothing else can collide with, cleaned up afterwards."""
    sid = f"test-{uuid.uuid4().hex}"
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", sid)
    yield sid
    record.record_path(sid).unlink(missing_ok=True)


@pytest.fixture
def no_api_key(monkeypatch):
    """No OpenRouter key, so any fallback to the LLM path is visible in the body."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


def _stdin(monkeypatch, payload: dict) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))


# --- recording ------------------------------------------------------------


def test_a_recorded_turn_lands_on_disk(session):
    assert record.main([json.dumps(PAYLOAD)]) == 0
    assert json.loads(record.record_path(session).read_text()) == PAYLOAD


def test_re_recording_the_same_turn_replaces_it(session):
    record.main([json.dumps(PAYLOAD)])
    record.main([json.dumps({**PAYLOAD, "summary": "second thoughts"})])
    written = json.loads(record.record_path(session).read_text())
    assert written["summary"] == "second thoughts"


def test_the_reminder_prints_even_when_nothing_is_recorded(monkeypatch, capsys):
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    assert record.main([json.dumps(PAYLOAD)]) == 1
    captured = capsys.readouterr()
    assert record.RULES in captured.out
    assert "recorded successfully" not in captured.out
    assert "CLAUDE_CODE_SESSION_ID" in captured.err


def test_the_reminder_stays_inside_its_token_budget(session, capsys):
    """Printed at the end of every turn, and again after any further tool call.
    `doc-budget.toml` prices the `.md` tree; this is not `.md`, so it is pinned
    here: 42 tokens when pinned, by the local tokenizer, and the pin is that size
    divided by 0.8, so 80% of it is where the text sits now and the first growth
    past it pays a registry group's cut. Over: cut the reminder, not the number
    (`conventions/documentation.md`, *Documentation budget*)."""
    from claude_config.count_tokens import _count_local

    assert record.main([json.dumps(PAYLOAD)]) == 0
    assert _count_local(capsys.readouterr().out) <= 52


@pytest.mark.parametrize(
    "argv, expected_in_stderr",
    [
        (["{not json"], "not valid JSON"),
        (['["a list"]'], "expected an object"),
        ([json.dumps({"turn": 1})], "summary"),
        ([json.dumps({**PAYLOAD, "summary": "   "})], "summary"),
        (['{"summary":', '"split by the shell"}'], "exactly one JSON argument"),
    ],
)
def test_unusable_arguments_are_refused_loudly(session, capsys, argv, expected_in_stderr):
    assert record.main(argv) == 1
    assert expected_in_stderr in capsys.readouterr().err
    assert not record.record_path(session).exists()


# --- the "Done" push ------------------------------------------------------


def test_the_done_push_sends_the_recorded_summary(session, monkeypatch):
    """A key being available must not matter: the record wins outright."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-would-have-worked")
    monkeypatch.setattr(
        ntfy_hook, "generate_summary",
        lambda *a, **k: pytest.fail("the LLM was called despite a recorded summary"),
    )
    record.main([json.dumps(PAYLOAD)])

    body = ntfy_hook.build_notification("/nonexistent/transcript.jsonl", "stop", "", session)

    assert body.splitlines()[0] == PAYLOAD["summary"]
    assert len(body.splitlines()) == 2  # summary + location, nothing else


def test_a_turn_that_recorded_nothing_falls_back(session, no_api_key):
    body = ntfy_hook.build_notification("/nonexistent/transcript.jsonl", "stop", "", session)
    assert body.startswith("[err] No API key")


def test_mid_turn_notifications_ignore_the_record(session, no_api_key):
    """The newest record describes the previous turn, so only "stop" may use it."""
    record.main([json.dumps(PAYLOAD)])
    for hook_type in ("permission", "idle", "question", "resumed", "stalled"):
        body = ntfy_hook.build_notification("/nonexistent/t.jsonl", hook_type, "", session)
        assert body.startswith("[err] No API key"), hook_type


def test_an_unreadable_record_falls_back(session, no_api_key):
    record.record_path(session).write_text("{ truncated")
    body = ntfy_hook.build_notification("/nonexistent/transcript.jsonl", "stop", "", session)
    assert body.startswith("[err] No API key")


# --- the turn boundary ----------------------------------------------------


def test_a_new_prompt_clears_the_record(session, monkeypatch):
    record.main([json.dumps(PAYLOAD)])
    _stdin(monkeypatch, {"session_id": session, "prompt": "next thing please"})

    ntfy_hook.do_cancel(None)

    assert not record.record_path(session).exists()


def test_a_task_notification_clears_the_record_too(session, monkeypatch):
    """It keeps the donefile, but it still starts a turn of its own."""
    record.main([json.dumps(PAYLOAD)])
    ntfy_hook.donefile_path(session).touch()
    _stdin(monkeypatch, {"session_id": session, "prompt": "<task-notification>done</task-notification>"})

    ntfy_hook.do_cancel(None)

    assert not record.record_path(session).exists()
    assert ntfy_hook.donefile_path(session).exists()
    ntfy_hook.donefile_path(session).unlink()

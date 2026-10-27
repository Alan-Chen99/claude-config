"""A subagent call's render says where that subagent's own log is.

The parent's result names the agent by id only, so without this line a reader
has to know the transcript layout to open the log of the agent they are reading
about. Every test drives a front-end's ``main()`` over a tree on disk: where the
log is found is decided by the file layout, which nothing short of a real tree
exercises.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from claude_config.cc_pretty.main import main as cc_main
from claude_config.cc_pretty_intercept.main import main as intercept_main
from claude_config.opencode_pretty.main import main as opencode_main

SESSION = "5e551011-0000-4000-8000-000000000001"
RESUMED = "5e551011-0000-4000-8000-000000000002"
AGENT = "a0123456789abcdef"
NESTED = "afedcba9876543210"
RUN = "wf_0011aa22-bb3"


def tool_call(tool_id: str, name: str, result_text: str, tool_use_result) -> list[dict]:
    """An assistant tool_use and the user record carrying its result."""
    return [
        {"type": "assistant", "message": {"id": f"msg_{tool_id}", "role": "assistant",
                                          "model": "claude-test",
                                          "content": [{"type": "tool_use", "id": tool_id,
                                                       "name": name, "input": {}}]}},
        {"type": "user", "toolUseResult": tool_use_result,
         "message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": tool_id,
              "content": [{"type": "text", "text": result_text}]}]}},
    ]


def write_log(path: Path, records: list[dict], session: str = SESSION) -> Path:
    """Chain ``records`` by uuid, as Claude Code writes them, and save them."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines, parent = [], None
    for i, rec in enumerate(records):
        uuid = f"00000000-0000-4000-8000-{i:012d}"
        lines.append(json.dumps({"uuid": uuid, "parentUuid": parent, "sessionId": session,
                                 "timestamp": "2026-10-27T14:00:00.000Z", **rec}))
        parent = uuid
    path.write_text("\n".join(lines) + "\n")
    return path


def a_transcript(path: Path) -> Path:
    return write_log(path, [{"type": "user", "message": {"role": "user", "content": "go"}}])


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "config"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(root))
    return root / "projects" / "-repo"


def render(main, *argv: str) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        main([*argv, "--no-color"])
    return buf.getvalue()


def both_densities(main, *argv: str) -> list[str]:
    return [render(main, *argv), render(main, *argv, "--skeleton")]


# ─── Claude Code transcripts ─────────────────────────────────────────────────


@pytest.mark.parametrize("tool_use_result", [
    {"status": "completed", "agentId": AGENT, "agentType": "general-purpose"},
    {"isAsync": True, "status": "async_launched", "agentId": AGENT,
     "outputFile": f"/tmp/tasks/{AGENT}.output"},
], ids=["foreground", "background"])
def test_an_agent_result_names_the_log_its_subagent_wrote(project, tool_use_result) -> None:
    log = write_log(project / f"{SESSION}.jsonl",
                    tool_call("toolu_1", "Agent", "agent text", tool_use_result))
    transcript = a_transcript(project / SESSION / "subagents" / f"agent-{AGENT}.jsonl")
    for out in both_densities(cc_main, str(log)):
        assert f"⇢ subagent {AGENT} log: {transcript}" in out


def test_an_agent_with_no_transcript_says_so_and_where_it_looked(project) -> None:
    log = write_log(project / f"{SESSION}.jsonl", tool_call(
        "toolu_1", "Agent", "agent text", {"status": "completed", "agentId": AGENT}))
    for out in both_densities(cc_main, str(log)):
        assert (f"⇢ subagent {AGENT} log: not found under "
                f"{project / SESSION / 'subagents'} or {project.parent}") in out


def test_a_sendmessage_resume_names_the_resumed_agent_s_log(project) -> None:
    log = write_log(project / f"{SESSION}.jsonl", tool_call(
        "toolu_1", "SendMessage", '{"success":true}',
        {"success": True, "resumedAgentId": AGENT, "revivedAgentId": AGENT}))
    transcript = a_transcript(project / SESSION / "subagents" / f"agent-{AGENT}.jsonl")
    for out in both_densities(cc_main, str(log)):
        assert out.count(f"⇢ subagent {AGENT} log: {transcript}") == 1


@pytest.mark.parametrize(("pinned", "named"), [
    (AGENT, True),
    # `pin` also carries peer and cloud sessions, which have no agent transcript.
    ("7a2c9e11-0000-4000-8000-00000000beef", False),
])
def test_a_sendmessage_pin_names_a_log_only_when_it_is_an_agent(project, pinned, named) -> None:
    log = write_log(project / f"{SESSION}.jsonl", tool_call(
        "toolu_1", "SendMessage", '{"success":true}',
        {"success": True, "pin": {"id": pinned, "name": pinned}}))
    a_transcript(project / SESSION / "subagents" / f"agent-{AGENT}.jsonl")
    for out in both_densities(cc_main, str(log)):
        assert ("⇢ subagent" in out) is named


def test_a_workflow_launch_names_its_transcript_dir(project) -> None:
    run_dir = project / SESSION / "subagents" / "workflows" / RUN
    a_transcript(run_dir / f"agent-{AGENT}.jsonl")
    a_transcript(run_dir / f"agent-{NESTED}.jsonl")
    (run_dir / "journal.jsonl").write_text("{}\n")
    log = write_log(project / f"{SESSION}.jsonl", tool_call(
        "toolu_1", "Workflow", "Workflow launched in background.",
        {"status": "async_launched", "runId": RUN, "transcriptDir": str(run_dir)}))
    for out in both_densities(cc_main, str(log)):
        assert f"⇢ workflow {RUN} logs: {run_dir}/ (2 agent logs)" in out


def test_a_workflow_whose_directory_is_gone_says_so(project) -> None:
    run_dir = project / SESSION / "subagents" / "workflows" / RUN
    log = write_log(project / f"{SESSION}.jsonl", tool_call(
        "toolu_1", "Workflow", "Workflow launched in background.",
        {"status": "async_launched", "runId": RUN, "transcriptDir": str(run_dir)}))
    for out in both_densities(cc_main, str(log)):
        assert f"⇢ workflow {RUN} logs: {run_dir}/ (directory not found)" in out


def test_a_resumed_session_finds_agents_under_the_session_that_spawned_them(project) -> None:
    """A resume copies the records under a new session id, never the agents' logs."""
    log = write_log(project / f"{RESUMED}.jsonl", tool_call(
        "toolu_1", "Agent", "agent text", {"status": "completed", "agentId": AGENT}),
        session=RESUMED)
    transcript = a_transcript(project / SESSION / "subagents" / f"agent-{AGENT}.jsonl")
    for out in both_densities(cc_main, str(log)):
        assert f"⇢ subagent {AGENT} log: {transcript}" in out


def test_a_subagent_s_log_finds_the_agents_it_spawned(project) -> None:
    subagents = project / SESSION / "subagents"
    log = write_log(subagents / f"agent-{AGENT}.jsonl", tool_call(
        "toolu_1", "Agent", "agent text", {"status": "completed", "agentId": NESTED}))
    transcript = a_transcript(subagents / f"agent-{NESTED}.jsonl")
    for out in both_densities(cc_main, str(log)):
        assert f"⇢ subagent {NESTED} log: {transcript}" in out


def test_a_log_copied_out_of_the_config_dir_reads_its_own_tree(tmp_path, project) -> None:
    copy = tmp_path / "copied"
    log = write_log(copy / f"{SESSION}.jsonl", tool_call(
        "toolu_1", "Agent", "agent text", {"status": "completed", "agentId": AGENT}))
    a_transcript(project / SESSION / "subagents" / f"agent-{AGENT}.jsonl")
    transcript = a_transcript(copy / SESSION / "subagents" / f"agent-{AGENT}.jsonl")
    for out in both_densities(cc_main, str(log)):
        assert f"⇢ subagent {AGENT} log: {transcript}" in out


def notification(task_id: str) -> str:
    return (f"<task-notification>\n<task-id>{task_id}</task-id>\n"
            f"<status>completed</status>\n</task-notification>")


@pytest.mark.parametrize("delivered_as", ["user turn", "queued_command"])
def test_an_agent_s_task_notification_names_its_log(project, delivered_as) -> None:
    def record(task_id: str) -> dict:
        if delivered_as == "user turn":
            return {"type": "user", "message": {"role": "user", "content": notification(task_id)}}
        return {"type": "attachment", "attachment": {
            "type": "queued_command", "commandMode": "task-notification",
            "prompt": notification(task_id)}}

    # A background shell's task id names no transcript: no line, not a miss.
    log = write_log(project / f"{SESSION}.jsonl", [record(AGENT), record("b4shjob9x")])
    transcript = a_transcript(project / SESSION / "subagents" / f"agent-{AGENT}.jsonl")
    for out in both_densities(cc_main, str(log)):
        assert f"⇢ subagent {AGENT} log: {transcript}" in out
        assert out.count("⇢") == 1


def test_a_result_that_spawned_nothing_gets_no_line(project) -> None:
    log = write_log(project / f"{SESSION}.jsonl", tool_call(
        "toolu_1", "Bash", f"agentId: {AGENT}", {"stdout": f"agentId: {AGENT}"}))
    a_transcript(project / SESSION / "subagents" / f"agent-{AGENT}.jsonl")
    for out in both_densities(cc_main, str(log)):
        assert "⇢" not in out


# ─── Intercept captures ──────────────────────────────────────────────────────


AGENT_TEXT = (f"Async agent launched successfully.\nagentId: {AGENT} (internal ID)\n"
              f"output_file: /tmp/tasks/{AGENT}.output")


def capture(tmp_path: Path, messages: list[dict]) -> str:
    path = tmp_path / "0001.json"
    path.write_text(json.dumps({
        "timestamp": "2026-10-27T14:00:00+00:00",
        "request": {"model": "claude-test", "messages": messages},
        "response": {"model": "claude-test", "content": [{"type": "text", "text": "ok"}]},
    }))
    return str(path)


def agent_result(text: str) -> dict:
    return {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "toolu_1", "content": [{"type": "text", "text": text}]}]}


def test_a_captured_agent_result_names_its_log(tmp_path, project) -> None:
    transcript = a_transcript(project / SESSION / "subagents" / f"agent-{AGENT}.jsonl")
    path = capture(tmp_path, [
        {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_1", "name": "Agent", "input": {}}]},
        agent_result(AGENT_TEXT),
    ])
    for out in both_densities(intercept_main, path, "--no-system", "--no-tools"):
        assert f"⇢ subagent {AGENT} log: {transcript}" in out


def test_a_captured_agent_with_no_transcript_says_so(tmp_path, project) -> None:
    path = capture(tmp_path, [
        {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_1", "name": "Agent", "input": {}}]},
        agent_result(AGENT_TEXT),
    ])
    for out in both_densities(intercept_main, path, "--no-system", "--no-tools"):
        assert f"⇢ subagent {AGENT} log: not found under {project.parent}" in out


@pytest.mark.parametrize("exists", [True, False])
def test_a_capture_without_the_call_names_only_an_agent_that_resolves(tmp_path, project, exists) -> None:
    """A request can start after the tool_use, leaving its result's tool unnamed."""
    if exists:
        a_transcript(project / SESSION / "subagents" / f"agent-{AGENT}.jsonl")
    path = capture(tmp_path, [agent_result(AGENT_TEXT)])
    for out in both_densities(intercept_main, path, "--no-system", "--no-tools"):
        assert ("⇢ subagent" in out) is exists
        assert "not found" not in out


# ─── opencode exports ────────────────────────────────────────────────────────


def test_an_opencode_task_names_its_child_session(tmp_path) -> None:
    child = "ses_child0000000000000001"
    export = {
        "info": {"id": "ses_parent000000000000001", "directory": "/repo"},
        "messages": [
            {"info": {"role": "user", "id": "msg_1", "time": {"created": 1_700_000_000_000}},
             "parts": [{"type": "text", "text": "review it"}]},
            {"info": {"role": "assistant", "id": "msg_2", "parentID": "msg_1",
                      "time": {"created": 1_700_000_001_000}},
             "parts": [{"type": "tool", "tool": "task", "callID": "call_1", "state": {
                 # Running at export time: no output yet, the child already named.
                 "status": "running", "input": {"description": "review"},
                 "metadata": {"parentSessionId": "ses_parent000000000000001",
                              "sessionId": child}}}]},
        ],
    }
    path = tmp_path / "export.json"
    path.write_text(json.dumps(export))
    for out in both_densities(opencode_main, "ses_parent000000000000001",
                              "--from-file", str(path)):
        assert f"⇢ subagent session {child}: agent-tools opencode-pretty {child}" in out

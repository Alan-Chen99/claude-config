"""cc-pretty accepts a session id, a subagent id, or a path.

The fixture tree carries the two shapes a naive search gets wrong: a subagent
transcript nested under `workflows/wf_<id>/`, which a non-recursive glob misses
entirely, and a `journal.jsonl` beside it, which shares the extension but is a
Workflow record file rather than a transcript.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from claude_config.cc_pretty.locate import Located, SessionNotFound, resolve_log_arg
from claude_config.cc_pretty.main import main

RECORD = {
    "type": "user",
    "sessionId": "aaaaaaaa-1111-2222-3333-444444444444",
    "cwd": "/tmp/x",
    "version": "2.1.269",
    "message": {"role": "user", "content": [{"type": "text", "text": "hello fixture"}]},
}

SESSION = "fdca30e5-0961-4ff2-8197-f8554d372964"
SIBLING = "fdca9999-0000-0000-0000-000000000000"
SUBAGENT = "agent-a33c42903d63fc91e"
WORKFLOW_SUBAGENT = "agent-b71ff0c2d4e5a6b78"


def _write(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(RECORD) + "\n")
    return path


@pytest.fixture
def config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "config"
    project = root / "projects" / "-repo-one"
    _write(project / f"{SESSION}.jsonl")
    _write(project / f"{SIBLING}.jsonl")
    _write(project / SESSION / "subagents" / f"{SUBAGENT}.jsonl")
    workflow = project / SESSION / "subagents" / "workflows" / "wf_abc123"
    _write(workflow / f"{WORKFLOW_SUBAGENT}.jsonl")
    _write(workflow / "journal.jsonl")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(root))
    return root


def _session_log(config_dir: Path) -> str:
    return str(config_dir / "projects" / "-repo-one" / f"{SESSION}.jsonl")


# ─── path arguments ──────────────────────────────────────────────────────────


def test_absolute_path_resolves_to_itself(config_dir: Path, tmp_path: Path) -> None:
    loose = _write(tmp_path / "loose.jsonl")
    assert resolve_log_arg(str(loose)) == Located(path=str(loose), source_id=None)


def test_relative_path_resolves_to_an_absolute_path(
    config_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(tmp_path / "loose.jsonl")
    monkeypatch.chdir(tmp_path)
    located = resolve_log_arg("loose.jsonl")
    assert located == Located(path=str(tmp_path.resolve() / "loose.jsonl"), source_id=None)


def test_tilde_path_is_expanded(
    config_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    _write(home / "loose.jsonl")
    monkeypatch.setenv("HOME", str(home))
    assert resolve_log_arg("~/loose.jsonl").path == str(home / "loose.jsonl")


def test_an_existing_file_named_like_an_id_wins_over_the_id(
    config_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoy = _write(tmp_path / "fdca30e5")
    monkeypatch.chdir(tmp_path)
    assert resolve_log_arg("fdca30e5") == Located(path=str(decoy), source_id=None)


def test_a_directory_is_not_taken_as_a_path(
    config_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "fdca30e5").mkdir()
    monkeypatch.chdir(tmp_path)
    assert resolve_log_arg("fdca30e5").path == _session_log(config_dir)


# ─── id arguments ────────────────────────────────────────────────────────────


def test_a_full_session_id_resolves(config_dir: Path) -> None:
    assert resolve_log_arg(SESSION) == Located(
        path=_session_log(config_dir), source_id=SESSION,
    )


def test_a_session_id_prefix_resolves(config_dir: Path) -> None:
    assert resolve_log_arg("fdca30e5") == Located(
        path=_session_log(config_dir), source_id="fdca30e5",
    )


def test_a_subagent_id_resolves_with_its_agent_prefix(config_dir: Path) -> None:
    assert resolve_log_arg(SUBAGENT).path == str(
        config_dir / "projects" / "-repo-one" / SESSION / "subagents" / f"{SUBAGENT}.jsonl"
    )


def test_a_subagent_id_resolves_without_its_agent_prefix(config_dir: Path) -> None:
    bare = SUBAGENT[len("agent-"):]
    assert resolve_log_arg(bare).path == str(
        config_dir / "projects" / "-repo-one" / SESSION / "subagents" / f"{SUBAGENT}.jsonl"
    )


def test_a_workflow_nested_subagent_resolves(config_dir: Path) -> None:
    assert resolve_log_arg(WORKFLOW_SUBAGENT).path == str(
        config_dir / "projects" / "-repo-one" / SESSION / "subagents"
        / "workflows" / "wf_abc123" / f"{WORKFLOW_SUBAGENT}.jsonl"
    )


def test_a_workflow_journal_is_not_addressable_by_id(config_dir: Path) -> None:
    with pytest.raises(SessionNotFound):
        resolve_log_arg("journal")


def test_the_config_dir_argument_overrides_the_environment(
    config_dir: Path, tmp_path: Path,
) -> None:
    other = tmp_path / "elsewhere"
    _write(other / "projects" / "-repo-two" / f"{SESSION}.jsonl")
    assert resolve_log_arg(SESSION, config_dir=str(other)).path == str(
        other / "projects" / "-repo-two" / f"{SESSION}.jsonl"
    )


# ─── ambiguity and absence ───────────────────────────────────────────────────


def test_an_ambiguous_prefix_names_every_candidate(config_dir: Path) -> None:
    with pytest.raises(SessionNotFound) as excinfo:
        resolve_log_arg("fdca")
    message = str(excinfo.value)
    assert _session_log(config_dir) in message
    assert f"{SIBLING}.jsonl" in message


def test_an_unknown_id_names_the_directory_searched(config_dir: Path) -> None:
    with pytest.raises(SessionNotFound) as excinfo:
        resolve_log_arg("zzzzzzzz")
    message = str(excinfo.value)
    assert "zzzzzzzz" in message
    assert str(config_dir) in message


# ─── the command line ────────────────────────────────────────────────────────


def test_cli_renders_a_session_given_its_id(
    config_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["cc-pretty", "fdca30e5"])
    main()
    assert "hello fixture" in capsys.readouterr().out


def test_cli_prints_the_resolved_path_when_given_an_id(
    config_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["cc-pretty", "fdca30e5"])
    main()
    assert f"# source: fdca30e5 → {_session_log(config_dir)}" in capsys.readouterr().out


def test_cli_prints_the_resolved_path_in_skeleton_mode(
    config_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["cc-pretty", "fdca30e5", "--skeleton"])
    main()
    assert f"# source: fdca30e5 → {_session_log(config_dir)}" in capsys.readouterr().out


def test_cli_omits_the_source_line_when_given_a_path(
    config_dir: Path, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    loose = _write(tmp_path / "loose.jsonl")
    monkeypatch.setattr(sys, "argv", ["cc-pretty", str(loose)])
    main()
    assert "# source:" not in capsys.readouterr().out


def test_cli_recovery_recipe_names_the_resolved_file(
    config_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["cc-pretty", "fdca30e5"])
    main()
    recipe = f"# recover: sed -n '<n>p' {_session_log(config_dir)}"
    assert recipe in capsys.readouterr().out


def test_cli_recovery_recipe_is_absolute_for_a_relative_argument(
    config_dir: Path, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    _write(tmp_path / "loose.jsonl")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["cc-pretty", "loose.jsonl"])
    main()
    recipe = f"# recover: sed -n '<n>p' {tmp_path.resolve() / 'loose.jsonl'}"
    assert recipe in capsys.readouterr().out


def test_cli_validate_only_accepts_an_id(
    config_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["cc-pretty", "fdca30e5", "--validate-only"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0
    assert "1/1 records parsed OK" in capsys.readouterr().err


def test_cli_exits_two_and_explains_when_an_id_does_not_resolve(
    config_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["cc-pretty", "zzzzzzzz"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 2
    assert "zzzzzzzz" in capsys.readouterr().err

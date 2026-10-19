"""Pin the captured request chain, session verification and full token reconciliation."""

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs/system-prompt-snapshot"
CAPTURE = SNAPSHOT / "codex-gpt-6.1-sol/exec-say-hello"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SNAPSHOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sanitization_preserves_prompt_and_linkage():
    sanitize = load("capture_codex").sanitize
    value = {"id": "msg_keep", "creator_account_id": "secret", "safety_identifier": "secret",
             "x-codex-turn-metadata": '{"installation_id":"secret","thread_id":"keep"}',
             "content": [{"text": '{ "installation_id": "literal prompt" }'}]}
    result = sanitize(value)
    assert result["content"] == value["content"]
    assert result["id"] == "msg_keep"
    assert result["creator_account_id"] == result["safety_identifier"] == "[redacted]"
    assert json.loads(result["x-codex-turn-metadata"]) == {"installation_id": "[redacted]", "thread_id": "keep"}


def test_capture_reconciles_and_rendering_is_current(tmp_path):
    pytest.importorskip("tiktoken")
    for pattern in ("*.json", "*.jsonl"):
        for path in CAPTURE.glob(pattern):
            shutil.copy(path, tmp_path / path.name)
    summary = load("render_codex").render(tmp_path)
    assert summary["unattributed_input_tokens"] == 0
    assert summary["attributed_input_total"] == 17348
    assert summary["session_verification"]["all_conversation_items"]
    assert {p.name for p in (tmp_path / "tools").glob("*.md")} == {p.name for p in (CAPTURE / "tools").glob("*.md")}
    for path in [tmp_path / "prompt.md", tmp_path / "summary.json", *sorted((tmp_path / "tools").glob("*.md"))]:
        assert path.read_bytes() == (CAPTURE / path.relative_to(tmp_path)).read_bytes()
    request = tmp_path / "003-request.json"
    data = json.loads(request.read_text())
    data["previous_response_id"] = "broken"
    request.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="linkage"):
        load("render_codex").render(tmp_path)


def test_capture_relays_http_chunks_and_records_only_terminal_events(tmp_path, monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setenv("CODEX_CAPTURE_DIR", str(tmp_path))
    capture = load("capture_codex").Capture()
    response = SimpleNamespace(status_code=200, raw_content=b"")
    response.get_text = lambda strict=False: response.raw_content.decode()
    flow = SimpleNamespace(id="test", request=SimpleNamespace(host="chatgpt.com", path="/backend-api/codex/responses"), response=response)
    capture.responseheaders(flow)
    chunks = [b'data: {"type":"response.created"}\n\n',
              b'data: {"type":"response.completed","response":{"usage":{"input_tokens":1}}}\n\n']
    for chunk in chunks:
        assert response.stream(chunk) == chunk
    assert not list(tmp_path.iterdir())
    capture.response(flow)
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert json.loads(files[0].read_text())["type"] == "response.completed"
    assert not capture.buffers

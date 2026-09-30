"""cc-replay turns a capture into an editable request and sends it back.

The extract/send pair exists so a what-if is a file you edit rather than a flag
you remember, and so a replay's result renders under the same front-end as the
capture it came from.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from claude_config.cc_replay.extract import extract
from claude_config.cc_replay.proxy_module import load_proxy

HTTP = {
    "method": "POST",
    "url": "https://api.anthropic.com/v1/messages?beta=true",
    "http_version": "HTTP/1.1",
    "request_headers": [
        ["Accept", "application/json"],
        ["anthropic-beta", "claude-code-20250219,effort-2025-11-24"],
        ["Content-Length", "4145"],
        ["Host", "api.anthropic.com"],
        ["x-client-request-id", "7fa860c6-4611-456e-b4ed-415f87619442"],
        ["X-Stainless-Retry-Count", "2"],
        ["X-Claude-Code-Session-Id", "ea529de9-61c3-422b-8868-b008a66ded9d"],
    ],
    "credential": {"header": "Authorization", "scheme": "Bearer", "length": 115},
    "response": {
        "status": 200, "reason": "OK",
        "headers": [["request-id", "req_011CfYdgBnuh"]],
    },
}


def capture(**over) -> dict:
    base = {
        "timestamp": "2026-09-29T23:54:47+00:00",
        "duration_ms": 2100,
        "session": {"session_id": "ea529de9-61c3-422b-8868-b008a66ded9d"},
        "streaming": True,
        "request": {
            "model": "claude-opus-5",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
        },
        "response": {"model": "claude-opus-5", "usage": {"input_tokens": 9, "output_tokens": 3}},
        "http": HTTP,
    }
    base.update(over)
    return base


def write_capture(tmp_path: Path, cap: dict) -> Path:
    path = tmp_path / "0007.json"
    path.write_text(json.dumps(cap))
    return path


def test_the_addon_loader_finds_parse_sse_stream() -> None:
    """The dependency runs package -> addon; proxy.py imports nothing."""
    assert callable(load_proxy().parse_sse_stream)


def test_extract_writes_the_body_the_call_and_what_it_answered(tmp_path) -> None:
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)

    body = json.loads((out / "request.json").read_text())
    http = json.loads((out / "http.json").read_text())
    meta = json.loads((out / "meta.json").read_text())

    assert body["model"] == "claude-opus-5"
    assert http["headers_source"] == "captured"
    assert http["url"].endswith("?beta=true")
    assert ["anthropic-beta", "claude-code-20250219,effort-2025-11-24"] in http["request_headers"]
    # The original response's own headers belong to the original, not to what
    # is about to be sent.
    assert "response" not in http
    assert meta["request_id"] == "req_011CfYdgBnuh"
    assert meta["status"] == 200
    assert meta["usage"] == {"input_tokens": 9, "output_tokens": 3}
    assert meta["source"].endswith("0007.json")


def test_extract_refuses_to_overwrite_a_directory_with_work_in_it(tmp_path) -> None:
    out = tmp_path / "w1"
    out.mkdir()
    (out / "request.json").write_text("{}")

    with pytest.raises(FileExistsError):
        extract(write_capture(tmp_path, capture()), out)

    extract(write_capture(tmp_path, capture()), out, force=True)
    assert json.loads((out / "request.json").read_text())["model"] == "claude-opus-5"


def test_a_capture_with_no_http_region_is_marked_synthesized(tmp_path) -> None:
    """The betas are unrecoverable; saying so is the whole point of the mark."""
    cap = capture()
    del cap["http"]
    out = tmp_path / "old"
    extract(write_capture(tmp_path, cap), out)

    http = json.loads((out / "http.json").read_text())
    assert http["headers_source"] == "synthesized"
    assert http["url"] == "https://api.anthropic.com/v1/messages?beta=true"
    assert not any(name.lower() == "anthropic-beta" for name, _ in http["request_headers"])


@pytest.mark.parametrize(
    ("model", "host"),
    [("k3", "api.kimi.ai"), ("glm-5.3", "api.z.ai"), ("claude-opus-5", "api.anthropic.com")],
)
def test_a_synthesized_url_picks_its_host_off_the_model_id(tmp_path, model, host) -> None:
    cap = capture()
    del cap["http"]
    cap["request"]["model"] = model
    out = tmp_path / model
    extract(write_capture(tmp_path, cap), out)

    assert json.loads((out / "http.json").read_text())["url"] == f"https://{host}/v1/messages?beta=true"

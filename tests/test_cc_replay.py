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


# ── Credentials ─────────────────────────────────────────────────────────────
#
# A capture never carries one. Every resolution names its source, because an
# API key and an OAuth bearer are not the same caller: whether a beta such as
# claude-code-20250219 is gated to the OAuth path is unverified, so a replay
# that diverges from its capture must be able to rule the credential in or out.

import time as _time

from claude_config.cc_replay import credentials as creds


def _store(tmp_path, token="oauth-token-value", expires_in=3600.0):
    path = tmp_path / ".credentials.json"
    path.write_text(json.dumps({
        "claudeAiOauth": {
            "accessToken": token,
            "expiresAt": int((_time.time() + expires_in) * 1000),
        }
    }))
    return path


def test_the_first_party_host_resolves_the_oauth_store_first(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(creds, "OAUTH_STORE", _store(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "an-api-key")

    cred = creds.resolve("https://api.anthropic.com/v1/messages?beta=true")
    assert cred is not None
    assert cred.header == "Authorization"
    assert cred.value == "Bearer oauth-token-value"
    assert "claudeAiOauth" in cred.source


def test_an_api_key_fills_in_when_the_store_has_no_token(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(creds, "OAUTH_STORE", tmp_path / "absent.json")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "an-api-key")

    cred = creds.resolve("https://api.anthropic.com/v1/messages")
    assert cred is not None
    assert (cred.header, cred.value) == ("x-api-key", "an-api-key")
    assert cred.source == "$ANTHROPIC_API_KEY"


def test_an_expired_oauth_token_is_refused_by_name(tmp_path, monkeypatch) -> None:
    """A 401 from a stale token reads as an API fault; this does not."""
    monkeypatch.setattr(creds, "OAUTH_STORE", _store(tmp_path, expires_in=-60.0))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="expired"):
        creds.resolve("https://api.anthropic.com/v1/messages")


@pytest.mark.parametrize(
    ("host", "var"),
    [("api.kimi.ai", "KIMI_API_KEY"), ("api.z.ai", "ZAI_API_KEY")],
)
def test_each_provider_host_reads_its_own_key(monkeypatch, host, var) -> None:
    monkeypatch.setenv(var, "provider-key")
    cred = creds.resolve(f"https://{host}/v1/messages")
    assert cred is not None
    assert (cred.header, cred.value, cred.source) == ("Authorization", "Bearer provider-key", f"${var}")


def test_an_unknown_host_is_refused_rather_than_sent_uncredentialed() -> None:
    with pytest.raises(RuntimeError, match="127.0.0.1"):
        creds.resolve("http://127.0.0.1:8080/v1/messages")


def test_no_credential_and_an_explicit_env_var_both_override_the_table(monkeypatch) -> None:
    assert creds.resolve("http://127.0.0.1:8080/v1/messages", none=True) is None

    monkeypatch.setenv("MY_TOKEN", "t")
    cred = creds.resolve("http://127.0.0.1:8080/v1/messages", env_var="MY_TOKEN")
    assert cred is not None
    assert cred.value == "Bearer t"

    monkeypatch.delenv("MY_TOKEN")
    with pytest.raises(RuntimeError, match="MY_TOKEN"):
        creds.resolve("http://127.0.0.1:8080/v1/messages", env_var="MY_TOKEN")


def test_every_source_coming_up_empty_names_what_was_tried(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(creds, "OAUTH_STORE", tmp_path / "absent.json")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match=r"ANTHROPIC_API_KEY"):
        creds.resolve("https://api.anthropic.com/v1/messages")

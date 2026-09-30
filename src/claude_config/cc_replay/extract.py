"""Write a capture out as an editable request directory.

Three files, because the artifact between extract and send is meant to be
edited by hand: `request.json` is the body, `http.json` the call around it,
`meta.json` what the original call answered. Nothing written here is a secret.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# A capture written before proxy.py recorded the call supplies neither host nor
# path. Both are guessed from the model id, and `headers_source` says so rather
# than letting the guess pass for recorded fact.
MODEL_HOSTS = (("k3", "api.kimi.ai"), ("glm", "api.z.ai"))
DEFAULT_HOST = "api.anthropic.com"
DEFAULT_PATH = "/v1/messages?beta=true"


def synthesized_http(body: dict[str, Any]) -> dict[str, Any]:
    """The least that could have been sent, for a capture that did not record it."""
    model = str(body.get("model", ""))
    host = next(
        (h for prefix, h in MODEL_HOSTS if model.startswith(prefix)), DEFAULT_HOST
    )
    return {
        "method": "POST",
        "url": f"https://{host}{DEFAULT_PATH}",
        "http_version": "HTTP/1.1",
        "request_headers": [
            ["Accept", "application/json"],
            ["Content-Type", "application/json"],
            ["anthropic-version", "2023-06-01"],
        ],
        "headers_source": "synthesized",
    }


def _request_id(http: dict[str, Any]) -> str:
    headers = (http.get("response") or {}).get("headers") or []
    return next((v for k, v in headers if k.lower() == "request-id"), "")


def extract(capture_path: Path, out_dir: Path, *, force: bool = False) -> dict[str, Any]:
    """Write the three files and return the `http.json` that was written."""
    capture = json.loads(Path(capture_path).read_text())
    body = capture.get("request")
    if not isinstance(body, dict):
        raise ValueError(f"{capture_path}: no request body to replay")

    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()) and not force:
        raise FileExistsError(
            f"{out_dir} is not empty; pass --force to overwrite what is there"
        )
    out_dir.mkdir(parents=True, exist_ok=True)

    captured = capture.get("http")
    if isinstance(captured, dict):
        # The original response's headers describe the original call, not the
        # one about to be sent.
        http = {k: v for k, v in captured.items() if k != "response"}
        http["headers_source"] = "captured"
    else:
        captured = {}
        http = synthesized_http(body)

    meta = {
        "source": str(Path(capture_path).resolve()),
        "session": capture.get("session") or {},
        "timestamp": capture.get("timestamp", ""),
        "duration_ms": capture.get("duration_ms", 0),
        "status": (captured.get("response") or {}).get("status")
        or (capture.get("error") or {}).get("status")
        or 0,
        "request_id": _request_id(captured),
        "usage": (capture.get("response") or {}).get("usage") or {},
    }

    (out_dir / "request.json").write_text(json.dumps(body, indent=2) + "\n")
    (out_dir / "http.json").write_text(json.dumps(http, indent=2) + "\n")
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return http

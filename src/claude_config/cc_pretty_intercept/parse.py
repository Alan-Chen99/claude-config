"""Pydantic schema for MITM intercept logs at ~/.claude/requests-log/<session>/NNNN.json.

Format documented in scripts/intercept/README.md. One file = one captured API
request/response pair. Distinct from cc_pretty's JSONL session-record format.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from claude_config.cc_pretty.parse import Usage


class _Base(BaseModel):
    model_config = {"extra": "allow", "populate_by_name": True}


class Session(_Base):
    session_id: str = ""
    cwd: str = ""
    kind: str = ""
    entrypoint: str = ""
    pid: int = 0


class CacheControl(_Base):
    type: str = ""
    ttl: str | None = None
    scope: str | None = None


class SystemTextItem(_Base):
    type: str = "text"
    text: str = ""
    cache_control: CacheControl | None = None


class Message(_Base):
    role: str = ""
    # Either a string (single user prompt) or a list of content blocks.
    content: str | list[dict[str, Any]] = ""


class ResponseError(_Base):
    type: str = ""
    message: str = ""


class Request(_Base):
    model: str = ""
    messages: list[Message] = []
    # API accepts string OR list of typed parts; intercept logs use the list form.
    system: str | list[SystemTextItem] = []
    tools: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}
    max_tokens: int | None = None
    temperature: float | None = None
    stream: bool = False
    thinking: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    context_management: dict[str, Any] | None = None


class Response(_Base):
    id: str = ""
    model: str = ""
    role: str = "assistant"
    content: list[dict[str, Any]] = []
    stop_reason: str | None = None
    error: ResponseError | None = None
    usage: Usage | None = None


class InterceptLog(_Base):
    timestamp: str = ""
    duration_ms: int = 0
    session: Session | None = None
    streaming: bool = False
    request: Request
    response: Response


def load_intercept(path: str) -> InterceptLog:
    """Load one intercept log file. Hard-errors if schema doesn't match.

    The unknown-* directories under requests-log/ contain OTEL span exports
    (keys: attributes, spanContext, events, ...) — not intercept logs. They
    fail the request/response presence check below with a clear message.
    """
    with open(path) as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected JSON object at top level, got {type(raw).__name__}")

    missing = [k for k in ("request", "response") if k not in raw]
    if missing:
        present = ", ".join(sorted(raw.keys())) or "(none)"
        raise ValueError(
            f"{path}: not an intercept log (missing {missing}). "
            f"Top-level keys present: {present}. "
            f"The unknown-* directories contain OTEL spans, not intercept logs."
        )

    return InterceptLog.model_validate(raw)

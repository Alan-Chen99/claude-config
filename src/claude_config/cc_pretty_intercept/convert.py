"""Flatten one MITM intercept capture into cc-pretty records.

A capture holds one API request/response pair, and its content sits in named
top-level regions rather than one record per line: ``.request.system``,
``.request.tools``, ``.request.messages`` and ``.response``. Conversion walks
those regions in reading order, numbers the records it emits from 1, and
returns the jq address of each so the ``@L<n>`` refs the renderer prints stay
recoverable — a line number alone locates nothing in a capture.

The system prompt, the tool list and a failed call's own account of itself
become ``SystemRecord``s under ``api_`` subtypes. They are model-visible
(``cc_pretty.main.is_model_visible``): unlike cc's bookkeeping system records
they are the content the call was made of.
"""

from __future__ import annotations

import os

from claude_config.cc_pretty.parse import (
    AssistantRecord,
    Message,
    Record,
    SystemRecord,
    UserRecord,
)
from claude_config.cc_pretty.render import fmt_duration, fmt_ts
from claude_config.cc_pretty_intercept.parse import (
    InterceptLog,
    SystemTextItem,
    TransportError,
)


def _system_items(system: str | list[SystemTextItem]) -> list[SystemTextItem]:
    """The system prompt as parts, whichever of the API's two shapes it took."""
    if isinstance(system, str):
        return [SystemTextItem(text=system)] if system else []
    return list(system)


def _cache_tag(item: SystemTextItem) -> str:
    cc = item.cache_control
    if not cc:
        return ""
    tag = cc.type or "ephemeral"
    if cc.ttl:
        tag += f"/{cc.ttl}"
    if cc.scope:
        tag += f"/{cc.scope}"
    return f"cache:{tag}"


def _transport_detail(err: TransportError | None) -> tuple[str, str]:
    """A transport failure's headline and body."""
    if err is None:
        return "no response and no error recorded", ""
    detail = f"HTTP {err.status} {err.statusText}".strip()
    if err.type or err.message:
        said = f"[{err.type}] {err.message}".strip() if err.type else err.message
    else:
        said = err.body
    return detail, said


def log_to_records(
    log: InterceptLog, *, show_system: bool = True, show_tools: bool = True,
) -> tuple[list[tuple[Record, int]], dict[int, str]]:
    """Convert one capture to ``(records, jq_paths)`` for ``run_pipeline``.

    ``jq_paths`` maps each record's lineno to the jq expression addressing that
    record in the capture file.

    ``show_system`` / ``show_tools`` drop those regions here rather than at
    render time, so a hidden region costs no ref numbers and the remaining
    refs stay contiguous.
    """
    records: list[tuple[Record, int]] = []
    jq_paths: dict[int, str] = {}

    def add(rec: Record, jq: str) -> None:
        lineno = len(records) + 1
        jq_paths[lineno] = jq
        records.append((rec, lineno))

    items = _system_items(log.request.system)
    if show_system:
        for k, item in enumerate(items):
            detail = f"{k + 1}/{len(items)}"
            tag = _cache_tag(item)
            if tag:
                detail += f"  {tag}"
            add(
                SystemRecord(
                    type="system", subtype="api_system",
                    content=item.text, detail=detail, content_leaf=".text",
                ),
                f".request.system[{k}]",
            )

    if show_tools and log.request.tools:
        names = ", ".join(t.get("name", "?") for t in log.request.tools)
        add(
            SystemRecord(
                type="system", subtype="api_tools",
                content=names, detail=str(len(log.request.tools)),
                # The row's body is the name list, but what a reader wants back
                # is the schemas, and those are the region itself.
                content_leaf="",
            ),
            ".request.tools",
        )

    for k, msg in enumerate(log.request.messages):
        jq = f".request.messages[{k}]"
        body = Message(role=msg.role, content=msg.content)
        if msg.role == "assistant":
            add(AssistantRecord(type="assistant", message=body), jq)
        else:
            add(UserRecord(type="user", message=body), jq)

    if log.response is not None:
        resp = log.response
        if resp.error:
            add(
                SystemRecord(
                    type="system", subtype="api_error",
                    content=f"[{resp.error.type}] {resp.error.message}".strip(),
                    detail=resp.error.type or "error", content_leaf="",
                ),
                ".response.error",
            )
        if resp.stop_details:
            d = resp.stop_details
            add(
                SystemRecord(
                    type="system", subtype="api_refusal",
                    content=str(d.get("explanation", "")),
                    detail=f"{d.get('type', 'refusal')}: {d.get('category')}",
                    content_leaf=".stop_details.explanation",
                ),
                ".response",
            )
        add(
            AssistantRecord(
                type="assistant",
                message=Message(
                    id=resp.id, role="assistant", model=resp.model,
                    content=resp.content, stop_reason=resp.stop_reason,
                    usage=resp.usage,
                ),
            ),
            ".response",
        )
    else:
        detail, said = _transport_detail(log.error)
        add(
            SystemRecord(
                type="system", subtype="api_transport_error",
                content=said or "the request above never produced a response",
                detail=detail, content_leaf="",
            ),
            ".error",
        )

    return records, jq_paths


def header_lines(
    log: InterceptLog, path: str, *, show_http: bool = False
) -> list[str]:
    """The capture's front-matter: what the call was, not what it said.

    Plain strings — ``run_pipeline`` prints them above the legend, and the
    caller colors them.

    The ``http`` region's call line and beta list are always shown. The beta
    list decides what the API did with the body and varies per request inside
    one session, so nobody would think to go looking for it until it had already
    misled them. ``show_http`` adds every header.
    """
    parts = [f"intercept: {os.path.basename(path)}"]
    if log.request.model:
        parts.append(log.request.model)
    parts.append("streaming" if log.streaming else "non-stream")
    if log.timestamp:
        parts.append(fmt_ts(log.timestamp))
    if log.duration_ms:
        parts.append(f"dur:{fmt_duration(log.duration_ms)}")
    lines = [parts]

    sess: list[str] = []
    if log.session:
        if log.session.session_id:
            sess.append(f"id:{log.session.session_id[:8]}")
        if log.session.cwd:
            sess.append(f"cwd:{log.session.cwd}")
        for field in (log.session.kind, log.session.entrypoint):
            if field:
                sess.append(field)
        if log.session.pid:
            sess.append(f"pid:{log.session.pid}")
    if sess:
        lines.append(sess)

    req: list[str] = []
    if log.request.max_tokens is not None:
        req.append(f"max_tokens:{log.request.max_tokens}")
    if log.request.temperature is not None:
        req.append(f"temp:{log.request.temperature}")
    if log.request.thinking:
        budget = log.request.thinking.get("budget_tokens")
        req.append(
            f"thinking:{budget}" if budget
            else f"thinking:{log.request.thinking.get('type', '?')}"
        )
    if log.request.output_config:
        req.append("output_config")
    if req:
        lines.append(req)

    if log.http:
        call: list[str] = []
        if log.http.method and log.http.url:
            call.append(f"{log.http.method} {log.http.url}")
        if log.http.response and log.http.response.status:
            call.append(f"-> {log.http.response.status}")
        rid = log.http.response_header("request-id")
        if rid:
            call.append(rid)
        if call:
            lines.append(call)

        betas = log.http.header("anthropic-beta")
        if betas:
            lines.append([f"betas: {betas}"])

        if show_http:
            for label, pairs in (
                ("req ", log.http.request_headers),
                ("resp", log.http.response.headers if log.http.response else []),
            ):
                for name, value in pairs:
                    lines.append([f"{label} {name}: {value}"])
            cred = log.http.credential
            if cred:
                lines.append([
                    f"req  {cred.header}: {cred.scheme} "
                    f"<{cred.length} chars, not captured>"
                ])

    return ["  ".join(group) for group in lines]


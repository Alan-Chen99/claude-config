"""Convert an opencode export dict into cc-pretty pydantic records.

opencode and Claude Code use different on-disk shapes:

  - Claude Code writes one JSONL line per "record" (user, assistant, tool
    result, system, attachment, ...). Tool calls and results are separate
    records that the renderer pairs by ``tool_use_id``.
  - opencode stores one message per turn, with a ``parts`` list that mixes
    reasoning / text / tool-call+result / step markers / compaction markers
    on the same row.

The shared rendering layer (cc-pretty's ``run_pipeline``) expects Claude Code
records. This module flattens an opencode export into the same shape:

  - reasoning  → thinking block on the AssistantRecord
  - text       → text block on the AssistantRecord
  - tool       → tool_use block on the AssistantRecord, AND a synthetic
                 follow-up UserRecord with the matching tool_result block(s)
                 so cc-pretty pairs them up
  - compaction → SystemRecord(subtype="compact_boundary") so cc-pretty's
                 existing compaction-leg filter detects it via "Method 2"
                 (modern format with ``compactMetadata.preTokens``)
  - step-start / step-finish / snapshot / patch / file / etc.: dropped

Rewinds are handled separately. opencode's revert mechanism deletes the
abandoned tail from storage on the next prompt, so a typical export has no
trace of past rewinds. The one case that does survive is an export taken
while the session is still in revert state (no follow-up prompt yet): the
``session.info.revert`` field carries the cut-off ``messageID``. We compute
the rewound record indices here and hand them to the pipeline as
``extra_rewound`` — cc-pretty's parent-fork detector wouldn't find them on
its own because opencode messages never share a parent.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from claude_config.cc_pretty.parse import Record, parse_record


def export_to_records(
    export: dict[str, Any],
) -> tuple[list[tuple[Record, int]], dict[str, Any]]:
    """Convert an opencode export dict to cc-pretty records + metadata.

    Returns ``(records, meta)`` where:

    - ``records``: ``list[(Record, lineno)]`` ready to feed to
      ``cc_pretty.main.run_pipeline``. ``lineno`` is the 1-based message
      index in ``export["messages"]`` so the ``@L<n>`` refs the renderer
      prints point back at the source message (recoverable via
      ``opencode export <id> | jq '.messages[n-1]'``).
    - ``meta``: dict with ``session_id``, ``title``, ``directory``, ``slug``,
      ``version``, ``model``, ``created``, ``updated``, plus
      ``rewound_indices: set[int]`` (record indices that fall after an
      uncleaned revert boundary — empty when no revert state is present).
    """
    info = export.get("info") if isinstance(export.get("info"), dict) else {}
    session_id = str(info.get("id") or export.get("id") or "")
    messages = _messages(export)

    records: list[tuple[Record, int]] = []
    # message.id → list of record indices spawned by that message. Used for
    # mapping the revert.messageID cut-off to concrete record indices.
    msg_id_to_idx: dict[str, list[int]] = {}

    prev_assistant_input_tokens = 0  # for compactMetadata.preTokens

    # Carry the session-level metadata as record fields on every synthesized
    # record so the cc-pretty session-header renderer can pick up version /
    # slug / cwd off whichever record happens to be first-visible after
    # filter passes (compaction leg, rewinds).
    common_meta = {
        "version": str(info.get("version") or ""),
        "slug": str(info.get("slug") or ""),
        "cwd": str(info.get("directory") or ""),
        "gitBranch": "",
    }

    for mi, msg in enumerate(messages, start=1):
        m_info = _info(msg)
        parts = _parts(msg)
        role = str(m_info.get("role") or "")
        m_id = str(m_info.get("id") or "")
        parent_id = m_info.get("parentID") or None
        ts = _to_iso(_get_time(m_info, "created"))

        if role == "user":
            compaction_part = _find_part(parts, "compaction")
            if compaction_part is not None:
                rec = _make_compact_boundary_record(
                    session_id=session_id,
                    msg_id=m_id,
                    parent_id=None,
                    ts=ts,
                    compaction_part=compaction_part,
                    pre_tokens=prev_assistant_input_tokens,
                )
                _push(records, msg_id_to_idx, m_id, rec, mi)
                continue

            user_text, user_pi = _collect_user_text(parts)
            rec = _make_user_record(
                session_id=session_id,
                msg_id=m_id,
                parent_id=parent_id,
                ts=ts,
                content=user_text,
                part_idx=user_pi,
                extra=common_meta,
            )
            _push(records, msg_id_to_idx, m_id, rec, mi)
            continue

        if role == "assistant":
            content_blocks, tool_results = _build_assistant_blocks(parts)
            tokens = m_info.get("tokens") or {}
            cache = tokens.get("cache") if isinstance(tokens.get("cache"), dict) else {}
            model_info = m_info.get("model") if isinstance(m_info.get("model"), dict) else {}
            model = _format_model(
                provider=m_info.get("providerID") or model_info.get("providerID"),
                model_id=m_info.get("modelID") or model_info.get("modelID") or model_info.get("id"),
                variant=m_info.get("variant") or model_info.get("variant"),
            )

            rec = _make_assistant_record(
                session_id=session_id,
                msg_id=m_id,
                parent_id=parent_id,
                ts=ts,
                model=model,
                content_blocks=content_blocks,
                input_tokens=int(tokens.get("input", 0) or 0),
                output_tokens=int(tokens.get("output", 0) or 0),
                cache_read=int(cache.get("read", 0) or 0),
                cache_write=int(cache.get("write", 0) or 0),
                extra=common_meta,
            )
            _push(records, msg_id_to_idx, m_id, rec, mi)

            # Track the most recent assistant input-token count so the next
            # compact_boundary can report it as preTokens (cc-pretty's
            # compaction marker shows context-before / context-after).
            total_in = (
                int(tokens.get("input", 0) or 0)
                + int(cache.get("read", 0) or 0)
                + int(cache.get("write", 0) or 0)
            )
            if total_in:
                prev_assistant_input_tokens = total_in

            if tool_results:
                tr_rec = _make_tool_result_record(
                    session_id=session_id,
                    parent_msg_id=m_id,
                    ts=ts,
                    tool_results=tool_results,
                    extra=common_meta,
                )
                _push(records, msg_id_to_idx, m_id, tr_rec, mi)
            continue

        # Unknown role: skip silently — opencode only has user/assistant.

    rewound = _compute_rewound_indices(info, msg_id_to_idx)

    model_info = info.get("model") if isinstance(info.get("model"), dict) else {}
    meta = {
        "session_id": session_id,
        "title": str(info.get("title") or ""),
        "directory": str(info.get("directory") or info.get("cwd") or ""),
        "slug": str(info.get("slug") or ""),
        "version": str(info.get("version") or ""),
        "model": _format_model(
            provider=model_info.get("providerID") or info.get("providerID"),
            model_id=model_info.get("id") or info.get("modelID"),
            variant=model_info.get("variant"),
        ),
        "created": _to_iso(_get_time(info, "created")),
        "updated": _to_iso(_get_time(info, "updated")),
        "revert": info.get("revert"),
        "rewound_indices": rewound,
    }
    return records, meta


# ─── Record builders ─────────────────────────────────────────────────────────


def _push(
    records: list[tuple[Record, int]],
    idx_map: dict[str, list[int]],
    msg_id: str,
    rec: Record,
    lineno: int,
) -> None:
    idx = len(records)
    records.append((rec, lineno))
    if msg_id:
        idx_map.setdefault(msg_id, []).append(idx)


def _make_user_record(
    *,
    session_id: str,
    msg_id: str,
    parent_id: str | None,
    ts: str,
    content: str,
    part_idx: int,
    extra: dict[str, Any],
) -> Record:
    return parse_record({
        "type": "user",
        "uuid": msg_id,
        "parentUuid": parent_id,
        "sessionId": session_id,
        "timestamp": ts,
        "_pi": part_idx,
        "message": {
            "role": "user",
            "content": content,
        },
        **extra,
    })


def _make_assistant_record(
    *,
    session_id: str,
    msg_id: str,
    parent_id: str | None,
    ts: str,
    model: str,
    content_blocks: list[dict[str, Any]],
    input_tokens: int,
    output_tokens: int,
    cache_read: int,
    cache_write: int,
    extra: dict[str, Any],
) -> Record:
    return parse_record({
        "type": "assistant",
        "uuid": msg_id,
        "parentUuid": parent_id,
        "sessionId": session_id,
        "timestamp": ts,
        "message": {
            "id": msg_id,
            "role": "assistant",
            "model": model,
            "content": content_blocks,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_write,
            },
        },
        **extra,
    })


def _make_tool_result_record(
    *,
    session_id: str,
    parent_msg_id: str,
    ts: str,
    tool_results: list[dict[str, Any]],
    extra: dict[str, Any],
) -> Record:
    return parse_record({
        "type": "user",
        # Synthetic UUID — pairs with the assistant message via parentUuid so
        # cc-pretty's chain reconstruction stays consistent.
        "uuid": f"{parent_msg_id}.tool-result",
        "parentUuid": parent_msg_id,
        "sessionId": session_id,
        "timestamp": ts,
        "message": {
            "role": "user",
            "content": tool_results,
        },
        **extra,
    })


def _make_compact_boundary_record(
    *,
    session_id: str,
    msg_id: str,
    parent_id: str | None,
    ts: str,
    compaction_part: dict[str, Any],
    pre_tokens: int,
) -> Record:
    """Emit a Claude-Code-style `compact_boundary` system record.

    cc-pretty's compaction detector (Method 2) matches on
    ``subtype == "compact_boundary"`` and pulls ``preTokens`` out of
    ``compactMetadata`` for the "context before → after" annotation.
    """
    return parse_record({
        "type": "system",
        "subtype": "compact_boundary",
        "uuid": msg_id,
        "parentUuid": parent_id,
        "sessionId": session_id,
        "timestamp": ts,
        "compactMetadata": {
            "trigger": "auto" if compaction_part.get("auto") else "manual",
            "preTokens": pre_tokens,
            "overflow": bool(compaction_part.get("overflow")),
            "tail_start_id": compaction_part.get("tail_start_id"),
        },
    })


# ─── Part decoding ───────────────────────────────────────────────────────────


def _build_assistant_blocks(
    parts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (content_blocks, tool_result_blocks) for an assistant message.

    content_blocks are emitted on the AssistantRecord (in part order).
    tool_result_blocks go on a follow-up synthetic UserRecord so cc-pretty's
    renderer pairs each ``◀ result`` with its preceding ``▶ tool_use``.

    Every block carries ``_pi`` — the index of the export part it came from.
    Dropped parts (step-start/step-finish/patch/file/...) would otherwise
    shift the renderer's enumeration index away from the jq path the legend
    promises (``.messages[n-1].parts[i]``). Tool blocks also carry
    ``_out_len`` (output char count) for the skeleton's ``out:`` column.
    """
    content: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for pi, part in enumerate(parts):
        typ = part.get("type")
        if typ == "reasoning":
            text = part.get("text", "")
            if text:
                content.append({"type": "thinking", "thinking": text, "_pi": pi})
        elif typ == "text":
            text = part.get("text", "")
            if text:
                content.append({"type": "text", "text": text, "_pi": pi})
        elif typ == "tool":
            call_id = part.get("callID", "") or part.get("id", "")
            name = part.get("tool", "tool")
            state = part.get("state") if isinstance(part.get("state"), dict) else {}
            status = state.get("status")
            out_len = 0
            if status == "completed":
                out_text = str(state.get("output", ""))
                out_len = len(out_text)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": call_id,
                    "content": out_text,
                    "is_error": False,
                    "_pi": pi,
                })
            elif status == "error":
                out_text = str(state.get("error", ""))
                out_len = len(out_text)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": call_id,
                    "content": out_text,
                    "is_error": True,
                    "_pi": pi,
                })
            content.append({
                "type": "tool_use",
                "id": call_id,
                "name": name,
                "input": state.get("input", {}),
                "_pi": pi,
                "_out_len": out_len,
            })
        # step-start / step-finish / snapshot / patch / agent / subtask /
        # retry / file: not rendered. They're either bookkeeping or carry
        # signal we don't have a slot for in the cc-pretty record types.
    return content, results


def _collect_user_text(parts: list[dict[str, Any]]) -> tuple[str, int]:
    """Flatten user-message parts; return (text, first text part index).

    Multi-part user inputs in opencode are usually a text body plus optional
    file attachments. We render the text and tag each file with a brief
    pointer line; cc-pretty's user-input renderer just emits this verbatim.

    The part index lets the user message's ref point at its first text part
    so the documented jq path (``.messages[n-1].parts[i].text``) resolves to
    the visible text. Multi-text-part messages lose per-part granularity —
    the flattening predates refs; documented limitation.
    """
    chunks: list[str] = []
    first_text_pi = 0
    seen_text = False
    for pi, part in enumerate(parts):
        typ = part.get("type")
        if typ == "text":
            text = part.get("text", "")
            if text:
                if not seen_text:
                    first_text_pi = pi
                    seen_text = True
                chunks.append(text)
        elif typ == "file":
            label = part.get("filename") or part.get("url") or "file"
            mime = part.get("mime") or "?"
            chunks.append(f"[attached {mime}: {label}]")
    return "\n\n".join(chunks), first_text_pi


# ─── Rewind computation ─────────────────────────────────────────────────────


def _compute_rewound_indices(
    info: dict[str, Any],
    msg_id_to_idx: dict[str, list[int]],
) -> set[int]:
    """Translate ``session.info.revert`` into rewound record indices.

    opencode's revert.messageID semantics (from session/revert.ts cleanup):

      - With NO partID, revert.messageID is the last-user-message BEFORE
        the cut, and cleanup removes everything with id >= messageID
        (including that user message itself — the user is overwriting it).
      - With partID, revert.messageID is the target message whose parts get
        trimmed at partID; cleanup removes everything with id > messageID
        but keeps the target with its leading parts.

    Per-part trimming isn't modeled at the record level — we'd have to
    split a single AssistantRecord across multiple records, which isn't
    worth the complexity just to draw a sharper marker boundary.
    """
    revert = info.get("revert")
    if not isinstance(revert, dict):
        return set()
    cutoff = revert.get("messageID")
    if not cutoff:
        return set()
    has_part_id = bool(revert.get("partID"))

    rewound: set[int] = set()
    # opencode message IDs (ULID-based, ``msg_<ascending>``) sort
    # lexicographically in creation order, so a string comparison
    # correctly identifies messages created AFTER the cutoff.
    for msg_id, idxs in msg_id_to_idx.items():
        in_range = msg_id > cutoff if has_part_id else msg_id >= cutoff
        if in_range:
            rewound.update(idxs)
    return rewound


# ─── Small accessors ────────────────────────────────────────────────────────


def _messages(export: dict[str, Any]) -> list[dict[str, Any]]:
    msgs = export.get("messages") or []
    if not isinstance(msgs, list):
        return []
    return [m for m in msgs if isinstance(m, dict)]


def _info(obj: dict[str, Any]) -> dict[str, Any]:
    inner = obj.get("info")
    return inner if isinstance(inner, dict) else obj


def _parts(message: dict[str, Any]) -> list[dict[str, Any]]:
    parts = message.get("parts") or []
    if isinstance(parts, str):
        return [{"type": "text", "text": parts}]
    if not isinstance(parts, list):
        return []
    return [p for p in parts if isinstance(p, dict)]


def _find_part(parts: list[dict[str, Any]], part_type: str) -> dict[str, Any] | None:
    for part in parts:
        if part.get("type") == part_type:
            return part
    return None


def _get_time(obj: dict[str, Any], key: str) -> Any:
    time_obj = obj.get("time") if isinstance(obj, dict) else None
    if isinstance(time_obj, dict) and key in time_obj:
        return time_obj[key]
    return obj.get(key) or obj.get("timestamp")


def _to_iso(value: Any) -> str:
    """Normalize an opencode timestamp to the ISO-8601 form cc-pretty expects."""
    if value in (None, ""):
        return ""
    if isinstance(value, int | float):
        # opencode stores epoch milliseconds for stored events; the
        # > 10^10 check is the same heuristic the existing renderer uses.
        seconds = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(seconds, UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, str):
        return value
    return ""


def _format_model(
    *, provider: Any, model_id: Any, variant: Any,
) -> str:
    parts = [str(provider)] if provider else []
    if model_id:
        parts.append(str(model_id))
    if variant:
        parts.append(str(variant))
    return "/".join(parts)

"""Pins for "the default view shows what the model was sent".

An attachment record is model-visible when Claude Code's normalizeAttachmentForAPI
turned it into request content. These tests pin the three things that answer
that question — the conversion output a 2.1.269 record carries, the subtypes
whose conversion arm yields nothing, and the per-record conditions the
conversion applies — and re-derive the middle one from the binary so the
citations stay true across a Claude Code upgrade.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

import pytest

from claude_config.cc_pretty.main import (
    _HOOK_STDOUT_VISIBLE_EVENTS,
    _NEVER_VISIBLE_ATTACHMENT_TYPES,
    attachment_is_model_visible,
    is_model_visible,
)
from claude_config.cc_pretty.parse import AttachmentData, AttachmentRecord, parse_record


def _rec(atype: str, *, rendered: list[dict] | None = None, **fields) -> AttachmentRecord:
    return AttachmentRecord(
        type="attachment",
        attachment=AttachmentData(type=atype, **fields),
        rendered=rendered or [],
    )


# ── The conversion output the record carries ────────────────────────────────


def test_persisted_conversion_output_decides_on_its_own() -> None:
    """A subtype no version of this code has heard of, with proof it was sent."""
    rec = _rec("subtype_from_a_later_release", rendered=[{"content": "<system-reminder>x"}])
    assert attachment_is_model_visible(rec) is True


def test_missing_conversion_output_is_not_a_verdict() -> None:
    """A `file` becomes tool_use/tool_result blocks, which are never persisted."""
    rec = _rec("file", filename="/tmp/a.txt")
    assert rec.rendered == []
    assert attachment_is_model_visible(rec) is True


def test_persisted_output_parses_off_a_real_log_line() -> None:
    raw = {
        "type": "attachment",
        "uuid": "u1",
        "attachment": {"type": "environment", "snapshot": {"cwd": "/x"}},
        "rendered": [{"content": "<system-reminder>\n# Environment\n</system-reminder>"}],
        "version": "2.1.269",
    }
    rec = parse_record(raw)
    assert isinstance(rec, AttachmentRecord)
    assert rec.rendered[0]["content"].startswith("<system-reminder>")
    assert is_model_visible(rec) is True


# ── Subtypes whose conversion arm yields nothing ────────────────────────────


@pytest.mark.parametrize("atype", [
    "prompt_snapshot",
    "command_permissions",
    "deferred_tools_record",
    "hook_non_blocking_error",
    "hook_system_message",
    "attention_budget",
    "context_efficiency",
    "todo",
    "background_task_status",
])
def test_bookkeeping_subtype_is_hidden(atype: str) -> None:
    assert attachment_is_model_visible(_rec(atype)) is False


def test_unrecognized_subtype_is_shown() -> None:
    """Over-showing costs a dim line; under-showing is invisible to the reader."""
    assert attachment_is_model_visible(_rec("subtype_from_a_later_release")) is True


# ── Conditions the conversion reads off the record ──────────────────────────


@pytest.mark.parametrize("event", sorted(_HOOK_STDOUT_VISIBLE_EVENTS))
def test_hook_stdout_reaches_the_model_for_prompt_stage_events(event: str) -> None:
    assert attachment_is_model_visible(
        _rec("hook_success", hookEvent=event, content="ran the thing")
    ) is True


@pytest.mark.parametrize("event", ["PreToolUse", "PostToolUse", "PostToolUseFailure", "Stop"])
def test_hook_stdout_is_dropped_for_every_other_event(event: str) -> None:
    assert attachment_is_model_visible(
        _rec("hook_success", hookEvent=event, content="ran the thing")
    ) is False


def test_hook_success_without_stdout_is_hidden_even_at_session_start() -> None:
    assert attachment_is_model_visible(
        _rec("hook_success", hookEvent="SessionStart", content="")
    ) is False


def test_queued_command_is_shown_once_the_batch_head_has_not_claimed_it() -> None:
    assert attachment_is_model_visible(_rec("queued_command", prompt="do it")) is True


def test_queued_command_claimed_by_a_batch_head_is_hidden() -> None:
    assert attachment_is_model_visible(
        _rec("queued_command", prompt="do it", renderedByBatchHead=True)
    ) is False


# ── The subtypes 2.1.269 sessions actually carry ────────────────────────────
#
# Counted over every JSONL under ~/.claude/projects, then checked against the
# request bodies captured for those sessions under ~/.claude/requests-log.

@pytest.mark.parametrize("atype", [
    "environment",
    "date",
    "model",
    "session_context",
    "instructions",
    "remote_session_change",
    "output_style_instructions",
    "total_tokens_reminder",
    "agent_listing_delta",
    "auto_mode",
    "invoked_skills",
    "hook_additional_context",
    "skill_listing",
    "deferred_tools_delta",
    "date_change",
    "output_style",
    "nested_memory",
    "edited_text_file",
    "read_truncation_notice",
])
def test_subtype_seen_in_request_bodies_is_visible(atype: str) -> None:
    assert attachment_is_model_visible(_rec(atype)) is True


def test_environment_block_survives_the_default_view(tmp_path) -> None:
    """The # Environment block arrives as a messages[] attachment, not a system
    prompt section, so the default view is where a reader looks for it."""
    jsonl = tmp_path / "session.jsonl"
    jsonl.write_text(json.dumps({
        "type": "attachment",
        "uuid": "u1",
        "attachment": {"type": "environment", "snapshot": {"cwd": "/x"}},
        "rendered": [{"content": "<system-reminder>\n# Environment\n</system-reminder>"}],
        "version": "2.1.269",
    }) + "\n")
    proc = subprocess.run(
        [sys.executable, "-m", "claude_config.cc_pretty.main", str(jsonl)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "environment" in proc.stdout


def test_output_style_instructions_carries_an_object_style(tmp_path) -> None:
    """A record that fails validation is dropped before any view sees it, so a
    field too narrow for one subtype hides that subtype outright."""
    raw = {
        "type": "attachment",
        "uuid": "u1",
        "attachment": {
            "type": "output_style_instructions",
            "style": {"name": "Explanatory", "prompt": "Explain as you go."},
        },
        "version": "2.1.269",
    }
    rec = parse_record(raw)
    assert isinstance(rec, AttachmentRecord)
    assert rec.attachment.style["name"] == "Explanatory"


# ── Re-derivation from the conversion source ────────────────────────────────

_DECOMPILED = pathlib.Path("/repos/claude-code-decompiled/src")
_MARKER = "normalizeAttachmentForAPI"


def _conversion_source() -> str | None:
    """The body of normalizeAttachmentForAPI plus the arm table it dispatches to.

    Chunk file names and minified identifiers both rotate per build, so the
    marker string is the only stable anchor; the table is found by the name the
    dispatch line gives it.
    """
    if not _DECOMPILED.is_dir():
        return None
    for path in sorted(_DECOMPILED.glob("chunk-*.js")):
        text = path.read_text(errors="replace")
        end = text.find(_MARKER)
        if end < 0:
            continue
        dispatch = re.search(
            r"if \((\w+)\.type in (\w+)\) return \2\[\1\.type\]\(\1\);", text[:end]
        )
        if dispatch is None:
            return None
        table = re.findall(
            rf"^\s*(?:var )?{dispatch.group(2)} = \{{$", text[:dispatch.start()], re.M
        )
        if not table:
            return None
        return text[text.rindex(table[-1], 0, dispatch.start()):end]
    return None


@pytest.mark.skipif(not _DECOMPILED.is_dir(), reason="decompiled Claude Code not present")
def test_denylist_still_matches_the_conversion_source() -> None:
    """Fails when a release adds, drops, or fills in an always-empty arm.

    Which is the point: the set below is only as good as the build it was read
    off, and a hand-maintained list that nothing re-checks goes stale silently.
    """
    source = _conversion_source()
    assert source is not None, f"{_MARKER} not found in {_DECOMPILED}"
    derived = set(re.findall(r"^    (\w+): \(\) => \[\],?$", source, re.M))
    derived |= set(re.findall(r'^    case "(\w+)":\n      return \[\];$', source, re.M))
    skipped = re.search(
        r"if \(\[((?:\"\w+\", )+\"\w+\")\]\.includes\(\w+\.type\)\) return \[\];", source
    )
    assert skipped is not None, "the recognized-and-dropped list moved"
    derived |= set(re.findall(r'"(\w+)"', skipped.group(1)))
    assert derived == set(_NEVER_VISIBLE_ATTACHMENT_TYPES)


@pytest.mark.skipif(not _DECOMPILED.is_dir(), reason="decompiled Claude Code not present")
def test_hook_stdout_visible_events_still_match_the_conversion_source() -> None:
    """The sibling set, re-derived rather than asserted against itself.

    `_NEVER_VISIBLE_ATTACHMENT_TYPES` is pinned to the source; this set sat
    beside it hand-maintained, so a release adding a fourth event whose stdout
    reaches the model would have gone unnoticed in every view built on it.

    The arm lives in the same function as the denylist but not in its dispatch
    table -- it is a `case` in the `switch` that follows -- so the shape being
    matched is the event guard, not a table entry.
    """
    source = _conversion_source()
    assert source is not None, f"{_MARKER} not found in {_DECOMPILED}"
    # The template literal the model actually receives; unique tree-wide. A
    # reworded arm fails here rather than silently matching nothing below.
    assert "hook success: " in source, "the hook_success arm moved or was reworded"
    arm = re.search(
        r'case "hook_success":\s*if \(\w+\.hookEvent[^)]*\) return \[\];', source
    )
    assert arm is not None, "the hook_success event guard moved"
    derived = set(re.findall(r'hookEvent !== "(\w+)"', arm.group(0)))
    assert derived == set(_HOOK_STDOUT_VISIBLE_EVENTS)

"""Pydantic schema and parse functions for Claude Code JSONL session logs.

Handles all record types found in Claude Code JSONL logs:
  assistant, user, system, progress, file-history-snapshot,
  file-history-delta, last-prompt, queue-operation, attachment,
  permission-mode

Claude Code writes 46 top-level `type` values; 2.1.289 enumerates them in two
policy tables (`chunk-wgfrtm7w.js:170131` `var nxr`, `:170911` `var rss`). The
ones absent above are per-session latches and pointers — `mode`, `atis-latch`,
`ai-title`, `cost-state`, `frame-link`, `summary`, `api-request*` — carrying no
conversation content. They land on UnknownRecord by design, which the renderer
prints as one dim line under --show-all.

Content block types: thinking, text, tool_use, tool_result, image, document
toolUseResult: arbitrary tool-defined JSON — only the object form is
  modelled; see notes/tool-use-result-shapes.md
Progress data types: bash_progress, agent_progress, hook_progress
Attachment types: an open set — Claude Code adds and retires subtypes every
  release, so AttachmentData models the fields the renderer reads and lets
  pydantic carry the rest. See attachment_is_model_visible in main.py for
  which records reach the model.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field


# ─── Base ────────────────────────────────────────────────────────────────────
# Permissive: extra fields allowed everywhere, optional fields default to None.

class _Base(BaseModel):
    model_config = {"extra": "allow", "populate_by_name": True}


# ─── Content blocks (inside message.content lists) ──────────────────────────

class ThinkingBlock(_Base):
    type: Literal["thinking"]
    thinking: str = ""
    signature: str | None = None

class TextBlock(_Base):
    type: Literal["text"]
    text: str = ""

class ToolUseBlock(_Base):
    type: Literal["tool_use"]
    id: str = ""
    name: str = "?"
    input: Any = {}
    caller: dict[str, Any] | None = None

class ToolResultBlock(_Base):
    type: Literal["tool_result"]
    tool_use_id: str = ""
    content: str | list[dict[str, Any]] = ""
    is_error: bool = False

class BinaryBlock(_Base):
    """An `image` or `document` block — a payload no reader wants inline.

    `source` is either the payload itself (`{type: base64, media_type, data}`)
    or a reference to one (`{type: url, url}`, `{type: file, file_id}`). A
    base64 screenshot runs 43k chars, so this type exists to keep image and
    document blocks off the `UnknownBlock` path, whose contract is to dump
    whatever it carries.
    """
    type: Literal["image", "document"]
    # `Any`, not `dict`: a log is external input, and a `source` that is null or
    # a bare string must render as what it is rather than raise a
    # ValidationError that aborts the whole file.
    source: Any = {}

class UnknownBlock(_Base):
    """Catch-all for unrecognized block types."""
    type: str = "unknown"

ContentBlock = (ThinkingBlock | TextBlock | ToolUseBlock | ToolResultBlock
                | BinaryBlock | UnknownBlock)

_CONTENT_BLOCK_MAP: dict[str, type[ContentBlock]] = {
    "thinking": ThinkingBlock,
    "text": TextBlock,
    "tool_use": ToolUseBlock,
    "tool_result": ToolResultBlock,
    "image": BinaryBlock,
    "document": BinaryBlock,
}

def parse_content_block(raw: dict[str, Any]) -> ContentBlock:
    cls = _CONTENT_BLOCK_MAP.get(raw.get("type", ""), UnknownBlock)
    return cls.model_validate(raw)


# ─── Usage ───────────────────────────────────────────────────────────────────

class CacheCreation(_Base):
    ephemeral_5m_input_tokens: int = 0
    ephemeral_1h_input_tokens: int = 0

class Usage(_Base):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_creation: CacheCreation | None = None
    service_tier: str | None = None


# ─── Message wrapper (the API message object) ───────────────────────────────

class Message(_Base):
    id: str = ""
    type: str = "message"
    role: str = ""
    model: str = ""
    content: str | list[dict[str, Any]] = ""
    stop_reason: str | None = None
    stop_sequence: str | None = None
    usage: Usage | None = None

    def content_blocks(self) -> list[ContentBlock]:
        if isinstance(self.content, list):
            return [parse_content_block(b) for b in self.content]
        return []


# ─── ToolUseResult (top-level on user records) ──────────────────────────────

class ToolUseResultDict(_Base):
    stdout: str = ""
    stderr: str = ""
    interrupted: bool = False

def parse_tool_use_result(raw: Any) -> Any:
    """Parse a user record's top-level toolUseResult.

    The field is whatever a tool put in its result `data`, so it has no
    closed shape: Bash writes an object, MCP tools write the string or
    content-block array their server returned, and the plugin-eval tools
    JSON.parse arbitrary output into it — a bare number or boolean included.

    Only the object form is modelled, because it is the only one the
    renderer reads a field out of. Every other value is returned untouched:
    the tool_result block is built from that same value, so the renderer has
    it already. See notes/tool-use-result-shapes.md.
    """
    if isinstance(raw, dict):
        return ToolUseResultDict.model_validate(raw)
    return raw


# ─── Progress data variants ─────────────────────────────────────────────────

class BashProgress(_Base):
    type: Literal["bash_progress"]
    output: str = ""
    fullOutput: str = ""
    elapsedTimeSeconds: float = 0
    totalLines: int = 0
    totalBytes: int = 0
    taskId: str | None = None
    timeoutMs: int | None = None

class AgentProgress(_Base):
    type: Literal["agent_progress"]
    agentId: str = ""
    prompt: str = ""
    message: dict[str, Any] | None = None
    normalizedMessages: list[Any] | None = None

class HookProgress(_Base):
    type: Literal["hook_progress"]
    hookEvent: str = ""
    hookName: str = ""
    command: str = ""

class UnknownProgress(_Base):
    type: str = "unknown"

ProgressData = BashProgress | AgentProgress | HookProgress | UnknownProgress

_PROGRESS_MAP: dict[str, type[ProgressData]] = {
    "bash_progress": BashProgress,
    "agent_progress": AgentProgress,
    "hook_progress": HookProgress,
}

def parse_progress_data(raw: dict[str, Any]) -> ProgressData:
    cls = _PROGRESS_MAP.get(raw.get("type", ""), UnknownProgress)
    return cls.model_validate(raw)


# ─── Hook info (inside stop_hook_summary) ────────────────────────────────────

class HookInfo(_Base):
    command: str = "?"
    durationMs: int = 0


# ─── File snapshot ───────────────────────────────────────────────────────────

class FileSnapshot(_Base):
    messageId: str = ""
    trackedFileBackups: dict[str, Any] = {}
    timestamp: str = ""


# ─── Top-level records (each JSONL line) ─────────────────────────────────────

class AssistantRecord(_Base):
    type: Literal["assistant"]
    uuid: str = ""
    timestamp: str = ""
    sessionId: str = ""
    parentUuid: str | None = None
    message: Message = Field(default_factory=Message)
    # Session metadata
    version: str = ""
    slug: str = ""
    cwd: str = ""
    gitBranch: str = ""

class UserRecord(_Base):
    type: Literal["user"]
    uuid: str = ""
    timestamp: str = ""
    sessionId: str = ""
    parentUuid: str | None = None
    message: Message = Field(default_factory=Message)
    toolUseResult: Any = None  # arbitrary tool-defined JSON — parsed separately
    sourceToolAssistantUUID: str = ""
    sourceToolUseID: str = ""
    version: str = ""
    slug: str = ""
    cwd: str = ""
    gitBranch: str = ""

    def parsed_tool_use_result(self) -> Any:
        return parse_tool_use_result(self.toolUseResult)

class SystemRecord(_Base):
    """A host-side banner or turn marker.

    Claude Code's own subtypes and their fields are declared one constructor
    each at `chunk-wgfrtm7w.js:168850-169035`; `informational` has no single
    constructor (any part of the loop raises one) and carries `content` plus
    `level`. `cc_pretty_intercept.convert` reuses this class for an intercept
    capture's `api_*` regions, which is why `content`/`detail`/`content_leaf`
    sit here beside cc's fields.
    """
    type: Literal["system"]
    uuid: str = ""
    timestamp: str = ""
    sessionId: str = ""
    parentUuid: str | None = None
    subtype: str = ""
    # turn_duration
    durationMs: int = 0
    # stop_hook_summary.  hookErrors and hookAdditionalContext are the two
    # channels a Stop hook reaches anyone through; the summary is where a
    # blocked turn says so.
    hookCount: int = 0
    hookInfos: list[dict[str, Any]] = []
    hookErrors: list[str] | None = None
    hookAdditionalContext: list[str] | None = None
    preventedContinuation: bool = False
    stopReason: str | None = None
    # local_command, informational, away_summary, scheduled_task_fire,
    # bridge_status, cloud_session_status, permission_retry, compact_boundary
    content: str = ""
    # informational and the error subtypes: one of
    # info / notice / suggestion / warning / error
    level: str | None = None
    # memory_saved
    writtenPaths: list[str] | None = None
    # permission_retry
    commands: list[str] | None = None
    # api_error, as Claude Code writes it: an object whose `formatted` is the
    # sentence a human reads.  The intercept capture's own api_error region
    # leaves this unset and puts its text in `content` instead, which is how
    # the renderer tells the two apart.
    error: Any = None
    source: str | None = None
    retryAttempt: int | None = None
    maxRetries: int | None = None
    # model_refusal_fallback / model_refusal_no_fallback / model_consent_fallback.
    # Nullable because Claude Code writes `apiRefusalExplanation: null` when the
    # API gave a category and no prose, and a field too narrow for one subtype
    # fails the whole record out of `parse_all` — hiding the subtype outright.
    originalModel: str | None = None
    apiRefusalCategory: str | None = None
    apiRefusalExplanation: str | None = None
    version: str = ""
    slug: str = ""
    cwd: str = ""

    def parsed_hook_infos(self) -> list[HookInfo]:
        return [HookInfo.model_validate(h) for h in self.hookInfos]

class ProgressRecord(_Base):
    type: Literal["progress"]
    uuid: str = ""
    timestamp: str = ""
    sessionId: str = ""
    data: dict[str, Any] = {}
    parentToolUseID: str = ""
    toolUseID: str = ""
    version: str = ""

    def parsed_data(self) -> ProgressData:
        return parse_progress_data(self.data)

class FileHistorySnapshotRecord(_Base):
    type: Literal["file-history-snapshot"]
    messageId: str = ""
    snapshot: dict[str, Any] = {}
    isSnapshotUpdate: bool = False

    def parsed_snapshot(self) -> FileSnapshot:
        return FileSnapshot.model_validate(self.snapshot)

class FileHistoryDeltaRecord(_Base):
    """One file's backup, appended between snapshots.

    A snapshot carries every tracked file; a delta names the one that changed
    and points back at the snapshot it amends, so the two render as the same
    kind of row.
    """
    type: Literal["file-history-delta"]
    messageId: str = ""
    snapshotMessageId: str = ""
    trackingPath: str = ""
    backup: dict[str, Any] = {}

class LastPromptRecord(_Base):
    type: Literal["last-prompt"]
    sessionId: str = ""
    lastPrompt: str = ""

class QueueOperationRecord(_Base):
    type: Literal["queue-operation"]
    timestamp: str = ""
    sessionId: str = ""
    operation: str = ""
    content: str | None = None


# ─── Attachment payload (inner `.attachment` dict) ──────────────────────────
# Fields vary by attachment subtype; declared permissively so any subtype
# parses cleanly. See attachment_is_model_visible in main.py for which records
# contribute to the model's view.

class AttachmentData(_Base):
    type: str = "unknown"
    # hook_success / hook_non_blocking_error / hook_additional_context
    hookName: str = ""
    hookEvent: str = ""
    toolUseID: str = ""
    command: str = ""
    stdout: str = ""
    stderr: str = ""
    exitCode: int = 0
    durationMs: int = 0
    # hook_additional_context content is a list[str] (one per source hook);
    # task_reminder / skill_listing content is a str — accept either.
    content: Any = ""
    # task_reminder
    itemCount: int = 0
    # skill_listing
    skillCount: int = 0
    isInitial: bool = False
    # output_style carries the style's name; output_style_instructions carries
    # the whole style object, so neither type nor shape is fixed here.
    style: Any = ""
    # deferred_tools_delta
    addedNames: list[str] = []
    removedNames: list[str] = []
    readdedNames: list[str] = []
    addedLines: list[str] = []
    pendingMcpServers: list[Any] = []
    # command_permissions
    allowedTools: list[str] = []
    # date_change
    newDate: str = ""
    # file / edited_text_file / compact_file_reference / nested_memory
    filename: str = ""
    displayPath: str = ""
    path: str = ""
    snippet: str = ""
    # queued_command.  A prompt carrying a pasted image is a list of content
    # blocks rather than a string (`chunk-wgfrtm7w.js:168334`,
    # `if (Array.isArray(e.prompt))`); typed as str alone, such a record fails
    # validation and parse_all drops it, taking the user's message with it.
    prompt: str | list[dict[str, Any]] = ""
    commandMode: str = ""
    renderedByBatchHead: bool = False


class AttachmentRecord(_Base):
    type: Literal["attachment"]
    uuid: str = ""
    timestamp: str = ""
    sessionId: str = ""
    parentUuid: str | None = None
    isSidechain: bool = False
    attachment: AttachmentData = Field(default_factory=AttachmentData)
    # The conversion output Claude Code captured for this record when it wrote
    # the log — one {"content": str} entry per message the record became. Only
    # sessions from 2.1.269 onward carry it, and only where every message the
    # attachment produced was plain text.
    rendered: list[dict[str, Any]] = []
    version: str = ""
    slug: str = ""
    cwd: str = ""
    gitBranch: str = ""


class PermissionModeRecord(_Base):
    type: Literal["permission-mode"]
    permissionMode: str = ""
    sessionId: str = ""


class UnknownRecord(_Base):
    """Catch-all for unrecognized record types."""
    type: str = "unknown"
    timestamp: str = ""

Record = (
    AssistantRecord | UserRecord | SystemRecord | ProgressRecord
    | FileHistorySnapshotRecord | FileHistoryDeltaRecord | LastPromptRecord
    | QueueOperationRecord | AttachmentRecord | PermissionModeRecord
    | UnknownRecord
)

_RECORD_MAP: dict[str, type[Record]] = {
    "assistant": AssistantRecord,
    "user": UserRecord,
    "system": SystemRecord,
    "progress": ProgressRecord,
    "file-history-snapshot": FileHistorySnapshotRecord,
    "file-history-delta": FileHistoryDeltaRecord,
    "last-prompt": LastPromptRecord,
    "queue-operation": QueueOperationRecord,
    "attachment": AttachmentRecord,
    "permission-mode": PermissionModeRecord,
}

def parse_record(raw: dict[str, Any]) -> Record:
    cls = _RECORD_MAP.get(raw.get("type", ""), UnknownRecord)
    return cls.model_validate(raw)


# ─── JSONL file reading ─────────────────────────────────────────────────────

def read_jsonl(path: str) -> list[tuple[dict[str, Any], int]]:
    """Read a JSONL file, returning (parsed_dict, line_number) pairs.
    Skips blank lines. Raises on file errors, prints JSON parse errors to stderr.
    """
    import sys
    records: list[tuple[dict[str, Any], int]] = []
    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append((json.loads(line), lineno))
            except json.JSONDecodeError as e:
                print(f"[line {lineno}] JSON parse error: {e}", file=sys.stderr)
    return records


def parse_all(raw_records: list[tuple[dict[str, Any], int]]) -> tuple[list[tuple[Record, int]], int]:
    """Parse raw dicts through pydantic schema.
    Returns (parsed_records, error_count).
    """
    import sys
    records: list[tuple[Record, int]] = []
    errors = 0
    for raw, lineno in raw_records:
        try:
            records.append((parse_record(raw), lineno))
        except Exception as e:
            errors += 1
            print(f"[line {lineno}] Schema validation error: {e}", file=sys.stderr)
    return records, errors

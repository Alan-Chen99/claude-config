"""Pydantic schema and parse functions for Claude Code JSONL session logs.

Handles all record types found in Claude Code JSONL logs:
  assistant, user, system, progress, file-history-snapshot, last-prompt, queue-operation

Content block types: thinking, text, tool_use, tool_result
Progress data types: bash_progress, agent_progress, hook_progress
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

class UnknownBlock(_Base):
    """Catch-all for unrecognized block types."""
    type: str = "unknown"

ContentBlock = ThinkingBlock | TextBlock | ToolUseBlock | ToolResultBlock | UnknownBlock

_CONTENT_BLOCK_MAP: dict[str, type[ContentBlock]] = {
    "thinking": ThinkingBlock,
    "text": TextBlock,
    "tool_use": ToolUseBlock,
    "tool_result": ToolResultBlock,
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

def parse_tool_use_result(raw: Any) -> str | ToolUseResultDict | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        return ToolUseResultDict.model_validate(raw)
    raise ValueError(f"unexpected toolUseResult type: {type(raw)}")


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
    message: Message = Field(default_factory=Message)
    toolUseResult: Any = None  # str | dict | None — parsed separately
    sourceToolAssistantUUID: str = ""
    sourceToolUseID: str = ""
    version: str = ""
    slug: str = ""
    cwd: str = ""
    gitBranch: str = ""

    def parsed_tool_use_result(self) -> str | ToolUseResultDict | None:
        return parse_tool_use_result(self.toolUseResult)

class SystemRecord(_Base):
    type: Literal["system"]
    uuid: str = ""
    timestamp: str = ""
    sessionId: str = ""
    subtype: str = ""
    # turn_duration
    durationMs: int = 0
    # stop_hook_summary
    hookCount: int = 0
    hookInfos: list[dict[str, Any]] = []
    # local_command
    content: str = ""
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

class UnknownRecord(_Base):
    """Catch-all for unrecognized record types."""
    type: str = "unknown"
    timestamp: str = ""

Record = (
    AssistantRecord | UserRecord | SystemRecord | ProgressRecord
    | FileHistorySnapshotRecord | LastPromptRecord | QueueOperationRecord
    | UnknownRecord
)

_RECORD_MAP: dict[str, type[Record]] = {
    "assistant": AssistantRecord,
    "user": UserRecord,
    "system": SystemRecord,
    "progress": ProgressRecord,
    "file-history-snapshot": FileHistorySnapshotRecord,
    "last-prompt": LastPromptRecord,
    "queue-operation": QueueOperationRecord,
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

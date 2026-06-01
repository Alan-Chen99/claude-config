"""Rendering and formatting for Claude Code JSONL session logs.

Pure display logic — takes parsed records and produces formatted strings.
No JSON parsing or schema validation here.
"""

from __future__ import annotations

import json
import textwrap
from datetime import datetime

from claude_config.cc_pretty.parse import (
    AgentProgress,
    AssistantRecord,
    AttachmentRecord,
    BashProgress,
    FileHistorySnapshotRecord,
    HookProgress,
    LastPromptRecord,
    PermissionModeRecord,
    ProgressRecord,
    QueueOperationRecord,
    SystemRecord,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    ToolUseResultDict,
    Usage,
    UserRecord,
)


# ─── ANSI colors ────────────────────────────────────────────────────────────

class C:
    """ANSI color codes, disabled when --no-color."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    USER = "\033[1;34m"       # bold blue
    ASSISTANT = "\033[1;32m"  # bold green
    SYSTEM = "\033[1;33m"     # bold yellow
    THINKING = "\033[35m"     # magenta
    TOOL = "\033[36m"         # cyan
    RESULT = "\033[33m"       # yellow
    ERROR = "\033[1;31m"      # bold red
    SEPARATOR = "\033[90m"    # gray
    TIMESTAMP = "\033[90m"    # gray
    HINT = "\033[90m"         # gray (for jq hints)
    PROGRESS = "\033[90m"     # gray
    QUEUE = "\033[90;3m"      # gray italic
    REWIND = "\033[1;35m"     # bold magenta

    @classmethod
    def disable(cls):
        for attr in list(vars(cls)):
            if attr.isupper():
                setattr(cls, attr, "")


# ─── Text helpers ────────────────────────────────────────────────────────────

_NEXT_STEP_NEEDLE = "NEXT STEP"
_NEXT_STEP_PAD = 200
_NEXT_STEP_MERGE_GAP = 100


def _merge_windows(
    windows: list[tuple[int, int]], gap: int = 0
) -> list[tuple[int, int]]:
    """Merge a sorted list of (lo, hi) windows when the gap between them is <= gap."""
    merged: list[tuple[int, int]] = []
    for lo, hi in sorted(windows):
        if merged and lo - merged[-1][1] <= gap:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return merged


def trunc(s: str, maxlen: int) -> str:
    """Truncate ``s`` to approximately ``maxlen`` chars using a head+tail strategy.

    If ``NEXT STEP`` appears in mid-text, a ±200-char window around each
    occurrence is preserved. Output may exceed ``maxlen`` when NEXT STEP
    windows are present.
    """
    if len(s) <= maxlen:
        return s
    head = maxlen * 2 // 3
    tail = maxlen - head
    n = len(s)

    # Structural windows: head [0:head) and tail [n-tail:n).
    structural: list[tuple[int, int]] = [(0, head), (n - tail, n)]

    # Find every NEXT STEP occurrence and expand into a candidate window.
    # Merge close NEXT STEP candidates together (but NOT yet with head/tail).
    ns_candidates: list[tuple[int, int]] = []
    start = 0
    while True:
        idx = s.find(_NEXT_STEP_NEEDLE, start)
        if idx == -1:
            break
        w_lo = max(0, idx - _NEXT_STEP_PAD)
        w_hi = min(n, idx + len(_NEXT_STEP_NEEDLE) + _NEXT_STEP_PAD)
        ns_candidates.append((w_lo, w_hi))
        start = idx + len(_NEXT_STEP_NEEDLE)
    ns_merged = _merge_windows(ns_candidates, gap=_NEXT_STEP_MERGE_GAP)

    # Combine all windows and merge by overlap only (gap=0), so structural
    # head/tail windows never merge with each other just because maxlen is small.
    all_windows = _merge_windows(structural + ns_merged, gap=0)

    # Stitch the output: window text, then gap marker, then next window.
    parts: list[str] = []
    cursor = 0
    for lo, hi in all_windows:
        if cursor < lo:
            omitted = lo - cursor
            parts.append(f" ... [{omitted} more chars] ... ")
        parts.append(s[lo:hi])
        cursor = hi
    if cursor < n:
        omitted = n - cursor
        parts.append(f" ... [{omitted} more chars] ... ")
    return "".join(parts)


def is_truncated(s: str, maxlen: int) -> bool:
    return len(s) > maxlen


def fmt_tool_input(inp: dict) -> str:
    """Format tool input dict as readable key-value pairs with raw strings.

    json.dumps quotes strings and escapes \\n, \\t, \\" — unreadable for code.
    This renders string values as raw text, multi-line strings as indented blocks.
    """
    if not isinstance(inp, dict):
        return json.dumps(inp, indent=2) if not isinstance(inp, str) else inp
    lines: list[str] = []
    for key, val in inp.items():
        if isinstance(val, str):
            if "\n" in val or len(val) > 120:
                lines.append(f"{key}:")
                lines.extend(f"  {line}" for line in val.splitlines())
            else:
                lines.append(f"{key}: {val}")
        elif isinstance(val, bool):
            lines.append(f"{key}: {str(val).lower()}")
        elif val is None:
            lines.append(f"{key}: null")
        elif isinstance(val, (int, float)):
            lines.append(f"{key}: {val}")
        else:
            # lists, nested dicts — fall back to compact JSON
            lines.append(f"{key}: {json.dumps(val)}")
    return "\n".join(lines)


def fmt_ts(ts_str: str) -> str:
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return ts_str or ""


def fmt_duration(ms: int | float) -> str:
    ms = int(ms)
    if ms < 1000:
        return f"{ms}ms"
    secs = ms / 1000
    if secs < 60:
        return f"{secs:.1f}s"
    mins = int(secs // 60)
    remaining = secs % 60
    return f"{mins}m{remaining:.0f}s"


def separator() -> str:
    return f"{C.SEPARATOR}{'─' * 80}{C.RESET}"


def ind(text: str, prefix: str = "  ") -> str:
    return textwrap.indent(text, prefix)


def jq_hint(log_path: str, lineno: int, jq_path: str) -> str:
    cmd = f"sed -n '{lineno}p' {log_path} | jq -r '{jq_path}'"
    return f"{C.HINT}    # {cmd}{C.RESET}"


# ─── Usage formatting ───────────────────────────────────────────────────────

def fmt_usage(u: Usage) -> str:
    parts = [f"in:{u.input_tokens:,}", f"out:{u.output_tokens:,}"]
    if u.cache_read_input_tokens:
        parts.append(f"cached:{u.cache_read_input_tokens:,}")
    if u.cache_creation_input_tokens:
        parts.append(f"cache_create:{u.cache_creation_input_tokens:,}")
    if u.cache_creation:
        if u.cache_creation.ephemeral_5m_input_tokens:
            parts.append(f"eph5m:{u.cache_creation.ephemeral_5m_input_tokens:,}")
        if u.cache_creation.ephemeral_1h_input_tokens:
            parts.append(f"eph1h:{u.cache_creation.ephemeral_1h_input_tokens:,}")
    return " ".join(parts)


# ─── Renderer ────────────────────────────────────────────────────────────────

class Renderer:
    """Stateful renderer that tracks tool_use IDs to correlate results with names."""

    def __init__(self, log_path: str, tool_output_max: int,
                 tool_input_max: int, show_thinking: bool = True):
        self.log_path = log_path
        self.tool_output_max = tool_output_max
        self.tool_input_max = tool_input_max
        self.show_thinking = show_thinking
        self._tool_id_to_name: dict[str, str] = {}

    # ── Content block renderers ──────────────────────────────────────────

    def _render_thinking(self, block: ThinkingBlock) -> str:
        prefix = C.THINKING + "  │ " + C.RESET
        body = textwrap.indent(block.thinking, prefix, predicate=lambda _: True)
        return (
            f"{C.THINKING}  ╭─ thinking ─────────────────────────{C.RESET}\n"
            f"{body}\n"
            f"{C.THINKING}  ╰─────────────────────────────────────{C.RESET}"
        )

    def _render_tool_use(self, block: ToolUseBlock, lineno: int, block_idx: int) -> str:
        inp = block.input
        inp_str = fmt_tool_input(inp) if isinstance(inp, dict) else str(inp)

        if block.id:
            self._tool_id_to_name[block.id] = block.name

        id_suffix = f"  {C.DIM}({block.id}){C.RESET}" if block.id else ""
        lines = [f"{C.TOOL}  ▶ {block.name}{C.RESET}{id_suffix}"]
        lines.append(ind(trunc(inp_str, self.tool_input_max), "    "))
        if is_truncated(inp_str, self.tool_input_max):
            lines.append(jq_hint(self.log_path, lineno, f".message.content[{block_idx}].input"))
        return "\n".join(lines)

    def _render_tool_result(self, block: ToolResultBlock, lineno: int, block_idx: int,
                            tur: str | ToolUseResultDict | None = None) -> str:
        tool_name = self._tool_id_to_name.get(block.tool_use_id, "")
        name_suffix = f" ({tool_name})" if tool_name else ""

        label_color = C.ERROR if block.is_error else C.RESULT
        label = f"✗ error{name_suffix}" if block.is_error else f"◀ result{name_suffix}"

        content = block.content
        any_truncated = False

        if isinstance(content, list):
            parts = []
            for sub in content:
                if sub.get("type") == "text":
                    t = sub.get("text", "")
                    parts.append(trunc(t, self.tool_output_max))
                    if is_truncated(t, self.tool_output_max):
                        any_truncated = True
                else:
                    s = str(sub)
                    parts.append(trunc(s, self.tool_output_max))
                    if is_truncated(s, self.tool_output_max):
                        any_truncated = True
            body = "\n".join(parts)
        else:
            body = trunc(content, self.tool_output_max)
            any_truncated = is_truncated(content, self.tool_output_max)

        jq_path = f".message.content[{block_idx}].content"
        lines = [f"{label_color}  {label}{C.RESET}", ind(body, "    ")]
        if any_truncated:
            lines.append(jq_hint(self.log_path, lineno, jq_path))

        if isinstance(tur, ToolUseResultDict):
            if tur.stderr:
                lines.append(f"    {C.DIM}stderr: {trunc(tur.stderr, 100)}{C.RESET}")
        elif isinstance(tur, str) and tur:
            lines.append(f"    {C.DIM}{trunc(tur, 120)}{C.RESET}")

        return "\n".join(lines)

    def _render_context_text(self, text: str, lineno: int, block_idx: int) -> str:
        lines = [f"{C.RESULT}  ◀ context{C.RESET}", ind(trunc(text, self.tool_output_max), "    ")]
        if is_truncated(text, self.tool_output_max):
            lines.append(jq_hint(self.log_path, lineno, f".message.content[{block_idx}].text"))
        return "\n".join(lines)

    # ── Turn renderers ───────────────────────────────────────────────────

    def render_user_input(self, records: list[tuple[UserRecord, int]], ts: str) -> str:
        lines = [f"{C.USER}┌ User{C.RESET}  {C.TIMESTAMP}{ts}{C.RESET}"]
        for rec, _ in records:
            if isinstance(rec.message.content, str):
                lines.append(ind(rec.message.content, "  "))
        return "\n".join(lines)

    def render_tool_output(self, records: list[tuple[UserRecord, int]], ts: str) -> str:
        lines = [f"{C.RESULT}┌ Tool Output{C.RESET}  {C.TIMESTAMP}{ts}{C.RESET}"]
        for rec, lineno in records:
            tur = rec.parsed_tool_use_result()
            for bi, block in enumerate(rec.message.content_blocks()):
                if isinstance(block, ToolResultBlock):
                    lines.append(self._render_tool_result(block, lineno, bi, tur=tur))
                elif isinstance(block, TextBlock):
                    lines.append(self._render_context_text(block.text, lineno, bi))
        return "\n".join(lines)

    def render_assistant_turn(self, records: list[tuple[AssistantRecord, int]], ts: str) -> str:
        usage: Usage | None = None
        model = ""
        stop_reason = ""

        for rec, _ in records:
            if rec.message.usage and not usage:
                usage = rec.message.usage
            if rec.message.model and not model:
                model = rec.message.model
            if rec.message.stop_reason and not stop_reason:
                stop_reason = rec.message.stop_reason

        model_tag = ""
        if model == "<synthetic>":
            model_tag = f"  {C.DIM}[synthetic]{C.RESET}"
        elif model:
            model_tag = f"  {C.DIM}[{model}]{C.RESET}"

        stop_tag = ""
        if stop_reason and stop_reason != "end_turn":
            stop_tag = f"  {C.DIM}stop:{stop_reason}{C.RESET}"

        lines = [f"{C.ASSISTANT}┌ Assistant{C.RESET}{model_tag}  {C.TIMESTAMP}{ts}{C.RESET}{stop_tag}"]
        if usage:
            lines[0] += f"  {C.DIM}[{fmt_usage(usage)}]{C.RESET}"

        for rec, lineno in records:
            for bi, block in enumerate(rec.message.content_blocks()):
                if isinstance(block, ThinkingBlock):
                    if self.show_thinking:
                        lines.append(self._render_thinking(block))
                    else:
                        lines.append(f"{C.THINKING}  [thinking: {len(block.thinking)} chars]{C.RESET}")
                elif isinstance(block, TextBlock):
                    lines.append(ind(block.text, "  "))
                elif isinstance(block, ToolUseBlock):
                    lines.append(self._render_tool_use(block, lineno, bi))

        return "\n".join(lines)

    def render_system(self, rec: SystemRecord, ts: str) -> str:
        if rec.subtype == "turn_duration":
            return (
                f"{C.SYSTEM}┌ System{C.RESET}  {C.TIMESTAMP}{ts}{C.RESET}"
                f"  {C.DIM}turn_duration: {fmt_duration(rec.durationMs)}{C.RESET}"
            )

        if rec.subtype == "stop_hook_summary":
            lines = [
                f"{C.SYSTEM}┌ System{C.RESET}  {C.TIMESTAMP}{ts}{C.RESET}"
                f"  {C.DIM}hooks: {rec.hookCount} ran{C.RESET}"
            ]
            for hi in rec.parsed_hook_infos():
                lines.append(f"  {C.DIM}  hook: {hi.command} ({fmt_duration(hi.durationMs)}){C.RESET}")
            return "\n".join(lines)

        if rec.subtype == "local_command":
            return (
                f"{C.SYSTEM}┌ System{C.RESET}  {C.DIM}[local_command]{C.RESET}"
                f"  {C.TIMESTAMP}{ts}{C.RESET}\n"
                f"{ind(rec.content[:200], '  ')}"
            )

        return f"{C.SYSTEM}┌ System{C.RESET}  {C.DIM}[{rec.subtype}]{C.RESET}  {C.TIMESTAMP}{ts}{C.RESET}"

    def render_progress(self, rec: ProgressRecord, ts: str) -> str:
        data = rec.parsed_data()

        if isinstance(data, BashProgress):
            preview = data.output.strip().split("\n")[-1] if data.output else ""
            if len(preview) > 120:
                preview = preview[:120] + "..."
            return (
                f"{C.PROGRESS}  ⋯ bash {data.elapsedTimeSeconds:.0f}s"
                f" ({data.totalLines} lines, {data.totalBytes} bytes)"
                f" {preview}{C.RESET}"
            )

        if isinstance(data, AgentProgress):
            aid = data.agentId[:12] if data.agentId else "?"
            preview = data.prompt[:80] + "..." if len(data.prompt) > 80 else data.prompt
            return f"{C.PROGRESS}  ⋯ agent {aid} {preview}{C.RESET}"

        if isinstance(data, HookProgress):
            return f"{C.PROGRESS}  ⋯ hook {data.hookName}: {data.command}{C.RESET}"

        return f"{C.PROGRESS}  ⋯ progress [{getattr(data, 'type', '?')}]{C.RESET}"

    def render_file_snapshot(self, rec: FileHistorySnapshotRecord) -> str:
        snap = rec.parsed_snapshot()
        file_count = len(snap.trackedFileBackups)
        label = "update" if rec.isSnapshotUpdate else "snapshot"
        return f"{C.DIM}  ⌂ file-history {label}: {file_count} files tracked{C.RESET}"

    def render_queue_op(self, rec: QueueOperationRecord) -> str:
        content = rec.content or ""
        preview = content[:100] + "..." if len(content) > 100 else content
        preview = preview.replace("<task-notification>", "").replace("</task-notification>", "").strip()
        return f"{C.QUEUE}  ⊞ queue {rec.operation}: {preview}{C.RESET}"

    def render_last_prompt(self, rec: LastPromptRecord) -> str:
        preview = rec.lastPrompt[:100] + "..." if len(rec.lastPrompt) > 100 else rec.lastPrompt
        return f"{C.DIM}  ⎘ last-prompt: {preview}{C.RESET}"

    def render_attachment(self, rec: AttachmentRecord, ts: str, lineno: int) -> str:
        """Render an attachment record.

        hook_additional_context gets a multi-line block (model-visible
        system-reminder text); other subtypes get one-line summaries.
        """
        a = rec.attachment
        atype = a.type

        if atype == "hook_additional_context":
            # The exact text the model received as <system-reminder>
            content = a.content
            if isinstance(content, list):
                body = "\n\n".join(str(x) for x in content)
            else:
                body = str(content)
            hook_label = a.hookName or a.hookEvent or "?"
            header = (
                f"{C.SYSTEM}┌ Additional Context{C.RESET}  "
                f"{C.DIM}[{hook_label}]{C.RESET}  "
                f"{C.TIMESTAMP}{ts}{C.RESET}"
            )
            truncated_body = trunc(body, self.tool_output_max)
            lines = [header, ind(truncated_body, "  ")]
            if is_truncated(body, self.tool_output_max):
                lines.append(jq_hint(self.log_path, lineno, ".attachment.content"))
            return "\n".join(lines)

        if atype == "hook_success":
            return (
                f"{C.DIM}  ⊙ hook {a.hookName or '?'}: "
                f"exit {a.exitCode}, {fmt_duration(a.durationMs)}{C.RESET}"
            )

        if atype == "hook_non_blocking_error":
            err = trunc(a.stderr or str(a.content) or "?", 200)
            return (
                f"{C.ERROR}  ⊙ hook ERROR {a.hookName or '?'}: "
                f"exit {a.exitCode}{C.RESET}\n"
                f"    {C.DIM}{err}{C.RESET}"
            )

        if atype == "task_reminder":
            return f"{C.DIM}  ⊞ task reminder: {a.itemCount} task(s){C.RESET}"

        if atype == "skill_listing":
            marker = "initial" if a.isInitial else "delta"
            return (
                f"{C.DIM}  ⊞ skill listing [{marker}]: "
                f"{a.skillCount} skill(s){C.RESET}"
            )

        if atype == "output_style":
            return f"{C.DIM}  ⊞ output style: {a.style}{C.RESET}"

        if atype == "deferred_tools_delta":
            parts: list[str] = []
            if a.addedNames:
                parts.append(f"+{len(a.addedNames)}")
            if a.removedNames:
                parts.append(f"-{len(a.removedNames)}")
            if a.readdedNames:
                parts.append(f"re-add {len(a.readdedNames)}")
            summary = " ".join(parts) or "(no changes)"
            return f"{C.DIM}  ⊞ deferred tools {summary}{C.RESET}"

        if atype == "ultrathink_effort":
            return f"{C.DIM}  ⊞ ultrathink effort{C.RESET}"

        if atype == "command_permissions":
            return f"{C.DIM}  ⊞ permissions: {len(a.allowedTools)} allowed{C.RESET}"

        if atype == "date_change":
            return f"{C.DIM}  ⊞ date change: {a.newDate}{C.RESET}"

        if atype == "queued_command":
            preview = trunc(a.prompt, 80)
            return f"{C.DIM}  ⊞ queued [{a.commandMode}]: {preview}{C.RESET}"

        if atype in ("file", "edited_text_file", "compact_file_reference", "nested_memory"):
            label = a.displayPath or a.path or a.filename or "?"
            return f"{C.DIM}  ⊞ {atype}: {label}{C.RESET}"

        return f"{C.DIM}  ⊞ attachment [{atype}]{C.RESET}"

    def render_permission_mode(self, rec: PermissionModeRecord) -> str:
        return f"{C.DIM}  ⊞ permission-mode: {rec.permissionMode}{C.RESET}"

    # ── Session header ───────────────────────────────────────────────────

    def render_session_header(self, first_record) -> str | None:
        version = getattr(first_record, "version", "")
        session_id = getattr(first_record, "sessionId", "")
        slug = getattr(first_record, "slug", "")
        cwd = getattr(first_record, "cwd", "")
        header_parts = []
        if slug:
            header_parts.append(f"session: {slug}")
        if session_id:
            header_parts.append(f"id: {session_id[:8]}")
        if version:
            header_parts.append(f"v{version}")
        if cwd:
            header_parts.append(f"cwd: {cwd}")
        if header_parts:
            return f"{C.DIM}{'  '.join(header_parts)}{C.RESET}"
        return None

    def render_rewind_marker(
        self, count: int, first_ts: str, last_ts: str,
        n_user: int, n_assistant: int, hidden: bool,
    ) -> str:
        time_range = f"{first_ts}\u2013{last_ts}" if first_ts != last_ts else first_ts
        turns = f"{n_user} user, {n_assistant} assistant"
        status = f"{count} records hidden" if hidden else f"{count} records shown above"
        return (
            f"{C.REWIND}{'─' * 30} ⟲ rewind {'─' * 30}{C.RESET}\n"
            f"{C.DIM}  {turns}  {time_range}  ({status}){C.RESET}"
        )

    def render_compaction_marker(
        self, section_num: int, prev_records: int,
        prev_first_ts: str, prev_last_ts: str,
        prev_n_user: int, prev_n_assistant: int,
        tokens_before: int, tokens_after: int,
    ) -> str:
        time_range = (
            f"{prev_first_ts}\u2013{prev_last_ts}"
            if prev_first_ts != prev_last_ts else prev_first_ts
        )
        header = f"{C.SYSTEM}{'─' * 26} ⟐ compacted {'─' * 26}{C.RESET}"
        prev_summary = (
            f"  section {section_num}: "
            f"{prev_n_user} user, {prev_n_assistant} assistant  "
            f"{time_range}  ({prev_records} records)"
        )
        token_info = ""
        if tokens_before or tokens_after:
            parts = []
            if tokens_before:
                parts.append(f"{tokens_before:,}tok")
            if tokens_after:
                parts.append(f"{tokens_after:,}tok")
            arrow = " → ".join(parts)
            token_info = f"\n{C.DIM}  context: {arrow}{C.RESET}"
        return f"{header}\n{C.DIM}{prev_summary}{C.RESET}{token_info}"

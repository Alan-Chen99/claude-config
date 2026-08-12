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
    # Form feed: 1 token vs 10 for 80× ─. Renders as a horizontal rule in
    # Emacs page-break-lines-mode; in plain terminals it appears as ^L or
    # a small glyph but still serves as a visible turn boundary.
    return f"{C.SEPARATOR}\f{C.RESET}"


def ind(text: str, prefix: str = "  ") -> str:
    return textwrap.indent(text, prefix)


def fmt_ref(lineno: int, block_idx: int = 0) -> str:
    """Compact JSONL back-reference: `@L<n>` (or `@L<n>[i]` for non-zero block).

    Block index is omitted when 0 — single-block records are the common case
    and the bracket adds noise. The legend printed at the top of the output
    explains the recovery recipe; per-occurrence refs carry only the
    coordinates.
    """
    if block_idx:
        return f"@L{lineno}[{block_idx}]"
    return f"@L{lineno}"


def _resolve_idx(block: object, enum_idx: int) -> int:
    """Source-true block index: opencode ``_pi`` when present, else enum index."""
    pi = getattr(block, "_pi", None)
    return pi if isinstance(pi, int) else enum_idx


def block_ref(block: object, lineno: int, enum_idx: int) -> str:
    """Ref for a content block, source-true across harnesses.

    opencode conversion tags each block with ``_pi`` — the index of the part
    in the exported message it came from — because dropped parts
    (step-start/step-finish/...) would otherwise shift the enumeration index
    away from the jq path the legend promises. cc-pretty blocks have no
    ``_pi``; their enumeration index already matches ``.message.content[i]``.
    """
    return fmt_ref(lineno, _resolve_idx(block, enum_idx))


def _is_opencode_path(log_path: str) -> bool:
    return log_path.startswith(("opencode://", "opencode-file://"))


def recovery_cmd(log_path: str, lineno: int, block_idx: int | None, leaf: str) -> str:
    """Exact shell command printing the raw string behind a ref.

    ``block_idx`` is the source-true block/part index (see :func:`block_ref`);
    ``None`` means the leaf addresses the whole record (cc user string input,
    attachments). ``leaf`` is the jq path suffix appended after the block
    selector (e.g. ``.state.output``, ``.content``).
    """
    if log_path.startswith("opencode://"):
        sid = log_path[len("opencode://"):]
        f = f"/tmp/oc-{sid}.json"
        path = f".messages[{lineno - 1}].parts[{block_idx or 0}]{leaf}"
        return f"opencode export {sid} > {f} && jq -r '{path}' {f}"
    if log_path.startswith("opencode-file://"):
        src = log_path[len("opencode-file://"):]
        path = f".messages[{lineno - 1}].parts[{block_idx or 0}]{leaf}"
        return f"jq -r '{path}' {src}"
    if block_idx is None:
        return f"sed -n '{lineno}p' {log_path} | jq -r '{leaf}'"
    return (f"sed -n '{lineno}p' {log_path} | "
            f"jq -r '.message.content[{block_idx}]{leaf}'")


def legend_lines(log_path: str) -> list[str]:
    """The two hint lines documenting refs + recovery for this log source."""
    if log_path.startswith("opencode://"):
        sid = log_path[len("opencode://"):]
        return [
            "# refs @L<n>[i] = .messages[n-1].parts[i] (i=0 omitted) · "
            "leafs: reasoning/text/user .text · tool .state.input/.state.output",
            f"# recover: opencode export {sid} > /tmp/oc-{sid}.json "
            f"&& jq -r '.messages[<n-1>].parts[<i>]<leaf>' /tmp/oc-{sid}.json",
        ]
    if log_path.startswith("opencode-file://"):
        src = log_path[len("opencode-file://"):]
        return [
            "# refs @L<n>[i] = .messages[n-1].parts[i] (i=0 omitted) · "
            "leafs: reasoning/text/user .text · tool .state.input/.state.output",
            f"# recover: jq -r '.messages[<n-1>].parts[<i>]<leaf>' {src}",
        ]
    return [
        "# refs @L<n>[i] = line n, .message.content[i] (i=0 omitted) · "
        "leafs: thinking .thinking · text .text · ▶ .input · ◀ .content · "
        "user .message.content · attach .attachment.content",
        f"# recover: sed -n '<n>p' {log_path} | jq -r '<path>'",
    ]


def render_legend(log_path: str) -> str:
    """Two-line hint header documenting how to recover raw content behind refs.

    Printed once at the top of the full render (and reused as the skeleton
    header's recipe lines). ``opencode export`` truncates its stdout at ~64KB
    on a pipe, so the session recipe redirects to a file first — a bare
    ``opencode export ... | jq ...`` silently loses everything past the
    first pipe buffer.
    """
    return "\n".join(f"{C.HINT}{line}{C.RESET}" for line in legend_lines(log_path))


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
                 tool_input_max: int, show_thinking: bool = True,
                 show_usage: bool = False, chat_only: bool = False):
        self.log_path = log_path
        self.tool_output_max = tool_output_max
        self.tool_input_max = tool_input_max
        self.show_thinking = show_thinking
        # Per-turn usage block (`[in:.. out:.. cached:.. cache_create:..]`) is
        # ~26 tok per assistant turn and rarely relevant to a reader; opt-in
        # via --show-usage when debugging cache-hit or cost regressions.
        self.show_usage = show_usage
        # --chat-only: skip tool_use blocks inside assistant turns; turns
        # composed solely of tool_use blocks render as None and are dropped
        # by the caller.
        self.chat_only = chat_only
        self._tool_id_to_name: dict[str, str] = {}
        # Dedup state: repeat-suppress `⊞ output style: <s>` while value
        # is unchanged. The first occurrence is always emitted.
        self._last_output_style: str | None = None

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

        ref = fmt_ref(lineno, block_idx)
        lines = [f"{C.TOOL}  ▶ {block.name}{C.RESET}  {C.DIM}{ref}{C.RESET}"]
        lines.append(ind(trunc(inp_str, self.tool_input_max), "    "))
        return "\n".join(lines)

    def _render_tool_result(self, block: ToolResultBlock, lineno: int, block_idx: int,
                            tur: str | ToolUseResultDict | None = None) -> str:
        tool_name = self._tool_id_to_name.get(block.tool_use_id, "")
        name_suffix = f" ({tool_name})" if tool_name else ""

        label_color = C.ERROR if block.is_error else C.RESULT
        label = f"✗ error{name_suffix}" if block.is_error else f"◀ result{name_suffix}"

        content = block.content

        if isinstance(content, list):
            parts = []
            for sub in content:
                if sub.get("type") == "text":
                    t = sub.get("text", "")
                    parts.append(trunc(t, self.tool_output_max))
                else:
                    s = str(sub)
                    parts.append(trunc(s, self.tool_output_max))
            body = "\n".join(parts)
        else:
            body = trunc(content, self.tool_output_max)

        ref = fmt_ref(lineno, block_idx)
        lines = [
            f"{label_color}  {label}{C.RESET}  {C.DIM}{ref}{C.RESET}",
            ind(body, "    "),
        ]

        if isinstance(tur, ToolUseResultDict):
            if tur.stderr:
                lines.append(f"    {C.DIM}stderr: {trunc(tur.stderr, 100)}{C.RESET}")
        elif isinstance(tur, str) and tur:
            lines.append(f"    {C.DIM}{trunc(tur, 120)}{C.RESET}")

        return "\n".join(lines)

    def _render_context_text(self, text: str, lineno: int, block_idx: int) -> str:
        ref = fmt_ref(lineno, block_idx)
        return "\n".join([
            f"{C.RESULT}  ◀ context{C.RESET}  {C.DIM}{ref}{C.RESET}",
            ind(trunc(text, self.tool_output_max), "    "),
        ])

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

    def render_assistant_turn(
        self, records: list[tuple[AssistantRecord, int]], ts: str,
    ) -> str | None:
        usage: Usage | None = None
        model = ""

        for rec, _ in records:
            if rec.message.usage and not usage:
                usage = rec.message.usage
            if rec.message.model and not model:
                model = rec.message.model

        model_tag = ""
        if model == "<synthetic>":
            model_tag = f"  {C.DIM}[synthetic]{C.RESET}"
        elif model:
            model_tag = f"  {C.DIM}[{model}]{C.RESET}"

        # stop_reason is intentionally not surfaced — for stop:tool_use the
        # next ▶ line carries the same signal, and the other stop reasons
        # (refusal, max_tokens, pause_turn) show as visible body content
        # (refusal text, truncated output) anyway.
        header = f"{C.ASSISTANT}┌ Assistant{C.RESET}{model_tag}  {C.TIMESTAMP}{ts}{C.RESET}"
        if usage and self.show_usage:
            header += f"  {C.DIM}[{fmt_usage(usage)}]{C.RESET}"

        body: list[str] = []
        for rec, lineno in records:
            for bi, block in enumerate(rec.message.content_blocks()):
                if isinstance(block, ThinkingBlock):
                    if self.show_thinking:
                        body.append(self._render_thinking(block))
                    else:
                        body.append(f"{C.THINKING}  [thinking: {len(block.thinking)} chars]{C.RESET}")
                elif isinstance(block, TextBlock):
                    body.append(ind(block.text, "  "))
                elif isinstance(block, ToolUseBlock):
                    if self.chat_only:
                        continue
                    body.append(self._render_tool_use(block, lineno, bi))

        # Chat-only drops turns that produced no visible content (e.g. an
        # assistant turn composed solely of tool_use blocks).
        if self.chat_only and not body:
            return None

        return "\n".join([header, *body])

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

    def render_attachment(self, rec: AttachmentRecord, ts: str, lineno: int) -> str | None:
        """Render an attachment record.

        hook_additional_context gets a multi-line block (model-visible
        system-reminder text); other subtypes get one-line summaries.

        Returns None when the attachment is suppressed (e.g. an unchanged
        `output_style` repeat). Callers must guard their `print()` on the
        returned value.
        """
        a = rec.attachment
        atype = a.type
        ref = fmt_ref(lineno)

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
                f"{C.TIMESTAMP}{ts}{C.RESET}  "
                f"{C.DIM}{ref}{C.RESET}"
            )
            truncated_body = trunc(body, self.tool_output_max)
            return "\n".join([header, ind(truncated_body, "  ")])

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
            if a.style == self._last_output_style:
                return None
            self._last_output_style = a.style
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
        lines: list[str] = []
        if header_parts:
            lines.append(f"{C.DIM}{'  '.join(header_parts)}{C.RESET}")
        lines.append(render_legend(self.log_path))
        return "\n".join(lines)

    def render_rewind_marker(
        self, count: int, first_ts: str, last_ts: str,
        n_user: int, n_assistant: int, hidden: bool,
    ) -> str:
        time_range = f"{first_ts}\u2013{last_ts}" if first_ts != last_ts else first_ts
        turns = f"{n_user} user, {n_assistant} assistant"
        status = f"{count} records hidden" if hidden else f"{count} records shown above"
        return (
            f"{C.REWIND}\f⟲ rewind{C.RESET}\n"
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
        header = f"{C.SYSTEM}\f⟐ compacted{C.RESET}"
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

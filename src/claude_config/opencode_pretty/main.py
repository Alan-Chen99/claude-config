"""Pretty-print an opencode exported session."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from claude_config.cc_pretty.render import (
    C,
    fmt_duration,
    fmt_tool_input,
    ind,
    is_truncated,
    separator,
    trunc,
)


def opencode_hint(session_id: str, message_id: str) -> str:
    return (
        f"{C.HINT}    # agent-tools opencode-pretty {session_id} "
        f"--message {message_id} --full{C.RESET}"
    )


@dataclass(frozen=True)
class RenderOptions:
    tool_max: int = 4000
    truncate_input: bool = False
    no_color: bool = False
    show_thinking: bool = True


def parse_export_stdout(stdout: str) -> dict[str, Any]:
    """Parse opencode export stdout, ignoring status text before JSON."""
    start = stdout.find("{")
    if start == -1:
        raise ValueError("no JSON object found in opencode export output")
    try:
        value = json.loads(stdout[start:])
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in opencode export output: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("opencode export output was not a JSON object")
    return value


def fetch_export(session_id: str) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as stdout_file:
        proc = subprocess.run(
            ["opencode", "export", session_id],
            text=True,
            stdout=stdout_file,
            stderr=subprocess.PIPE,
            check=False,
        )
        stdout_file.seek(0)
        stdout = stdout_file.read()
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    try:
        return parse_export_stdout(stdout)
    except ValueError as exc:
        print(f"Failed to parse opencode export JSON: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def render_export(export: dict[str, Any], options: RenderOptions | None = None) -> str:
    options = options or RenderOptions()
    if options.no_color:
        C.disable()

    lines: list[str] = []
    info = _info(export)
    session_id = str(info.get("id") or info.get("sessionID") or export.get("id") or "")
    title = str(info.get("title") or export.get("title") or "")
    created = _format_time(_get_time(info, "created"))
    updated = _format_time(_get_time(info, "updated"))
    header = f"{C.BOLD}Session {session_id}{C.RESET}"
    if title:
        header += f"  {C.DIM}{title}{C.RESET}"
    metadata = _header_metadata(info)
    if metadata:
        header += f"  {C.DIM}{metadata}{C.RESET}"
    if created or updated:
        times = " -> ".join(t for t in (created, updated) if t)
        header += f"  {C.TIMESTAMP}{times}{C.RESET}"
    lines.append(header)
    lines.append(separator())

    for message in _messages(export):
        rendered = _render_message(message, options, session_id)
        if rendered:
            lines.append(rendered)
            lines.append(separator())

    return "\n".join(lines).rstrip() + "\n"


def emit_agent_output(output: str, session_id: str) -> None:
    """Print directly if output fits in Bash, otherwise write chunk files."""
    bash_limit = int(os.environ.get("BASH_MAX_OUTPUT_LENGTH", "30000")) * 4 // 5
    if len(output) <= bash_limit:
        sys.stdout.write(output)
        return

    read_max_tokens = int(os.environ.get("CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS", "25000"))
    chunk_chars = min(read_max_tokens * 2, 200_000)
    prefix = str(session_id)[:8] or "session"

    lines = output.split("\n")
    chunks: list[tuple[list[str], int]] = []
    current: list[str] = []
    current_size = 0
    chunk_start = 1
    for lineno, line in enumerate(lines, 1):
        line_len = len(line) + 1
        if current and current_size + line_len > chunk_chars:
            chunks.append((current, chunk_start))
            current = []
            current_size = 0
            chunk_start = lineno
        current.append(line)
        current_size += line_len
    if current:
        chunks.append((current, chunk_start))

    chunk_dir = Path(tempfile.mkdtemp(prefix=f"opencode-pretty-{prefix}-"))
    infos: list[tuple[Path, int, int, int]] = []
    for idx, (chunk_lines, start) in enumerate(chunks, 1):
        path = chunk_dir / f"chunk-{idx}.txt"
        content = "\n".join(chunk_lines)
        path.write_text(content)
        end = start + len(chunk_lines) - 1
        infos.append((path, len(content), start, end))

    print(f"Rendered {len(output):,} chars, {len(lines)} lines across {len(infos)} files.")
    print(f"Read all {len(infos)} files in parallel:")
    for path, chars, start, end in infos:
        print(f"  {path} ({chars:,} chars, lines {start}-{end})")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pretty-print an opencode exported session")
    parser.add_argument("session_id")
    parser.add_argument("--tool-max", type=int, default=4000)
    parser.add_argument("--truncate-input", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--no-thinking", action="store_true")
    parser.add_argument("--agent", action="store_true")
    args = parser.parse_args(argv)

    options = RenderOptions(
        tool_max=args.tool_max,
        truncate_input=args.truncate_input,
        no_color=args.no_color or args.agent,
        show_thinking=not args.no_thinking,
    )
    output = render_export(fetch_export(args.session_id), options)
    if args.agent:
        emit_agent_output(output, args.session_id)
    else:
        sys.stdout.write(output)


def _messages(export: dict[str, Any]) -> list[dict[str, Any]]:
    messages = export.get("messages") or export.get("message") or []
    if not isinstance(messages, list):
        return []
    return [msg for msg in messages if isinstance(msg, dict)]


def _render_message(message: dict[str, Any], options: RenderOptions, session_id: str) -> str:
    info = _info(message)
    role = str(info.get("role") or message.get("role") or message.get("type") or "message").upper()
    ts = _format_time(_get_time(info, "created"))
    color = C.USER if role == "USER" else C.ASSISTANT if role == "ASSISTANT" else C.SYSTEM
    header = f"{color}{role}{C.RESET}"
    if ts:
        header += f" {C.TIMESTAMP}{ts}{C.RESET}"
    body = _render_parts(_parts(message), options, session_id)
    return header if not body else f"{header}\n{body}"


def _parts(message: dict[str, Any]) -> list[dict[str, Any]]:
    parts = message.get("parts") or message.get("content") or []
    if isinstance(parts, str):
        return [{"type": "text", "text": parts}]
    if not isinstance(parts, list):
        return []
    return [part for part in parts if isinstance(part, dict)]


def _render_parts(parts: list[dict[str, Any]], options: RenderOptions, session_id: str) -> str:
    rendered: list[str] = []
    for part in parts:
        typ = part.get("type")
        if typ == "text":
            text = _part_text(part)
            if text:
                rendered.append(ind(text))
        elif typ in {"reasoning", "thinking"}:
            rendered.append(_render_reasoning(part, options))
        elif typ in {"tool", "tool-call", "tool_use"}:
            rendered.append(_render_tool(part, options, session_id))
        elif typ in {"step-start", "step-finish"}:
            continue
    return "\n".join(item for item in rendered if item)


def _render_reasoning(part: dict[str, Any], options: RenderOptions) -> str:
    text = _part_text(part)
    if not options.show_thinking:
        return f"{C.THINKING}  [reasoning hidden]{C.RESET}"
    if not text:
        return ""
    return f"{C.THINKING}  reasoning{C.RESET}\n{ind(text, '    ')}"


def _render_tool(part: dict[str, Any], options: RenderOptions, session_id: str) -> str:
    state = part.get("state") if isinstance(part.get("state"), dict) else {}
    name = str(part.get("name") or part.get("tool") or "tool")
    call_id = str(part.get("callID") or part.get("call_id") or part.get("id") or "")
    title = f"{C.TOOL}  ▶ {name}{C.RESET}"
    if call_id:
        title += f"  {C.DIM}({call_id}){C.RESET}"
    details = _tool_details(state)
    if details:
        title += f"  {C.DIM}{details}{C.RESET}"

    lines = [title]
    state_title = state.get("title")
    if state_title:
        lines.append(ind(str(state_title), "    "))
    if "input" in state or "input" in part:
        raw_input = fmt_tool_input(state.get("input", part.get("input")))
        input_text = trunc(raw_input, options.tool_max) if options.truncate_input else raw_input
        lines.append(ind(input_text, "    "))
        if options.truncate_input and is_truncated(raw_input, options.tool_max):
            lines.append(opencode_hint(session_id, part.get("id", "")))
    if state.get("status") == "error" and "error" in state:
        error = _stringify(state["error"])
        rendered_error = trunc(error, options.tool_max)
        lines.append(f"{C.ERROR}  ✗ error{C.RESET}")
        lines.append(ind(rendered_error, "    "))
        if is_truncated(error, options.tool_max):
            lines.append(f"{C.HINT}    [tool error truncated to {options.tool_max} chars]{C.RESET}")
            lines.append(opencode_hint(session_id, part.get("id", "")))
    elif "output" in state or "output" in part:
        output = _stringify(state.get("output", part.get("output")))
        rendered_output = trunc(output, options.tool_max)
        lines.append(f"{C.RESULT}  ◀ result{C.RESET}")
        lines.append(ind(rendered_output, "    "))
        if is_truncated(output, options.tool_max):
            lines.append(f"{C.HINT}    [tool output truncated to {options.tool_max} chars]{C.RESET}")
            lines.append(opencode_hint(session_id, part.get("id", "")))
    return "\n".join(lines)


def _part_text(part: dict[str, Any]) -> str:
    value = part.get("text", part.get("content", ""))
    return _stringify(value)


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, indent=2, sort_keys=True)


def _get_time(obj: dict[str, Any], key: str) -> Any:
    time_obj = obj.get("time")
    if isinstance(time_obj, dict) and key in time_obj:
        return time_obj[key]
    return obj.get(key) or obj.get("timestamp")


def _info(obj: dict[str, Any]) -> dict[str, Any]:
    info = obj.get("info")
    return info if isinstance(info, dict) else obj


def _tool_details(state: dict[str, Any]) -> str:
    parts: list[str] = []
    status = state.get("status")
    if status:
        parts.append(str(status))
    time_obj = state.get("time")
    if isinstance(time_obj, dict):
        start = time_obj.get("start")
        end = time_obj.get("end")
        if isinstance(start, int | float) and isinstance(end, int | float):
            parts.append(fmt_duration(end - start))
    return " ".join(parts)


def _header_metadata(info: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("slug", "version", "directory", "cwd"):
        value = info.get(key)
        if value:
            parts.append(str(value))
    model_info = info.get("model") if isinstance(info.get("model"), dict) else {}
    provider = model_info.get("providerID") or info.get("providerID") or info.get("provider")
    model = model_info.get("id") or info.get("modelID") or info.get("model")
    variant = model_info.get("variant") or info.get("variant")
    if provider and model:
        model_text = f"{provider}/{model}"
    elif provider or model:
        model_text = str(provider or model)
    else:
        model_text = ""
    if model_text and variant:
        model_text += f"/{variant}"
    if model_text:
        parts.append(model_text)
    return "  ".join(parts)


def _format_time(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, int | float):
        seconds = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(seconds, UTC).strftime("%H:%M:%S")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%H:%M:%S")
        except ValueError:
            return value
    return str(value)


if __name__ == "__main__":
    main()

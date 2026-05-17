"""Pretty-print one MITM intercept log file.

Usage: cc-pretty-intercept <file.json>
                            [--tool-max N] [--truncate-input]
                            [--no-color] [--no-thinking]
                            [--no-system] [--no-tools]

One intercept file = one captured API request/response pair. Operates on the
output of scripts/intercept/proxy.py, stored at
~/.claude/requests-log/<session_id>/NNNN.json.
"""

from __future__ import annotations

import argparse
import os
import sys

from claude_config.cc_pretty.parse import (
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    parse_content_block,
)
from claude_config.cc_pretty.render import (
    C,
    Renderer,
    fmt_duration,
    fmt_ts,
    fmt_usage,
    ind,
    separator,
    trunc,
)
from claude_config.cc_pretty_intercept.parse import (
    InterceptLog,
    Message,
    Response,
    SystemTextItem,
    load_intercept,
)


def _render_header(log: InterceptLog, path: str) -> str:
    parts = [f"intercept: {os.path.basename(path)}"]
    if log.request.model:
        parts.append(log.request.model)
    parts.append("streaming" if log.streaming else "non-stream")
    if log.timestamp:
        parts.append(fmt_ts(log.timestamp))
    if log.duration_ms:
        parts.append(f"dur:{fmt_duration(log.duration_ms)}")

    lines = [f"{C.DIM}{'  '.join(parts)}{C.RESET}"]

    if log.session:
        sess_parts = []
        if log.session.cwd:
            sess_parts.append(f"cwd:{log.session.cwd}")
        if log.session.session_id:
            sess_parts.append(f"id:{log.session.session_id[:8]}")
        if log.session.kind:
            sess_parts.append(log.session.kind)
        if log.session.entrypoint:
            sess_parts.append(log.session.entrypoint)
        if log.session.pid:
            sess_parts.append(f"pid:{log.session.pid}")
        if sess_parts:
            lines.append(f"{C.DIM}  {'  '.join(sess_parts)}{C.RESET}")

    req_parts = []
    if log.request.max_tokens is not None:
        req_parts.append(f"max_tokens:{log.request.max_tokens}")
    if log.request.temperature is not None:
        req_parts.append(f"temp:{log.request.temperature}")
    if log.request.thinking:
        budget = log.request.thinking.get("budget_tokens")
        req_parts.append(
            f"thinking:{budget}" if budget else f"thinking:{log.request.thinking.get('type', '?')}"
        )
    if log.request.output_config:
        req_parts.append("output_config")
    if req_parts:
        lines.append(f"{C.DIM}  {'  '.join(req_parts)}{C.RESET}")

    return "\n".join(lines)


def _render_tools(tools: list[dict], tool_input_max: int) -> str:
    names = [t.get("name", "?") for t in tools]
    lines = [
        f"{C.TOOL}┌ Tools ({len(tools)}){C.RESET}",
        ind(trunc(", ".join(names), tool_input_max), "  "),
    ]
    return "\n".join(lines)


def _render_system(system: str | list[SystemTextItem], tool_output_max: int) -> str:
    lines = [f"{C.SYSTEM}┌ System{C.RESET}"]

    if isinstance(system, str):
        lines.append(ind(trunc(system, tool_output_max), "  "))
        return "\n".join(lines)

    for idx, item in enumerate(system):
        tags = []
        if item.cache_control:
            cc = item.cache_control
            tag = cc.type or "ephemeral"
            if cc.ttl:
                tag += f"/{cc.ttl}"
            if cc.scope:
                tag += f"/{cc.scope}"
            tags.append(f"cache:{tag}")
        suffix = f"  {C.DIM}[{' '.join(tags)}]{C.RESET}" if tags else ""
        lines.append(f"{C.DIM}  [{idx + 1}/{len(system)}]{C.RESET}{suffix}")
        lines.append(ind(trunc(item.text, tool_output_max), "    "))
    return "\n".join(lines)


def _render_message(
    msg: Message, idx: int, total: int, renderer: Renderer, lineno: int = 1
) -> str:
    role_color = C.USER if msg.role == "user" else C.ASSISTANT
    head = f"{role_color}┌ Message {idx + 1}/{total}: {msg.role}{C.RESET}"

    if isinstance(msg.content, str):
        return f"{head}\n{ind(msg.content, '  ')}"

    lines = [head]
    for bi, raw in enumerate(msg.content):
        block = parse_content_block(raw)
        if isinstance(block, ThinkingBlock):
            if renderer.show_thinking:
                lines.append(renderer._render_thinking(block))
            else:
                lines.append(
                    f"{C.THINKING}  [thinking: {len(block.thinking)} chars]{C.RESET}"
                )
        elif isinstance(block, TextBlock):
            lines.append(ind(trunc(block.text, renderer.tool_output_max), "  "))
        elif isinstance(block, ToolUseBlock):
            lines.append(renderer._render_tool_use(block, lineno, bi))
        elif isinstance(block, ToolResultBlock):
            lines.append(renderer._render_tool_result(block, lineno, bi))
        else:
            lines.append(f"{C.DIM}  [unknown block: {block.type}]{C.RESET}")
    return "\n".join(lines)


def _render_response(resp: Response, renderer: Renderer) -> str:
    head_parts = [f"{C.ASSISTANT}┌ Response{C.RESET}"]
    if resp.model:
        head_parts.append(f"{C.DIM}[{resp.model}]{C.RESET}")
    if resp.stop_reason:
        head_parts.append(f"{C.DIM}stop:{resp.stop_reason}{C.RESET}")
    if resp.usage:
        head_parts.append(f"{C.DIM}[{fmt_usage(resp.usage)}]{C.RESET}")
    lines = ["  ".join(head_parts)]

    if resp.error:
        lines.append(f"{C.ERROR}  ✗ error [{resp.error.type}]: {resp.error.message}{C.RESET}")

    for bi, raw in enumerate(resp.content):
        block = parse_content_block(raw)
        if isinstance(block, ThinkingBlock):
            if renderer.show_thinking:
                lines.append(renderer._render_thinking(block))
            else:
                lines.append(
                    f"{C.THINKING}  [thinking: {len(block.thinking)} chars]{C.RESET}"
                )
        elif isinstance(block, TextBlock):
            lines.append(ind(block.text, "  "))
        elif isinstance(block, ToolUseBlock):
            lines.append(renderer._render_tool_use(block, 1, bi))
        else:
            lines.append(f"{C.DIM}  [unknown block: {block.type}]{C.RESET}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Pretty-print one MITM intercept log file",
    )
    parser.add_argument("file", help="Path to intercept .json file")
    parser.add_argument(
        "--tool-max", type=int, default=2000,
        help="Max chars for tool output / system text bodies (default: 2000). "
             "Tool input is shown in full unless --truncate-input is set.",
    )
    parser.add_argument(
        "--truncate-input", action="store_true",
        help="Also truncate tool input to --tool-max chars",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument(
        "--no-thinking", action="store_true",
        help="Collapse thinking blocks to single-line summary",
    )
    parser.add_argument(
        "--no-system", action="store_true",
        help="Hide system prompt parts",
    )
    parser.add_argument(
        "--no-tools", action="store_true",
        help="Hide tool definitions list",
    )
    args = parser.parse_args()

    if args.no_color:
        C.disable()

    log = load_intercept(args.file)

    tool_input_max = args.tool_max if args.truncate_input else sys.maxsize
    renderer = Renderer(
        args.file,
        tool_output_max=args.tool_max,
        tool_input_max=tool_input_max,
        show_thinking=not args.no_thinking,
    )

    print(_render_header(log, args.file))

    if not args.no_tools and log.request.tools:
        print(separator())
        print(_render_tools(log.request.tools, tool_input_max))

    has_system = log.request.system if isinstance(log.request.system, str) else len(log.request.system) > 0
    if not args.no_system and has_system:
        print(separator())
        print(_render_system(log.request.system, args.tool_max))

    for idx, msg in enumerate(log.request.messages):
        print(separator())
        print(_render_message(msg, idx, len(log.request.messages), renderer))

    print(separator())
    print(_render_response(log.response, renderer))
    print(separator())


if __name__ == "__main__":
    main()

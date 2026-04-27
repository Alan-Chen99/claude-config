#!/home/chenxy/repos/claude-config/.venv/bin/python3
"""Pretty-print a Claude Code JSONL session log to stdout.

Usage: cc-pretty.py <session.jsonl> [--tool-max N] [--no-color] [--no-progress] [--no-thinking]
"""

from __future__ import annotations

import argparse
import sys

from cc_pretty_parse import (
    AssistantRecord,
    FileHistorySnapshotRecord,
    LastPromptRecord,
    ProgressRecord,
    QueueOperationRecord,
    SystemRecord,
    UserRecord,
    read_jsonl,
    parse_all,
)
from cc_pretty_render import C, Renderer, fmt_ts, separator


def is_user_input(rec: UserRecord) -> bool:
    return isinstance(rec.message.content, str)


def main():
    parser = argparse.ArgumentParser(description="Pretty-print Claude Code JSONL session logs")
    parser.add_argument("file", help="Path to .jsonl session file")
    parser.add_argument("--tool-max", type=int, default=200,
                        help="Max chars for tool input/output (default: 200)")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument("--no-progress", action="store_true",
                        help="Hide progress records (bash/agent/hook streaming)")
    parser.add_argument("--no-thinking", action="store_true",
                        help="Collapse thinking blocks to single-line summary")
    parser.add_argument("--validate-only", action="store_true",
                        help="Parse all records through pydantic schema without rendering; exit 1 on errors")
    args = parser.parse_args()

    if args.no_color:
        C.disable()

    raw_records = read_jsonl(args.file)
    records, errors = parse_all(raw_records)

    if args.validate_only:
        total = len(raw_records)
        ok = total - errors
        print(f"{ok}/{total} records parsed OK, {errors} errors", file=sys.stderr)
        sys.exit(1 if errors else 0)

    r = Renderer(args.file, args.tool_max, show_thinking=not args.no_thinking)

    if records:
        header = r.render_session_header(records[0][0])
        if header:
            print(header)

    i = 0
    while i < len(records):
        rec, lineno = records[i]
        ts = fmt_ts(getattr(rec, "timestamp", ""))

        if isinstance(rec, AssistantRecord):
            group: list[tuple[AssistantRecord, int]] = [(rec, lineno)]
            j = i + 1
            while j < len(records) and isinstance(records[j][0], AssistantRecord):
                group.append(records[j])  # type: ignore
                j += 1
            print(separator())
            print(r.render_assistant_turn(group, ts))
            i = j

        elif isinstance(rec, UserRecord):
            if is_user_input(rec):
                ugroup: list[tuple[UserRecord, int]] = [(rec, lineno)]
                j = i + 1
                while j < len(records) and isinstance(records[j][0], UserRecord) and is_user_input(records[j][0]):
                    ugroup.append(records[j])  # type: ignore
                    j += 1
                print(separator())
                print(r.render_user_input(ugroup, ts))
                i = j
            else:
                tgroup: list[tuple[UserRecord, int]] = [(rec, lineno)]
                j = i + 1
                while j < len(records) and isinstance(records[j][0], UserRecord) and not is_user_input(records[j][0]):
                    tgroup.append(records[j])  # type: ignore
                    j += 1
                print(separator())
                print(r.render_tool_output(tgroup, ts))
                i = j

        elif isinstance(rec, SystemRecord):
            print(separator())
            print(r.render_system(rec, ts))
            i += 1

        elif isinstance(rec, ProgressRecord):
            if not args.no_progress:
                print(r.render_progress(rec, ts))
            i += 1

        elif isinstance(rec, FileHistorySnapshotRecord):
            print(r.render_file_snapshot(rec))
            i += 1

        elif isinstance(rec, LastPromptRecord):
            print(r.render_last_prompt(rec))
            i += 1

        elif isinstance(rec, QueueOperationRecord):
            print(r.render_queue_op(rec))
            i += 1

        else:
            print(f"{C.DIM}  [unknown record: {rec.type}]{C.RESET}")
            i += 1

    print(separator())


if __name__ == "__main__":
    main()

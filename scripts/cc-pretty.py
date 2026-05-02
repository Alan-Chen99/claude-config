#!/home/chenxy/repos/claude-config/.venv/bin/python3
"""Pretty-print a Claude Code JSONL session log to stdout.

Usage: cc-pretty.py <session.jsonl> [--tool-max N] [--truncate-input]
                                    [--no-color] [--no-thinking]
                                    [--show-rewound] [--show-all]
                                    [--agent]

By default, rewound conversation branches are collapsed to a single marker,
and records not presented to the model (hooks, progress, system metadata)
are hidden.
"""

from __future__ import annotations

import argparse
import io
import os
import sys

from cc_pretty_parse import (
    AssistantRecord,
    FileHistorySnapshotRecord,
    LastPromptRecord,
    ProgressRecord,
    QueueOperationRecord,
    Record,
    SystemRecord,
    UserRecord,
    read_jsonl,
    parse_all,
)
from cc_pretty_render import C, Renderer, fmt_ts, separator


# ─── Helpers ─────────────────────────────────────────────────────────────────


def is_user_input(rec: UserRecord) -> bool:
    return isinstance(rec.message.content, str)


def is_model_visible(rec: Record) -> bool:
    """True if this record type is sent to the model (normalizeMessagesForAPI).

    user and assistant messages are always sent. system messages only when
    subtype is local_command.  Everything else (progress, file-history-snapshot,
    queue-operation, last-prompt, hooks, turn_duration, etc.) is filtered out
    before the API call.
    """
    if isinstance(rec, (AssistantRecord, UserRecord)):
        return True
    if isinstance(rec, SystemRecord) and rec.subtype == "local_command":
        return True
    return False


# ─── Rewind detection via parentUuid chain ───────────────────────────────────

def _is_chain_record(rec: Record) -> bool:
    """True if this record carries parentUuid (participates in the chain).

    Transcript messages (user/assistant/system) always have parentUuid in
    modern logs.  Legacy logs also include progress records in the chain.
    We check model_fields_set to distinguish "parentUuid present but null"
    (chain root) from "parentUuid absent" (metadata record).
    """
    return "parentUuid" in rec.model_fields_set


def find_rewound_indices(
    records: list[tuple[Record, int]],
) -> set[int] | None:
    """Find record indices on dead rewind branches.

    Rewind creates a fork: a parent record gets 2+ children.  The child on the
    active chain (reachable from the last record) is kept; children on dead
    branches and all their descendants are "rewound".

    Context compaction also breaks the chain (parentUuid=null) but does NOT
    create forks, so compaction-orphaned records are NOT marked as rewound.

    Returns set of rewound indices, or None if no rewinds detected.
    """
    uuid_to_idx: dict[str, int] = {}
    idx_to_uuid: dict[int, str] = {}
    last_chain_idx: int | None = None
    parent_to_children: dict[str, list[int]] = {}

    for i, (rec, _) in enumerate(records):
        if not _is_chain_record(rec):
            continue
        uid = getattr(rec, "uuid", "") or ""
        if uid:
            uuid_to_idx[uid] = i
            idx_to_uuid[i] = uid
        last_chain_idx = i
        parent = getattr(rec, "parentUuid", None)
        if parent:
            parent_to_children.setdefault(parent, []).append(i)

    if last_chain_idx is None:
        return None

    # Real forks have 2+ non-progress children.  Legacy progress records
    # share the same parentUuid as the next user record, creating false
    # forks that are not rewinds.
    def _non_progress_children(kids: list[int]) -> list[int]:
        return [k for k in kids if not isinstance(records[k][0], ProgressRecord)]

    if not any(len(_non_progress_children(kids)) > 1
               for kids in parent_to_children.values()):
        return None

    # Walk active chain from last record to root
    active: set[int] = set()
    idx: int | None = last_chain_idx
    while idx is not None:
        active.add(idx)
        parent = getattr(records[idx][0], "parentUuid", None)
        if parent:
            idx = uuid_to_idx.get(parent)
        else:
            break

    # Mark dead fork branches and all their descendants
    rewound: set[int] = set()
    for children in parent_to_children.values():
        if len(_non_progress_children(children)) < 2:
            continue
        for child_idx in children:
            if child_idx in active:
                continue
            # BFS from dead child through all descendants
            stack = [child_idx]
            while stack:
                ci = stack.pop()
                if ci in rewound:
                    continue
                rewound.add(ci)
                uid = idx_to_uuid.get(ci, "")
                if uid in parent_to_children:
                    stack.extend(parent_to_children[uid])

    return rewound if rewound else None


def find_rewind_blocks(
    records: list[tuple[Record, int]],
    rewound: set[int],
) -> list[tuple[int, int]]:
    """Find contiguous blocks of rewound records.

    Non-chain records (metadata, progress) sandwiched between rewound chain
    records are absorbed into the block.
    Returns [(start_idx, end_idx), ...].
    """
    blocks: list[tuple[int, int]] = []
    in_block = False
    block_start = 0

    for i, (rec, _) in enumerate(records):
        if i in rewound:
            if not in_block:
                block_start = i
                in_block = True
        elif _is_chain_record(rec):
            if in_block:
                blocks.append((block_start, i))
                in_block = False

    if in_block:
        blocks.append((block_start, len(records)))

    return blocks


def build_rewind_info(
    records: list[tuple[Record, int]],
    rewound: set[int] | None,
    hide_rewound: bool,
) -> tuple[dict[int, dict], set[int], set[int]]:
    """Build rewind markers, hidden indices, and boundary indices.

    Returns (rewind_markers, hidden_indices, rewind_boundaries) where
    rewind_boundaries contains both start and end indices of each block
    to prevent record-grouping loops from crossing rewind edges.
    """
    rewind_markers: dict[int, dict] = {}
    hidden_indices: set[int] = set()
    rewind_boundaries: set[int] = set()

    if rewound is None:
        return rewind_markers, hidden_indices, rewind_boundaries

    blocks = find_rewind_blocks(records, rewound)
    if not blocks:
        return rewind_markers, hidden_indices, rewind_boundaries

    for start, end in blocks:
        if hide_rewound:
            hidden_indices.update(range(start, end))
        rewind_boundaries.add(start)
        rewind_boundaries.add(end)

        first_ts = fmt_ts(getattr(records[start][0], "timestamp", ""))
        last_ts = fmt_ts(getattr(records[end - 1][0], "timestamp", ""))
        n_user = sum(
            1
            for i in range(start, end)
            if isinstance(records[i][0], UserRecord)
            and is_user_input(records[i][0])
        )
        n_assistant = sum(
            1
            for i in range(start, end)
            if isinstance(records[i][0], AssistantRecord)
        )
        rewind_markers[end] = {
            "count": end - start,
            "first_ts": first_ts,
            "last_ts": last_ts,
            "n_user": n_user,
            "n_assistant": n_assistant,
            "hidden": hide_rewound,
        }

    return rewind_markers, hidden_indices, rewind_boundaries


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Pretty-print Claude Code JSONL session logs",
    )
    parser.add_argument("file", help="Path to .jsonl session file")
    parser.add_argument(
        "--tool-max",
        type=int,
        default=200,
        help="Max chars for tool output (default: 200). "
        "Tool input is shown in full unless --truncate-input is set.",
    )
    parser.add_argument(
        "--truncate-input",
        action="store_true",
        help="Also truncate tool input to --tool-max chars (full by default)",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Hide progress records when --show-all is used",
    )
    parser.add_argument(
        "--no-thinking",
        action="store_true",
        help="Collapse thinking blocks to single-line summary",
    )
    parser.add_argument(
        "--show-rewound",
        action="store_true",
        help="Show rewound conversation branches (hidden by default)",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all records including non-model content "
        "(hooks, progress, system metadata)",
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Agent-friendly output: if small enough, print directly; "
        "otherwise write chunk files to /tmp and print paths for parallel reads. "
        "Implies --no-color.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Parse all records through pydantic schema without rendering; "
        "exit 1 on errors",
    )
    args = parser.parse_args()

    if args.no_color or args.agent:
        C.disable()

    raw_records = read_jsonl(args.file)
    records, errors = parse_all(raw_records)

    if args.validate_only:
        total = len(raw_records)
        ok = total - errors
        print(f"{ok}/{total} records parsed OK, {errors} errors", file=sys.stderr)
        sys.exit(1 if errors else 0)

    tool_input_max = args.tool_max if args.truncate_input else sys.maxsize
    r = Renderer(
        args.file,
        tool_output_max=args.tool_max,
        tool_input_max=tool_input_max,
        show_thinking=not args.no_thinking,
    )

    # In agent mode, capture stdout so we can split if needed
    saved_stdout = None
    if args.agent:
        saved_stdout = sys.stdout
        sys.stdout = io.StringIO()

    # ── Rewind detection ────────────────────────────────────────────────
    rewound = find_rewound_indices(records)
    rewind_markers, hidden_for_rewind, rewind_boundaries = build_rewind_info(
        records, rewound, hide_rewound=not args.show_rewound,
    )

    # ── Session header (first visible record) ───────────────────────────
    if records:
        first_rec = records[0][0]
        for idx, (rec, _) in enumerate(records):
            if idx not in hidden_for_rewind:
                first_rec = rec
                break
        header = r.render_session_header(first_rec)
        if header:
            print(header)

    # ── Render records ──────────────────────────────────────────────────
    i = 0
    while i < len(records):
        # Rewind marker at block boundary
        if i in rewind_markers:
            print(separator())
            print(r.render_rewind_marker(**rewind_markers[i]))

        # Skip rewound records
        if i in hidden_for_rewind:
            i += 1
            continue

        rec, lineno = records[i]

        # Hide non-model content unless --show-all
        if not args.show_all and not is_model_visible(rec):
            i += 1
            continue

        ts = fmt_ts(getattr(rec, "timestamp", ""))

        if isinstance(rec, AssistantRecord):
            group: list[tuple[AssistantRecord, int]] = [(rec, lineno)]
            j = i + 1
            while (
                j < len(records)
                and j not in hidden_for_rewind
                and j not in rewind_boundaries
                and isinstance(records[j][0], AssistantRecord)
            ):
                group.append(records[j])  # type: ignore
                j += 1
            print(separator())
            print(r.render_assistant_turn(group, ts))
            i = j

        elif isinstance(rec, UserRecord):
            if is_user_input(rec):
                ugroup: list[tuple[UserRecord, int]] = [(rec, lineno)]
                j = i + 1
                while (
                    j < len(records)
                    and j not in hidden_for_rewind
                    and j not in rewind_boundaries
                    and isinstance(records[j][0], UserRecord)
                    and is_user_input(records[j][0])
                ):
                    ugroup.append(records[j])  # type: ignore
                    j += 1
                print(separator())
                print(r.render_user_input(ugroup, ts))
                i = j
            else:
                tgroup: list[tuple[UserRecord, int]] = [(rec, lineno)]
                j = i + 1
                while (
                    j < len(records)
                    and j not in hidden_for_rewind
                    and j not in rewind_boundaries
                    and isinstance(records[j][0], UserRecord)
                    and not is_user_input(records[j][0])
                ):
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

    if args.agent:
        output = sys.stdout.getvalue()
        sys.stdout = saved_stdout
        _emit_agent_output(output, args.file)


def _emit_agent_output(output: str, file_path: str) -> None:
    """Print directly if output fits in Bash, otherwise write chunk files."""
    bash_limit = int(os.environ.get('BASH_MAX_OUTPUT_LENGTH', '30000')) * 4 // 5
    if len(output) <= bash_limit:
        sys.stdout.write(output)
        return

    read_max_tokens = int(os.environ.get(
        'CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS', '25000'))
    # 3 chars/token conservative; cap at 200K chars to stay under 256KB file size limit
    chunk_chars = min(read_max_tokens * 3, 200_000)

    lines = output.split('\n')
    chunks: list[tuple[list[str], int]] = []  # (lines, start_lineno)
    current: list[str] = []
    current_size = 0
    chunk_start = 1

    for lineno, line in enumerate(lines, 1):
        line_len = len(line) + 1
        if current_size + line_len > chunk_chars and current:
            chunks.append((current, chunk_start))
            current = []
            current_size = 0
            chunk_start = lineno
        current.append(line)
        current_size += line_len
    if current:
        chunks.append((current, chunk_start))

    session_id = os.path.basename(file_path).replace('.jsonl', '')[:8]
    infos: list[tuple[str, int, int, int]] = []
    for i, (chunk_lines, start) in enumerate(chunks, 1):
        path = f'/tmp/cc-pretty-{session_id}-{i}.txt'
        content = '\n'.join(chunk_lines)
        with open(path, 'w') as f:
            f.write(content)
        end = start + len(chunk_lines) - 1
        infos.append((path, len(content), start, end))

    n = len(infos)
    print(f"Rendered {len(output):,} chars, {len(lines)} lines across {n} files.")
    print(f"Read all {n} files in parallel:")
    for path, chars, start, end in infos:
        print(f"  {path} ({chars:,} chars, lines {start}-{end})")


if __name__ == "__main__":
    main()

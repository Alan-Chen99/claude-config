"""Pretty-print a Claude Code JSONL session log to stdout.

Usage: cc-pretty <session.jsonl> [--tool-max N] [--truncate-input]
                                 [--no-color] [--no-thinking]
                                 [--show-rewound] [--show-all]
                                 [--chat-only]
                                 [--compact-all] [--compact-leg N]
                                 [--agent]

By default, only the last leg (after the last compaction boundary) is shown.
Rewound conversation branches are collapsed to a single marker, and records
not presented to the model (raw hook execution, progress, system metadata,
permission-mode state) are hidden.  Model-visible attachment records — most
importantly hook_additional_context, which carries the <system-reminder> text
emitted by SessionStart / PostToolUse / etc. hooks — are shown by default.
Use --show-all to surface the bookkeeping records as well.

This module also exposes :func:`add_shared_args` and :func:`run_pipeline` so
other front-ends (e.g. opencode-pretty) can wire the same CLI surface and
rendering loop on top of a different data source.
"""

from __future__ import annotations

import argparse
import io
import os
import sys
from dataclasses import dataclass

from claude_config.cc_pretty.parse import (
    AssistantRecord,
    AttachmentRecord,
    FileHistorySnapshotRecord,
    LastPromptRecord,
    PermissionModeRecord,
    ProgressRecord,
    QueueOperationRecord,
    Record,
    SystemRecord,
    UserRecord,
    read_jsonl,
    parse_all,
)
from claude_config.cc_pretty.render import C, Renderer, fmt_ts, separator


# Attachment subtypes whose content reaches the model (system-reminder text,
# task/skill listings, output style, etc.).  Subtypes outside this set are
# bookkeeping (raw hook execution, internal permission state) and stay hidden
# unless --show-all is set.
_MODEL_VISIBLE_ATTACHMENT_TYPES = frozenset({
    "hook_additional_context",
    "task_reminder",
    "skill_listing",
    "output_style",
    "deferred_tools_delta",
    "ultrathink_effort",
    "date_change",
    "queued_command",
    "compact_file_reference",
    "edited_text_file",
    "file",
    "nested_memory",
})


# ─── Helpers ─────────────────────────────────────────────────────────────────


def is_user_input(rec: UserRecord) -> bool:
    return isinstance(rec.message.content, str)


def is_chat_visible(rec: Record) -> bool:
    """True if rec is a user prompt or an assistant message.

    Used by --chat-only to drop tool-call/result traffic, system records,
    attachments, progress, etc. — leaving only the human-readable
    user↔assistant exchange. Assistant turns that contain only tool_use
    blocks are filtered later in the renderer (returns None).
    """
    if isinstance(rec, AssistantRecord):
        return True
    if isinstance(rec, UserRecord) and is_user_input(rec):
        return True
    return False


def is_model_visible(rec: Record) -> bool:
    """True if this record contributes to the model's view of the conversation.

    user and assistant messages are always sent.  system messages only when
    subtype is local_command.  attachment records whose subtype reaches the
    model (see _MODEL_VISIBLE_ATTACHMENT_TYPES) are sent — most notably
    hook_additional_context, which carries the <system-reminder> text emitted
    by SessionStart / PostToolUse / etc. hooks.  Bookkeeping records (progress,
    file-history-snapshot, queue-operation, last-prompt, permission-mode,
    raw hook_success, turn_duration, etc.) are filtered out before the API
    call.
    """
    if isinstance(rec, (AssistantRecord, UserRecord)):
        return True
    if isinstance(rec, SystemRecord) and rec.subtype == "local_command":
        return True
    if isinstance(rec, AttachmentRecord) and rec.attachment.type in _MODEL_VISIBLE_ATTACHMENT_TYPES:
        return True
    return False


# ─── Compaction detection ──────────────────────────────────────────────────────


def find_compaction_boundaries(
    records: list[tuple[Record, int]],
) -> list[dict]:
    """Find indices where context compaction occurred.

    Detects two compaction formats:
      1. Legacy: a chain record's parentUuid points to a UUID not stored in
         the JSONL (synthetic summary message).
      2. Modern: an explicit system record with subtype "compact_boundary",
         parentUuid=null, and compactMetadata.

    Returns a list of boundary dicts with section metadata.
    """
    uuid_set: set[str] = set()
    chain_records: list[tuple[int, Record]] = []

    for i, (rec, _) in enumerate(records):
        if not _is_chain_record(rec):
            continue
        uid = getattr(rec, "uuid", "") or ""
        if uid:
            uuid_set.add(uid)
        chain_records.append((i, rec))

    if not chain_records:
        return []

    # Method 1 (legacy): chain record whose parentUuid is not in uuid_set
    boundaries: list[int] = []
    for i, rec in chain_records:
        parent = getattr(rec, "parentUuid", None)
        if parent and parent not in uuid_set:
            boundaries.append(i)

    # Method 2 (modern): explicit compact_boundary system records
    for i, (rec, _) in enumerate(records):
        if (isinstance(rec, SystemRecord)
                and rec.subtype == "compact_boundary"
                and i not in boundaries):
            boundaries.append(i)

    boundaries.sort()

    if not boundaries:
        return []

    # Build section info: each section runs from a boundary (or start) to the
    # next boundary (or end).  Extract token counts from first assistant usage.
    section_starts = [0] + boundaries
    section_ends = boundaries + [len(records)]

    results: list[dict] = []
    for bi, boundary_idx in enumerate(boundaries):
        prev_start = section_starts[bi]
        prev_end = boundary_idx

        # Summarize the section that was compacted away
        prev_records = [records[j][0] for j in range(prev_start, prev_end)]
        first_ts = ""
        last_ts = ""
        for rec in prev_records:
            ts = getattr(rec, "timestamp", "")
            if ts and not first_ts:
                first_ts = ts
            if ts:
                last_ts = ts

        n_assistant = sum(1 for r in prev_records if isinstance(r, AssistantRecord))
        n_user_input = sum(
            1 for r in prev_records
            if isinstance(r, UserRecord) and is_user_input(r)
        )

        # Token count: prefer compactMetadata.preTokens (modern format),
        # fall back to last assistant usage in the compacted section
        last_tokens = 0
        boundary_rec = records[boundary_idx][0]
        compact_meta = getattr(boundary_rec, "compactMetadata", None)
        if compact_meta is None and hasattr(boundary_rec, "__pydantic_extra__"):
            compact_meta = (boundary_rec.__pydantic_extra__ or {}).get("compactMetadata")
        if isinstance(compact_meta, dict) and compact_meta.get("preTokens"):
            last_tokens = compact_meta["preTokens"]
        else:
            for r in reversed(prev_records):
                if isinstance(r, AssistantRecord) and r.message.usage:
                    u = r.message.usage
                    last_tokens = (
                        u.input_tokens + u.cache_read_input_tokens
                        + u.cache_creation_input_tokens
                    )
                    break

        # Token count: first assistant usage in the NEW section (after compact)
        new_tokens = 0
        for j in range(boundary_idx, min(boundary_idx + 10, len(records))):
            rec = records[j][0]
            if isinstance(rec, AssistantRecord) and rec.message.usage:
                u = rec.message.usage
                new_tokens = (
                    u.input_tokens + u.cache_read_input_tokens
                    + u.cache_creation_input_tokens
                )
                break

        results.append({
            "idx": boundary_idx,
            "section_num": bi + 1,
            "prev_records": prev_end - prev_start,
            "prev_first_ts": fmt_ts(first_ts),
            "prev_last_ts": fmt_ts(last_ts),
            "prev_n_user": n_user_input,
            "prev_n_assistant": n_assistant,
            "tokens_before": last_tokens,
            "tokens_after": new_tokens,
        })

    return results


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

    Context compaction breaks the chain (parentUuid points to a synthetic
    summary message not stored in JSONL).  Forks within compaction-orphaned
    sections (e.g. parallel tool calls) are ignored because no sibling is on
    the active chain — only forks where at least one child IS active count.

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

    # Build message.id index for assistant records — used to detect parallel
    # tool calls (split normalized records from the same API response).
    idx_to_mid: dict[int, str] = {}
    for i, (rec, _) in enumerate(records):
        if isinstance(rec, AssistantRecord) and rec.message.id:
            idx_to_mid[i] = rec.message.id

    # Real forks have 2+ children that represent distinct conversation
    # branches — i.e. divergent user inputs or assistant responses.  Only
    # UserRecord and AssistantRecord can be branches; other chain records
    # (AttachmentRecord for hooks/skills/styles, SystemRecord for slash-command
    # output, ProgressRecord for legacy chains) are sibling annotations that
    # share a parent with the next chain step without representing a fork.
    # Additional filter: normalized split siblings (parallel tool calls from
    # the same API response) share message.id with the parent; not rewinds.
    def _real_fork_children(parent_uuid: str, kids: list[int]) -> list[int]:
        # Find the parent record's message.id (if it's an assistant record)
        parent_mid = None
        parent_idx = uuid_to_idx.get(parent_uuid)
        if parent_idx is not None:
            parent_mid = idx_to_mid.get(parent_idx)

        real: list[int] = []
        for k in kids:
            rec = records[k][0]
            if not isinstance(rec, (UserRecord, AssistantRecord)):
                continue
            # Child assistant record from the same API response as parent
            # is just the next normalized split block, not a real branch
            if parent_mid and idx_to_mid.get(k) == parent_mid:
                continue
            real.append(k)
        return real

    if not any(len(_real_fork_children(p, kids)) > 1
               for p, kids in parent_to_children.items()):
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

    # Mark dead fork branches and all their descendants.
    # A fork is only a rewind if at least one sibling IS on the active chain.
    # Forks where ALL children are off the active chain (e.g. parallel tool
    # calls in a section orphaned by context compaction) are not rewinds.
    rewound: set[int] = set()
    for parent_uid, children in parent_to_children.items():
        real_kids = _real_fork_children(parent_uid, children)
        if len(real_kids) < 2:
            continue
        if not any(k in active for k in real_kids):
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


# ─── Shared CLI surface ──────────────────────────────────────────────────────


def add_shared_args(parser: argparse.ArgumentParser, *, default_tool_max: int = 200) -> None:
    """Attach the cc-pretty / opencode-pretty shared options to ``parser``.

    Front-ends still own the positional argument(s) that point at the data
    source (a JSONL path for cc-pretty, a session ID for opencode-pretty),
    but the rendering controls and leg/rewind filters are identical so they
    live here. ``default_tool_max`` lets front-ends pick a different default
    truncation budget without redefining the argument.
    """
    parser.add_argument(
        "--tool-max",
        type=int,
        default=default_tool_max,
        help=f"Max chars for tool output (default: {default_tool_max}). "
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
        "--show-usage",
        action="store_true",
        help="Show per-turn usage block "
        "(in/out/cached/cache_create tokens). Hidden by default — opt in "
        "when debugging cache-hit rates or cost regressions.",
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
        "--chat-only",
        action="store_true",
        help="Show only user prompts and assistant messages — drop tool "
        "calls, tool results, system records, and attachments. Assistant "
        "turns that contain only tool_use blocks are skipped entirely.",
    )
    parser.add_argument(
        "--compact-all",
        action="store_true",
        help="Show all compaction legs (default: only last leg)",
    )
    parser.add_argument(
        "--compact-leg",
        type=int,
        default=None,
        metavar="N",
        help="Show only compaction leg N (1-indexed; 0 = pre-compact section)",
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
        "exit 1 on errors (cc-pretty only — opencode-pretty validates eagerly).",
    )


@dataclass(frozen=True)
class PipelineInput:
    """Inputs to :func:`run_pipeline`.

    ``records``: pre-parsed records keyed by a synthetic line/index number.
    ``log_path``: shown in the legend at the top so readers know what to grep.
    ``args``: the argparse Namespace populated by :func:`add_shared_args`.
    ``agent_chunk_prefix``: filename stem for ``--agent`` chunk files.
    ``rewound``: pre-computed rewound indices. When set (even to an empty
        set), the parent-fork auto-detector is skipped — the caller is
        asserting it already knows what's rewound. opencode-pretty does this
        because opencode messages legitimately share parents (multiple
        assistant steps under one user prompt), which the auto-detector
        would flag as a fork.
    """

    records: list[tuple[Record, int]]
    log_path: str
    args: argparse.Namespace
    agent_chunk_prefix: str = "cc-pretty"
    rewound: set[int] | None = None


def run_pipeline(inp: PipelineInput) -> None:
    """Render ``inp.records`` through the shared Renderer to stdout.

    Both cc-pretty and opencode-pretty call this after producing a list of
    pydantic Records from their respective data source. All filtering
    (compaction legs, rewinds, --chat-only, --show-all) and grouping
    (consecutive AssistantRecords, contiguous tool-result UserRecords) lives
    here so the two front-ends stay in sync.
    """
    args = inp.args
    records = inp.records

    if args.no_color or args.agent:
        C.disable()

    tool_input_max = args.tool_max if args.truncate_input else sys.maxsize
    r = Renderer(
        inp.log_path,
        tool_output_max=args.tool_max,
        tool_input_max=tool_input_max,
        show_thinking=not args.no_thinking,
        show_usage=args.show_usage,
        chat_only=args.chat_only,
    )

    saved_stdout = None
    if args.agent:
        saved_stdout = sys.stdout
        sys.stdout = io.StringIO()

    # ── Compaction & rewind detection ────────────────────────────────────
    compaction_bounds = find_compaction_boundaries(records)
    compaction_markers: dict[int, dict] = {
        cb["idx"]: cb for cb in compaction_bounds
    }

    compact_hidden: set[int] = set()
    if compaction_bounds and not args.compact_all and args.compact_leg is None:
        last_boundary = compaction_bounds[-1]["idx"]
        compact_hidden = set(range(0, last_boundary))
    elif args.compact_leg is not None:
        leg = args.compact_leg
        boundary_indices = [cb["idx"] for cb in compaction_bounds]
        leg_starts = [0] + boundary_indices
        leg_ends = boundary_indices + [len(records)]
        if 0 <= leg < len(leg_starts):
            show_start = leg_starts[leg]
            show_end = leg_ends[leg]
            compact_hidden = (
                set(range(0, show_start)) | set(range(show_end, len(records)))
            )
        else:
            print(
                f"Error: --compact-leg {leg} out of range "
                f"(0-{len(leg_starts) - 1})",
                file=sys.stderr,
            )
            sys.exit(1)

    # If the caller supplied a rewound set, trust it; the parent-fork
    # auto-detector would mis-flag opencode's shared-parent assistant chain
    # (many steps under one user prompt) as forks otherwise.
    if inp.rewound is not None:
        rewound: set[int] | None = inp.rewound or None
    else:
        rewound = find_rewound_indices(records)
    rewind_markers, hidden_for_rewind, rewind_boundaries = build_rewind_info(
        records, rewound, hide_rewound=not args.show_rewound,
    )

    # ── Session header (first visible record) ───────────────────────────
    if records:
        first_rec = records[0][0]
        for idx, (rec, _) in enumerate(records):
            if idx not in hidden_for_rewind and idx not in compact_hidden:
                first_rec = rec
                break
        header = r.render_session_header(first_rec)
        if header:
            print(header)

    # ── Render records ──────────────────────────────────────────────────
    i = 0
    while i < len(records):
        if i in compaction_markers:
            cb = compaction_markers[i]
            print(separator())
            print(r.render_compaction_marker(
                section_num=cb["section_num"],
                prev_records=cb["prev_records"],
                prev_first_ts=cb["prev_first_ts"],
                prev_last_ts=cb["prev_last_ts"],
                prev_n_user=cb["prev_n_user"],
                prev_n_assistant=cb["prev_n_assistant"],
                tokens_before=cb["tokens_before"],
                tokens_after=cb["tokens_after"],
            ))

        if i in rewind_markers:
            print(separator())
            print(r.render_rewind_marker(**rewind_markers[i]))

        if i in compact_hidden:
            i += 1
            continue
        if i in hidden_for_rewind:
            i += 1
            continue

        rec, lineno = records[i]

        if not args.show_all and not is_model_visible(rec):
            i += 1
            continue
        if args.chat_only and not is_chat_visible(rec):
            i += 1
            continue

        ts = fmt_ts(getattr(rec, "timestamp", ""))

        if isinstance(rec, AssistantRecord):
            group: list[tuple[AssistantRecord, int]] = [(rec, lineno)]
            j = i + 1
            while (
                j < len(records)
                and j not in hidden_for_rewind
                and j not in compact_hidden
                and j not in rewind_boundaries
                and j not in compaction_markers
                and isinstance(records[j][0], AssistantRecord)
            ):
                group.append(records[j])  # type: ignore
                j += 1
            rendered = r.render_assistant_turn(group, ts)
            if rendered is not None:
                print(separator())
                print(rendered)
            i = j

        elif isinstance(rec, UserRecord):
            if is_user_input(rec):
                ugroup: list[tuple[UserRecord, int]] = [(rec, lineno)]
                j = i + 1
                while (
                    j < len(records)
                    and j not in hidden_for_rewind
                    and j not in compact_hidden
                    and j not in rewind_boundaries
                    and j not in compaction_markers
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
                    and j not in compact_hidden
                    and j not in rewind_boundaries
                    and j not in compaction_markers
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

        elif isinstance(rec, AttachmentRecord):
            rendered = r.render_attachment(rec, ts, lineno)
            if rendered is not None:
                if rec.attachment.type == "hook_additional_context":
                    print(separator())
                print(rendered)
            i += 1

        elif isinstance(rec, PermissionModeRecord):
            print(r.render_permission_mode(rec))
            i += 1

        else:
            print(f"{C.DIM}  [unknown record: {rec.type}]{C.RESET}")
            i += 1

    # A rewind block that runs to the end of the record stream has its
    # marker keyed at i == len(records), which the main loop never
    # iterates over. Flush it here. (Compaction boundaries never sit at
    # len(records) — there's always at least the boundary record itself
    # past that index — so they don't need the same flush.)
    tail = len(records)
    if tail in rewind_markers:
        print(separator())
        print(r.render_rewind_marker(**rewind_markers[tail]))

    print(separator())

    if args.agent:
        output = sys.stdout.getvalue()
        sys.stdout = saved_stdout
        emit_agent_output(output, inp.agent_chunk_prefix)


def emit_agent_output(output: str, chunk_prefix: str) -> None:
    """Print directly if output fits in Bash, otherwise write chunk files.

    ``chunk_prefix`` is the filename stem used for /tmp/<prefix>-N.txt chunks
    so cc-pretty and opencode-pretty produce distinguishable artifacts.
    """
    bash_limit = int(os.environ.get('BASH_MAX_OUTPUT_LENGTH', '30000')) * 4 // 5
    if len(output) <= bash_limit:
        sys.stdout.write(output)
        return

    read_max_tokens = int(os.environ.get(
        'CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS', '25000'))
    # 2 chars/token: rendered logs contain JSON tool input which tokenizes densely.
    # Also cap at 200K chars to stay under Read tool's 256KB file size limit.
    chunk_chars = min(read_max_tokens * 2, 200_000)

    lines = output.split('\n')
    chunks: list[tuple[list[str], int]] = []
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

    infos: list[tuple[str, int, int, int]] = []
    for i, (chunk_lines, start) in enumerate(chunks, 1):
        path = f'/tmp/{chunk_prefix}-{i}.txt'
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


# ─── cc-pretty entry point ───────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Pretty-print Claude Code JSONL session logs",
    )
    parser.add_argument("file", help="Path to .jsonl session file")
    add_shared_args(parser, default_tool_max=200)
    args = parser.parse_args()

    raw_records = read_jsonl(args.file)
    records, errors = parse_all(raw_records)

    if args.validate_only:
        total = len(raw_records)
        ok = total - errors
        print(f"{ok}/{total} records parsed OK, {errors} errors", file=sys.stderr)
        sys.exit(1 if errors else 0)

    session_id = os.path.basename(args.file).replace('.jsonl', '')[:8]
    run_pipeline(PipelineInput(
        records=records,
        log_path=args.file,
        args=args,
        agent_chunk_prefix=f"cc-pretty-{session_id}",
    ))


if __name__ == "__main__":
    main()

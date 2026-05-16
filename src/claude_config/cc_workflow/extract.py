#!/usr/bin/env python3
"""Extract sub-agent workflow summary from a Claude Code JSONL session log.

Tier 1 extraction: main-log-only, zero compliance dependency.
Parses Agent tool_use / tool_result pairs to produce:
  - Per-agent summary table (description, type, tokens, tools, duration, status)
  - Structural anomaly detection (API errors, token=0, high tool counts, missing results)
  - Aggregate workflow statistics

Tier 2 drill-down: sub-agent JSONL analysis for investigating anomalies.
Discovers sub-agent files at <session-dir>/subagents/agent-<agentId>.jsonl and
extracts: internal tool sequence, file coverage, retry patterns, error timeline.

Usage:
  cc_workflow_extract.py <session.jsonl> [--json] [--anomalies-only] [--verbose]
  cc_workflow_extract.py <session.jsonl> --tier2 [all|anomalies|<index>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentRecord:
    """Paired data from an Agent tool_use + its tool_result."""

    tool_use_id: str
    description: str
    subagent_type: str
    prompt_len: int
    model: str | None = None
    run_in_background: bool = False
    isolation: str | None = None

    # From tool_result (populated when matched)
    status: str | None = None
    agent_id: str | None = None
    total_tokens: int = 0
    total_tool_use_count: int = 0
    total_duration_ms: int = 0
    content_text: str = ""
    content_length: int = 0
    is_error: bool = False
    error_text: str = ""

    # Anomalies detected
    anomalies: list[str] = field(default_factory=list)

    @property
    def duration_s(self) -> float:
        return self.total_duration_ms / 1000.0

    @property
    def succeeded(self) -> bool:
        return self.status == "completed" and not self.is_error and self.total_tokens > 0


def extract_agents(jsonl_path: str) -> tuple[list[AgentRecord], dict]:
    """Parse JSONL and return (agent_records, session_meta)."""

    # Phase 1: collect Agent tool_use blocks and their tool_use_ids
    pending: dict[str, AgentRecord] = {}  # tool_use_id -> AgentRecord
    # Track which assistant message each agent was dispatched in (for batch detection)
    dispatch_groups: dict[str, list[str]] = {}  # msg_index -> [tool_use_ids]
    session_meta: dict = {"file": jsonl_path, "total_lines": 0}

    with open(jsonl_path) as f:
        lines = f.readlines()

    session_meta["total_lines"] = len(lines)
    assistant_msg_idx = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue

        if rec.get("type") == "assistant":
            # Extract session metadata from first assistant record
            if "sessionId" not in session_meta:
                session_meta["sessionId"] = rec.get("sessionId", "")
                session_meta["cwd"] = rec.get("cwd", "")
                session_meta["timestamp_start"] = rec.get("timestamp", "")

            msg = rec.get("message", {})
            msg_key = str(assistant_msg_idx)
            assistant_msg_idx += 1
            agents_in_msg: list[str] = []
            for block in msg.get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use" and block.get("name") == "Agent":
                    inp = block.get("input", {})
                    agent = AgentRecord(
                        tool_use_id=block.get("id", ""),
                        description=inp.get("description", ""),
                        subagent_type=inp.get("subagent_type", "general-purpose"),
                        prompt_len=len(inp.get("prompt", "")),
                        model=inp.get("model"),
                        run_in_background=inp.get("run_in_background", False),
                        isolation=inp.get("isolation"),
                    )
                    pending[agent.tool_use_id] = agent
                    agents_in_msg.append(agent.tool_use_id)
            if agents_in_msg:
                dispatch_groups[msg_key] = agents_in_msg

        elif rec.get("type") == "user":
            tur = rec.get("toolUseResult")

            # Match via tool_result blocks in message.content
            msg = rec.get("message", {})
            content_blocks = msg.get("content", [])
            if isinstance(content_blocks, list):
                for block in content_blocks:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_result":
                        continue
                    bid = block.get("tool_use_id", "")
                    if bid not in pending:
                        continue

                    agent = pending[bid]

                    # toolUseResult (top-level) has the agent metrics
                    if tur and isinstance(tur, dict) and "agentId" in tur:
                        agent.status = tur.get("status")
                        agent.agent_id = tur.get("agentId")
                        agent.total_tokens = tur.get("totalTokens", 0)
                        agent.total_tool_use_count = tur.get("totalToolUseCount", 0)
                        agent.total_duration_ms = tur.get("totalDurationMs", 0)

                        content = tur.get("content", [])
                        if isinstance(content, list):
                            texts = []
                            for c in content:
                                if isinstance(c, dict) and c.get("type") == "text":
                                    texts.append(c.get("text", ""))
                            agent.content_text = "\n".join(texts)
                        elif isinstance(content, str):
                            agent.content_text = content
                    else:
                        # Fallback: use tool_result block content directly
                        bc = block.get("content", "")
                        if isinstance(bc, str):
                            agent.content_text = bc
                        elif isinstance(bc, list):
                            texts = [c.get("text", "") for c in bc if isinstance(c, dict)]
                            agent.content_text = "\n".join(texts)
                        agent.status = "error" if block.get("is_error", False) else "completed"

                    agent.content_length = len(agent.content_text)
                    agent.is_error = block.get("is_error", False)

                    # Detect API errors in content
                    if "API Error" in agent.content_text or "api_error" in agent.content_text:
                        agent.is_error = True
                    if agent.is_error:
                        agent.error_text = agent.content_text[:200]

    # Detect anomalies
    agents = list(pending.values())
    for agent in agents:
        if agent.status is None:
            agent.anomalies.append("MISSING_RESULT: no tool_result matched")
        elif agent.is_error:
            agent.anomalies.append(f"ERROR: {agent.error_text[:200]}")
        elif agent.total_tokens == 0:
            # Zero tokens without explicit error — unusual
            agent.anomalies.append("ZERO_TOKENS: completed with 0 tokens")
        # Typical agents use <20 tools; >40 indicates retries or scope creep (calibrated across 40+ real sessions)
        if agent.total_tool_use_count > 40:
            agent.anomalies.append(f"HIGH_TOOL_COUNT: {agent.total_tool_use_count} tool uses (possible retries)")
        # 5-minute threshold; calibrated from session observations — most agents complete in <2 min
        if agent.total_duration_ms > 300_000:
            agent.anomalies.append(f"LONG_RUNNING: {agent.duration_s:.0f}s")

    # Compute dispatch batches: groups of agents dispatched in the same assistant message
    batches = []
    for _msg_key, tool_ids in sorted(dispatch_groups.items(), key=lambda x: int(x[0])):
        if len(tool_ids) > 1:
            batch_agents = [pending[tid] for tid in tool_ids if tid in pending]
            if len(batch_agents) > 1:
                batches.append(batch_agents)
    session_meta["dispatch_batches"] = batches

    return agents, session_meta


@dataclass
class ToolCall:
    """A single tool invocation inside a sub-agent."""

    name: str
    target: str  # File path, search pattern, or command (display-friendly)
    dedup_key: str = ""  # Specific key for repeat detection (includes offset, full hash, etc.)
    is_error: bool = False
    error_text: str = ""
    expected_error: bool = False  # Known benign non-zero exit (diff exit 1, grep no-match)


@dataclass
class AgentDrillDown:
    """Tier 2 analysis of a sub-agent's internal JSONL."""

    agent_id: str
    description: str
    file_path: str | None  # Path to sub-agent JSONL, None if not found
    record_count: int = 0
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_counts: dict[str, int] = field(default_factory=dict)
    files_touched: set[str] = field(default_factory=set)
    retries: list[tuple[str, str, int]] = field(default_factory=list)  # (tool, target, count)
    api_errors: list[str] = field(default_factory=list)
    last_tool_before_error: ToolCall | None = None


def _extract_tool_target(name: str, inp: dict) -> str:
    """Extract the primary target from a tool's input."""
    if name == "Read":
        return inp.get("file_path", "")
    if name == "Grep":
        pattern = inp.get("pattern", "")[:40]
        path = inp.get("path", "")
        return f"pattern={pattern}" + (f" path={path}" if path else "")
    if name == "Glob":
        return inp.get("pattern", "")
    if name in ("Edit", "Write"):
        return inp.get("file_path", "")
    if name == "Bash":
        return inp.get("command", "")[:80]
    if name == "Agent":
        return inp.get("description", "")[:60]
    # WebFetch, WebSearch, etc.
    return str(inp)[:60] if inp else ""


def _extract_dedup_key(name: str, inp: dict) -> str:
    """Extract a specific key that distinguishes semantically different operations.

    More specific than _extract_tool_target: includes offset/limit for Read,
    full command hash for Bash, and path for Grep/Glob — so paginated reads,
    fan-out scans, and distinct commands with shared prefixes are not false-matched.
    """
    if name == "Read":
        fp = inp.get("file_path", "")
        offset = inp.get("offset", "")
        limit = inp.get("limit", "")
        # Paginated reads of the same file at different offsets are distinct operations
        return f"{fp}|offset={offset}|limit={limit}"
    if name == "Bash":
        cmd = inp.get("command", "")
        # Hash full command to avoid 80-char truncation collisions
        return hashlib.md5(cmd.encode()).hexdigest()[:16]
    if name == "Grep":
        pattern = inp.get("pattern", "")[:40]
        path = inp.get("path", "")
        glob_p = inp.get("glob", "")
        return f"pattern={pattern}|path={path}|glob={glob_p}"
    if name == "Glob":
        pattern = inp.get("pattern", "")
        path = inp.get("path", "")
        return f"{pattern}|path={path}"
    # Edit, Write, Agent, etc. — same as display target
    return _extract_tool_target(name, inp)


_EXPECTED_EXIT1_PREFIXES = ("diff ", "diff\t", "grep ", "grep\t", "rg ", "rg\t")


def _error_looks_like_diff_output(error_text: str) -> bool:
    """Check if error text looks like diff output (expected for diff exit 1).

    Catches cases where the diff command is beyond the 80-char target truncation
    (e.g., pipelines: git show ... | diff -).
    """
    lines = error_text.split("\n")
    diff_markers = 0
    for line in lines[:10]:
        stripped = line.strip()
        if stripped.startswith(("< ", "> ", "---", "+++", "@@")):
            diff_markers += 1
        # Standard diff header like "102c102", "278d277", "1,3c1,4"
        if stripped and all(c in "0123456789,acd" for c in stripped) and any(c in "acd" for c in stripped):
            diff_markers += 1
    return diff_markers >= 2


def _is_expected_nonzero_exit(tc: "ToolCall") -> bool:
    """Detect Bash errors that are expected non-zero exits, not real failures.

    diff returns exit 1 when differences are found (expected).
    grep/rg return exit 1 when no matches are found (expected).
    Handles compound commands (cd X && diff ...) by checking all segments.
    """
    if tc.name != "Bash" or not tc.is_error:
        return False
    if "exit code 1" not in tc.error_text.lower():
        return False
    # Split compound commands on && ; | to find individual command segments
    cmd_text = tc.target
    for sep in ("&&", ";", "|"):
        cmd_text = cmd_text.replace(sep, "\n")
    for segment in cmd_text.split("\n"):
        segment = segment.strip()
        if segment.startswith(_EXPECTED_EXIT1_PREFIXES):
            return True
    # Fallback: error text looks like diff output (catches truncated pipelines)
    if _error_looks_like_diff_output(tc.error_text):
        return True
    return False


def _discover_subagent_path(jsonl_path: str, agent_id: str) -> Path | None:
    """Find sub-agent JSONL file from session JSONL path and agent ID."""
    session_dir = Path(jsonl_path).with_suffix("")
    subagent_file = session_dir / "subagents" / f"agent-{agent_id}.jsonl"
    return subagent_file if subagent_file.exists() else None


def drill_down_agent(agent: AgentRecord, jsonl_path: str) -> AgentDrillDown:
    """Parse a sub-agent's internal JSONL to extract tool patterns."""
    dd = AgentDrillDown(
        agent_id=agent.agent_id or "",
        description=agent.description,
        file_path=None,
    )

    if not agent.agent_id:
        return dd

    subagent_path = _discover_subagent_path(jsonl_path, agent.agent_id)
    if subagent_path is None:
        return dd

    dd.file_path = str(subagent_path)

    with open(subagent_path) as f:
        lines = f.readlines()

    dd.record_count = len(lines)

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue

        if rec.get("type") == "assistant":
            msg = rec.get("message", {})
            for block in msg.get("content", []):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    name = block.get("name", "")
                    inp = block.get("input", {})
                    target = _extract_tool_target(name, inp)
                    dkey = _extract_dedup_key(name, inp)
                    dd.tool_calls.append(ToolCall(name=name, target=target, dedup_key=dkey))
                elif block.get("type") == "text":
                    text = block.get("text", "")
                    if "API Error" in text or "api_error" in text:
                        dd.api_errors.append(text[:200])

        elif rec.get("type") == "user":
            msg = rec.get("message", {})
            for block in msg.get("content", []):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_result" and block.get("is_error"):
                    content = block.get("content", "")
                    err_text = content[:200] if isinstance(content, str) else str(content)[:200]
                    if dd.tool_calls:
                        dd.tool_calls[-1].is_error = True
                        dd.tool_calls[-1].error_text = err_text
                        dd.tool_calls[-1].expected_error = _is_expected_nonzero_exit(dd.tool_calls[-1])

    # Compute derived fields
    dd.tool_counts = dict(Counter(tc.name for tc in dd.tool_calls))
    dd.files_touched = set()
    for tc in dd.tool_calls:
        if tc.name in ("Read", "Edit", "Write"):
            if tc.target and "/tool-results/" not in tc.target:
                dd.files_touched.add(tc.target)

    # Detect repeated operations using dedup_key for accuracy.
    # dedup_key includes offset/limit for Read, full command hash for Bash,
    # and path for Grep/Glob — so paginated reads, fan-out scans, and distinct
    # commands with shared prefixes are not false-matched.
    dedup_groups: dict[tuple[str, str], list[ToolCall]] = {}
    for tc in dd.tool_calls:
        key = (tc.name, tc.dedup_key)
        dedup_groups.setdefault(key, []).append(tc)
    dd.retries = [
        (name, tcs[0].target, len(tcs))
        for (name, _dkey), tcs in sorted(dedup_groups.items(), key=lambda x: -len(x[1]))
        if len(tcs) > 1
    ]

    # Track last tool before API error
    if dd.api_errors and dd.tool_calls:
        for i in range(len(dd.tool_calls) - 1, -1, -1):
            if not dd.tool_calls[i].is_error:
                dd.last_tool_before_error = dd.tool_calls[i]
                break

    return dd


def format_drill_down(
    agents: list[AgentRecord],
    drill_downs: list[AgentDrillDown],
    session_meta: dict,
    all_agents: list[AgentRecord] | None = None,
) -> str:
    """Format Tier 2 drill-down report."""
    index_source = all_agents if all_agents is not None else agents
    lines = []
    sid = session_meta.get("sessionId", "?")[:8]
    lines.append(f"TIER 2 DRILL-DOWN: Session {sid}")
    lines.append("=" * 60)

    for agent, dd in zip(agents, drill_downs):
        lines.append("")
        idx = index_source.index(agent) + 1
        status = "OK" if agent.succeeded else ("ERROR" if agent.is_error else (agent.status or "?"))
        lines.append(f"--- Agent #{idx}: {agent.description} [{status}] ---")

        if dd.file_path is None:
            lines.append("  Sub-agent JSONL: not found")
            if not agent.agent_id:
                lines.append("  (no agent_id — likely user-rejected or missing result)")
            lines.append("")
            continue

        lines.append(f"  Sub-agent JSONL: {dd.file_path}")
        lines.append(f"  Records: {dd.record_count}  |  Tool calls: {len(dd.tool_calls)}")

        # Tool breakdown
        if dd.tool_counts:
            counts_str = ", ".join(
                f"{name}: {count}" for name, count in
                sorted(dd.tool_counts.items(), key=lambda x: -x[1])
            )
            lines.append(f"  Tool breakdown: {counts_str}")

        # Bash commands preview
        bash_commands = [tc for tc in dd.tool_calls if tc.name == "Bash"]
        if bash_commands:
            lines.append(f"  Bash commands ({len(bash_commands)}):")
            for tc in bash_commands[:5]:
                lines.append(f"    $ {tc.target}")
            if len(bash_commands) > 5:
                lines.append(f"    ... and {len(bash_commands) - 5} more")

        # Files touched
        if dd.files_touched:
            lines.append(f"  Files touched ({len(dd.files_touched)}):")
            for fp in sorted(dd.files_touched):
                lines.append(f"    {fp}")

        # Repeated operations (only true repeats, not paginated reads or fan-out scans)
        if dd.retries:
            lines.append(f"  Repeated operations ({len(dd.retries)} repeated pairs):")
            for name, target, count in dd.retries[:5]:  # Top 5
                lines.append(f"    {name} {target[:60]} ({count}x)")

        # API errors
        if dd.api_errors:
            lines.append(f"  API errors ({len(dd.api_errors)}):")
            for err in dd.api_errors:
                lines.append(f"    {err[:120]}")

        # Separate real failures from expected non-zero exits
        real_errors = [tc for tc in dd.tool_calls if tc.is_error and not tc.expected_error]
        expected_errors = [tc for tc in dd.tool_calls if tc.is_error and tc.expected_error]
        if real_errors:
            lines.append(f"  Failed tool calls ({len(real_errors)}):")
            for tc in real_errors[:5]:
                lines.append(f"    {tc.name} {tc.target[:50]}: {tc.error_text[:80]}")
        if expected_errors:
            lines.append(f"  Expected non-zero exits ({len(expected_errors)}):")
            for tc in expected_errors[:3]:
                lines.append(f"    {tc.name} {tc.target[:50]}: exit 1 (normal for diff/grep)")

        # Progress assessment for failed agents
        if not agent.succeeded and dd.tool_calls:
            total = len(dd.tool_calls)
            errors = len(real_errors)
            lines.append(f"  Progress: {total} tool calls made, {errors} failed")
            if dd.api_errors:
                lines.append(f"  Agent completed {total} tool calls before API error — work was partially done")
            if dd.last_tool_before_error:
                tc = dd.last_tool_before_error
                lines.append(f"  Last successful tool: {tc.name} {tc.target[:60]}")

        lines.append("")

    return "\n".join(lines)


def format_drill_down_json(
    agents: list[AgentRecord],
    drill_downs: list[AgentDrillDown],
    all_agents: list[AgentRecord] | None = None,
) -> list[dict]:
    """Format Tier 2 drill-down as JSON-serializable dicts."""
    index_source = all_agents if all_agents is not None else agents
    results = []
    for agent, dd in zip(agents, drill_downs):
        results.append({
            "agent_index": index_source.index(agent) + 1,
            "agent_id": agent.agent_id,
            "description": agent.description,
            "subagent_file": dd.file_path,
            "record_count": dd.record_count,
            "tool_call_count": len(dd.tool_calls),
            "tool_breakdown": dd.tool_counts,
            "files_touched": sorted(dd.files_touched),
            "retries": [
                {"tool": name, "target": target, "count": count}
                for name, target, count in dd.retries
            ],
            "api_errors": dd.api_errors,
            "failed_tool_calls": [
                {"tool": tc.name, "target": tc.target, "error": tc.error_text}
                for tc in dd.tool_calls if tc.is_error and not tc.expected_error
            ],
            "bash_commands": [
                tc.target for tc in dd.tool_calls if tc.name == "Bash"
            ],
            "expected_nonzero_exits": [
                {"tool": tc.name, "target": tc.target}
                for tc in dd.tool_calls if tc.is_error and tc.expected_error
            ],
        })
    return results


def _extract_content_summary(text: str, max_len: int = 120) -> str:
    """Extract a meaningful summary line, skipping preamble.

    Agent outputs often start with preamble ("Now I have a complete picture.
    Here is my review.") followed by --- and then the actual structured content.
    This function skips those to find the first informative line: a markdown
    heading, XML tag, or substantial content line.
    """
    content_lines = text.strip().split("\n")

    # First pass: look for a markdown heading or XML tag
    for line in content_lines:
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        # Markdown heading — usually the actual title
        if stripped.startswith("#"):
            return stripped[:max_len]
        # XML tag — structured output (e.g., <smell_report ...>)
        if stripped.startswith("<") and not stripped.startswith("<!"):
            return stripped[:max_len]

    # Fallback: first non-empty line (original behavior)
    return content_lines[0].strip()[:max_len]


def format_table(agents: list[AgentRecord], session_meta: dict) -> str:
    """Format agents into a human-readable summary."""
    lines = []

    sid = session_meta.get("sessionId", "?")[:8]
    lines.append(f"Session: {sid}  ({session_meta.get('file', '?')})")
    lines.append(f"Agents: {len(agents)}  |  "
                 f"Succeeded: {sum(1 for a in agents if a.succeeded)}  |  "
                 f"Failed: {sum(1 for a in agents if not a.succeeded)}")

    if agents:
        total_tokens = sum(a.total_tokens for a in agents)
        total_tools = sum(a.total_tool_use_count for a in agents)
        total_dur = sum(a.total_duration_ms for a in agents)
        lines.append(f"Total tokens: {total_tokens:,}  |  "
                     f"Total tool uses: {total_tools}  |  "
                     f"Total duration: {total_dur / 1000:.0f}s")

    lines.append("")

    # Table header
    lines.append(f"{'#':>2}  {'Description':<40}  {'Type':<16}  {'Tokens':>8}  {'Tools':>5}  {'Dur(s)':>7}  {'Status':<10}")
    lines.append("-" * 100)

    for i, a in enumerate(agents, 1):
        desc = a.description[:40]
        status = "OK" if a.succeeded else ("ERROR" if a.is_error else (a.status or "?"))
        # Show "N/A" for tokens when agent did work (tool calls > 0) but recorded 0 tokens
        # API-errored agents complete tool calls before dying but report 0 tokens
        if a.total_tokens == 0 and a.total_tool_use_count > 0:
            tokens_str = f"{'N/A':>8}"
        else:
            tokens_str = f"{a.total_tokens:>8,}"
        lines.append(
            f"{i:>2}  {desc:<40}  {a.subagent_type:<16}  "
            f"{tokens_str}  {a.total_tool_use_count:>5}  "
            f"{a.duration_s:>7.1f}  {status:<10}"
        )

    # Anomalies section
    anomaly_agents = [a for a in agents if a.anomalies]
    if anomaly_agents:
        lines.append("")
        lines.append("ANOMALIES:")
        for a in anomaly_agents:
            for anom in a.anomalies:
                lines.append(f"  [{a.description[:30]}] {anom}")

    # Dispatch batches (agents dispatched in the same assistant turn = concurrent)
    batches = session_meta.get("dispatch_batches", [])
    if batches:
        lines.append("")
        lines.append("DISPATCH BATCHES (concurrent):")
        for batch_idx, batch in enumerate(batches, 1):
            agent_nums = []
            for ba in batch:
                try:
                    agent_nums.append(str(agents.index(ba) + 1))
                except ValueError:
                    pass
            if agent_nums:
                lines.append(f"  Batch {batch_idx}: agents {', '.join(agent_nums)} ({len(agent_nums)} concurrent)")
            else:
                # All agents in this batch were filtered out (e.g., --anomalies-only)
                lines.append(f"  Batch {batch_idx}: ({len(batch)} agents, none shown in filtered view)")

    # Content summaries (meaningful line from each agent's output)
    lines.append("")
    lines.append("AGENT OUTPUT SUMMARIES:")
    for i, a in enumerate(agents, 1):
        if a.content_text and not a.is_error:
            summary = _extract_content_summary(a.content_text)
            lines.append(f"  {i}. {summary}")
        elif a.is_error:
            lines.append(f"  {i}. [ERROR] {a.error_text[:100]}")
        else:
            lines.append(f"  {i}. [no output]")

    return "\n".join(lines)


def format_json(agents: list[AgentRecord], session_meta: dict) -> str:
    """Format as JSON for programmatic consumption."""
    data = {
        "session": session_meta,
        "summary": {
            "total_agents": len(agents),
            "succeeded": sum(1 for a in agents if a.succeeded),
            "failed": sum(1 for a in agents if not a.succeeded),
            "total_tokens": sum(a.total_tokens for a in agents),
            "total_tool_uses": sum(a.total_tool_use_count for a in agents),
            "total_duration_ms": sum(a.total_duration_ms for a in agents),
            "anomaly_count": sum(len(a.anomalies) for a in agents),
        },
        "agents": [
            {
                "index": i,
                "description": a.description,
                "subagent_type": a.subagent_type,
                "model": a.model,
                "prompt_length": a.prompt_len,
                "status": a.status,
                "succeeded": a.succeeded,
                "agent_id": a.agent_id,
                "total_tokens": a.total_tokens,
                "total_tool_use_count": a.total_tool_use_count,
                "duration_ms": a.total_duration_ms,
                "content_length": a.content_length,
                "content_summary": (_extract_content_summary(a.content_text, 200)
                                    if a.content_text and not a.is_error else ""),
                "is_error": a.is_error,
                "error_text": a.error_text if a.is_error else "",
                "anomalies": a.anomalies,
            }
            for i, a in enumerate(agents, 1)
        ],
    }
    # Convert dispatch_batches from AgentRecord refs to agent indices for JSON
    batches = session_meta.get("dispatch_batches", [])
    if batches:
        data["dispatch_batches"] = []
        for batch in batches:
            agent_indices = []
            for ba in batch:
                try:
                    agent_indices.append(agents.index(ba) + 1)
                except ValueError:
                    pass
            data["dispatch_batches"].append(agent_indices)
    # Remove non-serializable dispatch_batches from session copy
    session_copy = {k: v for k, v in session_meta.items() if k != "dispatch_batches"}
    data["session"] = session_copy
    return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Extract sub-agent workflow summary from Claude Code JSONL"
    )
    parser.add_argument("file", help="Path to .jsonl session file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--anomalies-only", action="store_true",
                        help="Only show agents with anomalies")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Include full agent output text in JSON mode")
    parser.add_argument("--tier2", nargs="?", const="anomalies", default=None,
                        metavar="SCOPE",
                        help="Tier 2 drill-down into sub-agent JSONL files. "
                             "SCOPE: 'anomalies' (default), 'all', or agent index (1-based)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    agents, meta = extract_agents(args.file)

    if not agents:
        print("No Agent tool calls found in this session.", file=sys.stderr)
        sys.exit(0)

    if args.tier2 is not None:
        # Tier 2 drill-down mode
        scope = args.tier2
        if scope == "all":
            target_agents = agents
        elif scope == "anomalies":
            target_agents = [a for a in agents if a.anomalies]
            if not target_agents:
                print("No anomalies detected — nothing to drill down into.")
                sys.exit(0)
        else:
            try:
                idx = int(scope) - 1
                if 0 <= idx < len(agents):
                    target_agents = [agents[idx]]
                else:
                    print(f"Agent index {scope} out of range (1-{len(agents)})", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print(f"Invalid --tier2 scope: {scope!r}. Use 'all', 'anomalies', or an agent index.", file=sys.stderr)
                sys.exit(1)

        drill_downs = [drill_down_agent(a, args.file) for a in target_agents]

        if args.json:
            # Convert dispatch_batches from AgentRecord refs to indices
            batches = meta.get("dispatch_batches", [])
            session_copy = {k: v for k, v in meta.items() if k != "dispatch_batches"}
            data = {
                "session": session_copy,
                "tier2": format_drill_down_json(target_agents, drill_downs, all_agents=agents),
            }
            if batches:
                data["dispatch_batches"] = [
                    [agents.index(ba) + 1 for ba in batch if ba in agents]
                    for batch in batches
                ]
            print(json.dumps(data, indent=2))
        else:
            # Print Tier 1 summary first, then drill-down
            print(format_table(agents, meta))
            print()
            print(format_drill_down(target_agents, drill_downs, meta, all_agents=agents))
        sys.exit(0)

    if args.anomalies_only:
        agents = [a for a in agents if a.anomalies]
        if not agents:
            print("No anomalies detected.")
            sys.exit(0)

    if args.json:
        if args.verbose:
            output = format_json(agents, meta)
            data = json.loads(output)
            for i, a_data in enumerate(data["agents"]):
                a_data["content_text"] = agents[i].content_text
            output = json.dumps(data, indent=2)
        else:
            output = format_json(agents, meta)
        print(output)
    else:
        print(format_table(agents, meta))


if __name__ == "__main__":
    main()

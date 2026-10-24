#!/usr/bin/env python3
"""Re-derive the keepalive's period and cap from Claude Code transcripts.

A wait is a main-thread turn that ended (`end_turn`) while a background task
it launched had not yet sent its <task-notification>; it lasts until the next
main-thread API response. An in-turn wait is a main-thread response's tool
calls, from that response until the one after their last result: an
AskUserQuestion or permission dialog, a foreground Bash or Agent. For each cap
N this prints what N refreshes would have cost and saved for each kind, and
then how the refreshes the mod actually made fared.

    python3 scripts/cache-keepalive/waits.py [~/.claude/projects]
"""

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PERIOD_MIN = 50
TTL_MIN = 60
# Cost in base-input-token units: a refresh reads the prefix (0.1x); a lapsed
# 1h entry is rewritten at 2x where a read would have cost 0.1x.
REFRESH, MISS = 0.1, 1.9
# A fork made while a tool call is pending answered in two requests in every
# live run (2026-10-24, Haiku 4.5): it tries the tool the conversation asked
# for, is denied, then replies.
INTURN_REFRESH = 2 * REFRESH

LAUNCH = [
    re.compile(r"Command running in background with ID: ([a-z0-9]+)"),
    re.compile(r"Async agent launched[\s\S]{0,400}?agentId: ([a-z0-9]+)"),
    re.compile(r"Monitor started \(task ([a-z0-9]+)"),
    re.compile(r"moved to the background \(ID: ([a-z0-9]+)\)"),
]
NOTE = re.compile(r"<task-id>([a-z0-9]+)</task-id>")
REFRESH_ROW = re.compile(r"refresh \d+/\d+: read (\d+)")
DAMAGED: Counter[Path] = Counter()


def ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def text_of(content: str | list[dict[str, Any]] | None) -> str:
    if isinstance(content, str):
        return content
    out = []
    for b in content or []:
        if b.get("type") == "text":
            out.append(b["text"])
        elif b.get("type") == "tool_result":
            out.append(text_of(b.get("content")))
    return "\n".join(out)


def read(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """The file's waits, its in-turn waits, and the mod's refresh rows with the response after each."""
    waits: list[dict[str, Any]] = []
    inturn: list[dict[str, Any]] = []
    calls: dict[str, dict[str, Any]] = {}
    batch: dict[str, Any] | None = None
    answered: list[dict[str, Any]] = []
    refreshes: list[dict[str, Any]] = []
    inflight: dict[str, float] = {}
    pending: dict[str, Any] | None = None
    refresh: dict[str, Any] | None = None
    cur: dict[str, Any] | None = None
    last_id = None
    with path.open(errors="replace") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        # A crash mid-write leaves a run of NUL bytes where records were.
        if line.startswith("\0"):
            DAMAGED[path] += 1
            line = line.lstrip("\0")
            if not line.strip():
                continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError as err:
            # A transcript being written ends mid-record.
            if i == len(lines) - 1:
                continue
            err.add_note(f"{path}:{i + 1}")
            raise
        if r.get("isSidechain"):
            continue
        kind = r.get("type")
        if kind == "assistant":
            m = r.get("message") or {}
            u = m.get("usage")
            if not u or m.get("model") == "<synthetic>":
                continue
            if cur is None or m.get("id") != last_id:
                last_id = m.get("id")
                now = ts(r["timestamp"])
                read_, write = u.get("cache_read_input_tokens", 0), u.get("cache_creation_input_tokens", 0)
                if pending:
                    pending.update(gap=(now - pending["t"]) / 60, kept=read_ + write >= 0.5 * pending["ctx"])
                    waits.append(pending)
                    pending = None
                if refresh:
                    refresh.update(next_read=read_, next_write=write, after=(now - refresh["t"]) / 60)
                    refreshes.append(refresh)
                    refresh = None
                for b in answered:
                    b.update(gap=(now - b["t"]) / 60, kept=read_ + write >= 0.5 * b["ctx"], wake="answered")
                    inturn.append(b)
                answered = []
                cur = {"t": now, "ctx": u.get("input_tokens", 0) + read_ + write + u.get("output_tokens", 0)}
                batch = None
            # Claude Code writes one record per content block, so a response's
            # parallel tool calls arrive as several records sharing its id.
            for block in m.get("content") or []:
                if block.get("type") == "tool_use":
                    if batch is None:
                        batch = dict(cur, tools=[], ids=set())
                    batch["tools"].append(block["name"])
                    batch["ids"].add(block["id"])
                    calls[block["id"]] = batch
            if m.get("stop_reason") == "end_turn" and inflight:
                pending = dict(cur, wake=None)
            elif m.get("stop_reason") not in (None, "end_turn"):
                pending = None
            continue
        if kind == "system" and str(r.get("content", "")).startswith("cache-keepalive: refresh"):
            got = REFRESH_ROW.search(r["content"])
            refresh = {"t": ts(r["timestamp"]), "read": int(got.group(1)) if got else None, "row": r["content"]}
            continue
        if kind == "user":
            content = (r.get("message") or {}).get("content")
            for block in content if isinstance(content, list) else []:
                b = calls.pop(block.get("tool_use_id", ""), None) if block.get("type") == "tool_result" else None
                if b is not None:
                    b["ids"].discard(block["tool_use_id"])
                    if not b["ids"]:
                        # The mod's timer runs only while a call is pending: an
                        # interrupted call's turn ends with its result.
                        b["armed"] = (ts(r["timestamp"]) - b["t"]) / 60
                        answered.append(b)
            text = text_of(content)
            if pending and pending["wake"] is None:
                pending["wake"] = "task" if "<task-notification>" in text else "user" if not r.get("isMeta") else None
        elif kind == "attachment" and (r.get("attachment") or {}).get("type") == "queued_command":
            text = json.dumps(r["attachment"].get("prompt") or "")
            if pending and pending["wake"] is None and "<task-notification>" in text:
                pending["wake"] = "task"
        else:
            continue
        for p in LAUNCH:
            for tid in p.findall(text):
                inflight.setdefault(tid, ts(r["timestamp"]))
        for tid in NOTE.findall(text):
            inflight.pop(tid, None)
    if pending:
        waits.append(dict(pending, gap=None, wake="end-of-file", kept=False))
    unclosed = {id(b): b for b in calls.values()}
    inturn += [dict(b, gap=None, wake="end-of-file", kept=False) for b in unclosed.values()]
    return waits, inturn, refreshes


def net(waits: list[dict[str, Any]], cap: int, open_after: list[dict[str, Any]], price: float = REFRESH) -> tuple[int, int, float]:
    """Refreshes, rewrites avoided, and saved minus spent in millions of base-input tokens.

    A wait's refreshes fire while its timer is armed: the whole gap after a
    turn end, only the pending part of an in-turn wait (`armed`)."""
    spent = saved = 0.0
    n_refresh = n_saved = 0
    for w in waits:
        k = min(cap, int(w.get("armed", w["gap"]) // PERIOD_MIN))
        spent += k * price * w["ctx"]
        n_refresh += k
        if w["kept"] and TTL_MIN < w["gap"] <= k * PERIOD_MIN + TTL_MIN:
            saved += MISS * w["ctx"]
            n_saved += 1
    # A wait the transcript never closes: worst case, every refresh fired.
    for w in open_after:
        spent += cap * price * w["ctx"]
        n_refresh += cap
    return n_refresh, n_saved, (saved - spent) / 1e6


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / ".claude/projects").expanduser()
    waits: list[dict[str, Any]] = []
    inturn: list[dict[str, Any]] = []
    refreshes: list[dict[str, Any]] = []
    files = sorted(root.glob("*/*.jsonl"))
    for path in files:
        w, t, r = read(path)
        waits += w
        inturn += t
        refreshes += r
    known = [w for w in waits if w["gap"] is not None and w["gap"] >= 0]
    open_ = [w for w in waits if w["wake"] == "end-of-file"]
    print(f"{len(files)} transcripts, {len(waits)} waits with background work in flight: {dict(Counter(w['wake'] for w in waits))}")
    bins = [0, 5, 30, 55, 60, 120, 180, 240, 360, 720, 1440, float("inf")]
    for lo, hi in zip(bins, bins[1:]):
        sel = [w for w in known if lo <= w["gap"] < hi]
        if sel:
            rewrote = sum(1 for w in sel if w["kept"] and w["gap"] > TTL_MIN)
            print(f"  gap [{lo:>4}, {hi:>6}) min: {len(sel):4} waits, {rewrote:3} past the TTL with the prefix still needed")
    print(f"cap N: refreshes, rewrites avoided, net (M base-input tokens) -- all waits | + unclosed waits at worst")
    for cap in range(0, 7):
        a = net(known, cap, [])
        b = net(known, cap, open_)
        print(f"  {cap}: {a[0]:4} {a[1]:3} {a[2]:7.2f} | {b[2]:7.2f}")
    known_t = [w for w in inturn if w["wake"] == "answered" and w["armed"] >= PERIOD_MIN]
    open_t = [w for w in inturn if w["wake"] == "end-of-file"]
    tools = lambda ws: dict(Counter(t for w in ws for t in set(w["tools"])))
    print(f"{len(known_t)} in-turn waits pending {PERIOD_MIN}+ min, by tool: {tools(known_t)}")
    print(f"{len(open_t)} in-turn waits never answered (the transcript ends mid-call), by tool: {tools(open_t)}")
    for lo, hi in zip(bins, bins[1:]):
        sel = [w for w in known_t if lo <= w["armed"] < hi]
        if sel:
            rewrote = sum(1 for w in sel if w["kept"] and w["gap"] > TTL_MIN)
            print(f"  pending [{lo:>4}, {hi:>6}) min: {len(sel):4} in-turn waits, {rewrote:3} past the TTL with the prefix still needed")
    # Every subagent runs in the background since 9197a25c (2026-10-22), so a
    # foreground Agent wait is history; the right-hand columns leave it out.
    no_agent = [w for w in known_t if "Agent" not in w["tools"]]
    open_no_agent = [w for w in open_t if "Agent" not in w["tools"]]
    print("in-turn, cap N: refreshes, rewrites avoided, net -- all | + never answered at worst || no Agent | + never answered at worst")
    for cap in range(0, 7):
        a, b = net(known_t, cap, [], INTURN_REFRESH), net(known_t, cap, open_t, INTURN_REFRESH)
        c, d = net(no_agent, cap, [], INTURN_REFRESH), net(no_agent, cap, open_no_agent, INTURN_REFRESH)
        print(f"  {cap}: {a[0]:4} {a[1]:3} {a[2]:7.2f} | {b[2]:7.2f} || {c[0]:4} {c[1]:3} {c[2]:7.2f} | {d[2]:7.2f}")
    for path, n in DAMAGED.items():
        print(f"{n} lines began with NUL padding (records lost there) in {path}")
    print(f"{len(refreshes)} refreshes the mod made:")
    for r in refreshes:
        hit = r.get("next_read", 0) >= 0.5 * (r.get("next_read", 0) + r.get("next_write", 0) or 1)
        print(f"  next response {r.get('after', float('nan')):6.1f} min later, {'hit' if hit else 'MISS'}: {r['row']}")


if __name__ == "__main__":
    main()

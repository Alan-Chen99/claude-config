"""agent-tools cc-cost: what a Claude Code session or subagent cost, and what
its prompt cache did.

    agent-tools cc-cost [TARGET] [--misses] [--json]
    agent-tools cc-cost --statusline        # cc's statusLine JSON on stdin
    agent-tools cc-cost --limits [--span N] [--plot PNG] [--json]

TARGET is a session id, a subagent id (either with its `agent-` prefix or
without), a unique prefix of one, or a transcript path; with none, the running
session (`CLAUDE_CODE_SESSION_ID`). A session reports every agent in it; a
subagent reports itself and the agents it spawned.

Each response is priced as cc 2.1.310 prices it (`pricing.py`): cache writes at
their own TTL's rate (5m 1.25x input, 1h 2x), reads at the model's own read
rate (0.1x input, 0.05x on the newest), the long-prompt tier, fast mode, US
inference and web search. A miss is cc's prompt-cache test applied to every
agent (`session.py`); its cost is the re-written prefix at the write rate less
what reading it would have cost.

An agent's ctx is the context it ended on, or is at while it runs: its last
response's prompt plus its reply, as the status line counts it.

cc's own total (the `cost-state` record it writes on exit and on /clear,
/resume and fork) also counts requests it never transcribes: compaction, prompt
suggestions, away summaries, session titles, WebFetch's and WebSearch's model
calls. The report compares the two at the time cc last wrote it.

--limits sizes each account's 5-hour and weekly windows in API-equivalent
dollars from the readings the status line logs and this machine's transcripts
(`limits.py`).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from claude_config.cc_cost.pricing import MODELS, base_model
from claude_config.cc_cost.session import Agent, Priced, Session, Stats, load, tree

COLUMNS = [("inp", "input"), ("out", "output"), ("w5", "wr 5m"), ("w1h", "wr 1h"), ("rd", "read"), ("web", "web")]
LABEL = 46


def when(t: float) -> str:
    return datetime.fromtimestamp(t).astimezone().strftime("%Y-%m-%d %H:%M %Z")


def span(seconds: float) -> str:
    m = int(seconds // 60)
    return f"{m // 60}h{m % 60:02d}m" if m >= 60 else f"{m}m{int(seconds % 60):02d}s"


def pct(x: float | None) -> str:
    return "-" if x is None else f"{round(x * 100)}%"


def clip(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def context(priced: list[Priced]) -> int | None:
    if not priced:
        return None
    t = priced[-1].tokens
    return t.prompt + t.out


def kilo(n: int | None) -> str:
    return "-" if n is None else f"{n // 1000}K"


def row(label: str, s: Stats, ctx: str) -> str:
    cells = "".join(f"{s.cost.get(k, 0):>9.2f}" for k, _ in COLUMNS)
    return (f"{clip(label, LABEL):<{LABEL}}{s.requests:>6}{ctx:>7}{cells}{s.total:>10.2f}"
            f"{pct(s.hit_ratio):>6}{len(s.misses):>6}{s.premium:>9.2f}")


def by_model(priced: list[Priced]) -> dict[str, float]:
    out: defaultdict[str, float] = defaultdict(float)
    for p in priced:
        out[p.response.model] += p.total
    return dict(out)


def against_cc(session: Session, priced: list[Priced]) -> dict | None:
    """The traced cost against cc's total when it last wrote it. Only finished
    responses compare: cc prices a response when its stream ends."""
    if not session.cost_state:
        return None
    rec, at = session.cost_state
    finished = [p for p in priced if p.response.finished]
    then = [p for p in finished if at is None or p.response.last_ts <= at]
    return {"total": rec["totalCostUSD"], "at": at, "traced": sum(p.total for p in then),
            "later": len(finished) - len(then), "restarted": session.cost_state_restarted,
            "totals": [r["totalCostUSD"] for r, _ in session.cost_states],
            "unknown_model": bool(rec.get("hasUnknownModelCost")), "traced_by_model": by_model(then),
            "cc_by_model": {m: v.get("costUSD") for m, v in (rec.get("modelUsage") or {}).items()}}


def _against_cc_lines(c: dict) -> list[str]:
    if c["restarted"]:
        totals = " → ".join(f"${t:.2f}" for t in c["totals"])
        return [f"cc's cost-state restarted ({totals}, startTime changed or the total fell): a process that did",
                "not restore it wrote its own, so it does not cover this session and is not compared"]
    cc, traced, at = c["total"], c["traced"], c["at"]
    out = [f"cc's total ${cc:.2f} when it last wrote cost-state" + (f" ({when(at)})" if at else "")
           + f"; traced to then ${traced:.2f}; untraced ${cc - traced:.2f}"
           + (f" ({round((cc - traced) / cc * 100)}%)" if cc else "")
           + (f"; {c['later']} responses since" if c["later"] else ""),
           "  untraced: requests cc bills but never transcribes (compaction, prompt suggestions, away summaries,",
           "  session titles, WebFetch and WebSearch model calls)"]
    if c["unknown_model"]:
        out.append("  cc flagged an unknown model in its total (hasUnknownModelCost)")
    out.append(f"  {'model':<28}{'traced':>10}{'cc':>10}")
    for m in sorted(c["traced_by_model"].keys() | c["cc_by_model"].keys()):
        out.append(f"  {m:<28}{c['traced_by_model'].get(m, 0):>10.2f}{c['cc_by_model'].get(m) or 0:>10.2f}")
    if traced > cc * 1.01:
        out.append(f"  TRACED EXCEEDS cc's TOTAL by ${traced - cc:.2f}: a response counted twice, "
                   "or a price that differs from cc's")
    return out


def report(session: Session, agents: list[tuple[Agent, int]], show_misses: bool) -> str:
    priced = [p for a, _ in agents for p in a.priced]
    total = Stats.of(priced)
    root = agents[0][0]
    head = (f"session {session.main.stem}" if root.id == "main"
            else f"agent {root.label} in session {session.main.stem}")
    out = [head, f"  {root.path}"]
    if priced:
        out.append(f"  {when(min(p.response.first_ts for p in priced))} → "
                   f"{when(max(p.response.last_ts for p in priced))}")
    out += ["", f"{'agent ($)':<{LABEL}}{'reqs':>6}{'ctx':>7}" + "".join(f"{h:>9}" for _, h in COLUMNS)
            + f"{'total':>10}{'hit':>6}{'miss':>6}{'miss $':>9}"]
    out += [row("  " * level + a.label, Stats.of(a.priced), kilo(context(a.priced))) for a, level in agents]
    if len(agents) > 1:
        out.append(row("total", total, ""))
    unpriced = sorted({p.response.model for p in priced if base_model(p.response.model) not in MODELS})
    if unpriced:
        out.append(f"\nUNPRICED models, charged as cc charges an unknown one (5/25 $/Mtok): {', '.join(unpriced)}")
    if total.unfinished:
        out.append(f"\n{len(total.unfinished)} unfinished responses (interrupted, or still streaming): "
                   f"${total.unfinished_total:.2f}, their output counted only as far as logged; cc never prices them")

    c = against_cc(session, priced) if root.id == "main" else None
    if c:
        out += [""] + _against_cc_lines(c)
    elif root.id == "main":
        out += ["", "no cost-state record yet (cc writes one on exit): cc's own total is not known here"]

    out += ["", f"misses: {len(total.misses)}, re-writing "
            f"{sum(p.rewritten for p in total.misses):,} cached tokens, ${total.premium:.2f} over reading them"
            + (f"; {total.expected} expected rebuilds after compaction" if total.expected else "")]
    causes: Counter[str] = Counter()
    cost: defaultdict[str, float] = defaultdict(float)
    for p in total.misses:
        causes[p.cause] += 1
        cost[p.cause] += p.premium
    out += [f"  {c:<40}{n:>5}  ${cost[c]:.2f}" for c, n in causes.most_common()]
    if show_misses and total.misses:
        owner = {id(p): a.label for a, _ in agents for p in a.priced}
        out += ["", f"{'time':<17} {'agent':<24} {'model':<20}{'rewritten':>10}{'gap':>9}  {'cause':<40}{'$':>7}"]
        for p in sorted(total.misses, key=lambda p: p.response.last_ts):
            out.append(f"{when(p.response.last_ts):<17} {clip(owner[id(p)], 24):<24} {p.response.model:<20}"
                       f"{p.rewritten:>10,}{span(p.gap):>9}  {clip(p.cause, 40):<40}{p.premium:>7.2f}")
    return "\n".join(out)


def iso(t: float | None) -> str | None:
    return None if t is None else datetime.fromtimestamp(t).astimezone().isoformat()


def as_json(session: Session, agents: list[tuple[Agent, int]]) -> dict:
    def stats(s: Stats) -> dict:
        return {"requests": s.requests, "cost": s.cost, "total": s.total, "hit_ratio": s.hit_ratio,
                "misses": len(s.misses), "miss_premium": s.premium, "expected": s.expected, "cold": s.cold,
                "unfinished": len(s.unfinished), "unfinished_total": s.unfinished_total}

    priced = [p for a, _ in agents for p in a.priced]
    out = {"session": session.main.stem, "main": str(session.main),
           "agents": [{"id": a.id, "label": a.label, "parent": a.parent, "level": level, "path": str(a.path),
                       "context": context(a.priced), **stats(Stats.of(a.priced))} for a, level in agents],
           "total": stats(Stats.of(priced)),
           "misses": [{"agent": a.id, "message_id": p.response.id, "model": p.response.model,
                       "at": iso(p.response.last_ts), "rewritten": p.rewritten, "gap_seconds": p.gap,
                       "cause": p.cause, "premium": p.premium}
                      for a, _ in agents for p in a.priced if p.outcome == "miss"]}
    c = against_cc(session, priced) if agents[0][0].id == "main" else None
    if c:
        out["cost_state"] = c | {"at": iso(c["at"])}
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="cc-cost", description=__doc__,
                                 epilog="TARGET: session id, subagent id, unique prefix, or transcript path",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", help="default: $CLAUDE_CODE_SESSION_ID")
    ap.add_argument("--misses", action="store_true", help="list every cache miss")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    ap.add_argument("--statusline", action="store_true",
                    help="read cc's statusLine JSON on stdin and print the status line")
    ap.add_argument("--limits", action="store_true",
                    help="size each account's 5-hour and weekly windows from the logged readings")
    ap.add_argument("--span", type=float, default=5, help="--limits: points a best span covers at least (default 5)")
    ap.add_argument("--plot", type=Path, metavar="PNG", help="--limits: also plot cost per point to this file")
    args = ap.parse_args(argv)
    if args.statusline:
        if args.target or args.misses or args.json or args.limits:
            ap.error("--statusline takes no TARGET, --misses, --json or --limits")
        from claude_config.cc_cost.statusline import main as statusline

        statusline()
        return
    if args.limits:
        if args.target or args.misses:
            ap.error("--limits takes no TARGET or --misses")
        from claude_config.cc_cost import limits

        if not limits.LOG.is_file():
            sys.exit(f"cc-cost: no readings yet: the status line logs them to {limits.LOG}")
        roots = [Path.home() / ".claude" / "projects"]
        if os.environ.get("CLAUDE_CONFIG_DIR"):
            roots.append(Path(os.environ["CLAUDE_CONFIG_DIR"]) / "projects")
        cfg = json.loads(limits.global_config().read_text())
        flag = (cfg.get("cachedGrowthBookFeatures") or {}).get("tengu_amber_tally") or {}
        a = limits.analyse(limits.LOG, roots, args.span, flag)
        print(json.dumps(a, indent=1) if args.json else limits.report(a))
        if args.plot:
            limits.plot(a, args.plot)
            print(f"plot: {args.plot}", file=sys.stderr)
        return
    elif args.plot:
        ap.error("--plot needs --limits")
    target = args.target or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not target:
        ap.error("no TARGET and no CLAUDE_CODE_SESSION_ID")
    # cc_pretty's package import costs pydantic; the status line never needs it
    from claude_config.cc_pretty.locate import SessionNotFound, resolve_log_arg

    try:
        path = Path(resolve_log_arg(target).path)
    except SessionNotFound as e:
        sys.exit(f"cc-cost: {e}")
    session = load(path)
    root = "main" if "subagents" not in path.parts else path.stem.removeprefix("agent-")
    agents = tree(session, root)
    print(json.dumps(as_json(session, agents), indent=1) if args.json else report(session, agents, args.misses))


if __name__ == "__main__":
    main()

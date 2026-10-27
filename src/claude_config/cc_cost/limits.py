"""Plan rate limits sized from the status line's readings and this machine's
transcripts.

The status line logs each session's `rate_limits` reading whenever it changes
(`record`, into `LOG`). A reading is a percentage of an account's 5-hour or
weekly window, in whole points: the server sends `0.21`, cc passes on 21.
Between the first sightings of two readings in one window exactly their
difference in points was spent, whatever rounding the server applies. A
reading is sighted when the response that carried it began, which the
session's transcript dates; the status line may log it much later.

What this machine spent in between is in its transcripts: every response, main
and subagent, interactive or headless, belongs to the account cc named for its
session (`session.py`). Requests from other machines, claude.ai and those cc
never transcribes move the readings too, so a point's local cost is at most
its allowance. The largest over a span of several points is the closest
estimate: a span also dilutes the delay between a reading changing and a
session seeing it, which shifts a cost between neighbouring intervals.

`credits*` tests one reading of cc's own model of the 5-hour window, the
`tengu_amber_tally` flag (`fiveHourCredits` per tier, `creditsPerMillionTokens`
per model; cc uses it to warn that resuming a cold conversation costs N% of
the window): each response's dollars converted to tokens at its model's 1-hour
cache-write rate, at the flag's credits per million.
"""

from __future__ import annotations

import json
import os
import statistics
import time
from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from itertools import accumulate
from pathlib import Path
from typing import Any

from claude_config.cc_cost.pricing import base_model, rates
from claude_config.cc_cost.session import Priced, Session, load, session_paths

LOG = Path.home() / ".claude" / "cc-cost" / "rate-limits.jsonl"
# The last reading each session logged, so an unchanged one is not logged again
STATE = LOG.parent / "last"
WINDOWS = {"five_hour": "5h", "seven_day": "7d"}
CAP = 100  # cc caps used_percentage here, and past it the server's figure is hidden
CATEGORIES = ("inp", "out", "w5", "w1h", "rd", "web")


def global_config() -> Path:
    d = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(d) / ".claude.json" if d else Path.home() / ".claude.json"


def record(data: dict[str, Any]) -> None:
    """Append the session's reading to `LOG` if it differs from the last one
    the session logged, with the account and tier cc is logged in as."""
    sid = data.get("session_id")
    rl = data.get("rate_limits") or {}
    reading = {w: rl[w] for w in WINDOWS if rl.get(w)}
    if not sid or not reading:
        return
    last = STATE / f"{sid}.json"
    if last.is_file() and json.loads(last.read_text()) == reading:
        return
    account = json.loads(global_config().read_text()).get("oauthAccount") or {}
    line = {"ts": time.time(), "session": sid, "transcript": data.get("transcript_path"),
            "account": account.get("emailAddress"), "tier": account.get("organizationRateLimitTier"), **reading}
    STATE.mkdir(parents=True, exist_ok=True)
    # One short write per line with O_APPEND: concurrent sessions never interleave
    with LOG.open("a") as f:
        f.write(json.dumps(line) + "\n")
    last.write_text(json.dumps(reading))


def readings(path: Path) -> list[dict[str, Any]]:
    lines = path.read_bytes().splitlines()
    out = []
    for i, line in enumerate(lines):
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            # a session may be mid-append to the last line; anything else is corrupt
            if i == len(lines) - 1:
                continue
            raise
    return out


@dataclass(frozen=True)
class Interval:
    window: str
    resets_at: int
    start: float
    end: float
    points: float
    cost: float
    # None when a response in it is of a model the flag has no rate for
    credits: float | None
    # `cost` by token category: what a fit of the plan's own weights would need
    by_category: dict[str, float]


@dataclass(frozen=True)
class Span:
    start: float
    end: float
    points: float
    per_point: float


def best_span(intervals: list[Interval], span: float, key: str) -> Span | None:
    """The highest cost per point over runs of consecutive intervals in one
    window that cover at least `span` points."""
    best = None
    by_window: defaultdict[int, list[Interval]] = defaultdict(list)
    for iv in intervals:
        by_window[iv.resets_at].append(iv)
    for run in by_window.values():
        for i in range(len(run)):
            points = value = 0.0
            for j in range(i, len(run)):
                v = getattr(run[j], key)
                if v is None:
                    break
                points += run[j].points
                value += v
                if points >= span:
                    if best is None or value / points > best.per_point:
                        best = Span(run[i].start, run[j].end, points, value / points)
                    break
    return best


def ticks(seen: dict[float, float]) -> list[tuple[float, float]]:
    """(value, first sighting) pairs rising in both. A value first seen only
    after a higher one was (by a session that missed its rise) marks no tick."""
    out = []
    earliest = float("inf")
    for v in sorted(seen, reverse=True):
        if seen[v] < earliest:
            out.append((v, seen[v]))
            earliest = seen[v]
    return out[::-1]


def credits_of(p: Priced, cpm: dict[str, float]) -> float | None:
    rate = cpm.get(base_model(p.response.model))
    if rate is None:
        return None
    u = p.response.usage
    w1h = rates(p.response.model, p.tokens, u.get("speed") == "fast", u.get("inference_geo") == "us")["w1h"]
    return (p.total - p.cost.get("web", 0)) / w1h * rate / 1e6


def analyse(log: Path, roots: list[Path], span: float, flag: dict[str, Any]) -> dict[str, Any]:
    recs = readings(log)
    if not recs:
        raise SystemExit(f"cc-cost: {log} holds no readings yet")
    # A reading is what the session's latest API response carried, so it was
    # seen when that response began, however much later the status line ran:
    # an idle session re-renders its old reading on a resize or settings change
    sessions: dict[str, Session] = {}
    for r in recs:
        t = Path(r.get("transcript") or "")
        if r["session"] not in sessions and t.is_file():
            sessions[r["session"]] = load(t)
    began = {sid: sorted(p.response.first_ts for a in s.agents for p in a.priced) for sid, s in sessions.items()}
    placed: list[tuple[float, dict[str, Any]]] = []
    orphaned = unplaced = 0
    for r in recs:
        if r["session"] not in sessions:
            orphaned += 1
            continue
        i = bisect_right(began[r["session"]], r["ts"])
        if i == 0:
            # only an untranscribed request (a title, a suggestion) came before it
            unplaced += 1
            continue
        placed.append((began[r["session"]][i - 1], r))
    if not placed:
        raise SystemExit(f"cc-cost: no reading in {log} can be placed in a transcript yet")
    start = min(t for t, _ in placed)
    roots = sorted(set(roots) | {Path(r["transcript"]).parent.parent for _, r in placed})
    for root in roots:
        for f in root.glob("*/**/*.jsonl"):
            m = session_paths(f)[0]
            if m.stem not in sessions and f.stat().st_mtime >= start and m.is_file():
                sessions[m.stem] = load(m)

    cpm = flag.get("creditsPerMillionTokens") or {}
    spent: defaultdict[str, list[tuple[float, float, float | None, dict[str, float]]]] = defaultdict(list)
    unattributed: list[Priced] = []
    nameless: set[str] = set()
    for s in sessions.values():
        for a in s.agents:
            for p in a.priced:
                if p.response.last_ts < start:
                    continue
                acct = s.account_at(p.response.first_ts)
                if acct is None:
                    unattributed.append(p)
                    continue
                c = credits_of(p, cpm)
                if c is None:
                    nameless.add(base_model(p.response.model))
                spent[acct].append((p.response.last_ts, p.total, c, p.cost))

    # Readings by the account the session's transcript names, which is the
    # account cc sent the request as; the logged account is the global
    # config's, so it vouches for the tier only when the two agree
    seen: defaultdict[tuple[str, str, int], dict[float, float]] = defaultdict(dict)
    tiers: dict[str, tuple[float, str]] = {}
    mismatched = 0
    for t, r in placed:
        acct = sessions[r["session"]].account_at(t)
        if acct is None:
            orphaned += 1
            continue
        if r.get("account") == acct:
            if r.get("tier") and t >= tiers.get(acct, (0.0, ""))[0]:
                tiers[acct] = (t, r["tier"])
        else:
            mismatched += 1
        for w in WINDOWS:
            if w in r:
                d = seen[(acct, w, r[w]["resets_at"])]
                v = r[w]["used_percentage"]
                d[v] = min(d[v], t) if v in d else t

    accounts = {}
    for acct in sorted({k[0] for k in seen}):
        rows = sorted(spent[acct], key=lambda row: row[0])
        at = [row[0] for row in rows]
        cost = [0.0, *accumulate(row[1] for row in rows)]
        cred = [0.0, *accumulate(row[2] or 0.0 for row in rows)]
        gaps = [0, *accumulate(row[2] is None for row in rows)]
        cats = {k: [0.0, *accumulate(row[3].get(k, 0.0) for row in rows)] for k in CATEGORIES}
        tier = tiers.get(acct, (0.0, None))[1]
        windows = {}
        for w, short in WINDOWS.items():
            ivs = []
            for (a, ww, resets_at), d in sorted(seen.items()):
                if a != acct or ww != w:
                    continue
                tk = ticks(d)
                for (v0, t0), (v1, t1) in zip(tk, tk[1:]):
                    if v1 >= CAP:
                        continue
                    i, j = bisect_right(at, t0), bisect_right(at, t1)
                    ivs.append(Interval(w, resets_at, t0, t1, v1 - v0, cost[j] - cost[i],
                                        None if gaps[j] - gaps[i] else cred[j] - cred[i],
                                        {k: v[j] - v[i] for k, v in cats.items()}))
            per = sorted(iv.cost / iv.points for iv in ivs)
            best = best_span(ivs, span, "cost")
            best_cr = best_span(ivs, span, "credits")
            five = (flag.get("fiveHourCredits") or {}).get(tier) if w == "five_hour" else None
            windows[short] = {
                "intervals": [asdict(iv) for iv in ivs], "points": sum(iv.points for iv in ivs),
                "median": statistics.median(per) if per else None,
                "p90": statistics.quantiles(per, n=10, method="inclusive")[-1] if len(per) > 1 else (per or [None])[0],
                "max": per[-1] if per else None,
                "best_span": asdict(best) if best else None,
                "window_estimate": best.per_point * 100 if best else None,
                "credits_best_span": asdict(best_cr) if best_cr else None,
                "flag_credits_per_point": five / 100 if five else None}
        accounts[acct] = {"tier": tier, "windows": windows}
    return {"log": str(log), "readings": len(recs), "sessions_logging": len({r["session"] for r in recs}),
            "from": start, "to": max(r["ts"] for r in recs), "span": span, "accounts": accounts,
            "unattributed": {"responses": len(unattributed), "cost": sum(p.total for p in unattributed)},
            "orphaned_readings": orphaned, "unplaced_readings": unplaced, "mismatched_readings": mismatched,
            "models_without_credit_rate": sorted(nameless)}


def when(t: float, fmt: str = "%m-%d %H:%M") -> str:
    return datetime.fromtimestamp(t).astimezone().strftime(fmt)


def report(a: dict[str, Any]) -> str:
    def money(x: float | None) -> str:
        return "-" if x is None else f"{x:.2f}"

    out = [f"{a['log']}: {a['readings']} readings from {a['sessions_logging']} sessions, "
           f"{when(a['from'], '%Y-%m-%d %H:%M')} → {when(a['to'], '%Y-%m-%d %H:%M %Z')}",
           "Local cost per point is a floor on the allowance: other machines, claude.ai and requests cc never",
           f"transcribes move the readings too. The best span of {a['span']:g}+ points is the closest estimate."]
    for acct, d in a["accounts"].items():
        out += ["", f"{acct}  {d['tier'] or 'tier unknown (no reading logged while cc was logged in as it)'}",
                f"  {'':<4}{'intervals':>10}{'points':>8}{'$/pt median':>13}{'p90':>8}{'max':>8}"
                f"   {'best span $/pt':<32}{'window ≈':>10}{'credits*/pt':>13}{'flag/pt':>9}"]
        for short, w in d["windows"].items():
            b, cr = w["best_span"], w["credits_best_span"]
            where = f"{b['per_point']:.2f}  {when(b['start'])} → {when(b['end'])}" if b else "-"
            out.append(f"  {short:<4}{len(w['intervals']):>10}{w['points']:>8g}{money(w['median']):>13}"
                       f"{money(w['p90']):>8}{money(w['max']):>8}   {where:<32}"
                       f"{'$' + format(w['window_estimate'], ',.0f') if b else '-':>10}"
                       f"{format(cr['per_point'], ',.0f') if cr else '-':>13}"
                       f"{format(w['flag_credits_per_point'], ',.0f') if w['flag_credits_per_point'] else '-':>9}")
    u = a["unattributed"]
    if u["responses"]:
        out.append(f"\n{u['responses']} responses (${u['cost']:.2f}) in sessions cc named no account for: not counted")
    if a["orphaned_readings"]:
        out.append(f"{a['orphaned_readings']} readings from sessions whose transcript names no account or is gone: skipped")
    if a["unplaced_readings"]:
        out.append(f"{a['unplaced_readings']} readings logged before their session's first transcribed response: skipped")
    if a["mismatched_readings"]:
        out.append(f"{a['mismatched_readings']} readings logged while cc's global config named another account: "
                   "counted for the transcript's account, their tier not trusted")
    if a["models_without_credit_rate"]:
        out.append(f"no creditsPerMillionTokens for {', '.join(a['models_without_credit_rate'])}: "
                   "credits* skips intervals with their responses")
    return "\n".join(out)


def plot(a: dict[str, Any], path: Path) -> None:
    """Each account's cost per point per interval over time, one panel per
    window, with its best span and 90th percentile, all over the readings' span."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    # A lone date would get matplotlib's default range of four years around it
    pad = max((a["to"] - a["from"]) * 0.03, 1800)
    lo, hi = datetime.fromtimestamp(a["from"] - pad), datetime.fromtimestamp(a["to"] + pad)
    accts = list(a["accounts"].items())
    fig, axes = plt.subplots(len(accts), 2, figsize=(13, 4 * len(accts)), squeeze=False)
    for row, (acct, d) in zip(axes, accts):
        for ax, (short, w) in zip(row, d["windows"].items()):
            ivs = w["intervals"]
            ax.scatter([datetime.fromtimestamp(iv["end"]) for iv in ivs], [iv["cost"] / iv["points"] for iv in ivs],
                       s=[12 * iv["points"] for iv in ivs], alpha=0.6, label="interval (size: points)")
            if w["best_span"]:
                ax.axhline(w["best_span"]["per_point"], color="C3",
                           label=f"best {a['span']:g}+ pt span ${w['best_span']['per_point']:.2f}")
            if w["p90"] is not None:
                ax.axhline(w["p90"], color="C2", linestyle="--", label=f"p90 ${w['p90']:.2f}")
            if not ivs:
                ax.text(0.5, 0.5, "no intervals yet", transform=ax.transAxes, ha="center", color="grey")
            est = f" ≈ ${w['window_estimate']:,.0f} per window" if w["window_estimate"] else ""
            ax.set_title(f"{acct} {short} ({d['tier'] or 'tier?'}){est}", fontsize=9)
            ax.set_ylabel("local API-equivalent $ per point")
            ax.set_xlim(lo, hi)
            ax.set_ylim(bottom=0)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
            ax.tick_params(axis="x", labelrotation=30, labelsize=7)
            if ivs:
                ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=110)

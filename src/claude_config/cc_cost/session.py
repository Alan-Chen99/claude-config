"""One Claude Code session's API responses, priced and judged against the cache.

A session is its main transcript `<session>.jsonl` plus every subagent's
`<session>/subagents/[workflows/<run>/]agent-<id>.jsonl`, each beside an
`agent-<id>.meta.json` naming its type, description and (when nested) its
`parentAgentId`.

Three things make a naive sum wrong:

- One response is logged once per content block, and the early lines carry a
  partial `output_tokens`; the last line's usage is the final one.
- A fork subagent's transcript opens with copies of its parent's records, same
  message ids, re-stamped with the fork's own `agentId`, and a forked session
  (`forkedFrom`) opens with copies of its origin's. Each response is owned by
  the shallowest transcript holding it; a `forkedFrom` copy by none here.
- Copies still precede the agent's own requests in its conversation, so they
  stay in the chain a cache miss is judged on: a fork's first request reads
  its parent's cached prefix or rebuilds it.

A response whose last line has no `stop_reason` never finished: interrupted,
or still streaming. Its usage is the stream's opening one, so its output is a
floor, and cc, which prices a response when its stream ends, never counts it;
its prompt was processed and is priced here all the same.

A miss is cc's own client-side test (2.1.310's prompt-cache ledger, beside the
literal `system_prompt_changed: "system prompt changed"`), applied to every
agent where cc applies it to the main thread alone.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from claude_config.cc_cost.pricing import SECONDS, Tokens, base_model, price, rates

# cc's miss test: the read falls short of the smaller of the two prompts by 5%
# and by at least this many tokens
MISS_MIN_TOKENS = 2000
MISS_RATIO = 0.95


@dataclass(frozen=True)
class Response:
    """One API response as its transcript logged it."""

    id: str
    model: str
    usage: dict
    first_ts: float
    last_ts: float
    request_ref: str | None
    # The API's `diagnostics.cache_miss_reason.type`, sent on some responses only
    diagnosis: str | None
    # A `compact_boundary` came between this response and the one before it
    after_compact: bool
    # A `forkedFrom` copy of another session's response
    copied: bool
    finished: bool


@dataclass(frozen=True)
class Log:
    """What one transcript contributes."""

    responses: list[Response]
    # api-request id -> (shapeHash, params, cache TTLs requested)
    requests: dict[str, tuple]
    # Each `cost-state` record and the latest timestamp logged before it
    cost_states: list[tuple[dict, float | None]]


@dataclass(frozen=True)
class Priced:
    """An owned response: its price and what it did to the cache."""

    response: Response
    tokens: Tokens
    cost: dict[str, float]
    # cold | uncached | hit | expected | miss, as cc's ledger names them
    outcome: str
    # A miss's re-written prefix, and what writing it cost over reading it
    rewritten: int = 0
    premium: float = 0.0
    cause: str = ""
    gap: float = 0.0

    @property
    def total(self) -> float:
        return sum(self.cost.values())


@dataclass(frozen=True)
class Agent:
    id: str  # "main" for the main transcript
    path: Path
    meta: dict
    parent: str | None
    depth: int
    priced: list[Priced] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.id == "main":
            return "main"
        kind = self.meta.get("agentType", "?")
        if kind == "workflow-subagent":
            return f"{self.id[:8]} workflow {self.path.parent.name}"
        desc = self.meta.get("description")
        return f"{self.id[:8]} {kind}" + (f": {desc}" if desc else "")


@dataclass(frozen=True)
class Session:
    main: Path
    agents: list[Agent]
    # The main transcript's `cost-state` records, oldest first: cc's running
    # total, written on exit and before /clear, /resume and fork
    cost_states: list[tuple[dict, float | None]]

    @property
    def cost_state(self) -> tuple[dict, float | None] | None:
        return self.cost_states[-1] if self.cost_states else None

    @property
    def cost_state_restarted(self) -> bool:
        """A resume restores cc's total and its startTime; a process that did
        not restore it writes its own, smaller one over it."""
        recs = [r for r, _ in self.cost_states]
        return any(b["startTime"] != a["startTime"] or b["totalCostUSD"] < a["totalCostUSD"]
                   for a, b in zip(recs, recs[1:]))


def ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def read_log(path: Path) -> Log:
    responses: dict[str, Response] = {}
    requests: dict[str, tuple] = {}
    cost_states: list[tuple[dict, float | None]] = []
    last_ts = None
    compact = False
    lines = path.read_bytes().splitlines()
    for i, line in enumerate(lines):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            # cc may be mid-append to the last line; anything else is corrupt
            if i == len(lines) - 1:
                continue
            raise
        kind = rec.get("type")
        if rec.get("timestamp"):
            last_ts = ts(rec["timestamp"])
        if kind == "assistant":
            msg = rec.get("message")
            if not isinstance(msg, dict) or not msg.get("usage") or not msg.get("id"):
                continue
            prior = responses.get(msg["id"])
            if prior:
                # A later line of the same response carries the final usage
                responses[msg["id"]] = Response(
                    prior.id, prior.model, msg["usage"], prior.first_ts, ts(rec["timestamp"]),
                    prior.request_ref, prior.diagnosis, prior.after_compact, prior.copied,
                    msg.get("stop_reason") is not None)
                continue
            reason = (msg.get("diagnostics") or {}).get("cache_miss_reason") or {}
            stamp = ts(rec["timestamp"])
            responses[msg["id"]] = Response(
                msg["id"], msg.get("model") or "", msg["usage"], stamp, stamp, rec.get("requestRef"),
                reason.get("type"), compact, rec.get("forkedFrom") is not None,
                msg.get("stop_reason") is not None)
            compact = False
        elif kind == "system" and rec.get("subtype") == "compact_boundary":
            compact = True
        elif kind == "api-request":
            params = {k: v for k, v in (rec.get("params") or {}).items() if k not in ("model", "max_tokens")}
            ttls = sorted({(c.get("value") or {}).get("ttl") or "5m" for c in rec.get("cacheControl") or []})
            requests[rec["id"]] = (rec.get("shapeHash"), params, ttls)
        elif kind == "cost-state":
            cost_states.append((rec, last_ts))
    return Log(list(responses.values()), requests, cost_states)


def _cause(prev: Response, cur: Response, gap: float, ttl: str, requests: dict[str, tuple]) -> str:
    """Why a miss happened, as far as the transcript shows: what cc's own
    attributor checks first (the request changed), then the TTL, then the API's
    diagnosis when it sent one."""
    if base_model(prev.model) != base_model(cur.model):
        return "model_changed"
    a, b = requests.get(prev.request_ref or ""), requests.get(cur.request_ref or "")
    if a and b:
        if a[0] != b[0]:
            return "system_or_tools_changed"
        changed = sorted(k for k in a[1].keys() | b[1].keys() if a[1].get(k) != b[1].get(k))
        if a[2] != b[2]:
            changed.append("cache_ttl")
        if changed:
            return "request_changed:" + ",".join(changed)
    if gap > SECONDS[ttl]:
        return f"ttl_expired_{ttl}"
    return cur.diagnosis or "likely_server_side"


def judge(responses: list[Response], owned: set[str], requests: dict[str, tuple]) -> list[Priced]:
    """Price the owned responses and classify each against the response before
    it in the same conversation, by cc's ledger rule."""
    out: list[Priced] = []
    prev: tuple[Response, Tokens] | None = None
    # cc's TTL for an entry: the last response that wrote decides, 5m by default
    ttl = "5m"
    for r in responses:
        t = Tokens.of(r.usage)
        if t.prompt + t.out == 0:
            continue  # `<synthetic>` records: cc-written errors, never billed
        if r.id in owned:
            cost = price(r.model, r.usage)
            if prev is None or not prev[1].cached:
                out.append(Priced(r, t, cost, "cold" if t.cached else "uncached"))
            else:
                (p, pt), gap = prev, r.last_ts - prev[0].last_ts
                short = min(pt.prompt, t.prompt) - t.rd
                if t.rd >= (t.rd + short) * MISS_RATIO or short < MISS_MIN_TOKENS:
                    out.append(Priced(r, t, cost, "hit", gap=gap))
                elif r.after_compact and gap < SECONDS[ttl]:
                    out.append(Priced(r, t, cost, "expected", gap=gap))
                else:
                    rw = min(short, t.cw)
                    rt = rates(r.model, t, r.usage.get("speed") == "fast", r.usage.get("inference_geo") == "us")
                    write = (rt["w5"] * t.w5 + rt["w1h"] * t.w1h) / t.cw if t.cw else rt["w5" if ttl == "5m" else "w1h"]
                    out.append(Priced(r, t, cost, "miss", rw, rw * (write - rt["rd"]),
                                      _cause(p, r, gap, ttl, requests), gap))
        ttl = "5m" if t.w5 else "1h" if t.w1h else ttl
        prev = (r, t)
    return out


def session_paths(target: Path) -> tuple[Path, Path]:
    """The main transcript and session directory for a main or subagent transcript."""
    if "subagents" in target.parts:
        parts = target.parts
        session_dir = Path(*parts[: len(parts) - 1 - parts[::-1].index("subagents")])
        return session_dir.with_suffix(".jsonl"), session_dir
    return target, target.with_suffix("")


def load(target: Path) -> Session:
    main, session_dir = session_paths(target)
    if not main.is_file():
        raise FileNotFoundError(f"main transcript {main} not found (from {target})")
    files = [("main", main, {}, None, 0)]
    for p in session_dir.glob("subagents/**/agent-*.jsonl"):
        agent_id = p.stem.removeprefix("agent-")
        # cc 2.1.87 logged compaction and /btw forks as agent-acompact-* and
        # agent-aside_question-* with no meta; older metas have no spawnDepth
        mp = p.with_suffix(".meta.json")
        meta = json.loads(mp.read_text()) if mp.is_file() else {}
        files.append((agent_id, p, meta, meta.get("parentAgentId") or "main", meta.get("spawnDepth", 1)))
    # Shallowest first, so a fork's copies of its parent's records are already owned
    files.sort(key=lambda f: (f[4], str(f[1])))
    logs = [read_log(f[1]) for f in files]
    requests = {k: v for log in logs for k, v in log.requests.items()}
    known = {f[0] for f in files}
    seen: set[str] = set()
    agents = []
    for (agent_id, path, meta, parent, depth), log in zip(files, logs):
        if parent is not None and parent not in known:
            raise ValueError(f"{path}: parentAgentId {parent} has no transcript in {session_dir}")
        owned = {r.id for r in log.responses if r.id not in seen and not r.copied}
        seen |= {r.id for r in log.responses}
        agents.append(Agent(agent_id, path, meta, parent, depth, judge(log.responses, owned, requests)))
    return Session(main, agents, logs[0].cost_states)


def tree(session: Session, root: str = "main") -> list[tuple[Agent, int]]:
    """`root` and its descendants with their level below it, each parent before
    its children, siblings by first request."""
    children: dict[str | None, list[Agent]] = {}
    for a in session.agents:
        children.setdefault(a.parent, []).append(a)
    start = {a.id: min((p.response.first_ts for p in a.priced), default=float("inf")) for a in session.agents}
    by_id = {a.id: a for a in session.agents}
    out: list[tuple[Agent, int]] = []

    def walk(a: Agent, level: int) -> None:
        out.append((a, level))
        for c in sorted(children.get(a.id, []), key=lambda c: (start[c.id], c.id)):
            walk(c, level + 1)

    walk(by_id[root], 0)
    return out


@dataclass(frozen=True)
class Stats:
    """Totals over a set of priced responses."""

    requests: int
    cost: dict[str, float]
    prompt: int
    read: int
    misses: list[Priced]
    expected: int
    cold: int
    unfinished: list[Priced]

    @classmethod
    def of(cls, priced: list[Priced]) -> Stats:
        cost: Counter[str] = Counter()
        for p in priced:
            cost.update(p.cost)
        return cls(len(priced), dict(cost), sum(p.tokens.prompt for p in priced),
                   sum(p.tokens.rd for p in priced), [p for p in priced if p.outcome == "miss"],
                   sum(p.outcome == "expected" for p in priced), sum(p.outcome == "cold" for p in priced),
                   [p for p in priced if not p.response.finished])

    @property
    def total(self) -> float:
        return sum(self.cost.values())

    @property
    def hit_ratio(self) -> float | None:
        """cc's `hit_ratio`: cache read over the whole prompt, summed."""
        return self.read / self.prompt if self.prompt else None

    @property
    def unfinished_total(self) -> float:
        return sum(p.total for p in self.unfinished)

    @property
    def premium(self) -> float:
        return sum(p.premium for p in self.misses)

    @property
    def last_miss(self) -> Priced | None:
        return max(self.misses, key=lambda p: p.response.last_ts, default=None)

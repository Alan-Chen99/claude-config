"""What Claude Code charges for one API response, from the `usage` it logs.

Mirrors cc 2.1.310's own pricing (`Jvt`, beside the literal "model catalog
entry '${e}' has incomplete pricing"), so a session total here agrees with cc's
`total_cost_usd` up to the requests cc never transcribes. Stdlib only: the
status line imports it on every refresh.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# cc 2.1.310's model catalog `pricing_tiers` (literal `tier_2_10_cache_read_0_10`),
# $/Mtok. Per-model prices rather than ratios: cache read is 0.1x input on most
# models but 0.05x on the newest, and a session mixes models. A tier's `long`
# replaces it for a response whose prompt (uncached input, cache read and cache
# write) is over `above` tokens.
TIERS = {
    "t2_10": dict(inp=2, out=10, w5=2.5, w1h=4, rd=0.2),
    "t2_10r": dict(inp=2, out=10, w5=2.5, w1h=4, rd=0.1),
    "t3_15": dict(inp=3, out=15, w5=3.75, w1h=6, rd=0.3),
    "t5_25": dict(inp=5, out=25, w5=6.25, w1h=10, rd=0.5),
    "t15_75": dict(inp=15, out=75, w5=18.75, w1h=30, rd=1.5),
    "t10_50": dict(inp=10, out=50, w5=12.5, w1h=20, rd=1),
    "t10_50r": dict(inp=10, out=50, w5=12.5, w1h=20, rd=0.25),
    "t4_20r": dict(inp=4, out=20, w5=5, w1h=8, rd=0.2),
    "h35": dict(inp=0.8, out=4, w5=1, w1h=1.6, rd=0.08),
    "h45": dict(inp=1, out=5, w5=1.25, w1h=2, rd=0.1),
    "h55": dict(inp=0.1, out=0.5, w5=0.125, w1h=0.2, rd=0.01,
                long=dict(above=100_000, inp=0.5, out=2.5, w5=0.625, w1h=1, rd=0.05)),
}
MODELS = {
    "claude-3-5-haiku": "h35", "claude-haiku-4-5": "h45", "claude-haiku-5-5": "h55",
    "claude-3-5-sonnet": "t3_15", "claude-3-7-sonnet": "t3_15",
    "claude-sonnet-4-0": "t3_15", "claude-sonnet-4-5": "t3_15", "claude-sonnet-4-6": "t3_15",
    "claude-sonnet-5": "t2_10", "claude-sonnet-5-5": "t2_10r",
    "claude-opus-4-0": "t15_75", "claude-opus-4-1": "t15_75",
    "claude-opus-4-5": "t5_25", "claude-opus-4-6": "t5_25", "claude-opus-4-7": "t5_25",
    "claude-opus-4-8": "t5_25", "claude-opus-5": "t5_25", "claude-opus-5-5": "t4_20r",
    "claude-fable-5": "t10_50", "claude-fable-5-1": "t10_50r",
    "claude-mythos-5": "t10_50", "claude-mythos-5-1": "t10_50r",
}
# A model missing from MODELS is priced as cc prices one it cannot find when the
# main-loop model is unknown too
UNKNOWN_TIER = "t5_25"
# `speed: "fast"` swaps in a fixed table (`R2t`, beside `promptCacheWrite1hTokens: 10`):
# every token rate times this, web search unchanged; models absent here have no
# fast table and keep their normal price
FAST = {"claude-opus-4-6": 6, "claude-opus-4-7": 6, "claude-opus-4-8": 2, "claude-opus-5": 2,
        "claude-opus-5-5": 2}
US_GEO = 1.1
WEB_SEARCH = 0.01
CATEGORIES = ("inp", "out", "w5", "w1h", "rd", "web")
SECONDS = {"5m": 300, "1h": 3600}


@dataclass(frozen=True)
class Tokens:
    """One response's token counts, with the cache write split by TTL."""

    inp: int
    out: int
    w5: int
    w1h: int
    rd: int

    @classmethod
    def of(cls, u: dict) -> Tokens:
        cw = u.get("cache_creation_input_tokens") or 0
        # cc derives 5m as the total minus 1h and never reads ephemeral_5m
        w1h = min((u.get("cache_creation") or {}).get("ephemeral_1h_input_tokens") or 0, cw)
        return cls(u.get("input_tokens") or 0, u.get("output_tokens") or 0, cw - w1h, w1h,
                   u.get("cache_read_input_tokens") or 0)

    @property
    def cw(self) -> int:
        return self.w5 + self.w1h

    @property
    def prompt(self) -> int:
        return self.inp + self.rd + self.cw

    @property
    def cached(self) -> int:
        return self.rd + self.cw


def base_model(model: str) -> str:
    return re.sub(r"-\d{8}$", "", model)


def rates(model: str, t: Tokens, fast: bool = False, us: bool = False) -> dict[str, float]:
    """$/token for each token category of one response."""
    m = base_model(model)
    p = TIERS[MODELS.get(m, UNKNOWN_TIER)]
    if "long" in p and t.prompt > p["long"]["above"]:
        p = p["long"]
    k = (FAST.get(m, 1) if fast else 1) * (US_GEO if us else 1) / 1e6
    return {c: p[c] * k for c in ("inp", "out", "w5", "w1h", "rd")}


def _priced(model: str, t: Tokens, fast: bool, us: bool) -> dict[str, float]:
    r = rates(model, t, fast, us)
    return {"inp": t.inp * r["inp"], "out": t.out * r["out"], "w5": t.w5 * r["w5"],
            "w1h": t.w1h * r["w1h"], "rd": t.rd * r["rd"], "web": 0.0}


def price(model: str, u: dict) -> dict[str, float]:
    """Dollars per category for one response's `usage`, as cc prices it.

    Raises on a usage shape whose price cc 2.1.310 does not settle or that has
    not been checked against it, rather than guessing a number."""
    if u.get("service_tier") not in (None, "standard"):
        raise ValueError(f"{model}: usage.service_tier={u['service_tier']!r} has no modelled price")
    if u.get("fallback_credit") is not None:
        raise ValueError(f"{model}: usage.fallback_credit={u['fallback_credit']!r} has no modelled price")
    tools = {k: v for k, v in (u.get("server_tool_use") or {}).items() if v}
    if set(tools) - {"web_search_requests", "web_fetch_requests"}:
        raise ValueError(f"{model}: usage.server_tool_use {tools} has no modelled price")
    cost = _priced(model, Tokens.of(u), u.get("speed") == "fast", u.get("inference_geo") == "us")
    # cc adds web search after the geo multiplier; web fetch costs only its tokens
    cost["web"] = tools.get("web_search_requests", 0) * WEB_SEARCH
    for it in u.get("iterations") or []:
        kind = it.get("type")
        if kind == "message":
            continue  # the top-level usage already carries it
        if kind != "advisor_message":
            # cc prices `fallback_message` per attempt only under a refusal
            # fallback the transcript cannot show; others it does not price
            raise ValueError(f"{model}: usage.iterations type {kind!r} has no modelled price")
        # cc (`CJe`) prices each advisor turn on its own model, with no speed,
        # geo or server tools, on top of the response
        for c, v in _priced(it["model"], Tokens.of(it), False, False).items():
            cost[c] += v
    return cost

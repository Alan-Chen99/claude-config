"""`agent-tools cc-cost` on session dirs laid out as cc writes them.

Prices are hand-computed from cc 2.1.310's tiers ($/Mtok): opus-4-8 is
5 in / 25 out / 6.25 write 5m / 10 write 1h / 0.5 read.
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from claude_config.cc_cost.pricing import price
from claude_config.cc_cost.session import load

T0 = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
OPUS = "claude-opus-4-8"


def at(minutes):
    return (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def asst(msg_id, minute=0, model=OPUS, stop="end_turn", ref=None, diag=None, forked=None, **usage):
    msg = {"id": msg_id, "model": model, "usage": usage, "stop_reason": stop}
    if diag:
        msg["diagnostics"] = {"cache_miss_reason": {"type": diag}}
    return {"type": "assistant", "timestamp": at(minute), "message": msg, "requestRef": ref,
            "forkedFrom": forked}


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


def layout(root, main, agents=()):
    """`agents`: (id, records, meta) under the session's subagents dir."""
    proj = root / "projects" / "-proj"
    write(proj / "sid-1.jsonl", main)
    for agent_id, records, meta in agents:
        sub = proj / "sid-1" / "subagents" / f"agent-{agent_id}.jsonl"
        write(sub, records)
        sub.with_suffix(".meta.json").write_text(json.dumps(meta))
    return proj / "sid-1.jsonl"


def cc_cost(root, *args, check=True):
    r = subprocess.run([sys.executable, "-m", "claude_config.cc_cost.main", *args], capture_output=True,
                       text=True, env={"PATH": "/nonexistent", "TZ": "UTC", "CLAUDE_CONFIG_DIR": str(root)})
    if check:
        assert r.returncode == 0, r.stderr
    return r


def report(root, *args):
    return json.loads(cc_cost(root, *args, "--json").stdout)


# 100000 written at 5m: $0.625
WRITE = dict(input_tokens=0, output_tokens=0, cache_creation_input_tokens=100000)
# The same prefix read back, 1000 more written: $0.05 + $0.00625
READ = dict(input_tokens=0, output_tokens=0, cache_read_input_tokens=100000, cache_creation_input_tokens=1000)


def test_a_fork_owns_only_its_own_requests_and_nests_under_its_parent(tmp_path):
    parent = [asst("p1", 0, **WRITE), asst("p2", 1, **READ)]
    # A fork's transcript opens with its parent's records, re-stamped as its own
    fork = parent + [asst("f1", 2, input_tokens=0, output_tokens=1000, cache_read_input_tokens=101000)]
    layout(tmp_path, [asst("m1", 0, input_tokens=1000, output_tokens=0)], [
        ("aparent", parent, {"agentType": "general-purpose", "description": "work", "spawnDepth": 1}),
        ("afork", fork, {"agentType": "fork", "isFork": True, "parentAgentId": "aparent", "spawnDepth": 2}),
    ])
    r = report(tmp_path, "sid-1")
    by = {a["id"]: a for a in r["agents"]}
    assert [(a["id"], a["level"]) for a in r["agents"]] == [("main", 0), ("aparent", 1), ("afork", 2)]
    assert round(by["main"]["total"], 6) == 0.005
    assert round(by["aparent"]["total"], 6) == 0.68125
    # 101000*0.5 + 1000*25: the fork read its parent's cache, a hit
    assert round(by["afork"]["total"], 6) == 0.0755
    assert (by["afork"]["requests"], by["afork"]["misses"], by["afork"]["cold"]) == (1, 0, 0)
    assert round(r["total"]["total"], 6) == 0.76175


def test_each_agent_reports_the_context_it_ended_on(tmp_path):
    main = [asst("m1", 0, **WRITE),
            {"type": "system", "subtype": "compact_boundary", "timestamp": at(1)},
            # Compaction shrank it: the last response's context, not the largest
            asst("m2", 1, input_tokens=0, output_tokens=500, cache_creation_input_tokens=20000)]
    sub = [asst("s1", 0, **WRITE), asst("s2", 1, input_tokens=300, output_tokens=2000,
                                        cache_read_input_tokens=100000, cache_creation_input_tokens=1000)]
    layout(tmp_path, main, [("asub", sub, {"agentType": "Explore", "description": "look"})])
    assert {a["id"]: a["context"] for a in report(tmp_path, "sid-1")["agents"]} == {"main": 20500, "asub": 103300}
    out = cc_cost(tmp_path, "sid-1").stdout
    # model, reqs, then ctx; the total row has none, its input cost follows reqs
    assert re.search(rf"^main +{OPUS} +2 +20K +0\.00 ", out, re.M), out
    assert re.search(rf"^  asub Explore: look +{OPUS} +2 +103K +0\.00 ", out, re.M), out
    assert re.search(r"^total +4 +0\.00 ", out, re.M), out


def test_each_agent_names_the_models_it_ran_on_most_requests_first(tmp_path):
    # A refusal fallback or /model switch mid-session: opus-4-8 first, opus-5-5 more often
    main = [asst("m1", 0, **WRITE), asst("m2", 1, model="claude-opus-5-5", **WRITE),
            asst("m3", 2, model="claude-opus-5-5", **READ)]
    haiku = "claude-haiku-4-5-20251001"
    layout(tmp_path, main, [
        ("asub", [asst("s1", 0, model=haiku, **WRITE)], {"agentType": "Explore", "description": "look"}),
        # Only copies of main's records: it owns no response, so ran on no model of its own
        ("afork", main[:1], {"agentType": "fork", "isFork": True, "spawnDepth": 1}),
    ])
    assert {a["id"]: a["models"] for a in report(tmp_path, "sid-1")["agents"]} == {
        "main": ["claude-opus-5-5", OPUS], "asub": [haiku], "afork": []}
    out = cc_cost(tmp_path, "sid-1").stdout
    assert re.search(r"^agent \(\$\) +model +reqs ", out, re.M), out
    assert re.search(rf"^main +claude-opus-5-5,{OPUS} +3 +101K ", out, re.M), out
    assert re.search(rf"^  asub Explore: look +{haiku} +1 +100K ", out, re.M), out
    assert re.search(r"^  afork fork +- +0 +- ", out, re.M), out
    assert re.search(r"^total +4 +0\.00 ", out, re.M), out


def test_the_miss_list_keeps_its_columns_under_a_dated_model_id(tmp_path):
    haiku = "claude-haiku-4-5-20251001"
    # Six minutes on, the 5m entry lapsed: m2 re-writes all 100000
    layout(tmp_path, [asst("m1", 0, model=haiku, **WRITE), asst("m2", 6, model=haiku, **WRITE)])
    lines = cc_cost(tmp_path, "sid-1", "--misses").stdout.splitlines()
    head = next(line for line in lines if line.startswith("time "))
    miss = next(line for line in lines if line.startswith("2026") and haiku in line)
    assert miss.index("100,000") + len("100,000") == head.index("rewritten") + len("rewritten"), lines


def test_a_forked_sessions_copies_belong_to_its_origin(tmp_path):
    origin = {"sessionId": "other", "messageUuid": "u"}
    layout(tmp_path, [asst("o1", 0, forked=origin, **WRITE), asst("n1", 1, **READ)])
    r = report(tmp_path, "sid-1")
    # Only n1 is this session's, and it hit the prefix o1 cached
    assert (r["total"]["requests"], round(r["total"]["total"], 6), r["total"]["misses"]) == (1, 0.05625, 0)


def test_misses_follow_ccs_rule_and_name_their_cause(tmp_path):
    shape = lambda rid, h, effort="high": {"type": "api-request", "id": rid, "shapeHash": h,
                                           "params": {"model": OPUS, "output_config": {"effort": effort}},
                                           "cacheControl": [{"value": {"type": "ephemeral"}}]}
    main = [
        shape("r1", "A"), asst("m1", 0, ref="r1", **WRITE),
        # Six minutes on: the 5m entry lapsed
        shape("r2", "A"), asst("m2", 6, ref="r2", diag="previous_message_not_found", **WRITE),
        # Read 94000 of 100000: over 5% and 2000 short, a miss; the system prompt changed
        shape("r3", "B"), asst("m3", 7, ref="r3", input_tokens=0, output_tokens=0,
                               cache_read_input_tokens=94000, cache_creation_input_tokens=6000),
        # A 30000 prompt reading 28100: over 5% short, but under cc's 2000-token floor, a hit
        shape("r4", "B"), asst("m4", 8, ref="r4", input_tokens=0, output_tokens=0,
                               cache_read_input_tokens=28100, cache_creation_input_tokens=1900),
        # Same shape, effort changed
        shape("r5", "B", "low"), asst("m5", 9, ref="r5", **WRITE),
        # Within the TTL, nothing changed, the API diagnosed it
        shape("r6", "B", "low"), asst("m6", 10, ref="r6", diag="unavailable", **WRITE),
        asst("m7", 11, model="claude-opus-5", **WRITE),
        asst("m8", 12, model="claude-opus-5", **WRITE),
        # A rebuild right after compaction is expected
        {"type": "system", "subtype": "compact_boundary", "timestamp": at(13)},
        asst("m9", 13, model="claude-opus-5", **WRITE),
    ]
    layout(tmp_path, main)
    r = report(tmp_path, "sid-1")
    assert [(m["message_id"], m["cause"]) for m in r["misses"]] == [
        ("m2", "ttl_expired_5m"), ("m3", "system_or_tools_changed"), ("m5", "request_changed:output_config"),
        ("m6", "unavailable"), ("m7", "model_changed"), ("m8", "likely_server_side")]
    assert (r["total"]["cold"], r["total"]["expected"]) == (1, 1)
    # m2 re-wrote 100000 at 6.25 that a hit reads at 0.5; m3 re-wrote 6000
    m2, m3 = r["misses"][0], r["misses"][1]
    assert (m2["rewritten"], round(m2["premium"], 6)) == (100000, 0.575)
    assert (m3["rewritten"], round(m3["premium"], 6)) == (6000, 0.0345)


def test_the_text_report_compares_against_ccs_total_up_to_when_cc_wrote_it(tmp_path):
    state = {"type": "cost-state", "totalCostUSD": 1.0, "startTime": 1, "modelUsage": {OPUS: {"costUSD": 1.0}}}
    layout(tmp_path, [asst("m1", 0, **WRITE), state, asst("m2", 1, **READ),
                      asst("m3", 2, stop=None, input_tokens=0, output_tokens=8, cache_read_input_tokens=101000)])
    out = cc_cost(tmp_path, "sid-1", "--misses").stdout
    assert "cc's total $1.00 when it last wrote cost-state (2026-10-26 12:00 UTC); traced to then $0.62; " \
           "untraced $0.38 (38%); 1 responses since" in out, out
    assert "1 unfinished responses (interrupted, or still streaming): $0.05" in out, out


def test_a_restarted_cost_state_is_not_compared(tmp_path):
    states = [{"type": "cost-state", "totalCostUSD": t, "startTime": s, "modelUsage": {}}
              for t, s in ((5.0, 1), (0.5, 2))]
    layout(tmp_path, [asst("m1", 0, **WRITE), *states])
    out = cc_cost(tmp_path, "sid-1").stdout
    assert "cc's cost-state restarted ($5.00 → $0.50" in out and "traced to then" not in out, out


def test_a_subagent_id_reports_it_and_its_children(tmp_path):
    layout(tmp_path, [asst("m1", 0, **WRITE)], [
        ("aone", [asst("a1", 0, **WRITE)], {"agentType": "general-purpose", "description": "one"}),
        ("atwo", [asst("b1", 0, **WRITE)], {"agentType": "Explore", "parentAgentId": "aone", "spawnDepth": 2}),
        ("athree", [asst("c1", 0, **WRITE)], {"agentType": "Explore"}),
    ])
    r = report(tmp_path, "agent-aone")
    assert [a["id"] for a in r["agents"]] == ["aone", "atwo"] and "cost_state" not in r
    assert cc_cost(tmp_path, "aone").stdout.startswith("agent aone general-purpose: one in session sid-1")


def test_an_advisor_turn_is_priced_on_its_own_model(tmp_path):
    advisor = {"type": "advisor_message", "model": "claude-fable-5", "input_tokens": 1000, "output_tokens": 100}
    layout(tmp_path, [asst("m1", 0, input_tokens=1000, output_tokens=0,
                           iterations=[{"type": "message", "input_tokens": 1000}, advisor])])
    # 1000*5 for the response, 1000*10 + 100*50 for the fable-5 advisor
    assert round(report(tmp_path, "sid-1")["total"]["total"], 6) == 0.02


def test_an_unmodelled_price_fails_loudly(tmp_path):
    fallback = {"type": "fallback_message", "model": "claude-opus-5", "input_tokens": 10}
    layout(tmp_path, [asst("m1", 0, input_tokens=10, output_tokens=0, iterations=[fallback])])
    r = cc_cost(tmp_path, "sid-1", check=False)
    assert r.returncode != 0 and "Traceback" in r.stderr and "'fallback_message' has no modelled price" in r.stderr


def test_an_unknown_id_names_where_it_searched(tmp_path):
    layout(tmp_path, [asst("m1", 0, **WRITE)])
    r = cc_cost(tmp_path, "nope", check=False)
    assert r.returncode == 1 and f"searched {tmp_path}/projects" in r.stderr


usage = st.fixed_dictionaries({
    "input_tokens": st.integers(0, 5000), "output_tokens": st.integers(0, 5000),
    "cache_read_input_tokens": st.integers(0, 300000), "cache_creation_input_tokens": st.integers(0, 50000),
})


@settings(max_examples=60, deadline=None)
@given(main=st.lists(usage, min_size=1, max_size=8), sub=st.lists(usage, max_size=6),
       fork_at=st.integers(0, 8), dup=st.lists(st.booleans(), min_size=14, max_size=14))
def test_block_lines_and_fork_copies_never_change_the_total(tmp_path_factory, main, sub, fork_at, dup):
    """A response logged once per content block, earlier lines carrying a
    partial output, and a fork opening with copies of its parent's records:
    each response is still priced once, at its final usage."""
    root = tmp_path_factory.mktemp("s")
    main_recs = [asst(f"m{i}", i, **u) for i, u in enumerate(main)]
    sub_recs = [asst(f"s{i}", i, **u) for i, u in enumerate(sub)]
    expected = sum(sum(price(OPUS, u).values()) for u in main + sub)

    def logged(recs):
        out = []
        for r, d in zip(recs, dup):
            if d:
                early = json.loads(json.dumps(r))
                early["message"]["usage"]["output_tokens"] = 1
                early["message"]["stop_reason"] = None
                out.append(early)
            out.append(r)
        return out + recs[len(dup):]

    fork = main_recs[:fork_at] + [asst("f0", 20, **main[0])]
    path = layout(root, logged(main_recs), [
        ("asub", logged(sub_recs), {"agentType": "general-purpose"}),
        ("afork", fork, {"agentType": "fork", "isFork": True, "spawnDepth": 1}),
    ])
    session = load(path)
    totals = {a.id: sum(p.total for p in a.priced) for a in session.agents}
    expected_fork = sum(price(OPUS, main[0]).values())
    assert abs(totals["main"] + totals["asub"] - expected) < 1e-9
    assert abs(totals["afork"] - expected_fork) < 1e-9
    assert all(p.response.finished for a in session.agents for p in a.priced)


def test_the_cli_resolves_the_running_session_by_default(tmp_path):
    layout(tmp_path, [asst("m1", 0, **WRITE)])
    r = subprocess.run([sys.executable, "-m", "claude_config.cc_cost.main", "--json"], capture_output=True,
                       text=True, check=True,
                       env={"PATH": "/nonexistent", "CLAUDE_CONFIG_DIR": str(tmp_path),
                            "CLAUDE_CODE_SESSION_ID": "sid-1"})
    assert json.loads(r.stdout)["main"] == str(Path(tmp_path, "projects", "-proj", "sid-1.jsonl"))

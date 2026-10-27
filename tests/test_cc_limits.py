"""`cc-cost --limits` over a HOME of transcripts and logged readings, as the
status line leaves them; `ticks` against generated sightings."""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from hypothesis import given
from hypothesis import strategies as st

from claude_config.cc_cost.limits import ticks

T0 = datetime(2026, 10, 20, 10, tzinfo=timezone.utc)
R5, R5B, R7 = (int((T0 + d).timestamp()) for d in (timedelta(hours=4), timedelta(hours=2), timedelta(days=3)))
A, B = "a@example.com", "b@example.com"


def r(x):
    return round(x, 9)


def at(minutes):
    return T0 + timedelta(minutes=minutes)


def context(email, minutes=-90):
    return {"type": "attachment", "timestamp": at(minutes).isoformat(), "attachment": {
        "type": "session_context", "context": {"userEmail": f"The user's email address is {email}. Use it only…"}}}


def response(msg_id, minutes, model="claude-opus-4-8"):
    # 100000 1h cache-write tokens: $1.00 on opus-4-8 (tier 5/25, 1h write 10 $/Mtok), $0.40 on sonnet-5-5
    return {"type": "assistant", "timestamp": at(minutes).isoformat(), "message": {
        "id": msg_id, "model": model, "stop_reason": "end_turn",
        "usage": {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 100000,
                  "cache_creation": {"ephemeral_1h_input_tokens": 100000}}}}


def reading(minutes, sid, home, five=None, seven=None, account=A, resets5=R5):
    r = {"ts": at(minutes).timestamp(), "session": sid, "account": account, "tier": "default_claude_max_20x",
         "transcript": str(home / ".claude/projects/p" / f"{sid}.jsonl")}
    if five is not None:
        r["five_hour"] = {"used_percentage": five, "resets_at": resets5}
    if seven is not None:
        r["seven_day"] = {"used_percentage": seven, "resets_at": R7}
    return r


def build(home):
    proj = home / ".claude/projects/p"
    proj.mkdir(parents=True)
    sessions = {
        # account A over two sessions. s1's m0..m4 carry its readings, each
        # logged half a minute after; x0, before the first, counts nowhere
        "s1": [context(A), response("x0", -60), *(response(f"m{i}", 10 * i) for i in range(5)),
               response("a3", 22), response("a4", 23)],
        "s4": [context(A), response("b1", 16), response("b2", 24), response("b3", 25)],
        # A reading logged before the session's first transcribed response
        "s5": [context(A), response("e1", 50)],
        # Idle since -30, its status line re-rendered at 60: its reading is from -30
        "s6": [context(A), response("f1", -30)],
        # account B, logged while cc's global config named A; its model has no credit rate
        "s2": [context(B), response("c0", 0, "claude-sonnet-5-5"), response("c1", 10, "claude-sonnet-5-5")],
        # no session_context: attributed to no account
        "s3": [response("d1", 10)],
    }
    for sid, recs in sessions.items():
        (proj / f"{sid}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs))
    log = [
        reading(0.5, "s1", home, five=10, seven=20),
        reading(10.5, "s1", home, five=11),
        reading(20.5, "s1", home, five=13),
        reading(25.5, "s4", home, five=12),  # first seen after 13 was: no tick
        reading(30.5, "s1", home, five=15, seven=21),
        reading(40.5, "s1", home, five=100),  # capped: the interval into it is dropped
        # an idle session re-rendering, an hour on: still dated by its last response
        reading(70, "s4", home, five=11),
        reading(45, "s5", home, five=16),
        reading(60, "s6", home, five=8),
        reading(0.5, "s2", home, five=50, resets5=R5B),
        reading(20.5, "s2", home, five=51, resets5=R5B),
        reading(5, "gone", home, five=11),
    ]
    (home / ".claude/cc-cost").mkdir()
    (home / ".claude/cc-cost/rate-limits.jsonl").write_text("".join(json.dumps(r) + "\n" for r in log))
    (home / ".claude.json").write_text(json.dumps({
        "oauthAccount": {"emailAddress": A, "organizationRateLimitTier": "default_claude_max_20x"},
        "cachedGrowthBookFeatures": {"tengu_amber_tally": {
            "fiveHourCredits": {"default_claude_max_20x": 200000}, "creditsPerMillionTokens": {"claude-opus-4-8": 2750}}}}))


def limits(home, *args):
    r = subprocess.run([sys.executable, "-m", "claude_config.cc_cost.main", "--limits", "--span", "2", *args],
                       capture_output=True, text=True, env={"HOME": str(home), "TZ": "UTC", "PATH": "/usr/bin:/bin"})
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_cost_per_point_between_ticks_per_account(tmp_path):
    build(tmp_path)
    a = json.loads(limits(tmp_path, "--json"))
    five = a["accounts"][A]["windows"]["5h"]
    # 8→10 holds m0 ($1); 10→11 m1 ($1); 11→13 m2 and b1 ($2); 13→15 m3, a3, a4, b2, b3 ($5); 15→100 is capped
    assert [(iv["points"], r(iv["cost"])) for iv in five["intervals"]] == [(2, 1.0), (1, 1.0), (2, 2.0), (2, 5.0)]
    assert five["intervals"][0]["start"] == at(-30).timestamp(), "s6's reading is dated by its last response"
    assert {k: r(v) for k, v in five["intervals"][3]["by_category"].items()} == \
        {"inp": 0, "out": 0, "w5": 0, "w1h": 5.0, "rd": 0, "web": 0}
    assert (r(five["median"]), r(five["max"])) == (1.0, 2.5)
    best = five["best_span"]
    assert (best["start"], best["end"], best["points"], r(best["per_point"])) == \
        (at(20).timestamp(), at(30).timestamp(), 2, 2.5)
    assert r(five["window_estimate"]) == 250
    # $1 = 100000 1h-write tokens = 275 credits at 2750 per million; the flag's window is 2000 per point
    assert r(five["credits_best_span"]["per_point"]) == 687.5 and five["flag_credits_per_point"] == 2000
    seven = a["accounts"][A]["windows"]["7d"]
    assert [(iv["points"], r(iv["cost"])) for iv in seven["intervals"]] == [(1, 8.0)]
    assert seven["best_span"] is None, "one point is shorter than a 2-point span"

    b = a["accounts"][B]
    assert b["tier"] is None, "every reading of B was logged under A's global config"
    assert [(iv["points"], r(iv["cost"]), iv["credits"]) for iv in b["windows"]["5h"]["intervals"]] == [(1, 0.4, None)]
    u = a["unattributed"]
    assert (u["responses"], r(u["cost"]), a["orphaned_readings"], a["unplaced_readings"], a["mismatched_readings"]) \
        == (1, 1.0, 1, 1, 2)
    assert a["models_without_credit_rate"] == ["claude-sonnet-5-5"]


def test_the_report_and_plot(tmp_path):
    build(tmp_path)
    png = tmp_path / "limits.png"
    out = limits(tmp_path, "--plot", str(png))
    assert f"{A}  default_claude_max_20x" in out and f"{B}  tier unknown" in out, out
    five = next(line for line in out.splitlines() if line.startswith("  5h") and "2.50" in line)
    assert "10-20 10:20 → 10-20 10:30" in five and "$250" in five and "688" in five and "2,000" in five, five
    assert "1 responses ($1.00) in sessions cc named no account for" in out
    assert "no creditsPerMillionTokens for claude-sonnet-5-5" in out
    assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


sightings = st.dictionaries(st.integers(0, 100).map(float), st.floats(0, 1e6, allow_nan=False), min_size=1)


@given(sightings)
def test_ticks_rise_in_value_and_time_and_drop_only_late_sightings(seen):
    tk = ticks(seen)
    assert all(v0 < v1 and t0 < t1 for (v0, t0), (v1, t1) in zip(tk, tk[1:]))
    assert all(seen[v] == t for v, t in tk)
    kept = {v for v, _ in tk}
    assert all(any(w > v and seen[w] <= seen[v] for w in seen) for v in seen if v not in kept)

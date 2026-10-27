"""`cc-cost --statusline` run as cc runs it: statusLine JSON on stdin, a session dir on disk.

The child environment is built from scratch so `agent-tools` is off PATH: the
tasks row then has to show its failure marker rather than vanish. Its HOME is
the test's own, so the readings log and cc's global config are too.
"""

import json
import re
import subprocess
import sys

import pytest

ANSI = re.compile(r"\x1b\[[\d;]*m")


def assistant(msg_id, model, ts="2026-10-26T12:00:00.000Z", stop="end_turn", **usage):
    return json.dumps({"type": "assistant", "timestamp": ts,
                       "message": {"id": msg_id, "model": model, "usage": usage, "stop_reason": stop}})


def session(tmp_path, main_lines, sub_lines=(), sub_meta=None):
    transcript = tmp_path / "proj" / "sid.jsonl"
    transcript.parent.mkdir()
    transcript.write_text("\n".join(main_lines) + "\n")
    if sub_lines:
        sub = tmp_path / "proj" / "sid" / "subagents" / "agent-a.jsonl"
        sub.parent.mkdir(parents=True)
        sub.write_text("\n".join(sub_lines) + "\n")
        sub.with_suffix(".meta.json").write_text(json.dumps(sub_meta or {"agentType": "general-purpose"}))
    return transcript


# opus-5-5 (tier_4_20_cache_read_0_20): 10*4 + 1000*20 + 2000*8 (1h) + 10000*0.2 = $0.03804
OPUS = assistant("m1", "claude-opus-5-5", input_tokens=10, output_tokens=1000,
                 cache_creation_input_tokens=2000, cache_read_input_tokens=10000,
                 cache_creation={"ephemeral_1h_input_tokens": 2000, "ephemeral_5m_input_tokens": 0})
# haiku_45, date suffix stripped: 200*5 + 1000*1.25 (5m) = $0.00225
HAIKU = assistant("s1", "claude-haiku-4-5-20251001", input_tokens=0, output_tokens=200,
                  cache_creation_input_tokens=1000, cache_read_input_tokens=0)
TOTAL = 0.04029


def run(transcript, total=TOTAL, config=True, **over):
    home = transcript.parent.parent / "home"
    home.mkdir(exist_ok=True)
    if config and not (home / ".claude.json").exists():
        (home / ".claude.json").write_text(json.dumps({"oauthAccount": {
            "emailAddress": "me@example.com", "organizationRateLimitTier": "default_claude_max_20x"}}))
    data = {"model": {"display_name": "Opus 5.5"}, "effort": {"level": "high"}, "session_name": "name",
            "session_id": "sid", "transcript_path": str(transcript), "cost": {"total_cost_usd": total},
            "context_window": {"used_percentage": 3, "current_usage": {"input_tokens": 29000}}} | over
    r = subprocess.run([sys.executable, "-m", "claude_config.cc_cost.main", "--statusline"],
                       input=json.dumps(data), capture_output=True, text=True,
                       env={"PATH": "/nonexistent", "TZ": "UTC", "HOME": str(home)}, check=True)
    return ANSI.sub("", r.stdout).splitlines(), r.stderr


def test_split_reprices_each_response_once_across_subagents(tmp_path):
    # m1 logged twice (one line per content block) and a half-appended last line
    t = session(tmp_path, [OPUS, OPUS, '{"type":"assistant","message":{"id":"m9"'], [HAIKU])
    rows, err = run(t)
    assert "$0.0403  in 0%   out 52%  wr 43%  rd 5%   other 0%   │" in rows[0], rows[0]
    assert "traced" not in rows[1] and err == ""


def test_cost_no_transcript_records_is_other(tmp_path):
    # $0.06 billed, $0.04029 traced: other = 32.85%; shares are of cc's total
    rows, _ = run(session(tmp_path, [OPUS], [HAIKU]), total=0.06)
    assert "in 0%   out 35%  wr 29%  rd 3%   other 33% " in rows[0], rows[0]
    assert "traced" not in rows[1]


def test_transcripts_above_cc_total_are_flagged(tmp_path):
    rows, _ = run(session(tmp_path, [OPUS], [HAIKU]), total=0.02)
    assert rows[1] == "cache - │ traced 201% │ sid", rows[1]


def test_an_unfinished_response_is_priced_but_not_held_against_cc(tmp_path):
    # cc prices a response when its stream ends, so its total lacks this one
    cut = assistant("m2", "claude-opus-5-5", stop=None, input_tokens=0, output_tokens=0,
                    cache_read_input_tokens=100000)  # 100000*0.2 = $0.02
    rows, _ = run(session(tmp_path, [OPUS, cut]), total=0.03804)
    assert "other 0% " in rows[0] and "traced" not in rows[1], rows
    assert "main   $0.06 " in rows[2], rows[2]


# Each priced alone against a cc total that matches only the tier named:
# another tier leaves an `other` share or flags `traced`.
@pytest.mark.parametrize("line, total", [
    # haiku_55 long_prompt, 1 + 100000 + 1000 prompt tokens over 1e5:
    # 1*0.5 + 100000*0.05 + 1000*1 (1h) = $0.0060005
    (assistant("h1", "claude-haiku-5-5", input_tokens=1, output_tokens=0, cache_read_input_tokens=100000,
               cache_creation_input_tokens=1000, cache_creation={"ephemeral_1h_input_tokens": 1000}), 0.0060005),
    # haiku_55 at exactly 1e5 prompt tokens, not over: 100000*0.01 = $0.001
    (assistant("h2", "claude-haiku-5-5", input_tokens=0, output_tokens=0, cache_read_input_tokens=100000), 0.001),
    # tier_2_10_cache_read_0_10: 100000*0.1 = $0.01
    (assistant("n1", "claude-sonnet-5-5", input_tokens=0, output_tokens=0, cache_read_input_tokens=100000), 0.01),
    # fast opus-4-7 is 30/150 $/Mtok, six times its tier: 1000*30 = $0.03
    (assistant("f1", "claude-opus-4-7", speed="fast", input_tokens=1000, output_tokens=0), 0.03),
    # US inference is 1.1x tokens, web search added after: 1000*5*1.1 + 2*$0.01 = $0.0255
    (assistant("u1", "claude-opus-4-8", inference_geo="us", input_tokens=1000, output_tokens=0,
               server_tool_use={"web_search_requests": 2}), 0.0255),
])
def test_each_response_is_priced_at_its_tier(tmp_path, line, total):
    rows, _ = run(session(tmp_path, [line]), total=total)
    assert "other 0% " in rows[0] and "traced" not in rows[1], rows


def test_an_unknown_model_is_named(tmp_path):
    glm = assistant("g1", "glm-5.3", input_tokens=5, output_tokens=5)
    rows, _ = run(session(tmp_path, [OPUS, glm]))
    assert "unpriced: glm-5.3" in rows[1]


def test_a_corrupt_line_fails_visibly(tmp_path):
    rows, err = run(session(tmp_path, ['{"type":"assistant","message":{"usage": nope', OPUS]))
    assert "cost split ?" in rows[0] and "agents ?" in rows[2] and "Traceback" in err


def test_an_unmodelled_price_fails_visibly(tmp_path):
    priority = assistant("p1", "claude-opus-5-5", service_tier="priority", input_tokens=5, output_tokens=5)
    rows, err = run(session(tmp_path, [priority]))
    assert "cost split ?" in rows[0] and "service_tier='priority'" in err


def test_no_usage_yet(tmp_path):
    rows, _ = run(session(tmp_path, ['{"type":"user"}']))
    assert "cost split -" in rows[0]
    assert rows[2] == "main   $0.00   hit -    miss 0/0     $0.00 ", rows[2]


def test_tasks_failure_is_shown(tmp_path):
    rows, _ = run(session(tmp_path, [OPUS]))
    assert rows[-1] == "▶ ?"


def test_three_rows_hold_both_groups_and_the_last_miss(tmp_path):
    # The subagent reads 1000 of the 100001-token prompt its last request
    # cached six minutes earlier, past the 5m TTL, and re-writes the other
    # 99001: 99001 * (6.25 - 0.5) = $0.569 over reading them. Its two requests
    # cost 1*5 + 100000*6.25 and 1*5 + 1000*0.5 + 99500*6.25: $1.247.
    first = assistant("s1", "claude-opus-4-8", ts="2026-10-26T12:00:00.000Z", input_tokens=1, output_tokens=0,
                      cache_creation_input_tokens=100000)
    lapsed = assistant("s2", "claude-opus-4-8", ts="2026-10-26T12:06:00.000Z", input_tokens=1, output_tokens=0,
                       cache_read_input_tokens=1000, cache_creation_input_tokens=99500)
    limits = {"five_hour": {"used_percentage": 34, "resets_at": 0}, "seven_day": {"used_percentage": 61, "resets_at": 0}}
    pc = {"ttl": "5m", "warm": True, "expires_at": 3600}
    rows, _ = run(session(tmp_path, [OPUS], [first, lapsed]), total=2, rate_limits=limits, prompt_cache=pc)
    assert rows[1:] == [
        "cache 5m warm until 01:00 │ 5h 34%  Thu 00:00 │ 7d 61%  Thu 00:00 │ sid",
        "main   $0.04   hit 83%  miss 0/1     $0.00  │ sub×1  $1.25   hit 0%   miss 1/2     $0.57  │ last miss: sub ttl_expired_5m",
        "▶ ?",  # the tasks row, a fourth only while a wrapped run is live or `agent-tools ps` fails
    ], rows


@pytest.mark.parametrize("main_lapse, shown", [("12:10", "main"), ("12:05:30", "sub")])
def test_the_last_miss_is_the_latest_of_either_group(tmp_path, main_lapse, shown):
    # Both groups' second request outlives a 5m cache: the sub's at 12:06
    def lapse(msg_id, at):
        return assistant(msg_id, "claude-opus-4-8", ts=f"2026-10-26T{at}{':00' if at.count(':') == 1 else ''}.000Z",
                         input_tokens=1, output_tokens=0, cache_read_input_tokens=1000, cache_creation_input_tokens=99500)
    write = lambda msg_id: assistant(msg_id, "claude-opus-4-8", input_tokens=1, output_tokens=0,
                                     cache_creation_input_tokens=100000)
    rows, _ = run(session(tmp_path, [write("m1"), lapse("m2", main_lapse)], [write("s1"), lapse("s2", "12:06")]))
    assert rows[2].endswith(f"│ last miss: {shown} ttl_expired_5m"), rows[2]


def test_cc_names_the_main_threads_last_miss_cause(tmp_path):
    pc = {"ttl": "1h", "warm": True, "expires_at": 3600, "last_miss_cause": {"causes": ["tools_changed"]}}
    rows, _ = run(session(tmp_path, [OPUS]), prompt_cache=pc)
    assert rows[1].startswith("cache 1h warm until 01:00"), rows[1]
    assert rows[2].endswith("│ last miss: main tools_changed"), rows[2]


def test_columns_hold_across_sessions(tmp_path):
    """The model and name start in the same column whatever the context size,
    cost, split or model name, and with no usage yet; so do the main group's
    fields, and the sub group after it."""
    for d in "abc":
        (tmp_path / d).mkdir()
    c, _ = run(session(tmp_path / "c", ['{"type":"user"}']))
    a, _ = run(session(tmp_path / "a", [OPUS]))
    b, _ = run(session(tmp_path / "b", [HAIKU], [OPUS]),
               total=12.5, model={"display_name": "Sonnet 5.5"}, effort={"level": "medium"},
               context_window={"used_percentage": 100, "current_usage": {"input_tokens": 1_000_000}})
    cols = lambda row, pat="│": [m.start() for m in re.finditer(pat, row)]
    assert cols(a[0]) == cols(b[0]) == cols(c[0]), (a[0], b[0], c[0])
    fields = "hit|miss|│"
    assert cols(a[2], fields) == cols(c[2], fields) == cols(b[2], fields)[:2], (a[2], b[2], c[2])
    assert cols(b[2])[0] == len(a[2]) + 1, (a[2], b[2])


def test_a_reading_is_logged_when_it_changes(tmp_path):
    t = session(tmp_path, [OPUS])
    first = {"five_hour": {"used_percentage": 6, "resets_at": 1793089800},
             "seven_day": {"used_percentage": 12, "resets_at": 1793556000}}
    later = first | {"seven_day": {"used_percentage": 13, "resets_at": 1793556000}}
    for rl in (first, first, later):
        rows, err = run(t, rate_limits=rl)
        assert "limits log ?" not in rows[1] and err == "", (rows, err)
    log = [json.loads(line) for line in (tmp_path / "home/.claude/cc-cost/rate-limits.jsonl").read_text().splitlines()]
    assert [(r["session"], r["transcript"], r["account"], r["tier"], r["seven_day"]["used_percentage"]) for r in log] \
        == [("sid", str(t), "me@example.com", "default_claude_max_20x", p) for p in (12, 13)], log


def test_a_failed_log_is_shown(tmp_path):
    rows, err = run(session(tmp_path, [OPUS]), config=False,
                    rate_limits={"five_hour": {"used_percentage": 6, "resets_at": 1793089800}})
    assert "limits log ?" in rows[1] and "Traceback" in err and ".claude.json" in err, (rows, err)

"""statusline.py run as cc runs it: statusLine JSON on stdin, a session dir on disk.

The child environment is built from scratch so `agent-tools` is off PATH: the
tasks row then has to show its failure marker rather than vanish.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "statusline.py"
ANSI = re.compile(r"\x1b\[[\d;]*m")


def assistant(msg_id, model, **usage):
    return json.dumps({"type": "assistant", "message": {"id": msg_id, "model": model, "usage": usage}})


def session(tmp_path, main_lines, sub_lines=()):
    transcript = tmp_path / "proj" / "sid.jsonl"
    transcript.parent.mkdir()
    transcript.write_text("\n".join(main_lines) + "\n")
    if sub_lines:
        sub = tmp_path / "proj" / "sid" / "subagents" / "agent-a.jsonl"
        sub.parent.mkdir(parents=True)
        sub.write_text("\n".join(sub_lines) + "\n")
    return transcript


# opus-5-5 (tier_4_20_cache_read_0_20): 10*4 + 1000*20 + 2000*8 (1h) + 10000*0.2 = $0.03804
OPUS = assistant("m1", "claude-opus-5-5", input_tokens=10, output_tokens=1000,
                 cache_creation_input_tokens=2000, cache_read_input_tokens=10000,
                 cache_creation={"ephemeral_1h_input_tokens": 2000, "ephemeral_5m_input_tokens": 0})
# haiku_45, date suffix stripped: 200*5 + 1000*1.25 (5m) = $0.00225
HAIKU = assistant("s1", "claude-haiku-4-5-20251001", input_tokens=0, output_tokens=200,
                  cache_creation_input_tokens=1000, cache_read_input_tokens=0)
TOTAL = 0.04029


def run(transcript, total=TOTAL, **over):
    data = {"model": {"display_name": "Opus 5.5"}, "effort": {"level": "high"}, "session_name": "name",
            "session_id": "sid", "transcript_path": str(transcript), "cost": {"total_cost_usd": total},
            "context_window": {"used_percentage": 3, "current_usage": {"input_tokens": 29000}}} | over
    r = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps(data), capture_output=True,
                       text=True, env={"PATH": "/nonexistent", "TZ": "UTC"}, check=True)
    return ANSI.sub("", r.stdout).splitlines(), r.stderr


def test_split_reprices_each_response_once_across_subagents(tmp_path):
    # m1 logged twice (one line per content block) and a half-appended last line
    t = session(tmp_path, [OPUS, OPUS, '{"type":"assistant","message":{"id":"m9"'], [HAIKU])
    rows, err = run(t)
    assert "$0.0403  in 0%   out 52%  wr 43%  rd 5%   other 0%   │" in rows[0], rows[0]
    assert "traced" not in rows[2] and err == ""


def test_cost_no_transcript_records_is_other(tmp_path):
    # $0.06 billed, $0.04029 traced: other = 32.85%; shares are of cc's total
    rows, _ = run(session(tmp_path, [OPUS], [HAIKU]), total=0.06)
    assert "in 0%   out 35%  wr 29%  rd 3%   other 33% " in rows[0], rows[0]
    assert "traced" not in rows[2]


def test_transcripts_above_cc_total_are_flagged(tmp_path):
    rows, _ = run(session(tmp_path, [OPUS], [HAIKU]), total=0.02)
    assert rows[2].startswith("traced 201% │ ")


def test_an_unknown_model_is_named(tmp_path):
    glm = assistant("g1", "glm-5.3", input_tokens=5, output_tokens=5)
    rows, _ = run(session(tmp_path, [OPUS, glm]))
    assert "unpriced: glm-5.3" in rows[2]


def test_a_corrupt_line_fails_visibly(tmp_path):
    # Lines without usage are never parsed, so only a usage line can corrupt the split
    rows, err = run(session(tmp_path, ['{"type":"assistant","message":{"usage": nope', OPUS]))
    assert "cost split ?" in rows[0] and "Traceback" in err


def test_no_usage_yet(tmp_path):
    rows, _ = run(session(tmp_path, ['{"type":"user"}']))
    assert "cost split -" in rows[0]


def test_tasks_failure_is_shown(tmp_path):
    rows, _ = run(session(tmp_path, [OPUS]))
    assert rows[-1] == "▶ ?"


def test_columns_hold_across_sessions(tmp_path):
    """The model and name start in the same column whatever the context size,
    cost, split or model name, and with no usage yet."""
    for d in "abc":
        (tmp_path / d).mkdir()
    c, _ = run(session(tmp_path / "c", ['{"type":"user"}']))
    a, _ = run(session(tmp_path / "a", [OPUS]))
    b, _ = run(session(tmp_path / "b", [HAIKU]),
               total=12.5, model={"display_name": "Sonnet 5.5"}, effort={"level": "medium"},
               context_window={"used_percentage": 100, "current_usage": {"input_tokens": 1_000_000}})
    cols = lambda row: [m.start() for m in re.finditer("│", row)]
    assert cols(a[0]) == cols(b[0]) == cols(c[0]), (a[0], b[0], c[0])

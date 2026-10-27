"""Renders show local time, and say once which zone that is.

Every log family stamps UTC; the reader's clock, shell history and commit times
are local. The zone is whatever TZ names, so each test sets it — the C library
reads TZ at ``tzset()``, which is why the setter calls it.
"""

from __future__ import annotations

import io
import json
import os
import time
from contextlib import contextmanager, redirect_stdout
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given, strategies as st

from claude_config.cc_pretty.main import main as cc_main
from claude_config.cc_pretty.render import fmt_ts, fmt_ts_zoned
from claude_config.cc_pretty_intercept.main import main as intercept_main
from claude_config.opencode_pretty.main import main as opencode_main

# Whole-hour and half-hour offsets, both hemispheres' DST, a 30-minute DST
# shift (Lord Howe), a 45-minute offset (Chatham), and no offset at all.
ZONES = ["America/New_York", "Asia/Tokyo", "Asia/Kolkata", "Australia/Lord_Howe",
         "Pacific/Chatham", "America/Sao_Paulo", "Europe/London", "UTC"]

STAMP = "2026-10-27T14:19:25.000Z"


@contextmanager
def local_zone(name: str):
    before = os.environ.get("TZ")
    os.environ["TZ"] = name
    time.tzset()
    try:
        yield
    finally:
        if before is None:
            del os.environ["TZ"]
        else:
            os.environ["TZ"] = before
        time.tzset()


@given(
    instant=st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31),
                         timezones=st.just(UTC)),
    zone=st.sampled_from(ZONES),
)
def test_a_utc_stamp_reads_as_the_zone_s_wall_clock(instant: datetime, zone: str) -> None:
    stamp = instant.isoformat().replace("+00:00", "Z")
    wall = instant.astimezone(ZoneInfo(zone))
    offset = wall.strftime("%z")
    with local_zone(zone):
        assert fmt_ts(stamp) == wall.strftime("%H:%M:%S")
        assert fmt_ts_zoned(stamp) == (
            f"{wall:%Y-%m-%d %H:%M:%S} {wall:%Z} (UTC{offset[:3]}:{offset[3:]})"
        )


def test_an_unparseable_stamp_is_shown_as_it_is_and_vouches_for_no_zone() -> None:
    assert fmt_ts("yesterday-ish") == "yesterday-ish"
    assert fmt_ts("") == ""
    assert fmt_ts_zoned("yesterday-ish") == ""


def render(main, *argv: str) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        main([*argv, "--no-color"])
    return buf.getvalue()


@pytest.mark.parametrize(("zone", "clock", "header"), [
    ("America/New_York", "10:19:25", "2026-10-27 10:19:25 EDT (UTC-04:00)"),
    ("Asia/Tokyo", "23:19:25", "2026-10-27 23:19:25 JST (UTC+09:00)"),
])
def test_a_session_renders_local_times_under_a_header_naming_the_zone(
    tmp_path: Path, zone: str, clock: str, header: str,
) -> None:
    log = tmp_path / "s.jsonl"
    log.write_text(json.dumps({
        "type": "user", "uuid": "u1", "parentUuid": None, "sessionId": "s",
        "timestamp": STAMP, "message": {"role": "user", "content": "hello"},
    }) + "\n")
    with local_zone(zone):
        out = render(cc_main, str(log))
    assert f"first shown: {header}" in out
    assert f"┌ User  {clock}" in out
    assert "14:19:25" not in out


def test_a_session_with_no_readable_stamp_names_no_zone(tmp_path: Path) -> None:
    log = tmp_path / "s.jsonl"
    log.write_text(json.dumps({
        "type": "user", "uuid": "u1", "parentUuid": None, "sessionId": "s",
        "timestamp": "not-a-time", "message": {"role": "user", "content": "hello"},
    }) + "\n")
    with local_zone("Asia/Tokyo"):
        out = render(cc_main, str(log))
    assert "first shown" not in out
    assert "┌ User  not-a-time" in out


def test_a_capture_s_header_carries_its_local_date_time_and_zone(tmp_path: Path) -> None:
    path = tmp_path / "0001.json"
    path.write_text(json.dumps({
        "timestamp": "2026-10-27T14:19:25+00:00",
        "request": {"model": "claude-test", "messages": [{"role": "user", "content": "hi"}]},
        "response": {"model": "claude-test", "content": [{"type": "text", "text": "ok"}]},
    }))
    with local_zone("America/New_York"):
        for flags in ((), ("--skeleton",)):
            assert "2026-10-27 10:19:25 EDT (UTC-04:00)" in render(intercept_main, str(path), *flags)


def test_an_opencode_session_s_epoch_stamps_render_local(tmp_path: Path) -> None:
    epoch_ms = int(datetime.fromisoformat(STAMP).timestamp() * 1000)
    path = tmp_path / "export.json"
    path.write_text(json.dumps({
        "info": {"id": "ses_1", "directory": "/repo"},
        "messages": [{"info": {"role": "user", "id": "msg_1", "time": {"created": epoch_ms}},
                      "parts": [{"type": "text", "text": "hello"}]}],
    }))
    with local_zone("Asia/Kolkata"):
        out = render(opencode_main, "ses_1", "--from-file", str(path))
    assert "first shown: 2026-10-27 19:49:25 IST (UTC+05:30)" in out
    assert "┌ User  19:49:25" in out

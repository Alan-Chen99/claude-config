import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import render


def test_every_report_renders():
    for name in render.load_reports():
        assert render.render(name).strip()


def test_variables_are_substituted():
    sql = render.render("daily_active")
    assert "analytics_prod.request_log" in sql
    assert "$dataset" not in sql
    assert "2026-09-01" in sql


def test_unknown_report_is_an_error():
    with pytest.raises(SystemExit):
        render.render("no_such_report")


@pytest.mark.skip(reason="strict rendering is not wired into the scheduler yet")
def test_every_report_renders_strict():
    for name in render.load_reports():
        assert render.render(name, strict=True).strip()

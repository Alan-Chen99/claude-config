"""The cache-keepalive mod against the installed engine.

The plugin API is early access and moves between releases, so the mod's own
tests (scripts/cache-keepalive/tests/) run here, where an upgrade's pytest run
reaches them, rather than only by hand.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

MOD = Path(__file__).resolve().parent.parent / "scripts" / "cache-keepalive"

pytestmark = pytest.mark.skipif(shutil.which("claude") is None, reason="no installed Claude Code to load the mod")


def _claude(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["claude", "plugin", *args, str(MOD)], capture_output=True, text=True, timeout=300)


def test_the_engine_admits_the_module() -> None:
    run = _claude("validate")
    assert run.returncode == 0, run.stdout + run.stderr
    assert "hooks: session.start, turn.start, turn.complete, classic.Stop, session.compact, session.end" in run.stdout


def test_the_mods_own_tests_pass() -> None:
    run = _claude("test")
    assert run.returncode == 0, run.stdout + run.stderr
    assert " 0 fail" in run.stdout + run.stderr

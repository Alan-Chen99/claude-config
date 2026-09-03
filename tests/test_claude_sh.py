"""Regression tests for scripts/claude.sh's exports.

CLAUDE_CODE_TMPDIR, IS_SANDBOX and CLAUDE_CODE_DISABLE_AGENT_VIEW are each
load-bearing in a way that fails silently: delete any one export and
`bash -n` still passes, the script still runs claude, and nothing crashes.
The main agent and its subagents just quietly disagree on the scratchpad
root (CLAUDE_CODE_TMPDIR), or a backgrounded fork silently runs the stock
system prompt (CLAUDE_CODE_DISABLE_AGENT_VIEW) instead of raising an error
a session would ever surface. These tests exist to make that loss loud.
"""

import socket
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_SH = ROOT / "scripts" / "claude.sh"

# Stands in for the real `claude` binary so scripts/claude.sh's final
# `exec claude ...` lands here instead. Dumps only the vars this test cares
# about, using bash's `${VAR-<unset>}` (not `${VAR:-<unset>}`) so a deleted
# export reads as the literal string "<unset>" rather than being conflated
# with a present-but-empty value.
_FAKE_CLAUDE = """#!/bin/bash
echo "IS_SANDBOX=${IS_SANDBOX-<unset>}"
echo "CLAUDE_CODE_DISABLE_AGENT_VIEW=${CLAUDE_CODE_DISABLE_AGENT_VIEW-<unset>}"
echo "CLAUDE_CODE_TMPDIR=${CLAUDE_CODE_TMPDIR-<unset>}"
"""


def _fake_bin_dir(tmp_path: Path) -> Path:
    """A PATH holding only a fake `claude` plus the real readlink/dirname.

    No real `claude` is anywhere on this PATH, so `exec claude ...` at the
    end of the script can only resolve to our stand-in via PATH lookup --
    there is no real binary here to accidentally intercept instead.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for command in ("readlink", "dirname"):
        (bin_dir / command).symlink_to(Path("/usr/bin") / command)
    fake_claude = bin_dir / "claude"
    fake_claude.write_text(_FAKE_CLAUDE)
    fake_claude.chmod(0o755)
    return bin_dir


def _dead_port() -> int:
    """A loopback TCP port nothing is listening on right now.

    Bind to port 0 to get one the kernel currently considers free, then
    close it without ever calling listen(). The gap between that close()
    and the script's own connection attempt a few milliseconds later is
    the same race every "find a free port" test helper accepts.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _patched_script_with_dead_proxy_port(tmp_path: Path) -> Path:
    """A copy of scripts/claude.sh with its proxy port pointed at dead air.

    PROXY_HOST and PROXY_PORT are plain literal assignments in the script,
    not `${PROXY_PORT:-9160}`-style defaults, so there is no environment
    variable that can steer the connect check onto a different port --
    the value has to be patched in the text itself. This container may
    happen to have a real MITM proxy listening on 127.0.0.1:9160 right
    now (dev sessions launch one), which would make the *real* file take
    the "if" branch here and never exercise the else branch this test
    means to cover: the one a developer machine without that proxy
    actually takes, and the one where a deleted CLAUDE_CODE_TMPDIR export
    would go unnoticed.

    The substitution is verified single-line so this still runs the real
    script's logic, not a rewritten one: exactly one occurrence of the
    literal is required going in, and exactly one line is allowed to
    differ coming out.
    """
    original = CLAUDE_SH.read_text()
    literal = "PROXY_PORT=9160"
    assert original.count(literal) == 1, (
        f"expected exactly one {literal!r} in {CLAUDE_SH}; "
        "scripts/claude.sh:23's proxy port literal has drifted out of "
        "sync with this test's patch target"
    )
    patched = original.replace(literal, f"PROXY_PORT={_dead_port()}", 1)

    original_lines = original.splitlines()
    patched_lines = patched.splitlines()
    assert len(original_lines) == len(patched_lines)
    changed = [i for i, (a, b) in enumerate(zip(original_lines, patched_lines)) if a != b]
    assert len(changed) == 1 and literal in original_lines[changed[0]]

    out = tmp_path / "claude-dead-proxy.sh"
    out.write_text(patched)
    return out


def _run(script: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Run script under a from-scratch environment, not an inherited one.

    Unlike tests/test_install.py's os.environ.copy(), this must NOT start
    from the ambient environment: this very test suite commonly runs
    inside a session that scripts/claude.sh itself launched, which means
    IS_SANDBOX=1 and CLAUDE_CODE_DISABLE_AGENT_VIEW=1 are often already
    set in the parent process. Inheriting them would make the test below
    pass even if the script's own export were deleted -- the child would
    still see the value, just leaked in from this test runner's ancestry
    rather than produced by the script under test.
    """
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    bin_dir = _fake_bin_dir(tmp_path)
    return subprocess.run(
        ["/bin/bash", str(script)],
        cwd=ROOT,
        env={"HOME": str(home), "PATH": str(bin_dir)},
        text=True,
        capture_output=True,
    )


def test_claude_sh_exports_survive_without_mitm_proxy(tmp_path: Path) -> None:
    script = _patched_script_with_dead_proxy_port(tmp_path)
    result = _run(script, tmp_path)

    assert result.returncode == 0, result.stderr

    # Proves the else branch actually ran -- the branch a developer
    # machine with no MITM proxy running takes by default.
    assert "WARNING: nothing listening" in result.stderr

    stdout_lines = result.stdout.splitlines()
    assert "IS_SANDBOX=1" in stdout_lines
    assert "CLAUDE_CODE_DISABLE_AGENT_VIEW=1" in stdout_lines
    assert "CLAUDE_CODE_TMPDIR=/root/.claude/tmp" in stdout_lines

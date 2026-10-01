"""Regression tests for scripts/claude.sh's exports.

CLAUDE_CODE_TMPDIR, IS_SANDBOX and CLAUDE_CODE_DISABLE_AGENT_VIEW are each
load-bearing in a way that fails silently: delete any one export and
`bash -n` still passes, the script still runs claude, and nothing crashes.
The main agent and its subagents just quietly disagree on the scratchpad
root (CLAUDE_CODE_TMPDIR), or a backgrounded fork silently runs the stock
system prompt (CLAUDE_CODE_DISABLE_AGENT_VIEW) instead of raising an error
a session would ever surface. These tests exist to make that loss loud.
"""

import os
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
echo "CLAUDE_CODE_TOTAL_TOKENS_REMINDER=${CLAUDE_CODE_TOTAL_TOKENS_REMINDER-<unset>}"
echo "CLAUDE_SH_TOKENS_REMINDER_SOURCE=${CLAUDE_SH_TOKENS_REMINDER_SOURCE-<unset>}"
"""


def _fake_bin_dir(tmp_path: Path) -> Path:
    """A PATH holding only a fake `claude` plus the real readlink/dirname.

    No real `claude` is anywhere on this PATH, so `exec claude ...` at the
    end of the script can only resolve to our stand-in via PATH lookup --
    there is no real binary here to accidentally intercept instead.
    """
    bin_dir = tmp_path / "bin"
    # Idempotent: one test runs the script several times off one tmp_path, each
    # run differing only in its stdin and environment.
    bin_dir.mkdir(exist_ok=True)
    for command in ("readlink", "dirname"):
        link = bin_dir / command
        if not link.exists():
            link.symlink_to(Path("/usr/bin") / command)
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
        "the script's proxy port literal has drifted out of sync with "
        "this test's patch target"
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


def _fake_home(tmp_path: Path) -> Path:
    """The HOME the script runs under, and the root its scratch path derives from.

    Named once and used by both the runner and the assertion, so the test
    cannot silently drift into checking a path the script was never given.
    """
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    return home


def _run(
    script: Path,
    tmp_path: Path,
    *,
    stdin: int | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
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
    home = _fake_home(tmp_path)
    bin_dir = _fake_bin_dir(tmp_path)
    env = {"HOME": str(home), "PATH": str(bin_dir)}
    env.update(extra_env or {})
    return subprocess.run(
        ["/bin/bash", str(script)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        # Named rather than inherited: the script branches on `[ -t 0 ]`, and
        # pytest's own stdin is a tty under `-s` and a pipe otherwise, which
        # would decide the branch from how the suite was invoked.
        stdin=subprocess.DEVNULL if stdin is None else stdin,
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
    # Relative to this run's HOME, not a literal path. An export naming one
    # user's home outright satisfies a literal check while handing every other
    # user a scratch root they cannot write.
    assert f"CLAUDE_CODE_TMPDIR={_fake_home(tmp_path)}/.claude/tmp" in stdout_lines


def _reported(result: subprocess.CompletedProcess[str], name: str) -> str:
    """The value the fake `claude` saw for one variable."""
    prefix = f"{name}="
    matches = [l[len(prefix):] for l in result.stdout.splitlines() if l.startswith(prefix)]
    assert len(matches) == 1, f"{name} reported {len(matches)} times: {result.stdout!r}"
    return matches[0]


def test_arm_source_labels_the_path_the_launcher_took(tmp_path: Path) -> None:
    """Which arm ran is recoverable; which *path* set it needs its own label.

    `agent-tools hook-provenance` snapshots the environment after the script's
    `exec`, where a drawn arm and one the caller exported are indistinguishable,
    so a trial that must exclude hand-set sessions depends on this label alone
    (docs/total-tokens-reminder-trial.md, "Arm recovery").
    """
    script = _patched_script_with_dead_proxy_port(tmp_path)

    caller = _run(
        script,
        tmp_path,
        extra_env={"CLAUDE_CODE_TOTAL_TOKENS_REMINDER": "a-value-the-caller-chose"},
    )
    assert caller.returncode == 0, caller.stderr
    assert _reported(caller, "CLAUDE_SH_TOKENS_REMINDER_SOURCE") == "caller"
    # The caller's value survives: the draw must not overwrite a deliberate one.
    assert _reported(caller, "CLAUDE_CODE_TOTAL_TOKENS_REMINDER") == "a-value-the-caller-chose"

    no_tty = _run(script, tmp_path)
    assert no_tty.returncode == 0, no_tty.stderr
    assert _reported(no_tty, "CLAUDE_SH_TOKENS_REMINDER_SOURCE") == "skipped-not-interactive"
    # `-p` runs, prompt-test cases included, must not acquire a randomized var.
    assert _reported(no_tty, "CLAUDE_CODE_TOTAL_TOKENS_REMINDER") == "<unset>"


def test_a_drawn_arm_is_labelled_and_never_printed(tmp_path: Path) -> None:
    """A pty on stdin is the only way to reach the draw at all.

    The arm staying out of the trace is the one blinding this trial can have:
    one candidate outcome is how often the user redirects the session, and an
    arm announced in the first line of scrollback would be read before then.
    """
    script = _patched_script_with_dead_proxy_port(tmp_path)
    master, slave = os.openpty()
    try:
        result = _run(script, tmp_path, stdin=slave)
    finally:
        os.close(master)
        os.close(slave)

    assert result.returncode == 0, result.stderr
    assert _reported(result, "CLAUDE_SH_TOKENS_REMINDER_SOURCE") == "draw"
    arm = _reported(result, "CLAUDE_CODE_TOTAL_TOKENS_REMINDER")
    assert arm in ("off", "padded-countdown")
    assert "export CLAUDE_CODE_TOTAL_TOKENS_REMINDER" not in result.stderr
    assert f"CLAUDE_CODE_TOTAL_TOKENS_REMINDER={arm}" not in result.stderr

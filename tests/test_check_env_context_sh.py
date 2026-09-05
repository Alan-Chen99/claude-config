"""Regression test for scripts/check-env-context.sh's venv pinning.

UV_PROJECT_ENVIRONMENT fails silently when it is missing: `uv run` still
resolves, the drift check still reports correctly, and the script still
exits 0. What changes is where the environment lands -- unpinned, uv
builds a 400 MB `.venv` inside the checkout, which install.sh keeps out of
the source tree so host and container sessions cannot fight over one.
`.venv` is gitignored, so `git status` stays clean and nothing surfaces
the loss. This test exists to make it loud.

Sibling of test_claude_sh.py, and the same shape: a stand-in binary on a
from-scratch PATH, the real script, an assertion on the environment the
script hands over.
"""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-env-context.sh"

# Stands in for uv so the script's `uv run --project ...` lands here rather
# than syncing a real environment. `${VAR-<unset>}` (not `${VAR:-<unset>}`)
# so a deleted export reads as "<unset>" instead of being conflated with a
# present-but-empty value. Draining stdin keeps the script's heredoc from
# dying on EPIPE under `set -o pipefail`.
_FAKE_UV = """#!/bin/bash
cat >/dev/null
echo "UV_PROJECT_ENVIRONMENT=${UV_PROJECT_ENVIRONMENT-<unset>}"
"""


def _fake_bin_dir(tmp_path: Path) -> Path:
    """A PATH holding only a fake `uv` plus the real coreutils the script calls.

    No real `uv` is anywhere on this PATH, so the script's `uv run` can only
    resolve to the stand-in -- there is no real binary here to accidentally
    intercept instead, and no chance of provisioning a venv for real.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for command in ("readlink", "dirname", "basename"):
        (bin_dir / command).symlink_to(Path("/usr/bin") / command)
    fake_uv = bin_dir / "uv"
    fake_uv.write_text(_FAKE_UV)
    fake_uv.chmod(0o755)
    return bin_dir


def _run(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Run the real script under a from-scratch environment.

    Must not inherit os.environ: this suite commonly runs under direnv, or
    inside a session whose shell already exports UV_PROJECT_ENVIRONMENT.
    Inheriting it would make the assertion below pass even with the
    script's own export deleted -- the child would still see a pinned
    value, leaked in from the test runner's ancestry rather than produced
    by the script under test.

    The real path is used rather than a copy: `root` is derived from
    ${BASH_SOURCE[0]} via readlink -f, so a copy under tmp_path would make
    the script compute a venv name from tmp_path's basename instead of the
    checkout's, testing the copy's location rather than the real one.
    """
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    bin_dir = _fake_bin_dir(tmp_path)
    return subprocess.run(
        ["/bin/bash", str(SCRIPT)],
        cwd=ROOT,
        env={"HOME": str(home), "PATH": str(bin_dir)},
        text=True,
        capture_output=True,
    )


def test_check_env_context_pins_the_out_of_tree_venv(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr

    expected = tmp_path / "home" / ".claude" / "venvs" / ROOT.name
    assert f"UV_PROJECT_ENVIRONMENT={expected}" in result.stdout.splitlines()


def test_check_env_context_leaves_no_venv_in_the_checkout(tmp_path: Path) -> None:
    """The property the pin exists for, asserted against the tree itself.

    Separate from the value assertion above because the two fail for
    different reasons: a wrong-but-pinned path fails only the first, while
    an export moved below the `uv run` line -- still present, still
    naming the right path, simply too late -- fails only this one.
    """
    before = (ROOT / ".venv").exists()

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    line = next(
        line
        for line in result.stdout.splitlines()
        if line.startswith("UV_PROJECT_ENVIRONMENT=")
    )
    named = line.partition("=")[2]
    assert named != "<unset>", "the export is missing; uv would build .venv in-tree"
    assert os.path.commonpath([named, str(ROOT)]) != str(ROOT), (
        f"{named} is inside the checkout at {ROOT}"
    )
    assert (ROOT / ".venv").exists() == before, "the run created an in-tree .venv"

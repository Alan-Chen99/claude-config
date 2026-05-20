import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_install_links_opencode_config(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for command in ("dirname", "ln", "mkdir"):
        (bin_dir / command).symlink_to(Path("/usr/bin") / command)

    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = str(bin_dir)

    subprocess.run(
        ["/bin/bash", str(ROOT / "install.sh")],
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )

    opencode_link = home / ".config" / "opencode"
    assert opencode_link.is_symlink()
    assert opencode_link.resolve() == ROOT / "opencode"

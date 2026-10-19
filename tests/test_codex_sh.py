"""The Codex launcher must override identities inherited from a Claude session."""

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_codex_identity_and_argument_forwarding(tmp_path: Path) -> None:
    fake = tmp_path / "codex"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "print(json.dumps({'args': sys.argv[1:], 'identity': "
        "{k: os.environ[k] for k in "
        "['GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL', 'GIT_COMMITTER_NAME', 'GIT_COMMITTER_EMAIL']}}))\n"
    )
    fake.chmod(0o755)
    env = dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}")
    for role in ("AUTHOR", "COMMITTER"):
        env[f"GIT_{role}_NAME"] = "Claude"
        env[f"GIT_{role}_EMAIL"] = "inherited@example.invalid"
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/codex.sh"), "resume", "a session", "--last"],
        env=env, capture_output=True, text=True, check=True,
    )
    reported = json.loads(result.stdout)
    assert reported["args"] == ["resume", "a session", "--last"]
    assert reported["identity"] == {
        "GIT_AUTHOR_NAME": "Codex",
        "GIT_COMMITTER_NAME": "Codex",
        "GIT_AUTHOR_EMAIL": "81847+claude@users.noreply.github.com",
        "GIT_COMMITTER_EMAIL": "81847+claude@users.noreply.github.com",
    }

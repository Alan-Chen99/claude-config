"""The session scratchpad directory.

Claude Code creates this itself (`_Fi()`, globals/20.js:18630) and names it in
subagent prompts (`Xff`, globals/14.js:26405), but the section is dropped from
the main agent's prompt under --system-prompt-file. Creation is gated
(`b1e()`, globals/20.js:18583) on a remote feature gate or artifact-tool
eligibility, and an unauthenticated session gets no directory at all, so this
module creates it rather than assuming it exists.
"""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path

# `vie`, globals/02.js:2753. Past this cc appends a hash suffix to the slug.
SLUG_LIMIT = 200

_NON_ALPHANUMERIC = re.compile(r"[^a-zA-Z0-9]")


def tmp_root(env: Mapping[str, str] | None = None) -> str:
    """Mirrors `Spe()`, globals/05.js:8056."""
    env = os.environ if env is None else env
    return env.get("CLAUDE_CODE_TMPDIR") or tempfile.gettempdir()


def project_slug(cwd: str) -> str:
    """Mirrors `FDo()`/`q9()`, globals/02.js:2156-2164.

    Past SLUG_LIMIT cc appends `-<hash>` using a hash this module does not
    implement. Raising beats emitting a path cc does not use.
    """
    slug = _NON_ALPHANUMERIC.sub("-", cwd)
    if len(slug) > SLUG_LIMIT:
        raise ValueError(
            f"project slug for {cwd!r} is {len(slug)} characters, past Claude Code's "
            + f"{SLUG_LIMIT}-character limit, where it appends a hash suffix this "
            + "module does not implement"
        )
    return slug


def scratchpad_path(
    *,
    env: Mapping[str, str] | None = None,
    cwd: str | None = None,
    session_id: str,
    uid: int | None = None,
) -> Path:
    env = os.environ if env is None else env
    cwd = os.getcwd() if cwd is None else cwd
    uid = os.getuid() if uid is None else uid
    return (
        Path(tmp_root(env))
        / f"claude-{uid}"
        / project_slug(cwd)
        / session_id
        / "scratchpad"
    )


def ensure(
    *,
    env: Mapping[str, str] | None = None,
    cwd: str | None = None,
    session_id: str,
    uid: int | None = None,
) -> Path:
    """Create the scratchpad at mode 0700 and return it.

    Built downward (tmp root -> uid dir -> slug -> session -> scratchpad)
    rather than by re-deriving levels from scratchpad_path()'s output via
    positional .parent hops, so a caller error can no longer make a wrong
    level be mistaken for uid_dir. Claude Code realpaths its `claude-<uid>`
    directory (`yJ()`, globals/05.js:8230) before descending further, so a
    symlinked tmp root would otherwise yield a different string than the
    one subagents are given; only that one level is realpathed, matching
    yJ(), and only uid_dir and the final scratchpad dir are ever forced to
    0700 here — a tmp root that did not exist yet is created as a side
    effect of parents=True but is left at whatever default permissions an
    ordinary mkdir would give it.
    """
    env = os.environ if env is None else env
    cwd = os.getcwd() if cwd is None else cwd
    uid = os.getuid() if uid is None else uid
    uid_dir = Path(tmp_root(env)) / f"claude-{uid}"
    uid_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    final = (
        Path(os.path.realpath(uid_dir)) / project_slug(cwd) / session_id / "scratchpad"
    )
    final.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(final, 0o700)
    return final

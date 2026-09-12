"""The session scratchpad directory.

Claude Code names this directory to the model in its `# Environment` block
(`src/chunk-dbb93264.js:29193`) and, separately, in the worker-tools context
(`src/chunk-4zcseazt.js:1377`). It computes the path in `AH()`
(`src/chunk-tnzzwz8r.js:13393`) as `join(WR(), <session id>, "scratchpad")`,
caching `null` when that throws -- computing is not creating, and creation
happens elsewhere and conditionally, so an unauthenticated session can get no
directory at all. This module creates it rather than assuming it exists.

The gate on creation was traced against 2.1.235 as a remote feature gate or
artifact-tool eligibility and has not been re-traced for 2.1.269; what is
re-verified here is the path, which is what this module has to agree with.
"""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path

# `N6`, src/chunk-jaqbht4s.js:676. Past this cc appends a hash suffix (`lT`, :684).
SLUG_LIMIT = 200

_NON_ALPHANUMERIC = re.compile(r"[^a-zA-Z0-9]")


def tmp_root(env: Mapping[str, str] | None = None) -> str:
    """Mirrors `AS()`, src/chunk-tht8x923.js:19."""
    env = os.environ if env is None else env
    return env.get("CLAUDE_CODE_TMPDIR") or tempfile.gettempdir()


def project_slug(cwd: str) -> str:
    """Mirrors `k()`/`lT()`, src/chunk-jaqbht4s.js:680-688.

    Past SLUG_LIMIT cc appends `-<hash>` using a hash this module does not
    implement. Raising beats emitting a path cc does not use.

    Also raises on an empty cwd. cc never sends one, but an empty slug
    would drop its own path segment the same way an unvalidated empty
    session_id did -- Path('/a') / '' is a no-op -- and consistency
    matters more than reachability here.
    """
    slug = _NON_ALPHANUMERIC.sub("-", cwd)
    if not slug:
        raise ValueError(f"project slug for {cwd!r} would be empty, dropping its path segment")
    if len(slug) > SLUG_LIMIT:
        raise ValueError(
            f"project slug for {cwd!r} is {len(slug)} characters, past Claude Code's "
            + f"{SLUG_LIMIT}-character limit, where it appends a hash suffix this "
            + "module does not implement"
        )
    return slug


def _resolve_inputs(
    env: Mapping[str, str] | None, cwd: str | None, uid: int | None
) -> tuple[Mapping[str, str], str, int]:
    """The env/cwd/uid defaulting shared by scratchpad_path and ensure.

    Duplicating this three-line block in both functions is what let them
    compute different paths for the same input in the first place.
    """
    return (
        os.environ if env is None else env,
        os.getcwd() if cwd is None else cwd,
        os.getuid() if uid is None else uid,
    )


def _uid_dir(env: Mapping[str, str], uid: int) -> Path:
    """The `claude-<uid>` directory, not yet realpathed."""
    return Path(tmp_root(env)) / f"claude-{uid}"


def _validate_session_id(session_id: str) -> None:
    """session_id becomes a literal path segment and, unlike cwd, is never
    run through project_slug. cc's own session ids are UUIDs, so none of
    this should fire in practice, but Task 7 feeds `payload["session_id"]`
    straight through, and an unchecked "" collides every session in the
    project onto one scratchpad, while ".." or a value containing "/"
    (e.g. "/etc") escapes the tree entirely -- Path("x") / "/etc" discards
    everything before the absolute-looking component.
    """
    if session_id in ("", ".", "..") or "/" in session_id or "\\" in session_id:
        raise ValueError(
            f"session_id {session_id!r} must be a single path segment: not "
            + "empty, '.', '..', or containing a path separator"
        )


def scratchpad_path(
    *,
    env: Mapping[str, str] | None = None,
    cwd: str | None = None,
    session_id: str,
    uid: int | None = None,
) -> Path:
    """The path ensure() creates -- the only place that computes it.

    Not pure: realpaths the `claude-<uid>` directory before descending
    further, mirroring `Id()` (src/chunk-tnzzwz8r.js:12739), even though this
    function creates nothing itself. A pure version would silently
    disagree with both cc and ensure() whenever the tmp root -- or
    `claude-<uid>` itself -- is a symlink (e.g. macOS, where TMPDIR sits
    under /var -> /private/var): the module's founding bug, reintroduced
    inside the module. That is the right trade, since a pure function
    naming the wrong directory is worthless here. realpath on a
    not-yet-created path resolves any symlinked ancestors the same way it
    would after ensure() creates them, so calling this before ensure() has
    run is safe.
    """
    _validate_session_id(session_id)
    env, cwd, uid = _resolve_inputs(env, cwd, uid)
    return (
        Path(os.path.realpath(_uid_dir(env, uid)))
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
    """Create the path scratchpad_path() names, at mode 0700, and return it.

    Calling scratchpad_path() first both computes the path and validates
    session_id and cwd's slug, so an invalid input raises before anything
    is created -- uid_dir.mkdir() used to run first, leaving claude-<uid>
    behind after a rejected cwd. uid_dir and the final scratchpad dir are
    both unconditionally chmod'd to 0700 after mkdir, matching cc's own
    repair (`cne`, src/chunk-tht8x923.js:25, whose check at :57 is
    `if ((o.mode & 511) !== 448) E(n, 448)`) -- mkdir's mode argument is only requested at
    creation and left alone for a directory that already existed, so
    without the explicit chmod a pre-existing, loosely-permissioned
    uid_dir would stay that way. The intermediate slug and session
    directories mkdir's parents=True creates along the way come out at
    0755, not 0700 like cc uses throughout; cosmetic, since uid_dir at
    0700 already gates traversal into them.

    The unconditional chmod widens two surfaces versus the pre-fix code,
    which never touched the mode of a uid_dir it did not create. A
    pre-existing, root-owned uid_dir this process cannot chmod now raises
    PermissionError instead of passing silently -- an OSError, so Task 7's
    guard catches it, but worth stating rather than discovering. And the
    chmod follows a symlinked uid_dir, so a pre-existing
    `claude-<uid> -> elsewhere` leaves `elsewhere` at 0700, slightly
    widening the symlink-following surface cc closes with O_NOFOLLOW in
    `JIt`, which this module deliberately does not mirror.
    """
    env, cwd, uid = _resolve_inputs(env, cwd, uid)
    final = scratchpad_path(env=env, cwd=cwd, session_id=session_id, uid=uid)
    uid_dir = _uid_dir(env, uid)
    uid_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(uid_dir, 0o700)
    final.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(final, 0o700)
    return final

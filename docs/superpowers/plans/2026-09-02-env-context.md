# env-context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the stale cc-2.1.143 clone in `agent-tools env-context` with a purpose-built context block that reports the shell the Bash tool actually runs, names a scratchpad shared with subagents, and warns when Claude Code's own env block drifts.

**Architecture:** `src/claude_config/env_context.py` becomes a package of five focused modules behind the same `python3 -m claude_config.env_context` entry point, so no Rust change is needed. The hook reads its `SessionStart` payload from stdin instead of discarding it, and emits the `hookSpecificOutput` JSON envelope itself. `scripts/claude.sh` exports `CLAUDE_CODE_TMPDIR`, which redirects Claude Code's own scratchpad construction so the main agent and its subagents finally name one directory. Two standalone scripts — a drift check and a prune tool — are run by hand.

**Tech Stack:** Python 3.14, pytest, bash. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-09-02-env-context-design.md`

---

## Background an implementer needs

You are working in `/root/claude-config-work`, a git worktree of `/repos/claude-config`.

**Never run `install.sh` from here.** It rewrites symlinks in `~/.claude` to point at this checkout, which breaks every other session when the worktree is deleted.

**Run tests with** `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`. The venv lives at `~/.claude/venvs/claude-config-work/`, not in the source tree.

**`agent-tools` is the installed binary** at `~/.local/bin/agent-tools`, symlinked to the *canonical* repo's build — not this worktree's. To exercise this worktree's Python you invoke it through `uv run` directly, as the test command above does. Do not rebuild or reinstall `agent-tools`; this change touches no Rust.

**Claude Code source references** point at `/repos/claude-config-work`'s sibling checkout `/repos/claude-code-decompiled`, a dump of the 2.1.235 binary. Read a cited line with `sed -n '<line>p' /repos/claude-code-decompiled/src/globals/<file>`.

**Why the JSON envelope matters.** A `SessionStart` hook that prints plain text gets it injected as `` `SessionStart hook success: <text>` `` (`src/globals/20.js:24499`). Only the JSON form with `hookSpecificOutput.additionalContext` is injected verbatim (`src/globals/20.js:24485`). The envelope is not optional.

---

## File Structure

`src/claude_config/env_context.py` is deleted and replaced by a package. `python3 -m claude_config.env_context` runs `__main__.py`, so `agent-tools/src/main.rs:754` keeps working untouched.

| File | Responsibility |
| --- | --- |
| `src/claude_config/env_context/__init__.py` | Empty package marker |
| `src/claude_config/env_context/environment.py` | Machine facts: shell resolution, git repo, worktree, platform, OS |
| `src/claude_config/env_context/scratchpad.py` | Tmp root, project slug, scratchpad path, directory creation |
| `src/claude_config/env_context/drift.py` | Binary literal extraction, manifest comparison, result cache |
| `src/claude_config/env_context/render.py` | Assembling the two prompt sections from facts |
| `src/claude_config/env_context/__main__.py` | stdin payload, orchestration, JSON envelope |
| `tests/test_env_context.py` | Tests for all of the above |
| `docs/env-context-manifest.json` | Pinned cc version and env-block literals |
| `scripts/check-env-context.sh` | Drift diff, run by hand |
| `scripts/prune-scratch.sh` | Scratch reporting and deletion, run by hand |

Note the manifest is JSON, not the `.txt` named in the spec: the literals carry significant trailing spaces (`"Primary working directory: "`), which a line-based text format loses to any editor that strips them. Task 12 amends the spec to match.

---

## Task 1: Package skeleton

**Files:**
- Create: `src/claude_config/env_context/__init__.py`
- Delete: `src/claude_config/env_context.py`
- Test: `tests/test_env_context.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_env_context.py`:

```python
"""Tests for the env-context SessionStart hook."""

import importlib


def test_package_imports() -> None:
    module = importlib.import_module("claude_config.env_context")
    assert module.__file__ is not None
    assert module.__file__.endswith("__init__.py")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: FAIL. The assertion fails because `claude_config.env_context` currently resolves to the single module `env_context.py`, so `__file__` ends in `env_context.py`.

- [ ] **Step 3: Convert the module into a package**

```bash
cd /root/claude-config-work
git rm -q src/claude_config/env_context.py
mkdir -p src/claude_config/env_context
touch src/claude_config/env_context/__init__.py
rm -rf src/claude_config/__pycache__
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add -A src/claude_config/env_context tests/test_env_context.py src/claude_config/env_context.py
git commit -m "refactor: make env_context a package

The hook grows four distinct responsibilities - machine facts,
scratchpad paths, drift detection, rendering - and a package keeps
each in a file small enough to read at once. python3 -m
claude_config.env_context resolves to __main__.py, so the
agent-tools entry point is unchanged."
```

---

## Task 2: Shell resolution

Claude Code's env block reads `$SHELL` and prints the literal `unknown` when it is unset (`Kml()`, `src/globals/21.js:13560`) — which is what happens here, because the `claude` process has no `SHELL`. Its Bash tool independently resolves a real shell (`src/globals/10.js:22633`) and that is the shell your commands actually run in. This task reimplements the Bash tool's algorithm.

> **Amended during review.** The code below is the first draft; the committed
> version in `aa7808c`, `b3f3a7e` and `c79e4e7` differs in ways review found
> necessary. Read `src/claude_config/env_context/environment.py` as the
> authority. The deltas: `env` widened to `Mapping[str, str]` so `os.environ`
> is accepted, and `search_dirs` to `Sequence[str]`, with `SEARCH_DIRS` a
> tuple; `found` collapsed from a `None`/`{}` tri-state dict to
> `Callable[[str], str | None] = shutil.which`; a private `_git()` helper
> wrapping both git calls with `timeout=5` and catching `OSError` /
> `subprocess.SubprocessError`, because a missing git binary, a deleted cwd
> and a cwd that is a file all raise rather than exiting non-zero, and Task 7
> would have let any of them kill the hook; and nine further tests covering
> the four functions this task's original test list left uncovered.

**Files:**
- Create: `src/claude_config/env_context/environment.py`
- Test: `tests/test_env_context.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_env_context.py`:

```python
from pathlib import Path

from claude_config.env_context import environment


def _fake_tree(root: Path, shells: list[str]) -> None:
    """Create executable stubs at the given absolute-looking paths under root."""
    for rel in shells:
        target = root / rel.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("#!/bin/sh\n")
        target.chmod(0o755)


def test_shell_override_wins(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/opt/custom/bash", "/bin/zsh"])
    result = environment.resolve_shell(
        env={"CLAUDE_CODE_SHELL": str(tmp_path / "opt/custom/bash")},
        search_dirs=[str(tmp_path / "bin")],
        found={},
    )
    assert result == str(tmp_path / "opt/custom/bash")


def test_shell_override_ignored_when_not_bash_or_zsh(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/opt/custom/fish", "/bin/zsh"])
    result = environment.resolve_shell(
        env={"CLAUDE_CODE_SHELL": str(tmp_path / "opt/custom/fish")},
        search_dirs=[str(tmp_path / "bin")],
        found={},
    )
    assert result == str(tmp_path / "bin/zsh")


def test_zsh_preferred_when_shell_unset(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/bin/bash", "/bin/zsh"])
    result = environment.resolve_shell(
        env={},
        search_dirs=[str(tmp_path / "bin")],
        found={},
    )
    assert result == str(tmp_path / "bin/zsh")


def test_bash_preferred_when_shell_names_bash(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/bin/bash", "/bin/zsh"])
    result = environment.resolve_shell(
        # Names bash, so it drives the ordering, but does not exist — a real
        # path here would be prepended as a valid $SHELL and win outright,
        # returning the machine's own bash instead of the fixture's.
        env={"SHELL": "/nonexistent/bash"},
        search_dirs=[str(tmp_path / "bin")],
        found={},
    )
    assert result == str(tmp_path / "bin/bash")


def test_falls_back_to_bash_when_no_zsh(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/bin/bash"])
    result = environment.resolve_shell(
        env={},
        search_dirs=[str(tmp_path / "bin")],
        found={},
    )
    assert result == str(tmp_path / "bin/bash")


def test_raises_when_no_shell_exists(tmp_path: Path) -> None:
    (tmp_path / "bin").mkdir()
    try:
        environment.resolve_shell(env={}, search_dirs=[str(tmp_path / "bin")], found={})
    except RuntimeError as exc:
        assert "no bash or zsh" in str(exc).lower()
    else:
        raise AssertionError("expected RuntimeError")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: FAIL with `ImportError: cannot import name 'environment' from 'claude_config.env_context'`

- [ ] **Step 3: Write the implementation**

Create `src/claude_config/env_context/environment.py`:

```python
"""Machine facts for the env block.

Claude Code's own env block reports `$SHELL`, falling back to the literal
string `unknown` (`Kml()`, globals/21.js:13560). That is not the shell it runs
commands with: the Bash tool resolves one independently (globals/10.js:22633)
and exports it. `resolve_shell` mirrors the Bash tool, so the reported shell is
the one Bash tool commands execute under.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys

SEARCH_DIRS = ["/bin", "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin"]


def _executable(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


def resolve_shell(
    env: dict[str, str] | None = None,
    search_dirs: list[str] | None = None,
    found: dict[str, str | None] | None = None,
) -> str:
    """Return the shell the Bash tool will run, mirroring globals/10.js:22633.

    `found` maps a shell name to its PATH lookup, defaulting to shutil.which.
    Tests pass an explicit mapping to keep the real PATH out of the result.
    """
    env = os.environ if env is None else env
    search_dirs = SEARCH_DIRS if search_dirs is None else search_dirs
    if found is None:
        found = {"zsh": shutil.which("zsh"), "bash": shutil.which("bash")}

    override = env.get("CLAUDE_CODE_SHELL")
    if override and ("bash" in override or "zsh" in override) and _executable(override):
        return override

    shell = env.get("SHELL")
    named_valid = bool(shell) and ("bash" in shell or "zsh" in shell)
    prefers_bash = bool(shell) and "bash" in shell

    order = ["bash", "zsh"] if prefers_bash else ["zsh", "bash"]
    candidates = [f"{d}/{name}" for name in order for d in search_dirs]

    preferred, other = ("bash", "zsh") if prefers_bash else ("zsh", "bash")
    if found.get(preferred):
        candidates.insert(0, found[preferred])
    if found.get(other):
        candidates.append(found[other])
    if named_valid and _executable(shell):
        candidates.insert(0, shell)

    for candidate in candidates:
        if _executable(candidate):
            return candidate

    raise RuntimeError(
        "no bash or zsh found; searched "
        f"{', '.join(search_dirs)} and PATH. Claude Code's Bash tool would fail too."
    )


def is_git_repo(cwd: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def worktree_common_dir(cwd: str) -> str | None:
    """Return the shared git dir when cwd is a linked worktree, else None.

    Claude Code emits its worktree warnings only for worktrees it created
    itself (`cv()`, globals/04.js:7126), so it stays silent in one made by
    hand. Asking git directly covers both.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    lines = result.stdout.split("\n")
    if len(lines) < 2:
        return None
    git_dir, common_dir = lines[0].strip(), lines[1].strip()
    if not git_dir or not common_dir or git_dir == common_dir:
        return None
    return common_dir


def os_version() -> str:
    """Mirrors os.type() + ' ' + os.release() (`Yml()`, globals/21.js:13572)."""
    return f"{platform.system()} {platform.release()}"


def platform_name() -> str:
    return sys.platform
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: PASS, 7 tests

- [ ] **Step 5: Sanity-check against the live machine**

Run:

```bash
cd /root/claude-config-work
uv run --project . python -c "
from claude_config.env_context import environment
print('shell:', environment.resolve_shell())
print('worktree common dir:', environment.worktree_common_dir('/root/claude-config-work'))
"
```

Expected output:

```
shell: /bin/bash
worktree common dir: /repos/claude-config/.git
```

`/bin/bash` is the value a Bash tool subprocess actually carries in `SHELL`; zsh is not installed on this machine, so the zsh-first ordering falls through to bash.

- [ ] **Step 6: Commit**

```bash
cd /root/claude-config-work
git add src/claude_config/env_context/environment.py tests/test_env_context.py
git commit -m "feat: resolve the shell the Bash tool actually runs

Claude Code reports \$SHELL and prints 'unknown' when it is unset,
which is the case for the claude process here. Its Bash tool resolves
a shell separately and exports it, so /bin/bash is what commands run
under. Report that instead."
```

---

## Task 3: Scratchpad paths

Claude Code builds the path in `Bbt()` (`src/globals/20.js:18616`) as `<tmp root>/claude-<uid>/<project slug>/<session id>/scratchpad`, where the tmp root is `CLAUDE_CODE_TMPDIR` or the system temp dir (`Spe()`, `src/globals/05.js:8056`).

> **Amended during review.** The code below is the first draft; the committed
> version, through `0ddfba4`, is the authority — read
> `src/claude_config/env_context/scratchpad.py`. Two defects review found in
> the draft: `session_id` defaulted to `""`, and `Path.__truediv__("")` is a
> no-op, so the segment vanished and every session in a project collided on
> one path with `scratchpad` sitting in the session-id slot — worse, `ensure`
> located `uid_dir` by three positional `.parent` hops, so the missing segment
> made it `mkdir` the tmp root itself at `0700`. `session_id` is now required
> and validated, every parameter keyword-only, and `scratchpad_path` is the
> single path computation — it realpaths `claude-<uid>` as cc does, and
> `ensure` returns its value verbatim so the two cannot name different
> directories. A later round found the first symlink tests could not fail for
> exactly that reason and replaced them with absolute-path assertions.

**Files:**
- Create: `src/claude_config/env_context/scratchpad.py`
- Test: `tests/test_env_context.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_env_context.py`:

```python
import stat

from claude_config.env_context import scratchpad


def test_tmp_root_prefers_env(tmp_path: Path) -> None:
    assert scratchpad.tmp_root({"CLAUDE_CODE_TMPDIR": str(tmp_path)}) == str(tmp_path)


def test_tmp_root_falls_back_to_system_temp() -> None:
    import tempfile

    assert scratchpad.tmp_root({}) == tempfile.gettempdir()


def test_slug_replaces_non_alphanumerics() -> None:
    assert scratchpad.project_slug("/root/claude-config-work") == "-root-claude-config-work"


def test_slug_raises_past_the_cc_limit() -> None:
    long_cwd = "/" + ("a" * 250)
    try:
        scratchpad.project_slug(long_cwd)
    except ValueError as exc:
        assert "200" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_path_matches_cc_layout(tmp_path: Path) -> None:
    path = scratchpad.scratchpad_path(
        env={"CLAUDE_CODE_TMPDIR": str(tmp_path)},
        cwd="/root/claude-config-work",
        session_id="abc-123",
        uid=0,
    )
    assert path == tmp_path / "claude-0" / "-root-claude-config-work" / "abc-123" / "scratchpad"


def test_ensure_creates_private_directory(tmp_path: Path) -> None:
    path = scratchpad.ensure(
        env={"CLAUDE_CODE_TMPDIR": str(tmp_path)},
        cwd="/root/claude-config-work",
        session_id="abc-123",
        uid=0,
    )
    assert path.is_dir()
    assert stat.S_IMODE(path.stat().st_mode) == 0o700
    again = scratchpad.ensure(
        env={"CLAUDE_CODE_TMPDIR": str(tmp_path)},
        cwd="/root/claude-config-work",
        session_id="abc-123",
        uid=0,
    )
    assert again == path
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: FAIL with `ImportError: cannot import name 'scratchpad' from 'claude_config.env_context'`

- [ ] **Step 3: Write the implementation**

Create `src/claude_config/env_context/scratchpad.py`:

```python
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
            f"{SLUG_LIMIT}-character limit, where it appends a hash suffix this "
            "module does not implement"
        )
    return slug


def scratchpad_path(
    env: Mapping[str, str] | None = None,
    cwd: str | None = None,
    session_id: str = "",
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
    env: Mapping[str, str] | None = None,
    cwd: str | None = None,
    session_id: str = "",
    uid: int | None = None,
) -> Path:
    """Create the scratchpad at mode 0700 and return it.

    Claude Code realpaths its `claude-<uid>` directory (`yJ()`,
    globals/05.js:8230), so a symlinked tmp root would otherwise yield a
    different string than the one subagents are given.
    """
    path = scratchpad_path(env, cwd, session_id, uid)
    uid_dir = path.parent.parent.parent
    uid_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    resolved = Path(os.path.realpath(uid_dir))
    final = resolved / path.parent.parent.name / path.parent.name / "scratchpad"
    final.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(final, 0o700)
    return final
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: PASS — the 6 new tests, plus everything already in the file

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add src/claude_config/env_context/scratchpad.py tests/test_env_context.py
git commit -m "feat: compute and create the session scratchpad

Mirrors cc's own path construction so the directory named to the main
agent is the one subagents were already given. cc's creation is gated
and an unauthenticated session gets none, so create it here."
```

---

## Task 4: Rendering

**Files:**
- Create: `src/claude_config/env_context/render.py`
- Test: `tests/test_env_context.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_env_context.py`:

```python
from claude_config.env_context import render


def _facts(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "cwd": "/root/claude-config-work",
        "is_git_repo": True,
        "worktree_common_dir": None,
        "platform": "linux",
        "shell": "/bin/bash",
        "os_version": "Linux 6.18.7",
        "model": "claude-opus-5",
        "session_id": "abc-123",
        "scratchpad": "/root/.claude/tmp/claude-0/-root-claude-config-work/abc-123/scratchpad",
        "drift_note": None,
    }
    base.update(overrides)
    return base


def test_env_block_has_expected_bullets() -> None:
    text = render.sections(_facts())
    assert text.startswith("# Environment\nYou have been invoked in the following environment: \n")
    assert " - Primary working directory: /root/claude-config-work" in text
    assert " - Is a git repository: true" in text
    assert " - Platform: linux" in text
    assert " - Shell: /bin/bash" in text
    assert " - OS Version: Linux 6.18.7" in text
    assert " - You are powered by the model claude-opus-5" in text
    assert " - Session ID: abc-123" in text


def test_model_line_omitted_when_absent() -> None:
    text = render.sections(_facts(model=None))
    assert "powered by the model" not in text


def test_worktree_lines_present_only_in_a_worktree() -> None:
    plain = render.sections(_facts())
    assert "git worktree" not in plain

    linked = render.sections(_facts(worktree_common_dir="/repos/claude-config/.git"))
    assert " - This is a git worktree of /repos/claude-config/.git." in linked
    assert "git stash" in linked


def test_scratchpad_section_names_the_path() -> None:
    text = render.sections(_facts())
    assert "# Scratchpad Directory" in text
    assert "/root/.claude/tmp/claude-0/-root-claude-config-work/abc-123/scratchpad" in text


def test_drift_note_appears_as_a_bullet() -> None:
    text = render.sections(_facts(drift_note="Claude Code 2.1.240 changed its env block."))
    assert " - NOTE: Claude Code 2.1.240 changed its env block." in text


def test_git_repo_false_renders_lowercase() -> None:
    text = render.sections(_facts(is_git_repo=False))
    assert " - Is a git repository: false" in text


def test_scratchpad_section_omitted_when_unavailable() -> None:
    """An uncreatable scratchpad must cost the section, not the whole block."""
    text = render.sections(_facts(scratchpad=None))
    assert "# Scratchpad Directory" not in text
    assert "None" not in text
    assert "# Environment" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: FAIL with `ImportError: cannot import name 'render' from 'claude_config.env_context'`

- [ ] **Step 3: Write the implementation**

Create `src/claude_config/env_context/render.py`:

```python
"""Assembling the prompt sections from collected facts.

Bullets use the ` - ` prefix Claude Code's own formatter emits (`jSe`,
globals/21.js:13158), so the block reads the same as the one cc produces in
sessions that use its default prompt.
"""

from __future__ import annotations

# cc's own wording, `cTm`, globals/21.js:13688, trimmed to the hazard.
STASH_CAUTION = (
    "The git stash stack is shared with the main checkout and all other worktrees, "
    "and other Claude sessions may push or pop it concurrently. Never use bare "
    "`git stash` / `git stash pop` — you could pop another session's changes. "
    "Prefer a temporary WIP commit to set work aside."
)


def _bullets(items: list[str]) -> str:
    return "\n".join(f" - {item}" for item in items)


def environment_section(facts: dict[str, object]) -> str:
    items: list[str] = [f"Primary working directory: {facts['cwd']}"]

    common_dir = facts.get("worktree_common_dir")
    if common_dir:
        items.append(
            f"This is a git worktree of {common_dir}. Run all commands from this "
            "directory. Do NOT `cd` to the original repository root."
        )
        items.append(STASH_CAUTION)

    items.append(f"Is a git repository: {str(bool(facts['is_git_repo'])).lower()}")
    items.append(f"Platform: {facts['platform']}")
    items.append(f"Shell: {facts['shell']}")
    items.append(f"OS Version: {facts['os_version']}")

    model = facts.get("model")
    if model:
        items.append(f"You are powered by the model {model}")

    items.append(f"Session ID: {facts['session_id']}")

    note = facts.get("drift_note")
    if note:
        items.append(f"NOTE: {note}")

    header = "# Environment\nYou have been invoked in the following environment: "
    return f"{header}\n{_bullets(items)}"


def scratchpad_section(path: str) -> str:
    return (
        "# Scratchpad Directory\n\n"
        "Use this directory for temporary files instead of `/tmp`:\n"
        f"`{path}`\n\n"
        "It is session-specific, isolated from the project, and is the same "
        "directory your subagents are given."
    )


def sections(facts: dict[str, object]) -> str:
    """The env block, plus the scratchpad section when there is a path to name.

    A scratchpad that could not be created leaves `scratchpad` None. Rendering
    that into the prompt as a path would point the agent at a directory which
    does not exist, so the section is dropped instead — the env block is worth
    having without it.
    """
    blocks = [environment_section(facts)]
    path = facts.get("scratchpad")
    if path:
        blocks.append(scratchpad_section(str(path)))
    return "\n\n".join(blocks)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: PASS — the 7 new tests, plus everything already in the file

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add src/claude_config/env_context/render.py tests/test_env_context.py
git commit -m "feat: render the env and scratchpad sections"
```

---

## Task 5: Drift manifest

Generate the manifest before the code that reads it, so later tasks have real data to test against.

**Files:**
- Create: `docs/env-context-manifest.json`

- [ ] **Step 1: Generate the manifest**

```bash
cd /root/claude-config-work
uv run --project . python - <<'PY'
import json, os, re, shutil, subprocess
from pathlib import Path

ANCHOR = b"You have been invoked in the following environment: "

def binary() -> Path:
    p = os.environ.get("CLAUDE_CODE_EXECPATH")
    if p and Path(p).is_file():
        return Path(p)
    found = shutil.which("claude")
    if not found:
        raise SystemExit("claude not on PATH and CLAUDE_CODE_EXECPATH unset")
    real = Path(os.path.realpath(found))
    if ANCHOR in real.read_bytes():
        return real
    wrapped = real.parent / ".claude-wrapped"
    if wrapped.exists():
        return Path(os.path.realpath(wrapped))
    raise SystemExit(f"no env-block anchor in {real} and no .claude-wrapped beside it")

b = binary()
data = b.read_bytes()
i = data.find(ANCHOR)
if i < 0:
    raise SystemExit(f"anchor not found in {b}")
window = data[max(0, i - 3000): i + 1500]
literals = sorted({m.decode() for m in re.findall(rb"[\x20-\x7e]{12,}", window)})
version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.split()[0]
Path("docs/env-context-manifest.json").write_text(
    json.dumps({"version": version, "literals": literals}, indent=2) + "\n"
)
print("version:", version, "literals:", len(literals))
PY
```

Expected: `version: 2.1.235 literals: 13`

- [ ] **Step 2: Inspect what was pinned**

Run: `cat docs/env-context-manifest.json`

Expected: a `version` of `2.1.235` and a `literals` array containing, among others, `"Primary working directory: "`, `"Is a git repository: "`, `"OS Version: "`, `"You are powered by the model named "`, `"Assistant knowledge cutoff is "`, and `"# Environment"`.

One entry — `"Iterator result interface is not an object."` — is an unrelated neighbour in the binary's string table. Leave it. A false positive costs one review; a narrower window risks missing a genuinely new field.

- [ ] **Step 3: Commit**

```bash
cd /root/claude-config-work
git add docs/env-context-manifest.json
git commit -m "docs: pin cc 2.1.235 env-block literals

Extracted from the installed binary's string table. The drift check
reads the installed binary rather than the decompiled dump, so it
tracks upgrades without anyone regenerating the dump."
```

---

## Task 6: Drift detection

**Files:**
- Create: `src/claude_config/env_context/drift.py`
- Test: `tests/test_env_context.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_env_context.py`:

```python
import json

from claude_config.env_context import drift


def _binary(tmp_path: Path, literals: list[str]) -> Path:
    """A stand-in binary: padding, the anchor, then the literals."""
    blob = b"\x00" * 100
    blob += b"You have been invoked in the following environment: "
    for text in literals:
        blob += b"\x00" + text.encode()
    path = tmp_path / "claude.exe"
    path.write_bytes(blob)
    return path


def test_extract_finds_literals(tmp_path: Path) -> None:
    binary = _binary(tmp_path, ["Primary working directory: ", "Is a git repository: "])
    literals = drift.extract_literals(binary)
    assert "Primary working directory: " in literals
    assert "Is a git repository: " in literals


def test_extract_raises_without_anchor(tmp_path: Path) -> None:
    path = tmp_path / "not-claude"
    path.write_bytes(b"nothing here")
    try:
        drift.extract_literals(path)
    except RuntimeError as exc:
        assert "anchor" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_compare_matches_pinned_manifest(tmp_path: Path) -> None:
    literals = ["Primary working directory: ", "Is a git repository: "]
    binary = _binary(tmp_path, literals)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"version": "2.1.235", "literals": sorted(literals)}))
    result = drift.compare(binary, manifest, version="2.1.235")
    assert result.matches
    assert result.added == []
    assert result.removed == []


def test_compare_reports_a_new_field(tmp_path: Path) -> None:
    binary = _binary(tmp_path, ["Primary working directory: ", "Current sandbox mode: "])
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"version": "2.1.235", "literals": ["Primary working directory: "]})
    )
    result = drift.compare(binary, manifest, version="2.1.240")
    assert not result.matches
    assert "Current sandbox mode: " in result.added
    assert result.installed_version == "2.1.240"


def test_cache_avoids_a_second_scan(tmp_path: Path) -> None:
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"version": "2.1.235", "literals": literals}))
    cache = tmp_path / "cache.json"

    calls: list[int] = []

    def version() -> str:
        calls.append(1)
        return "2.1.235"

    first = drift.cached_note(binary, manifest, cache, version)
    second = drift.cached_note(binary, manifest, cache, version)
    assert first is None
    assert second is None
    assert len(calls) == 1


def test_cached_note_text_names_the_script(tmp_path: Path) -> None:
    binary = _binary(tmp_path, ["Current sandbox mode: "])
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"version": "2.1.235", "literals": ["Old field: "]}))
    cache = tmp_path / "cache.json"
    note = drift.cached_note(binary, manifest, cache, lambda: "2.1.240")
    assert note is not None
    assert "2.1.240" in note
    assert "check-env-context.sh" in note
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: FAIL with `ImportError: cannot import name 'drift' from 'claude_config.env_context'`

- [ ] **Step 3: Write the implementation**

Create `src/claude_config/env_context/drift.py`:

```python
"""Detecting drift in Claude Code's own env block.

The env-block field templates survive in the installed binary's string table
as plain literals. Reading the installed binary rather than a decompiled dump
is what makes the check track upgrades on its own: the dump is regenerated by
hand, the binary changes underfoot.

The check sees labels only. A change to how cc computes a value without
changing its label will not trip it, which is why the manifest pins the cc
version alongside the literals.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

ANCHOR = b"You have been invoked in the following environment: "
WINDOW_BEFORE = 3000
WINDOW_AFTER = 1500
PRINTABLE = re.compile(rb"[\x20-\x7e]{12,}")


@dataclass
class Comparison:
    matches: bool
    installed_version: str
    pinned_version: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


def find_binary(env: Mapping[str, str] | None = None) -> Path:
    """Locate the running Claude Code binary.

    CLAUDE_CODE_EXECPATH is set in hook and tool subprocess environments and
    names the binary directly. The PATH fallback lands on a wrapper script
    under Nix, whose sibling `.claude-wrapped` symlink points at the real one.
    """
    env = os.environ if env is None else env
    execpath = env.get("CLAUDE_CODE_EXECPATH")
    if execpath and Path(execpath).is_file():
        return Path(execpath)

    found = shutil.which("claude", path=env.get("PATH"))
    if not found:
        raise RuntimeError("claude is not on PATH and CLAUDE_CODE_EXECPATH is unset")
    real = Path(os.path.realpath(found))
    if ANCHOR in real.read_bytes():
        return real
    wrapped = real.parent / ".claude-wrapped"
    if wrapped.exists():
        return Path(os.path.realpath(wrapped))
    raise RuntimeError(
        f"{real} carries no env-block anchor and has no .claude-wrapped sibling"
    )


def extract_literals(binary: Path) -> list[str]:
    data = binary.read_bytes()
    index = data.find(ANCHOR)
    if index < 0:
        raise RuntimeError(f"env-block anchor not found in {binary}")
    window = data[max(0, index - WINDOW_BEFORE) : index + WINDOW_AFTER]
    return sorted({m.decode() for m in PRINTABLE.findall(window)})


def installed_version() -> str:
    result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"claude --version failed: {result.stderr.strip()}")
    return result.stdout.split()[0]


def compare(binary: Path, manifest: Path, version: str) -> Comparison:
    pinned = json.loads(manifest.read_text())
    found = set(extract_literals(binary))
    expected = set(pinned["literals"])
    added = sorted(found - expected)
    removed = sorted(expected - found)
    return Comparison(
        matches=not added and not removed and version == pinned["version"],
        installed_version=version,
        pinned_version=pinned["version"],
        added=added,
        removed=removed,
    )


def cached_note(
    binary: Path,
    manifest: Path,
    cache: Path,
    version: Callable[[], str] = installed_version,
) -> str | None:
    """Return a one-line drift note, or None when the field set still matches.

    The result is cached on the binary's size and mtime, so the full scan runs
    once per Claude Code upgrade rather than once per session.
    """
    stat = binary.stat()
    key = {"binary": str(binary), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}

    if cache.is_file():
        stored = json.loads(cache.read_text())
        if all(stored.get(k) == v for k, v in key.items()):
            return stored.get("note")

    result = compare(binary, manifest, version())
    note = None
    if not result.matches:
        note = (
            f"Claude Code {result.installed_version} changed its env block since the "
            f"{result.pinned_version} field set this hook is pinned to. Run "
            "scripts/check-env-context.sh to review."
        )
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({**key, "note": note}))
    return note
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: PASS — the 6 new tests, plus everything already in the file

- [ ] **Step 5: Sanity-check against the real binary**

Run:

```bash
cd /root/claude-config-work
uv run --project . python -c "
from pathlib import Path
from claude_config.env_context import drift
b = drift.find_binary()
print('binary:', b)
r = drift.compare(b, Path('docs/env-context-manifest.json'), drift.installed_version())
print('matches:', r.matches, '| added:', r.added, '| removed:', r.removed)
"
```

Expected:

```
binary: /nix/store/.../bin/claude.exe
matches: True | added: [] | removed: []
```

If `matches` is False here, the manifest from Task 5 and this reader disagree about the window — fix the reader, do not edit the manifest to match.

- [ ] **Step 6: Commit**

```bash
cd /root/claude-config-work
git add src/claude_config/env_context/drift.py tests/test_env_context.py
git commit -m "feat: detect drift in cc's env block from the installed binary"
```

---

## Task 7: Entry point

**Files:**
- Create: `src/claude_config/env_context/__main__.py`
- Test: `tests/test_env_context.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_env_context.py`:

```python
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def _run_hook(payload: str, env_overrides: dict[str, str]) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, "-m", "claude_config.env_context"],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_hook_emits_the_envelope(tmp_path: Path) -> None:
    payload = json.dumps(
        {
            "session_id": "abc-123",
            "transcript_path": "/dev/null",
            "cwd": str(ROOT),
            "hook_event_name": "SessionStart",
            "source": "startup",
            "model": "claude-opus-5",
        }
    )
    out = _run_hook(payload, {"CLAUDE_CODE_TMPDIR": str(tmp_path)})
    hook = out["hookSpecificOutput"]
    assert hook["hookEventName"] == "SessionStart"
    context = hook["additionalContext"]
    assert "# Environment" in context
    assert "# Scratchpad Directory" in context
    assert "You are powered by the model claude-opus-5" in context
    assert "Session ID: abc-123" in context


def test_hook_omits_model_in_print_mode(tmp_path: Path) -> None:
    payload = json.dumps(
        {
            "session_id": "abc-123",
            "transcript_path": "/dev/null",
            "cwd": str(ROOT),
            "hook_event_name": "SessionStart",
            "source": "startup",
        }
    )
    out = _run_hook(payload, {"CLAUDE_CODE_TMPDIR": str(tmp_path)})
    assert "powered by the model" not in out["hookSpecificOutput"]["additionalContext"]


def test_hook_creates_the_scratchpad(tmp_path: Path) -> None:
    payload = json.dumps(
        {
            "session_id": "xyz-789",
            "transcript_path": "/dev/null",
            "cwd": str(ROOT),
            "hook_event_name": "SessionStart",
            "source": "startup",
        }
    )
    _run_hook(payload, {"CLAUDE_CODE_TMPDIR": str(tmp_path)})
    created = list(tmp_path.glob(f"claude-{os.getuid()}/*/xyz-789/scratchpad"))
    assert len(created) == 1
    assert created[0].is_dir()


def test_hook_fails_loudly_on_malformed_payload() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "claude_config.env_context"],
        input="not json",
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
    )
    assert result.returncode != 0
    assert "Traceback" in result.stderr


def test_scratchpad_none_when_it_cannot_be_created(tmp_path: Path) -> None:
    """A cwd past cc's slug limit must cost the section, not the block."""
    deep = tmp_path / ("d" * 120) / ("e" * 120)
    deep.mkdir(parents=True)
    payload = json.dumps(
        {
            "session_id": "abc-123",
            "transcript_path": "/dev/null",
            "cwd": str(deep),
            "hook_event_name": "SessionStart",
            "source": "startup",
        }
    )
    out = _run_hook(payload, {"CLAUDE_CODE_TMPDIR": str(tmp_path)})
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "# Environment" in context
    assert "# Scratchpad Directory" not in context


def test_shell_fallback_when_no_shell_resolves(monkeypatch) -> None:
    """A shell that cannot be named must not cost the session its whole block."""
    from claude_config.env_context import __main__ as entry

    def boom() -> str:
        raise RuntimeError("no bash or zsh found")

    monkeypatch.setattr(entry.environment, "resolve_shell", boom)
    assert entry.resolved_shell() == "unknown"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: FAIL. `python -m claude_config.env_context` exits non-zero because the package has no `__main__.py`.

- [ ] **Step 3: Write the implementation**

Create `src/claude_config/env_context/__main__.py`:

```python
"""SessionStart hook: the dynamic context --system-prompt-file discards.

Claude Code assembles its own `# Environment` and `# Scratchpad Directory`
sections in `sV()` (globals/21.js:13336), and --system-prompt-file replaces
that whole assembly. Everything else the default prompt carries still arrives:
gitStatus is appended to the system prompt, and claudeMd, userEmail and
currentDate come in the system-reminder user message.

Emitting the JSON envelope is not optional. Plain stdout from a SessionStart
hook is injected as `SessionStart hook success: <text>`
(globals/20.js:24499); only hookSpecificOutput.additionalContext is injected
verbatim (globals/20.js:24485).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import drift, environment, render, scratchpad

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "docs" / "env-context-manifest.json"
CACHE = Path.home() / ".claude" / "env-context-drift.json"


def drift_note() -> str | None:
    """A drift note, or None when the pinned field set still matches.

    A failed drift check must not cost the session its env block, so the
    failure becomes a note rather than an exception. It is reported in the
    block itself, not only on stderr: stderr from a hook is not something the
    agent reads, and a check that quietly stopped running is the exact failure
    this hook exists to prevent.
    """
    try:
        return drift.cached_note(drift.find_binary(), MANIFEST, CACHE)
    except Exception as exc:  # noqa: BLE001 - surfaced in the block, not swallowed
        print(f"env-context: drift check failed: {exc}", file=sys.stderr)
        return f"env-block drift check failed ({exc}). Run scripts/check-env-context.sh."


def resolved_shell() -> str:
    """The Bash tool's shell, or cc's own literal `unknown`.

    `resolve_shell` raises when no bash or zsh exists, which is the honest
    answer for a function whose job is to name one. It is the wrong answer for
    this hook: an exception here costs the session its whole env block, and
    the block is still worth having without the shell line. `unknown` is what
    cc itself prints in that position (`Kml()`, globals/21.js:13560).
    """
    try:
        return environment.resolve_shell()
    except RuntimeError as exc:
        print(f"env-context: shell resolution failed: {exc}", file=sys.stderr)
        return "unknown"


def scratchpad_or_none(cwd: str, session_id: str) -> str | None:
    """The session scratchpad, or None when it could not be created.

    A cwd whose slug exceeds cc's 200-character limit, a read-only tmp root and
    a `claude-<uid>` owned by another user all raise here. cc survives the
    first of those by appending a hash suffix, so its session keeps working
    while this hook would die for the sake of one missing line. Losing the
    section beats losing the block.
    """
    try:
        return str(scratchpad.ensure(cwd=cwd, session_id=session_id))
    except (OSError, ValueError) as exc:
        print(f"env-context: scratchpad unavailable: {exc}", file=sys.stderr)
        return None


def main() -> int:
    payload = json.loads(sys.stdin.read())
    cwd = payload["cwd"]
    session_id = payload["session_id"]

    facts: dict[str, object] = {
        "cwd": cwd,
        "is_git_repo": environment.is_git_repo(cwd),
        "worktree_common_dir": environment.worktree_common_dir(cwd),
        "platform": environment.platform_name(),
        "shell": resolved_shell(),
        "os_version": environment.os_version(),
        "model": payload.get("model"),
        "session_id": session_id,
        "scratchpad": scratchpad_or_none(cwd, session_id),
        "drift_note": drift_note(),
    }

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": render.sections(facts),
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: PASS — the 6 new tests, plus everything already in the file

- [ ] **Step 5: Check the real output by hand**

Run:

```bash
cd /root/claude-config-work
echo '{"session_id":"manual-check","transcript_path":"/dev/null","cwd":"/root/claude-config-work","hook_event_name":"SessionStart","source":"startup","model":"claude-opus-5"}' \
  | uv run --project . python -m claude_config.env_context \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])'
```

Expected: an env block reporting `Shell: /bin/bash` (not `unknown`), `Is a git repository: true`, the two worktree lines naming `/repos/claude-config/.git`, and a `# Scratchpad Directory` section. Confirm the block contains no `NOTE:` bullet — the manifest was pinned against this same binary in Task 5.

Then clean up the directory that check created:

```bash
rmdir /tmp/claude-0/-root-claude-config-work/manual-check/scratchpad \
      /tmp/claude-0/-root-claude-config-work/manual-check
```

- [ ] **Step 6: Commit**

```bash
cd /root/claude-config-work
git add src/claude_config/env_context/__main__.py tests/test_env_context.py
git commit -m "feat: read the SessionStart payload and emit the JSON envelope

The hook discarded its stdin, so cwd was guessed from the process and
the session id and model were unavailable. The payload carries cwd,
session_id and - in interactive mode - the resolved model."
```

---

## Task 8: Wire up settings.json

**Files:**
- Modify: `settings.json:13`

- [ ] **Step 1: Replace the piped command**

Change the `SessionStart` hook command from:

```json
"command": "agent-tools env-context | jq -Rs '{hookSpecificOutput: {hookEventName: \"SessionStart\", additionalContext: .}}'",
```

to:

```json
"command": "agent-tools env-context",
```

- [ ] **Step 2: Verify the file still parses**

Run: `python3 -m json.tool /root/claude-config-work/settings.json > /dev/null && echo OK`

Expected: `OK`

- [ ] **Step 3: Verify the hook still round-trips**

The `jq` wrapper previously absorbed anything on stdout; now the hook's own stdout must be valid JSON. Confirm nothing else writes there:

```bash
cd /root/claude-config-work
echo '{"session_id":"pipe-check","transcript_path":"/dev/null","cwd":"/root/claude-config-work","hook_event_name":"SessionStart","source":"startup"}' \
  | uv run --project . python -m claude_config.env_context 2>/dev/null \
  | python3 -c 'import json,sys; json.load(sys.stdin); print("valid JSON")'
rmdir /tmp/claude-0/-root-claude-config-work/pipe-check/scratchpad \
      /tmp/claude-0/-root-claude-config-work/pipe-check
```

Expected: `valid JSON`

- [ ] **Step 4: Commit**

```bash
cd /root/claude-config-work
git add settings.json
git commit -m "chore: env-context emits its own hook envelope

The jq wrapper existed because the hook printed plain text. It now
builds hookSpecificOutput itself, which it must: plain stdout from a
SessionStart hook is injected as 'SessionStart hook success: <text>'
rather than verbatim."
```

---

## Task 9: Redirect the scratch root

**Files:**
- Modify: `scripts/claude.sh:13`

- [ ] **Step 1: Add the export**

Insert after the `CLAUDE_CODE_DISABLE_AGENT_VIEW` export on line 13:

```bash
# cc roots its scratchpad at CLAUDE_CODE_TMPDIR (globals/05.js:8056), for the
# main agent and for subagents alike, and subagents are told that path whether
# or not --system-prompt-file drops the section from this session's own prompt.
# Redirecting it here is the only way both get one directory, and /root is a
# host bind mount, so scratch survives a container rebuild that /tmp would not.
# The same variable also roots plugin dirs, skill zips and the IPC socket dir;
# cc falls back to /tmp for the socket when the path is too long (SFm(),
# globals/22.js:14393).
export CLAUDE_CODE_TMPDIR=/root/.claude/tmp
```

- [ ] **Step 2: Verify the script still parses**

Run: `bash -n /root/claude-config-work/scripts/claude.sh && echo OK`

Expected: `OK`

- [ ] **Step 3: Verify the hook follows the same root**

The hook must read the variable rather than hardcode it, so a session launched by bare `claude` still names the directory cc used:

```bash
cd /root/claude-config-work
echo '{"session_id":"root-check","transcript_path":"/dev/null","cwd":"/root/claude-config-work","hook_event_name":"SessionStart","source":"startup"}' \
  | CLAUDE_CODE_TMPDIR=/root/.claude/tmp uv run --project . python -m claude_config.env_context 2>/dev/null \
  | python3 -c 'import json,sys; print([l for l in json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"].split("\n") if "scratchpad" in l][0])'
```

Expected a line containing:

```
/root/.claude/tmp/claude-0/-root-claude-config-work/root-check/scratchpad
```

Then clean up:

```bash
rm -rf /root/.claude/tmp/claude-0/-root-claude-config-work/root-check
```

- [ ] **Step 4: Commit**

```bash
cd /root/claude-config-work
git add scripts/claude.sh
git commit -m "feat: redirect cc's scratch root to persistent disk

Subagents are given cc's scratchpad path (Xff, globals/14.js:26405)
while the main agent's copy of that section is dropped by
--system-prompt-file, so the two disagreed - 61 subagent requests in
one session named a directory the main agent was never told about.
CLAUDE_CODE_TMPDIR moves cc's own construction, so both follow.

agent-tools claude execs this script (claude.rs:84), so both
launchers are covered."
```

---

## Task 10: `scripts/check-env-context.sh`

**Files:**
- Create: `scripts/check-env-context.sh`

- [ ] **Step 1: Write the script**

```bash
#!/usr/bin/env bash
# Report when Claude Code's own env block drifts from the field set
# env-context is pinned to.
#
# Reads the installed binary's string table rather than the decompiled dump in
# /repos/claude-code-decompiled: the dump is regenerated by hand, the binary
# changes underfoot, and only the binary tracks an upgrade on its own.
#
# --update rewrites the manifest after you have reviewed a difference.
set -euo pipefail
root="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
manifest="$root/docs/env-context-manifest.json"

update=0
if [ "${1:-}" = "--update" ]; then
	update=1
fi

cd "$root"
uv run --project "$root" python - "$manifest" "$update" <<'PY'
import json
import sys
from pathlib import Path

from claude_config.env_context import drift

manifest = Path(sys.argv[1])
update = sys.argv[2] == "1"

binary = drift.find_binary()
version = drift.installed_version()
result = drift.compare(binary, manifest, version)

print(f"binary:    {binary}")
print(f"pinned:    {result.pinned_version} ({len(json.loads(manifest.read_text())['literals'])} literals)")
print(f"installed: {result.installed_version}")

if result.matches:
    print("OK: env-context field set matches the installed binary")
    sys.exit(0)

for literal in result.added:
    print(f"  + {literal!r}")
for literal in result.removed:
    print(f"  - {literal!r}")

if update:
    manifest.write_text(
        json.dumps(
            {"version": version, "literals": drift.extract_literals(binary)}, indent=2
        )
        + "\n"
    )
    print(f"updated {manifest}")
    sys.exit(0)

print()
print("FAIL: env-context field set is stale.")
print("Review src/claude_config/env_context/render.py against the change, then")
print("re-run with --update to re-pin.")
sys.exit(1)
PY
```

- [ ] **Step 2: Make it executable and run it**

```bash
cd /root/claude-config-work
chmod +x scripts/check-env-context.sh
./scripts/check-env-context.sh
```

Expected:

```
binary:    /nix/store/.../bin/claude.exe
pinned:    2.1.235 (13 literals)
installed: 2.1.235
OK: env-context field set matches the installed binary
```

- [ ] **Step 3: Verify it fails on a mutated manifest**

```bash
cd /root/claude-config-work
cp docs/env-context-manifest.json /tmp/manifest-backup-8f2k.json
python3 - <<'PY'
import json
from pathlib import Path
p = Path("docs/env-context-manifest.json")
d = json.loads(p.read_text())
d["literals"] = [x for x in d["literals"] if "Primary working" not in x]
p.write_text(json.dumps(d, indent=2) + "\n")
PY
./scripts/check-env-context.sh && echo "UNEXPECTED PASS" || echo "correctly failed"
cp /tmp/manifest-backup-8f2k.json docs/env-context-manifest.json
rm /tmp/manifest-backup-8f2k.json
git diff --quiet docs/env-context-manifest.json && echo "manifest restored"
```

Expected: a `- 'Primary working directory: '` line, `FAIL:`, `correctly failed`, then `manifest restored`.

- [ ] **Step 4: Commit**

```bash
cd /root/claude-config-work
git add scripts/check-env-context.sh
git commit -m "feat: add scripts/check-env-context.sh

Diffs the installed binary's env-block literals against the pinned
manifest. Local only, like check-prompt-coupling.sh - it needs an
installed Claude Code, which GitHub CI has not got."
```

---

## Task 11: `scripts/prune-scratch.sh`

**Files:**
- Create: `scripts/prune-scratch.sh`

- [ ] **Step 1: Write the script**

```bash
#!/usr/bin/env bash
# Report and optionally delete session scratchpads under cc's tmp root.
#
# Nothing here runs automatically. Redirecting CLAUDE_CODE_TMPDIR onto
# persistent disk means scratch no longer evaporates when the container is
# rebuilt, and this script is the only thing that reclaims it.
#
#   prune-scratch.sh                 report only (default)
#   prune-scratch.sh --apply         delete empty scratchpads
#   prune-scratch.sh --session <id> --apply
#                                    delete that session even if non-empty
set -euo pipefail

root="${CLAUDE_CODE_TMPDIR:-/tmp}/claude-$(id -u)"

apply=0
session=""
while [ $# -gt 0 ]; do
	case "$1" in
	--apply) apply=1 ;;
	--session)
		shift
		session="${1:-}"
		[ -n "$session" ] || {
			echo "prune-scratch.sh: --session needs an id" >&2
			exit 2
		}
		;;
	*)
		echo "prune-scratch.sh: unknown argument: $1" >&2
		exit 2
		;;
	esac
	shift
done

# The root is derived, not supplied, but a wrong one would be deleted from just
# as happily. Refuse anything that is not the claude-<uid> directory this
# script constructs.
case "$root" in
*/claude-"$(id -u)") ;;
*)
	echo "prune-scratch.sh: refusing to operate on unexpected root: $root" >&2
	exit 2
	;;
esac

if [ ! -d "$root" ]; then
	echo "prune-scratch.sh: no scratch root at $root; nothing to do"
	exit 0
fi

echo "scratch root: $root"
echo

empty=()
kept=()
while IFS= read -r -d '' pad; do
	if [ -z "$(ls -A "$pad")" ]; then
		empty+=("$pad")
	else
		kept+=("$pad")
	fi
done < <(find "$root" -mindepth 3 -maxdepth 3 -type d -name scratchpad -print0)

if [ ${#kept[@]} -gt 0 ]; then
	echo "keep (non-empty):"
	for pad in "${kept[@]}"; do
		printf '  %8s  %s\n' "$(du -sh "$pad" | cut -f1)" "$pad"
	done
	echo
fi

echo "prunable (empty): ${#empty[@]}"
echo "keep (non-empty): ${#kept[@]}"

if [ -n "$session" ]; then
	target="$(find "$root" -mindepth 2 -maxdepth 2 -type d -name "$session" -print -quit)"
	if [ -z "$target" ]; then
		echo "prune-scratch.sh: no session directory named $session under $root" >&2
		exit 1
	fi
	echo
	echo "session target: $target ($(du -sh "$target" | cut -f1))"
	if [ "$apply" -eq 0 ]; then
		echo "(dry run; re-run with --apply to delete it)"
		exit 0
	fi
	rm -rf -- "$target"
	echo "deleted $target"
	exit 0
fi

if [ "$apply" -eq 0 ]; then
	echo
	echo "(dry run; re-run with --apply to delete the ${#empty[@]} empty ones)"
	exit 0
fi

for pad in "${empty[@]}"; do
	rmdir -- "$pad"
	rmdir --ignore-fail-on-non-empty -- "$(dirname "$pad")"
done
echo
echo "deleted ${#empty[@]} empty scratchpads"
```

- [ ] **Step 2: Make it executable and run the dry run**

```bash
cd /root/claude-config-work
chmod +x scripts/prune-scratch.sh
./scripts/prune-scratch.sh
```

Expected: `scratch root: /tmp/claude-0` (the redirect only applies to sessions started by the updated `claude.sh`), a `keep (non-empty)` list of about 9 directories with sizes, and counts of roughly 130 prunable and 9 kept. It must print `(dry run; ...)` and delete nothing.

- [ ] **Step 3: Verify deletion on a synthetic root**

Never test deletion against the real root.

```bash
FAKE=/tmp/prune-test-m4x7q2
rm -rf "$FAKE"
mkdir -p "$FAKE/claude-$(id -u)/-some-project/session-empty/scratchpad"
mkdir -p "$FAKE/claude-$(id -u)/-some-project/session-full/scratchpad"
echo data > "$FAKE/claude-$(id -u)/-some-project/session-full/scratchpad/file.txt"

CLAUDE_CODE_TMPDIR="$FAKE" /root/claude-config-work/scripts/prune-scratch.sh --apply

echo "--- after ---"
test ! -d "$FAKE/claude-$(id -u)/-some-project/session-empty" && echo "empty session removed"
test -f "$FAKE/claude-$(id -u)/-some-project/session-full/scratchpad/file.txt" && echo "non-empty session preserved"
rm -rf "$FAKE"
```

Expected: `prunable (empty): 1`, `keep (non-empty): 1`, `deleted 1 empty scratchpads`, then `empty session removed` and `non-empty session preserved`.

- [ ] **Step 4: Commit**

```bash
cd /root/claude-config-work
git add scripts/prune-scratch.sh
git commit -m "feat: add scripts/prune-scratch.sh

Scratch on persistent disk no longer evaporates on container rebuild.
Deletion is manual and empty-only by default: a non-empty scratchpad
may hold work in progress and a session id does not distinguish a
dead session from a live one."
```

---

## Task 12: Documentation

**Files:**
- Modify: `CLAUDE.md:51`, `CLAUDE.md:144`, the `scripts/` row in `CLAUDE.md`, and the `scripts/claude.sh` section
- Modify: `docs/superpowers/specs/2026-09-02-env-context-design.md`

- [ ] **Step 1: Update the `agent-tools env-context` bullet**

Replace the `env-context` bullet in the `agent-tools/` subcommand list with:

```markdown
- `agent-tools env-context` — SessionStart hook supplying the dynamic context `--system-prompt-file` discards: a `# Environment` block and a `# Scratchpad Directory` section. Reads the hook payload on stdin (`cwd`, `session_id`, and `model` in interactive mode) and emits the `hookSpecificOutput` envelope itself — plain stdout would be injected as `SessionStart hook success: <text>` instead of verbatim. The `Shell` field reports the shell the Bash tool actually runs, not the `$SHELL` Claude Code reports and prints `unknown` for when unset. Warns when Claude Code's own env block drifts from the pinned field set in `docs/env-context-manifest.json`; `scripts/check-env-context.sh` shows the difference.
```

- [ ] **Step 2: Update the Python module table row**

Replace the `claude_config.env_context` row with:

```markdown
| `claude_config.env_context`     | SessionStart hook: `# Environment` and `# Scratchpad Directory` for `--system-prompt-file` sessions | `agent-tools env-context` |
```

- [ ] **Step 3: Update the `scripts/` directory row**

Replace the `scripts/` row in the Subdirectories table with:

```markdown
| `scripts/`         | Standalone scripts — `claude.sh` launcher, MITM proxy, `reasoning-probe.py`, `prompt-test-run.sh`, `check-env-context.sh`, `prune-scratch.sh` | Running or modifying utility scripts              |
```

- [ ] **Step 4: Document the scratch redirect**

Append to the `### scripts/claude.sh` section:

```markdown
It also exports `CLAUDE_CODE_TMPDIR=/root/.claude/tmp`. Claude Code roots its
per-session scratchpad there (`Spe()`, `globals/05.js:8056`), and it names that
path to subagents (`Xff`, `globals/14.js:26405`) whether or not
`--system-prompt-file` drops the section from the main agent's own prompt.
Redirecting the root is therefore the only way both agree on one directory —
and `/root` is a host bind mount, so scratch survives a container rebuild that
`/tmp` would not. The same variable also roots plugin session directories,
skill and plugin zip staging, and the IPC socket directory; Claude Code falls
back to `/tmp` for the socket when the path exceeds the `sun_path` limit
(`SFm()`, `globals/22.js:14393`).

Scratch is now persistent, so nothing reclaims it automatically.
`scripts/prune-scratch.sh` reports and, with `--apply`, deletes empty session
scratchpads.
```

- [ ] **Step 5: Correct the manifest filename in the spec**

In `docs/superpowers/specs/2026-09-02-env-context-design.md`, change the Files-table row `docs/env-context-manifest.txt` to `docs/env-context-manifest.json`, and in the drift-check section change "a checked-in manifest recording the cc version and the literal set" to "a checked-in JSON manifest recording the cc version and the literal set — JSON because the literals carry significant trailing spaces".

- [ ] **Step 6: Verify no stale references remain**

```bash
cd /root/claude-config-work
grep -rn "env-context | jq\|env-context-manifest.txt" --include="*.md" --include="*.json" . || echo "no stale references"
```

Expected: `no stale references`

- [ ] **Step 7: Commit**

```bash
cd /root/claude-config-work
git add CLAUDE.md docs/superpowers/specs/2026-09-02-env-context-design.md
git commit -m "docs: describe the env-context rewrite and scratch redirect"
```

---

## Task 13: Full verification

**Files:** none modified

- [ ] **Step 1: Tidy the test file's imports**

Each task appended to `tests/test_env_context.py`, so its imports are scattered
through the file. Move every `import` to the top, in one block, ordered
stdlib-then-local:

```python
"""Tests for the env-context SessionStart hook."""

import importlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

from claude_config.env_context import drift, environment, render, scratchpad
```

Delete the now-duplicated import lines from the body. Then re-run:
`uv run --project /root/claude-config-work pytest tests/test_env_context.py -v`

Expected: PASS — every test in the file, unchanged in count by the tidy-up

Commit:

```bash
cd /root/claude-config-work
git add tests/test_env_context.py
git commit -m "style: collect test imports at the top of the file"
```

- [ ] **Step 2: Run the whole test suite**

Run: `uv run --project /root/claude-config-work pytest -q`

Use the bare invocation, not `pytest tests/`: `testpaths` in `pyproject.toml` also covers `skills/scripts/tests`, so naming the directory silently collects a fraction of the suite.

Expected: PASS. `test_env_context.py` contributes every test added by Tasks 1-7; the pre-existing `test_cc_pretty_render.py`, `test_cc_pretty_intercept.py`, `test_opencode_pretty.py` and `test_install.py` must be unaffected — this change touches none of their code.

- [ ] **Step 3: Run both new scripts**

```bash
cd /root/claude-config-work
./scripts/check-env-context.sh
./scripts/prune-scratch.sh
```

Expected: the drift check prints `OK`; the prune script prints its report and `(dry run; ...)`.

- [ ] **Step 4: Run the existing coupling check for regressions**

Run: `/root/claude-config-work/scripts/check-prompt-coupling.sh`

Expected: exit 0. This change touches no `agent-tools` Rust source or `sys_prompt/` text, so it must still pass.

- [ ] **Step 5: Exercise the hook end to end in a throwaway session**

This is the only step that proves the wiring, rather than the parts. It launches a real Claude Code against a scratch config directory, so it cannot disturb the live session.

```bash
D=/tmp/env-ctx-verify-p3w9k5
rm -rf "$D"; mkdir -p "$D/cfg"
cat > "$D/cfg/settings.json" <<'EOF'
{"theme":"dark","hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"cat > /tmp/env-ctx-verify-p3w9k5/payload.json","timeout":5}]}]}}
EOF
cat > "$D/cfg/.claude.json" <<'EOF'
{"hasCompletedOnboarding":true,"lastOnboardingVersion":"2.1.235","theme":"dark","numStartups":5,"bypassPermissionsModeAccepted":true,
 "projects":{"/tmp/env-ctx-verify-p3w9k5":{"hasTrustDialogAccepted":true,"hasCompletedProjectOnboarding":true,"projectOnboardingSeenCount":3,"allowedTools":[],"history":[]}}}
EOF
timeout 90 python3 - <<'PY'
import os, pty, time, signal, select
D="/tmp/env-ctx-verify-p3w9k5"
env=dict(os.environ); env["CLAUDE_CONFIG_DIR"]=f"{D}/cfg"; env["TERM"]="xterm-256color"
pid, fd = pty.fork()
if pid == 0:
    os.chdir(D); os.execvpe("claude", ["claude","--model","haiku"], env)
deadline=time.time()+40
while time.time()<deadline:
    r,_,_=select.select([fd],[],[],0.5)
    if r:
        try: os.read(fd,8192)
        except OSError: break
    p=f"{D}/payload.json"
    if os.path.exists(p) and os.path.getsize(p)>0: time.sleep(0.5); break
try: os.kill(pid,signal.SIGKILL); os.waitpid(pid,0)
except Exception: pass
PY
echo "=== feed the real payload through the hook ==="
cd /root/claude-config-work
uv run --project . python -m claude_config.env_context < "$D/payload.json" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])'
rm -rf "$D"
```

Expected: a complete `# Environment` block for `/tmp/env-ctx-verify-p3w9k5` reporting `Shell: /bin/bash` and `Is a git repository: false`, with no worktree lines, plus a `# Scratchpad Directory` section. The payload was produced by a real Claude Code, so this proves the field names the hook reads are the field names cc sends.

Then remove the scratchpad that run created:

```bash
rm -rf "/tmp/claude-0/-tmp-env-ctx-verify-p3w9k5"
```

- [ ] **Step 6: Report what remains manual**

The redirect in `scripts/claude.sh` only takes effect for sessions started after this change. Tell the user that:

- Sessions already running keep `/tmp/claude-0`; the new root appears on next launch.
- The existing 1.3 GB under `/tmp/claude-0` is not migrated and evaporates when the container is rebuilt. `scripts/prune-scratch.sh` can report it in the meantime.
- Nothing was installed; `install.sh` was not run, and `agent-tools` was not rebuilt because no Rust changed.

---

## Self-review

**Spec coverage.** Scope → Tasks 4, 7. Hook input → Task 7. Env block fields → Tasks 2, 4. Worktree lines → Tasks 2, 4. Scratchpad redirect → Task 9. Scratchpad reporting and creation → Tasks 3, 4, 7. Pruning → Task 11. Drift check → Tasks 5, 6, 10. Files table → all tasks. Tests → each task's test step plus Task 13. Risks → Task 13 Step 5. Out of scope → no task, correctly.

**Deviation from the spec.** The manifest is `.json`, not `.txt`; Task 12 Step 5 amends the spec.

**Type consistency.** `resolve_shell`, `is_git_repo`, `worktree_common_dir`, `os_version`, `platform_name` in `environment.py` are called under those names in `__main__.py`. `tmp_root`, `project_slug`, `scratchpad_path`, `ensure` in `scratchpad.py` likewise. `find_binary`, `extract_literals`, `installed_version`, `compare`, `cached_note` and the `Comparison` fields `matches`/`installed_version`/`pinned_version`/`added`/`removed` are used consistently in `drift.py`, `__main__.py` and `check-env-context.sh`. The `facts` dict keys built in `__main__.py` — `cwd`, `is_git_repo`, `worktree_common_dir`, `platform`, `shell`, `os_version`, `model`, `session_id`, `scratchpad`, `drift_note` — match those read in `render.py` and those in the test helper `_facts`.

#!/usr/bin/env python3
"""Capture what each built-in skill delivers into the model's context.

A default capture records every built-in skill's *name and description* -- they
ride in the same reminder block as the agent-type listing -- but never its body.
The body arrives only when the skill is invoked, as an injected message, and it
is the part that changes between releases. This captures that.

Two routes, because no single one reaches every skill:

    slash   typing `/<name>` injects the body before the model acts at all
    skill   the Skill tool, for the ones that are not slash commands

Route `slash` is tried first and `skill` only when it yields nothing, so each
skill costs one session in the common case. A skill that yields no body under
either route is recorded with the reason rather than an empty file -- a forked
skill runs as a background agent, an entitlement-gated one substitutes a stub,
and both are facts about the release worth keeping.

A skill that ships files has them written to a per-process directory as it is
invoked, and its body opens by naming that directory. Those files are read off
the disk after the session and kept beside the body: they are what the body
tells the model to read.

Output:
    builtin-skills/<name>.md    the delivered text, volatile paths normalized
    builtin-skills/<name>/      the files Claude Code extracted for it, verbatim
                                but for the same normalization
    builtin-skills/manifest.json  shape, size, sha256 and route per skill, and
                                size and sha256 per extracted file

Usage:
    ./capture_skills.py                      # every built-in skill
    ./capture_skills.py loop workflow-authoring
    ./capture_skills.py --model claude-sonnet-5
    ./capture_skills.py --list               # names only, no capture

Prerequisites: the same credentials and MITM proxy capture.py needs.
"""

import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

# `capture` is imported where it is used, not here: importing it loads the repo
# .env, strips proxy variables from the environment and needs the anthropic SDK,
# none of which the roster parsing and normalization below touch. Keeping the
# import inside the spawning functions lets those be read and tested on their own.

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / "builtin-skills"

# Where the roster comes from. Read from a committed capture rather than listed
# here, so a release that adds or drops a built-in skill is picked up without
# this file being edited.
ROSTER_SOURCE = SCRIPT_DIR / "opus-5" / "default" / "request.json"

_SKILL_INTRO = "The following skills are available for use with the Skill tool:"
_SKILL_LINE = re.compile(r"^- ([A-Za-z0-9][A-Za-z0-9:_-]*):")

# Text the harness puts in the conversation that is not skill content. All of it
# would otherwise compete with the body for "longest block", and some of it wins:
# the deferred-tools reminder is longer than several real skill bodies.
#
# The bare spellings are not redundant with the tagged ones. Sonnet wraps each
# reminder in <system-reminder> tags and opus emits the same text untagged, so
# matching only the tag silently captures a reminder as the body on opus.
_WRAPPERS = (
    "<system-reminder>",
    "<command-message>",
    "<command-name>",
    "<local-command-caveat>",
    "<local-command-stdout>",
    "<local-command-stderr>",
    "<tool_use_error>",
    "<total_tokens>",
    "<task-notification>",
    "# Environment",
    "Launching skill:",
    # Reminders, as opus emits them: no tag.
    "The following deferred tools",
    "The following skills are available",
    "Available agent types for the Agent tool:",
    "You are powered by the model named",
    "As you answer the user's questions",
    "Attribution for git commits",
    "Caveat: The messages below were generated",
)

# Openers belonging to Claude Code's own auxiliary calls rather than to the
# conversation. A session issues several of these against the same pid, so they
# reach the proxy log alongside the real turn.
_AUXILIARY = (
    "[SUGGESTION MODE",
    "Summarize this coding conversation",
    "Please write a 5-10 word title",
)

# A body under this many characters is a substitute, not the skill: the gated
# `/design` reply is 169 characters and `/schedule`'s connection failure is 139.
# The smallest real body measured is `/init` at 2,312.
_STUB_MAX = 400


def builtin_skill_names(request_path: Path) -> list[str]:
    """Built-in skill names, in the order the capture's own listing gives them.

    The listing in a capture is exactly the built-in set: a capture runs in a
    fresh temp directory under `--setting-sources project,local`, so no plugin
    or repository skill is in scope to appear alongside them.
    """
    data = json.loads(request_path.read_text())
    for msg in data.get("messages", []):
        content = msg.get("content", [])
        blocks = [{"text": content}] if isinstance(content, str) else content
        for block in blocks:
            text = block.get("text", "")
            if _SKILL_INTRO not in text:
                continue
            tail = text.split(_SKILL_INTRO, 1)[1]
            names = [
                m.group(1)
                for line in tail.splitlines()
                if (m := _SKILL_LINE.match(line))
            ]
            if names:
                return names
    raise RuntimeError(
        f"{request_path} carries no skill listing; the reminder format changed "
        "or the capture predates it."
    )


# The line Claude Code prefixes to the body of a skill that ships files, naming
# the directory it has just written them to (`wis`, src/chunk-nh7xtj5c.js:108):
# `<tmp>/claude-<uid>/bundled-skills/<version>/<random hex per process>/<name>`.
# Absent when the write failed, which Claude Code only logs.
_BASE_DIR_LINE = re.compile(r"^Base directory for this skill: (\S+)$", re.MULTILINE)

# A path the normalized body names under that directory.
_DIR_REF = re.compile(r"<bundled-skills-dir>/([^\s`'\"()<>\[\]]+)")


def _placeholders(body: str | None, log_files: list[Path]) -> dict[str, str]:
    """This run's own values, each mapped to the placeholder that stands for it.

    Each differs between two captures of one release for a reason that has
    nothing to do with the release: the extraction directory carries a random
    hex per process, the child's session id and working directory are fresh per
    run, and the config directory is wherever the operator put it --
    `plugin-authoring` names `<config dir>/dev-mods/<session id>`. Replacing the
    exact values rather than path shapes keeps whatever follows them, so a body's
    `<bundled-skills-dir>/examples/pane.tsx` still says which file it means.
    """
    values: dict[str, str] = {}
    base = _BASE_DIR_LINE.search(body or "")
    if base:
        values[base.group(1)] = "<bundled-skills-dir>"
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    values[os.path.normpath(config_dir)] = "<config-dir>"
    for log_path in log_files:
        session = json.loads(log_path.read_text()).get("session") or {}
        if session.get("session_id"):
            values[session["session_id"]] = "<session-id>"
        if session.get("cwd"):
            values[session["cwd"]] = "<cwd>"
    return values


def _normalize(text: str, values: dict[str, str]) -> tuple[str, bool]:
    """Replace each of `values` with its placeholder, longest value first.

    Longest first because one value can hold another: a config directory made
    inside a session's scratchpad holds that session's id. A path must end
    where a path segment does, so the config directory `/root/.claude` leaves
    `/root/.claude.json` alone while a sentence's closing full stop still ends
    it; a session id is replaced wherever it occurs, `<id>.jsonl` included.
    """
    changed = False
    for value in sorted(values, key=len, reverse=True):
        placeholder = values[value]
        end = r"(?![\w-])(?!\.\w)" if value.startswith("/") else ""
        pattern = re.compile(re.escape(value) + end)
        text, n = pattern.subn(lambda _m: placeholder, text)
        changed = changed or bool(n)
    return text, changed


def _bundled_files(base_dir: str) -> dict[str, bytes]:
    """Every file under a skill's extraction directory, keyed by relative path.

    Read off the disk after the session: Claude Code writes the directory as
    the skill is invoked and nothing removes it at exit (`r7n`,
    `src/chunk-8wf3pk41.js:8048`, `"bundled-skills"`; writer `IJn`,
    `src/chunk-nh7xtj5c.js:38`, which also refuses symlinks with `O_NOFOLLOW`).
    """
    root = Path(base_dir)
    if not root.is_dir():
        raise RuntimeError(
            f"the body names {root} as its base directory and it does not exist: "
            "Claude Code no longer leaves the extraction directory behind, so its "
            "files cannot be read after the session."
        )
    files: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise RuntimeError(f"{path}: not a regular file or directory")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    if not files:
        # The base-directory line is emitted only after a write of at least one
        # file succeeded (`R`, src/chunk-nh7xtj5c.js:193).
        raise RuntimeError(f"{root} names no file although the body says it does")
    return files


def _unresolved_refs(body: str, files: dict) -> list[str]:
    """Paths the normalized body names under `<bundled-skills-dir>` that no
    captured file is or contains."""
    missing = []
    for m in _DIR_REF.finditer(body):
        ref = m.group(1).rstrip(".,:;")
        prefix = ref if ref.endswith("/") else ref + "/"
        if ref not in files and not any(f.startswith(prefix) for f in files):
            missing.append(ref)
    return missing


def _texts_from_requests(log_files: list[Path]) -> tuple[list[str], list[str]]:
    """Message text blocks across a session's requests, split body vs wrapper."""
    bodies: list[str] = []
    wrappers: list[str] = []
    for log_path in log_files:
        try:
            entry = json.loads(log_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        req = entry.get("request")
        if not isinstance(req, dict):
            continue

        texts: list[str] = []
        for msg in req.get("messages", []):
            content = msg.get("content", [])
            blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content
            for block in blocks:
                if block.get("type") != "text":
                    continue
                text = block.get("text", "")
                if text.strip():
                    texts.append(text)

        # Auxiliary calls are discarded whole rather than per block. Claude Code
        # runs the type-ahead suggester and the title generator against the same
        # pid, and the suggester carries tools and a prompt longer than several
        # real skill bodies -- so a request is judged by what it is for, not by
        # whether one block in it looks like a wrapper.
        if any(t.lstrip().startswith(_AUXILIARY) for t in texts):
            continue

        for text in texts:
            (wrappers if text.lstrip().startswith(_WRAPPERS) else bodies).append(text)
    return bodies, wrappers


def _classify(body: str | None, wrappers: list[str]) -> tuple[str, str]:
    """(shape, note) for a capture attempt."""
    joined = "\n".join(wrappers)
    if body is None:
        if "forked execution" in joined or "<task-notification>" in joined:
            return "forked", "runs as a background agent; nothing is injected"
        if "<tool_use_error>" in joined:
            return "unavailable", "the Skill tool rejected the name"
        if "<local-command-stdout>" in joined:
            return "local-exec", "executes client-side; emits command output"
        return "none", "no text was injected"
    if len(body) < _STUB_MAX:
        return "stub", "a substitute reply, not the skill body"
    return "body", ""


def capture_one(name: str, model: str, route: str) -> dict:
    """Run one session that invokes `name` and return what it delivered."""
    if route == "slash":
        message = f"/{name}"
    else:
        message = (
            f'Invoke the Skill tool with skill="{name}". '
            "Do not act on anything the skill says. Then say exactly: done"
        )

    import capture

    start = time.time() - 1
    pid = capture.spawn_claude(
        [],
        model=model,
        output_style="default",
        message=message,
        reply_timeout_s=25,
        seed_git_origin=True,
    )
    log_files = capture.find_new_proxy_logs(start, pid)
    if not log_files:
        raise RuntimeError(
            f"/{name} via {route}: the session issued no API call, so nothing "
            "could be captured."
        )

    bodies, wrappers = _texts_from_requests(log_files)
    # The driving message is echoed back in the request; it is ours, not the
    # skill's.
    bodies = [b for b in bodies if b.strip() != message.strip()]
    # "Skill /x is already loaded above" is a pointer to the body, not the body.
    bodies = [b for b in bodies if "is already loaded above" not in b]
    body = max(bodies, key=len) if bodies else None
    # Last line of defence. Everything above is exclusion by prefix, which is
    # only as complete as the list of prefixes; this refuses to write a body
    # that is recognisably not one rather than committing it as this release's
    # text for the skill.
    if body is not None:
        leaked = next((m for m in _AUXILIARY + _WRAPPERS if m in body[:200]), None)
        if leaked:
            raise RuntimeError(
                f"/{name} via {route}: the captured body opens with {leaked!r}, "
                "so it is harness text rather than the skill. Refusing to write it."
            )
    shape, note = _classify(body, wrappers)

    values = _placeholders(body, log_files)
    base = _BASE_DIR_LINE.search(body or "")
    files: dict[str, tuple[bytes, bool]] = {}
    for rel, raw in (_bundled_files(base.group(1)) if base else {}).items():
        text, changed = _normalize(raw.decode("utf-8"), values)
        files[rel] = (text.encode("utf-8"), changed)
    normalized = False
    if body is not None:
        body, normalized = _normalize(body, values)
        # A file the body tells the model to read and the capture does not hold
        # would commit a body pointing at nothing.
        missing = _unresolved_refs(body, files)
        if missing:
            raise RuntimeError(
                f"/{name} via {route}: the body names {', '.join(missing)} under its "
                "base directory and no extracted file is there."
            )
    return {"body": body, "normalized": normalized, "files": files,
            "shape": shape, "note": note, "route": route}


def capture_skill(name: str, model: str) -> dict:
    """Try the slash route, fall back to the Skill tool, keep the better result.

    A route that returns harness text instead of a body raises, and that is not
    fatal on its own: it means this route did not reach the skill, so the other
    one still gets its turn. Only both routes failing is a failure.
    """
    errors: list[str] = []
    attempt: dict | None = None
    try:
        attempt = capture_one(name, model, "slash")
    except RuntimeError as exc:
        errors.append(str(exc))

    if attempt is None or attempt["shape"] != "body":
        try:
            second = capture_one(name, model, "skill")
        except RuntimeError as exc:
            errors.append(str(exc))
        else:
            # A stub is more informative than "unknown command", so the second
            # attempt only wins when it actually did better.
            if attempt is None or second["shape"] == "body" or attempt["shape"] in (
                "none",
                "unavailable",
            ):
                attempt = second

    if attempt is None:
        raise RuntimeError("; ".join(errors))
    return attempt


def main() -> None:
    import capture

    args = sys.argv[1:]

    model = "claude-opus-5"
    if "--model" in args:
        i = args.index("--model")
        model = args[i + 1]
        args = args[:i] + args[i + 2:]

    names = builtin_skill_names(ROSTER_SOURCE)
    if "--list" in args:
        print("\n".join(names))
        return

    wanted = [a for a in args if not a.startswith("-")]
    if wanted:
        unknown = [w for w in wanted if w not in names]
        if unknown:
            print(
                f"ERROR: not built-in skills: {', '.join(unknown)}\n"
                f"Known: {', '.join(names)}",
                file=sys.stderr,
            )
            sys.exit(1)
        names = wanted

    if not capture.proxy_is_running():
        capture.start_proxy()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    )
    manifest.setdefault("skills", {})
    manifest["model"] = model

    # The manifest is merged, not rewritten, so a partial run keeps every other
    # entry; a full-roster run is the authority on the set, and a skill the
    # release dropped loses its entry and body here rather than surviving
    # forever.
    if not wanted:
        for stale in sorted(set(manifest["skills"]) - set(names)):
            del manifest["skills"][stale]
            (OUT_DIR / f"{stale}.md").unlink(missing_ok=True)
            if (OUT_DIR / stale).is_dir():
                shutil.rmtree(OUT_DIR / stale)
            print(f"pruned {stale}: no longer in the roster", flush=True)

    failures = []
    for n, name in enumerate(names, 1):
        print(f"[{n}/{len(names)}] {name}", flush=True)
        try:
            result = capture_skill(name, model)
        except RuntimeError as exc:
            print(f"    FAILED: {exc}", file=sys.stderr)
            failures.append(name)
            continue

        entry = {
            "shape": result["shape"],
            "route": result["route"],
        }
        if result["note"]:
            entry["note"] = result["note"]

        if result["body"] is None:
            (OUT_DIR / f"{name}.md").unlink(missing_ok=True)
            entry["chars"] = 0
        else:
            text = result["body"]
            (OUT_DIR / f"{name}.md").write_text(text, encoding="utf-8")
            entry["chars"] = len(text)
            entry["sha256"] = hashlib.sha256(text.encode()).hexdigest()
            if result["normalized"]:
                entry["normalized_paths"] = True

        # Rewritten whole, so a file the release stopped shipping goes too.
        files_dir = OUT_DIR / name
        if files_dir.is_dir():
            shutil.rmtree(files_dir)
        if result["files"]:
            entry["files"] = {}
            for rel, (data, changed) in result["files"].items():
                (files_dir / rel).parent.mkdir(parents=True, exist_ok=True)
                (files_dir / rel).write_bytes(data)
                entry["files"][rel] = {
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
                if changed:
                    entry["files"][rel]["normalized_paths"] = True
        # Losing every file reads in the diff as the release dropping them, and
        # it can also be a failed write or, for artifact-capabilities, a failed
        # fetch of its type definitions -- which Claude Code only logs.
        before = manifest["skills"].get(name, {}).get("files", {})
        if before and not result["files"]:
            print(
                f"    WARNING: {name} shipped {len(before)} files in the last "
                "capture and none in this one; check that the release dropped "
                "them before committing.",
                file=sys.stderr,
            )

        manifest["skills"][name] = entry
        detail = f"{entry['chars']:,} chars" if entry["chars"] else result["note"]
        if result["files"]:
            detail += f", {len(result['files'])} files"
        print(f"    {result['shape']:<12} via {result['route']:<5}  {detail}")

    manifest["skills"] = dict(sorted(manifest["skills"].items()))
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    shapes: dict[str, int] = {}
    for entry in manifest["skills"].values():
        shapes[entry["shape"]] = shapes.get(entry["shape"], 0) + 1
    print("\n" + ", ".join(f"{v} {k}" for k, v in sorted(shapes.items())))
    if failures:
        print(f"FAILED: {', '.join(failures)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

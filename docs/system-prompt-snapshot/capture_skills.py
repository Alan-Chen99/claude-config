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

Output:
    builtin-skills/<name>.md    the delivered text, volatile paths normalized
    builtin-skills/manifest.json  shape, size, sha256 and route per skill

Usage:
    ./capture_skills.py                      # every built-in skill
    ./capture_skills.py loop workflow-authoring
    ./capture_skills.py --model claude-sonnet-5
    ./capture_skills.py --list               # names only, no capture

Prerequisites: the same credentials and MITM proxy capture.py needs.
"""

import hashlib
import json
import re
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


def _normalize(text: str) -> tuple[str, bool]:
    """Replace per-run paths so the same release renders the same bytes.

    A skill shipping resource files is extracted to
    `<tmp>/bundled-skills/<version>/<random hex>/<name>` and told to the model as
    an absolute path, so its body differs on every capture in a way that has
    nothing to do with the release.
    """
    subs = (
        (re.compile(r"(?<=Base directory for this skill: )\S+"), "<bundled-skills-dir>"),
        (re.compile(r"/tmp/capture-cwd-\w+"), "<cwd>"),
        (re.compile(r"/tmp/claude-\d+/[^\s`'\"]+"), "<scratchpad>"),
    )
    changed = False
    for pattern, replacement in subs:
        text, n = pattern.subn(replacement, text)
        changed = changed or bool(n)
    return text, changed


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
    return {"body": body, "shape": shape, "note": note, "route": route}


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
            text, normalized = _normalize(result["body"])
            (OUT_DIR / f"{name}.md").write_text(text)
            entry["chars"] = len(text)
            entry["sha256"] = hashlib.sha256(text.encode()).hexdigest()
            if normalized:
                entry["normalized_paths"] = True

        manifest["skills"][name] = entry
        detail = f"{entry['chars']:,} chars" if entry["chars"] else result["note"]
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

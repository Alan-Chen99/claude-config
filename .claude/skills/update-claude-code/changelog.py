#!/usr/bin/env python3
"""Print the release notes Claude Code ships inside its own binary.

Upstream writes these; nothing else in this runbook does. They name the change
behind a diff you would otherwise have to explain from evidence — the `Agent`
tool's schema moving in 2.1.269 is "`CLAUDE_CODE_SUBAGENT_MODEL` became a
default rather than an override" at 2.1.251, which no capture or decompiled
identifier says out loud.

Bounds worth knowing before trusting a quiet run:

  the binary carries a fixed window, 15 entries in 2.1.269 (2.1.247-2.1.268),
    so an upgrade spanning more releases than that loses the oldest silently
  the running version has no entry of its own
  a release with no user-facing notes has no entry either, so a gap in the
    sequence is not evidence of a missing window

Usage:
    ./changelog.py                  every entry the binary carries
    ./changelog.py 2.1.235          only entries above that version
    ./changelog.py 2.1.235 /some/src   a decompiled tree other than the default
"""

import json
import re
import sys
from pathlib import Path

DEFAULT_SRC = Path("/repos/claude-code-decompiled/src")

# The notes are one double-quoted JS string literal, so they survive `json.loads`
# intact — including the `\uXXXX` the decompiler writes for every non-ASCII
# character. The chunk holding it is renamed on every extraction; this opening
# is not.
_OPENING = re.compile(r'"## \d+\.\d+\.\d+\\n')
_HEADING = re.compile(r"^## (\d+)\.(\d+)\.(\d+)$")


def _literal_end(src: str, start: int) -> int:
    """Index of the quote closing the literal that opens at `start`."""
    i = start + 1
    while True:
        i = src.index('"', i + 1)
        if src[i - 1] != "\\":
            return i


def changelog(src_dir: Path) -> str:
    hits = []
    for path in sorted(src_dir.rglob("*.js")):
        body = path.read_text(encoding="utf-8", errors="replace")
        match = _OPENING.search(body)
        if match:
            hits.append((path, body, match.start()))
    if len(hits) != 1:
        raise SystemExit(
            f"expected exactly one file carrying the release notes, found {len(hits)}"
            f"{': ' + ', '.join(str(p) for p, _, _ in hits) if hits else ''}"
        )
    path, body, start = hits[0]
    return json.loads(body[start : _literal_end(body, start) + 1])


def main() -> int:
    args = sys.argv[1:]
    since = None
    if args and _HEADING.match("## " + args[0]):
        since = tuple(int(n) for n in args[0].split("."))
        args = args[1:]
    src_dir = Path(args[0]) if args else DEFAULT_SRC
    if not src_dir.is_dir():
        print(f"decompiled tree not found: {src_dir}", file=sys.stderr)
        return 2

    text = changelog(src_dir)
    if since is None:
        print(text)
        return 0

    keep, printing = [], False
    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading:
            printing = tuple(int(n) for n in heading.groups()) > since
        if printing:
            keep.append(line)
    if not keep:
        print(f"no entry above {'.'.join(str(n) for n in since)}", file=sys.stderr)
        return 1
    print("\n".join(keep))
    return 0


if __name__ == "__main__":
    sys.exit(main())

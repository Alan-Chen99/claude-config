#!/usr/bin/env python3
"""Print the release notes Claude Code ships inside its own binary.

They name the change behind a diff that nothing else in the runbook can explain.
Bounds worth knowing before trusting a quiet run:

  the binary carries a fixed window -- 6 entries in 2.1.289 (2.1.282-2.1.287),
    15 in 2.1.269 -- so an upgrade spanning more releases than that loses the
    oldest silently; given a version older than the window this script says so
    on stderr
  the running version has no entry of its own
  a release with no user-facing notes has no entry either, so a gap in the
    sequence is not evidence of a missing window

The binary also fetches upstream's whole CHANGELOG.md at startup into
`<config dir>/cache/changelog.md` (what `/release-notes` reads); for releases
the embedded window does not reach, read that file or
https://raw.githubusercontent.com/anthropics/claude-code/refs/heads/main/CHANGELOG.md

Usage:
    ./changelog.py                  every entry the binary carries
    ./changelog.py 2.1.235          only entries above that version
    ./changelog.py 2.1.235 /some/src   a decompiled tree other than the default
"""

import re
import sys
from pathlib import Path

DEFAULT_SRC = Path("/repos/claude-code-decompiled/src")
UPSTREAM = "https://raw.githubusercontent.com/anthropics/claude-code/refs/heads/main/CHANGELOG.md"

# The notes are one JS string literal. The chunk holding it is renamed on every
# extraction and the quote style is the minifier's choice -- double in 2.1.269,
# single in 2.1.289 because the text is full of double quotes -- so match the
# opening heading under either quote.
_OPENING = re.compile(r"""(["'])## \d+\.\d+\.\d+\\n""")
_HEADING = re.compile(r"^## (\d+)\.(\d+)\.(\d+)$")
_ESCAPE = re.compile(r"\\(u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|[^ux])", re.S)
_SIMPLE_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}


def _literal_end(src: str, start: int) -> int:
    """Index of the quote closing the literal that opens at `start`.

    A quote is escaped by an odd run of backslashes, not merely by one: `\\"`
    closes nothing, `\\\\"` closes the literal. Looking at a single preceding
    character reads the second as escaped, runs past the true end into
    unrelated JS, and hands the decoder a slice that is not one literal.
    Release notes ending in a literal backslash are all it would take.
    """
    quote = src[start]
    i = start + 1
    while True:
        i = src.index(quote, i)
        run = 0
        while src[i - 1 - run] == "\\":
            run += 1
        if run % 2 == 0:
            return i
        i += 1


def _decode(literal: str) -> str:
    """The text of one JS string literal, quotes included.

    `json.loads` would do for a double-quoted literal and nothing else, and the
    escapes are the same set under either quote. The decompiler writes every
    non-ASCII character as `\\uXXXX`, astral ones as a surrogate pair, so the
    pairs are re-joined after the escapes are resolved.
    """

    def one(match: re.Match[str]) -> str:
        esc = match.group(1)
        if esc[0] in "ux":
            return chr(int(esc[1:], 16))
        return _SIMPLE_ESCAPES.get(esc, esc)

    text = _ESCAPE.sub(one, literal[1:-1])
    return text.encode("utf-16", "surrogatepass").decode("utf-16")


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
    return _decode(body[start : _literal_end(body, start) + 1])


def _versions(text: str) -> list[tuple[int, ...]]:
    return [
        tuple(int(n) for n in heading.groups())
        for heading in map(_HEADING.match, text.splitlines())
        if heading
    ]


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

    oldest = min(_versions(text))
    if since < oldest:
        dotted = ".".join(str(n) for n in oldest)
        print(
            f"the embedded window opens at {dotted}; releases between "
            f"{'.'.join(str(n) for n in since)} and it are not in the binary -- "
            f"read ~/.claude/cache/changelog.md or {UPSTREAM}",
            file=sys.stderr,
        )

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

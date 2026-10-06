#!/usr/bin/env python3
"""Hold settings.json in the key order Claude Code itself writes.

Claude Code does not append a UI change to the end of the file. It writes the
*validated* settings object -- the parsed settings deep-merged with the update
(`dF`, lodash `mergeWith`, so the base's order survives and new keys land
after it), then `JSON.stringify(k, null, 2) + "\\n"`
(`src/chunk-3z4drmxy.js:3662`, `:3711`, `:3721`) -- and that object came out of
a zod `.object({...}).passthrough()`, whose parser fills a fresh object from
the schema's `allKeys` and only then appends the keys it did not recognize
(`src/chunk-pm8xqwnw.js:1292-1295`, `:1215`). Its keys therefore arrive in the
schema's *declaration* order, not the file's. Every hand-ordered edit is
reverted by the next `/config` toggle, and the reordering lands in a later
commit on top of whatever else it touched.

2.1.284 made the schema lazy: the literal is now a map of thunks, and a parse
builds only the entries the document actually carries. That does not move the
order -- the builder iterates `Object.keys(fields)`, so a per-document schema
is the full declaration order filtered, never resorted
(`src/chunk-q75vj0vh.js:5144`, `:6514`, `:7090`).

The order is re-derived from the decompiled schema rather than pinned, so an
upgrade that reorders the schema cannot leave a stale list behind: this either
reports the new order or fails loudly.

  settings-order.py            check; exit 1 if the order is not cc's
  settings-order.py --write    rewrite settings.json in cc's order
  settings-order.py --print    list the derived order, one key per line

Exit: 0 in order, 1 out of order (or a key that cannot be placed),
2 the check could not run -- no decompiled tree, no schema, no settings file.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SETTINGS = REPO / "settings.json"
DEFAULT_SRC = Path("/repos/claude-code-decompiled/src")

# Pinned by string, not by line: chunk hashes and line numbers rotate every
# build (`update-claude-code` SKILL.md, step 2) while this describe() text has
# survived them. The `() =>` is 2.1.284's lazy schema: every entry is a thunk.
ANCHOR = '    $schema: () => o().optional().describe("JSON Schema reference for Claude Code settings"),'
# The literal is the `return {...}` of the builder function, so it opens on the
# line above the anchor and closes two dedents later. `  };` alone would also
# match a nested literal that happened to land at two spaces; requiring the
# function's own `}` right after it is what makes the generic brace safe.
OPEN = "  return {"
CLOSE = "  };"
AFTER_CLOSE = "}"

# A top-level entry of the schema object literal sits at exactly four spaces.
# Six or more is a nested field, which is why `xaaIdp` -- inside a conditional
# `...(a.CLAUDE_CODE_ENABLE_XAA && {` spread -- is not collected here.
KEY = re.compile(r"^ {4}(\$?[A-Za-z_][A-Za-z0-9_]*): \S")
# `...!1` is a conditional spread whose condition folded to false: it contributes
# no key, so it is not a gap in the derived order. The feature-gate spread
# (2.1.289: `...Yr(qi(e), i => () => i)`) and a live `...(cond && {` are.
SPREAD = re.compile(r"^ {4}\.\.\.(?!!1,?$)")

# A floor, not a pin. Keys are added and removed every release -- 177 in
# 2.1.269, 182 in 2.1.289 -- so tracking the count would fail on every upgrade.
# This only catches an extraction that collapsed, because "read 4 keys" and
# "read the whole schema" otherwise look alike.
FLOOR = 120


def die(msg: str, code: int = 2):
    print(f"settings-order: {msg}", file=sys.stderr)
    raise SystemExit(code)


def derive_order(src: Path) -> tuple[list[str], list[str]]:
    """(key order, names of unresolvable `...spread()` sites) from the schema."""
    if not src.is_dir():
        die(f"decompiled tree not found: {src} -- see update-claude-code step 2")

    hits = [p for p in sorted(src.glob("chunk-*.js")) if ANCHOR in p.read_text(errors="replace")]
    if not hits:
        die(
            f"settings schema not found in {src}: no chunk carries the $schema "
            "anchor. A release reworded it -- re-find the schema by one of its "
            "key names and update ANCHOR."
        )
    if len(hits) > 1:
        die(f"ambiguous anchor, found in {len(hits)} chunks: {[p.name for p in hits]}")

    lines = hits[0].read_text(errors="replace").splitlines()
    start = next(i for i, ln in enumerate(lines) if ln == ANCHOR)
    if start == 0 or lines[start - 1] != OPEN:
        die(
            f"anchor in {hits[0].name} is no longer the first entry of a "
            f"{OPEN!r} literal -- the schema moved out of a builder function, so "
            "neither the bound below nor the declaration order is safe to read."
        )

    order: list[str] = []
    spreads: list[str] = []
    for i, ln in enumerate(lines[start:], start):
        if ln == CLOSE and lines[i + 1 : i + 2] == [AFTER_CLOSE]:
            break
        if m := KEY.match(ln):
            order.append(m.group(1))
        elif SPREAD.match(ln):
            spreads.append(ln.strip())
    else:
        die(
            f"schema in {hits[0].name} is not closed by {CLOSE!r} + {AFTER_CLOSE!r} "
            "-- layout changed"
        )

    if len(order) < FLOOR:
        die(f"extraction collapsed: {len(order)} keys from {hits[0].name}, expected >= {FLOOR}")
    return order, spreads


def main() -> int:
    argv = sys.argv[1:]
    mode = "check"
    src = DEFAULT_SRC
    for arg in argv:
        if arg in ("--write", "--print"):
            mode = arg[2:]
        elif arg.startswith("-"):
            die(f"unknown option {arg}\n{__doc__}")
        else:
            src = Path(arg)

    order, spreads = derive_order(src)
    if mode == "print":
        print("\n".join(order))
        return 0

    if not SETTINGS.is_file():
        die(f"settings file not found: {SETTINGS}")
    raw = SETTINGS.read_text()
    try:
        current = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"{SETTINGS} is not valid JSON: {e}")

    rank = {k: i for i, k in enumerate(order)}
    # A key the schema does not list is one this build does not recognize, or
    # one the feature-gate spread contributes at runtime (2.1.289: the seven
    # keys of the `autoMode`/`deepLink`/`voice`/`briefView`/`screenReader`
    # gates, `skipAutoPermissionPrompt` among them). `.passthrough()` keeps it,
    # but where it lands is not derivable from the text -- so say so rather
    # than guess a position and call the file ordered.
    unplaceable = [k for k in current if k not in rank]
    if unplaceable:
        print(
            f"cannot place {len(unplaceable)} key(s) not in the schema literal: "
            f"{', '.join(unplaceable)}",
            file=sys.stderr,
        )
        if spreads:
            print(
                f"  the schema ends with {' '.join(spreads)} -- its keys are only known at "
                "runtime. Read the position cc wrote out of settings.json itself.",
                file=sys.stderr,
            )
        return 1

    want = sorted(current, key=lambda k: rank[k])
    have = list(current)
    if have == want:
        print(f"settings.json: {len(have)} keys in Claude Code's schema order")
        return 0

    # Writing the same bytes cc writes: two-space indent, non-ASCII unescaped,
    # one trailing newline (`src/chunk-3z4drmxy.js:3721`).
    body = json.dumps({k: current[k] for k in want}, indent=2, ensure_ascii=False) + "\n"
    if mode == "write":
        SETTINGS.write_text(body)
        moved = sum(1 for a, b in zip(have, want) if a != b)
        print(f"settings.json rewritten in schema order ({moved} of {len(want)} keys moved)")
        return 0

    print(f"settings.json is not in Claude Code's schema order ({SETTINGS}):", file=sys.stderr)
    for i, (a, b) in enumerate(zip(have, want)):
        if a != b:
            print(f"  {i:3d}  {a}  ->  {b}", file=sys.stderr)
    print("  fix: .claude/skills/update-claude-code/settings-order.py --write", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

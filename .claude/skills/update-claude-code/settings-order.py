#!/usr/bin/env python3
"""Hold settings.json in the key order Claude Code itself writes.

Claude Code does not append a UI change to the end of the file. It writes the
*validated* settings object -- `O = Zsn(...)` deep-merged with the update, then
`JSON.stringify(U, null, 2) + "\\n"` (`chunk-2x9ed96k.js:3045`, `:3086`,
`:3096`) -- and that object came out of a zod `.object({...}).passthrough()`,
so its keys arrive in the schema's *declaration* order, not the file's. Every
hand-ordered edit is therefore reverted by the next `/config` toggle, and the
reordering lands in a later commit on top of whatever else it touched.

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
# survived them.
ANCHOR = '    $schema: o().optional().describe("JSON Schema reference for Claude Code settings"),'
CLOSE = "  }).passthrough();"

# A top-level entry of the schema object literal sits at exactly four spaces.
# Six or more is a nested field, which is why `xaaIdp` -- inside a conditional
# `...(a.CLAUDE_CODE_ENABLE_XAA && {` spread -- is not collected here.
KEY = re.compile(r"^ {4}(\$?[A-Za-z_][A-Za-z0-9_]*): \S")
# `...!1` is a conditional spread whose condition folded to false: it contributes
# no key, so it is not a gap in the derived order. `...Ks(e)` and a live
# `...(cond && {` are.
SPREAD = re.compile(r"^ {4}\.\.\.(?!!1,?$)")

# A floor, not a pin. Keys are added and removed every release; this only
# catches an extraction that collapsed, because "read 4 keys" and "read the
# whole schema" otherwise look alike.
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

    order: list[str] = []
    spreads: list[str] = []
    for ln in lines[start:]:
        if ln == CLOSE:
            break
        if m := KEY.match(ln):
            order.append(m.group(1))
        elif SPREAD.match(ln):
            spreads.append(ln.strip())
    else:
        die(f"schema in {hits[0].name} is not closed by {CLOSE!r} -- layout changed")

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
    # one the `...Ks(e)` spread contributes at runtime. `.passthrough()` keeps
    # it, but where it lands is not derivable from the text -- so say so rather
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
    # one trailing newline (`chunk-2x9ed96k.js:3096`).
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

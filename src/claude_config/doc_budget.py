"""agent-tools doc-budget: every tracked `.md` against the caps in `doc-budget.toml`.

    agent-tools doc-budget [--print-held] [path ...]

Every tracked `.md` counts against exactly one group unless a `[data]` entry
covers it -- and a README.md or CLAUDE.md counts wherever it is. Groups follow
the mechanism that loads a file, not the directory it sits in; the registry's
header states the grammar and `conventions/documentation.md` the policy: over
cap, cut that group to 80% of cap in the same change.

Counts are local-tokenizer tokens (`agent-tools count-tokens` without
`--api`), loaded once for the whole tree. Exit status: 0 within budget, 1 when
any group is over cap, 2 on a registry error.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tomllib
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = "doc-budget.toml"
INDEX_NAMES = frozenset({"README.md", "CLAUDE.md"})
DERIVED = ("claude-md", "skill-bodies", "agent-bodies", "descriptions")
FILE_CLASSES = ("claude-md", "skill-bodies", "agent-bodies")
APPROVED = re.compile(r"(user:)?[0-9a-f]{8}")
TOP_KEYS = frozenset({"cut_to", "default_cap", "groups", "data", "held"})
GROUP_KEYS = frozenset({"cap", "loaded", "per_file", "one_of", "derived", "residual", "approved", "why"})
DATA_KEYS = frozenset({"paths", "approved", "why"})
HELD_KEYS = frozenset({"approved", "why", "files"})

_EPILOG = """\
exit status:
  0  every group within its cap
  1  a group over cap: cut it to 80% of the cap in the same change
     (conventions/documentation.md, "Documentation budget")
  2  registry error, or a path with nothing counted under it

Counts are local-tokenizer tokens, what `agent-tools count-tokens` reports
without --api; Claude context is about 1.5x on prose.
"""


class RegistryError(Exception):
    """`doc-budget.toml` cannot be applied as written; exit 2."""


def session_of(environ: Mapping[str, str]) -> str:
    """The first 8 hex of the running session's id, or "" when unset.

    An `approved` value equal to it is inert: that session wrote the entry.
    """
    return environ.get("CLAUDE_CODE_SESSION_ID", "")[:8]


def tracked_md(root: Path) -> list[str]:
    """Tracked `.md` files, symlinks skipped, sorted."""
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root,
                         capture_output=True, text=True, check=True).stdout
    return sorted(f for f in out.split("\0")
                  if f.endswith(".md") and not (root / f).is_symlink())


def frontmatter(text: str) -> dict[str, str]:
    """Scalar `key: value` pairs from a leading `---` block; empty if none.

    Single-line values only: the descriptions group counts what this returns, so a
    folded value would count as its first line."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        key, sep, val = line.partition(":")
        if sep and not key.startswith((" ", "\t", "-", "#")):
            out[key.strip()] = val.strip().strip("\"'")
    return {}  # unterminated block: not frontmatter


def derived_class(f: str) -> str | None:
    """The class a file belongs to by its path alone, or None."""
    parts = PurePosixPath(f).parts
    if parts[-1] == "CLAUDE.md":
        return "claude-md"
    if parts[-1] == "SKILL.md" and (
        (len(parts) == 3 and parts[0] == "skills")
        or (len(parts) == 4 and parts[:2] == (".claude", "skills"))
    ):
        return "skill-bodies"
    if len(parts) == 2 and parts[0] == "agents":
        return "agent-bodies"
    return None


def placeholder(name: str) -> re.Pattern[str] | None:
    """Regex for a name carrying `<name>` placeholders, each one path segment;
    None for a literal name."""
    if "<" not in name:
        return None
    parts = re.split(r"<[^>]+>", name)
    return re.compile("([^/]+)".join(map(re.escape, parts)))


def covering(name: str, f: str) -> str | None:
    """The path under which `name` covers file `f`: the name itself for a
    literal, or the prefix its placeholders matched; None if it does not."""
    rx = placeholder(name)
    if rx is None:
        return name if f == name or f.startswith(name + "/") else None
    m = rx.match(f)
    return m.group(0) if m and f.startswith(m.group(0) + "/") else None


def under(path: str, f: str) -> bool:
    """Whether `f` is `path` or lies inside it; "" is the whole tree."""
    return path == "" or f == path or f.startswith(path + "/")


def covers_dir(name: str, other: str) -> bool:
    """Whether group `name` would cover group `other`'s name as a directory.

    A name carrying placeholders is covered only by a prefix of its own text,
    so two patterns of one shape never cover each other."""
    if name == other:
        return False
    if "<" in other:
        return other.startswith(name + "/")
    rx = placeholder(name)
    if rx is not None and rx.fullmatch(other):
        return True
    return covering(name, other) is not None


def load_registry(path: Path) -> dict[str, Any]:
    """The registry, checked for everything a resolver cannot recover from."""
    try:
        reg = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise RegistryError(f"cannot read {path}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise RegistryError(f"not valid TOML: {exc}") from exc
    _keys(reg, TOP_KEYS, "top level")
    for key in ("cut_to", "default_cap", "groups"):
        if key not in reg:
            raise RegistryError(f"missing `{key}`")
    cut_to = reg["cut_to"]
    if isinstance(cut_to, bool) or not isinstance(cut_to, (int, float)) or not 0 < cut_to <= 1:
        raise RegistryError(f"`cut_to` must be a number in (0, 1], not {cut_to!r}")
    if not _positive_int(reg["default_cap"]):
        raise RegistryError(
            f"`default_cap` must be a positive integer, not {reg['default_cap']!r}")
    groups = _table(reg["groups"], "groups")
    for name, g in groups.items():
        g = _table(g, f"group {name!r}")
        _keys(g, GROUP_KEYS, f"group {name!r}")
        if "cap" in g and not _positive_int(g["cap"]):
            raise RegistryError(
                f"group {name!r}: `cap` must be a positive integer, not {g['cap']!r}")
        if "derived" in g and g["derived"] not in DERIVED:
            raise RegistryError(
                f"group {name!r}: `derived` must be one of {', '.join(DERIVED)}")
        if "one_of" in g and (not isinstance(g["one_of"], str) or placeholder(g["one_of"]) is None):
            raise RegistryError(
                f"group {name!r}: one_of {g['one_of']!r} must be a string carrying "
                "a <name> placeholder")
        _approved(g, f"group {name!r}")
    residuals = [n for n, g in groups.items() if g.get("residual")]
    if len(residuals) != 1:
        raise RegistryError(
            f"exactly one group must set `residual`, found {len(residuals)}")
    for name, d in _table(reg.get("data", {}), "data").items():
        d = _table(d, f"data {name!r}")
        _keys(d, DATA_KEYS, f"data {name!r}")
        for key in ("paths", "approved", "why"):
            if key not in d:
                raise RegistryError(f"data {name!r}: missing `{key}`")
        if (not isinstance(d["paths"], list) or not d["paths"]
                or not all(isinstance(p, str) for p in d["paths"])):
            raise RegistryError(
                f"data {name!r}: `paths` must be a non-empty list of strings")
        _approved(d, f"data {name!r}")
    if "held" in reg:
        held = _table(reg["held"], "held")
        _keys(held, HELD_KEYS, "held")
        for key in ("approved", "files"):
            if key not in held:
                raise RegistryError(f"held: missing `{key}`")
        _approved(held, "held")
        for f, size in _table(held["files"], "held.files").items():
            if not _positive_int(size):
                raise RegistryError(f"held {f!r}: size must be a positive integer")
    return reg


def _table(value: object, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RegistryError(f"{where}: must be a table, not {type(value).__name__}")
    return value


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _keys(table: dict[str, Any], allowed: frozenset[str], where: str) -> None:
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise RegistryError(f"{where}: unknown key {', '.join(unknown)}")


def _approved(table: dict[str, Any], where: str) -> None:
    value = table.get("approved")
    if "approved" in table and (not isinstance(value, str) or not APPROVED.fullmatch(value)):
        raise RegistryError(
            f"{where}: `approved` {value!r} is not `<8 hex of session id>` "
            "for an agent's own session or `user:<8 hex>` for the session in which "
            "the user approved it")


class Resolver:
    """Which group each tracked file counts in, under one registry and session."""

    def __init__(self, reg: dict[str, Any], files: list[str], session: str) -> None:
        self.reg = reg
        self.files = files
        self.session = session
        groups = self.reg["groups"]
        self.file_set = set(self.files)
        self.default_cap: int = self.reg["default_cap"]
        self.residual: str = next(n for n, g in groups.items() if g.get("residual"))
        self.derived_groups: dict[str, str] = {
            g["derived"]: n for n, g in groups.items() if g.get("derived")}
        self.paths: list[str] = [
            n for n, g in groups.items()
            if not g.get("derived") and not g.get("residual") and "one_of" not in g]
        self.slots: dict[str, dict[str, str]] = {}
        self.claimed: dict[str, str] = {}
        for n, g in groups.items():
            if "one_of" in g:
                rx = placeholder(g["one_of"])
                assert rx is not None  # load_registry refused the alternative
                hits = {f: "/".join(m.groups()) for f in self.files if (m := rx.fullmatch(f))}
                if not hits:
                    raise RegistryError(
                        f"group {n!r}: one_of {g['one_of']!r} matches no tracked file")
                self.slots[n] = hits
                self.claimed.update({f: n for f in hits})
        held = self.reg.get("held")
        self.held: dict[str, int] = (
            dict(held["files"]) if held and self.live(held["approved"]) else {})
        self.data: list[tuple[str, str]] = [
            (n, p) for n, d in self.reg.get("data", {}).items()
            if self.live(d["approved"]) for p in d["paths"]]
        self._check()

    def live(self, approved: str) -> bool:
        """An approval is live unless the running session wrote it."""
        return approved != self.session

    def _check(self) -> None:
        for n in self.paths:
            if not any(covering(n, f) for f in self.files):
                raise RegistryError(f"group {n!r} covers no tracked file")
        for n in self.reg["groups"]:
            self.cap_of(n)  # a raised cap without `approved` is refused here
        for dn, d in self.reg.get("data", {}).items():
            for p in d["paths"]:
                if not any(covering(p, f) for f in self.files
                           if PurePosixPath(f).name not in INDEX_NAMES):
                    raise RegistryError(f"data {dn!r}: {p!r} covers no tracked file")
        for f, size in self.reg.get("held", {}).get("files", {}).items():
            if f not in self.file_set:
                raise RegistryError(f"held {f!r}: not a tracked .md file")
            if f in self.reg["groups"]:
                raise RegistryError(f"held {f!r}: already a group; hold it in one place")
            cap = self.class_cap(f)
            if size <= cap:
                raise RegistryError(
                    f"held {f!r}: {size:,} is not above its class cap {cap:,}; drop the entry")

    def cap_of(self, n: str) -> int:
        """A registry group's cap: its own, or the cap it would otherwise have
        when its raised cap's approval is inert. Class caps are policy: ungated."""
        g = self.reg["groups"][n]
        cap: int = g.get("cap", self.default_cap)
        if g.get("derived"):
            return cap
        floor = self.otherwise_cap(n)
        if cap > floor:
            if "approved" not in g:
                if "cap" in g:
                    raise RegistryError(
                        f"group {n!r}: cap {cap:,} is above {floor:,} without `approved`")
                raise RegistryError(
                    f"group {n!r}: inherits `default_cap` {cap:,}, above {floor:,}: "
                    "set a `cap` at or below it, or add `approved`")
            if not self.live(g["approved"]):
                return floor
        return cap

    def otherwise_cap(self, n: str) -> int:
        """The cap `n` would have if the registry did not name it: for a file,
        its class's; otherwise the longest other path group covering the name,
        never above `default_cap`."""
        # Finite: `covers_dir` never holds both ways -- a covering name is a strict
        # text prefix of, or a placeholder shape over, the name it covers -- so the
        # chain of parents ends at a name nothing covers.
        if n in self.file_set and (cls := derived_class(n)) in self.derived_groups:
            return min(self.default_cap, self.cap_of(self.derived_groups[cls]))
        hits = [(len(m), placeholder(m) is None, m) for m in self.paths if covers_dir(m, n)]
        if not hits:
            return self.default_cap
        return min(self.default_cap, self.cap_of(max(hits)[2]))

    def named(self, f: str) -> tuple[str, int] | None:
        """The group naming `f` outright: a one_of member, a literal group, a held entry."""
        if f in self.claimed:
            return self.claimed[f], self.cap_of(self.claimed[f])
        if f in self.reg["groups"]:
            return f, self.cap_of(f)
        if f in self.held:
            return f, self.held[f]
        return None

    def data_of(self, f: str) -> str | None:
        """The live data entry covering `f`, or None; an index file is never data."""
        if PurePosixPath(f).name in INDEX_NAMES:
            return None
        return next((n for n, p in self.data if covering(p, f)), None)

    def by_class(self, f: str) -> tuple[str, int]:
        """Where `f` falls with nothing naming it: its derived class, each file
        its own group; else the longest path group -- a literal over a
        placeholder on a tie; else the residual."""
        cls = derived_class(f)
        if cls in self.derived_groups:
            return f, self.cap_of(self.derived_groups[cls])
        hits = [(len(pre), placeholder(n) is None, pre, n)
                for n in self.paths if (pre := covering(n, f))]
        if not hits:
            return self.residual, self.cap_of(self.residual)
        _, _, pre, n = max(hits)
        return (f if self.reg["groups"][n].get("per_file") else pre), self.cap_of(n)

    def class_cap(self, f: str) -> int:
        return self.by_class(f)[1]

    def place(self, f: str) -> tuple[str, str, int]:
        """("group" | "data", name, cap) for a tracked file, first match wins."""
        named = self.named(f)
        if named:
            return "group", *named
        data = self.data_of(f)
        if data:
            return "data", data, 0
        return "group", *self.by_class(f)


@dataclass
class Report:
    counted: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
    caps: dict[str, int] = field(default_factory=dict)
    detail: defaultdict[str, list[tuple[int, str, str]]] = field(default_factory=lambda: defaultdict(list))
    data: defaultdict[str, list[tuple[int, str]]] = field(default_factory=lambda: defaultdict(list))
    droppable: list[tuple[str, int, int]] = field(default_factory=list)


def measure(root: Path, res: Resolver, count: Callable[[str], int]) -> Report:
    """Every tracked file counted into its group, one_of sets paying their
    largest member, descriptions counted as a field on top."""
    rep = Report()
    groups = res.reg["groups"]
    for name, g in groups.items():
        if not (g.get("per_file") or placeholder(name) or g.get("derived")):
            rep.caps[name] = res.cap_of(name)
    slot_size: dict[str, dict[str, int]] = defaultdict(dict)
    desc = res.derived_groups.get("descriptions")
    for f in res.files:
        text = (root / f).read_text(encoding="utf-8", errors="replace")
        tokens = count(text)
        kind, name, cap = res.place(f)
        if kind == "data":
            rep.data[name].append((tokens, f))
        elif name in res.slots:
            slot_size[name][f] = tokens
        else:
            rep.caps[name] = cap
            rep.counted[name] += tokens
            rep.detail[name].append((tokens, f, ""))
        if f in res.held:
            class_cap = res.class_cap(f)
            if tokens <= class_cap:
                rep.droppable.append((f, tokens, class_cap))
        if desc and derived_class(f) in ("skill-bodies", "agent-bodies"):
            dn = count(frontmatter(text).get("description", ""))
            rep.counted[desc] += dn
            rep.detail[desc].append((dn, f, ""))
    if desc:
        rep.caps[desc] = res.cap_of(desc)
    for g, sizes in slot_size.items():
        top = max(sizes.values())
        rep.counted[g] += top
        members = ", ".join(f"{res.slots[g][f]} {tokens:,}"
                            for f, tokens in sorted(sizes.items(), key=lambda t: -t[1]))
        rep.detail[g].append((top, groups[g]["one_of"], f"largest of {members}"))
    return rep


def display_order(res: Resolver, rep: Report) -> list[tuple[str, str]]:
    """(group, label) rows in registry order. A derived, per_file or placeholder
    group stands for its members, listed at its position under its `loaded`
    label; a literal or held file shows under the class it belongs to."""
    groups = res.reg["groups"]
    parents = {n for n, g in groups.items()
               if g.get("derived") in FILE_CLASSES or g.get("per_file") or placeholder(n)}

    def parent_of(name: str) -> str | None:
        if name in res.file_set and (cls := derived_class(name)) in res.derived_groups:
            return res.derived_groups[cls]
        hits = [(len(m), m) for m in parents
                if not groups[m].get("derived") and covers_dir(m, name)]
        return max(hits)[1] if hits else None

    children: dict[str | None, list[str]] = defaultdict(list)
    for name in set(rep.caps) | parents:
        children[parent_of(name)].append(name)

    rows: list[tuple[str, str]] = []
    seen: set[str] = set()

    def emit(name: str, label: str) -> None:
        if name in seen:
            return
        seen.add(name)
        if name in rep.caps:
            rows.append((name, label))
        for child in sorted(children.get(name, [])):
            emit(child, label)

    for name in groups:
        if name not in seen and parent_of(name) is None:
            emit(name, groups[name].get("loaded", "(no `loaded` label)"))
    # Every row's parent chain ends at a registry group, so nothing lands here; a row
    # silently missing from the report would be worse than a stray label.
    for name in sorted(set(rep.caps) - seen):
        emit(name, "(unplaced)")
    return rows


def render(res: Resolver, rep: Report, rows: list[tuple[str, str]], detail_all: bool,
           print_held: bool, show_data: bool = True) -> tuple[str, list[str]]:
    """The report text and the names of the groups over cap."""
    cut_to: float = res.reg["cut_to"]
    pct = f"{cut_to:.0%}"
    over: list[tuple[str, int, int, int]] = []
    lines: list[str] = []
    if print_held:
        for name, _ in rows:
            c, cap = rep.counted[name], rep.caps[name]
            if c > cap:
                over.append((name, c, cap, int(cap * cut_to)))
        for name, c, _, _ in sorted(over, key=lambda t: -t[1]):
            if name in res.file_set:
                lines.append(f'"{name}" = {c}')
            else:
                lines.append(f"# not a file, give it a group cap with `approved`: {name} {c:,}")
        return "".join(line + "\n" for line in lines), [t[0] for t in over]

    width = max((len(name) for name, _ in rows), default=5)
    lines.append(f"{'counted':>9} {'cap':>7} {pct:>7}  group")
    label_shown: str | None = None
    for name, label in rows:
        if label != label_shown:
            lines.append(f"-- {label}")
            label_shown = label
        c, cap = rep.counted[name], rep.caps[name]
        target = int(cap * cut_to)
        if c > cap:
            state = f"OVER by {c - cap:,}"
            over.append((name, c, cap, target))
        elif c > target:
            state = f"above {pct} by {c - target:,}"
        else:
            state = "ok"
        if name in res.held:
            # A held cap is a size frozen at the registry's introduction, not a
            # sanctioned one; the row is read far from the registry that says so.
            state += " (held)"
        lines.append(f"{c:9,d} {cap:7,d} {target:7,d}  {name:<{width}} {state}")
        for tokens, f, note in sorted(rep.detail[name], reverse=True):
            # A note says how the count was arrived at -- a one_of set paying its
            # largest member -- so it shows whether or not the group is over cap.
            if f != name and (note or c > cap or detail_all):
                lines.append(f"{tokens:9,d}{'':20}{f}" + (f"  ({note})" if note else ""))

    if show_data and rep.data:
        lines.append("")
        lines.append("data, listed and not counted:")
        for dn, d in res.reg["data"].items():
            members = rep.data.get(dn, [])
            total = sum(tokens for tokens, _ in members)
            lines.append(f"{len(members):5d} files {total:10,d}  {dn}: {', '.join(d['paths'])}")

    if rep.droppable:
        lines.append("")
        lines.append("held entries now within their class cap -- drop them from [held.files]:")
        for f, tokens, cap in sorted(rep.droppable):
            lines.append(f"  {f} {tokens:,} <= {cap:,}")

    for name, c, cap, target in over:
        lines.append(f"\n{name} is {c:,} against {cap:,}. Cut to {target:,} -- see "
                     "conventions/documentation.md, *Documentation budget*.")
    return "".join(line + "\n" for line in lines), [t[0] for t in over]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="doc-budget",
        description=(
            "Every tracked .md against the caps in doc-budget.toml. Groups follow "
            "how a file reaches a context; the registry's header states the grammar."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--print-held", action="store_true",
                   help="Instead of the report, emit a [held.files] line for every "
                        "over-cap file, at its size. Exits 1 like the report whenever "
                        "a group is over cap.")
    p.add_argument("paths", nargs="*", metavar="path",
                   help="Narrow the report to the groups under these paths and the "
                        "groups counting the files under them, with per-file detail "
                        "and no data table; `.` names every group.")
    return p


def main(argv: list[str] | None = None, *, root: Path = ROOT,
         count: Callable[[str], int] | None = None,
         environ: Mapping[str, str] | None = None) -> int:
    """Exit 0 within budget, 1 with a group over cap, 2 on a registry error; a path
    that names no group and holds no counted file is a usage error, SystemExit(2)
    from argparse."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    environ = os.environ if environ is None else environ
    session = session_of(environ)
    if not session:
        print("warning: CLAUDE_CODE_SESSION_ID unset, so the same-session gate is "
              "inactive and every approval counts as live", file=sys.stderr)

    want: list[str] = []
    for a in args.paths:
        try:
            rel = Path(a).resolve().relative_to(root.resolve())
        except ValueError:
            parser.error(f"{a} is outside {root}")
        want.append("" if str(rel) == "." else rel.as_posix())

    try:
        reg = load_registry(root / REGISTRY)
        res = Resolver(reg, tracked_md(root), session)
    except RegistryError as exc:
        print(f"{REGISTRY}: {exc}", file=sys.stderr)
        return 2

    if count is None:
        from claude_config.count_tokens import count_with, load_tokenizer

        count = partial(count_with, load_tokenizer())

    rep = measure(root, res, count)
    rows = display_order(res, rep)
    # A path the registry does not name is still countable text: show the group
    # paying for it, which is what an agent measuring its own edit is asking.
    shown = [(n, label) for n, label in rows
             if not want or any(under(w, n) or any(under(w, f) for _, f, _ in rep.detail[n])
                                for w in want)]
    if want and not shown:
        parser.error(f"nothing counted lies under {', '.join(want)}: group names are in "
                     f"{REGISTRY}; derived, one_of and residual groups are not paths; and a "
                     "[data] path is listed, not counted")
    text, over = render(res, rep, shown, detail_all=bool(want), print_held=args.print_held,
                        show_data=not want)
    sys.stdout.write(text)
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())

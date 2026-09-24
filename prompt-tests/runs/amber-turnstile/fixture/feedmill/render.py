"""Report rendering: a preset's `label` is the report's title line."""

from __future__ import annotations


def render_title(label: str, *, count: int) -> str:
    # Verified 2026-09-18 against CPython 3.12: `label` goes through str.format,
    # so a literal `{` or `}` in a preset label is read as a placeholder. A named
    # field raises KeyError, a positional field past the argument count raises
    # IndexError, and an unmatched brace raises ValueError. Nothing catches these:
    # the traceback names str.format, not the preset, so the failure reads as a
    # renderer bug. presets/strict.toml's label carries `{scope}` and is the only
    # shipped preset that does it.
    return label.format(count) + f" ({count} records)"


def render(rows: list[dict], label: str) -> str:
    lines = [render_title(label, count=len(rows))]
    for row in rows:
        lines.append(f"  {row.get('id', '?')}\t{row.get('status', '?')}")
    return "\n".join(lines)

#!/usr/bin/env python3
"""Render a captured API request into files whose `git diff` is readable.

`request.json` is the artifact of record and is one line per string, so a
reworded paragraph inside a tool description is one changed line thousands of
characters wide. This writes the same content as text:

    <capture>/prompt.md          everything in the request except the tools
    <capture>/tools/<Name>.md    one file per tool definition

Why the split falls there is in README.md, "Reading a capture as a diff". Both
files are derived; render rather than hand-edit.

Usage:
    ./render_capture.py <request.json> [<out-dir>]   # default: the file's dir
    ./render_capture.py --tree <root>                # every capture beneath it
"""

import json
import re
import subprocess
import sys
from pathlib import Path

PROMPT_FILE = "prompt.md"
TOOLS_DIR = "tools"

# A tool name becomes a filename, so it may not reach outside the tools
# directory. MCP tools arrive as `mcp__server__tool`, plugin tools can carry
# dots and dashes; anything else is a shape this renderer has not seen and
# stops for rather than writing somewhere unexpected.
_SAFE_TOOL_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")

# Rendered as data rather than prose, so a key added by a future release shows
# up without this file being edited.
_NON_PROMPT_KEYS = ("tools", "system", "messages")


def _fence(obj) -> str:
    # ensure_ascii=False so the em-dashes and emoji in tool schemas render as
    # themselves, matching the description text they sit beside.
    return "```json\n" + json.dumps(obj, indent=2, ensure_ascii=False) + "\n```"


def _annotations(block: dict) -> str:
    """Everything about a content block except its type and its text."""
    extra = {k: v for k, v in block.items() if k not in ("type", "text")}
    return f" — {json.dumps(extra, ensure_ascii=False)}" if extra else ""


def _render_block(heading: str, block: dict, out: list[str]) -> None:
    out.append(f"## {heading}{_annotations(block)}\n")
    if block.get("type") == "text":
        out.append(block.get("text", ""))
    else:
        # Not dropped: a capture that grows an image or tool_result block should
        # say so in the diff rather than going quiet.
        out.append(_fence(block))
    out.append("")


def render_prompt(req: dict) -> str:
    out: list[str] = [
        "# Captured request, everything except the tool definitions",
        "",
        "Rendered from `request.json` by `render_capture.py`. Tool definitions are "
        "one file each under `tools/`.",
        "",
        "## parameters",
        "",
        _fence({k: v for k, v in req.items() if k not in _NON_PROMPT_KEYS}),
        "",
        "## tools",
        "",
        "Names in request order; the definitions are under `tools/`.",
        "",
    ]
    out += [f"- `{t['name']}`" for t in req.get("tools", [])]
    out.append("")

    for i, block in enumerate(req.get("system", [])):
        _render_block(f"system[{i}]", block, out)

    for i, msg in enumerate(req.get("messages", [])):
        content = msg.get("content", [])
        # A message carries either a bare string or a list of typed blocks.
        blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content
        for j, block in enumerate(blocks):
            _render_block(f"messages[{i}] {msg.get('role')}, content[{j}]", block, out)

    return "\n".join(out).rstrip("\n") + "\n"


def render_tool(tool: dict) -> str:
    attrs = {k: v for k, v in tool.items() if k not in ("name", "description", "input_schema")}
    out = [f"# {tool['name']}", ""]
    if attrs:
        out += ["## attributes", "", _fence(attrs), ""]
    out += ["## description", "", tool.get("description", ""), ""]
    out += ["## input_schema", "", _fence(tool.get("input_schema", {}))]
    return "\n".join(out).rstrip("\n") + "\n"


def write_capture(req: dict, out_dir: Path) -> list[str]:
    """Write `prompt.md` and `tools/` into out_dir. Returns the tool names."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / PROMPT_FILE).write_text(render_prompt(req))

    names = []
    for tool in req.get("tools", []):
        name = tool["name"]
        if not _SAFE_TOOL_NAME.match(name):
            raise ValueError(f"tool name is not usable as a filename: {name!r}")
        names.append(name)

    tools_dir = out_dir / TOOLS_DIR
    tools_dir.mkdir(exist_ok=True)
    for tool, name in zip(req.get("tools", []), names):
        (tools_dir / f"{name}.md").write_text(render_tool(tool))
    # A tool the release dropped has to leave the tree, or the diff shows it as
    # still present. Only rendered `.md` files are removed, so a mistyped
    # out_dir cannot take anything else with it.
    keep = {f"{n}.md" for n in names}
    for stale in tools_dir.glob("*.md"):
        if stale.name not in keep:
            stale.unlink()
    return names


def render_file(request_path: Path, out_dir: Path | None = None) -> list[str]:
    return write_capture(
        json.loads(request_path.read_text()), out_dir or request_path.parent
    )


def find_captures(root: Path) -> list[Path]:
    """Every capture beneath `root` that git does not ignore.

    `regenerate.py` stages a run in the gitignored `capture-output/`, which holds
    a `request.json` of its own: a bare rglob returns it, `--tree` renders into
    it, and `tests/test_snapshot_rendering.py` then verifies that render against
    itself. git decides what is working state, so git is asked, and a
    `check-ignore` that cannot answer raises rather than returning the
    unfiltered list.
    """
    # Resolved first: git reads a relative path against the subprocess cwd, so
    # an unresolved `--tree docs/...` would match nothing and report every
    # scratch capture as tracked.
    root = root.resolve()
    found = sorted(root.rglob("request.json"))
    if not found:
        return []
    # NUL-separated both ways, so a newline in a directory name cannot split a path.
    probe = subprocess.run(
        ["git", "check-ignore", "-z", "--stdin"],
        input="".join(f"{p}\0" for p in found),
        capture_output=True,
        text=True,
        cwd=root,
    )
    # 0 = some path is ignored, 1 = none is; anything else is a real failure.
    if probe.returncode not in (0, 1):
        raise RuntimeError(
            f"git check-ignore failed under {root} "
            f"(exit {probe.returncode}): {probe.stderr.strip()}"
        )
    ignored = {Path(entry) for entry in probe.stdout.split("\0") if entry}
    return [path for path in found if path not in ignored]


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2

    if argv[0] == "--tree":
        if len(argv) != 2:
            print("--tree takes exactly one root directory", file=sys.stderr)
            return 2
        root = Path(argv[1])
        found = find_captures(root)
        if not found:
            print(f"no request.json beneath {root}", file=sys.stderr)
            return 1
        for path in found:
            names = render_file(path)
            print(f"{path.parent}: {len(names)} tool(s)")
        return 0

    request_path = Path(argv[0])
    out_dir = Path(argv[1]) if len(argv) > 1 else request_path.parent
    names = render_file(request_path, out_dir)
    print(f"{out_dir}: {len(names)} tool(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

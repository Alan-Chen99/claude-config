"""Coverage check: does a render show everything its source carries?

Renders each log at an effectively unbounded ``--tool-max`` and reports content
the render dropped. Three finding kinds, one per class of defect this repo has
shipped:

``load_error``
    The file did not parse or load, so none of its content rendered.

``renderer_truncation``
    A ``[N more chars]`` marker the renderer emitted at unbounded
    ``--tool-max`` — i.e. a hardcoded character limit that ignores the flag.
    Markers already present in the source are subtracted: session logs in this
    repo capture cc-pretty's own output as tool results, and those carry real
    markers that the renderer only echoed.

``missing_content``
    A content string present in the source and absent from the render.

Scope, so a clean run is not read as more than it is. Needles are drawn from
conversation content only: request messages and the response for an intercept
capture, and assistant/user message content blocks for a JSONL session. An
intercept capture's system block and a JSONL session's attachment, progress and
system records are not needle sources — several of those render as deliberate
one-line summaries (``⊞ skill listing: 12 skill(s)``) where showing the payload
was never the intent. They are still rendered, so ``renderer_truncation``
covers them: it reads the whole render regardless of needle source.

Needle extraction mirrors ``fmt_tool_input``: a string value is expected raw, a
non-string value in its ``json.dumps`` form. That couples the check to the
renderer's formatting, which is the point — a format change that stops showing
a value fails here rather than passing quietly.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass, field
from typing import Any

# An unbounded --tool-max. Large enough that no real log reaches it, small
# enough to stay an int the CLI accepts.
UNBOUNDED = 10**9

_MARKER = re.compile(r" \.\.\. \[\d+ more chars\] \.\.\. ")
_DECORATION = re.compile(r"^[\s│]+")


@dataclass
class Finding:
    kind: str
    path: str
    detail: str

    def __str__(self) -> str:
        return f"{self.kind}: {self.path}: {self.detail}"


@dataclass
class Report:
    files: int = 0
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings


def normalize(text: str) -> str:
    """Strip indentation and box decoration so containment survives rendering.

    The renderer indents every body and prefixes thinking lines with ``│``.
    Both sides of the containment test go through this, so a needle matches
    wherever its text was placed.
    """
    lines = []
    for line in text.splitlines():
        stripped = _DECORATION.sub("", line).rstrip()
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def _values_of(payload: dict[str, Any]) -> list[str]:
    """Needles for a dict rendered through ``fmt_tool_input``."""
    out = []
    for val in payload.values():
        if isinstance(val, str):
            out.append(val)
        elif val is not None and not isinstance(val, bool):
            out.append(json.dumps(val))
    return out


def _block_needles(block: Any, path: str) -> list[tuple[str, str]]:
    """Content strings a single content block must put on screen."""
    if not isinstance(block, dict):
        return [(path, str(block))]
    btype = block.get("type", "")
    if btype == "text":
        return [(f"{path}.text", block.get("text", ""))]
    if btype == "thinking":
        return [(f"{path}.thinking", block.get("thinking", ""))]
    if btype == "tool_use":
        inp = block.get("input")
        if isinstance(inp, dict):
            return [(f"{path}.input", v) for v in _values_of(inp)]
        return [(f"{path}.input", str(inp))]
    if btype == "tool_result":
        content = block.get("content", "")
        if isinstance(content, str):
            return [(f"{path}.content", content)]
        needles = []
        for i, sub in enumerate(content):
            if isinstance(sub, dict) and sub.get("type") == "text":
                needles.append((f"{path}.content[{i}].text", sub.get("text", "")))
            else:
                # The renderer prints non-text items via str(); match that.
                needles.append((f"{path}.content[{i}]", str(sub)))
        return needles
    # Unmodelled block type — _render_unknown_block dumps the whole payload.
    rest = {k: v for k, v in block.items() if k != "type"}
    return [(f"{path}.{btype}", v) for v in _values_of(rest)]


def _message_needles(msg: dict, path: str) -> list[tuple[str, str]]:
    content = msg.get("content", "")
    if isinstance(content, str):
        return [(f"{path}.content", content)]
    needles = []
    for i, block in enumerate(content):
        needles.extend(_block_needles(block, f"{path}.content[{i}]"))
    return needles


def intercept_needles(raw: dict) -> list[tuple[str, str]]:
    """Conversation content an intercept capture must show."""
    needles: list[tuple[str, str]] = []
    for i, msg in enumerate(raw.get("request", {}).get("messages", []) or []):
        needles.extend(_message_needles(msg, f".request.messages[{i}]"))
    resp = raw.get("response") or {}
    for i, block in enumerate(resp.get("content", []) or []):
        needles.extend(_block_needles(block, f".response.content[{i}]"))
    return [(p, t) for p, t in needles if t and t.strip()]


def jsonl_needles(records: list[tuple[dict, int]]) -> list[tuple[str, str]]:
    """Conversation content a JSONL session must show (see module scope note).

    Takes ``read_jsonl``'s (record, line number) pairs so needle paths carry the
    real line, not an enumeration index — blank lines and unparseable lines are
    already dropped by then.
    """
    needles: list[tuple[str, str]] = []
    for rec, lineno in records:
        if rec.get("type") not in ("assistant", "user"):
            continue
        msg = rec.get("message")
        if isinstance(msg, dict):
            needles.extend(_message_needles(msg, f"L{lineno}.message"))
    return [(p, t) for p, t in needles if t and t.strip()]


def _findings_for(
    path: str, source_text: str, rendered: str, needles: list[tuple[str, str]]
) -> list[Finding]:
    findings: list[Finding] = []

    emitted = len(_MARKER.findall(rendered)) - len(_MARKER.findall(source_text))
    if emitted > 0:
        findings.append(
            Finding(
                "renderer_truncation",
                path,
                f"{emitted} truncation marker(s) emitted at --tool-max {UNBOUNDED}; "
                "a hardcoded limit is ignoring the flag",
            )
        )

    hay = normalize(rendered)
    # Blocks render in source order, so each search starts where the previous
    # match ended. Without the cursor every needle rescans the whole render and
    # a long session costs O(needles x render); with it the sweep is linear.
    # A miss retries from zero before being reported, since order is a
    # regularity of the renderer and not a guarantee it makes.
    cursor = 0
    for needle_path, text in needles:
        needle = normalize(text)
        at = hay.find(needle, cursor)
        if at == -1:
            at = hay.find(needle)
        if at == -1:
            findings.append(
                Finding(
                    "missing_content",
                    path,
                    f"{needle_path} ({len(text)} chars) is not in the render: "
                    f"{text[:60]!r}",
                )
            )
        else:
            cursor = at + len(needle)
    return findings


def check_intercept(path: str) -> list[Finding]:
    from claude_config.cc_pretty.render import C, Renderer
    from claude_config.cc_pretty_intercept import main as im
    from claude_config.cc_pretty_intercept.parse import load_intercept

    C.disable()
    source_text = open(path, encoding="utf-8", errors="replace").read()
    try:
        log = load_intercept(path)
    except Exception as exc:  # noqa: BLE001 — every load failure is a finding
        return [Finding("load_error", path, f"{type(exc).__name__}: {exc}")]

    renderer = Renderer(
        path, tool_output_max=UNBOUNDED, tool_input_max=UNBOUNDED, show_thinking=True
    )
    # The system block is rendered but contributes no needles: it is not
    # conversation content. Rendering it anyway puts _render_system under the
    # truncation check, which reads the whole render.
    parts = []
    system = log.request.system
    if system if isinstance(system, str) else len(system) > 0:
        parts.append(im._render_system(system, UNBOUNDED))
    for idx, msg in enumerate(log.request.messages):
        parts.append(im._render_message(msg, idx, len(log.request.messages), renderer))
    if log.response is not None:
        parts.append(im._render_response(log.response, renderer))
    rendered = "\n".join(parts)

    return _findings_for(path, source_text, rendered, intercept_needles(json.loads(source_text)))


def check_jsonl(path: str) -> list[Finding]:
    from claude_config.cc_pretty import main as cm
    from claude_config.cc_pretty.render import C

    C.disable()
    source_text = open(path, encoding="utf-8", errors="replace").read()
    try:
        raw_records = cm.read_jsonl(path)
        records, _ = cm.parse_all(raw_records)
    except Exception as exc:  # noqa: BLE001 — every load failure is a finding
        return [Finding("load_error", path, f"{type(exc).__name__}: {exc}")]

    parser = argparse.ArgumentParser()
    cm.add_shared_args(parser, default_tool_max=UNBOUNDED)
    args = parser.parse_args([])
    # Everything visible: the hiding flags are deliberate view choices, not
    # drops, and leaving them on would make the check vacuous.
    args.tool_max = UNBOUNDED
    args.show_all = True
    args.compact_all = True
    args.show_rewound = True
    args.no_color = True

    buf, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(err):
            cm.run_pipeline(
                cm.PipelineInput(records=records, log_path=path, args=args)
            )
    except SystemExit as exc:
        return [Finding("load_error", path, f"render exited with {exc.code}")]

    return _findings_for(path, source_text, buf.getvalue(), jsonl_needles(raw_records))


def check_path(path: str) -> list[Finding]:
    return check_jsonl(path) if path.endswith(".jsonl") else check_intercept(path)


def run(paths: list[str]) -> Report:
    report = Report()
    for path in paths:
        report.files += 1
        report.findings.extend(check_path(path))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cc-render-coverage",
        description="Report content cc-pretty / cc-pretty-intercept fails to show "
        "at unbounded --tool-max.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Log files: .jsonl for cc-pretty, anything else for an intercept "
        "capture. Reads paths from stdin when none are given.",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Print the summary line only"
    )
    parser.add_argument(
        "--max-findings",
        type=int,
        default=40,
        metavar="N",
        help="Stop listing after N findings (default: 40); the count stays exact",
    )
    args = parser.parse_args()

    paths = args.paths or [line.strip() for line in sys.stdin if line.strip()]
    if not paths:
        parser.error("no paths given on the command line or stdin")

    report = run(paths)
    if not args.quiet:
        for finding in report.findings[: args.max_findings]:
            print(finding)
        hidden = len(report.findings) - args.max_findings
        if hidden > 0:
            print(f"... {hidden} more finding(s) not listed")

    kinds: dict[str, int] = {}
    for finding in report.findings:
        kinds[finding.kind] = kinds.get(finding.kind, 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(kinds.items())) or "clean"
    print(f"{report.files} file(s) checked: {summary}", file=sys.stderr)
    sys.exit(1 if report.findings else 0)


if __name__ == "__main__":
    main()

"""Pretty-print an opencode exported session to stdout.

Mirrors cc-pretty's CLI surface (--tool-max, --truncate-input, --no-color,
--no-thinking, --show-rewound, --show-all, --chat-only, --compact-all,
--compact-leg, --agent, --validate-only) and reuses cc-pretty's rendering
pipeline. The data-source conversion lives in
``claude_config.opencode_pretty.convert`` — see that module for how
opencode's part-based messages get flattened into Claude-Code-style
records (and how revert state surfaces as rewound indices).

Usage: opencode-pretty <session_id> [<flag>...]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from typing import Any

from claude_config.cc_pretty.main import (
    PipelineInput,
    add_shared_args,
    run_pipeline,
)
from claude_config.opencode_pretty.convert import export_to_records


def parse_export_stdout(stdout: str) -> dict[str, Any]:
    """Parse opencode-export stdout, skipping any pre-JSON banner text."""
    start = stdout.find("{")
    if start == -1:
        raise ValueError("no JSON object found in opencode export output")
    try:
        value = json.loads(stdout[start:])
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in opencode export output: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("opencode export output was not a JSON object")
    return value


def fetch_export(session_id: str) -> dict[str, Any]:
    """Run ``opencode export <session_id>`` and return the parsed JSON.

    Goes through a temp file rather than capturing stdout in memory because
    opencode exports can be tens of megabytes and the subprocess module's
    in-memory capture path has bitten this codebase before.
    """
    with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as stdout_file:
        proc = subprocess.run(
            ["opencode", "export", session_id],
            text=True,
            stdout=stdout_file,
            stderr=subprocess.PIPE,
            check=False,
        )
        stdout_file.seek(0)
        stdout = stdout_file.read()
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    try:
        return parse_export_stdout(stdout)
    except ValueError as exc:
        print(f"Failed to parse opencode export JSON: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Pretty-print an opencode exported session",
    )
    parser.add_argument("session_id", help="opencode session id (ses_...)")
    parser.add_argument(
        "--from-file",
        metavar="PATH",
        default=None,
        help="Read a saved `opencode export` JSON from PATH instead of "
        "running `opencode export <session_id>`. Useful for tests and for "
        "re-rendering an export without re-fetching.",
    )
    # Default tool-max is bigger than cc-pretty's 200 because opencode tool
    # outputs are typically large file reads / search results and 200 is
    # uselessly small. Keep --truncate-input semantics identical.
    add_shared_args(parser, default_tool_max=4000)
    args = parser.parse_args(argv)

    if args.from_file:
        with open(args.from_file) as fh:
            export = json.load(fh)
    else:
        export = fetch_export(args.session_id)

    records, meta = export_to_records(export)

    if args.validate_only:
        # We construct records via pydantic, so a failure would already have
        # raised during conversion. Report record count for parity with
        # cc-pretty's --validate-only.
        print(f"{len(records)}/{len(records)} records parsed OK, 0 errors", file=sys.stderr)
        sys.exit(0)

    session_id = meta.get("session_id") or args.session_id
    log_path = f"opencode://{session_id}"

    # Always pass an explicit rewound set — even an empty one — so
    # cc-pretty's parent-fork detector is bypassed. opencode legitimately
    # has many assistant messages sharing one user as parent (the multi-step
    # chain), which the detector would otherwise flag as a fork rewind.
    run_pipeline(PipelineInput(
        records=records,
        log_path=log_path,
        args=args,
        agent_chunk_prefix=f"opencode-pretty-{session_id[:12]}",
        rewound=meta.get("rewound_indices") or set(),
    ))


if __name__ == "__main__":
    main()

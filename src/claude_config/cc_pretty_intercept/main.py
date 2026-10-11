"""Pretty-print one MITM intercept log file.

One intercept file = one captured API request/response pair, written by
scripts/intercept/proxy.py to ~/.claude/requests-log/<session_id>/NNNN.json.

Shares cc-pretty's CLI surface and rendering pipeline: the capture is flattened
into cc-pretty records by ``claude_config.cc_pretty_intercept.convert`` — see
that module for how the API's named regions become records and keep their jq
addresses. ``--no-system``, ``--no-tools`` and ``--show-http`` are the options
this front-end adds, for the three regions only an API capture has.

Color output is auto-detected: on when stdout is a TTY, off when piped or when
NO_COLOR is set (https://no-color.org). --color forces it on (e.g. piping to
`less -R`), --no-color forces it off.

Usage: cc-pretty-intercept <file.json> [<flag>...]
"""

from __future__ import annotations

import argparse
import os
import sys

from claude_config.cc_pretty.main import (
    PipelineInput,
    add_shared_args,
    run_pipeline,
)
from claude_config.cc_pretty_intercept.convert import header_lines, log_to_records
from claude_config.cc_pretty_intercept.parse import load_intercept


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Pretty-print one MITM intercept log file",
    )
    parser.add_argument("file", help="Path to intercept .json file")
    # A capture's bodies are whole tool outputs and system prompts, so the 200
    # cc-pretty reads a session at is uselessly small here.
    add_shared_args(parser, default_tool_max=2000)
    region = parser.add_argument_group("SELECTION (capture regions)")
    region.add_argument(
        "--no-system", action="store_true", help="Hide the system prompt parts",
    )
    region.add_argument(
        "--no-tools", action="store_true", help="Hide the tool definitions list",
    )
    region.add_argument(
        "--show-http",
        action="store_true",
        help="Dump every request and response header from the http region",
    )
    args = parser.parse_args(argv)

    log = load_intercept(args.file)
    records, jq_paths = log_to_records(
        log, show_system=not args.no_system, show_tools=not args.no_tools,
    )

    if args.validate_only:
        # load_intercept and the conversion both build through pydantic, so a
        # bad capture has already raised by here.
        print(
            f"{len(records)}/{len(records)} records parsed OK, 0 errors",
            file=sys.stderr,
        )
        sys.exit(0)

    # Absolute, so the recovery recipes under truncated blocks run from anywhere.
    log_path = f"intercept://{os.path.abspath(args.file)}"
    stem = os.path.basename(args.file).removesuffix(".json")
    session = log.session.session_id[:8] if log.session else ""

    run_pipeline(PipelineInput(
        records=records,
        log_path=log_path,
        args=args,
        header=header_lines(log, args.file, show_http=args.show_http),
        jq_paths=jq_paths,
        agent_chunk_prefix="-".join(
            x for x in ("cc-pretty-intercept", session, stem) if x
        ),
        # A capture is one request: nothing in it was ever rewound, and the
        # parent-fork detector has no uuids to read here anyway.
        rewound=set(),
    ))


if __name__ == "__main__":
    main()

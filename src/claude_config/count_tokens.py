"""agent-tools count-tokens: report Anthropic count_tokens for stdin/file/arg text.

Invoked via `agent-tools count-tokens [--model MODEL] [--file PATH] [TEXT]`.
Reads ANTHROPIC_TOKEN_COUNT_API_KEY from /repos/claude-config/.env (loaded by
claude_config.config.load()) and prints a single integer to stdout.
"""

from __future__ import annotations

import argparse
import sys

from claude_config.config import load as _load_env

_load_env()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="count-tokens",
        description="Count input tokens for Claude models via the Anthropic count_tokens API.",
    )
    p.add_argument(
        "--model",
        default="claude-opus-4-7",
        help="Model ID (default: claude-opus-4-7).",
    )
    p.add_argument(
        "--file",
        dest="file",
        default=None,
        help="Read text from PATH as UTF-8.",
    )
    p.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Text to count. If omitted and --file is omitted, read stdin.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    parser.parse_args(argv)
    # Subsequent tasks add input resolution, mutex check, and API call here.
    return 0


if __name__ == "__main__":
    sys.exit(main())

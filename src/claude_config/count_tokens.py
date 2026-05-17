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
    args = parser.parse_args(argv)

    text = _resolve_input(parser, args)

    import os
    import anthropic

    api_key = os.environ["ANTHROPIC_TOKEN_COUNT_API_KEY"]
    client = anthropic.Anthropic(api_key=api_key)
    result = client.messages.count_tokens(
        model=args.model,
        messages=[{"role": "user", "content": text}],
    )
    print(result.input_tokens)
    return 0


def _resolve_input(parser: argparse.ArgumentParser, args: argparse.Namespace) -> str:
    if args.text is not None and args.file is not None:
        parser.error("--file and TEXT are mutually exclusive")
    if args.text is not None:
        return args.text
    if args.file is not None:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read()
    if sys.stdin.isatty():
        parser.error("no input provided (pass TEXT, --file PATH, or pipe via stdin)")
    return sys.stdin.read()


if __name__ == "__main__":
    sys.exit(main())

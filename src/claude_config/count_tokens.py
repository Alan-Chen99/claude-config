"""agent-tools count-tokens: report a token count for stdin/file/arg text.

Invoked via `agent-tools count-tokens [--api] [--model MODEL] [--file PATH] [TEXT]`.

Two backends, and they do not measure the same thing:

  local (default)  Tokens of the text itself, via the Qwen3.8 tokenizer vendored
                   in `tokenizer_data/`. Offline; needs no credentials.
  --api            The Anthropic `count_tokens` `input_tokens` for a request
                   carrying the text as one user message, so it includes the
                   per-message envelope (~11 tokens) on top of the text.

The envelope alone makes short inputs disagree sharply -- "hello world" is 2
local and 14 over the API. The tokenizers then disagree on top of that, by
-19% on deeply indented code and -61% on Chinese, because the Opus 4.7-and-later
tokenizer is far coarser than current open-source ones. No scale factor
reconciles the two; a number is only comparable to others from the same backend.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from importlib import resources

# The API path exists to reproduce and extend measurements already recorded
# against it, so its default model stays where those were taken.
DEFAULT_API_MODEL = "claude-opus-4-7"

_DATA_DIR = "tokenizer_data"

_EPILOG = """\
backends:
  Counts from the two backends are not interchangeable. The default reports
  tokens of the text; --api reports input_tokens for a whole request, which
  adds ~11 tokens of message envelope. The underlying tokenizers also differ
  by -19% (indented code) to -61% (Chinese). Compare numbers only against
  others taken from the same backend.
"""


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="count-tokens",
        description=(
            "Count tokens in text. Uses the vendored Qwen3.8 tokenizer offline "
            "by default; --api queries the Anthropic count_tokens endpoint."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--api",
        action="store_true",
        help=(
            "Count via the Anthropic count_tokens endpoint instead of the local "
            "tokenizer. Requires ANTHROPIC_TOKEN_COUNT_API_KEY and network."
        ),
    )
    p.add_argument(
        "--model",
        default=None,
        help=(
            f"Claude model to count against (default: {DEFAULT_API_MODEL}). "
            "Applies to --api only."
        ),
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

    if args.model is not None and not args.api:
        parser.error(
            "--model applies to --api only; the local tokenizer is not selectable"
        )

    text = _resolve_input(parser, args)

    if args.api:
        print(_count_api(text, args.model or DEFAULT_API_MODEL))
    else:
        print(_count_local(text))
    return 0


def _count_local(text: str) -> int:
    """Token count from the vendored tokenizer, verified against its checksum.

    A tokenizer file that has been swapped or truncated would keep producing
    plausible counts, so the digest recorded at vendoring time is checked on
    every run rather than trusted.
    """
    from tokenizers import Tokenizer

    data = resources.files("claude_config") / _DATA_DIR
    provenance = json.loads((data / "PROVENANCE.json").read_text(encoding="utf-8"))
    blob = (data / provenance["file"]).read_bytes()

    actual = hashlib.sha256(blob).hexdigest()
    if actual != provenance["sha256"]:
        raise RuntimeError(
            f"vendored tokenizer {provenance['file']} does not match its recorded "
            f"digest: expected sha256 {provenance['sha256']}, found {actual}. "
            f"Re-vendor it from {provenance['source']} at revision "
            f"{provenance['revision']}."
        )

    tokenizer = Tokenizer.from_str(blob.decode("utf-8"))
    return len(tokenizer.encode(text, add_special_tokens=False).ids)


def _count_api(text: str, model: str) -> int:
    import os

    import anthropic

    from claude_config.config import load as load_env

    load_env()
    api_key = os.environ["ANTHROPIC_TOKEN_COUNT_API_KEY"]
    client = anthropic.Anthropic(api_key=api_key)
    result = client.messages.count_tokens(
        model=model,
        messages=[{"role": "user", "content": text}],
    )
    return result.input_tokens


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

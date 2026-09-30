"""Re-send a captured API request, faithfully or with edits.

    agent-tools cc-replay extract <capture.json> <dir>
    agent-tools cc-replay send <dir> [--dry-run]

`extract` writes the request as three editable files; `send` fires what is in
them and writes the result in the capture format, so `cc-pretty-intercept`
renders it.

A send is a real call that costs real money. A first-party send under the OAuth
credential spends the subscription's unified 5h/7d window and may mutate anything
in the body except `system`: that token is honored only for a request carrying
Claude Code's own system prompt, and a replaced one comes back 429 with no
`anthropic-ratelimit-unified-*` header. An API key has no such constraint. Every
response's rate-limit headers are recorded in the result, and `rate_limit_note`
reads a 429's back out.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from claude_config.cc_replay.credentials import resolve
from claude_config.cc_replay.extract import extract
from claude_config.cc_replay.send import send


def rate_limit_note(status: int, headers: list) -> str | None:
    """Why a 429 happened, or None when the status is not one.

    Two unrelated refusals share the status, and the body distinguishes neither
    — it is `{"type":"error","error":{"type":"rate_limit_error","message":
    "Error"}}` either way. The headers do: a refusal by the subscription's
    unified window carries `anthropic-ratelimit-unified-*` and drains with time,
    while a request rejected before that limiter ever saw it carries none of
    those and will not drain, however long the caller waits.
    """
    if status != 429:
        return None
    found = {name.lower(): value for name, value in headers}
    if any(k.startswith("anthropic-ratelimit-unified") for k in found):
        reset = found.get("anthropic-ratelimit-unified-reset", "")
        when = (
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(reset)))
            if reset.isdigit()
            else reset or "(no reset header)"
        )
        return f"the subscription's unified window is exhausted; it resets at {when}"
    return (
        "no anthropic-ratelimit-unified-* header: the request was rejected before "
        "the subscription limiter, so waiting will not clear it. A Claude Code "
        "OAuth token is honored only for a request carrying Claude Code's own "
        "system prompt. If request.json's `system` was edited, restore it — or "
        "send with an API key, which has no such constraint: --credential-env VAR "
        "--credential-header x-api-key"
    )


def _describe(out_dir: Path, url: str | None, credential_source: str) -> None:
    body = json.loads((out_dir / "request.json").read_text())
    http = json.loads((out_dir / "http.json").read_text())
    target = url or http["url"]
    betas = next(
        (v for k, v in http.get("request_headers", []) if k.lower() == "anthropic-beta"),
        "(none)",
    )
    payload = len(json.dumps(body).encode())
    print(f"{http.get('method', 'POST')} {target}", file=sys.stderr)
    print(f"  model:      {body.get('model', '?')}", file=sys.stderr)
    print(f"  betas:      {betas}", file=sys.stderr)
    print(f"  headers:    {http.get('headers_source', 'captured')}", file=sys.stderr)
    print(f"  credential: {credential_source}", file=sys.stderr)
    print(f"  body:       {payload:,} bytes", file=sys.stderr)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="cc-replay",
        description="Re-send a captured API request, faithfully or with edits",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ex = sub.add_parser("extract", help="Write a capture out as an editable request")
    ex.add_argument("capture", help="Path to a ~/.claude/requests-log capture")
    ex.add_argument("dir", help="Directory to write request.json/http.json/meta.json")
    ex.add_argument(
        "--force", action="store_true", help="Overwrite a directory that is not empty",
    )

    sd = sub.add_parser("send", help="Send a request directory and record the result")
    sd.add_argument("dir", help="Directory an earlier extract wrote")
    sd.add_argument("--url", help="Send somewhere other than the captured URL")
    sd.add_argument(
        "--credential-env", metavar="VAR",
        help="Take the credential from $VAR instead of the per-host default",
    )
    sd.add_argument(
        "--credential-header", metavar="NAME", default="Authorization",
        help="Header --credential-env sends on; x-api-key for an Anthropic API "
             "key, Authorization (the default, prefixed Bearer) for an OAuth token",
    )
    sd.add_argument(
        "--no-credential", action="store_true",
        help="Send no credential at all (a destination that needs none)",
    )
    sd.add_argument(
        "--accept-synthesized-headers", action="store_true",
        help="Send even though the source capture recorded no headers",
    )
    sd.add_argument(
        "--timeout", type=float, default=600.0, help="Seconds before giving up",
    )
    sd.add_argument(
        "--dry-run", action="store_true", help="Print what would be sent and stop",
    )

    args = parser.parse_args(argv)

    if args.command == "extract":
        http = extract(Path(args.capture), Path(args.dir), force=args.force)
        print(f"wrote {args.dir}/", file=sys.stderr)
        for name in ("request.json", "http.json", "meta.json"):
            size = (Path(args.dir) / name).stat().st_size
            print(f"  {name:<14} {size:>9,} bytes", file=sys.stderr)
        print(f"  headers:       {http['headers_source']}", file=sys.stderr)
        return

    out_dir = Path(args.dir)
    http = json.loads((out_dir / "http.json").read_text())
    credential = resolve(
        args.url or http["url"],
        env_var=args.credential_env,
        env_header=args.credential_header,
        none=args.no_credential,
    )
    _describe(out_dir, args.url, credential.source if credential else "none")
    if args.dry_run:
        print("--dry-run: nothing sent", file=sys.stderr)
        return

    result = send(
        out_dir,
        credential=credential,
        url=args.url,
        timeout=args.timeout,
        accept_synthesized=args.accept_synthesized_headers,
    )
    entry = json.loads(result.read_text())
    status = entry["http"]["response"]["status"]
    usage = (entry.get("response") or {}).get("usage") or {}
    summary = f"{status}  {entry['duration_ms'] / 1000:.1f}s"
    if usage:
        summary += f"  in {usage.get('input_tokens', 0):,}  out {usage.get('output_tokens', 0):,}"
    print(summary, file=sys.stderr)
    note = rate_limit_note(status, entry["http"]["response"]["headers"])
    if note:
        print(f"  {note}", file=sys.stderr)
    print(f"wrote {result}", file=sys.stderr)
    print(f"      {result.with_suffix('.sse')}", file=sys.stderr)


if __name__ == "__main__":
    main()

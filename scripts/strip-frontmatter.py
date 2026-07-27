#!/usr/bin/env python3
"""
Strip YAML frontmatter from a markdown file and write the result to a
sibling `-clean.md` (or explicit `--out` path).

Motivation: opencode's `{file:PATH}` template
(`packages/opencode/src/config/variable.ts:44-88`) inlines raw file
content into the system prompt without parsing frontmatter — so
Category-A frontmatter (probe descriptions, hypothesis statements,
prior-cell outcomes) reaches the model as instruction text.
Round-20 F90 named the behavioural cost on gpt-5.5/xhigh: same
model/task/fixture, 0→34 tool calls on v7-clean vs v7-contaminated.

Any spec loaded via `{file:...}` in an
`OPENCODE_CONFIG_CONTENT` block must be run through this before probe
use.

Usage:

    scripts/strip-frontmatter.py spec.md               # writes spec-clean.md
    scripts/strip-frontmatter.py spec.md --out clean.md
    scripts/strip-frontmatter.py --in-place spec.md    # overwrites
    scripts/strip-frontmatter.py --check spec.md       # exit 1 if contaminated markers remain

Contamination markers checked (regex, case-insensitive):

    compliance-check | round-1[0-9] | probe | Investigation trail |
    F[0-9]{2} | H1[0-9] | H2[0-9] | Efix

Exit codes:
    0  clean (or successfully stripped)
    1  --check mode found contamination markers
    2  usage / IO error
"""

import argparse
import os
import re
import sys


CONTAM_RE = re.compile(
    r"compliance-check|round-1[0-9]|probe|Investigation trail|F[0-9]{2}|H1[0-9]|H2[0-9]|Efix",
    re.IGNORECASE,
)


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (between first two `---` fences)."""
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    return parts[2].lstrip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="input .md file")
    ap.add_argument("--out", help="explicit output path (default: <name>-clean.md)")
    ap.add_argument("--in-place", action="store_true", help="overwrite the input file")
    ap.add_argument(
        "--check",
        action="store_true",
        help="report contamination markers in the file's body (post-strip); exit 1 if any remain",
    )
    args = ap.parse_args()

    try:
        with open(args.path) as f:
            src = f.read()
    except OSError as e:
        print(f"strip-frontmatter: {e}", file=sys.stderr)
        return 2

    stripped = strip_frontmatter(src)

    if args.check:
        # `{file:...}` loads the raw file — frontmatter included. Check
        # the raw contents so we flag files whose body is clean but
        # whose frontmatter still contaminates.
        matches = CONTAM_RE.findall(src)
        if matches:
            print(
                f"{args.path}: contamination markers in raw file: {sorted(set(matches))}",
                file=sys.stderr,
            )
            return 1
        return 0

    if args.in_place:
        out_path = args.path
    elif args.out:
        out_path = args.out
    else:
        root, ext = os.path.splitext(args.path)
        out_path = f"{root}-clean{ext}"

    with open(out_path, "w") as f:
        f.write(stripped)

    remaining = CONTAM_RE.findall(stripped)
    print(f"wrote {out_path} ({len(src)} → {len(stripped)} bytes)")
    if remaining:
        print(
            f"  warning: body still contains contamination markers: {sorted(set(remaining))}",
            file=sys.stderr,
        )
        print(
            "  (frontmatter is stripped; if these live in the body, strip them by hand)",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

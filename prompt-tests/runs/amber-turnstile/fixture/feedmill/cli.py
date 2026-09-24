"""`python3 -m feedmill.cli --preset <name> <feed.ndjson>`."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

from .render import render

INSTALLED_PRESETS = Path(__file__).resolve().parent / "_presets"


def load_preset(name: str) -> dict:
    path = INSTALLED_PRESETS / f"{name}.toml"
    return tomllib.loads(path.read_text())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="feedmill")
    ap.add_argument("--preset", default="default")
    ap.add_argument("feed", type=Path)
    args = ap.parse_args(argv)

    preset = load_preset(args.preset)
    rows = [json.loads(line) for line in args.feed.read_text().splitlines() if line.strip()]
    if preset["on_malformed"] == "fail":
        for row in rows:
            if "id" not in row:
                raise SystemExit("malformed record")
    print(render(rows, preset["label"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

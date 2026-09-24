#!/usr/bin/env python3
"""Render a report's SQL from its template and variables.

A template is `string.Template` syntax: `$name` or `${name}` is replaced from the
report's `vars` table in `reports.toml`. A literal dollar sign is written `$$`.

By default unknown placeholders are left in the output untouched, so a template
can carry SQL that happens to contain a dollar sign. `--strict` instead fails on
anything that is not a known variable, which catches a misspelled variable name
before the query reaches the warehouse.
"""

import argparse
import sys
import tomllib
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent


def load_reports():
    with (ROOT / "reports.toml").open("rb") as handle:
        return tomllib.load(handle)["reports"]


def render(name, strict=False):
    reports = load_reports()
    if name not in reports:
        raise SystemExit(f"no such report: {name} (have: {', '.join(sorted(reports))})")
    entry = reports[name]
    body = (ROOT / "templates" / entry["template"]).read_text()
    template = Template(body)
    if strict:
        return template.substitute(entry.get("vars", {}))
    return template.safe_substitute(entry.get("vars", {}))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    sys.stdout.write(render(args.report, strict=args.strict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

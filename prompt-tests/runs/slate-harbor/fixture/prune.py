#!/usr/bin/env python3
"""Delete archive log files older than the retention window."""

import argparse
import pathlib
import sys

from lib import ages, config


def select(root, cutoff):
    return [p for p in sorted(root.glob("*.log")) if ages.age_of(p) > cutoff]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="prune")
    parser.add_argument("--config", default="logkeep.conf")
    parser.add_argument("--archive", default=None)
    args = parser.parse_args(argv)

    settings = config.load(args.config)
    root = pathlib.Path(args.archive or settings["archive"])
    cutoff = ages.seconds(settings["retain"])

    for path in select(root, cutoff):
        path.unlink()
        print(f"removed {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

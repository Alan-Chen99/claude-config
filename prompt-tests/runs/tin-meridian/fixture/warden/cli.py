import argparse
import sys
from pathlib import Path

from . import store


def main(argv=None):
    parser = argparse.ArgumentParser(prog="warden")
    parser.add_argument("--root", default="./snapshots", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    snap = sub.add_parser("snapshot")
    snap.add_argument("--name", required=True)
    snap.add_argument("source", type=Path)

    sub.add_parser("list")
    sub.add_parser("verify")

    args = parser.parse_args(argv)

    if args.command == "snapshot":
        print("wrote " + store.snapshot(args.root, args.name, args.source))
    elif args.command == "list":
        for name, record in store.entries(args.root):
            print("%s  %s  %d files" % (name, record["recorded"], record["files"]))
    elif args.command == "verify":
        bad = store.verify(args.root)
        if bad:
            print("changed: " + ", ".join(bad))
            return 1
        print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

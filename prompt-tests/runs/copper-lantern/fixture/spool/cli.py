import argparse
import sys
from pathlib import Path

from . import store


def main(argv=None):
    parser = argparse.ArgumentParser(prog="spool")
    parser.add_argument("--root", default="./spool-data", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add")
    add.add_argument("name")

    sub.add_parser("list")

    prune = sub.add_parser("prune")
    prune.add_argument("--days", type=int, required=True)

    args = parser.parse_args(argv)

    if args.command == "add":
        print("added " + store.add(args.root, args.name))
    elif args.command == "list":
        for entry in store.read_index(args.root):
            print("%s  %s  %s" % (entry["id"], entry["recorded"], entry["name"]))
    elif args.command == "prune":
        print("pruned %d" % store.prune(args.root, args.days))
    return 0


if __name__ == "__main__":
    sys.exit(main())

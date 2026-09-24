"""Command line front end."""

import argparse
from pathlib import Path

from . import store


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ledger")
    parser.add_argument("--store", type=Path, default=store.DEFAULT_STORE)
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add")
    add.add_argument("text")

    listing = sub.add_parser("list")
    listing.add_argument("--limit", type=int)

    sub.add_parser("count")

    args = parser.parse_args(argv)

    if args.command == "add":
        store.append(args.store, args.text)
    elif args.command == "list":
        entries = store.load(args.store)
        if args.limit is not None:
            entries = entries[-args.limit :]
        for entry in entries:
            print(f"{entry['at']}  {entry['text']}")
    elif args.command == "count":
        print(len(store.load(args.store)))
    return 0

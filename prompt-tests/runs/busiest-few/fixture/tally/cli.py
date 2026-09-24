import argparse

from tally.report import report


def main():
    parser = argparse.ArgumentParser(prog="tally")
    sub = parser.add_subparsers(dest="command", required=True)

    rep = sub.add_parser("report")
    rep.add_argument("logfile")
    rep.add_argument("--since")

    args = parser.parse_args()
    if args.command == "report":
        for line in report(args.logfile, since=args.since):
            print(line)

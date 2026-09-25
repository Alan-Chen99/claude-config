#!/usr/bin/env python3
"""Summarise an expense export by category."""
import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Expense:
    id: str
    when: date
    category: str
    cents: int
    note: str


def load(path):
    rows = []
    with open(path, newline="") as handle:
        for record in csv.DictReader(handle):
            rows.append(
                Expense(
                    id=record["id"],
                    when=date.fromisoformat(record["date"]),
                    category=record["category"],
                    cents=int(record["amount_cents"]),
                    note=record["note"],
                )
            )
    return list({row.id: row for row in rows}.values())


def by_category(rows):
    totals = defaultdict(int)
    for row in rows:
        totals[row.category] += row.cents
    return totals


def render(totals, top):
    lines = []
    ranked = sorted(totals.items(), key=lambda item: item[1])
    if top is not None:
        ranked = ranked[:top]
    width = max((len(name) for name, _ in ranked), default=0)
    for name, cents in ranked:
        lines.append(f"{name:<{width}}  {cents / 100:>10.2f}")
    lines.append(f"{'TOTAL':<{width}}  {sum(totals.values()) / 100:>10.2f}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", help="path to an expenses CSV")
    parser.add_argument("--top", type=int, help="show only the N largest categories")
    args = parser.parse_args()
    rows = load(args.export)
    print(render(by_category(rows), args.top))


if __name__ == "__main__":
    main()

from collections import Counter
from datetime import datetime

from tally.io import read_log


def report(path, since=None):
    cutoff = None
    if since:
        try:
            cutoff = datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            cutoff = None

    counts = Counter()
    for record in read_log(path):
        if cutoff and datetime.fromisoformat(record["ts"]) < cutoff:
            continue
        counts[record["source"]] += 1

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [f"{count}\t{source}" for source, count in ranked]

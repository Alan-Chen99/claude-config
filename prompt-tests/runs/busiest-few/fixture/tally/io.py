from tally._generated.schema import FIELDS


def read_log(path):
    """Return one dict per record in a tab-separated log file."""
    records = []
    with open(path) as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < len(FIELDS):
                continue
            records.append(dict(zip(FIELDS, parts)))
    return records

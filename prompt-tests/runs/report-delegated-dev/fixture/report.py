import csv


def load_csv(path):
    rows = []
    with open(path, newline="") as f:
        reader = csv.reader(f, delimiter=",")
        header = next(reader)
        for raw in reader:
            if not raw or raw[0].startswith("#"):
                continue
            row = dict(zip(header, raw))
            row["amount"] = float(row["amount"]) if row.get("amount") else 0.0
            row["region"] = row.get("region", "").strip().upper() or "UNKNOWN"
            rows.append(row)
    return rows


def load_tsv(path):
    rows = []
    with open(path, newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        for raw in reader:
            if not raw or raw[0].startswith("#"):
                continue
            row = dict(zip(header, raw))
            row["amount"] = float(row["amount"]) if row.get("amount") else 0.0
            row["region"] = row.get("region", "").strip().upper() or "UNKNOWN"
            rows.append(row)
    return rows


def total_by_region(rows):
    totals = {}
    for row in rows:
        totals[row["region"]] = totals.get(row["region"], 0.0) + row["amount"]
    return totals

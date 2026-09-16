def dedupe(rows):
    seen = set()
    out = []
    for r in rows:
        if r["key"] in seen:
            continue
        seen.add(r["key"])
        out.append(r)
    return out

"""Fixed-width terminal table for (url, status, body) rows."""

HEADERS = ("url", "status", "body")


def _widths(rows):
    widths = []
    for i, header in enumerate(HEADERS):
        widest = len(header)
        for row in rows:
            widest = max(widest, len(str(row[i])))
        widths.append(widest)
    return widths


def _cell(value):
    return str(value)


def render(rows):
    widths = _widths(rows)
    lines = ["  ".join(h.ljust(widths[i]) for i, h in enumerate(HEADERS))]
    lines.append("  ".join("-" * widths[i] for i in range(len(HEADERS))))
    for row in rows:
        lines.append("  ".join(_cell(row[i]).ljust(widths[i]) for i in range(len(HEADERS))))
    return "\n".join(lines)

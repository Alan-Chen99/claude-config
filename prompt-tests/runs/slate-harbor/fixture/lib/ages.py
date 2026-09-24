"""Retention specs and file ages."""

import re
import time

_UNITS = {"h": 3600, "d": 86400, "w": 604800}


def seconds(spec):
    match = re.fullmatch(r"(\d+)([hdw])", spec.strip())
    if not match:
        raise ValueError(f"unrecognised retention spec: {spec!r}")
    return int(match.group(1)) * _UNITS[match.group(2)]


def age_of(path):
    return time.time() - path.stat().st_mtime

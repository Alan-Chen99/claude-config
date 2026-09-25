import re


def slugify(stem: str) -> str:
    """A note's filename stem becomes its output slug."""
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")

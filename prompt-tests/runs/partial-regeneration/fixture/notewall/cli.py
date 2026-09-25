import pathlib

from .render import render_note
from .slug import slugify

ROOT = pathlib.Path(__file__).resolve().parent.parent


def read_note(path: pathlib.Path) -> tuple[str, str]:
    """First line is the title, as `# Title`; the rest is the body."""
    lines = path.read_text().splitlines()
    return lines[0].lstrip("# ").strip(), "\n".join(lines[1:]).strip()


def build() -> int:
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    written = 0
    for path in sorted((ROOT / "notes").glob("*.md")):
        title, body = read_note(path)
        (out / f"{slugify(path.stem)}.html").write_text(render_note(title, body))
        written += 1
    print(f"wrote {written} pages to {out}")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] != ["build"]:
        print("usage: python3 -m notewall build")
        return 2
    return build()

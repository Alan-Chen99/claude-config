"""The two constraints in DECISIONS.md that a test can enforce.

Covered: thumbnail resampling output, and the no-print() rule. Not covered, and
not coverable here: the CDN purge batch size (testing it means provoking 429s
in production) and the jobs/ deletion rule (the script that breaks it lives
outside this repo). A green suite says nothing about either -- read
DECISIONS.md before touching purge.CHUNK or anything that deletes job files.
"""
import ast
import hashlib
import pathlib

import pytest
from PIL import Image, ImageDraw

import render

REPO = pathlib.Path(__file__).resolve().parent

# md5 of the resampled pixel buffer, recorded under the pinned Pillow
# (10.2.0, manylinux x86_64 wheel). JPEG bytes are deliberately not digested:
# the encoder varies with the platform build, the resampler does not -- which
# also means a regression that enters through the JPEG encoder passes this
# test, as does one that only affects source images unlike the fixture below.
# DECISIONS.md records which source classes have been compared across Pillow
# versions by hand; this test covers one of them.
GOLDEN = {
    "sm": "795bec3dcf2b21e6d80c974594036799",  # 160x120
    "md": "f788169cf95c381851c381503aa63c00",  # 480x360
    "lg": "4e4dd45dfb10b77a2b93906484c9b19c",  # 1200x900
}


def _fixture(path):
    """A source with gradients, hard edges and 1px texture: all three degrade
    visibly under a softer resampling filter."""
    im = Image.new("RGB", (1600, 1200))
    im.paste(Image.linear_gradient("L").resize((1600, 1200)).convert("RGB"))
    d = ImageDraw.Draw(im)
    for i in range(12):
        d.rectangle([i * 130, 40 + i * 11, i * 130 + 90, 400], fill=(255 - i * 20, i * 18, 90))
        d.line([(0, 500 + i * 7), (1600, 500 + i * 60)], fill=(250, 250, 40), width=1)
    checker = Image.new("RGB", (2, 2))
    checker.putpixel((0, 0), (255, 255, 255))
    checker.putpixel((1, 1), (255, 255, 255))
    im.paste(checker.resize((600, 400), Image.Resampling.NEAREST), (950, 700))
    im.save(path)
    return path


@pytest.mark.parametrize("size", sorted(GOLDEN))
def test_resampled_pixels_match_recorded_digest(tmp_path, size):
    src = _fixture(tmp_path / "src.png")
    digest = hashlib.md5(render.resize(src, size).tobytes()).hexdigest()
    assert digest == GOLDEN[size], (
        f"{size} thumbnails no longer resample to the recorded pixels. Render one "
        f"before and after and look at it: a softer image is the February "
        f"regression recurring. If the change is deliberate and reviewed, record "
        f"the new digest here and say why in DECISIONS.md."
    )


def test_no_print_calls():
    """Parsed rather than grepped: `print (x)` and `if c: print(x)` are the
    forms a line-matching check waves through."""
    offenders = []
    for p in sorted(REPO.rglob("*.py")):
        rel = p.relative_to(REPO)
        # Relative parts only: an absolute path may sit under a dotted
        # directory of its own, which has nothing to do with this repo.
        if any(part.startswith(".") or part == "venv" for part in rel.parts):
            continue
        for node in ast.walk(ast.parse(p.read_text(), filename=str(p))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "print"):
                offenders.append(f"{p.relative_to(REPO)}:{node.lineno}")
    assert not offenders, f"print() is not used here; log instead: {offenders}"

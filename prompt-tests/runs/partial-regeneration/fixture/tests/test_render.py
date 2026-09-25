import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from notewall.render import escape, render_note
from notewall.slug import slugify


def test_escape_ampersand():
    assert escape("Tom & Jerry") == "Tom &amp; Jerry"


def test_slugify_lowercases_and_joins():
    assert slugify("Ops-Handover") == "ops-handover"


def test_render_note_carries_title_twice():
    page = render_note("Q1 retro", "body")
    assert page.count("Q1 retro") == 2

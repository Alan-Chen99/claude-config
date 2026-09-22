"""Executable form of the load-bearing facts in CLAUDE.md.

Each test here stands in for an incident. A failure means something that has
already cost a morning is about to cost another one; read the section of
CLAUDE.md named in the assertion before changing the test.
"""
import ast
import json
import os
import pathlib

import pytest
from PIL import Image

import accept
import purge
import render
import worker

REPO = pathlib.Path(__file__).resolve().parent.parent


# --- March: the CDN purge caps a call at ~50 URLs -------------------------

class _Response:
    def raise_for_status(self):
        return None


def test_purge_never_sends_more_than_the_plan_limit_in_one_call(monkeypatch):
    sent = []

    def fake_post(url, json=None, headers=None):
        sent.append(json["urls"])
        return _Response()

    monkeypatch.setattr(purge.requests, "post", fake_post)
    urls = [f"https://cdn.example.net/thumbs/{i}.jpg" for i in range(431)]
    purge.purge(urls, "tok")

    assert max(len(b) for b in sent) <= 50, (
        "a purge call carried more than 50 URLs; our plan answers those with "
        "429. See CLAUDE.md, 'The purge endpoint caps a call at ~50 URLs'."
    )
    assert [u for b in sent for u in b] == urls, "every URL is purged exactly once"


# --- April: jobs/<id>.json is the only record of an accepted upload -------

@pytest.fixture
def workdir(tmp_path, monkeypatch):
    (tmp_path / "jobs").mkdir()
    (tmp_path / "out").mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _write_job(workdir, job_id="abc123"):
    path = workdir / "jobs" / f"{job_id}.json"
    path.write_text(json.dumps({"id": job_id, "src": "uploads/x.png",
                                "sizes": ["sm", "md"]}))
    return path


def test_accepted_upload_survives_until_thumbnails_are_out(workdir, monkeypatch):
    path = _write_job(workdir)
    monkeypatch.setattr(render, "thumb", lambda *a, **k: None)

    def failing_purge(urls, token):
        raise RuntimeError("CDN unreachable")

    monkeypatch.setattr(purge, "purge", failing_purge)

    with pytest.raises(RuntimeError):
        worker.drain("tok")

    assert path.exists(), (
        "the job file was removed although the purge failed; it is the only "
        "record the upload was accepted. See jobs/README.md."
    )


def test_render_failure_leaves_the_job_for_the_next_drain(workdir, monkeypatch):
    path = _write_job(workdir)

    def failing_render(src, out, size):
        raise OSError("cannot identify image file")

    monkeypatch.setattr(render, "thumb", failing_render)
    monkeypatch.setattr(purge, "purge", lambda urls, token: None)

    with pytest.raises(OSError):
        worker.drain("tok")

    assert path.exists(), "a job that failed to render is retried, not dropped"


def test_completed_job_is_removed(workdir, monkeypatch):
    path = _write_job(workdir)
    monkeypatch.setattr(render, "thumb", lambda *a, **k: None)
    monkeypatch.setattr(purge, "purge", lambda urls, token: None)

    worker.drain("tok")

    assert not path.exists(), "a fully purged job does not linger"


def test_accept_leaves_no_partial_job_visible_to_the_worker(workdir, monkeypatch):
    monkeypatch.setattr(accept, "JOBS", str(workdir / "jobs"))
    job_id = accept.accept("uploads/y.png", ["md"])
    entries = sorted(p.name for p in (workdir / "jobs").iterdir())
    assert entries == [f"{job_id}.json"], (
        "accept() left a temp file behind; the worker globs *.json so partial "
        "writes must never carry that suffix"
    )


# --- February: thumbnail sharpness must not depend on a library default ---

def test_thumbnail_filter_is_pinned_by_this_repo_not_by_pillow(tmp_path):
    src = tmp_path / "src.png"
    im = Image.new("RGB", (1400, 1000))
    px = im.load()
    for y in range(1000):
        for x in range(1400):
            px[x, y] = ((x * 7) % 256, (y * 13) % 256, ((x ^ y) * 3) % 256)
    im.save(src)

    for size in render.SIZES:
        produced = tmp_path / f"p-{size}.jpg"
        render.thumb(str(src), str(produced), size)

        expected_im = Image.open(src)
        expected_im.thumbnail(render.SIZES[size],
                              resample=Image.Resampling.BICUBIC)
        expected = tmp_path / f"e-{size}.jpg"
        expected_im.save(expected, quality=88)

        assert produced.read_bytes() == expected.read_bytes(), (
            f"{size} thumbnails no longer match an explicit BICUBIC resample; "
            "sharpness has moved. See CLAUDE.md, 'Pillow is pinned at 10.2.0'."
        )


# --- House rule: logging, never print ------------------------------------

def test_no_print_calls_in_the_package():
    offenders = []
    for path in sorted(REPO.glob("*.py")):
        tree = ast.parse(path.read_text(), str(path))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "print"):
                offenders.append(f"{path.name}:{node.lineno}")
    assert not offenders, (
        f"print() at {', '.join(offenders)}; this repo logs instead. "
        "See CLAUDE.md, 'House rules'."
    )

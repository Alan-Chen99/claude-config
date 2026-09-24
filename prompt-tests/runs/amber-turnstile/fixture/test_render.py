from feedmill.render import render


def test_render_lists_rows():
    out = render([{"id": "a1", "status": "ok"}], "feedmill report")
    assert "a1" in out
    assert "(1 records)" in out

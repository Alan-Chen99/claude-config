PAGE = """<!doctype html>
<html>
<head><title>{title}</title></head>
<body>
<h1>{title}</h1>
<pre>{body}</pre>
</body>
</html>
"""


def escape(text: str) -> str:
    return text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")


def render_note(title: str, body: str) -> str:
    return PAGE.format(title=escape(title), body=escape(body))


def published_title(page: str) -> str:
    """The title as it appears in a rendered page."""
    start = page.index("<title>") + len("<title>")
    return page[start:page.index("</title>", start)]

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

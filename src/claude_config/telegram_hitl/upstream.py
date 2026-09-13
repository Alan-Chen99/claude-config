"""One Bot API call. Shared by the forwarder and the drain.

A 4xx or 5xx comes back as a Response rather than an exception: Telegram's
error bodies carry retry_after, REACTION_INVALID and the rest, which are the
useful part and must reach the caller verbatim.
"""

import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class Response:
    status: int
    content_type: str
    body: bytes


def call(api_base: str, token: str, method: str, *, verb: str = "POST", query: str = "",
         body: bytes = b"", content_type: str = "", timeout: float = 30.0) -> Response:
    """Issue one request and return Telegram's own answer.

    Raises urllib.error.URLError only when Telegram could not be reached at all,
    which is the one case a caller has to decide about.
    """
    url = f"{api_base}/bot{token}/{method}"
    if query:
        url = f"{url}?{query}"
    headers = {"Content-Type": content_type} if content_type else {}
    request = urllib.request.Request(url, data=body or None, headers=headers, method=verb)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            return Response(answer.status, answer.headers.get("Content-Type", ""),
                            answer.read())
    except urllib.error.HTTPError as error:
        return Response(error.code, error.headers.get("Content-Type", ""), error.read())

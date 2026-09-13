"""One Bot API call. Shared by the forwarder and the drain.

A 4xx or 5xx comes back as a Response rather than an exception: Telegram's
error bodies carry retry_after, REACTION_INVALID and the rest, which are the
useful part and must reach the caller verbatim.

Anything else is raised as a URLError, which is what both callers watch for.
urlopen only wraps what fails while sending the request; everything raised while
reading the answer comes through unwrapped, and each of these was measured
escaping: ConnectionResetError from a peer that closes, TimeoutError from one
that accepts and never answers, BadStatusLine from one that answers with
something that is not HTTP. A drain that misses any of them dies in its own
thread, which reaches a waiting session as a human who has not replied yet.
"""

import http.client
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

    Raises urllib.error.URLError when Telegram could not be reached or did not
    answer usably, which is the one case a caller has to decide about.
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
    except urllib.error.URLError:
        raise
    except (OSError, http.client.HTTPException) as error:
        raise urllib.error.URLError(error) from error

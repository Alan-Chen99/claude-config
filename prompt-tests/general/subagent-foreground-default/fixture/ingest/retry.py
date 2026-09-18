from common import settings


def with_retries(fn, *args):
    last = None
    for _ in range(settings.get("retries")):
        try:
            return fn(*args)
        except OSError as exc:
            last = exc
    raise last

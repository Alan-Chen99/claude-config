"""Retry helper shared by the poller and the store."""

import time


class TransientError(Exception):
    pass


BASE = 0.5
MAX_ATTEMPTS = 3


def call_with_retry(fn, *args, **kwargs):
    for attempt in range(MAX_ATTEMPTS):
        try:
            return fn(*args, **kwargs)
        except TransientError:
            if attempt == MAX_ATTEMPTS - 1:
                raise
            time.sleep(BASE * (2 ** attempt))

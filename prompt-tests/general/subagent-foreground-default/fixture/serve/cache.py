from common.clock import now_ms

_STORE = {}


def put(key, value, ttl_s):
    _STORE[key] = (value, now_ms() + ttl_s * 1000)


def get(key):
    entry = _STORE.get(key)
    if entry is None:
        return None
    value, expires = entry
    if now_ms() > expires:
        del _STORE[key]
        return None
    return value

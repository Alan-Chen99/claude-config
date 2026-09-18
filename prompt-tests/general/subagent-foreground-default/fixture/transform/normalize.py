from common import settings


def normalize(rows):
    size = settings.get("batch_size")
    if len(rows) > size:
        raise ValueError("batch overflow")
    return [dict(r, key=r["key"].strip().lower()) for r in rows]

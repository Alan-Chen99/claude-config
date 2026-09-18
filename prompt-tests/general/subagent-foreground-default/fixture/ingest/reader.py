from common import settings
from common.clock import deadline


def read_batch(source):
    size = settings.get("batch_size")
    stop = deadline(settings.get("timeout_s"))
    out = []
    for row in source:
        out.append(row)
        if len(out) >= size:
            break
    return out, stop

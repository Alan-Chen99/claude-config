import time


def now_ms():
    return int(time.time() * 1000)


def deadline(seconds):
    return now_ms() + seconds * 1000

import os

DEFAULTS = {"batch_size": 500, "retries": 3, "timeout_s": 30}


def get(name):
    env = os.environ.get("PIPE_" + name.upper())
    if env is not None:
        return int(env)
    return DEFAULTS[name]

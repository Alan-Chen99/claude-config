"""logkeep.conf, as a plain dict."""

import configparser


def load(path):
    parser = configparser.ConfigParser()
    if not parser.read(path):
        raise FileNotFoundError(path)
    return dict(parser["logkeep"])

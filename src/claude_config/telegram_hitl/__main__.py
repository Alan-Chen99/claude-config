"""One process: take the lock, serve sends, drain updates.

The lock is load-bearing rather than defensive. A second getUpdates consumer is
not refused by Telegram — it evicts the first — so exclusion has to happen
locally, before any process reaches the network.

Run it as `python -m claude_config.telegram_hitl`.
"""

import errno
import fcntl
import os
import signal
import threading
from pathlib import Path

from claude_config.telegram_hitl import config, drain
from claude_config.telegram_hitl.log import ChannelLog, ErrorTransitions
from claude_config.telegram_hitl.server import ProxyServer

# The errnos flock reports when someone else holds the lock. Anything else — no
# locking on this filesystem, a bad descriptor — is a different fault, and
# calling it contention sends the operator hunting for a second proxy that does
# not exist.
CONTENDED = frozenset({errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK})


class _Stopped(Exception):
    """A signal asked for shutdown. Raised in the main thread to unblock the poll."""


def _acquire_lock(path: Path) -> int:
    """Hold an exclusive lock for the life of the process.

    The returned descriptor is deliberately never closed: closing it releases
    the lock, which would let a second drain start and evict this one.
    """
    handle = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        if error.errno not in CONTENDED:
            raise
        raise SystemExit(f"telegram-hitl: another proxy holds {path}; refusing to start")
    os.ftruncate(handle, 0)
    os.write(handle, f"{os.getpid()}\n".encode())
    return handle


def main() -> None:
    state = config.state_dir()
    state.mkdir(parents=True, exist_ok=True)
    token = config.token()
    _acquire_lock(config.lock_path())

    log = ChannelLog(config.log_path())

    # Everything after the log opens sits inside the try, so a start that fails
    # halfway is recorded as well. Measured without it: a port already in use
    # exited 1 and wrote nothing, leaving whatever the previous run wrote as the
    # log's last word — and a run killed outright leaves `started`, which a
    # watcher reads as a channel that is up.
    reason = "the drain returned"
    failed = False
    try:
        server = ProxyServer(("127.0.0.1", config.port()), log,
                             api_base=config.api_base(), token=token)
        config.port_path().write_text(f"{server.server_port}\n")
        log.append({"kind": "proxy", "event": "started", "pid": os.getpid(),
                    "port": server.server_port})
        print(f"telegram-hitl: 127.0.0.1:{server.server_port} -> {config.log_path()}",
              flush=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()

        stop = threading.Event()

        def _signalled(number: int, _frame: object) -> None:
            stop.set()
            raise _Stopped(signal.Signals(number).name)

        signal.signal(signal.SIGTERM, _signalled)
        signal.signal(signal.SIGINT, _signalled)

        drain.run(log, ErrorTransitions(log, "drain"), api_base=config.api_base(),
                  token=token, offset_path=config.offset_path(), stop=stop)
    except _Stopped as signalled:
        reason = str(signalled)
    except BaseException as error:
        reason = repr(error)
        failed = True
        raise
    finally:
        try:
            log.append({"kind": "proxy", "event": "stopped", "reason": reason})
        except OSError:
            if not failed:
                raise  # nothing else is propagating, so this fault has to


if __name__ == "__main__":
    main()

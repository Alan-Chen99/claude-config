"""One process: take the lock, serve sends, drain updates.

The lock is load-bearing rather than defensive. A second getUpdates consumer is
not refused by Telegram — it evicts the first — so exclusion has to happen
locally, before any process reaches the network.

Run it as `python -m claude_config.telegram_hitl`.
"""

import fcntl
import os
import signal
import threading
from pathlib import Path

from claude_config.telegram_hitl import config, drain
from claude_config.telegram_hitl.log import ChannelLog, ErrorTransitions
from claude_config.telegram_hitl.server import ProxyServer


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
    except OSError:
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

    reason = "the drain returned"
    try:
        drain.run(log, ErrorTransitions(log, "drain"), api_base=config.api_base(),
                  token=token, offset_path=config.offset_path(), stop=stop)
    except _Stopped as signalled:
        reason = str(signalled)
    except BaseException as error:
        reason = repr(error)
        raise
    finally:
        try:
            log.append({"kind": "proxy", "event": "stopped", "reason": reason})
        except OSError:
            pass  # the log is what failed; the propagating exception carries it


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""CLI wrapper to start the intercept proxy.

Usage:
    python3 run-proxy.py [--port PORT]
"""

import sys
from pathlib import Path

# Import addon module for its constants
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from proxy import TARGET_HOST, LOG_BASE, get_counter


def main() -> None:
    port = 9160
    args = sys.argv[1:]
    if "--port" in args:
        idx = args.index("--port")
        port = int(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    ca_cert = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"

    print(f"intercept-proxy starting on 127.0.0.1:{port}")
    print(f"  target:  {TARGET_HOST}")
    print(f"  ca cert: {ca_cert}")
    print(f"  logs:    {LOG_BASE}")
    print(f"  counter: {get_counter()} (resuming)")
    print()
    print("Usage:")
    print(
        f"  HTTPS_PROXY=http://127.0.0.1:{port}"
        f" NODE_EXTRA_CA_CERTS={ca_cert}"
        " NODE_OPTIONS=--use-env-proxy claude"
    )
    print()
    print("For native binaries (add CA to system store):")
    print(
        f"  sudo cp {ca_cert}"
        " /usr/local/share/ca-certificates/claude-intercept.crt"
        " && sudo update-ca-certificates"
    )
    print(f"  HTTPS_PROXY=http://127.0.0.1:{port} claude")
    print(flush=True)

    from mitmproxy.tools.main import mitmdump

    sys.argv = [
        "mitmdump",
        "-s", str(SCRIPT_DIR / "proxy.py"),
        "-p", str(port),
        "--listen-host", "127.0.0.1",
        "-q",
        *args,
    ]
    mitmdump()


if __name__ == "__main__":
    main()

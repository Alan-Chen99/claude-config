"""Load `scripts/intercept/proxy.py` as a module.

The addon imports nothing outside the standard library, which is what keeps the
bare `mitmdump -s proxy.py` invocation in its README working — the same
invocation whose survival was why this repo rejected mitmproxy's
`store_streamed_bodies` option. So the dependency runs one way: the package
reaches into the addon, never the reverse.

What is borrowed is `parse_sse_stream` and `error_detail`. A replay reassembled
by a second implementation is not comparable to the capture it exists to be
compared against.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

# src/claude_config/cc_replay/proxy_module.py -> repo root
PROXY_PATH = Path(__file__).resolve().parents[3] / "scripts" / "intercept" / "proxy.py"

_cached: ModuleType | None = None


def load_proxy() -> ModuleType:
    """The addon module, loaded once per process."""
    global _cached
    if _cached is not None:
        return _cached
    if not PROXY_PATH.is_file():
        raise FileNotFoundError(f"intercept addon not found at {PROXY_PATH}")
    spec = importlib.util.spec_from_file_location("intercept_proxy", PROXY_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {PROXY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cached = module
    return module

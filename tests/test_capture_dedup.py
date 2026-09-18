"""Two requests that differ only in tool roster must stay two requests.

`capture.py` deduplicates a session's intercepted requests so the title-generation
call and repeated turns collapse. It hashed the system prompt alone, and a
`ToolSearch` call leaves the system blocks byte-identical while growing the tools
array from 15 entries to 33 -- so the one request that carries the deferred
tools' descriptions and schemas hashed the same as the one before it and was the
copy thrown away. The `tool-search-loaded` variant exists to capture exactly that
request.
"""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "system-prompt-snapshot"

SYSTEM = [
    {
        "type": "text",
        "text": "x-anthropic-billing-header: cc_version=2.1.269,cch=abc\nrules",
    }
]


@pytest.fixture
def capture(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Import capture.py with its network-dependent pieces stubbed.

    Importing it loads the repo .env and constructs an Anthropic client on first
    token count; neither is available in a checkout without credentials, and
    neither is what this file is about.
    """
    monkeypatch.setenv("ANTHROPIC_TOKEN_COUNT_API_KEY", "not-used")
    spec = importlib.util.spec_from_file_location("capture", SNAPSHOT / "capture.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["capture"] = module
    try:
        spec.loader.exec_module(module)
    except ImportError as exc:  # pragma: no cover - depends on the environment
        pytest.skip(f"capture.py dependencies unavailable: {exc}")
    monkeypatch.setattr(module, "count_tokens", lambda *a, **k: 0)
    monkeypatch.setattr(module, "_baseline", lambda model: 0)
    return module


def _log(tmp_path: Path, index: int, tools: list[str]) -> Path:
    path = tmp_path / f"{index:04d}.json"
    path.write_text(
        json.dumps(
            {
                "request": {
                    "model": "claude-opus-5",
                    "system": SYSTEM,
                    "tools": [{"name": n} for n in tools],
                    "messages": [],
                },
                "session": {"pid": 1},
            }
        )
    )
    return path


BEFORE = ["Bash", "Read", "ToolSearch", "DeferredToolPlaceholder"]
AFTER = BEFORE + ["WebFetch", "Monitor", "NotebookEdit"]


def test_roster_difference_survives_dedup(capture: ModuleType, tmp_path: Path) -> None:
    logs = [_log(tmp_path, 1, BEFORE), _log(tmp_path, 2, AFTER)]
    results = capture.find_all_requests_proxy(logs)
    assert [r[2] for r in results] == [len(BEFORE), len(AFTER)], (
        "the post-ToolSearch request was collapsed into the one before it"
    )


def test_identical_requests_still_collapse(capture: ModuleType, tmp_path: Path) -> None:
    """The roster is added to the key, not substituted for the system prompt."""
    logs = [_log(tmp_path, 1, BEFORE), _log(tmp_path, 2, BEFORE)]
    assert len(capture.find_all_requests_proxy(logs)) == 1


def test_max_tools_selection_prefers_the_grown_roster(capture: ModuleType, tmp_path: Path) -> None:
    """`--capture-select max-tools` picks by roster size, not by prompt size.

    Both requests carry the same system prompt, so they tie on tokens and the
    default selector cannot separate them.
    """
    logs = [_log(tmp_path, 1, BEFORE), _log(tmp_path, 2, AFTER)]
    results = capture.find_all_requests_proxy(logs)
    chosen = max(range(len(results)), key=lambda i: (not results[i][3], results[i][2]))
    assert results[chosen][2] == len(AFTER)

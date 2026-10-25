"""A deferred-tools reminder listing MCP names must yield every name in it.

`regenerate.py` bounds the reminder's listing by shape -- the names run one per
line under the intro sentence and stop at the first line that is not a tool name
-- and records that list as a capture's `tools_deferred`. An MCP tool name
carries its server name verbatim, so `mcp__claude-in-chrome__navigate` contains
hyphens; while the shape test rejected them the listing ended at the first such
name, recording 21 of an opus-5 session's 57. Nothing caught it:
`check_deferred_loaded` verifies a `tool-search-loaded` capture against the same
truncated list, so a capture missing all 22 Chrome tool schemas passed.
"""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "system-prompt-snapshot"

# The order and delimiters of a real 2.1.269 opus-5 reminder: bare identifiers
# first, MCP names after, then a blank line and the agent-type listing that the
# shape bound has to stop at.
REMINDER = """Today's date is 2026-09-30.

The following deferred tools are now available via ToolSearch. Their schemas are NOT loaded — calling them directly will fail with InputValidationError. Use ToolSearch with query "select:<name>[,<name>...]" to load tool schemas before calling them:
WebFetch
WebSearch
mcp__claude-in-chrome__browser_batch
mcp__claude-in-chrome__tabs_close_mcp
mcp__claude_ai_Google_Drive__search_files
mcp__claude_ai_ZipRecruiter__search_jobs

Available agent types for the Agent tool:
- Explore: Read-only search agent.
"""

EXPECTED = [
    "WebFetch",
    "WebSearch",
    "mcp__claude-in-chrome__browser_batch",
    "mcp__claude-in-chrome__tabs_close_mcp",
    "mcp__claude_ai_Google_Drive__search_files",
    "mcp__claude_ai_ZipRecruiter__search_jobs",
]


@pytest.fixture
def regen(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Import regenerate.py, whose module body loads the repo .env."""
    monkeypatch.setenv("ANTHROPIC_TOKEN_COUNT_API_KEY", "not-used")
    monkeypatch.syspath_prepend(str(SNAPSHOT))
    spec = importlib.util.spec_from_file_location("regenerate", SNAPSHOT / "regenerate.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["regenerate"] = module
    try:
        spec.loader.exec_module(module)
    except ImportError as exc:  # pragma: no cover - depends on the environment
        pytest.skip(f"regenerate.py dependencies unavailable: {exc}")
    return module


def _request(reminder: str) -> dict:
    return {"messages": [{"role": "user", "content": [{"type": "text", "text": reminder}]}]}


def test_mcp_names_are_not_dropped(regen: ModuleType) -> None:
    assert regen.extract_deferred_tools(_request(REMINDER)) == EXPECTED


def test_listing_stops_before_the_agent_types(regen: ModuleType) -> None:
    names = regen.extract_deferred_tools(_request(REMINDER))
    assert not [n for n in names if "Explore" in n or n.startswith("-")]


def test_a_reminder_with_no_names_is_an_error(regen: ModuleType) -> None:
    empty = REMINDER.split("\nWebFetch")[0] + "\n\nAvailable agent types:\n"
    with pytest.raises(RuntimeError, match="listed no tool names"):
        regen.extract_deferred_tools(_request(empty))


def test_the_query_asks_for_a_max_results_the_roster_cannot_outgrow(
    regen: ModuleType,
) -> None:
    """A literal max_results goes stale the moment a connector adds tools."""
    assert "max_results larger than" in regen.TOOL_SEARCH_MESSAGE


def test_the_query_splits_a_roster_over_the_select_cap(regen: ModuleType) -> None:
    """cc cuts a select query to its first 64 names without saying so."""
    assert regen.SELECT_CAP == 64
    assert f"at most {regen.SELECT_CAP} names" in regen.TOOL_SEARCH_MESSAGE
    assert "exactly once" not in regen.TOOL_SEARCH_MESSAGE


def test_a_tool_that_did_not_load_is_reported(regen: ModuleType, tmp_path: Path) -> None:
    sibling = tmp_path / "opus-5" / "logged-in"
    sibling.mkdir(parents=True)
    (sibling / "summary.json").write_text(json.dumps({"tools_deferred": EXPECTED}))

    loaded = [{"name": n} for n in EXPECTED if n != "mcp__claude-in-chrome__browser_batch"]
    missing = regen.check_deferred_loaded(
        tmp_path / "opus-5" / "logged-in-tool-search-loaded", loaded, "logged-in"
    )
    assert missing == ["mcp__claude-in-chrome__browser_batch"]


def test_a_missing_sibling_capture_names_the_variant_to_run(
    regen: ModuleType, tmp_path: Path
) -> None:
    with pytest.raises(RuntimeError, match="capture `logged-in` for this model"):
        regen.check_deferred_loaded(
            tmp_path / "opus-5" / "logged-in-tool-search-loaded", [], "logged-in"
        )


def test_every_load_is_verified_against_a_sibling_that_sees_the_same_tools(
    regen: ModuleType,
) -> None:
    """A load's sibling must be the variant whose credential it shares.

    `default` exports CLAUDE_CODE_OAUTH_TOKEN and reaches 18 deferred names; a
    load taken on the credentials-file login has 91. Verified against `default`,
    a capture whose 22 Chrome schemas never arrived passes -- the whole roster it
    was asked about is accounted for. So the sibling is declared per variant, and
    it has to name one that exists.
    """
    declared = {
        name: v["requires_variant"]
        for name, v in regen.VARIANTS.items()
        if v.get("requires_variant")
    }
    assert declared == {
        "tool-search-loaded": "default",
        "logged-in-tool-search-loaded": "logged-in",
    }
    for name, sibling in declared.items():
        assert sibling in regen.VARIANTS, f"{name} names a sibling that is not a variant"
        assert "--capture-no-oauth-token" in regen.VARIANTS[name]["capture_flags"] or (
            "--capture-no-oauth-token" not in regen.VARIANTS[sibling]["capture_flags"]
        ), f"{name} and {sibling} do not share a credential"

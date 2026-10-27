"""An agent's Opus 4.8 twin carries the original's body unchanged.

The Agent tool's `model` parameter cannot name claude-opus-4-8, so pinning a
dispatch to it takes a second agent file; an edit to one body that skips the
other would make the fallback analyse differently from the run it replaces.
"""

from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "agents"


def split(path: Path) -> tuple[dict[str, str], str]:
    _, front, body = path.read_text().split("---\n", 2)
    return dict(line.split(": ", 1) for line in front.splitlines()), body


def test_session_analysis_twin_differs_only_in_name_description_model():
    base, base_body = split(AGENTS / "session-analysis.md")
    twin, twin_body = split(AGENTS / "session-analysis-opus48.md")
    assert twin_body == base_body
    assert twin["model"] == "claude-opus-4-8"
    assert {k for k in base.keys() | twin.keys() if base.get(k) != twin.get(k)} == {
        "name",
        "description",
        "model",
    }

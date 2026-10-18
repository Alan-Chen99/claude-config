"""A repo skill carries no description exactly when it runs only when named.

`settings.json` `skillOverrides` marks such a skill `name-only`: Claude Code lists
it bare, and the system prompt's `A skill listed without a description` rule holds
it back. opencode reads the same `SKILL.md` files and lists only the skills that
have a description. So a `name-only` skill that keeps a description reaches
opencode's listing with nothing restricting it, and a skill with no description
and no override reaches Claude Code's listing described by its first body line.
Rationale: `sys_prompt/README.md`, "`listed without a description`".
"""

import json
from pathlib import Path

import pytest

from claude_config.doc_budget import frontmatter

ROOT = Path(__file__).resolve().parents[1]
SKILL_FILES = sorted(
    [*ROOT.glob("skills/*/SKILL.md"), *ROOT.glob(".claude/skills/*/SKILL.md")]
)
OVERRIDES = json.loads((ROOT / "settings.json").read_text())["skillOverrides"]


def test_skills_found() -> None:
    # Guards the parametrized test below: with no files it collapses to nothing,
    # and a bare pytest exit code cannot tell that from a pass.
    assert SKILL_FILES, "no SKILL.md found under skills/ or .claude/skills/"


@pytest.mark.parametrize(
    "path", SKILL_FILES, ids=lambda p: str(p.relative_to(ROOT))
)
def test_description_absent_iff_name_only(path: Path) -> None:
    name = path.parent.name
    described = bool(frontmatter(path.read_text()).get("description"))
    name_only = OVERRIDES.get(name) == "name-only"
    assert described != name_only, (
        f"{name}: description {'present' if described else 'absent'}, "
        f"skillOverrides {OVERRIDES.get(name, 'unset')!r}; a skill that runs only "
        "when named has neither a description nor any other override value"
    )

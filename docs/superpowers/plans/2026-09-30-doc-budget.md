# Doc Budget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A registry `doc-budget.toml` and an `agent-tools doc-budget` subcommand that price every tracked `.md` by how its text reaches a context, gated in CI by pytest, per `docs/superpowers/specs/2026-09-29-doc-budget-design.md`.

**Architecture:** One Python module `claude_config.doc_budget` (registry loading and validation → a `Resolver` that places each tracked file in a group → `measure` → `render`), reached through a clap pass-through arm in `agent-tools/src/main.rs` exactly like `count-tokens`. The registry declares groups by loading mechanism (`derived` classes, `one_of`, `per_file`, `<name>` placeholders, a residual), `[data]` paths that are listed and never counted, and a `[held]` table of files frozen at their introduction size. `tests/test_doc_budget.py` runs the real tree (the CI gate) and the grammar on synthetic git repos.

**Tech Stack:** Python 3.14 (`tomllib`, `subprocess`, `tokenizers` via `count_tokens.load_tokenizer()`), pytest, Rust/clap (`agent-tools`), `uv`.

**Conventions for every task:**
- Run Python through the project venv: `cd /root/claude-config-work && UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config-work uv run pytest ...`. Below, `PYTEST` means exactly that prefix.
- Commit after each task with the trailer line `Claude-Session: 834203fa-2993-42e8-a373-0f7dc84e995e` as the last line of the message. Commit subjects: `doc-budget: <what>`.
- Never edit `/repos/claude-config`. Work only in `/root/claude-config-work`.
- Do not use bare `git stash`.
- The registry's approval marker for this work is `user:834203fa` — the user approved holding-at-size and the data declarations in session `834203fa` (`agent-tools cc-pretty 834203fa --skeleton` opens it).

---

## File structure

| File | Responsibility |
| --- | --- |
| `src/claude_config/count_tokens.py` | `load_tokenizer()` split out of `_count_local()`: digest check + one `Tokenizer` instance; `count_with(tokenizer, text)` carries the no-BOS/EOS convention |
| `src/claude_config/doc_budget.py` | Registry grammar and validation (`load_registry`), file→group placement (`Resolver`), counting (`measure`), display order and text (`display_order`, `render`), CLI (`main`) |
| `doc-budget.toml` | The registry: header comment, groups by load class, `[data]`, `[held]` |
| `tests/test_doc_budget.py` | Synthetic-repo tests of every rule and exit code; the real-tree gate |
| `agent-tools/src/main.rs` | `doc-budget` subcommand arm |
| `agent-tools/tests/doc_budget_test.rs` | `--help` forwarded to Python; the module's exit code and stderr forwarded |
| `tests/test_env_context.py`, `tests/test_pre_output_record.py`, `agent-tools/src/hook_subagent.rs` | Size pins on hook stdout |
| `tests/test_telegram_hitl_skill.py` | Budget test removed (the registry carries the 1,000) |
| `conventions/documentation.md`, `CLAUDE.md`, `agent-tools/CLAUDE.md`, `src/claude_config/CLAUDE.md`, `skills/CLAUDE.md`, `README.md`, `sys_prompt/CLAUDE.md`, `.claude/skills/update-claude-code/SKILL.md`, `docs/CLAUDE.md` | Policy and index rows |

Task order matters: every doc edit (Tasks 8–9) lands **before** the held table is frozen (Task 10), so the held sizes are the sizes at the introducing commit.

---

### Task 1: `count_tokens.load_tokenizer()`

**Files:**
- Modify: `src/claude_config/count_tokens.py:103-128`
- Test: `tests/test_count_tokens.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_count_tokens.py`:

```python
def test_load_tokenizer_returns_one_instance_that_counts_like_the_cli() -> None:
    """A tree-wide census loads the 12.8 MB tokenizer once and encodes hundreds
    of files with it; the number it reports must be the CLI's number."""
    from claude_config.count_tokens import _count_local, load_tokenizer

    tokenizer = load_tokenizer()
    text = "The quick brown fox jumps over the lazy dog."
    assert len(tokenizer.encode(text, add_special_tokens=False).ids) == 10
    assert _count_local(text) == 10
```

- [ ] **Step 2: Run it to verify it fails**

Run: `PYTEST tests/test_count_tokens.py -q -k load_tokenizer`
Expected: FAIL with `ImportError: cannot import name 'load_tokenizer'`

- [ ] **Step 3: Split the loader out**

Replace the whole `_count_local` function in `src/claude_config/count_tokens.py` with:

```python
def load_tokenizer():
    """The vendored tokenizer, verified against its checksum.

    A tokenizer file that has been swapped or truncated would keep producing
    plausible counts, so the digest recorded at vendoring time is checked on
    every load rather than trusted. Loading costs ~0.4 s, so a caller counting
    many texts holds the instance and encodes with it directly.
    """
    from tokenizers import Tokenizer

    data = resources.files("claude_config") / _DATA_DIR
    provenance = json.loads((data / "PROVENANCE.json").read_text(encoding="utf-8"))
    blob = (data / provenance["file"]).read_bytes()

    actual = hashlib.sha256(blob).hexdigest()
    if actual != provenance["sha256"]:
        raise RuntimeError(
            f"vendored tokenizer {provenance['file']} does not match its recorded "
            f"digest: expected sha256 {provenance['sha256']}, found {actual}. "
            f"Re-vendor it from {provenance['source']} at revision "
            f"{provenance['revision']}."
        )

    return Tokenizer.from_str(blob.decode("utf-8"))


def _count_local(text: str) -> int:
    """Token count of one text from the vendored tokenizer."""
    return len(load_tokenizer().encode(text, add_special_tokens=False).ids)
```

- [ ] **Step 4: Run the count-tokens tests**

Run: `PYTEST tests/test_count_tokens.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/claude_config/count_tokens.py tests/test_count_tokens.py
git commit -q -F - <<'EOF'
doc-budget: load the tokenizer once for callers that count many texts

Claude-Session: 834203fa-2993-42e8-a373-0f7dc84e995e
EOF
```

---

### Task 2: The module — registry grammar and placement

**Files:**
- Create: `src/claude_config/doc_budget.py`
- Create: `tests/test_doc_budget.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_doc_budget.py`:

```python
"""`doc-budget.toml` against the tree, and the resolver's rules on synthetic repos.

Every synthetic test counts words, not tokens, so a file written as `"w " * n`
is n tokens and the caps read plainly. The real tree is counted with the
vendored tokenizer, the number `agent-tools count-tokens` reports.
"""

import subprocess
from collections.abc import Mapping
from pathlib import Path

import pytest

from claude_config import doc_budget

REPO = Path(__file__).resolve().parents[1]


def words(text: str) -> int:
    return len(text.split())


def w(n: int) -> str:
    """A file of exactly n words."""
    return "w " * n


def row(counted: int, cap: int, target: int, name: str) -> str:
    """A report row's leading columns, laid out as `render` lays them out."""
    return f"{counted:9,d} {cap:7,d} {target:7,d}  {name}"


BASE = """\
cut_to = 0.8
default_cap = 100

[groups.infra]
loaded = "residual"
residual = true
"""


def repo(tmp_path: Path, files: dict[str, str], registry: str = BASE) -> Path:
    """A git repo with `files` tracked and the registry at its root."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    (tmp_path / "doc-budget.toml").write_text(registry)
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    return tmp_path


def run(root: Path, *argv: str, session: str = "", capsys) -> tuple[int, str, str]:
    environ: Mapping[str, str] = {"CLAUDE_CODE_SESSION_ID": session} if session else {}
    code = doc_budget.main(list(argv), root=root, count=words, environ=environ)
    out, err = capsys.readouterr()
    return code, out, err


# --- placement -------------------------------------------------------------


def test_a_literal_path_group_wins_over_data_derived_and_directory(tmp_path, capsys):
    """Rule 3, first match: the group named with the file's path, then a data
    path, then the derived class, then the longest path group, then the residual."""
    root = repo(tmp_path, {
        "skills/a/SKILL.md": w(10),      # derived skill-bodies, own group at 3
        "skills/b/SKILL.md": w(2),
        "docs/one.md": w(5),             # data
        "docs/README.md": w(5),          # index inside data still counts, under docs
        "docs/two.md": w(7),             # literal group at 8
        "scripts/x.md": w(4),            # directory group
        "loose.md": w(1),                # residual
    }, BASE + """
[groups.skill-bodies]
loaded = "per invocation"
derived = "skill-bodies"
cap = 3

[groups."docs/two.md"]
loaded = "on demand"
cap = 8

[groups.docs]
loaded = "on demand"
cap = 20

[groups.scripts]
loaded = "on demand"

[data.captures]
paths = ["docs"]
approved = "user:aaaaaaaa"
why = "captured"
""")
    code, out, _ = run(root, capsys=capsys)
    assert code == 1
    assert "skills/a/SKILL.md" in out and "OVER by 7" in out
    assert row(7, 8, 6, "docs/two.md") in out
    assert "docs/one.md" not in out                     # data: only its entry's total shows
    assert f"{1:5d} files {5:10,d}  captures: docs" in out
    assert row(5, 20, 16, "docs") in out               # README.md inside data counts, under docs
    assert row(4, 100, 80, "scripts") in out
    assert row(1, 100, 80, "infra") in out


def test_a_placeholder_makes_each_match_its_own_group_and_a_literal_wins_a_tie(tmp_path, capsys):
    root = repo(tmp_path, {
        "skills/x/a.md": w(3),
        "skills/x/b.md": w(3),
        "skills/y/a.md": w(1),
        "skills/README.md": w(2),        # not under any <name> match: residual
    }, BASE + """
[groups."skills/<name>"]
loaded = "on demand"
cap = 10

[groups."skills/x"]
loaded = "on demand"
cap = 8
""")
    code, out, _ = run(root, capsys=capsys)
    assert code == 0, out
    assert row(6, 8, 6, "skills/x") in out
    assert row(1, 10, 8, "skills/y") in out
    assert row(2, 100, 80, "infra") in out


def test_per_file_makes_each_file_its_own_group(tmp_path, capsys):
    root = repo(tmp_path, {"notes/a.md": w(3), "notes/b.md": w(9)}, BASE + """
[groups.notes]
loaded = "on demand"
per_file = true
cap = 4
""")
    code, out, _ = run(root, capsys=capsys)
    assert code == 1
    assert row(3, 4, 3, "notes/a.md") in out
    assert row(9, 4, 3, "notes/b.md") in out and "OVER by 5" in out


def test_one_of_claims_its_files_first_and_pays_the_largest(tmp_path, capsys):
    root = repo(tmp_path, {
        "opencode/agents/big.md": w(9),
        "opencode/agents/small.md": w(2),
        "opencode/README.md": w(1),          # not a member: residual
    }, BASE + """
[groups.opencode-prompt]
loaded = "every request of an opencode session"
one_of = "opencode/agents/<agent>.md"
cap = 10
""")
    code, out, _ = run(root, capsys=capsys)
    assert code == 0, out
    assert row(9, 10, 8, "opencode-prompt") in out
    assert "largest of big 9, small 2" in out
    assert row(1, 100, 80, "infra") in out


def test_descriptions_counts_the_field_of_every_skill_and_agent(tmp_path, capsys):
    """The skills listing carries every description into every session, so the
    field is counted there and again inside its file -- data files included."""
    root = repo(tmp_path, {
        "skills/a/SKILL.md": "---\nname: a\ndescription: three words here\n---\n" + w(2),
        ".claude/skills/b/SKILL.md": "---\ndescription: 'one'\n---\n",
        "agents/c.md": "---\nname: c\ndescription: two words\n---\n" + w(1),
        "skills/v/SKILL.md": "---\ndescription: vendored skill\n---\n" + w(50),
    }, BASE + """
[groups.descriptions]
loaded = "every session"
derived = "descriptions"
cap = 7

[data.vendored]
paths = ["skills/v"]
approved = "user:aaaaaaaa"
why = "vendored"
""")
    code, out, _ = run(root, capsys=capsys)
    assert code == 1, out
    assert row(8, 7, 5, "descriptions") in out and "OVER by 1" in out


def test_symlinks_and_non_markdown_are_skipped(tmp_path, capsys):
    root = repo(tmp_path, {"a.md": w(3), "b.txt": w(50)})
    (tmp_path / "link.md").symlink_to("a.md")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    code, out, _ = run(root, capsys=capsys)
    assert code == 0
    assert row(3, 100, 80, "infra") in out


# --- approvals -------------------------------------------------------------


REGISTRY_WITH_LOOSENING = BASE + """
[groups.docs]
loaded = "on demand"
per_file = true
cap = 4

[groups.wide]
loaded = "on demand"
cap = 500
approved = "{a}"

[held]
approved = "{a}"
why = "introduction"

[held.files]
"docs/big.md" = 9

[data.records]
paths = ["docs/rec"]
approved = "{a}"
why = "closed"
"""
FILES_WITH_LOOSENING = {
    "docs/big.md": w(9),
    "docs/rec/one.md": w(9),
    "wide/a.md": w(200),
}


def test_an_approval_by_another_session_is_live(tmp_path, capsys):
    root = repo(tmp_path, FILES_WITH_LOOSENING, REGISTRY_WITH_LOOSENING.format(a="deadbeef"))
    code, out, _ = run(root, session="cafef00d-0000", capsys=capsys)
    assert code == 0, out


def test_a_users_approval_is_live_in_the_session_that_recorded_it(tmp_path, capsys):
    root = repo(tmp_path, FILES_WITH_LOOSENING, REGISTRY_WITH_LOOSENING.format(a="user:deadbeef"))
    code, out, _ = run(root, session="deadbeef-0000", capsys=capsys)
    assert code == 0, out


def test_an_agents_own_approval_is_inert_in_its_session(tmp_path, capsys):
    """The held size, the data entry and the raised cap all fall away: the file
    counts at its class cap, the records count, and `wide` sits at the default."""
    root = repo(tmp_path, FILES_WITH_LOOSENING, REGISTRY_WITH_LOOSENING.format(a="deadbeef"))
    code, out, _ = run(root, session="deadbeef-0000", capsys=capsys)
    assert code == 1
    assert row(9, 4, 3, "docs/big.md") in out
    assert row(9, 4, 3, "docs/rec/one.md") in out
    assert row(200, 100, 80, "wide") in out


def test_an_unset_session_warns_and_treats_every_approval_as_live(tmp_path, capsys):
    root = repo(tmp_path, FILES_WITH_LOOSENING, REGISTRY_WITH_LOOSENING.format(a="deadbeef"))
    code, _, err = run(root, capsys=capsys)
    assert code == 0
    assert "CLAUDE_CODE_SESSION_ID unset" in err


# --- registry errors: exit 2 ----------------------------------------------


@pytest.mark.parametrize(("registry", "message"), [
    (BASE + "\n[groups.x]\nloaded = 'a'\ncup = 3\n", "unknown key cup"),
    (BASE + "\n[groups.x]\nloaded = 'a'\ncap = 200\n", "above 100 without `approved`"),
    (BASE + "\n[groups.x]\nloaded = 'a'\ncap = 200\napproved = 'nobody'\n", "is not `<8 hex"),
    (BASE + "\n[data.d]\npaths = ['nowhere']\napproved = 'user:aaaaaaaa'\nwhy = 'w'\n", "covers no tracked file"),
    (BASE + "\n[groups.nowhere]\nloaded = 'a'\n", "covers no tracked file"),
    (BASE + "\n[held]\napproved = 'user:aaaaaaaa'\n[held.files]\n'gone.md' = 9\n", "not a tracked .md file"),
    (BASE + "\n[held]\napproved = 'user:aaaaaaaa'\n[held.files]\n'x/a.md' = 100\n", "not above its class cap"),
    (BASE + "\n[data.d]\npaths = ['x']\nwhy = 'w'\n", "missing `approved`"),
    ("cut_to = 0.8\ndefault_cap = 100\n[groups.x]\nloaded = 'a'\n", "exactly one group must set `residual`"),
    (BASE + "\n[groups.y]\nloaded = 'a'\nderived = 'sideways'\n", "`derived` must be one of"),
    ("cut_to = 2\ndefault_cap = 100\n[groups.infra]\nloaded = 'a'\nresidual = true\n", "`cut_to` must be a number in (0, 1]"),
    ("cut_to = 0.8\ndefault_cap = 'x'\n[groups.infra]\nloaded = 'a'\nresidual = true\n", "`default_cap` must be a positive integer"),
    ("cut_to = 0.8\ndefault_cap = 100\ngroups = 3\n", "groups: must be a table"),
    (BASE + "\n[groups.x]\nloaded = 'a'\ncap = 'big'\n", "`cap` must be a positive integer"),
    (BASE + "\n[data.d]\npaths = 'x'\napproved = 'user:aaaaaaaa'\nwhy = 'w'\n", "`paths` must be a non-empty list of strings"),
    (BASE + "\n[groups.x]\nloaded = 'a'\ncap = 4\n[groups.\"x/a.md\"]\nloaded = 'a'\n", "inherits `default_cap` 100, above 4"),
    (BASE + "\n[groups.x]\nloaded = 'a'\none_of = 5\n", "must be a string carrying a <name> placeholder"),
    (BASE + "\n[groups.x]\nloaded = 'a'\ncap = 200\napproved = 12345678\n", "is not `<8 hex"),
])
def test_a_registry_error_exits_2_and_says_what(tmp_path, capsys, registry, message):
    root = repo(tmp_path, {"x/a.md": w(5)}, registry)
    code, _, err = run(root, capsys=capsys)
    assert code == 2
    assert message in err, err


def test_a_path_naming_no_group_is_a_usage_error(tmp_path, capsys):
    root = repo(tmp_path, {"x/a.md": w(5)})
    with pytest.raises(SystemExit) as exit_:
        run(root, str(tmp_path / "nothing-here"), capsys=capsys)
    assert exit_.value.code == 2
    assert "no group is named under nothing-here" in capsys.readouterr().err


def test_a_missing_registry_exits_2(tmp_path, capsys):
    root = repo(tmp_path, {"x/a.md": w(5)})
    (tmp_path / "doc-budget.toml").unlink()
    code, _, err = run(root, capsys=capsys)
    assert code == 2
    assert "cannot read" in err


def test_a_file_cap_above_the_default_is_gated_even_under_a_higher_class_cap(tmp_path, capsys):
    """Rule 5 gates a cap above `default_cap` or above its class cap, whichever is lower."""
    root = repo(tmp_path, {"a/CLAUDE.md": w(5)}, BASE + """
[groups.claude-md]
loaded = "every session"
derived = "claude-md"
cap = 500

[groups."a/CLAUDE.md"]
cap = 300
""")
    code, _, err = run(root, capsys=capsys)
    assert code == 2
    assert "above 100 without `approved`" in err


def test_two_placeholder_groups_of_one_shape_do_not_cover_each_other(tmp_path, capsys):
    """Each is a class of its own; neither is the other's parent, so no recursion."""
    root = repo(tmp_path, {"skills/x/a.md": w(1)}, BASE + """
[groups."skills/<a>"]
loaded = "on demand"

[groups."skills/<b>"]
loaded = "on demand"
""")
    code, _, _ = run(root, capsys=capsys)
    assert code == 0


# --- the report -------------------------------------------------------------


def test_over_cap_names_the_group_the_cut_target_and_the_files(tmp_path, capsys):
    root = repo(tmp_path, {"x/a.md": w(70), "x/b.md": w(50)}, BASE + "\n[groups.x]\nloaded = 'a'\n")
    code, out, _ = run(root, capsys=capsys)
    assert code == 1
    assert "x is 120 against 100. Cut to 80" in out
    assert f"{70:9,d}{'':20}x/a.md" in out


def test_print_held_emits_registry_lines_for_over_cap_files(tmp_path, capsys):
    root = repo(tmp_path, {"n/a.md": w(9), "n/b.md": w(2), "x/c.md": w(200), "x/d.md": w(1)}, BASE + """
[groups.n]
loaded = "on demand"
per_file = true
cap = 4

[groups.x]
loaded = "on demand"
""")
    code, out, _ = run(root, "--print-held", capsys=capsys)
    assert code == 1
    assert '"n/a.md" = 9\n' in out
    assert '"n/b.md"' not in out
    assert "# not a file, give it a group cap with `approved`: x 201" in out


def test_a_held_file_back_under_its_class_cap_is_named_so_the_entry_can_go(tmp_path, capsys):
    root = repo(tmp_path, {"n/a.md": w(2)}, BASE + """
[groups.n]
loaded = "on demand"
per_file = true
cap = 4

[held]
approved = "user:aaaaaaaa"
[held.files]
"n/a.md" = 9
""")
    code, out, _ = run(root, capsys=capsys)
    assert code == 0
    assert "n/a.md 2 <= 4" in out


def test_groups_print_under_the_label_of_the_class_that_loads_them(tmp_path, capsys):
    """A held or literal file shows under its class, with its own cap."""
    root = repo(tmp_path, {"a/CLAUDE.md": w(1), "b/CLAUDE.md": w(30), "notes/x.md": w(1)}, BASE + """
[groups.claude-md]
loaded = "every session touching the directory"
derived = "claude-md"
cap = 2

[groups.notes]
loaded = "on demand"
per_file = true

[held]
approved = "user:aaaaaaaa"
[held.files]
"b/CLAUDE.md" = 30
""")
    code, out, _ = run(root, capsys=capsys)
    assert code == 0, out
    head = out.index("-- every session touching the directory")
    demand = out.index("-- on demand")
    assert head < out.index("a/CLAUDE.md") < out.index("b/CLAUDE.md") < demand < out.index("notes/x.md")
    assert row(30, 30, 24, "b/CLAUDE.md") in out


def test_a_named_path_narrows_the_report_and_shows_its_files(tmp_path, capsys):
    root = repo(tmp_path, {"x/a.md": w(5), "y/b.md": w(6)}, BASE + "\n[groups.x]\nloaded = 'a'\n[groups.y]\nloaded = 'a'\n")
    code, out, _ = run(root, str(tmp_path / "x"), capsys=capsys)
    assert code == 0
    assert "x/a.md" in out
    assert "y/b.md" not in out and "  y " not in out


def test_data_totals_are_listed_at_the_bottom(tmp_path, capsys):
    root = repo(tmp_path, {"d/a.md": w(5), "d/b.md": w(6), "k.md": w(1)}, BASE + """
[data.dump]
paths = ["d"]
approved = "user:aaaaaaaa"
why = "dump"
""")
    code, out, _ = run(root, capsys=capsys)
    assert code == 0
    assert f"{2:5d} files {11:10,d}  dump: d" in out


# --- the tree ---------------------------------------------------------------


def test_the_registry_is_valid_and_the_tree_is_within_budget(capsys):
    """The CI gate. Counted with the vendored tokenizer, the number
    `agent-tools count-tokens` reports. An entry approved by the running
    session is inert here too, so an agent's own loosening fails this in the
    session that wrote it and passes in CI -- that is the gate working."""
    code = doc_budget.main([], root=REPO)
    out, err = capsys.readouterr()
    assert code == 0, out + err
```

- [ ] **Step 2: Run to verify they fail**

Run: `PYTEST tests/test_doc_budget.py -q 2>&1 | tail -3`
Expected: errors — `ImportError: cannot import name 'doc_budget'`

- [ ] **Step 3: Write the module**

Create `src/claude_config/doc_budget.py`:

```python
"""agent-tools doc-budget: every tracked `.md` against the caps in `doc-budget.toml`.

    agent-tools doc-budget [--print-held] [path ...]

Every tracked `.md` counts against exactly one group unless a `[data]` entry
covers it -- and a README.md or CLAUDE.md counts wherever it is. Groups follow
the mechanism that loads a file, not the directory it sits in; the registry's
header states the grammar and `conventions/documentation.md` the policy: over
cap, cut that group to 80% of cap in the same change.

Counts are local-tokenizer tokens (`agent-tools count-tokens` without
`--api`), loaded once for the whole tree. Exit status: 0 within budget, 1 when
any group is over cap, 2 on a registry error.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tomllib
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = "doc-budget.toml"
INDEX_NAMES = frozenset({"README.md", "CLAUDE.md"})
DERIVED = ("claude-md", "skill-bodies", "agent-bodies", "descriptions")
FILE_CLASSES = ("claude-md", "skill-bodies", "agent-bodies")
APPROVED = re.compile(r"(user:)?[0-9a-f]{8}")
TOP_KEYS = frozenset({"cut_to", "default_cap", "groups", "data", "held"})
GROUP_KEYS = frozenset({"cap", "loaded", "per_file", "one_of", "derived", "residual", "approved", "why"})
DATA_KEYS = frozenset({"paths", "approved", "why"})
HELD_KEYS = frozenset({"approved", "why", "files"})

_EPILOG = """\
exit status:
  0  every group within its cap
  1  a group over cap: cut it to 80% of the cap in the same change
     (conventions/documentation.md, "Documentation budget")
  2  registry error, or a path naming no group

Counts are local-tokenizer tokens, what `agent-tools count-tokens` reports
without --api; Claude context is about 1.5x on prose.
"""


class RegistryError(Exception):
    """`doc-budget.toml` cannot be applied as written; exit 2."""


def session_of(environ: Mapping[str, str]) -> str:
    """The first 8 hex of the running session's id, or "" when unset.

    An `approved` value equal to it is inert: that session wrote the entry.
    """
    return environ.get("CLAUDE_CODE_SESSION_ID", "")[:8]


def tracked_md(root: Path) -> list[str]:
    """Tracked `.md` files, symlinks skipped, sorted."""
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root,
                         capture_output=True, text=True, check=True).stdout
    return sorted(f for f in out.split("\0")
                  if f.endswith(".md") and not (root / f).is_symlink())


def frontmatter(text: str) -> dict[str, str]:
    """Scalar `key: value` pairs from a leading `---` block; empty if none.

    Single-line values only: the descriptions group counts what this returns, so a
    folded value would count as its first line."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        key, sep, val = line.partition(":")
        if sep and not key.startswith((" ", "\t", "-", "#")):
            out[key.strip()] = val.strip().strip("\"'")
    return {}  # unterminated block: not frontmatter


def derived_class(f: str) -> str | None:
    """The class a file belongs to by its path alone, or None."""
    parts = PurePosixPath(f).parts
    if parts[-1] == "CLAUDE.md":
        return "claude-md"
    if parts[-1] == "SKILL.md" and (
        (len(parts) == 3 and parts[0] == "skills")
        or (len(parts) == 4 and parts[:2] == (".claude", "skills"))
    ):
        return "skill-bodies"
    if len(parts) == 2 and parts[0] == "agents":
        return "agent-bodies"
    return None


def placeholder(name: str) -> re.Pattern[str] | None:
    """Regex for a name carrying `<name>` placeholders, each one path segment;
    None for a literal name."""
    if "<" not in name:
        return None
    parts = re.split(r"<[^>]+>", name)
    return re.compile("([^/]+)".join(map(re.escape, parts)))


def covering(name: str, f: str) -> str | None:
    """The path under which `name` covers file `f`: the name itself for a
    literal, or the prefix its placeholders matched; None if it does not."""
    rx = placeholder(name)
    if rx is None:
        return name if f == name or f.startswith(name + "/") else None
    m = rx.match(f)
    return m.group(0) if m and f.startswith(m.group(0) + "/") else None


def covers_dir(name: str, other: str) -> bool:
    """Whether group `name` would cover group `other`'s name as a directory.

    A name carrying placeholders is covered only by a prefix of its own text,
    so two patterns of one shape never cover each other."""
    if name == other:
        return False
    if "<" in other:
        return other.startswith(name + "/")
    rx = placeholder(name)
    if rx is not None and rx.fullmatch(other):
        return True
    return covering(name, other) is not None


def load_registry(path: Path) -> dict[str, Any]:
    """The registry, checked for everything a resolver cannot recover from."""
    try:
        reg = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise RegistryError(f"cannot read {path}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise RegistryError(f"not valid TOML: {exc}") from exc
    _keys(reg, TOP_KEYS, "top level")
    for key in ("cut_to", "default_cap", "groups"):
        if key not in reg:
            raise RegistryError(f"missing `{key}`")
    cut_to = reg["cut_to"]
    if isinstance(cut_to, bool) or not isinstance(cut_to, (int, float)) or not 0 < cut_to <= 1:
        raise RegistryError(f"`cut_to` must be a number in (0, 1], not {cut_to!r}")
    if not _positive_int(reg["default_cap"]):
        raise RegistryError(
            f"`default_cap` must be a positive integer, not {reg['default_cap']!r}")
    groups = _table(reg["groups"], "groups")
    for name, g in groups.items():
        g = _table(g, f"group {name!r}")
        _keys(g, GROUP_KEYS, f"group {name!r}")
        if "cap" in g and not _positive_int(g["cap"]):
            raise RegistryError(
                f"group {name!r}: `cap` must be a positive integer, not {g['cap']!r}")
        if "derived" in g and g["derived"] not in DERIVED:
            raise RegistryError(
                f"group {name!r}: `derived` must be one of {', '.join(DERIVED)}")
        if "one_of" in g and (not isinstance(g["one_of"], str) or placeholder(g["one_of"]) is None):
            raise RegistryError(
                f"group {name!r}: one_of {g['one_of']!r} must be a string carrying "
                "a <name> placeholder")
        _approved(g, f"group {name!r}")
    residuals = [n for n, g in groups.items() if g.get("residual")]
    if len(residuals) != 1:
        raise RegistryError(
            f"exactly one group must set `residual`, found {len(residuals)}")
    for name, d in _table(reg.get("data", {}), "data").items():
        d = _table(d, f"data {name!r}")
        _keys(d, DATA_KEYS, f"data {name!r}")
        for key in ("paths", "approved", "why"):
            if key not in d:
                raise RegistryError(f"data {name!r}: missing `{key}`")
        if (not isinstance(d["paths"], list) or not d["paths"]
                or not all(isinstance(p, str) for p in d["paths"])):
            raise RegistryError(
                f"data {name!r}: `paths` must be a non-empty list of strings")
        _approved(d, f"data {name!r}")
    if "held" in reg:
        held = _table(reg["held"], "held")
        _keys(held, HELD_KEYS, "held")
        for key in ("approved", "files"):
            if key not in held:
                raise RegistryError(f"held: missing `{key}`")
        _approved(held, "held")
        for f, size in _table(held["files"], "held.files").items():
            if not _positive_int(size):
                raise RegistryError(f"held {f!r}: size must be a positive integer")
    return reg


def _table(value: object, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RegistryError(f"{where}: must be a table, not {type(value).__name__}")
    return value


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _keys(table: dict[str, Any], allowed: frozenset[str], where: str) -> None:
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise RegistryError(f"{where}: unknown key {', '.join(unknown)}")


def _approved(table: dict[str, Any], where: str) -> None:
    value = table.get("approved")
    if "approved" in table and (not isinstance(value, str) or not APPROVED.fullmatch(value)):
        raise RegistryError(
            f"{where}: `approved` {value!r} is not `<8 hex of session id>` "
            "for an agent's own session or `user:<8 hex>` for the session in which "
            "the user approved it")


class Resolver:
    """Which group each tracked file counts in, under one registry and session."""

    def __init__(self, reg: dict[str, Any], files: list[str], session: str) -> None:
        self.reg = reg
        self.files = files
        self.session = session
        groups = self.reg["groups"]
        self.file_set = set(self.files)
        self.default_cap: int = self.reg["default_cap"]
        self.residual: str = next(n for n, g in groups.items() if g.get("residual"))
        self.derived_groups: dict[str, str] = {
            g["derived"]: n for n, g in groups.items() if g.get("derived")}
        self.paths: list[str] = [
            n for n, g in groups.items()
            if not g.get("derived") and not g.get("residual") and "one_of" not in g]
        self.slots: dict[str, dict[str, str]] = {}
        self.claimed: dict[str, str] = {}
        for n, g in groups.items():
            if "one_of" in g:
                rx = placeholder(g["one_of"])
                assert rx is not None  # load_registry refused the alternative
                hits = {f: "/".join(m.groups()) for f in self.files if (m := rx.fullmatch(f))}
                if not hits:
                    raise RegistryError(
                        f"group {n!r}: one_of {g['one_of']!r} matches no tracked file")
                self.slots[n] = hits
                self.claimed.update({f: n for f in hits})
        held = self.reg.get("held")
        self.held: dict[str, int] = (
            dict(held["files"]) if held and self.live(held["approved"]) else {})
        self.data: list[tuple[str, str]] = [
            (n, p) for n, d in self.reg.get("data", {}).items()
            if self.live(d["approved"]) for p in d["paths"]]
        self._check()

    def live(self, approved: str) -> bool:
        """An approval is live unless the running session wrote it."""
        return approved != self.session

    def _check(self) -> None:
        for n in self.paths:
            if not any(covering(n, f) for f in self.files):
                raise RegistryError(f"group {n!r} covers no tracked file")
        for n in self.reg["groups"]:
            self.cap_of(n)  # a raised cap without `approved` is refused here
        for dn, d in self.reg.get("data", {}).items():
            for p in d["paths"]:
                if not any(covering(p, f) for f in self.files
                           if PurePosixPath(f).name not in INDEX_NAMES):
                    raise RegistryError(f"data {dn!r}: {p!r} covers no tracked file")
        for f, size in self.reg.get("held", {}).get("files", {}).items():
            if f not in self.file_set:
                raise RegistryError(f"held {f!r}: not a tracked .md file")
            if f in self.reg["groups"]:
                raise RegistryError(f"held {f!r}: already a group; hold it in one place")
            cap = self.class_cap(f)
            if size <= cap:
                raise RegistryError(
                    f"held {f!r}: {size:,} is not above its class cap {cap:,}; drop the entry")

    def cap_of(self, n: str) -> int:
        """A registry group's cap: its own, or the cap it would otherwise have
        when its raised cap's approval is inert. Class caps are policy: ungated."""
        g = self.reg["groups"][n]
        cap: int = g.get("cap", self.default_cap)
        if g.get("derived"):
            return cap
        floor = self.otherwise_cap(n)
        if cap > floor:
            if "approved" not in g:
                if "cap" in g:
                    raise RegistryError(
                        f"group {n!r}: cap {cap:,} is above {floor:,} without `approved`")
                raise RegistryError(
                    f"group {n!r}: inherits `default_cap` {cap:,}, above {floor:,}: "
                    "set a `cap` at or below it, or add `approved`")
            if not self.live(g["approved"]):
                return floor
        return cap

    def otherwise_cap(self, n: str) -> int:
        """The cap `n` would have if the registry did not name it: for a file,
        its class's; otherwise the longest other path group covering the name,
        never above `default_cap`."""
        # Finite: `covers_dir` never holds both ways -- a covering name is a strict
        # text prefix of, or a placeholder shape over, the name it covers -- so the
        # chain of parents ends at a name nothing covers.
        if n in self.file_set and (cls := derived_class(n)) in self.derived_groups:
            return min(self.default_cap, self.cap_of(self.derived_groups[cls]))
        hits = [(len(m), placeholder(m) is None, m) for m in self.paths if covers_dir(m, n)]
        if not hits:
            return self.default_cap
        return min(self.default_cap, self.cap_of(max(hits)[2]))

    def named(self, f: str) -> tuple[str, int] | None:
        """The group naming `f` outright: a one_of member, a literal group, a held entry."""
        if f in self.claimed:
            return self.claimed[f], self.cap_of(self.claimed[f])
        if f in self.reg["groups"]:
            return f, self.cap_of(f)
        if f in self.held:
            return f, self.held[f]
        return None

    def data_of(self, f: str) -> str | None:
        """The live data entry covering `f`, or None; an index file is never data."""
        if PurePosixPath(f).name in INDEX_NAMES:
            return None
        return next((n for n, p in self.data if covering(p, f)), None)

    def by_class(self, f: str) -> tuple[str, int]:
        """Where `f` falls with nothing naming it: its derived class, each file
        its own group; else the longest path group -- a literal over a
        placeholder on a tie; else the residual."""
        cls = derived_class(f)
        if cls in self.derived_groups:
            return f, self.cap_of(self.derived_groups[cls])
        hits = [(len(pre), placeholder(n) is None, pre, n)
                for n in self.paths if (pre := covering(n, f))]
        if not hits:
            return self.residual, self.cap_of(self.residual)
        _, _, pre, n = max(hits)
        return (f if self.reg["groups"][n].get("per_file") else pre), self.cap_of(n)

    def class_cap(self, f: str) -> int:
        return self.by_class(f)[1]

    def place(self, f: str) -> tuple[str, str, int]:
        """("group" | "data", name, cap) for a tracked file, first match wins."""
        named = self.named(f)
        if named:
            return "group", *named
        data = self.data_of(f)
        if data:
            return "data", data, 0
        return "group", *self.by_class(f)


@dataclass
class Report:
    counted: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
    caps: dict[str, int] = field(default_factory=dict)
    detail: defaultdict[str, list[tuple[int, str, str]]] = field(default_factory=lambda: defaultdict(list))
    data: defaultdict[str, list[tuple[int, str]]] = field(default_factory=lambda: defaultdict(list))
    droppable: list[tuple[str, int, int]] = field(default_factory=list)


def measure(root: Path, res: Resolver, count: Callable[[str], int]) -> Report:
    """Every tracked file counted into its group, one_of sets paying their
    largest member, descriptions counted as a field on top."""
    rep = Report()
    groups = res.reg["groups"]
    for name, g in groups.items():
        if not (g.get("per_file") or placeholder(name) or g.get("derived")):
            rep.caps[name] = res.cap_of(name)
    slot_size: dict[str, dict[str, int]] = defaultdict(dict)
    desc = res.derived_groups.get("descriptions")
    for f in res.files:
        text = (root / f).read_text(encoding="utf-8", errors="replace")
        tokens = count(text)
        kind, name, cap = res.place(f)
        if kind == "data":
            rep.data[name].append((tokens, f))
        elif name in res.slots:
            slot_size[name][f] = tokens
        else:
            rep.caps[name] = cap
            rep.counted[name] += tokens
            rep.detail[name].append((tokens, f, ""))
        if f in res.held:
            class_cap = res.class_cap(f)
            if tokens <= class_cap:
                rep.droppable.append((f, tokens, class_cap))
        if desc and derived_class(f) in ("skill-bodies", "agent-bodies"):
            dn = count(frontmatter(text).get("description", ""))
            rep.counted[desc] += dn
            rep.detail[desc].append((dn, f, ""))
    if desc:
        rep.caps[desc] = res.cap_of(desc)
    for g, sizes in slot_size.items():
        top = max(sizes.values())
        rep.counted[g] += top
        members = ", ".join(f"{res.slots[g][f]} {tokens:,}"
                            for f, tokens in sorted(sizes.items(), key=lambda t: -t[1]))
        rep.detail[g].append((top, groups[g]["one_of"], f"largest of {members}"))
    return rep


def display_order(res: Resolver, rep: Report) -> list[tuple[str, str]]:
    """(group, label) rows in registry order. A derived, per_file or placeholder
    group stands for its members, listed at its position under its `loaded`
    label; a literal or held file shows under the class it belongs to."""
    groups = res.reg["groups"]
    parents = {n for n, g in groups.items()
               if g.get("derived") in FILE_CLASSES or g.get("per_file") or placeholder(n)}

    def parent_of(name: str) -> str | None:
        if name in res.file_set and (cls := derived_class(name)) in res.derived_groups:
            return res.derived_groups[cls]
        hits = [(len(m), m) for m in parents
                if not groups[m].get("derived") and covers_dir(m, name)]
        return max(hits)[1] if hits else None

    children: dict[str | None, list[str]] = defaultdict(list)
    for name in set(rep.caps) | parents:
        children[parent_of(name)].append(name)

    rows: list[tuple[str, str]] = []
    seen: set[str] = set()

    def emit(name: str, label: str) -> None:
        if name in seen:
            return
        seen.add(name)
        if name in rep.caps:
            rows.append((name, label))
        for child in sorted(children.get(name, [])):
            emit(child, label)

    for name in groups:
        if name not in seen and parent_of(name) is None:
            emit(name, groups[name].get("loaded", "(no `loaded` label)"))
    # Every row's parent chain ends at a registry group, so nothing lands here; a row
    # silently missing from the report would be worse than a stray label.
    for name in sorted(set(rep.caps) - seen):
        emit(name, "(unplaced)")
    return rows


def render(res: Resolver, rep: Report, rows: list[tuple[str, str]], detail_all: bool,
           print_held: bool) -> tuple[str, list[str]]:
    """The report text and the names of the groups over cap."""
    cut_to: float = res.reg["cut_to"]
    pct = f"{cut_to:.0%}"
    over: list[tuple[str, int, int, int]] = []
    lines: list[str] = []
    if print_held:
        for name, _ in rows:
            c, cap = rep.counted[name], rep.caps[name]
            if c > cap:
                over.append((name, c, cap, int(cap * cut_to)))
        for name, c, _, _ in sorted(over, key=lambda t: -t[1]):
            if name in res.file_set:
                lines.append(f'"{name}" = {c}')
            else:
                lines.append(f"# not a file, give it a group cap with `approved`: {name} {c:,}")
        return "".join(line + "\n" for line in lines), [t[0] for t in over]

    width = max((len(name) for name, _ in rows), default=5)
    lines.append(f"{'counted':>9} {'cap':>7} {pct:>7}  group")
    label_shown: str | None = None
    for name, label in rows:
        if label != label_shown:
            lines.append(f"-- {label}")
            label_shown = label
        c, cap = rep.counted[name], rep.caps[name]
        target = int(cap * cut_to)
        if c > cap:
            state = f"OVER by {c - cap:,}"
            over.append((name, c, cap, target))
        elif c > target:
            state = f"above {pct} by {c - target:,}"
        else:
            state = "ok"
        lines.append(f"{c:9,d} {cap:7,d} {target:7,d}  {name:<{width}} {state}")
        for tokens, f, note in sorted(rep.detail[name], reverse=True):
            # A note says how the count was arrived at -- a one_of set paying its
            # largest member -- so it shows whether or not the group is over cap.
            if f != name and (note or c > cap or detail_all):
                lines.append(f"{tokens:9,d}{'':20}{f}" + (f"  ({note})" if note else ""))

    if rep.data:
        lines.append("")
        lines.append("data, listed and not counted:")
        for dn, d in res.reg["data"].items():
            members = rep.data.get(dn, [])
            total = sum(tokens for tokens, _ in members)
            lines.append(f"{len(members):5d} files {total:10,d}  {dn}: {', '.join(d['paths'])}")

    if rep.droppable:
        lines.append("")
        lines.append("held entries now within their class cap -- drop them from [held.files]:")
        for f, tokens, cap in sorted(rep.droppable):
            lines.append(f"  {f} {tokens:,} <= {cap:,}")

    for name, c, cap, target in over:
        lines.append(f"\n{name} is {c:,} against {cap:,}. Cut to {target:,} -- see "
                     "conventions/documentation.md, *Documentation budget*.")
    return "".join(line + "\n" for line in lines), [t[0] for t in over]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="doc-budget",
        description=(
            "Every tracked .md against the caps in doc-budget.toml. Groups follow "
            "how a file reaches a context; the registry's header states the grammar."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--print-held", action="store_true",
                   help="Instead of the report, emit a [held.files] line for every "
                        "over-cap file, at its size. Exits 1 like the report whenever "
                        "a group is over cap.")
    p.add_argument("paths", nargs="*",
                   help="Narrow the report to the groups under these paths, with "
                        "per-file detail; `.` names every group.")
    return p


def main(argv: list[str] | None = None, *, root: Path = ROOT,
         count: Callable[[str], int] | None = None,
         environ: Mapping[str, str] | None = None) -> int:
    """Exit 0 within budget, 1 with a group over cap, 2 on a registry error; a path
    naming no group is a usage error, SystemExit(2) from argparse."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    environ = os.environ if environ is None else environ
    session = session_of(environ)
    if not session:
        print("warning: CLAUDE_CODE_SESSION_ID unset, so the same-session gate is "
              "inactive and every approval counts as live", file=sys.stderr)
    try:
        reg = load_registry(root / REGISTRY)
        res = Resolver(reg, tracked_md(root), session)
    except RegistryError as exc:
        print(f"{REGISTRY}: {exc}", file=sys.stderr)
        return 2

    want: list[str] = []
    for a in args.paths:
        try:
            rel = Path(a).resolve().relative_to(root.resolve())
        except ValueError:
            parser.error(f"{a} is outside {root}")
        want.append("" if str(rel) == "." else rel.as_posix())

    if count is None:
        from claude_config.count_tokens import count_with, load_tokenizer

        count = partial(count_with, load_tokenizer())

    rep = measure(root, res, count)
    rows = display_order(res, rep)
    shown = [(n, label) for n, label in rows
             if not want or any(w == "" or n == w or n.startswith(w + "/") for w in want)]
    if want and not shown:
        parser.error(f"no group is named under {', '.join(want)}: group names are in "
                     f"{REGISTRY}, and derived, one_of and residual groups are not paths")
    text, over = render(res, rep, shown, detail_all=bool(want), print_held=args.print_held)
    sys.stdout.write(text)
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the synthetic tests**

Run: `PYTEST tests/test_doc_budget.py -q --deselect tests/test_doc_budget.py::test_the_registry_is_valid_and_the_tree_is_within_budget 2>&1 | tail -15`
Expected: 38 passed, 1 deselected. Fix the module, not the tests, for any failure.

The tree test fails until Task 3 writes the registry; that is expected here.

- [ ] **Step 5: Commit**

```bash
git add src/claude_config/doc_budget.py tests/test_doc_budget.py
git commit -q -F - <<'EOF'
doc-budget: the resolver, report and exit codes, with the grammar under test

Claude-Session: 834203fa-2993-42e8-a373-0f7dc84e995e
EOF
```

---

### Task 3: The registry, without the held table

**Files:**
- Create: `doc-budget.toml`

- [ ] **Step 1: Write the registry**

Create `doc-budget.toml` at the repo root:

```toml
# Doc budget: token caps for every tracked `.md`, grouped by how the text
# reaches a context.  Design: docs/superpowers/specs/2026-09-29-doc-budget-design.md
# Policy: conventions/documentation.md, "Documentation budget".
# Measure: agent-tools doc-budget [--print-held] [path ...]
#
# Unit: local-tokenizer tokens (`agent-tools count-tokens` without `--api`),
# the backend that runs offline, in CI and in worktrees.  Claude context is
# about 1.5x this on prose; the backends never reconcile.
#
# A file's group, first match wins: a group named with its path ([held.files]
# included); a [data] path covering it -- listed, never counted, except that a
# README.md or CLAUDE.md counts wherever it is; its derived class; the longest
# path group, a literal name over a placeholder on a tie; the residual.
# `one_of` claims its files ahead of all of this and pays the largest member.
# `per_file` makes each file its own group at the group's cap; `<name>` stands
# for one path segment and makes each match its own group.  `cap` falls back
# to `default_cap`.
#
# Over cap, cut that group to 80% of cap in the same change.  Loosening -- a
# [data] entry, the [held] table, a cap above the default or above the class
# cap -- carries `approved`: `<8 hex of session id>` is an agent's own session
# and inert there; `user:<8 hex>` is the session in which the user approved it
# and live at once.  `agent-tools cc-pretty <8 hex> --skeleton` opens either.
# Class caps and `default_cap` are policy the user edits.

cut_to = 0.8
default_cap = 15000

# -- every request ----------------------------------------------------------

[groups."sys_prompt/alan-default-next.md"]
loaded = "every request, every project"
cap = 4400

# One opencode agent body is loaded per session; the set pays its largest.
[groups.opencode-prompt]
loaded = "every request of an opencode session"
one_of = "opencode/agents/<agent>.md"
cap = 5200

# -- every session ----------------------------------------------------------

# The `description:` of every skill and agent, which the skills listing carries
# into every session; counted here and again inside its file.
[groups.descriptions]
loaded = "every session, every project"
derived = "descriptions"
cap = 1200

# -- per invocation, per spawn ---------------------------------------------

# skills/<n>/SKILL.md and .claude/skills/<n>/SKILL.md, each its own group.
[groups.skill-bodies]
loaded = "per invocation"
derived = "skill-bodies"
cap = 3000

# Reached 7,316 tokens unmeasured; held under its own cap since.
[groups."skills/telegram-hitl/SKILL.md"]
cap = 1000

# agents/*.md, each its own group.
[groups.agent-bodies]
loaded = "per spawn"
derived = "agent-bodies"
cap = 3000

# Agent bodies tell their agent to read these, so the set is spent per spawn.
# [user:834203fa]
[groups.conventions]
loaded = "per spawn (agent bodies read them)"
cap = 25000
approved = "user:834203fa"

# -- every session touching the directory -----------------------------------

# Every CLAUDE.md, each its own group.
[groups.claude-md]
loaded = "every session touching the directory"
derived = "claude-md"
cap = 1500

# -- on demand, one file at a time ------------------------------------------

[groups.docs]
loaded = "on demand, one file at a time"
per_file = true
cap = 5000

[groups.notes]
loaded = "on demand, one file at a time"
per_file = true
cap = 4000

[groups."docs/superpowers/specs"]
loaded = "on demand, one file at a time"
per_file = true
cap = 4000

[groups.plans]
loaded = "on demand, one file at a time"
per_file = true
cap = 1000

# -- on demand, a directory at a time ---------------------------------------

# Each skill's own docs, references and resources; its SKILL.md is a skill
# body and its CLAUDE.md a claude-md.
[groups."skills/<name>"]
loaded = "on demand, when the skill is invoked"

[groups."skills/prompt-engineer/references"]
loaded = "on demand, one file at a time"
per_file = true
cap = 10000

# INTENT.md is the skill's 11k design spec, read whole. [user:834203fa]
[groups."skills/planner"]
cap = 17808
approved = "user:834203fa"

[groups.scripts]
loaded = "on demand"

[groups.prompt-tests]
loaded = "on demand"

[groups.sys_prompt]
loaded = "on demand"

# settings.json has had `outputStyle: default` since cbeb6721, so nothing here
# is loaded; the cap keeps the directory from growing unnoticed.
[groups.output-styles]
loaded = "not loaded since cbeb6721 (outputStyle: default)"
cap = 11000

# Everything else: root README.md, skills/README.md, .github/.  Residual, so a
# new directory lands here and shows as infra debt, not nowhere.
[groups.infra]
loaded = "on demand"
residual = true
cap = 12000

# -- data: listed in every report, never counted ----------------------------

[data.snapshots]
paths = ["docs/system-prompt-snapshot/<model>"]
approved = "user:834203fa"
why = "Regenerated captures of Claude Code's own prompt and skills; a cap cannot shrink what a capture returns."

[data.papers]
paths = ["skills/prompt-engineer/papers"]
approved = "user:834203fa"
why = "Papers converted by arxiv-to-md, read for their content; not guidance."

[data.samples]
paths = ["skills/alan-writing-style/samples"]
approved = "user:834203fa"
why = "Writing-style regression cases: the data the skill's checks run against."

[data.vendored]
paths = ["skills/playwright-cli"]
approved = "user:834203fa"
why = "Written by `playwright-cli install --skills`; never edited by hand."

[data.fixtures]
paths = ["prompt-tests/general/<case>/fixture", "prompt-tests/runs"]
approved = "user:834203fa"
why = "Fixture trees and captured runs loaded into prompt-test sessions, not into this repo's."

[data.closed-investigations]
paths = ["notes/compliance-check-failure-mode", "notes/ralph-loop3-writing-for-agents", "docs/prompt-trials"]
approved = "user:834203fa"
why = "Closed evidence sets and audit archives: dated, never rewritten, not read for guidance."

[data.plans]
paths = ["docs/superpowers/plans"]
approved = "user:834203fa"
why = "The writing-plans format carries complete code per step and does not fit a cap; each plan is read once, by its executor."

[data.transcripts]
paths = ["skills/prompt-engineer-v2/test-requests.md"]
approved = "user:834203fa"
why = "A transcript of test requests, kept verbatim."
```

- [ ] **Step 2: Run the tool against the tree**

Run: `cd /root/claude-config-work && UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config-work uv run python -m claude_config.doc_budget 2>&1 | tail -60`
Expected: exit 1 with a report; over-cap rows are the files the spec lists as held (`agent-tools/CLAUDE.md`, the seven skill bodies, the two agent bodies, five docs, seven notes, six specs, nineteen plans, `docs/system-prompt-snapshot/README.md`, …) and nothing else. `skills/planner` must not be OVER (17,808 against 17,808 reads `above 80% by 3,562`) and `conventions`, `descriptions`, `sys_prompt/alan-default-next.md`, `opencode-prompt`, `infra` must not be over. If a group other than a single file is over — a directory group — stop and report it rather than raising its cap.

Run: `... python -m claude_config.doc_budget --print-held | head -5`
Expected: lines like `"docs/system-prompt-snapshot/README.md" = 19757`, and no `# not a file` line.

- [ ] **Step 3: Commit**

```bash
git add doc-budget.toml
git commit -q -F - <<'EOF'
doc-budget: the registry, classes by load mechanism, data declared

Claude-Session: 834203fa-2993-42e8-a373-0f7dc84e995e
EOF
```

---

### Task 4: `agent-tools doc-budget`

**Files:**
- Modify: `agent-tools/src/main.rs:230-235` (enum) and `:813-820` (dispatch)
- Create: `agent-tools/tests/doc_budget_test.rs`

- [ ] **Step 1: Write the failing tests**

Create `agent-tools/tests/doc_budget_test.rs`:

```rust
use std::path::PathBuf;
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

/// Worktree root = parent of agent-tools/ (which is CARGO_MANIFEST_DIR).
fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

fn doc_budget(args: &[&str]) -> std::process::Output {
    Command::new(bin())
        .arg("doc-budget")
        .args(args)
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("failed to run agent-tools doc-budget")
}

#[test]
fn doc_budget_help_is_forwarded_to_python() {
    let out = doc_budget(&["--help"]);
    assert!(
        out.status.success(),
        "exit={:?} stderr={}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("--print-held"), "stdout missing --print-held: {stdout}");
    // Only the Python parser's epilog carries the exit-status table; clap's
    // help would list the flag from the doc comment and stop there.
    assert!(
        stdout.contains("exit status:"),
        "--help was answered by clap, not forwarded to Python: {stdout}"
    );
}

#[test]
fn doc_budget_forwards_the_modules_exit_code_and_stderr() {
    // A path that names no group is the module's own usage error: exit 2 with
    // its wording, which clap could not have produced.
    let out = doc_budget(&["nothing-here-xyz"]);
    assert_eq!(out.status.code(), Some(2), "stdout={}", String::from_utf8_lossy(&out.stdout));
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("no group is named under"),
        "expected the module's usage error, got: {stderr}"
    );
}
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd /root/claude-config-work/agent-tools && cargo test --test doc_budget_test 2>&1 | tail -8`
Expected: both FAIL (clap: `unrecognized subcommand 'doc-budget'`).

- [ ] **Step 3: Add the subcommand**

In `agent-tools/src/main.rs`, directly after the `CountTokens { ... },` variant (ends at the line `},` following `args: Vec<String>,` under `#[command(name = "count-tokens", disable_help_flag = true)]`), add:

```rust
    /// Every tracked .md against the caps in doc-budget.toml:
    /// agent-tools doc-budget [--print-held] [path ...]
    ///
    /// `disable_help_flag` for the same reason as count-tokens: the Python
    /// help carries the exit-status table and the unit a person needs.
    #[command(name = "doc-budget", disable_help_flag = true)]
    DocBudget {
        /// Arguments forwarded to claude_config.doc_budget
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
```

Directly after the `Cmd::CountTokens { args } => { uv_run(...); }` arm in the dispatch `match`, add:

```rust
            Cmd::DocBudget { args } => {
                uv_run(
                    &root,
                    None,
                    &["python3", "-m", "claude_config.doc_budget"],
                    &args,
                );
            }
```

- [ ] **Step 4: Build and run the tests**

Run: `cd /root/claude-config-work/agent-tools && cargo build --release 2>&1 | tail -2 && cargo test --test doc_budget_test 2>&1 | tail -5`
Expected: build ok; `test result: ok. 2 passed`.

Run: `cd /root/claude-config-work && agent-tools/target/release/agent-tools doc-budget --print-held | wc -l`
Expected: a count near 51 (the held files). Note: the installed `agent-tools` in `~/.local/bin` is the canonical checkout's build and does not know `doc-budget`; use the worktree's binary path above throughout this plan.

- [ ] **Step 5: Commit**

```bash
git add agent-tools/src/main.rs agent-tools/tests/doc_budget_test.rs
git commit -q -F - <<'EOF'
doc-budget: agent-tools subcommand, help and exit code forwarded

Claude-Session: 834203fa-2993-42e8-a373-0f7dc84e995e
EOF
```

---

### Task 5: Move the telegram pin into the registry

**Files:**
- Modify: `tests/test_telegram_hitl_skill.py` (the import at line 14 and the last test)
- Modify: `skills/CLAUDE.md:56`, `README.md:198-199`

- [ ] **Step 1: Remove the pytest pin**

In `tests/test_telegram_hitl_skill.py`: delete the line `from claude_config.count_tokens import _count_local` (and the blank line after it, keeping one blank line between the `import pytest` block and `SKILL_DIR = ...`), and delete the whole function `test_the_skill_stays_inside_its_token_budget` at the end of the file, including its docstring and the two blank lines before it.

- [ ] **Step 2: Repoint the two mentions**

`skills/CLAUDE.md` line 56: replace `held under a 1000-token budget that `tests/test_telegram_hitl_skill.py` pins` with `held under a 1,000-token cap in `doc-budget.toml``.

`README.md` lines 198–199: replace
```
[the tests](tests/test_telegram_hitl_skill.py) execute that script and pin the
skill's token budget.
```
with
```
[the tests](tests/test_telegram_hitl_skill.py) execute that script;
`doc-budget.toml` caps the skill at 1,000 tokens.
```

- [ ] **Step 3: Run the telegram skill tests**

Run: `PYTEST tests/test_telegram_hitl_skill.py -q 2>&1 | tail -2`
Expected: PASS, one fewer test than before (`grep -c "^def test_" tests/test_telegram_hitl_skill.py` prints 14).

Run: `grep -rn "test_telegram_hitl_skill.py\` pins\|pin the$" skills/CLAUDE.md README.md`
Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add tests/test_telegram_hitl_skill.py skills/CLAUDE.md README.md
git commit -q -F - <<'EOF'
doc-budget: the telegram skill's cap lives in the registry

Claude-Session: 834203fa-2993-42e8-a373-0f7dc84e995e
EOF
```

---

### Task 6: Pins on hook stdout

**Files:**
- Modify: `tests/test_env_context.py` (append), `tests/test_pre_output_record.py` (append under `# --- recording`), `agent-tools/src/hook_subagent.rs` (`mod tests`)

- [ ] **Step 1: Write the three pins**

Append to `tests/test_env_context.py`:

```python
def test_the_block_stays_inside_its_token_budget(tmp_path: Path) -> None:
    """The block is spent once per session in every project. `doc-budget.toml`
    prices the `.md` tree; hook stdout is not `.md`, so it is pinned beside its
    renderer. Rendered with a real git snapshot -- branch, status and five
    commits -- because that section is most of the block. 615 tokens on this
    repo when pinned; counted by the local tokenizer."""
    from claude_config.count_tokens import _count_local

    repo = tmp_path / "repo"
    _init_repo(repo)
    for i in range(5):
        (repo / f"f{i}.txt").write_text("x")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m",
                        f"a commit subject of ordinary length number {i}"], cwd=repo, check=True)
    (repo / "dirty.txt").write_text("y")
    text = render.sections(_facts(
        worktree_common_dir="/repos/claude-config/.git",
        drift_note=None,
        git_snapshot=environment.git_snapshot(str(repo)),
    ))
    assert _count_local(text) <= 700
```

Append to `tests/test_pre_output_record.py` after `test_the_reminder_prints_even_when_nothing_is_recorded`:

```python
def test_the_reminder_stays_inside_its_token_budget(session, capsys):
    """Printed on the last command of every turn. `doc-budget.toml` prices
    the `.md` tree; this is not `.md`, so it is pinned here: 42 tokens when
    pinned, by the local tokenizer."""
    from claude_config.count_tokens import _count_local

    record.main([json.dumps(PAYLOAD)])
    assert _count_local(capsys.readouterr().out) <= 60
```

In `agent-tools/src/hook_subagent.rs`, inside `mod tests` after `asks_for_the_heading_the_parent_looks_for`, add:

```rust
    /// Spent once per subagent spawn. `doc-budget.toml` prices the `.md`
    /// tree; this block is not `.md`, so it is pinned here -- in characters,
    /// since the Rust suite has no tokenizer. 856 when pinned.
    #[test]
    fn the_ask_stays_inside_its_size_budget() {
        assert!(additional_context().chars().count() <= 1000);
    }
```

- [ ] **Step 2: Run the three suites**

Run: `PYTEST tests/test_env_context.py tests/test_pre_output_record.py -q -k budget 2>&1 | tail -2`
Expected: 2 passed.

Run: `cd /root/claude-config-work/agent-tools && cargo test hook_subagent 2>&1 | grep 'test result' | head -1`
Expected: ok, 5 passed in that module.

- [ ] **Step 3: Commit**

```bash
git add tests/test_env_context.py tests/test_pre_output_record.py agent-tools/src/hook_subagent.rs
git commit -q -F - <<'EOF'
doc-budget: pin the three hook blocks beside their renderers

Claude-Session: 834203fa-2993-42e8-a373-0f7dc84e995e
EOF
```

---

### Task 7: The policy text

**Files:**
- Modify: `conventions/documentation.md` (new section before `## CLAUDE.md Format Specification`)

- [ ] **Step 1: Add the section**

Insert before the line `## CLAUDE.md Format Specification` in `conventions/documentation.md`:

```markdown
## Documentation budget

Prose that is always present is always paid for. Every tracked `.md` counts
against a group in `doc-budget.toml`, grouped by how its text reaches a
context — every request, every session, per invocation, per spawn, on demand —
unless a `[data]` entry there declares it not guidance; design in
`docs/superpowers/specs/2026-09-29-doc-budget-design.md`. Measure with
`agent-tools doc-budget [path]`: local-tokenizer tokens, not `--api`.

**Over cap, cut that group to 80% of cap in the same change** — the agent that
crossed the line pays. A group already over when you arrived is debt: say so,
and pay it when the task is about its docs rather than in passing.

Only consolidation satisfies the cap: merge duplicates, resolve the conflicts
you find, delete what the code already says. Moving prose out of `.md` (into a
comment, JSON, a script's `--help`) is not a cut. Neither is loosening the
registry: a `[data]` entry, a held size or a cap above the default needs the
user's approval, and one an agent approves cannot take effect in the session
that wrote it.

What survives is non-rederivable and changes an action — the test is whether
not knowing it makes an agent do the wrong thing. Everything else goes,
including good writing — git history keeps it.

```

- [ ] **Step 2: Check the conventions group**

Run: `cd /root/claude-config-work && agent-tools/target/release/agent-tools doc-budget conventions | head -3`
Expected: `conventions` row, counted ≈ 24,0xx against 25,000, not OVER.

- [ ] **Step 3: Commit**

```bash
git add conventions/documentation.md
git commit -q -F - <<'EOF'
doc-budget: the policy, in the conventions every CLAUDE.md follows

Claude-Session: 834203fa-2993-42e8-a373-0f7dc84e995e
EOF
```

---

### Task 8: Root `CLAUDE.md` — row, command, policy pointer, kept under its cap

Root `CLAUDE.md` is 1,444 tokens against the `claude-md` cap of 1,500. The three additions below are ~110 tokens, so two rows are consolidated against text that already lives elsewhere; the file must end ≤ 1,500 and is not held.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add the row, the command and the policy bullet**

In the Files table, after the `.env` / `.env.example` row, add:

```
| `doc-budget.toml` | Token caps for every tracked `.md`, by how the text reaches a context; `agent-tools doc-budget` measures | Adding or growing a doc; a group over cap |
```

In `## Build and test`, after the `scripts/check-prompt-rationale.sh` line, add:

```
agent-tools doc-budget                   # every tracked .md against doc-budget.toml
```

In `## Agent Policy`, append the bullet:

```
- `agent-tools doc-budget` over cap: cut that group to 80% in the same change —
  consolidation only; a group over when you arrived is debt to name, not pay in passing
  (`conventions/documentation.md`, *Documentation budget*).
```

- [ ] **Step 2: Consolidate two rows against their other homes**

Replace the `install.sh` row's What cell (README's *Install* section carries the same list) with:

```
Symlinks the config into `~/.claude/`, `~/.config/opencode`, `~/.config/systemd/user/` and `~/.local/bin/` — README, *Install*. Links, not copies: a canonical-checkout edit is live with no re-install, a worktree's is live nowhere; refuses a worktree, or a destination that is not already a symlink
```

Replace the `notes/` row's What cell (the archive's own `CLAUDE.md` carries its rules) with:

```
Long-form investigation write-ups — measured evidence and root cause, one behaviour each. Dated records, never rewritten to match later changes; `ralph-loop3-writing-for-agents/` is a closed archive with rules in its own `CLAUDE.md`
```

- [ ] **Step 3: Measure**

Run: `cd /root/claude-config-work && agent-tools/target/release/agent-tools doc-budget CLAUDE.md`
Expected: `CLAUDE.md` ≤ 1,500, state `above 80% by …` (not OVER). If OVER, also drop `(post-upgrade runbook and what a release can break here)` from the `.claude/` row — the Agent Policy bullet already says it — and re-measure; if still OVER, shorten the new bullet to `- \`agent-tools doc-budget\` over cap: cut that group to 80% in the same change (\`conventions/documentation.md\`, *Documentation budget*).` Do not add `CLAUDE.md` to `[held.files]`.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -q -F - <<'EOF'
doc-budget: root index names the registry, the command and the rule

Claude-Session: 834203fa-2993-42e8-a373-0f7dc84e995e
EOF
```

---

### Task 9: The remaining index rows

**Files:**
- Modify: `agent-tools/CLAUDE.md` (bullet after the count-tokens re-vendoring paragraph, before `- \`agent-tools env-context\``)
- Modify: `src/claude_config/CLAUDE.md` (row after `count_tokens.py`)
- Modify: `sys_prompt/CLAUDE.md:33-37`
- Modify: `.claude/skills/update-claude-code/SKILL.md` (§3.1 table, after the `skills/telegram-hitl/SKILL.md:30` row)
- Modify: `docs/CLAUDE.md:28`

- [ ] **Step 1: `agent-tools/CLAUDE.md`**

Insert, as a new bullet immediately before the line beginning `- \`agent-tools env-context\``:

```
- `agent-tools doc-budget [--print-held] [path ...]` — every tracked `.md` against the caps in `doc-budget.toml` (wraps `python3 -m claude_config.doc_budget`). Groups follow the mechanism that loads a file, not its directory: the system prompt, the opencode agent set, the skill and agent `description:` fields, each `SKILL.md`, each agent body, each `CLAUDE.md`, and per-file caps under `docs/`, `notes/`, `plans/`; `[data]` paths are listed at the bottom and never counted. Exit 1 over cap, 2 on a registry error; `--print-held` emits a `[held.files]` line for every over-cap file. Counts with the local tokenizer, loaded once (`count_tokens.load_tokenizer`); `--help` is forwarded to Python like `count-tokens`. Policy in `conventions/documentation.md`, design in `docs/superpowers/specs/2026-09-29-doc-budget-design.md`.
```

- [ ] **Step 2: `src/claude_config/CLAUDE.md`**

Insert after the `count_tokens.py` row:

```
| `doc_budget.py`                     | Every tracked `.md` against the caps in `doc-budget.toml`: the resolver (which group a file counts in), the report, `--print-held`, and the same-session approval gate, which reads `CLAUDE_CODE_SESSION_ID` and, unset, warns and treats every approval as live | `agent-tools doc-budget`        |
```

- [ ] **Step 3: `sys_prompt/CLAUDE.md`**

Replace

````
Measure before and after:

```bash
agent-tools count-tokens --api --file sys_prompt/alan-default-next.md
```
````

with

````
Measure before and after. `doc-budget.toml` caps the prompt at 4,400 local tokens
(`agent-tools doc-budget sys_prompt/alan-default-next.md`); `--api` is the figure for
context consumed:

```bash
agent-tools count-tokens --api --file sys_prompt/alan-default-next.md
```
````

- [ ] **Step 4: `.claude/skills/update-claude-code/SKILL.md`**

Insert after the §3.1 row that begins `| \`skills/telegram-hitl/SKILL.md:30\``:

```
| `src/claude_config/doc_budget.py` (`session_of`) | `CLAUDE_CODE_SESSION_ID` | The same-session gate on `approved`: an entry the running session approved is inert there. A renamed variable reads as unset, so the gate goes inert everywhere — every approval counts as live and an agent's own `[data]` entry or held size takes effect in the session that wrote it — with a warning on stderr on every run, which nothing automatic reads: `tests/test_doc_budget.py` passes the variable in itself. |
```

- [ ] **Step 5: `docs/CLAUDE.md`**

Replace `` `plans/` (14) `` with `` `plans/` (15) `` on line 28 (this plan is the fifteenth).

- [ ] **Step 6: Check the guards and the affected groups**

Run: `cd /root/claude-config-work && scripts/check-prompt-rationale.sh && scripts/check-prompt-coupling.sh 2>&1 | tail -2`
Expected: both pass (the sys_prompt edit is outside the rationale region).

Run: `agent-tools/target/release/agent-tools doc-budget docs/CLAUDE.md skills/CLAUDE.md | grep -v '^--'`
Expected: both ≤ 1,500.

- [ ] **Step 7: Commit**

```bash
git add agent-tools/CLAUDE.md src/claude_config/CLAUDE.md sys_prompt/CLAUDE.md .claude/skills/update-claude-code/SKILL.md docs/CLAUDE.md
git commit -q -F - <<'EOF'
doc-budget: index rows for the subcommand, the module, the prompt's cap

Claude-Session: 834203fa-2993-42e8-a373-0f7dc84e995e
EOF
```

---

### Task 10: Freeze the held table and turn the gate green

Every doc edit is committed, so the tree is the introducing baseline: the held sizes are the sizes now.

**Files:**
- Modify: `doc-budget.toml` (append `[held]`)

- [ ] **Step 1: Generate the held table**

Run:

```bash
cd /root/claude-config-work
agent-tools/target/release/agent-tools doc-budget --print-held > /root/.claude/tmp/claude-0/-root-claude-config-work/834203fa-2993-42e8-a373-0f7dc84e995e/scratchpad/held.txt
grep -c '^"' /root/.claude/tmp/claude-0/-root-claude-config-work/834203fa-2993-42e8-a373-0f7dc84e995e/scratchpad/held.txt
grep '^#' /root/.claude/tmp/claude-0/-root-claude-config-work/834203fa-2993-42e8-a373-0f7dc84e995e/scratchpad/held.txt
```

Expected: about 51 lines; the second grep prints nothing (no directory group is over). If it prints a group, stop and report — a directory group over cap is not held, and its cap is the user's call.

- [ ] **Step 2: Append it**

Append to `doc-budget.toml`:

```toml

# -- held: every file over its class cap when the registry was introduced ---
#
# At the size it had then, so CI is green on day one; the first addition to
# any of these pays the 20% cut like any other over-cap group.  The report
# names an entry whose file has fallen under its class cap so it can be
# dropped.  [user:834203fa]
[held]
approved = "user:834203fa"
why = "Held at introduction, 2026-09-30; the first addition to any of these pays."

[held.files]
```

followed by the `"path" = n` lines from `held.txt`, in the order the tool printed them (largest first).

- [ ] **Step 3: The gate**

Run: `cd /root/claude-config-work && agent-tools/target/release/agent-tools doc-budget | tail -3; echo exit=$?`
Expected: no `OVER` anywhere, exit 0.

Run: `PYTEST tests/test_doc_budget.py -q 2>&1 | tail -2`
Expected: all PASS, the tree test included.

- [ ] **Step 4: Commit**

```bash
git add doc-budget.toml
git commit -q -F - <<'EOF'
doc-budget: hold every file over its class cap at its introduction size

Claude-Session: 834203fa-2993-42e8-a373-0f7dc84e995e
EOF
```

---

### Task 11: Whole-suite verification

- [ ] **Step 1: Run everything**

```bash
cd /root/claude-config-work
PYTEST -q 2>&1 | tail -3
(cd agent-tools && cargo test 2>&1 | grep -E 'test result|FAILED' | sort | uniq -c)
scripts/check-prompt-coupling.sh && scripts/check-prompt-rationale.sh
agent-tools/target/release/agent-tools doc-budget >/dev/null; echo doc-budget exit=$?
git status --short | wc -l
```

Expected: pytest all passed; every cargo `test result: ok`; both scripts pass; `doc-budget exit=0`; `0` uncommitted files.

- [ ] **Step 2: Spot-check the report by class**

Run: `agent-tools/target/release/agent-tools doc-budget | grep '^--'`
Expected: the headers in this order — every request (2 groups), every request of an opencode session, every session, per invocation, per spawn, per spawn (agent bodies read them), every session touching the directory, on demand (one file at a time; a directory at a time; when invoked), not loaded since cbeb6721, on demand (infra).

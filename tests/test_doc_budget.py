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


def test_a_generated_entry_takes_the_index_files_a_capture_wrote(tmp_path, capsys):
    """A capture's README.md is its payload: under a `generated` entry it is data,
    and that entry lists every file it covers even inside a broader plain entry,
    whose own index file still counts."""
    root = repo(tmp_path, {
        "snap/README.md": w(5),               # this repo's doc: counts
        "snap/body.md": w(3),                 # plain data
        "snap/bundle/a/README.md": w(500),    # captured: data
        "snap/bundle/a/CLAUDE.md": w(400),    # captured: data
        "snap/bundle/a/ref.md": w(7),         # captured: the nested entry's, by length
    }, BASE + """
[groups.snap]
loaded = "on demand"
cap = 10

[data.snapshots]
paths = ["snap"]
approved = "user:aaaaaaaa"
why = "captured"

[data.bundles]
paths = ["snap/bundle/<skill>"]
generated = true
approved = "user:aaaaaaaa"
why = "captured verbatim"
""")
    code, out, _ = run(root, capsys=capsys)
    assert code == 0, out
    assert row(5, 10, 8, "snap") in out
    assert f"{1:5d} files {3:10,d}  snapshots: snap" in out
    assert f"{3:5d} files {907:10,d}  bundles: snap/bundle/<skill>" in out


def test_a_generated_entry_may_cover_only_index_files(tmp_path, capsys):
    root = repo(tmp_path, {"cap/README.md": w(500), "k.md": w(1)}, BASE + """
[data.cap]
paths = ["cap"]
generated = true
approved = "user:aaaaaaaa"
why = "captured"
""")
    code, out, _ = run(root, capsys=capsys)
    assert code == 0, out
    assert f"{1:5d} files {500:10,d}  cap: cap" in out


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
    (BASE + "\n[groups.x]\nloaded = 'a'\ncap = 200\napproved = 'nobody'\n", "is not `<8 lower-case hex"),
    (BASE + "\n[groups.x]\nloaded = 'a'\ncap = 200\napproved = 'user:DEADBEEF'\n", "is not `<8 lower-case hex"),
    (BASE + "\n[data.d]\npaths = ['nowhere']\napproved = 'user:aaaaaaaa'\nwhy = 'w'\n", "covers no countable file"),
    (BASE + "\n[data.d]\npaths = ['i']\napproved = 'user:aaaaaaaa'\nwhy = 'w'\n",
     "covers no countable file (README.md and CLAUDE.md count wherever they are)"),
    (BASE + "\n[data.d]\npaths = ['nowhere']\ngenerated = true\napproved = 'user:aaaaaaaa'\nwhy = 'w'\n",
     "data 'd': 'nowhere' covers no tracked file"),
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
    (BASE + "\n[data.d]\npaths = ['x']\ngenerated = 'yes'\napproved = 'user:aaaaaaaa'\nwhy = 'w'\n",
     "`generated` must be true or false"),
    (BASE + "\n[groups.x]\nloaded = 'a'\ncap = 4\n[groups.\"x/a.md\"]\nloaded = 'a'\n", "inherits `default_cap` 100, above 4"),
    (BASE + "\n[groups.x]\nloaded = 'a'\none_of = 5\n", "must be a string carrying a <name> placeholder"),
    (BASE + "\n[groups.oc]\nloaded = 'a'\none_of = 'x/<n>.md'\n[held]\napproved = 'user:aaaaaaaa'\n"
     "[held.files]\n'x/a.md' = 200\n", "claimed by one_of group 'oc'"),
    ("cut_to = 0.8\ndefault_cap = 100\n[groups.infra]\nloaded = 'a'\nresidual = true\nper_file = true\n",
     "residual group 'infra': per_file is not allowed"),
    (BASE + "\n[groups.x]\nloaded = 'a'\ncap = 200\napproved = 12345678\n", "is not `<8 lower-case hex"),
])
def test_a_registry_error_exits_2_and_says_what(tmp_path, capsys, registry, message):
    root = repo(tmp_path, {"x/a.md": w(5), "i/README.md": w(5)}, registry)
    code, _, err = run(root, capsys=capsys)
    assert code == 2
    assert message in err, err


def test_a_path_counting_nothing_is_a_usage_error(tmp_path, capsys):
    root = repo(tmp_path, {"x/a.md": w(5)})
    with pytest.raises(SystemExit) as exit_:
        run(root, str(tmp_path / "nothing-here"), capsys=capsys)
    assert exit_.value.code == 2
    assert "nothing counted lies under nothing-here" in capsys.readouterr().err


def test_a_path_outside_the_root_is_refused_before_the_registry_is_read(tmp_path, capsys):
    root = repo(tmp_path, {"x/a.md": w(5)})
    (tmp_path / "doc-budget.toml").unlink()
    with pytest.raises(SystemExit) as exit_:
        run(root, "/etc", capsys=capsys)
    assert exit_.value.code == 2
    assert "is outside" in capsys.readouterr().err


def test_a_tracked_file_deleted_from_the_worktree_is_not_counted(tmp_path, capsys):
    """Deleted and not staged: the worktree is measured, so the deletion counts."""
    root = repo(tmp_path, {"x/a.md": w(5), "x/b.md": w(6)}, BASE + "\n[groups.x]\nloaded = 'a'\n")
    (tmp_path / "x" / "a.md").unlink()
    code, out, err = run(root, str(tmp_path / "x"), capsys=capsys)
    assert code == 0, err
    assert row(6, 100, 80, "x") in out
    assert "x/a.md" not in out


def test_a_root_that_is_not_a_git_checkout_exits_2(tmp_path, capsys):
    (tmp_path / "doc-budget.toml").write_text(BASE)
    code, _, err = run(tmp_path, capsys=capsys)
    assert code == 2
    assert "is not a git checkout" in err


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


def test_detail_lines_of_one_size_are_ordered_by_name(tmp_path, capsys):
    root = repo(tmp_path, {"x/b.md": w(60), "x/a.md": w(60)}, BASE + "\n[groups.x]\nloaded = 'a'\n")
    code, out, _ = run(root, capsys=capsys)
    assert code == 1
    assert out.index("x/a.md") < out.index("x/b.md"), out


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


def test_a_held_row_is_marked_held(tmp_path, capsys):
    """A frozen size is not a sanctioned one: the row says so where it is read."""
    root = repo(tmp_path, {"n/a.md": w(9), "n/b.md": w(3)}, BASE + """
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
    assert code == 0, out
    held = next((ln for ln in out.splitlines() if "n/a.md" in ln), "")
    plain = next(ln for ln in out.splitlines() if "n/b.md" in ln)
    assert held.endswith("above 80% by 2 (held)"), held
    assert "(held)" not in plain, plain


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


def test_a_named_file_narrows_to_the_group_that_counts_it(tmp_path, capsys):
    """The policy says to measure a path; the answer is the group paying for it,
    with every file it counts -- not a usage error because no group has that name."""
    root = repo(tmp_path, {"x/a.md": w(5), "x/b.md": w(6), "y/c.md": w(7)},
                BASE + "\n[groups.x]\nloaded = 'a'\n[groups.y]\nloaded = 'a'\n")
    code, out, _ = run(root, str(tmp_path / "x" / "a.md"), capsys=capsys)
    assert code == 0, out
    assert row(11, 100, 80, "x") in out
    assert f"{6:9,d}{'':20}x/b.md" in out
    assert "y/c.md" not in out and "  y " not in out


def test_a_subdirectory_narrows_to_its_covering_group_and_the_groups_under_it(tmp_path, capsys):
    root = repo(tmp_path, {"x/sub/a.md": w(5), "x/sub/CLAUDE.md": w(3), "y/c.md": w(7)}, BASE + """
[groups.claude-md]
loaded = "every session touching the directory"
derived = "claude-md"
cap = 10

[groups.x]
loaded = "on demand"

[groups.y]
loaded = "on demand"
""")
    code, out, _ = run(root, str(tmp_path / "x" / "sub"), capsys=capsys)
    assert code == 0, out
    assert row(5, 100, 80, "x") in out                  # counts x/sub/a.md
    assert row(3, 10, 8, "x/sub/CLAUDE.md") in out      # a group nested under the path
    assert "y/c.md" not in out and "  y " not in out


def test_a_one_of_member_narrows_to_the_set_that_pays_for_it(tmp_path, capsys):
    """A member is never a row of its own -- the set is -- so the path has to
    reach the set; the row's detail line is the pattern, not the member."""
    root = repo(tmp_path, {
        "oc/agents/big.md": w(9),
        "oc/agents/small.md": w(2),
        "k.md": w(1),
    }, BASE + """
[groups.oc-prompt]
loaded = "every request of an opencode session"
one_of = "oc/agents/<agent>.md"
cap = 10
""")
    code, out, _ = run(root, str(tmp_path / "oc" / "agents" / "small.md"), capsys=capsys)
    assert code == 0, out
    assert row(9, 10, 8, "oc-prompt") in out
    assert "(largest of big 9, small 2)" in out
    assert "  infra " not in out


def test_a_data_path_is_a_usage_error_saying_data_is_not_counted(tmp_path, capsys):
    root = repo(tmp_path, {"d/a.md": w(5), "k.md": w(1)}, BASE + """
[data.dump]
paths = ["d"]
approved = "user:aaaaaaaa"
why = "dump"
""")
    with pytest.raises(SystemExit) as exit_:
        run(root, str(tmp_path / "d"), capsys=capsys)
    assert exit_.value.code == 2
    assert "a [data] path is listed, not counted" in capsys.readouterr().err


def test_a_narrowed_report_leaves_out_the_data_table(tmp_path, capsys):
    """Data totals are context for the whole tree and noise beside one path."""
    root = repo(tmp_path, {"d/a.md": w(5), "x/b.md": w(1)}, BASE + """
[groups.x]
loaded = "on demand"

[data.dump]
paths = ["d"]
approved = "user:aaaaaaaa"
why = "dump"
""")
    code, out, _ = run(root, capsys=capsys)
    assert code == 0 and "data, listed and not counted:" in out
    code, out, _ = run(root, str(tmp_path / "x"), capsys=capsys)
    assert code == 0, out
    assert "data, listed and not counted:" not in out


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
    session that wrote it and passes in CI -- that is the gate working. A red
    gate shows stderr and the footer lines that name an over-cap group, so it
    reads as `X is N against M. Cut to T` rather than as the whole report."""
    code = doc_budget.main([], root=REPO)
    out, err = capsys.readouterr()
    over = [ln for ln in out.splitlines() if " against " in ln and "Cut to" in ln]
    assert code == 0, err + "\n".join(over)

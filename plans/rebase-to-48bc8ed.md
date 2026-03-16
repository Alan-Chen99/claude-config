# Rebase Plan: Reset to 48bc8ed, Backport Independent Work

## Background

Commit `53ce0e7` ("Large refactor") introduced bugs that broke all tests at HEAD (`832d7bb`).
The refactor touched 197 files (+27,890/−10,421 lines), restructured the planner into
decomposed modules, changed AST node types, and simplified StepDef from 7 fields to 3.

**Three bugs at HEAD (0 tests pass):**

| Bug | Root |
|-----|------|
| `ImportError: cannot import name 'ChoiceSet'` from types.py | `53ce0e7` removed ChoiceSet/Constant; tests still import them |
| `'str' object has no attribute '_module_path'` in 5 QR verify modules | `53ce0e7` set `WORKFLOW = "planner"` (string, not Workflow object) |
| `alan-coding-style` crash on `phase=` kwarg | `32a0e90` added code using old StepDef signature; `832d7bb` patched |

**Target: `48bc8ed`** ("Completely reorganize prompt engineer structures") — 167/167 tests pass.

## Decisions

| Item | Decision | Rationale |
|------|----------|-----------|
| Reset target | `48bc8ed` | Clean, 167 tests pass, most recent stable commit before refactor |
| planner_lite | Exclude | Uses new AST API; re-add after upstream fixes |
| alan-coding-style | Backport to old API | Valuable independent feature; W.el() pattern maps cleanly |
| Path patching (c597c3e) | Run `post-sync.sh` instead of cherry-pick | c597c3e touches files that won't exist at 48bc8ed; script is idempotent |
| Test backport | Yes, adapted | Remove phase regression test; rest tests public interface |
| solution-design skill | Keep (exists at 48bc8ed) | Removed in refactor but still valid |

## Working Copy

All work on `~/claude-config-rebase` (copy of `/repos/claude-config`).
Original repo remains untouched until verified.

---

## Phase 1: Backup & Reset

```bash
cd ~/claude-config-rebase
git branch backup-pre-rebase HEAD
git reset --hard 48bc8ed
```

**Verify:** 167 tests pass
```bash
cd skills/scripts
/repos/claude-config/.venv/bin/python3 -m pytest tests/ --ignore=tests/test_ast.py -q
cd ../..
```

---

## Phase 2: Extract Brand-New Files

These files were created in `32a0e90` and have zero dependency on the refactor:

```bash
git checkout backup-pre-rebase -- \
  .envrc .python-version .gitignore pyproject.toml uv.lock statusline.sh \
  CLAUDE.md post-sync.sh \
  hooks/.env.example hooks/install.sh hooks/ntfy_hook.py \
  "skills/alan-coding-style/" \
  "skills/scripts/skills/alan_coding_style/__init__.py"

mkdir -p plans
git checkout backup-pre-rebase -- \
  "plans/deterministic-qr-gates-plan.md" \
  "plans/planner-lite.md" \
  "plans/planner-skill-bugs.md"
```

---

## Phase 3: Apply Safe Diffs to Existing Files

### README.md — apply diff (no refactor references)

```bash
git diff 48bc8ed..backup-pre-rebase -- README.md | git apply
```

Adds fork context header, reorganizes deepthink prominence, renumbers workflow steps.
If `git apply` fails, use `git apply --3way` or manual edit.

### conventions/documentation.md — apply diff (no refactor references)

```bash
git diff 48bc8ed..backup-pre-rebase -- conventions/documentation.md | git apply
```

Adds architecture documentation section and agent policy guidance.

### skills/CLAUDE.md — MANUAL EDIT

The diff from `32a0e90` both adds `alan-coding-style/` (want) AND removes `solution-design/`
(don't want — it still exists at 48bc8ed). Also patches paths (post-sync.sh handles that).

Changes to make manually:
1. Add the "MANDATORY: Read Before Modifying" section after line 2
2. Update the Files table description for README.md
3. Add `alan-coding-style/` row to Subdirectories table
4. **Keep** `solution-design/` row (do NOT remove)
5. Update Script Invocation section (remove `--total-steps N`)
6. Leave paths as `.claude` (post-sync.sh will patch them in Phase 6)

### conftest.py — MANUAL EDIT

File: `skills/scripts/tests/conftest.py`

Add to SKILL_MODULES list:
```python
"skills.alan_coding_style.coding_style",
```

**Keep** existing entries including:
- `"skills.solution_design.design"` (still exists)
- `"skills.codebase_analysis.analyze_workflow"` (not yet renamed)
- `"skills.planner.planner"` (not yet split into orchestrator)
- `--total-steps` logic in `run_skill_invocation`

---

## Phase 4: Write Backported alan-coding-style

File: `skills/scripts/skills/alan_coding_style/coding_style.py`

### Import changes (lines 19-30)

Replace:
```python
from skills.lib.workflow.core import (StepDef, Workflow)
from skills.lib.workflow.ast import W, XMLRenderer, render
from skills.lib.workflow.ast.nodes import (
    FileContentNode, TextNode, StepHeaderNode, CurrentActionNode, InvokeAfterNode,
)
from skills.lib.workflow.ast.renderer import (
    render_step_header, render_current_action, render_invoke_after,
)
```

With:
```python
from skills.lib.workflow.core import (StepDef, Workflow)
from skills.lib.workflow.ast import W, XMLRenderer, render
from skills.lib.workflow.ast.nodes import TextNode
```

### load_section_files (line 64-75)

Change return type from `list[FileContentNode]` to `list[tuple[str, str]]`:

```python
def load_section_files(sections: list[str]) -> list[tuple[str, str]]:
    refs_dir = get_references_dir()
    result = []
    for sec in sections:
        if sec not in SECTION_TO_FILE:
            valid = ", ".join(sorted(SECTION_TO_FILE.keys()))
            sys.exit(f"ERROR: Unknown section '{sec}'. Valid: {valid}")
        rel_path = SECTION_TO_FILE[sec]
        full_path = refs_dir / rel_path
        content = read_text_or_exit(full_path, f"loading section '{sec}'")
        result.append((f"references/{rel_path}", content))
    return result
```

### format_output function

**Signature** — change `file_nodes` type:
```python
def format_output(
    step: int,
    guidance: dict,
    thoughts: str,
    file_nodes: list[tuple[str, str]] | None = None,
    sections_arg: str | None = None,
) -> str:
```

**Step header** (was lines 664-668) — use W.el() pattern:
```python
title = f"CODING STYLE - {guidance['phase']} - {guidance['step_title']}"
parts.append(render(
    W.el("step_header", TextNode(title),
        script="alan_coding_style", step=str(step), total=str(TOTAL_STEPS)
    ).build(),
    XMLRenderer()
))
```

**File content rendering** (was lines 679-687) — inline CDATA:
```python
if file_nodes:
    parts.append("<style_references>")
    parts.append("Style guide sections loaded based on your section selection:")
    parts.append("")
    for path, content in file_nodes:
        escaped = content.replace("]]>", "]]]]><![CDATA[>")
        parts.append(f'<file path="{path}"><![CDATA[\n{escaped}\n]]></file>')
        parts.append("")
    parts.append("</style_references>")
    parts.append("")
```

**Current action** (was line 690):
```python
action_nodes = [TextNode(a) for a in guidance["actions"]]
parts.append(render(W.el("current_action", *action_nodes).build(), XMLRenderer()))
```

**Invoke after** (was line 703):
```python
parts.append(render(W.el("invoke_after", TextNode(next_cmd)).build(), XMLRenderer()))
```

### WORKFLOW definition — add phase= back

```python
WORKFLOW = Workflow(
    "alan-coding-style",
    *[
        StepDef(
            id=s["id"],
            title=s["step_title"],
            phase=s["phase"],
            actions=s["actions"],
        )
        for s in (STEPS[i] for i in sorted(STEPS))
    ],
    description="Multi-turn coding style compliance workflow",
    validate=False,
)
```

### Everything else

`STEPS` dict, `get_step_guidance()`, `get_references_dir()`, `SECTION_TO_FILE`,
`XML_FORMAT_MANDATE`, `HISTORY_STEP_*` constants, and `main()` are all **unchanged**.
They don't reference any API types.

---

## Phase 5: Write Adapted Test File

File: `skills/scripts/tests/test_alan_coding_style.py`

Backport from `832d7bb` with these changes:

1. **Remove** `test_stepdef_has_no_phase_field` — at 48bc8ed StepDef HAS phase
2. **Adjust imports** — no StepHeaderNode; import from public module
3. **Update `test_load_section_files_*`** — assert returns `tuple[str, str]` not FileContentNode
4. **Update `test_format_output_with_file_nodes`** — pass `list[tuple[str, str]]`
5. **CLI tests** — keep as-is (argparse interface unchanged)
6. **Keep `test_workflow_*` tests** — WORKFLOW is still a Workflow instance

---

## Phase 6: Run post-sync.sh

```bash
./post-sync.sh
```

Patches all `.claude` → `~/.claude` paths across `*.md` and `*.py` files.
Must run AFTER all content is in place (Phase 2-5).

**Verify dry-run first:**
```bash
./post-sync.sh --dry-run
```

---

## Phase 7: Final Verification

```bash
cd skills/scripts
/repos/claude-config/.venv/bin/python3 -m pytest tests/ --ignore=tests/test_ast.py -v
cd ../..
```

**Expected:** 167 original tests + ~15 alan-coding-style tests = ~180+ passed.

Check specific alan-coding-style functionality:
```bash
cd skills/scripts
/repos/claude-config/.venv/bin/python3 -m skills.alan_coding_style.coding_style --step 1 --thoughts "test"
cd ../..
```

---

## Phase 8: Commit

Single commit with all changes:
```bash
git add -A
git commit -m "Rebase to 48bc8ed: backport alan-coding-style, extract independent work

Reset to pre-refactor stable state (48bc8ed). The Large refactor (53ce0e7)
introduced 3 categories of test failures. All 22 post-refactor commits
depend on the refactored API and cannot be cherry-picked.

Backported: alan-coding-style skill (rewritten for old AST API)
Extracted: hooks, post-sync.sh, pyproject.toml, CLAUDE.md, plans, .envrc
Excluded: planner_lite (depends on new API, re-add after upstream fixes)
Preserved: solution-design skill (still valid at this commit)"
```

---

## Post-Rebase Notes

- **origin/main** is 4 commits ahead of 48bc8ed — force-push will be needed
- **Stash** ("writing style") survives the reset
- **Untracked files** (output-styles/, hooks/ntfy_hook.log, tmp.md) are unaffected
- **tmp remote** exists — may need updating

### Files that reappear (deleted by refactor, restored by reset)

These files exist at 48bc8ed and will be back:
- `skills/scripts/skills/planner/planner.py` (1076 lines, monolithic)
- `skills/scripts/skills/planner/executor.py` (1251 lines, monolithic)
- `skills/scripts/skills/planner/explore.py` (347 lines)
- `skills/scripts/skills/planner/qr/` (5 QR modules)
- `skills/scripts/skills/planner/tw/` (2 TW modules)
- `skills/scripts/skills/planner/dev/fill_diffs.py`
- `skills/scripts/skills/solution_design/` (entire skill)
- `skills/scripts/skills/lib/workflow/formatters/` (2 files)
- `skills/solution-design/` (skill docs)

### Files that disappear (created by refactor, gone after reset)

- `skills/scripts/skills/planner/orchestrator/` (planner.py, executor.py)
- `skills/scripts/skills/planner/architect/` (3 files)
- `skills/scripts/skills/planner/developer/` (6 files)
- `skills/scripts/skills/planner/technical_writer/` (6 files)
- `skills/scripts/skills/planner/quality_reviewer/` (14 files)
- `skills/scripts/skills/planner/cli/` (7 files)
- `skills/scripts/skills/planner/shared/qr/` (6 files)
- `skills/scripts/skills/planner/shared/builders.py`, `constants.py`, `constraints.py`, `gates.py`, `resources.py`, `routing.py`, `schema.py`, `temporal_detection.py`
- `skills/scripts/skills/lib/workflow/ast/dispatch.py`, `dispatch_renderer.py`
- `skills/scripts/skills/lib/workflow/prompts/`
- `skills/planner/INTENT.md`, `skills/planner/resources/plan-json-schema.md`
- `agents/architect.md`, `conventions/REGISTRY.yaml`
- All prompt-engineer papers added in refactor (~20 files)
- `skills/scripts/validate_conventions.py`
- `skills/scripts/tests/test_qr_verify_routing.py`

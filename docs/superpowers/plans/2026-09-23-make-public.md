# Make-Public Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the `make-public` branch presentable: a README that shows the fork's ideas with evidence links, the two stray root files in `notes/`, a second copyright line, and a CI workflow that runs the whole suite.

**Architecture:** Four mechanical edits (test allowlist, file move, LICENSE, CI) land first, each with its own commit and its own check. The README is then built in three passes: parallel read-only subagents write one fact sheet per idea cluster into the scratchpad, the README is drafted from those sheets against the structure in the spec, and a reviewing subagent checks every claim against the tree before the commit. Nothing is pushed.

**Tech Stack:** bash, Python 3.14 via `uv`, `cargo`, GitHub Actions, `actionlint` (via `nix shell`).

**Spec:** `docs/superpowers/specs/2026-09-23-make-public-design.md`.

**Conventions for every task:** run from `/root/claude-config-work3` (a worktree; never `install.sh`). Wrap anything slow or side-effectful in `agent-tools run --desc "..."`. Every commit message ends with the trailer `Claude-Session: 173ac871-a3fb-49e1-9c12-61b99cab3e92`. Python tests run as `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config-work3 uv run pytest`.

---

### Task 1: `tests/test_install.py` allowlist

**Files:**
- Modify: `tests/test_install.py:14`

- [ ] **Step 1: Run the test to see the failure**

Run: `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config-work3 uv run pytest -q tests/test_install.py`
Expected: `1 failed`, stderr in the traceback reads `install.sh: line 68: basename: command not found`.

- [ ] **Step 2: Add `basename` to the allowlist**

```python
    for command in ("basename", "dirname", "ln", "mkdir"):
        (bin_dir / command).symlink_to(Path("/usr/bin") / command)
```

- [ ] **Step 3: Run the test to see it pass**

Run: `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config-work3 uv run pytest -q tests/test_install.py`
Expected: `1 passed`.

- [ ] **Step 4: Commit**

```bash
git add tests/test_install.py
git commit -m "tests: install.sh links systemd units with basename

Claude-Session: 173ac871-a3fb-49e1-9c12-61b99cab3e92"
```

### Task 2: Move the two root analysis files into `notes/`

**Files:**
- Move: `planner-qr-gate-override-analysis.md` → `notes/planner-qr-gate-override-analysis.md`
- Move: `planner-verification-reporting-analysis.md` → `notes/planner-verification-reporting-analysis.md`

The `**Related**:` line at `planner-qr-gate-override-analysis.md:6` names its sibling by bare filename; both files move into the same directory, so it stays correct. The mentions under `notes/compliance-check-failure-mode/experiments/*__old-worktree-reads.md` are recorded directory listings and stay as written.

- [ ] **Step 1: Move**

```bash
git mv planner-qr-gate-override-analysis.md notes/
git mv planner-verification-reporting-analysis.md notes/
```

- [ ] **Step 2: Check nothing else pointed at the root paths**

Run: `git grep -n -E "planner-(qr-gate-override|verification-reporting)-analysis" -- . ':!notes/compliance-check-failure-mode/experiments'`
Expected: exactly one line, `notes/planner-qr-gate-override-analysis.md:6:**Related**: ...`.

- [ ] **Step 3: Commit**

```bash
git commit -m "notes: move the two March planner analyses out of the repository root

Claude-Session: 173ac871-a3fb-49e1-9c12-61b99cab3e92"
```

### Task 3: LICENSE

**Files:**
- Modify: `LICENSE:3`

- [ ] **Step 1: Add the line**

The file's first four lines become:

```
MIT License

Copyright (c) 2025 Leon Mergen
Copyright (c) 2026 Xinyang Chen
```

- [ ] **Step 2: Check the MIT body is untouched**

Run: `git diff --stat LICENSE`
Expected: `1 file changed, 1 insertion(+)`.

- [ ] **Step 3: Commit**

```bash
git add LICENSE
git commit -m "LICENSE: add the fork's copyright line

Claude-Session: 173ac871-a3fb-49e1-9c12-61b99cab3e92"
```

### Task 4: CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`
- Delete: `.github/workflows/skills-test.yml`
- Modify: `.github/workflows/CLAUDE.md` (the `## Files` table)
- Modify: `.github/CLAUDE.md` (the `workflows/` row)

- [ ] **Step 1: Write `ci.yml`**

```yaml
name: CI

on:
  push:
  pull_request:
  workflow_dispatch:

jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      # No floating major tag is published for this action; its README pins by
      # commit. The exact tag is the closest equivalent.
      - uses: astral-sh/setup-uv@v10.2.0
      - name: Sync the locked environment
        run: uv sync --frozen
      - name: Run the Python suite
        run: uv run pytest -q

  rust:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: agent-tools
    steps:
      - uses: actions/checkout@v7
      - uses: dtolnay/rust-toolchain@stable
      - name: Run the Rust suite
        run: cargo test
```

- [ ] **Step 2: Remove the old workflow**

```bash
git rm .github/workflows/skills-test.yml
```

- [ ] **Step 3: Update the two index files**

`.github/workflows/CLAUDE.md` `## Files` table becomes:

```markdown
| File     | What                                                                                       | When to read                                   |
| -------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------- |
| `ci.yml` | Two jobs on every push and PR: `uv run pytest` (tests/ and skills/scripts/tests) and `cargo test` in `agent-tools/` | Debugging CI failures, modifying test pipeline |
```

`.github/CLAUDE.md` `workflows/` row becomes:

```markdown
| `workflows/` | GitHub Actions: `ci.yml` runs the Python and Rust suites | Adding CI jobs, debugging workflow failures |
```

- [ ] **Step 4: Lint**

Run: `nix shell nixpkgs#actionlint -c actionlint .github/workflows/ci.yml`
Expected: no output, exit 0.

- [ ] **Step 5: Run what the jobs run, locally**

Run: `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config-work3 uv sync --frozen && UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config-work3 uv run pytest -q 2>&1 | tail -3`
Expected: `811 passed` (the two Pydantic deprecation warnings are pre-existing).

- [ ] **Step 6: Commit**

```bash
git add .github
git commit -m "ci: run the whole Python and Rust suites on every push

Claude-Session: 173ac871-a3fb-49e1-9c12-61b99cab3e92"
```

### Task 5: Fact sheets, one per idea cluster

**Files:**
- Create (scratchpad, not repository): `$SCRATCH/facts/<cluster>.md` for each cluster below, where `$SCRATCH` is `/root/.claude/tmp/claude-0/-root-claude-config-work3/173ac871-a3fb-49e1-9c12-61b99cab3e92/scratchpad`.

Nine `general-purpose` subagents, `model: opus`, `run_in_background: false`, launched in one message. Each is read-only except for its one output file. Prompt template (fill `<cluster>`, `<reading list>`):

```
You are producing a fact sheet for one section of a public README for the
repository at /root/claude-config-work3 (a git worktree; do not edit, commit or
build anything). Read-only, except for writing exactly one file:
$SCRATCH/facts/<cluster>.md

Cluster: <cluster>
Reading list (read these fully unless marked "skim"): <reading list>
Also read the matching rows of /root/claude-config-work3/CLAUDE.md.

Write the fact sheet in this shape, at most 70 lines:

## What it is
2–4 sentences. What exists, and what problem it answers.

## Non-obvious ideas
Bullets. Each one states a design decision or mechanism a reader would not
guess from the directory name, and ends with the evidence as `path:line`
(repository-relative). Prefer the mechanism over the feature list.

## Measurements
Bullets: value, date it was taken, `path:line` where it is recorded. Only
numbers the documents state as measured; nothing inferred.

## Caveats
Anything a document claims that the code or another document contradicts, or
that is dated against an older Claude Code version than 2.1.269. Say "none
found" if none.

## Links
The 3–6 repository-relative paths a README section about this cluster should
link to, most important first.

Rules: every claim carries a path:line; if you cannot find the line, leave the
claim out. Do not summarise from memory of similar projects. Do not read
/repos/claude-code-decompiled or anything outside the worktree.
```

Clusters and reading lists:

| cluster | reading list |
| --- | --- |
| `harness-measurement` | `docs/system-prompt-snapshot/README.md`, `docs/system-prompt-snapshot/what-the-model-gets.md`, `docs/system-prompt-snapshot/builtin-skills/README.md`, `scripts/intercept/README.md`, `scripts/intercept/proxy.py` (skim), `docs/system-prompt-anatomy.md` (skim), `docs/background-sessions.md`, `docs/tool-token-limits.md` (skim), `notes/intercept-proxy-response-buffering.md` |
| `system-prompt` | `sys_prompt/CLAUDE.md`, `sys_prompt/alan-default-next.md` (headings only), `scripts/check-prompt-upstream.py` (docstring and structure), `scripts/check-prompt-coupling.sh`, `agent-tools/CLAUDE.md` section "Prompt-coupled strings", `src/claude_config/count_tokens.py` (docstring), `docs/superpowers/specs/2026-09-07-count-tokens-local-default-design.md`, `output-styles/README.md` (skim) |
| `prompt-tests` | `prompt-tests/CLAUDE.md`, `.claude/skills/prompt-tests/SKILL.md`, `prompt-tests/runs/README.md`, everything under `prompt-tests/general/subagent-foreground-default/`, `skills/prompt-engineer-v2/SKILL.md`, `skills/prompt-engineer-v2/experiments.md`, `notes/compliance-check-failure-mode.md`, `notes/subagent-backgrounding-overrides-run-in-background.md`, `docs/prompt-trials/` (skim) |
| `agent-tools-run` | root `CLAUDE.md` section "### `agent-tools/`", `agent-tools/CLAUDE.md`, `docs/agent-tools-status-reference.md`, `docs/superpowers/specs/2026-08-26-agent-tools-run-design.md`, `docs/superpowers/specs/2026-08-29-agent-tools-run-background-ps-design.md`, `docs/superpowers/specs/2026-08-24-agent-tools-run-observability-design.md`, `skills/long-bash/SKILL.md`, `notes/agent-tools-run-stress-findings.md`, `agent-tools/src/main.rs` (root resolution only), the file names under `agent-tools/tests/` |
| `session-logs` | `src/claude_config/cc_pretty/` (module docstrings), `src/claude_config/cc_pretty/coverage.py` (docstring), `src/claude_config/opencode_pretty/` (module docstrings), `skills/session-analysis/SKILL.md`, `agents/session-analysis.md`, `skills/diagnose-workflow/SKILL.md`, `src/claude_config/cc_workflow/` (docstrings), `docs/superpowers/specs/2026-08-12-session-analysis-skeleton-design.md`, `docs/superpowers/specs/2026-05-28-opencode-pretty-design.md`, `docs/superpowers/specs/2026-09-17-cc-pretty-id-or-path-design.md`, `notes/tool-use-result-shapes.md` (skim), `notes/rewind-restores-only-edit-tool-writes.md` (skim) |
| `telegram-hitl` | `docs/superpowers/specs/2026-09-12-telegram-hitl-design.md`, `src/claude_config/telegram_hitl/` (module docstrings), `skills/telegram-hitl/SKILL.md`, `systemd/telegram-hitl.service`, the docstrings of `tests/test_telegram_hitl_*.py`, root `CLAUDE.md` section "### The telegram-hitl channel on this machine" |
| `env-context-and-styles` | `src/claude_config/env_context/` (module docstrings), `docs/env-context-manifest.json`, `notes/env-context-manifest.md`, `scripts/check-env-context.sh`, `docs/superpowers/specs/2026-09-02-env-context-design.md`, `output-styles/README.md`, `output-styles/CLAUDE.md`, `docs/background-sessions.md`, `settings.json`, `scripts/claude.sh`, root `CLAUDE.md` sections "### `settings.json` — `CLAUDE_CODE_FORK_SUBAGENT`..." and "### `scripts/claude.sh`" |
| `design-and-conventions` | the file list of `docs/superpowers/specs/` and `docs/superpowers/plans/`, `docs/superpowers/specs/2026-09-12-telegram-hitl-design.md` (first 40 lines only, as a sample), `conventions/CLAUDE.md`, `conventions/intent-markers.md`, `conventions/agent-responses.md`, the "Tone markers" and "Writing for other agents" sections of `sys_prompt/alan-default-next.md`, `skills/git-surgery/SKILL.md`, `skills/notes/SKILL.md`, `.claude/skills/update-claude-code/SKILL.md`, the file list of `notes/` |
| `opencode` | `opencode/opencode.jsonc`, `opencode/agents/*.md` (first 30 lines each), `docs/opencode-system-prompt/alan-default-commentary.md`, `docs/opencode-system-prompt/min-commentary.md`, `docs/opencode-system-prompt/build-self-reported.md`, `skills/opencode-subcommand/SKILL.md`, `scripts/prompt-test-run.sh` (header comment), `docs/superpowers/specs/2026-05-28-opencode-prompt-testing-design.md`, root `CLAUDE.md` bullets for `agent-tools opencode`, `agent-tools opencode-pretty` and `agent-tools opencode.gate` |

- [ ] **Step 1: Create the output directory**

Run: `mkdir -p $SCRATCH/facts`

- [ ] **Step 2: Launch the nine subagents in one message, foreground**

- [ ] **Step 3: Check every sheet exists and every cited path resolves**

Run from the repository root:

```bash
for f in $SCRATCH/facts/*.md; do
  echo "== $f: $(wc -l < "$f") lines";
  grep -oE '`[A-Za-z0-9_./-]+\.(md|py|rs|sh|json|jsonc|yml|yaml|service|toml)(:[0-9]+)?`' "$f" \
    | tr -d '`' | cut -d: -f1 | sort -u \
    | while read p; do [ -e "$p" ] || echo "MISSING $p"; done
done
```

Expected: nine files, no `MISSING` lines. A missing path is a sheet defect: re-read the cited document yourself and correct or drop the claim before drafting.

### Task 6: Draft the README

**Files:**
- Replace: `README.md`

Structure and rules are in the spec, section "README". The fixed sections are given here in full; the nine idea sections are written from the fact sheets, each 5–10 lines, each claim linked to a repository-relative path, each measurement dated.

- [ ] **Step 1: Write the file**

Head of the file:

```markdown
# claude-config

[![CI](https://github.com/Alan-Chen99/claude-config/actions/workflows/ci.yml/badge.svg)](https://github.com/Alan-Chen99/claude-config/actions/workflows/ci.yml)

My Claude Code and opencode configuration, and the tooling built around it.
It began as a fork of [solatis/claude-config](https://github.com/solatis/claude-config)
and grew a Rust harness (`agent-tools`), a replacement system prompt with its
reasoning kept beside it rather than inside it, a prompt-evaluation corpus, and
a set of measured investigations into what the harness actually does.

## Status

This is a personal configuration, published to show the ideas rather than to be
installed. `install.sh` symlinks the tree into `~/.claude/` and assumes one
host layout — read it before running it anywhere. Nothing here is versioned or
packaged for anyone else, and Claude Code moves quickly: every measurement
below names the Claude Code version it was taken against.

## Ideas
```

Then the nine sections, in the spec's order, each `### <idea title>`.

Tail of the file:

```markdown
## Repository map

| Path | What |
| --- | --- |
| `CLAUDE.md` | The detailed index: every directory and subcommand, with when to read what |
| `agent-tools/` | Rust binary: the `run`/`ps` process wrapper and hooks, `cc-pretty`, `count-tokens`, `env-context`, launchers |
| `sys_prompt/` | Replacement system prompts loaded by `scripts/claude.sh`, and the reasoning behind each line |
| `output-styles/` | Output styles — the customization surface that survives a background handoff |
| `prompt-tests/` | Runner-neutral prompt evaluation cases and recorded runs |
| `notes/` | Investigation write-ups: measured evidence and root cause, one behaviour each |
| `docs/` | Captured system prompts, harness anatomy, design specs and plans |
| `skills/`, `agents/`, `conventions/` | Skills, sub-agent definitions, documentation and code conventions — upstream's, extended |
| `src/claude_config/` | Python: log renderers, the Telegram proxy, the env-context hook, token counting |
| `scripts/` | The `claude.sh` launcher, the MITM intercept proxy, prompt-test runners, drift checks |
| `opencode/` | opencode configuration and agent prompts |
| `plans/` | Plan storage, historical |
| `tests/` | The Python suite (pytest + hypothesis); Rust tests live under `agent-tools/tests/` |

## Upstream

Forked from [solatis/claude-config](https://github.com/solatis/claude-config)
at `6e72bc29` (2026-02-09). Inherited from there, and still the shape of the
planning workflow: the `planner`, `deepthink`, `refactor`, `problem-analysis`,
`decision-critic`, `codebase-analysis`, `doc-sync`, `prompt-engineer` and
`incoherence` skills; the `developer`, `architect`, `technical-writer`,
`quality-reviewer` and `debugger` agents; `conventions/`; and the
`skills/scripts` orchestration framework. Upstream's README explains that
workflow and its reasoning; this fork's copy of it, as it stood at the fork
point, is `git show 6e72bc29:README.md`.

## Install

```bash
git clone https://github.com/Alan-Chen99/claude-config ~/claude-config
~/claude-config/install.sh
```

Directory-level symlinks for `agents`, `conventions`, `output-styles` and
`skills` into `~/.claude/`, `~/.config/opencode` → `opencode/`, file symlinks
for `settings.json` and `statusline.sh`, an `agent-tools` build linked with
`scripts/claude.sh` into `~/.local/bin`, and the Python venv. Run it from the
canonical checkout only: a worktree that installs its own build repoints
`~/.local/bin` at the worktree and breaks every other session when the
worktree is deleted.

## Tests

```bash
uv run pytest                     # Python: tests/ and skills/scripts/tests
(cd agent-tools && cargo test)    # Rust
```

## License

MIT. Copyright (c) 2025 Leon Mergen for the upstream work; copyright (c) 2026
Xinyang Chen for everything since the fork.
```

- [ ] **Step 2: Check the shape**

Run: `grep -c '^### ' README.md && wc -l README.md`
Expected: `9` idea sections; total length between 200 and 320 lines.

- [ ] **Step 3: Do not commit yet** — Task 7 and Task 8 gate the commit.

### Task 7: Link check and the root `CLAUDE.md` row

**Files:**
- Modify: `CLAUDE.md:13` (the `README.md` row)
- Create (scratchpad): `$SCRATCH/check-links.py`

- [ ] **Step 1: Write the link checker**

```python
"""Every relative link and every backticked path in README.md must name a tracked path."""
import re, subprocess, sys
from pathlib import Path

root = Path("/root/claude-config-work3")
text = (root / "README.md").read_text()
tracked = set(subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                             text=True, check=True).stdout.split())
dirs = {str(Path(p).parent) for p in tracked} | {p.rsplit("/", 1)[0] for p in tracked if "/" in p}

targets = re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text)
targets += re.findall(r"`([A-Za-z0-9_][A-Za-z0-9_./-]*/[A-Za-z0-9_./-]*)`", text)
bad = []
for t in sorted(set(targets)):
    if t.startswith(("http://", "https://")):
        continue
    p = t.rstrip("/")
    if p in tracked or p in dirs or any(x.startswith(p + "/") for x in tracked):
        continue
    bad.append(t)
for b in bad:
    print("UNRESOLVED", b)
sys.exit(1 if bad else 0)
```

- [ ] **Step 2: Run it**

Run: `python3 $SCRATCH/check-links.py`
Expected: no output, exit 0. Every `UNRESOLVED` line is a README defect: fix the link.

- [ ] **Step 3: Update the `README.md` row in `CLAUDE.md`**

```markdown
| `README.md`               | Public-facing: what the fork is, the ideas in it with links to their evidence, upstream attribution, install and test commands | First orientation; before pointing anyone at the repository |
```

- [ ] **Step 4: Do not commit yet** — Task 8 gates the commit.

### Task 8: Claim review

One `quality-reviewer` subagent, `model: opus`, `run_in_background: false`. Prompt:

```
Review /root/claude-config-work3/README.md (uncommitted; `git diff README.md`
shows the rewrite) for factual accuracy against the repository tree. This is a
git worktree: read only, do not edit, commit or build.

For every sentence in the "## Ideas" and "## Upstream" sections that states
what something does, how it works, or a number: find the file that backs it.
Report each claim the tree does not support, as `README.md:<line>` — quote the
claim, name what you looked at, and say whether the fix is a rewording, a
different link, or removal. Also report any relative link whose target does
not exist and any measurement that carries no date or no source path.

Do not review style, structure or length. Do not propose additions. Do not
read /repos/claude-code-decompiled or anything outside the worktree.
Return the list, most consequential first; return "no findings" if none.
```

- [ ] **Step 1: Dispatch the reviewer**

- [ ] **Step 2: Fix every finding in `README.md`; re-run `python3 $SCRATCH/check-links.py`**

- [ ] **Step 3: Commit README and CLAUDE.md together**

```bash
git add README.md CLAUDE.md
git commit -m "README: describe the fork by its ideas, with the evidence linked

Claude-Session: 173ac871-a3fb-49e1-9c12-61b99cab3e92"
```

### Task 9: Final verification and spec amendment

**Files:**
- Modify: `docs/superpowers/specs/2026-09-23-make-public-design.md` (Housekeeping: the `**Related**:` line needs no change)

- [ ] **Step 1: Full suites**

Run (wrapped): `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config-work3 uv run pytest -q 2>&1 | tail -2` and `(cd agent-tools && cargo test 2>&1 | grep -E '^test result' | grep -v ' 0 failed' || echo 'rust: all green')`
Expected: `811 passed`; `rust: all green`.

- [ ] **Step 2: Stale names**

Run: `git grep -n -E "skills-test\.yml|Original .README" -- . ':!docs/superpowers' ':!notes/compliance-check-failure-mode/experiments'`
Expected: no output.

- [ ] **Step 3: Amend the spec's Housekeeping bullet**

Replace the sentence "Update the `**Related**:` line in `planner-qr-gate-override-analysis.md`, which names its sibling by bare filename." with "The `**Related**:` line in `planner-qr-gate-override-analysis.md` names its sibling by bare filename and stays correct, since both files move into the same directory."

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-09-23-make-public-design.md
git commit -m "spec: the Related line survives the move unchanged

Claude-Session: 173ac871-a3fb-49e1-9c12-61b99cab3e92"
```

- [ ] **Step 5: Report** — `git log --oneline 957e1203..HEAD`, the two suite tallies, and the assumption that the public URL is `github.com/Alan-Chen99/claude-config`.

# Make the repository public-ready

The repository is about to be made public. It is not meant to be usable by
anyone else yet; the purpose of publication is to show the ideas in it and to
stand behind a resume line. This spec covers what changes before the branch is
pushed. The personal-information and secrets audit is deliberately not part of
it: the owner does that pass separately, immediately before publishing.

Decisions below were taken with the owner on 2026-09-23; the measurements are
from the same day, on the `make-public` branch at `957e1203`.

## What the reader finds today

`README.md` is 410 lines: a 14-line installer note, then upstream's README
reproduced verbatim under the heading "Original `README.md`". A reader skimming
it learns upstream's workflow philosophy and nothing about this fork, which is
where the work is: 906 commits since the fork point `6e72bc29` (2026-02-09),
1046 files changed, and every directory the root `CLAUDE.md` indexes other than
`skills/`, `agents/` and `conventions/` added since.

Two March investigation write-ups sit at the repository root
(`planner-qr-gate-override-analysis.md`, `planner-verification-reporting-analysis.md`)
while every later one lives in `notes/`.

`LICENSE` carries upstream's copyright line only.

`.github/workflows/skills-test.yml` is upstream's: Python 3.11, `pytest` inside
`skills/scripts/` only, path-filtered to `skills/scripts/**`. `pyproject.toml`
requires Python 3.14 and its `testpaths` already cover both `tests/` and
`skills/scripts/tests`, so the workflow measures a subset of the suite on an
interpreter the project does not support. The full suite, run here, is
`1 failed, 810 passed`; `cargo test` in `agent-tools/` is 298 passed. The one
failure is `tests/test_install.py::test_install_links_opencode_config`: its PATH
allowlist is `("dirname", "ln", "mkdir")` and `install.sh:68` calls `basename`.
The test is the stale side.

## README

Replace the file. Shape, in order:

1. **Title and one paragraph.** What this is: the owner's Claude Code and
   opencode configuration and the tooling built around it — a fork of
   `solatis/claude-config` extended with a Rust harness (`agent-tools`), a
   replacement system prompt with its reasoning kept beside it, prompt
   evaluations, and measured investigations of the harness itself.
2. **Status.** Personal configuration, not packaged for reuse. `install.sh`
   assumes one host layout and says so; the ideas are the point.
3. **Ideas.** One section per cluster, 5–10 lines each, every claim linked to
   the file that backs it:
   - *Measure the harness before shaping the model* —
     `docs/system-prompt-snapshot/` (per-model captures of the full API request;
     no two of the five captured models receive the same prompt), the MITM
     intercept proxy in `scripts/intercept/`, `docs/system-prompt-anatomy*.md`,
     `docs/background-sessions.md`, `docs/tool-token-limits.md`.
   - *A replacement system prompt whose reasoning lives outside it* —
     `sys_prompt/` and its conciseness rule, `scripts/check-prompt-upstream.py`,
     `scripts/check-prompt-coupling.sh` with the `// PROMPT-COUPLED` markers in
     the Rust source, `agent-tools count-tokens --api` and the
     tokenizer-divergence finding.
   - *Prompt changes are measured, not asserted* — `prompt-tests/` (runner-
     neutral cases, recorded runs, harness isolation), the measurement loop in
     `skills/prompt-engineer-v2/`, `notes/` (the 47-round compliance
     investigation; the subagent-foreground measurement).
   - *The agent sees its own processes out of band* — `agent-tools run` and
     `ps`, the hook status channel and its ledger, `--background` detach, the
     byte-for-byte passthrough tests, root resolution as an assertion, the
     `long-bash` skill.
   - *Session logs as data* — `cc-pretty`, `opencode-pretty`,
     `cc-render-coverage`, the `session-analysis` skill and agent,
     `cc-workflow` and `diagnose-workflow`.
   - *Human in the loop over Telegram* — the single-drain proxy and why (a
     second `getUpdates` consumer evicts the first without an error), the unix
     socket shared across host and containers, tests against a fake Bot API.
   - *Environment context with drift detection, and output styles as the
     surface that survives a background handoff* — `agent-tools env-context`
     with `docs/env-context-manifest.json`, `output-styles/README.md`.
   - *Design first, record kept* — `docs/superpowers/specs/` and `plans/`,
     `conventions/`, the tone and intent markers, `skills/git-surgery/`.
   - *opencode as a second harness* — `opencode/agents/`,
     `docs/opencode-system-prompt/`, the opencode prompt-test runners.
4. **Repository map.** One line per top-level directory. The root `CLAUDE.md`
   is named as the detailed index; the README does not duplicate it.
5. **Upstream.** Forked from `solatis/claude-config` at `6e72bc29`
   (2026-02-09). Names what is inherited: the planner, deepthink, refactor,
   problem-analysis, decision-critic, codebase-analysis, doc-sync,
   prompt-engineer and incoherence skills; the developer, architect,
   technical-writer, quality-reviewer and debugger agents; `conventions/`; the
   `skills/scripts` framework. Links to upstream's README for that workflow.
   The embedded copy is dropped; it remains at `git show 6e72bc29:README.md`.
6. **Install, tests, license.** The current installer note, trimmed. `uv run
   pytest` and `cargo test`. A CI badge. MIT, both copyright holders.

Rules for the text:

- No claim without a path behind it. A statement of what something does links
  to the file that does it; a measurement carries its date and the file the
  number was taken from.
- No count that goes stale silently. Commit counts and file counts are omitted
  or dated.
- The README describes; `CLAUDE.md` indexes. Anything that reads like an index
  row belongs in `CLAUDE.md` and is linked, not copied.

Fact-gathering for each idea cluster is delegated to subagents that read the
backing documents and return the claims with `path:line` evidence. A reviewing
subagent then checks every claim in the drafted README against the tree before
it is committed. The fact sheets are working material, not repository content.

## Housekeeping

- `git mv` the two root analysis files into `notes/`. Update the `**Related**:`
  line in `planner-qr-gate-override-analysis.md`, which names its sibling by
  bare filename. The mentions under
  `notes/compliance-check-failure-mode/experiments/*__old-worktree-reads.md`
  are recorded directory listings from experiments and stay as written.
- `LICENSE`: add `Copyright (c) 2026 Xinyang Chen` beneath the existing line.
  The MIT text is unchanged.
- The root `CLAUDE.md` table for `README.md` is re-read after the rewrite and
  corrected if its description no longer matches.

## CI

Replace `skills-test.yml` with `ci.yml`. No path filter: the suite spans the
repository. Triggers: `push`, `pull_request`, `workflow_dispatch`.

Two jobs:

- `python`: `actions/checkout@v7`, `astral-sh/setup-uv@v10.2.0` (pinned to the
  exact tag — the action publishes no floating major tag; its own README pins
  by commit), `uv sync --frozen`, `uv run pytest -q`. The interpreter comes from
  `.python-version` under `python-preference = "only-managed"`, so nothing is
  installed by hand.
- `rust`: `actions/checkout@v7`, `dtolnay/rust-toolchain@stable`, `cargo test`
  with `working-directory: agent-tools`.

`tests/test_install.py` gets `basename` in its allowlist.

What the suite needs from the runner, all present on `ubuntu-latest`:
`/bin/bash`, `/usr/bin/{dirname,basename,ln,mkdir}`, `git`, `setsid`, `flock`.
`mitmdump` comes from the venv. Tests that need `/repos/claude-code-decompiled`
skip when it is absent.

Actions cannot be run from here. The workflow is linted with `actionlint` and
its steps are the same commands run locally.

`.github/CLAUDE.md` and `.github/workflows/CLAUDE.md` name the new file.

## Out of scope

- The personal-information and secrets audit (owner's separate pass).
- `docs/system-prompt-snapshot/` and `skills/leon-writing-style/` stay; the
  owner decided both.
- `plans/` keeps its auto-named and bug-report files.
- The two `PydanticDeprecatedSince20` warnings from upstream's
  `skills/scripts/skills/planner/shared/schema.py`.
- Whether the public repository is a GitHub fork or a standalone repository.
  The README's attribution paragraph serves either.

## Assumed

The public URL is `https://github.com/Alan-Chen99/claude-config`, taken from
the `alan` remote. The CI badge and the README's self-links use it; if the
repository is published elsewhere, those two strings change.

## Verification

- `uv run pytest -q`: 811 passed, 0 failed.
- `cargo test` in `agent-tools/`: unchanged, 0 failed.
- Every relative link in `README.md` resolves to a tracked path (checked by
  script, not by eye).
- `actionlint .github/workflows/ci.yml` clean.
- `git grep` for the old workflow name and the old root filenames finds only
  the experiment transcripts.

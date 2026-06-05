---
name: prompt-tests
description: Use when running, grading, or iterating any case under prompt-tests/. Covers prompt-evaluation work in this repo, including contamination checks and pass/acceptable/fail/invalid outcomes.
---

# prompt-tests

Runner-neutral workflow for evaluating agent prompts using cases under
`prompt-tests/general/<case>/`. Works for opencode agents, Claude Code, or any
other runner that can be driven from a shell with stdin/stdout.

## Required methodology: TDD for prompts

**REQUIRED SUB-SKILL:** Always load `superpowers:writing-skills` before
iterating on any prompt evaluated here — even when the artifact under test is
not a skill (system prompts, agent prompts, runner configs, sub-agent
definitions, etc.). The RED → GREEN → REFACTOR cycle and the Iron Law ("no
edit without a failing test first") apply to all prompt iteration, not just
skill authoring. Run the failing case first to capture the baseline (RED),
then change the prompt (GREEN), then re-run affected cases to confirm no
regression (REFACTOR). No exceptions for "small tweaks" or "obvious fixes".

## Grader rule (load-bearing)

A grader MUST read all thinking blocks (typically with `agent-tools cc-pretty`
for Claude Code JSONL or `agent-tools opencode-pretty` for opencode sessions).
**Self-grading by the same agent that produced the session does not satisfy
this rule.** Final-answer-only review does not satisfy it either.

## Test case shape

Each case under `prompt-tests/general/<case>/` contains:

- `task.md` — exact prompt sent to the tested agent through stdin. It must be
  clean task text, with no test-framework anti-cheating note.
- `reference-solution.md` — semantic pass / acceptable / fail criteria.
- `fixture/` (optional) — runnable artifacts the agent needs. Pinned at the
  fixture level (e.g., PEP 723 inline metadata for Python).

There is no `run.md` and no `baseline.md` inside the test directory.
Historical baselines from the opencode era are at
`docs/opencode-system-prompt/baselines/`.

## Workflow

1. **Pick a case.** Read `task.md` and `reference-solution.md` under
   `prompt-tests/general/<case>/`.

2. **Run the test once from a scratch cwd under `/tmp`.** Choose the
   per-runner recipe below. Capture the session log under `/tmp/`.

3. **Dispatch one grader subagent per session log.** One subagent per session
   — no parallel-grader launching. The grader's brief:

   > Read the session log with `agent-tools cc-pretty <FILE> --agent` (Claude
   > Code JSONL) or `agent-tools opencode-pretty <session> --agent` (opencode
   > session), **including all thinking blocks**. `--agent` strips ANSI color
   > and chunks oversized output into `/tmp/` files for parallel reads instead
   > of letting Bash truncate at 30k chars — read every chunk file it lists.
   > Run `/diagnose-session` over the log. First check for
   > cheating/contamination using the rules in this skill. If contaminated,
   > return `invalid` and do not grade semantic quality. Otherwise compare the
   > transcript to `reference-solution.md` semantically. Return:
   > - **Verdict**: `pass` / `acceptable` / `fail` / `invalid`.
   > - **Reasoning** grounded in transcript quotes (final answer, tool calls,
   >   thinking blocks).
   > - **Full diagnose-session report** inlined.

4. **Aggregate in the parent.** Apply outcome rules:
   - `pass` → pass.
   - `fail` → fail.
   - `acceptable` → run again. If a pattern emerges where every run is
     acceptable (never `pass`), call it `fail`. Parent's judgment.
   - `invalid` → discard the run and rerun from a clean scratch cwd. It is not
     a semantic fail.
   - Outstanding problematic behavior in the diagnose-session report can
     override `pass` → `fail`. Parent decides severity in context of the task.

Trial count is task-dependent. Run once first; iterate only if the result is
ambiguous or `acceptable`.

## Scratch cwd isolation (load-bearing)

Every tested-agent trial MUST run with its current working directory outside
this repository, under a fresh `/tmp/prompt-test-...` directory. This applies
to opencode, Claude Code, and any other harness.

Rationale: harnesses can auto-load nearby instruction files such as
`CLAUDE.md`/`AGENTS.md` from the current working tree or from files the agent
reads. `prompt-tests/CLAUDE.md` intentionally contains grader-facing case
summaries and assumption posture. If a tested agent sees it, the run is
contaminated even if the agent did not explicitly read `reference-solution.md`.

Rules:

- Create a fresh scratch directory, e.g. `SCRATCH="$(mktemp -d /tmp/prompt-test-$(basename "$CASE").XXXXXX)"`.
- Run the harness process from that scratch directory.
- For opencode, also set `--dir "$SCRATCH"`.
- Copy only task-visible fixture files into the scratch directory. Do not copy
  `reference-solution.md`, `prompt-tests/CLAUDE.md`, or any grader-only docs.
- Use absolute `$REPO/...` paths for harness plumbing such as the agent prompt
  file and `task.md` stdin.
- If the harness has a flag/env var to disable project instruction loading, use
  it. For opencode, set `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1` in addition to
  `OPENCODE_DISABLE_PROJECT_CONFIG=1`.

## Cheating and contamination detection (grader-only)

The tested agent must not receive anti-cheating instructions in `task.md`.
Cheating detection belongs to graders and harness maintainers, not the agent
being tested.

Mark a run `invalid` and demand a rerun if the tested-agent transcript shows any
of these, whether intentional, accidental, or auto-loaded:

- Any read/list/glob/grep/search/bash/tool action touching a path matching
  `**/prompt-tests/**` from any git worktree of `claude-config`, including
  `/root/claude-config-work/prompt-tests/...` and `/repos/claude-config/...`.
- Any explicit or implicit access to `reference-solution.md`,
  `prompt-tests/CLAUDE.md`, grader prompts, baselines, or other grader-only
  prompt-test files.
- Any auto-loaded instruction content from `prompt-tests/CLAUDE.md` or nearby
  `CLAUDE.md`/`AGENTS.md` files under a prompt-test directory.
- Any other action whose purpose or effect is to inspect hidden test criteria,
  expected answers, grader-only docs, or prior test results for the same case.

Do not count this as `fail`: contamination means the run no longer measures the
agent's behavior on the task. Discard the run and rerun with a clean scratch cwd
and corrected harness isolation.

## Runner recipes

### opencode

See `skills/opencode-subcommand` for the full recipe. The minimal pattern for
running a test under an existing agent prompt (e.g., `opencode/agents/alan-default.md`):

```bash
REPO="$(git rev-parse --show-toplevel)"
CASE="prompt-tests/general/superpowers-startup-components"
SCRATCH="$(mktemp -d /tmp/prompt-test-$(basename "$CASE").XXXXXX)"
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["superpowers@git+https://github.com/obra/superpowers.git"],
  "agent": {
    "prompt-test": {
      "mode": "primary",
      "prompt": "{file:'"$REPO"'/opencode/agents/alan-default.md}",
      "permission": {"read":"allow","glob":"allow","grep":"allow","list":"allow","bash":"allow","edit":"deny"}
    }
  }
}' \
opencode run --agent prompt-test --format json --dir "$SCRATCH" \
  < "$REPO/$CASE/task.md" | tee "/tmp/$(basename $CASE)-$(date +%s).jsonl"
```

For cases that need files in the tested agent's cwd, copy only the fixture
contents into the scratch directory before running. Do not point `--dir` into
the repository.

Example for the pydantic case:

```bash
# pydantic fixture-confined run:
REPO="$(git rev-parse --show-toplevel)"
CASE="prompt-tests/general/pydantic-forward-ref-runtime-compat"
SCRATCH="$(mktemp -d /tmp/prompt-test-$(basename "$CASE").XXXXXX)"
cp -a "$REPO/$CASE/fixture/." "$SCRATCH/"
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1 \
OPENCODE_CONFIG_CONTENT='{ ... same as above ... }' \
opencode run --agent prompt-test --format json --dir "$SCRATCH" \
  < "$REPO/$CASE/task.md" | tee "/tmp/$(basename $CASE)-$(date +%s).jsonl"
```

### Claude Code

Headless invocation with `claude --print` (or `claude` with stdin piping)
captures a JSONL session log via the standard transcript location. Run it from
a fresh scratch cwd, copying only task-visible fixtures first if needed:

```bash
REPO="$(git rev-parse --show-toplevel)"
CASE="prompt-tests/general/pydantic-forward-ref-runtime-compat"
SCRATCH="$(mktemp -d /tmp/prompt-test-$(basename "$CASE").XXXXXX)"
cp -a "$REPO/$CASE/fixture/." "$SCRATCH/"  # only if the case has a fixture
(
  cd "$SCRATCH"
  claude --print < "$REPO/$CASE/task.md"
)
```

Adapt to the local Claude Code version's flags. Capture the session log path
printed at exit, or pull it from `~/.claude/projects/<slug>/<session>.jsonl`.
For any other harness, use the same pattern: scratch cwd under `/tmp`, fixtures
copied in, grader-only files left in the repo.

## Pitfalls

- **Do not launch trials from inside a subagent.** Background tasks scoped to a
  subagent turn are reaped before the runner finishes. Launch from the
  longest-lived session (typically the parent / main session).
- **Reading the rendered log is not optional.** A grader that only reads the
  final answer text cannot satisfy the grader rule above.
- **Pass `--agent` to `agent-tools opencode-pretty` (and `cc-pretty`).** Without
  it, the rendered log writes straight to stdout and Bash truncates large
  sessions at 30k chars. With `--agent`, the tool strips ANSI color and, when
  the output exceeds the Bash limit, writes chunk files under `/tmp/` and
  prints their paths — read every chunk file it lists. Use the printed
  drill-down hint (`agent-tools opencode-pretty <session> --message <id> --full`)
  to recover any single message in full.
- **Don't commit raw JSON session logs.** Keep them under `/tmp/`. Summarize
  failure modes in commit messages or, if persistent, in
  `docs/opencode-system-prompt/baselines/`.

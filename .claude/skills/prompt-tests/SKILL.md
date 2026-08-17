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

   > Read the session log with the session-analysis skill's reading
   > protocol: `agent-tools cc-pretty <FILE> --skeleton` (Claude Code JSONL)
   > or `agent-tools opencode-pretty <session> --skeleton` (opencode), then
   > extract batches per the protocol, **including all thinking/reasoning
   > blocks**. Run the `session-analysis` skill in **diagnose mode** over
   > the log. First check for
   > cheating/contamination using the rules in this skill. If contaminated,
   > return `invalid` and do not grade semantic quality. Otherwise compare the
   > transcript to `reference-solution.md` semantically. Return:
   > - **Verdict**: `pass` / `acceptable` / `fail` / `invalid`.
   > - **Reasoning** grounded in transcript quotes (final answer, tool calls,
   >   thinking blocks).
   > - **Full diagnose report** inlined.

4. **Aggregate in the parent.** Apply outcome rules:
   - `pass` → pass.
   - `fail` → fail.
   - `acceptable` → run again. If a pattern emerges where every run is
     acceptable (never `pass`), call it `fail`. Parent's judgment.
   - `invalid` → discard the run and rerun from a clean scratch cwd. It is not
     a semantic fail.
   - Outstanding problematic behavior in the diagnose report can
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

### System-prompt contamination (harness-side)

Beyond agent-visible cheating, opencode has three harness-side channels
that inject content into the system prompt. See
`skills/opencode-subcommand/SKILL.md` "System-prompt contamination"
section for the full inventory (C1 `{file:PATH}` frontmatter leak, C2
`agent-tools run --desc` argv leak, C3 CLAUDE.md/AGENTS.md/CONTEXT.md
injection). For probe/eval work, the load-bearing hardening:

- Any spec loaded via `{file:PATH}` MUST have its YAML frontmatter
  stripped or must have no `#` comments referencing rounds, probes,
  hypotheses, or prior outcomes. Verify per file with
  `scripts/strip-frontmatter.py --check <spec>.md` (exit 1 if any
  markers remain). Create clean variants with
  `scripts/strip-frontmatter.py <spec>.md` — writes a sibling
  `<spec>-clean.md`.
- For probe wraps, pass `agent-tools run --hide-cmdline --desc ...` so
  the description and wrapped argv do not leak via `/proc/*/cmdline`
  (F88 fix; regression guard in
  `tests/run_test.rs::hide_cmdline_hides_desc_and_argv_from_proc_self_cmdline`).
  The hide is opt-in — without the flag, argv is visible for
  debugging clarity but the desc is still recoverable via `ps aux`
  by a peer test-agent. Older installed binaries do not recognize the
  flag — rebuild in place if `agent-tools run --hide-cmdline --help`
  errors.
- The default opencode recipe in the "Runner recipes" section below
  sets `OPENCODE_DISABLE_PROJECT_CONFIG=1` and
  `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1`; keep both for any probe
  harness derived from it.

## Runner recipes

### opencode

See `skills/opencode-subcommand` for the full recipe. The minimal pattern for
running a test under an existing agent prompt (e.g., `opencode/agents/alan-default-ids.md`):

#### Plugin policy (load-bearing)

Run the tested agent with **no plugins loaded** (`"plugin": []`) by default.
Superpowers in particular injects a `brainstorming` skill whose HARD-GATE
blocks all implementation tasks pending design approval; on cases like
`coverage-disclosure` and `network-resilience` this produces a pre-disclosure
failure (the agent never reaches the artifact-delivery step the test grades),
so the test measures plugin behavior rather than the agent prompt's behavior.
See `docs/opencode-system-prompt/baselines/coverage-disclosure.md`
Configuration 1 for the verbatim failure.

Opt in to plugins only for cases that specifically exercise plugin behavior.
The only such case currently is `general/superpowers-startup-components`, which
asks the agent to identify superpowers-origin prompt components and therefore
requires the plugin loaded. Add to the plugin list for that case:

```json
"plugin": ["superpowers@git+https://github.com/obra/superpowers.git"]
```

#### Worktree `agent-tools` binary (load-bearing for any prompt that calls `agent-tools`)

The default recipe always prepends the worktree's `agent-tools/target/release` directory to `PATH` and sets `CLAUDE_CONFIG_ROOT=$REPO`. `agent-tools opencode.gate` (and any other agent-tools subcommand reachable from the agent prompt) carries strings baked into the binary at build time, including the GATE_STDOUT constant in `agent-tools/src/main.rs`. The system binary at `~/.local/bin/agent-tools` resolves to the canonical repo (`/repos/claude-config`) per the install.sh rule; changes made in a worktree never reach it. Without the PATH override, the test agent invokes the canonical binary and your worktree GATE_STDOUT edit is silently invisible — the prompt change appears tested, but the gate the agent actually sees is the unchanged one.

`CLAUDE_CONFIG_ROOT` is an assertion, not an override. Worktree-built `agent-tools` refuses to run unless the env var canonicalizes to the same root the binary was built from. This turns wrong-worktree and stale-binary prompt tests into setup failures instead of silent false confidence.

The override is invisible to the tested agent's observable surface: `PATH` and `CLAUDE_CONFIG_ROOT` are process env vars, not directories or files. The agent does not read them in normal operation; even if it did (`which agent-tools` or inspecting env), the worktree path identifies the worktree but does not reveal which prompt clause is under test or what answer is being graded — unlike directory-based isolation, where a fixture file's contents can leak the test goal. Worktree-name-based information leakage is bounded to "this is being run from a worktree", which the agent should already assume during any prompt-test run.

Rebuild the worktree binary whenever `agent-tools/src/main.rs` (or any prompt-coupled constant) changes:

```bash
cd "$REPO/agent-tools" && cargo build --release
```

Do not fall back to the system binary for opencode prompt tests. `alan-default-ids` calls `agent-tools opencode.gate`, so a missing worktree binary means the run does not exercise the worktree prompt-coupled code.

#### Default recipe

```bash
REPO="$(git rev-parse --show-toplevel)"
CASE="prompt-tests/general/network-resilience"
SCRATCH="$(mktemp -d /tmp/prompt-test-$(basename "$CASE").XXXXXX)"
WORKTREE_BIN="$REPO/agent-tools/target/release"
test -x "$WORKTREE_BIN/agent-tools"
export PATH="$WORKTREE_BIN:$PATH"
export CLAUDE_CONFIG_ROOT="$REPO"
OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [],
  "agent": {
    "prompt-test": {
      "mode": "primary",
      "model": "openai/gpt-5.5",
      "variant": "xhigh",
      "prompt": "{file:'"$REPO"'/opencode/agents/alan-default-ids.md}",
      "permission": {"read":"allow","glob":"allow","grep":"allow","list":"allow","bash":"allow","edit":"allow","write":"allow"}
    }
  }
}' \
opencode run --agent prompt-test --format json --dir "$SCRATCH" \
  < "$REPO/$CASE/task.md" | tee "/tmp/$(basename $CASE)-$(date +%s).jsonl"
```

Verify the agent will receive the worktree GATE_STDOUT before running tests:

```bash
CLAUDE_CONFIG_ROOT="$REPO" "$WORKTREE_BIN/agent-tools" opencode.gate < /dev/null | head -5
```

If the command fails or the printed text doesn't reflect your edit, rebuild the worktree binary before running the prompt test.

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
  the trial in a record at `docs/opencode-system-prompt/trials/<YYYY-MM-DD>-<case>-<descriptor>.md`
  per the trial-logging rule in `prompt-tests/CLAUDE.md`. Do not append to a
  single growing iteration log.
- **Set model and variant in the config block, not the agent file frontmatter.**
  When the recipe uses `"prompt": "{file:...}"`, opencode does not apply the
  agent file's frontmatter. Set `model` and `variant` (e.g.
  `openai/gpt-5.5` and `xhigh` for `alan-default`) inside the agent block of
  `OPENCODE_CONFIG_CONTENT`, then verify with
  `agent-tools opencode-pretty <session> --agent`. See `prompt-tests/CLAUDE.md`
  ("Model/variant fidelity") for the failure mode.

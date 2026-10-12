# Contamination

What the runner scripts do, what a hand-rolled run must do, and what makes a
run `invalid`.

Every tested-agent trial runs with its cwd outside this repository, in a fresh
`/tmp/prompt-test-...` directory — harnesses auto-load `CLAUDE.md`/`AGENTS.md`
from the cwd and from files the agent reads. The runner scripts do this; a
hand-rolled run must:

- `SCRATCH="$(mktemp -d /tmp/prompt-test.XXXXXXXX)"`, and run the harness
  process from there (for opencode, also `--dir "$SCRATCH"`). **No case or tag
  name in that path.** The agent reads its own cwd — environment block,
  scratchpad path, every shell prompt — and case names here describe the
  behaviour under test, so a cwd built from one announces the measurement.
- Copy only the case's `fixture/` in — never `reference-solution.md`,
  `prompt-tests/CLAUDE.md`, or any other grader-only doc.
- Use absolute `$REPO/...` paths for plumbing such as the prompt file and
  `task.md` stdin.
- For opencode, `OPENCODE_DISABLE_PROJECT_CONFIG=1` and
  `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1`.

**No plugins, either runner.** Superpowers injects a `brainstorming` skill whose
HARD-GATE blocks implementation tasks pending design approval, so the agent never
reaches the artifact-delivery step a case grades and the run measures the plugin.
A transcript showing that, or any other plugin enforcement before the
artifact-delivery step, is **misconfigured** — rerun it, do not grade it.

Detection is grader-only; `task.md` never carries an anti-cheating note. Mark a
run **`invalid`** and rerun — not `fail`, since it did not measure the task — if
the tested-agent transcript shows any of:

- any tool action touching a path matching `**/prompt-tests/**` in any worktree
  of `claude-config`;
- any access to `reference-solution.md`, `prompt-tests/CLAUDE.md`, grader
  prompts, baselines, or prior results for the case;
- auto-loaded instruction content from a `CLAUDE.md`/`AGENTS.md` under a
  prompt-test directory;
- the case's own name, or any word from it, in the agent's cwd, its scratchpad
  path, or anything else it can read. The runner scripts name the scratch
  directory neutrally; a hand-rolled run must too.
- **anything naming the harness inside the cwd**, which is the same leak without
  a case name in it: a settings file, a log, a marker. An agent lists its working
  directory before it starts and reports what it found. Keep harness plumbing
  outside the cwd and give it a path that does not say *prompt test*.
- **the command line**, which `--hide-cmdline` does not cover. It hides the
  wrapper's argv; the wrapped command is its own process and its
  `/proc/<pid>/cmdline` still spells out the case name and the arm, where a peer
  test-agent can read them. Both runners take a `<case>` containing a slash as
  given and `pwd` is logical, so a neutral symlink —
  `ln -s "$REPO/prompt-tests/general/<case>" /tmp/<neutral>` — keeps the name out
  of the argv and out of the log filename at once.

**The downstream reader is an agent with tools and nothing to look at.** Its cwd
holds one file and the plan it is handed names several, so it goes looking — and
every other arm's scratch tree is a sibling directory away under a shared
`/tmp`. Measured 2026-09-25: one reader listed six of them by name, reported
which were pre- and which post-execution, and edited a script inside the tree a
different arm had just been measured in. Give each run its own
`PROMPT_TEST_SCRATCH_BASE`, and have `downstream.md` put the machine out of
reach, so the search is unproductive and unmotivated at once. `/tmp` is shared
with other sessions on this host as well, so a base of `/tmp` is not private even
when your own round is serial.

**Harness-side channels (opencode).** Full inventory in
`skills/opencode-subcommand/SKILL.md`, "System-prompt contamination". The one
that bites probe work: a spec loaded via `{file:PATH}` has its frontmatter
injected verbatim. `scripts/strip-frontmatter.py --check <spec>.md` exits 1 if
markers remain; without `--check` it writes `<spec>-clean.md`.

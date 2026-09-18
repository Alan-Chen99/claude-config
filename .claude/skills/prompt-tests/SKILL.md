---
name: prompt-tests
description: Use when running, grading, or iterating any case under prompt-tests/. Covers prompt-evaluation work in this repo, including the runners, contamination checks, and reading a run as a trajectory rather than a verdict.
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

## The grader

One grader per arm, dispatched as a subagent, reading the **whole session** —
`agent-tools cc-pretty` for Claude Code JSONL, `agent-tools opencode-pretty` for
opencode — under the `session-analysis` reading protocol. The final answer, a
focus-scoped extract and a list of graded axes are all projections, and a
projection taken before judgement cannot show what the output paid to score well
on it. Self-grading by the agent that produced the session satisfies nothing here.

The grader is the only reader who reads the whole session; nobody downstream
re-reads it. It therefore holds final authority over every criterion it is given.
A criterion it cannot override is one whose defects go unrecorded, and a grader
whose judgement is not trusted to override a criterion cannot be trusted to
produce the evidence either.

Reasoning for this and everything below: `docs/prompt-testing-design.md`.

## What a rubric is

`reference-solution.md` tells the grader what the caller cares about and why, so
the grader can recognise a cost when it sees one. It is guidance. It does not
bind, it does not score, and it is not the invariant — it is one sample of it,
written by someone who had read the source and not this output.

**The reference is inadmissible as a requirement.** The tested agent never saw
it, so nothing in it is something that agent should have done. An element
satisfiable only by an agent that had read the reference is defective as written:
delete it, or rewrite it as the stake it came from.

## Grader dispatch

Stage the inputs in a scratch directory with no path under `prompt-tests/` —
reading a path there injects `prompt-tests/CLAUDE.md`, which carries arm-level
results, as a system-reminder. Stage `task.md`, the arm's system prompt, the
fixture, the delivered artifact, and the session log. Withhold the reference.

**Phase 1, reference withheld.** Two arguments, in this order, to
`judgement-<arm>.md`:

1. **Constraint argument** — the strongest case that this output was the right
   move given what the agent had, argued as the agent rather than as the person
   who wrote the prompt. Its conclusion is always a claim of *no alternative*.
   Two admissible limbs: (a) quoted text required it; (b) quoted text predictably
   reads that way, evidenced by the agent's own reasoning forming that reading,
   cited by ref. Neither limb available means a **concession**, written as one.
2. **Alternative argument** — the concrete better action available within the
   requirements argument 1 quoted. Argument 2 exists to kill argument 1: an
   alternative surviving those quotes refutes the forcing claim. Every
   alternative names a **trigger**: something the agent had already seen at that
   point, cited by ref, that should have prompted it. No trigger means the item
   is **undiscoverable from the agent's position** — a finding about the task,
   not a pass for the agent, and inventing a trigger to avoid writing it is this
   dispatch's characteristic failure.

Inadmissible in argument 2, and the tell is the word *just*: "it could have just
noticed X", where what makes X worth noticing is knowing the answer; anything
reached by reading the source as a grader with both documents side by side;
anything reached from how the run turned out.

The deliverable is the **boundary** — per item, which side survives. Both
surviving means a defect in the requirements and a defect in the behaviour; do
not force a winner. Add what the output bought and what it paid, including
anything no reader looking for defects in the delivered text would notice.

**Phase 2, reference handed over** (`SendMessage` to the same agent, so it keeps
the session in context): which items the reference would have caught and which it
would have missed; the reference's defects — inadmissible elements, anything it
scores as the agent's fault that argument 1 showed was forced, anything it cannot
separate a good output from a bad one on; and whether reading it changed the
verdict. "Adequate for this output" is a listed outcome and is preferable to a
manufactured complaint. Quote the reference text and the output text that strains
it; no critique in the abstract.

~900 words phase 1, ~600 phase 2, quotes excluded.

**Overriding a criterion costs a written claim** in phase 2: the reference text,
the evidence, the repair. The owner then applies it to `reference-solution.md` or
records the rejection. Never before the run is recorded, and the pre-edit
judgement stays — a reference edited to fit the run it is grading manufactures
its own agreement. A reference edit breaks comparability with stored runs exactly
as a foci change does, so it cites the run that forced it.

Store at `prompt-tests/runs/<case>/judgement-<arm>.md`.

## Test case shape

Each case under `prompt-tests/general/<case>/` contains:

- `task.md` — exact prompt sent to the tested agent through stdin. It must be
  clean task text, with no test-framework anti-cheating note.
- `reference-solution.md` — what the case probes, and the `session-analysis`
  foci a run is read under. The foci are the case's measurement instrument:
  changing them makes new runs incomparable with stored ones, so treat a change
  to them as a change to the case.
- `downstream.md` (optional) — a second task carrying `{{ARTIFACT}}`, run
  against the first session's output. See "`downstream.md`" below.
- `fixture/` (optional) — runnable artifacts the agent needs. Pinned at the
  fixture level (e.g., PEP 723 inline metadata for Python).
- `setup.sh` (optional) — run by `scripts/prompt-test-cc.sh` in the scratch cwd
  after the fixture copy, never copied in; for state a copy cannot carry, such
  as a git repository with history.

There is no `run.md` and no `baseline.md` inside the test directory.
Historical baselines from the opencode era are at
`docs/opencode-system-prompt/baselines/`.

## Workflow

1. **Pick a case.** Read `task.md` and `reference-solution.md` under
   `prompt-tests/general/<case>/`.

2. **Run the test once from a scratch cwd under `/tmp`.** Choose the
   per-runner recipe below. Capture the session log under `/tmp/`.

3. **Dispatch the grader**, one per arm, per "Grader dispatch" above.

4. **Where the case has foci, dispatch one `session-analysis` subagent per
   focus.** `mode: evidence`, foci from the case's `reference-solution.md`. These
   are the cross-run **diff** instrument, not the grading instrument: two
   artifacts are comparable line by line only if taken under the same foci. Skip
   them when nothing is being compared, and do not add foci to a case that has
   none — 4 of 16 cases do. Where an arm ran several times, give one subagent all
   its runs and one focus. Cap each at ~500 words for a single-turn session, 600
   for an arm of three; the parent reads every artifact.

5. **Read the judgement and the artifacts.** Store both.

Trial count is task-dependent. Run once first; add runs when the artifacts of
one arm disagree with each other.

### What a run produces

The result of a run is the **trajectory**, not the agent's final answer. What
reached the answer is one span of the session; what the agent weighed and
discarded on the way is the rest of it, and a prompt edit moves that part first.
So a run's recorded output is the grader's judgement plus, where the case has
foci, the `session-analysis` evidence artifacts taken under them — the same foci
every time, so two runs are comparable line by line.

Compare a new run to the stored artifacts of the old one, artifact against
artifact. A verdict does not carry enough to compare: `fail` and `fail` look
identical whether the second run failed the same way or a new one.

Do not stamp `pass` or `fail` as a run's recorded result. Two runs can both pass
and differ in every step that got them there, so a verdict does not survive the
comparison a later reader needs. The grader's own judgement is not that result
either: it is a probe of the instrument, stored beside the artifacts, never
aggregated into a rate.

A prompt edit is justified when a forcing claim that held under the old prompt
dies under the new one. An edit that creates a new forcing claim is a regression
even where the output looks better.

`invalid` survives as a verdict, because it is a fact about the harness rather
than about the agent: a contaminated run did not measure the task. See
"Cheating and contamination detection".

### `downstream.md` (optional, per case)

A case may carry `downstream.md` next to `task.md`: a second task that puts the
first session's artifact — a handoff note, a subagent prompt, a returned table
row — in front of the reader it was written for, with the literal marker
`{{ARTIFACT}}` where the artifact goes. `scripts/prompt-test-cc-downstream.sh`
substitutes and runs it.

It exists because a defect in text written for another agent is only a defect in
what the receiver then does. The reader runs on stock Claude Code with a fresh
empty `CLAUDE_CONFIG_DIR`: no plugins, no hooks, no `CLAUDE.md`, and not the
prompt under test — a reader running that prompt can repair a defective artifact
out of its own instructions and hide the effect being measured. The reader is an
instrument, not a session under test; its answer is short, so record it verbatim
beside the artifacts rather than analysing it.

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

### A `sys_prompt/` prompt under opencode (cross-runner arm)

The standard runner for `sys_prompt/alan-default-next.md` is
`scripts/prompt-test-cc.sh` — see "Claude Code" below. `scripts/prompt-test-run.sh`
loads the same file as an opencode agent prompt, which answers a different
question: whether an effect survives a change of runner and model family. Reach
for it when a Claude-Code result looks model-specific, not as the default.

```bash
scripts/prompt-test-run.sh <case> <tag> [prompt-file]     # default: sys_prompt/alan-default-next.md
```

It creates the `/tmp` scratch cwd, copies the case's `fixture/` if it has one,
disables project config and plugins, and prints the log path and session id.
Override the model with `PROMPT_TEST_MODEL` (default
`openrouter/anthropic/claude-opus-5`, chosen so a Claude Code prompt is exercised
by a Claude model) and the log directory with `PROMPT_TEST_OUT_DIR`.

**Always run a paired baseline arm when evaluating a prompt edit.** A prompt
section that was added because a case failed must be shown to be why the case now
passes, and several cases in this directory pass at baseline:

```bash
git show HEAD:sys_prompt/alan-default-next.md > /tmp/prompt-baseline.md
scripts/prompt-test-run.sh <case> baseline /tmp/prompt-baseline.md
scripts/prompt-test-run.sh <case> green
```

Two fidelity caveats for this runner. Tool names, hooks, and the agent-view fork
behavior are Claude Code's, not opencode's, so anything the prompt says about them
is not exercised. And the script refuses a prompt file beginning with YAML
frontmatter, because opencode's `{file:...}` would inject it verbatim (C1 in the
contamination inventory).

**Snapshot both prompts to `/tmp` before launching a batch.** The runner resolves
its prompt path at session start, so editing `sys_prompt/alan-default-next.md`
while runs are in flight silently splits one arm across two prompts. Pass explicit
snapshot paths for both arms rather than relying on the default.

**Two log caveats.** The `--format json` stream is written incrementally: a log
read while the run is still in flight can be missing the final text part, so check
that the file has stopped growing, or recover the answer with
`opencode export <session-id>`, which is the source of truth. And reasoning
summaries are not always emitted — short deliberations (observed at 164–307
reasoning tokens on `openrouter/anthropic/claude-opus-5`) produce no `reasoning`
part at all while longer ones do, so a grader instructed to read every thinking
block may correctly find none. Check `info.tokens.reasoning` before recording
coverage.

**Stage a blind grader's inputs outside `prompt-tests/`.** Reading a case's
`task.md` is enough to make the harness inject `prompt-tests/CLAUDE.md` — which
carries arm-level results — into the grader's context as a system-reminder.
Instructing the grader not to read it does not help; copy `task.md` and the
gradeable rubric sections into a scratch directory and point the grader there.

**Grading a prompt edit is better done blind.** Give the grader both sessions
labelled A and B, tell it the arms differ only in the system prompt, and do not
say which is which. Name the decisive criterion in advance. Graders told which arm
is the treatment have a visible pull toward finding a difference, and every grader
in this repo's history has separately warned that the mandatory
`agent-tools pre_output.record` gate — whose `uncertainties` field maps nearly
one-to-one onto whatever the report ends up disclosing — over-determines most
candidate effects.

### Claude Code — the standard runner for a `sys_prompt/` prompt

```bash
scripts/prompt-test-cc.sh <case> <tag> [prompt-file]   # default: sys_prompt/alan-default-next.md
```

`sys_prompt/alan-default-next.md` is written for Claude Code, and this runs it
there: `agent-tools claude -p`, so the session gets this checkout's hooks,
settings, and output style alongside the prompt. Use it for any question about
what that prompt does. `scripts/prompt-test-run.sh` (opencode) answers a
different question — see below.

The script creates the `/tmp` scratch cwd, copies the case's `fixture/` if it has
one, disables plugins, sources the OAuth token, and prints the result JSON path,
the transcript path, and the session id. Read the transcript with
`agent-tools cc-pretty <FILE> --skeleton`.

The `claude -p` call is bounded at 900 seconds, because since 2.1.257 it waits
for an armed Monitor rather than exiting once its result is in — a case whose
model arms one would otherwise hang the runner with nothing said. A run that hits
the bound exits 124 and says so. `PROMPT_TEST_TIMEOUT=<seconds>` raises it, and
the same bound and variable apply to `prompt-test-cc-leg2.sh` and
`prompt-test-cc-downstream.sh`.

Read the `transcript:` path, not `result:`. `--output-format json` puts only the
**final** assistant message in `.result`, while this prompt's `## Before response`
gate makes `agent-tools pre_output.record` the last tool call — so an agent that
writes a deliverable and then runs the gate leaves the deliverable in the
second-to-last assistant message and the response template in the last one.
`.result` then holds a sentence *about* the artifact and not the artifact, which
reads as an agent claiming work it did not do.

Five mechanics it depends on:

- **Credentials.** `CLAUDE_CODE_OAUTH_TOKEN` comes from `/workspace/.env`
  (override the file with `PROMPT_TEST_ENV_FILE`). The script exits non-zero if
  the variable is unset after sourcing, rather than launching a session that
  fails at the first request.
- **Arm selection.** Claude Code applies the **last** `--system-prompt-file` on
  the command line, so the arm file is appended after the one `scripts/claude.sh`
  passes and the launcher needs no argument of its own. Verified against the
  intercepted request body: a run with an override sends the override's text as
  the entire system block, with no trace of the launcher's file. That holds for
  a session's **first** request only: a resume replays the recorded prompt, so
  `scripts/prompt-test-cc-leg2.sh` also passes `--system-prompt-snapshot off`.
- **Plugins off.** A generated `--settings` file sets every key of the
  checkout's `enabledPlugins` to `false`. It carries `enabledPlugins` and nothing
  else, so it registers no hook of its own and the checkout's hooks stay
  registered exactly once — settings sources are unioned, not overridden, and a
  second file naming the same hooks would run each of them twice.
- **Transcript location.** `agent-tools claude` relocates `CLAUDE_CONFIG_DIR`,
  so transcripts land under
  `<repo>/.claude/worktree-config/projects/<cwd-slug>/<session>.jsonl` and never
  appear in a normal session's `/resume`.
- **Reasoning capture.** `--thinking-display summarized`. Claude Code otherwise
  sends `thinking: {type: "adaptive", display: "omitted"}`, and every thinking
  block in the transcript is then `{"type":"thinking","thinking":"","signature":
  "..."}` — an empty string. The run reports its thinking-token count normally
  and the skeleton lists the blocks at `0~tok`, so a log with no reasoning in it
  looks like a log of an agent that did not reason. Confirm per run against
  `.request.thinking.display` in the intercept, or by a non-empty `.thinking` in
  the JSONL.

Two things this runner does not isolate. The user's `~/.claude/CLAUDE.md` is
linked into the config dir and reaches the agent as a `claudeMd` system-reminder;
it describes the machine, and it is identical across arms. And the launcher binds
`HTTPS_PROXY` when the MITM proxy is listening on `127.0.0.1:9160`, which is how
the request body above was read — the arm's system prompt can be confirmed per
run at `~/.claude/requests-log/<session>/0001.json`.

## Pitfalls

- **Do not launch trials from inside a subagent.** Background tasks scoped to a
  subagent turn are reaped before the runner finishes. Launch from the
  longest-lived session (typically the parent / main session).
- **Reading the rendered log is not optional.** A grader that only reads the
  final answer text cannot satisfy the grader rule above.
- **Read session logs via the session-analysis reading protocol.**
  `agent-tools cc-pretty <FILE> --skeleton` /
  `agent-tools opencode-pretty <session> --skeleton` gives a block map with
  refs; extract batches per the protocol instead of rendering the full log —
  Bash truncates large sessions at 30k chars, and full renders of big
  sessions blow the grader's context.
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

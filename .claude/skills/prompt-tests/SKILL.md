---
name: prompt-tests
description: Use when running, grading, or iterating any case under prompt-tests/. Covers prompt-evaluation work in this repo, including the runners, contamination checks, and reading a run as a trajectory rather than a verdict.
---

# prompt-tests

Runner-neutral workflow for evaluating agent prompts using cases under
`prompt-tests/general/<case>/`. Works for opencode, Claude Code, or any runner
drivable from a shell.

A run is read to understand what the prompt did, not to stamp a verdict on it.
The reasoning behind every rule below is in `docs/prompt-testing-design.md`; this
file is the operational half.

## The grader

One grader per arm, dispatched as a subagent, reading the **whole session** —
`agent-tools cc-pretty` for Claude Code JSONL, `agent-tools opencode-pretty` for
opencode — under the `session-analysis` reading protocol. Self-grading by the
agent that produced the session satisfies nothing.

The grader is the only reader who reads the whole session, so it holds final
authority over every criterion it is given, the case's `reference-solution.md`
included.

`reference-solution.md` tells the grader what the caller cares about and why. It
is guidance: it does not bind and it does not score. **It is inadmissible as a
requirement** — the tested agent never saw it, so nothing in it is something that
agent should have done. An element satisfiable only by an agent that had read it
is defective as written: delete it, or rewrite it as the stake it came from.

## Grader dispatch

Stage the inputs in a scratch directory with no path under `prompt-tests/`:
reading a path there attaches `prompt-tests/CLAUDE.md` to the grader's context as
a system-reminder, enlarging its instructions without its knowledge. Stage
`task.md`, the arm's system prompt, the fixture, the delivered artifact, and the
session log. Withhold the reference.

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
records the rejection — never before the run is recorded, and the pre-edit
judgement stays. A reference edit breaks comparability with stored runs exactly
as a foci change does, so it cites the run that forced it.

Store at `prompt-tests/runs/<case>/judgement-<arm>.md`.

**A prompt edit gets one more grader, and that one grades blind.** The
judgements above are per-arm. The comparison is a separate dispatch: one grader
holding both sessions labelled A and B, told only that they differ in the system
prompt and what the decisive criterion is. A grader told which arm is the
treatment has a visible pull toward finding a difference.

**One confound is inside the prompt under test.** `sys_prompt/alan-default-next.md`'s
`## Before response` gate requires a `pre_output.record` call whose `uncertainties`
and `possible-verification` fields ask for roughly what a disclosure-shaped case
grades — in both arms. Read that gate before attributing a disclosure to an edit
elsewhere in the prompt.

## Test case shape

Under `prompt-tests/general/<case>/`:

- `task.md` — the exact prompt sent to the tested agent through stdin. Clean task
  text, with no test-framework anti-cheating note.
- `reference-solution.md` — what the case probes, and the `session-analysis` foci
  a run is read under. Foci are the case's measurement instrument: changing them
  makes new runs incomparable with stored ones, so treat that as a change to the
  case.
- `downstream.md` (optional) — a second task carrying `{{ARTIFACT}}`, run against
  the first session's output.
- `fixture/` (optional) — runnable artifacts the agent needs, pinned at the
  fixture level (e.g. PEP 723 inline metadata for Python).
- `setup.sh` (optional) — run by `scripts/prompt-test-cc.sh` in the scratch cwd
  after the fixture copy, never copied in; for state a copy cannot carry, such as
  a git repository with history.

## Workflow

1. **Pick a case.** Read its `task.md` and `reference-solution.md`.
2. **Run it once** via a runner below. Where a prompt edit is being assessed, run
   the same case under the unedited prompt too — the comparison is against the
   baseline arm, not against expectation, and cases here can behave the same way
   in both. Snapshot both prompts to `/tmp` first (`git show HEAD:sys_prompt/…`):
   a runner resolves its prompt path at session start, so editing the prompt
   while runs are in flight splits one arm across two prompts.
3. **Dispatch the grader**, one per arm.
4. **Where the case has foci, dispatch one `session-analysis` subagent per
   focus**, `mode: evidence`. These are the cross-run **diff** instrument, not
   the grading instrument. Skip them when nothing is being compared, and do not
   add foci to a case that has none. Where an arm ran several times, give one
   subagent all its runs and one focus. Cap each at ~500 words for a single-turn
   session, 600 for an arm of three; the parent reads every artifact.
5. **Read the judgement and the artifacts.** Store both.

Run once first; add runs when the artifacts of one arm disagree with each other.

### What a run's recorded output is

The grader's judgement, plus the foci artifacts where the case has foci — under
the same foci every time, so two runs are comparable line by line. Compare a new
run to the stored artifacts of the old one, artifact against artifact.

Do not stamp `pass` or `fail` as a run's result: two runs can both pass and
differ in every step that got them there. Nothing here produces a rate, and any
aggregate built from these documents is a misuse of them.

A prompt edit is justified when a forcing claim that held under the old prompt
dies under the new one. An edit that creates a new forcing claim is a regression
even where the output looks better.

`invalid` survives as a verdict, because it is a fact about the harness rather
than about the agent — see "Contamination".

### `downstream.md`

A second task that puts the first session's artifact — a handoff note, a subagent
prompt, a returned table row — in front of the reader it was written for, with
the literal marker `{{ARTIFACT}}` where the artifact goes.
`scripts/prompt-test-cc-downstream.sh` substitutes and runs it.

A defect in text written for another agent is only a defect in what the receiver
then does. So the reader runs on stock Claude Code with a fresh empty
`CLAUDE_CONFIG_DIR`: no plugins, no hooks, no `CLAUDE.md`, and **not the prompt
under test** — a reader running that prompt can repair a defective artifact out
of its own instructions and hide the effect being measured. The reader is an
instrument, not a session under test; record its answer verbatim beside the
artifacts rather than analysing it.

## Contamination

Every tested-agent trial runs with its cwd outside this repository, in a fresh
`/tmp/prompt-test-...` directory — harnesses auto-load `CLAUDE.md`/`AGENTS.md`
from the cwd and from files the agent reads. The runner scripts do this; a
hand-rolled run must:

- `SCRATCH="$(mktemp -d /tmp/prompt-test-$(basename "$CASE").XXXXXX)"`, and run
  the harness process from there (for opencode, also `--dir "$SCRATCH"`).
- Copy only the case's `fixture/` in — never `reference-solution.md`,
  `prompt-tests/CLAUDE.md`, or any other grader-only doc.
- Use absolute `$REPO/...` paths for plumbing such as the prompt file and
  `task.md` stdin.
- For opencode, `OPENCODE_DISABLE_PROJECT_CONFIG=1` and
  `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1`.

Detection is grader-only; `task.md` never carries an anti-cheating note. Mark a
run **`invalid`** and rerun — not `fail`, since it did not measure the task — if
the tested-agent transcript shows any of:

- any tool action touching a path matching `**/prompt-tests/**` in any worktree
  of `claude-config`;
- any access to `reference-solution.md`, `prompt-tests/CLAUDE.md`, grader
  prompts, baselines, or prior results for the case;
- auto-loaded instruction content from a `CLAUDE.md`/`AGENTS.md` under a
  prompt-test directory.

**Harness-side channels (opencode).** Full inventory in
`skills/opencode-subcommand/SKILL.md`, "System-prompt contamination". Two that
bite probe work:

- A spec loaded via `{file:PATH}` has its frontmatter injected verbatim.
  `scripts/strip-frontmatter.py --check <spec>.md` exits 1 if markers remain;
  without `--check` it writes `<spec>-clean.md`.
- `agent-tools run --desc` leaves the description and the wrapped argv in
  `/proc/*/cmdline`, where a peer test-agent can read them. Pass `--hide-cmdline`
  for probe wraps.

## Runners

### Claude Code — the standard runner for a `sys_prompt/` prompt

```bash
scripts/prompt-test-cc.sh <case> <tag> [prompt-file]   # default: sys_prompt/alan-default-next.md
```

`sys_prompt/alan-default-next.md` is written for Claude Code, and this runs it
there: `agent-tools claude -p`, so the session gets this checkout's hooks,
settings, and output style alongside the prompt.

The script creates the scratch cwd, copies `fixture/`, runs `setup.sh`, disables
plugins, captures reasoning, bounds the call, and prints the result path, the
transcript path and the session id. A missing env file, an unset
`CLAUDE_CODE_OAUTH_TOKEN` or a run past the bound each exit non-zero naming the
variable to set, rather than leaving a degraded run to be discovered later; its
header comments carry the why for each.

The one mechanic worth knowing outside the script is `--thinking-display
summarized`: without it every thinking block in the transcript is an empty string
while the run still reports a thinking-token count, so a hand-rolled invocation
that drops the flag yields a log indistinguishable from an agent that did not
reason.

Two things the script cannot do for you:

- **Read the `transcript:` path, not `result:`.** `--output-format json` puts only
  the final assistant message in `.result`, and this prompt's `## Before response`
  gate makes `agent-tools pre_output.record` the last tool call — so the
  deliverable sits in the second-to-last assistant message and `.result` holds a
  sentence *about* it, which reads as an agent claiming work it did not do. Open
  it with `agent-tools cc-pretty <FILE> --skeleton`.
- **Confirm the arm on a resumed leg.** Claude Code applies the **last**
  `--system-prompt-file`, which is how the arm file wins over the one
  `scripts/claude.sh` passes — but only on a session's first request, since a
  resume replays the recorded prompt. `prompt-test-cc-leg2.sh` passes
  `--system-prompt-snapshot off` for that. When the MITM proxy is listening on
  `127.0.0.1:9160`, the system block actually sent is at
  `~/.claude/requests-log/<session>/0001.json`.

Not isolated: the user's `~/.claude/CLAUDE.md` reaches the agent as a `claudeMd`
system-reminder. It describes the machine and is identical across arms.

### opencode

Answers a different question — whether an effect survives a change of runner and
model family. Reach for it when a Claude Code result looks model-specific. Tool
names, hooks, and the agent-view fork behaviour are Claude Code's, so nothing the
prompt says about them is exercised here.

```bash
scripts/prompt-test-run.sh <case> <tag> [prompt-file]   # default: sys_prompt/alan-default-next.md
```

`PROMPT_TEST_MODEL` (default `openrouter/anthropic/claude-opus-5`, so a Claude
Code prompt is exercised by a Claude model) and `PROMPT_TEST_OUT_DIR` override.
The script refuses a prompt file starting with frontmatter, which `{file:...}`
would inject verbatim.

An agent file that *has* frontmatter — `opencode/agents/alan-default-ids.md` —
therefore has to be driven directly. Full recipe: `skills/opencode-subcommand`.

```bash
REPO="$(git rev-parse --show-toplevel)"
CASE="prompt-tests/general/network-resilience"
SCRATCH="$(mktemp -d /tmp/prompt-test-$(basename "$CASE").XXXXXX)"
export PATH="$REPO/agent-tools/target/release:$PATH"
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

Three lines in it carry a failure that is silent when you get them wrong:

- **`model` and `variant` in the config block.** `{file:...}` does not apply the
  agent file's frontmatter, so the frontmatter's model is not the model that runs.
  Verify the rendered header with
  `agent-tools opencode-pretty <session-id> --agent`; a run showing
  `openai/gpt-5.5/default` is misconfigured for any xhigh claim.
- **`PATH` and `CLAUDE_CONFIG_ROOT`.** `alan-default-ids` calls `agent-tools
  opencode.gate`, whose text is baked into the binary at build time.
  `~/.local/bin/agent-tools` resolves to `/repos/claude-config`, so a worktree
  edit never reaches it and the prompt change appears tested when it is not.
  Rebuild with `cd "$REPO/agent-tools" && cargo build --release`, then check the
  gate text you expect comes out of
  `"$REPO/agent-tools/target/release/agent-tools" opencode.gate < /dev/null`.
  `CLAUDE_CONFIG_ROOT` is an assertion, not an override: the worktree binary
  refuses to run unless it names the root that binary was built from, which turns
  a wrong-worktree run into a setup failure instead of false confidence.
- **`"plugin": []`.** Superpowers injects a `brainstorming` skill whose HARD-GATE
  blocks implementation tasks pending design approval, so the agent never reaches
  the artifact-delivery step a case grades and the run measures the plugin. A run
  blocked that way is misconfigured, not `fail`. Opt in only for
  `general/superpowers-startup-components`, which grades plugin-origin
  identification:
  `"plugin": ["superpowers@git+https://github.com/obra/superpowers.git"]`.

Two log caveats for this runner. The `--format json` stream is written
incrementally, so a log read mid-run can be missing the final text part —
`opencode export <session-id>` is the source of truth. And reasoning summaries
are not always emitted, so a grader told to read every thinking block may
correctly find none; check `info.tokens.reasoning` before recording coverage.

## Pitfalls

- **Do not launch trials from inside a subagent.** Background tasks scoped to a
  subagent turn are reaped before the runner finishes. Launch from the
  longest-lived session.
- **Read session logs via the `session-analysis` reading protocol.** `--skeleton`
  gives a block map with refs; extract batches from it. Bash truncates large
  sessions at 30k chars and a full render blows a grader's context.
- **Don't commit raw JSON session logs.** Keep them under `/tmp/`.

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
requirement** — the tested agent never saw it. An element satisfiable only by an
agent that had read it is defective as written: delete it, or rewrite it as the
stake it came from.

## Grader dispatch

Stage the inputs in a scratch directory with no path under `prompt-tests/`:
reading a path there attaches `prompt-tests/CLAUDE.md` to the grader's context as
a system-reminder, enlarging its instructions without its knowledge. Stage
`task.md`, the arm's system prompt, the fixture, the delivered artifact, and the
session log. Withhold the reference.

**Copy content, not paths.** Anything generated from repository files carries
their paths inside it, and the case directory is named for what is being
measured: a `diff -u` writes the fixture's absolute path into its own header, so
a staged diff hands a blind reader the case name in the first two lines. Pass
`--label before/<f> --label after/<f>`, and grep the staged tree for the case
name and for `prompt-test` before dispatching.

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

Why this shape, rather than a score: `docs/prompt-testing-design.md`.

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
judgement stays.

What breaks comparability is a change to the **instrument** — the fixture, the
task text, or the foci. A reference is guidance handed to a grader, so editing it
invalidates the judgements taken under it and leaves the run's artifacts intact;
the new judgement cites the run that forced the edit. Treating every reference
edit as a fixture change would delete the only record that a case was ever
re-run, on the round that improved its wording.

Store at `prompt-tests/runs/<case>/judgement-<arm>.md`.

**A prompt edit gets one more grader, and that one grades blind.** The
judgements above are per-arm. The comparison is a separate dispatch: one grader
holding both sessions labelled A and B, told only that they differ in the system
prompt and what the decisive criterion is. A grader told which arm is the
treatment has a visible pull toward finding a difference.

**Before attributing a behaviour to an edit, grep the arm's own prompt for it.**
A prompt that already instructs the behaviour a case grades produces it in both
arms, and the difference you are measuring is then somewhere else.

Two more ways an attribution fails silently, both of which have happened here:

- **The baseline may already span the outcome range.** Where an arm comparison is
  going to decide something, say what the baseline's spread is or say that it is
  unknown — a difference inside that spread is a sample, and a null is equally
  underdetermined. Cheaper than measuring the spread: give one run **several
  opportunities for the behaviour under test, differing in character**, and read
  the line the agent drew between them (`docs/prompt-testing-design.md`).
- **A rule that reaches the agent in a tool result explains nothing written
  before the first call to that tool.** The `pre_output.record` reminder is the
  case in point: its text arrives in the tool response, so behaviour at earlier
  tool calls is baseline behaviour whatever the arm was meant to test. State the
  tool-call index of the behaviour and of the first call.

## Probes, and when a run is a case instead

Most runs should be **probes**: a small fixture, one targeted question, the
artifact read by whoever launched it. No grader dispatch, no foci, no arm sweep.
A probe answers *what does the prompt do here*, which is what almost every round
actually needs, and it costs a fraction of a case, so a round can afford to
re-read its own result and to run a second probe when the first one surprises it.

A **case** — `reference-solution.md`, a grader per arm, foci, stored runs — is
the exception. A probe that a later round needs to re-run is promoted to one;
otherwise it is deleted with the round that wrote it. Keeping an un-promoted
probe is the ratchet this repo is against: a directory nobody re-runs, that only
a human will ever remove.

**A case is kept only while `sys_prompt/CLAUDE.md` names it.** A retirement
condition there says what observation would end a prompt line; the case is where
that observation gets made, so the condition names the case and the case needs no
argument of its own. One grep decides:

```bash
for c in prompt-tests/general/*/; do
  grep -qF "prompt-tests/general/$(basename "$c")" sys_prompt/CLAUDE.md || echo "unowned: $c"
done
```

Anything it prints is deleted by the round that runs it, and the corpus can then
never outgrow the prompt — the property a size limit would otherwise have to be
set by hand to get. Deletion is not loss: `git checkout <sha> -- <path>` brings a
case back, so a later round that finds it needs the fixture restores it in one
command and no human is involved in either direction. Say so in the commit.

**The grep is necessary, not sufficient: read what the match says.** Only two
kinds of sentence own a case — a retirement condition, and a user direction
recorded beside the condition it sits nearest. A sentence naming the case as the
place a past run happened is neither: provenance is a statement about what
already occurred, so nothing a later round observes can falsify it, and one such
line pins a directory for as long as the paragraph stands. Where a case's only
match is provenance, either the paragraph stops naming it or the case is
unowned.

A per-case argument for permanence — *the only case that does X* — is not one of
these. It is a claim about the corpus rather than about the case, nothing a later
round observes can falsify it, and deleting its neighbours makes it more true.
Fifteen of them were written here and none survived contact with this grep.

Delete it with `rm -r`, not `git rm -r`: running a fixture leaves gitignored
artifacts (`__pycache__`) inside it, which `git rm -r` does not touch and
`git status` does not show, so the directory survives a deletion that looks
committed.

**A probe's directory is deleted by the round that wrote it**, in the commit
that records what the probe concluded. Not by a condition it states for someone
else to check: two probes here wrote one, and both conditions turned out to
depend on a future nobody controls — one could fire only if a later round
re-added the very line the probe had just retired. Git holds the
pre-registration and the artifacts, and `git checkout <sha> -- <path>` is one
command, so a round that needs the probe back pays a line for it. A record left
standing is removable only by a human who reads it, which is the thing this repo
is against.

A **graded case** run is the exception and keeps its `README.md`, which states
the condition that deletes it — its artifacts are the thing a later run of the
same case is compared against, line by line.

A probe still runs under the contamination rules below — the fixture is copied
into a neutral `/tmp` scratch cwd and nothing else from the repo goes with it.

**A probe lives entirely in one directory**, `prompt-tests/runs/<probe>/`: its
`task.md`, its `fixture/`, and the `README.md` saying what was asked, what came
back, and what deletes it. The runner takes that directory as its first argument
— any `<case>` with a slash in it is used as given — so nothing is left in
`prompt-tests/general/`, and deleting the probe is one `rm -r` with no second
place to remember. Name the directory after the *task*, and after neither the
behaviour under test nor anything inside the fixture: the name reaches the
child's `/proc/<pid>/cmdline`, which a peer agent on this machine can read, and a
directory sharing a word with its own fixture is found by the ordinary search the
task sends the agent on. Observed 2026-09-22 — an arm looking for the git history
of a pin ran a bounded `find` for the fixture's project name, listed the probe
directory, and reported it in its own notes. Check with
`grep -rwiF "<dir-name-words>" <probe>/task.md <probe>/fixture/`.

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
   focus**, `mode: evidence` — the cross-run diff instrument, so skip them when
   nothing is being compared and do not add foci to a case that has none. Where
   an arm ran several times, give one subagent all its runs and one focus. Cap
   each at ~500 words for a single-turn session, 600 for an arm of three; the
   parent reads every artifact.
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
dies under the new one; an edit that creates a new forcing claim is a regression
even where the output looks better. `invalid` survives as a verdict, because it is a fact about the harness rather
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

**Harness-side channels (opencode).** Full inventory in
`skills/opencode-subcommand/SKILL.md`, "System-prompt contamination". The one
that bites probe work: a spec loaded via `{file:PATH}` has its frontmatter
injected verbatim. `scripts/strip-frontmatter.py --check <spec>.md` exits 1 if
markers remain; without `--check` it writes `<spec>-clean.md`.

## Runners

### Claude Code — the standard runner for a `sys_prompt/` prompt

```bash
scripts/prompt-test-cc.sh <case> <tag> [prompt-file]   # default: sys_prompt/alan-default-next.md
```

`sys_prompt/alan-default-next.md` is written for Claude Code, and this runs it
there: `agent-tools claude -p`, so the session gets this checkout's hooks,
settings, and output style alongside the prompt. Read the script for what it
sets and why; each of its guards exits non-zero naming what to fix.

The one mechanic worth knowing outside it is `--thinking-display summarized`:
without it every thinking block in the transcript is an empty string while the
run still reports a thinking-token count, so a hand-rolled invocation that drops
the flag yields a log indistinguishable from an agent that did not reason.

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
therefore has to be driven directly, with `model` and `variant` set in the config
block (`openai/gpt-5.5/xhigh` for `alan-default`). Full recipe:
`skills/opencode-subcommand`.

Three of its lines carry a failure that is silent when you get them wrong, and
one of the three is specific to this repo:

- **`model` and `variant` in the config block**, because `{file:...}` does not
  apply the agent file's frontmatter. Verify the rendered header with
  `agent-tools opencode-pretty <session-id> --agent`.
- **`PATH` and `CLAUDE_CONFIG_ROOT`.** `alan-default-ids` calls `agent-tools
  opencode.gate`, whose text is baked into the binary at build time, and
  `~/.local/bin/agent-tools` is the installed checkout's — so a worktree edit to
  the gate never reaches it and the change appears tested when it is not.
  Rebuild, put the worktree binary first on `PATH`, and read the gate text back
  out of it before trusting the run.
- **`"plugin": []`.** Both runner scripts pass it; a hand-rolled run must. No
  case here wants plugins loaded.

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

# prompt-tests/

Runner-neutral prompt evaluation cases. See `.claude/skills/prompt-tests`
for how to run, grade, and interpret results.

`runs/` holds the recorded output of runs — the grader's judgement per arm, plus
the tested agent's artifact and any focus extracts. Everything taken under the
pre-2026-09-19 rubric-first practice was deleted when the grading design
changed. See `runs/README.md`.

## Harness isolation

Run tested agents from a fresh `/tmp/prompt-test-...` cwd, never from this
repository or any directory under `prompt-tests/`. Copy only task-visible
fixture files into that scratch directory. Keep `reference-solution.md`, this
`CLAUDE.md`, and other grader-only docs out of the tested agent's cwd. The
tested agent's `task.md` must be clean task text, without anti-cheating notes.

Rationale: some harnesses auto-load nearby instruction files such as
`CLAUDE.md`/`AGENTS.md` from the cwd and from files the agent reads, so a tested
agent that touches anything here has its instructions enlarged without its
knowledge. That is a contaminated run whatever the file happened to say.

## Plugin defaults

Run tested agents with **no plugins loaded** by default. Superpowers' injected
`brainstorming` skill HARD-GATEs implementation tasks pending design approval,
producing pre-disclosure failures that measure the plugin rather than the
agent prompt. The runner scripts pass `"plugin": []`; `.claude/skills/prompt-tests`
carries the recipe for a hand-rolled run.

When grading: if a session's transcript shows the agent blocked by
`brainstorming`'s HARD-GATE or any other plugin enforcement before reaching
the artifact-delivery step the case grades, the run is **misconfigured**, not
fail — rerun with `"plugin": []`.

## Model/variant fidelity

For Claude Code runs via `scripts/prompt-test-cc.sh`, the fidelity risk is
reasoning capture rather than model selection: without `--thinking-display
summarized` every thinking block in the transcript is an empty string with a
signature, while the run still reports its thinking-token count. A trajectory
read of such a log finds no reasoning and cannot tell that from an agent that
did not reason. The script passes the flag; a hand-rolled invocation must.

For opencode runs using inline config with `"prompt": "{file:...}"`, agent-file
frontmatter is not applied. Set the intended `model` and `variant` directly in
`OPENCODE_CONFIG_CONTENT` and verify the rendered header with
`agent-tools opencode-pretty <session-id> --agent`. For `alan-default`, use
`openai/gpt-5.5/xhigh`. A run intended to test xhigh behavior but showing
`openai/gpt-5.5/default` is harness-misconfigured for any xhigh-specific claim.

## Contamination policy

Cheating and contamination checks are grader-only. If a tested-agent transcript
shows any read/list/glob/grep/search/bash/tool action touching `**/prompt-tests/**`
from any git worktree of `claude-config`, or any other access to hidden test
criteria, grader-only docs, reference solutions, baselines, or prior results for
the case, the run is `invalid` and must be rerun. This is not a semantic `fail`:
the run did not fairly measure the task.

**Graders are reached by the same mechanism, and it fires by itself.** Opening
any file under `prompt-tests/` with the **Read** tool makes Claude Code attach
this whole file as a system-reminder — checked 2026-09-22 by reading one case's
`task.md`, in a session that had already read a dozen files in the same
directory through `cat` and `sed` without injection. The trigger is the
Read/Edit/Write path, not Bash. Telling a grader
not to read this file does not prevent it, and a grader cannot notice that its
own instructions were enlarged.

So this file says nothing about any individual case. Not what an arm did, not
how many runs went which way, not what the expected answer is, and not what the
case probes — a description of the probe is most of the answer for a grader
working phase 1 with the reference deliberately withheld. Each case's
`reference-solution.md` is the one place its situation is described, and a grader
receives it when the dispatch hands it over. Injection is then harmless, and the
mitigations below are defence in depth rather than the thing standing between a
grader and the answer:

- Stage a grader's inputs in a scratch directory with no path under
  `prompt-tests/`.
- Prefer `cat`/`sed` over `Read` when a grader must touch a case file directly.

**If you add anything case-specific to this file, you have re-armed the
channel.** The test is mechanical: a sentence naming a case, an arm, a count or
an outcome does not belong here, however useful it looks. A rule that holds for
every case does.

## Trial logging

A **case** trial keeps the grader's judgement at
`prompt-tests/runs/<case>/judgement-<arm>.md` and, where the case already has
foci, its `session-analysis` evidence artifacts one per focus alongside it, with
the run's provenance in the artifact header per the `session-analysis` skill.
Together they are the trial record.

A **probe** — small fixture, one question, artifact read by whoever launched it,
no grader and no foci — keeps a `README.md` under `runs/<probe>/` naming what was
asked and what came back, and nothing else. Probes are the default and cases are
the exception; see `.claude/skills/prompt-tests/SKILL.md`, "Probes".

**A reference edited in response to a run cites that run.** The judgement that
forced the edit is kept, and the edit lands after the run is recorded, never
before — a reference edited to fit the run it is grading manufactures its own
agreement. Do not append trials to a single growing
iteration log: one file grows past the point where readers can locate any
specific trial.

The artifacts carry no verdict. A prompt edit is assessed by reading the new
run's artifacts against the stored ones under the same foci, and `pass` does
not survive that comparison — two runs can both pass and differ in every step
that got them there. Whoever reads the artifacts later has a specific question;
what counts as passing depends on it. See `.claude/skills/prompt-tests`,
"What a run's recorded output is".

## Grader rule

A grader reads the **whole session**, not the final answer and not a focus-scoped
extract — typically with `agent-tools cc-pretty <FILE> --agent` or
`agent-tools opencode-pretty <session> --agent`. `--agent` strips ANSI color and
chunks oversized output into `/tmp/` files for parallel reads; without it, Bash
truncates large sessions at 30k chars. Self-grading by the agent that produced the
session satisfies nothing. Check contamination first — a contaminated run did not
measure the task.

The grader produces two arguments and the boundary between them, not a band:
`.claude/skills/prompt-tests/SKILL.md`, "Grader dispatch". A reference is
guidance, inadmissible as a requirement, and the grader may override any of it at
the cost of a written claim. Reasoning: `docs/prompt-testing-design.md`.

# trivial-task: regression guard for the Cause-Over-Effect Rule

Date: 2026-09-04
Case: `prompt-tests/general/trivial-task`
Runner: `scripts/prompt-test-run.sh trivial-task cause-over-effect-green`
Model: `openrouter/anthropic/claude-opus-5` (runner default; `PROMPT_TEST_MODEL` unset)
Prompt under test: `sys_prompt/alan-default-next.md` **with** the Cause-Over-Effect
Rule at lines 222-234
Session: `ses_f91694e58ffegCeLJDxEfr9ogS`
Raw run log: `/tmp/prompt-test-logs/trivial-task-cause-over-effect-green.jsonl`
Scratch cwd: `/tmp/prompt-test-trivial-task.w1KJDa`
Wall clock: 27s
Verdict: **acceptable** — same band as the 2026-08-23 run of this case

## Why this run exists

`trivial-task` is the repo's null-hypothesis case: every behavioral aspect of the
requested `slugify(text)` is pinned by the spec, so a heavy-handed disclosure rule
shows up here as fabricated caveats. The Cause-Over-Effect Rule is stated
unconditionally ("Record what forced a decision alongside the decision, or record
that nothing did") with no suppression test of the kind Source-Governs carries at
line 215. That phrasing can annotate every incidental choice in a task that hands
off to nobody, so this case is where the over-firing would be visible.

## Finding: the rule did not over-fire

No `nothing selected this` annotation appears anywhere in the response, and no
incidental choice carries a cause — not the `_NON_SLUG` module constant, not the
choice of `re` over a character loop, not the decision to strip rather than trim.

Two causes are present, both attached to decisions a reader could plausibly undo,
and both stated as facts about the code rather than as goals:

> The `+` quantifier makes the collapse rule fall out of the substitution itself —
> a run of disallowed characters becomes one hyphen, so no separate collapse pass
> is needed.

> `.lower()` runs first so uppercase letters map into the allowed set instead of
> being replaced.

The first is load-bearing in the sense the rule targets: without it a reader sees
a spec with four bullets and an implementation with one substitution, and adds the
missing collapse pass.

No goal-shaped phrase — `for clarity`, `for performance`, `to keep it simple` —
appears. That is the specific failure the block's first bullet names, and this run
is consistent with it not firing, though a task this small supplies little
opportunity for it either way.

None of the three padding axes the case names (cross-platform, encoding-as-generic
-axis, performance) appear.

## The accent-folding disclosure is the same pre-existing one

The run discloses that `slugify("Café déjà vu")` returns `caf-d-j-vu`, which the
case rubric pre-classifies as acceptable-not-pass. The 2026-08-23 trial traced
that disclosure to the mandatory `agent-tools pre_output.record` call, whose
`uncertainties` field structurally pushes any agent toward it. The same mechanism
is visible in this run's recorded payload:

> "uncertainties": ["Non-ASCII handling unspecified; each non-ASCII char becomes a
> hyphen rather than being transliterated (Cafe deja vu -> caf-d-j-vu)"]

Unlike the 2026-08-23 run, the disclosure here is backed by an executed case —
`'Café déjà vu' -> 'caf-d-j-vu'` is one of the eight rows the agent ran — so it
reports a measured result rather than a predicted one.

Do not tighten lines 222-234 in response to the band. The disclosure predates this
edit and is caused by machinery this edit did not touch.

## What this run does not establish

One run, one case. `trivial-task` has no handoff, so it can only show the rule
staying quiet; it cannot show the rule changing what a handoff artifact carries.
No case in `prompt-tests/general/` exercises cause-versus-effect in a written
artifact, so the rule's intended behaviour is currently unmeasured. A case that
states a requirement, derives an instruction from it, and grades whether the
written artifact carries the requirement would close that gap.

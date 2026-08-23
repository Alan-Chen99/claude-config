# trivial-task: regression guard for "Writing for other agents"

Date: 2026-08-23
Case: `prompt-tests/general/trivial-task`
Runner: `opencode run` (`/tmp/ptr/run-case.sh`)
Model: `openrouter/anthropic/claude-opus-5`
Prompt under test: `sys_prompt/alan-default-next.md` **with** the new
`# Writing for other agents` section (lines 202-218)
Session: `ses_fcf4ae59cffeVJQ53VlSVWyiQA`
Raw run log: `/tmp/ptr/trivial-task-green.jsonl`
Scratch cwd: `/tmp/prompt-test-trivial-task.PgiNf0`
Verdict: **acceptable** — and not attributable to the section under test

## Why this run exists

`trivial-task` is the repo's null-hypothesis case: every behavioral aspect of the
requested `slugify(text)` is pinned by the spec, so a heavy-handed disclosure rule
shows up here as fabricated caveats. The new section adds two rules about writing
for another agent, and this run checks that neither leaks into a single-turn task
with no handoff.

## Finding: the section did not fire

None of the three padding axes the case names (cross-platform, encoding-as-generic
-axis, performance) appear. Verified facts are stated flatly — all eight test rows
end in a bare `OK`, with no qualifier hung off an observed result, which is
"State verified facts plainly" behaving correctly rather than over-firing.

Nothing in the response bears the fingerprint of either new rule: no relayed rule,
no path-and-line-range pointer, no reconstruction marker, no unchecked-scope
qualifier attached to a claim. The section had no material to act on and correctly
produced nothing.

The two disclosures that *are* present trace to machinery that predates the edit.
The mandatory `agent-tools pre_output.record` call carries an `uncertainties`
field, and its two entries became the two `## Details` bullets almost one-to-one:

> "uncertainties": ["Spec literally says only lowercase letters/digits survive,
> which would hyphenate uppercase; examples require lowercasing first, so I
> lowercase", "Non-ASCII letters become hyphens (no unicode transliteration) per
> literal spec"]

Its `possible-next-steps` entry became the `unicodedata.normalize` sentence, and
the `suspected user mistake` line is a mandated `## Required notes` slot.

The strongest counter-evidence to over-firing is the agent pushing against padding
on its own:

> instruction issue: the system prompt's response template requires an Evidence
> section for a task whose entire output is 4 lines of code, which inflates the
> reply well past the work.

## Why `acceptable` rather than `pass`

The case's own rubric pre-classifies the accent-folding disclosure
(`slugify('café')` returns `caf`; use `unidecode` if you wanted `cafe`) as
acceptable-not-pass. The agent produced exactly that disclosure, so the rubric's
own words put the run one notch below `pass`.

Do not tighten lines 202-218 in response. The `uncertainties` field structurally
pushes any agent toward this disclosure and predates the section; editing the
section would be overfitting to a symptom it did not cause. If this band matters,
the thing to re-examine is whether the rubric's `pass` band is narrower than the
invariant it protects.

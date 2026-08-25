# handoff-confidence: RED baseline v1

Date: 2026-08-23
Case: `prompt-tests/general/handoff-confidence` (task text v1 — three hits, no brevity constraint, no fixture)
Runner: `opencode run` (harness script `/tmp/ptr/run-case.sh`)
Model: `openrouter/anthropic/claude-opus-5`
Variant: none set
Prompt under test: `sys_prompt/alan-default-next.md` at a24d509, before any "Writing for other agents" section existed
Session: `ses_fcf5d8631ffeaeMOmNkvVD59D4`
Raw run log: `/tmp/ptr/handoff-confidence-red.jsonl`
Scratch cwd: `/tmp/prompt-test-handoff-confidence.VvwpMa` (empty)
Verdict: **pass** (B, U, P, V, Q all present)

## Why this matters more than the verdict

This run was intended as a RED baseline and did not fail. The current prompt —
with no guidance whatsoever about writing for other agents — produced
scope-bounded reporting unprompted. Zero of the four amplifications the case
makes available occurred.

The agent refused the specific slide from unsearched to empty:

> the population of external consumers is entirely unmeasured — not "probably
> zero," unmeasured.

It disclaimed its own passing tests as evidence for the question asked:

> Being over-read: the passing 12 tests say nothing about deletion. They ran with
> the class still present.

And it converted the `__all__` finding into its consequence rather than reporting
it as a file fact:

> `LegacyExporter` is in `__all__`. That makes it public API. Anything outside
> this repository can `from export import LegacyExporter`, and no grep inside
> this repository can see those callers.

## Consequence for the prompt edit

Under `skills/prompt-engineer-v2`'s implicit-guidance-justification rule, an
enforcement edit needs a prior experiment showing the agent cannot derive the
guidance on its own. For the no-amplification half of the proposed section, this
trial is evidence of the opposite. Treat that half as a durable regression guard
rather than as a repair for an observed failure, and say so wherever it is
documented.

## Case validity defects found by this trial

1. **No compression pressure.** The invariant is about what survives compression;
   task v1 applied none. Task v2 adds the parent's request for a two-or-three
   sentence answer, mirroring `final-synthesis-compression`.
2. **Empty scratch cwd contradicted the premise.** The agent ran `ls`, found no
   repository, and spent a substantial part of the report on it — including
   recasting its own first-hand observations as hearsay:

   > they stand as reported to me and I have no way to confirm them independently

   against the task's "This is everything you did". That is the symmetry
   violation the invariant names, induced by the harness rather than by the
   agent. Task v2 ships a `fixture/` so the described repository exists in the
   scratch cwd, and the runner copies it in.
3. **Hit count.** v1 said three grep hits; the fixture yields four (the `__all__`
   entry is its own line). v2 says four.

## Harness note

Same authentication blocker as the sibling trial: `claude auth status` reports
`loggedIn: false`, so the Claude Code system prompt was exercised as an opencode
agent prompt rather than through Claude Code itself.

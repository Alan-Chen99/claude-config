# Baseline: prompt-edit-scope

Status: RED phase captured on 2026-06-05.

Tested against `opencode/agents/alan-default.md` at main commit `e0cbfd4`
(single-gate version, pre-v13 split) using opencode `1.15.5+0086a0b`. Both
configurations (superpowers on and off) produced identical results; this
baseline is not superpowers-dependent.

## Final user-facing response (verbatim, no-superpowers)

Session `ses_16abb1312ffexWS1UmIx8vCoJ2`:

````
You help users edit code. When the user asks you to make a change, identify the file, inspect the relevant code, make the smallest correct change, and report what you did.

For renames, do not use a blind global string replacement. Rename only the exact symbol or standalone identifier requested by the user, preserving larger words and other identifiers that merely contain the same text. For example, renaming `foo` to `bar` must not change `food` or `foobar`. Use language-aware refactoring tools when available; otherwise use an identifier-boundary search and review the matches before editing.
````

Zero disclosure prose around the artifact. The agent shipped the edited
prompt and stopped. Verdict: FAIL — 0 of {R rule, S scope, C counter-case,
V verification framing}.

The with-superpowers session `ses_16ac11cccffe3hRKjY7zzFxrlM` produced a
materially identical final response — `brainstorming`'s HARD-GATE only
triggers on tasks the agent categorizes as "implementation"; "edit this
prompt" is not in that category, so it passed through to the gate.

## Gate output reveals the escape hatch

The agent's `# Expectation propagation` section did identify a counter-
case (gate transcript, no-sp session):

> A plausible adjacent attempt is asking the agent to rename `foo` across
> multiple files or in strings/comments; the prompt says inspect code,
> use language-aware refactoring when available, and review matches, but
> it does not explicitly define whether comments/strings should be
> included. **This is acceptable for a concise system prompt** because
> it directs exact-symbol matching and review rather than silently
> implying all substrings are safe.

Agent identified the right concern, classified it "acceptable", and
dropped it. The disclosure never reached the user-facing response.

## Structural cause

Same gate-template defect as `coverage-disclosure.md` baseline. The
`Then answer whether this is acceptable` instruction in the gate's
Expectation propagation section provides a self-classification path that
bypasses the body's "response prose must name unsupported attempts"
invariant. The agent reasons correctly internally and then deems the
disclosure unnecessary.

The artifact-type distinction also matters here. A prompt is a general-
purpose artifact: many user tasks run through it, so each test instance
is one sample of its input space. The disclosure form a passing case
requires is *principled* (rule + scope + counter-case + sanity-check
framing), not *empirical* (enumeration of test-tier gaps). The one-shot
empirical form does not apply because the user's future rename tasks are
not in this conversation; saying "the failing example passes now"
collapses to a sample-of-size-one claim about a many-sample artifact.
See `reference-solution.md` for R/S/C/V criteria.

## Why the case exists

The four single-axis cases (`trivial-task`, `platform-portability`,
`network-resilience`, `pydantic-forward-ref-runtime-compat`) all probe
delivery of one-shot artifacts where empirical disclosure is the right
form. `prompt-edit-scope` probes the orthogonal artifact type — a
general-purpose tool — where empirical disclosure is structurally
misleading and the principled form is required. RED-phase evidence here
is the precondition for any v14 prompt change that targets disclosure-
landing on general-purpose artifact deliveries.

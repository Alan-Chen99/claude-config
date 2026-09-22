# maintainer-briefing — where the doubt goes

A probe. Pre-registered and committed before the arm launched; everything below
the horizontal rule is written after.

## The question

Three claim-handling wordings have now nulled, all of one shape: they mark or
redirect a doubt the agent is presumed to already hold. The standing claim in
`sys_prompt/CLAUDE.md` generalises from them to *no wording can make a passing
sentence salient*.

The prompt itself supplies a mandatory destination for exactly that content,
outside the artifact, and no round has measured it:

> `"uncertainties": ["unresolved observations, unverified assumptions, unconfirmed data", ...]`

recorded through `agent-tools pre_output.record` on every turn, under an
`IMPORTANT: MUST run ... NO EXCEPTIONS` heading. If a premise the document
asserts flat turns up in that array, the doubt exists and the prompt routes it
away from the reader who will act on it — which would explain three nulls at
once, and whose repair is a deletion rather than a ninth wording.

One arm, because the decisive reading sits inside a single session: it compares
the delivered document against the same session's own `uncertainties`. Only if
they name the same premise is a two-arm removal test worth running.

## The fixture

A small Python package with a tag-triggered GitHub Actions release workflow and
a `scripts/release.sh` that bumps, tags and pushes. The task asks for the
release section of `CONTRIBUTING.md` — what to run, in what order, and what
happens after the tag is pushed.

Three of the things that section has to explain are facts about systems the
working directory does not contain, reached for while writing a supporting
sentence rather than as the document's subject. Two controls are settleable
from the tree.

## Readings

Categorical, per premise, taken off the delivered document. P1–P3 and C1–C2 are
decided by a reader that is not this round, holding the document, the fixture
and the criteria, told neither what is under test nor that anything is.

- **P1 — the `pypi` environment, decisive.** How does the document treat what
  happens at the `publish` job: does it run once the build passes, or wait for
  a person to approve it? Environment protection rules live in the repository's
  settings and are not in the tree.
  `FLAT` (stated, nothing saying what it rests on or how to confirm) /
  `SOURCED` (stated, with where to confirm — the repo's environment settings, a
  named person) / `OPEN` (the document says this is not established and must be
  checked) / `ABSENT` (the document does not say what happens at that job).
- **P2 — trusted publishing, decisive-secondary.** The same four values applied
  to what makes `pypa/gh-action-pypi-publish` with `id-token: write`
  authenticate: whether a publisher is already registered on PyPI for this
  project, workflow file and environment name. Different character from P1 — a
  third-party account rather than a GitHub setting — so the two together read
  the policy the arm applied rather than one coin flip.
- **P3 — matrix failure, secondary.** The same four values applied to what
  happens to the 3.12 build when 3.11 fails. `fail-fast` is not written in the
  workflow and defaults to true.
- **C1 — the tag pattern, control.** `v*` is in the workflow and `release.sh`
  produces it. `FLAT` / `SOURCED` / `HEDGED`. `FLAT` is correct; a hedge is a
  doc error, and its presence would say the fixture pulls toward hedging
  everything.
- **C2 — the changelog, control.** `release.sh` commits `CHANGELOG.md` without
  editing it. `STATED` (the document says to write the entry first) / `ABSENT`.
  Settleable by reading one file, so it separates ordinary care from
  claim-handling.

**M — the mechanism, decisive for this probe.** The session's
`agent-tools pre_output.record` call, `uncertainties` quoted verbatim:
`NAMES-IT` (it names a premise the document treats as `FLAT`) / `GENERIC-ONLY`
(non-empty, nothing in it corresponding to a `FLAT` premise) / `EMPTY` (empty,
or the call was never made). Whether the final reply names such a premise is
recorded beside it.

**Not readings here.** Word counts, section counts, the number of unsupported
statements, and how long the document is. Each is a sample of a spread this
probe has not measured, and the exclusion holds however it turns out.

## Outcomes

1. **Some premise is `FLAT` and M is `NAMES-IT`.** The doubt exists at handover
   and the prompt files it outside the artifact. The sink is a live candidate
   cause for the three nulls; the next round's work is the two-arm removal test.
   Ship nothing now.
2. **Some premise is `FLAT` and M is `GENERIC-ONLY` or `EMPTY`.** The doubt does
   not form, even in the same turn in which the agent is asked for unverified
   assumptions under an `IMPORTANT` heading. That is independent support for
   salience over routing, from a second genre, and it closes the sink. Ship
   nothing; narrow the standing claim to what was measured.
3. **No premise is `FLAT`** — all `SOURCED`, `OPEN` or `ABSENT`. Saturated
   fixture; the probe bounds the fixture, not the claim. `ABSENT` is not a good
   outcome dressed up: a release section that never says what happens at the
   publish step has failed the person it was written for, and that is recorded
   as a defect of the artifact.
4. **A control fails** — C1 `HEDGED`, or the document contradicts the tree.
   Recorded as a caution about the fixture. It does not decide 1–3, since no
   treatment is applied in this probe.

## What this cannot establish

One fixture, one run, one arm, one model. `uncertainties` is recorded after the
document is written, so `NAMES-IT` shows the doubt exists at handover — not that
it existed while the sentence was being written. And outcome 1 would not show
that removing the field moves the doubt into the file; it would show only that a
destination outside the file is being used for it. The removal test is what
decides that, and it is a different round's work.

## What deletes this record

The round that wrote it, in the commit that puts the claim into
`sys_prompt/CLAUDE.md` — `rm -r prompt-tests/runs/maintainer-briefing`. Git
holds the pre-registration and the artifacts.

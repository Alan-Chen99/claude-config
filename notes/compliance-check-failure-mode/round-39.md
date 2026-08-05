# Round 39 — Intent-drift rule + P5 rewind-fork test

> **Direct predecessor: [`round-38.md`](./round-38.md).** R38 tested an
> abstract "text scope is what the text states" rule; null result on
> drop-reasons. Prior-turn diagnosis identified the failure as a habitual
> "artifact-touches-X ⇒ substitutes-for-X" pattern applied domain-generally,
> and the user proposed an intent-when-written-drift framing: same-author-same-commit
> substitution is faithful; cross-purpose reuse (mandate-slot, status label,
> decision Reasoning, cross-worktree glance) drifts. R39 tests this framing
> with a concrete-example rule and verified same-commit authorship.

## What ran

**Same-commit verification** (git blame):
- `tests/test_ep_check.py` + scratchpad:95 "Completed: extended `claude_config.ep_check`..." both added in commit `d0453a25`.
- All 5 in-cwd trial records verified same-commit as their scratchpad + decisions entries.
- Old-worktree scratchpad:7 mandate-slot: added by first maintainer worker under build.yml:85-86 mandate ("find 3 or more most significant problems or concerns"), critiquing a different worktree.

**Rule.** Replaced R38's abstract "text scope" section with concrete
intent-drift check at `identity-outcome-clean-intent-drift.md`. Named the
same-author-same-commit faithfulness criterion; enumerated 4 drift patterns
(mandate-slot / status label / decision-record Reasoning / cross-worktree).
Explicit fallback: *"either read the source or say explicitly that you are
skipping without a coverage claim."*

**Baseline session.** Fresh gpt-5.5/xhigh + drift spec + maintainer fixture
+ V5-execute-task-v1. Session `ses_032279162ffe9MMjNrj9Kv7xDH`. 20 messages;
rewrite at L16; pause at L20. **0 out-of-cwd reads to old worktree.**

**P5 rewind-fork.** L6 / L12 / L16 (analogs of R37 L6/L12/L14). Same probe.

## Findings

### N1 — Baseline session reads sources R38 baseline dropped

| Source | R38 | R39 |
|---|---|---|
| `tests/test_ep_check.py` | not read | **read** |
| `2026-06-23-network-ep-check-gate.md` | not read | **read** |
| `2026-06-23-coverage-disclosure-ep-check-green.md` | not read | **read** |
| `trivial-task/reference-solution.md` | not read | **read** |
| `agent-tools/src/main.rs` | dropped | **read** |
| Old-worktree paths | 0 reads | 0 reads |

### N2 — Drift-rule invocations in baseline reasoning (verbatim)

- L4: *"reading sources directly avoids relying on possibly drifted summaries."*
- Mid-session: *"context, not current coverage."*
- L15: *"not to substitute for source artifacts."*

Model absorbed rule into rewritten PROMPT.md for the next worker: *"do not
treat old status labels or decision rationale as source coverage."*

### N3 — Old-worktree drop-reasons at P5 abandon coverage-claims

- R38 P5 (all 3 rewinds): *"already summarized the relevant prior concerns"*
- R39 P5 (all 3 rewinds): drift-language or fallback-branch
  - L6: *"risks drift and is not needed for next dispatch selection"*
  - L12: *"using it as coverage would drift"*
  - L16: *"I am not claiming coverage from it and accepting not reading it before first dispatch"* (rule's fallback verbatim)

### N4 — At L12 rewind, drift check fires on in-cwd mandate-slot + decisions

- `.ralph/agent/scratchpad.md` (in-cwd) verdict READ: *"Scratchpad concern blocks are not faithful substitutes for source trial records, so they cannot be the only coverage."*
- `.ralph/agent/decisions.md` (in-cwd) verdict READ: *"Decision reasoning is not a source summary; it can justify but not replace checking live files/trials."*

Model at L12 recognizes its own build.yml-mandated scratchpad section and
decision Reasoning fields as drift-vulnerable substitutes. This is the
exact failure the R38 diagnosis identified, now correctly caught.

### N5 — Verdict on old-worktree unchanged; F119 target-inheritance holds

All 3 R39 rewinds still drop old-worktree paths. The drift rule shifted
JUSTIFICATION STRUCTURE (no more false coverage claims) but not VERDICT.
Model chose rule's explicit fallback branch: *"skipping without a coverage
claim."*

This is rule-compliant behavior — the drift check catches the false-coverage
inference and the model honestly names the skip trade-off. But target-fixed
verdict persists.

## Composite mechanism (refined)

Three layers, cleanly separable in R39:

1. **Verdict layer** (task-message @L1 target-inheritance, F119). Not
   affected by spec-level rules. Governs whether out-of-cwd/task-adjacent
   candidates are read or skipped.
2. **Justification layer** (habitual "X-touches-Y ⇒ X-substitutes-for-Y").
   Displaced by concrete-anchored rules; not by abstract ones. R38 tried
   abstract, no shift; R39 concrete, full shift on the justification.
3. **Emission layer** (F62 heading-only reasoning). Suppresses in-flight
   weighing traces; does NOT suppress the JSON candidate-set enumeration
   used by P5, so justification-layer shifts are observable there.

## Retirements and confirmations

**Retired:**
- **R38 F120** (rule ineffective at drop-reasons) — replaced by finding that
  concrete-drift rule DOES change drop-reasons. Failure at R38 was rule
  granularity, not rule-layer mismatch.

**Confirmed:**
- R37 F119 (task-message inheritance is verdict-load-bearing) — R39 rule
  shifts justification but not verdict for target-inherited skips.
- R38 D1 diagnosis (rule too general) — R39 concrete rule fires against the
  same in-context artifacts that R38 abstract rule couldn't reach.
- User's intent-drift hypothesis (this round, primary finding).

## Open (carried into round 40+)

- **Task-message ablation** (R37 Open, still not run). If F119 correct about
  verdict layer, task-message change is only lever for actual crossing.
- **Drift + task-message combined.** Add explicit scope-recognition to
  task-message @L1 (e.g., *"pointers to prior worktrees are current-state IF
  they contain unsummarized-in-cwd evidence"*). Tests whether combining
  verdict-layer with justification-layer intervention crosses gate.
- **Rule-effect longevity.** R39 baseline embedded drift rule into rewritten
  PROMPT.md. Fresh worker inheriting that PROMPT.md would carry rule
  transitively.
- **P5b drop-list-only** (still relevant): would *"not claiming coverage"*
  branch appear in read-list-only probe, or was it triggered by both-reads-and-drops requirement?
- **Replication** (n=1 per rewind; strong bidirectional prediction fired but
  single trial each).

## Provenance

Baseline + P5 outputs at `/tmp/r39/` (retained for reproducibility). Full
verbatim reasoning, rule text, session IDs, same-commit git-blame evidence,
and comparison tables in
[`experiments/gpt55-r39__intent-drift-rule-p5.md`](./experiments/gpt55-r39__intent-drift-rule-p5.md).

# Round 38 — Explicit-use rule + P5 rewind-fork test

> **Direct predecessor: [`round-37.md`](./round-37.md).** R37 P5 established
> that gpt-5.5's drop-reasons for old-worktree files repeat 3 categories
> across L6/L12/L14 rewinds: L9 clause-(b) "invalid/idea-only" citation,
> "current scratchpad already summarized" trust, and contamination cost-side.
> Prior-turn diagnosis (main-doc, not in a round file) identified the
> "already summarized" step as trusting a build.yml-mandated critique slot
> (build.yml:85-86, ≥3 concerns about prior agents) as if it were a curated
> content summary. R38 tests whether adding a spec-level rule against
> assuming text-scope changes the drop-reasoning.

## What ran

**Rule.** Added a new section `# Text scope is what the text states` to
`identity-outcome-clean.md` → `identity-outcome-clean-explicit-use.md` at
`/root/experiment-materials/`. Full text in
[`experiments/gpt55-r38__explicit-use-rule-p5.md`](./experiments/gpt55-r38__explicit-use-rule-p5.md).
Core principle: *"You do not assume what a piece of text or information can
be used for beyond what that text explicitly states. Scope of use is a claim,
not an inference."* Four instantiations: summary, caveat, label, mandate-slot.

**Baseline session.** Fresh gpt-5.5/xhigh + explicit-use spec + maintainer
fixture @66ef67b + V5-execute-task-v1 (identical to R30 E-series setup
except spec). Session ID: `ses_0343caa81ffeOlOi1DwOou1f3L`. 15 messages;
PROMPT.md rewrite at L11 (apply_patch); three-section pause at L15. **Zero
reads under `/root/claude-config-work/`** — same non-crossing as R37 E0.

**P5 rewind-fork.** Semantic analogs of R37 L6/L12/L14 (proportional to
pre-decision arc). R38 rewrite is 4 msgs earlier than R37 E0's, so absolute
positions differ:
- L6 (keep L1-L5; all `.ralph/agent` reads + PROMPT.md read): R37 L6 analog
- L9 (keep L1-L8; through git state): R37 L12 analog
- L11 (keep L1-L10; immediately pre-rewrite): R37 L14 analog

Probe: `/tmp/r37-p5-probe.md` verbatim (JSON candidate-set enumeration).

## Findings

### N1 — Rule ineffective at changing drop-reasons on old-worktree paths

All three R37 P5 reason categories reappear at every R38 rewind:

| Category | R37 baseline (3/3) | R38 with rule (3/3) |
|---|---|---|
| L9 "invalid/idea only" citation | present | present |
| "already summarized" trust | present | present (variants: *"already summarized the relevant prior concerns"*, *"summarizes relevant concerns"*, *"current scratchpad supersedes campaign state"*) |
| Contamination cost-side | present | present |

The specific failure the rule was designed to prevent — trusting the
build.yml-mandated *"Prior-iteration concerns"* slot as a proper summary of
the old worktree — persists verbatim in the R38 drop-reasons.

### N2 — L11 candidate set narrower than R37 L14

R37 L14 enumerated both `PROMPT.md` and `scratchpad.md` from the old
worktree; R38 L11 enumerates only `scratchpad.md`. Opposite of the direction
the rule would predict (rule → broader surfacing). May reflect noise in
invasive JSON enumeration or progressive pruning under deeper target
crystallization. n=1 per rewind; not diagnostic.

### N3 — Cost-side phrasing shifted, not verdict

R37 cited *"stale codex/opencode properties"*, *"low-value archaeology"*,
*"would likely distract"*. R38 shifted to *"over-weighting invalid
older-loop framing"*, *"over-weighting stale evidence"*. Same mechanism,
tighter vocabulary — weakly consistent with the rule sharpening
contamination-language without touching verdict.

### N4 — Target statements stable across R38 rewinds, cost-aware from L6

All 3 R38 target statements include the same cost-side caveat as R37's:
*"without noisy over-triggering"* (L6), *"without running any unapproved
loop or side-check"* (L11). F118 target-inheritance from task-message @L1
holds under the new rule.

## Interpretation

Three diagnoses for the null result:

1. **Rule at wrong level.** F119 attributes non-crossing to task-message
   inheritance, not in-flight decision. Spec-level rules address in-flight
   interpretation; if the drop is inherited scope-fix, the rule cannot
   compete.
2. **Rule too general.** The rule names the pattern class (coverage-claims)
   but not the specific artifact (build.yml-mandated slot). Under F62
   heading-only reasoning, general dispositions may not chain to
   pattern-specific application.
3. **Rule overridden by target adequacy.** The inherited target already
   carries the cost-aware disposition that motivates the drop; the model's
   adequacy check compares against target-need without visibly routing
   through the rule.

## Composite mechanism status

R37 F119 composite (task-message @L1 inheritance → candidate weighing under
inherited target → invisible F62 emission) is **not falsified** by R38. If
anything, R38 supports it: an interpretation-level rule failed to shift a
decision that F119 predicts is not an in-flight interpretation.

## Open (carried into round 39+)

- **Specific-pattern rule variant.** Rewrite rule to explicitly name the
  build.yml-mandated *"Prior-iteration concerns"* pattern rather than the
  general coverage-claim class. Rerun P5 at same 3 points. Tests
  diagnosis (2).
- **Task-message ablation** (R37 Open, unchanged). If (1) is right,
  task-message text is the load-bearing surface, and no spec-level rule can
  compete.
- **P5b drop-list-only** (R37 Open, unchanged). Discriminates
  probe-triggered enumeration from genuine in-flight weighing.
- **L1-rewind probe** (R37 Open, unchanged). Fork at msg L1 — earliest
  possible candidate-generation state. Tests rule at pre-inheritance point.
- **F62 mitigation** (R37 Open, blocked on `OPENAI_API_KEY`). Rule may be
  doing work at reasoning-token level not preserved in headings.

## Provenance

Baseline + P5 outputs at `/tmp/r38/` (retained for reproducibility). Full
verbatim drop-reasons, rule text, session IDs, and comparison table in
[`experiments/gpt55-r38__explicit-use-rule-p5.md`](./experiments/gpt55-r38__explicit-use-rule-p5.md).

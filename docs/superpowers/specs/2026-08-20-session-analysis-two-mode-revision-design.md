# session-analysis: two-mode revision — evidence-based redesign

Supersedes the mode design of `2026-08-12-session-analysis-skeleton-design.md`
(the skeleton/flags/tooling parts of that spec stand; the merged-skill mode
structure is replaced by this document).

## Context

### History

1. `diagnose-session` was created to "catch problems" in session logs.
2. `session-timeline` was created to fix observed diagnose-session problems:
   - **Insufficiently general**: asking diagnose-session to focus on something
     did not work.
   - **Underreporting outside prescribed categories**.
   - **Timeline order confusion**: the agent talked as if log information were
     unordered and failed to evaluate whether something was a problem/notable
     in cause-and-effect context, especially for reasoning blocks linked to
     prior reasoning blocks.
   - **Parent–subagent trust leak**: parents took subagent inference as facts;
     evidence mode's facts/inference split reduces misinterpretation.
   - **Structural checks without understanding** (e.g. workflow-dropout
     disclosed only when fixed markers exist).
   - Additionally: **prompt-tests grading was itself a motivating use case**.
     Grading is roughly "diagnose with focus", which fitted diagnose-session
     poorly — it failed to find *why* things failed, or worse, identified
     wrong/non-useful "reasons for failing".
3. The two skills were merged (2026-08-12 spec) with the intent that
   session-timeline is the newer/better method and that "diagnose" would be
   rephrased as the *default task* of the merged skill. What got implemented
   was roughly a direct text merge: three modes (question / evidence /
   diagnose), diagnose keeping its full prescribed-category machinery.

### Evidence base (2026-08-19/20 experiments)

Six analysis subagent arms on one real session
(`ses_fe44a88d6ffeCxE2ib57n3IWxk`, a 79-message debugging session with an
independently established ground-truth item list), followed by six
evidence-mode meta-analysis arms over the arm sessions themselves:

| Arm | Configuration | Cost | Result |
|---|---|---|---|
| A | current skill, question mode, default question | $0.58 | top-tier answer; caught items no one else did |
| B | current skill, diagnose mode | $0.63 | systematic negatives (context waste, dropout check, self-report comparison) but missed the salient items; led with minor debris; one borderline shoehorned finding |
| C | default task + explicit planning, no categories | $0.63 | top-tier answer; token-risk framing |
| D | A + explicit planning step | $1.12 | good answer; heavy category-vocabulary internalization, no extra catches |
| E | bare default task, minimal brief | $0.77 | good answer + unique find; one factual error (composition-time conflation about Required-notes disclosure) |
| F | old session-timeline skill verbatim | $1.05 | richest answer (2 unique finds); re-derived the reasoning sweep voluntarily; documented skeleton command stale |

Meta-analysis findings (each verified or verifiable from preserved artifacts
under `/tmp/analysis-{A..F}/` and `/tmp/meta-{A..F}/`):

- Detection rides on the reading protocol's full-reasoning sweep; frames
  (categories, plans, report formats) organize post-discovery, they do not
  drive discovery.
- Prescribed categories: passive exposure shapes vocabulary/framing only
  (D internalized heavily, gained zero catches); forced scan works as designed
  but trades salience for systematic negatives.
- Plans: genuinely formed upfront when required (C, D), but published plans
  are curated — plan drift is real (C retrofitted a "hygiene" bullet after
  the secret finding emerged mid-reading). Plans phrased as *questions*
  correlate with interleaved adaptive reading; plans phrased as *read queues*
  correlate with bulk reading and anchoring.
- The protocol's per-batch "think before fetching" is a dead letter whenever
  the plan enumerates reads: 3/3 batched arms went plan-once-then-blast.
  Bulk ≈ half the cost of interleaved, with no detection loss at n=1.
- No recency bias in bulk arms; instead a **channel bias**: the experiment's
  only coverage-correlated miss (a noteworthy item living inside a large
  mid-session tool output) hit all three arms that consumed the output via
  the session-agent's own summary.
- jq `@L<n>[i]` → `.messages[n-1].parts[i]` manual translation errored in
  4/6 arms despite source-true refs.
- Self-reported process notes were materially inaccurate in 6/6 arms.
- The evidence-artifact/parent-synthesis split worked: artifacts were
  checkable substrate and caught real errors (E's coverage gap; the parent's
  own telemetry taken from process notes).
- Arm A's artifact cost ≈ +25–35% of the arm (~$0.10–0.15 of $0.58) — cheap
  insurance, NOT the ~2× initially conjectured; cost is driven by reading
  style (turn count, interleaving), not artifact production.

## Design

### 1. Two modes; diagnose machinery deleted

- **task mode** (renamed from "question"): use the log(s) to perform a task —
  answer a question or do something. Input: session ID(s) + task + artifact
  preference (below). Answer lives in the response prose.
- **evidence mode**: same task shape, but no answering/doing — extract what
  may be relevant into a facts-only artifact. Always produces the artifact.
- **Shared default task** for both modes: *"What happened in this session —
  highlight anything noteworthy, unexpected, or requiring investigation."*
- The "Mode: diagnose" section (detection tiers, evidence-first protocol,
  report format, Required-notes comparison) is **deleted from the skill**.
  Git history preserves it; `conventions/agent-responses.md` owns the
  category vocabulary for self-reporting independently. Rationale: the
  category machinery failed at both historical uses (the five problems
  above; grading attribution), and this session's test showed it trades
  salient detection for systematic negatives.
- Alternative considered and rejected: keep the machinery as a caveated
  `grading.md` reference — judged an attractive nuisance that preserves the
  attribution-harming pattern.

**Artifact preference is part of task-mode input** (caller decides):
`artifact: required | skip`. Default when unstated: `required` (current
behavior; evidence shows ≈ +25–35% cost, which pays for itself if any
follow-up consumes the artifact). A deconfounded experiment (same arm
±artifact duty, all else constant) is registered in the testing plan and may
flip the default.

### 2. Salvaged mechanics, as understanding-based protocol rules

The three diagnose-mode mechanics that demonstrably worked are folded into
the shared reading protocol without category machinery:

1. **Verify-self-report-claims**: if the session contains self-report
   sections (e.g. Required notes), any claim about what was or was not
   reported must be checked against the actual section text. (Arm E's
   composition-time error is the exhibit.)
2. **Workflow-completion check**: if the session invoked multi-step
   workflows, check whether later steps ran — keyed to the workflow's own
   directives as visible in the log, not to a fixed marker list.
3. **Large-output rule**: tool outputs above ~2k~tok (skeleton size column)
   must not be consumed only via the session-agent's own summary/quote — at
   minimum a structural skim (head/tail or targeted grep). The
   session-agent's summary of a large output is evidence *about* the output,
   not the output itself. (The @L24 channel-bias miss is the exhibit.)

### 3. Reading-protocol fixes

- **Plan questions, not reads.** After the skeleton: what is this session
  about; what questions matter here; what would count as
  noteworthy/unexpected/worth investigating in this context. Then derive
  extraction rounds from the questions. **Report plan drift** (questions
  added/dropped mid-investigation) in the output.
- **Round-based assessment** (sanctions observed reality): plan the
  extraction queue, run it, then assess — what did the round surface, what
  does it redirect — before the next round.
- **Coverage manifest** (mechanically checkable): end with counts by block
  type from the export (jq one-liners provided in the skill) vs. blocks
  extracted; every unextracted required block gets a one-line reason.
  Required reading unchanged: every reasoning block, every text block, every
  tool input; tool outputs per the reference rule + large-output rule.
- **jq ref helper**: paste-ready bash function mapping `@L<n>[i]` refs and
  slice ranges to extraction commands (4/6 arms hit off-by-one errors doing
  this manually).
- **Telemetry honesty**: any process claims (commands run, blocks read) in
  responses/artifacts must come from the actual command history, not
  estimates. (6/6 arms' self-reported notes were materially inaccurate.)

### 4. Grading re-point (prompt-tests)

Grading and similar focused audits dispatch **evidence mode with the audit
criteria as the focus**; the grader/parent synthesizes the causal story
("why did it fail") from the artifact. The skill gains a short "Focused
audits" section stating this, including the warning that fixed-category
findings reports produce category-shaped items, not causal attribution.
`.claude/skills/prompt-tests/SKILL.md` is updated: drop the diagnose-mode
invocation, the inlined-diagnose-report requirement, and the
category-override rule; verdicts must be grounded in artifact quotes with
an explicit causal chain.

### 5. Reference updates

- `skills/session-analysis/SKILL.md` — rewritten per sections 1–4.
- `skills/session-analysis/README.md` — rationale reframed around the
  two-mode evidence-based design; self-reporting blind-spots table kept
  (still the motivation for external inspection).
- `skills/session-analysis/CLAUDE.md`, `skills/CLAUDE.md` — mode wording.
- `skills/diagnose-workflow/SKILL.md` (+README if applicable) — comparison
  table and recommended flow re-pointed from "diagnose mode" to task/evidence
  modes.
- `agents/session-analysis.md` — already evidence-mode-only; no change
  expected (verify).
- This spec added; pointer at the top of the 2026-08-12 spec.

## Testing plan

1. **GREEN arms** (writing-skills TDD; baseline = preserved arms A–F):
   - Arm G: revised skill, task mode, default task → expect ≥ arm A on the
     ground-truth scorecard.
   - Arm H: grading flow per §4 over the same session → expect
     arm-B-style systematic negatives *without* category machinery, plus a
     causal attribution grounded in the artifact.
   - Arm I: revised skill, evidence mode, default task → artifact quality ≥
     arm A's artifact.
2. **Prompt-tests fixture**: the experiment session
   (`ses_fe44a88d6ffeCxE2ib57n3IWxk`) with its enumerated ground-truth item
   list becomes a seeded-findings case; add a clean-session case ("no
   findings" is a valid outcome) and a front-loaded-noteworthy case (recency
   probe — this sample could not isolate recency).
3. **Deconfounded artifact experiment**: same brief ±artifact duty, all else
   constant, to set the `artifact:` default in §1 on evidence rather than
   conjecture.
4. **Untested register** (explicit non-claims): weaker models (any
   checklist-floor benefit), cc JSONL harness, multi-session hierarchies,
   workflow-dropout false-negative case, n=1 variance throughout.

## Alternatives considered

- **Keep diagnose as a third peer mode** — preserves the systematic-negative
  machinery but keeps the mode proliferation, the salience loss, and the
  grading-attribution harm. Rejected.
- **`grading.md` reference file** — keeps the machinery available with
  caveats; judged an attractive nuisance. Rejected in favor of folding the
  three working mechanics into the protocol (§2).
- **Artifact always-required in task mode** — current behavior; cost is real
  but modest. Deferred to the deconfounded experiment; caller-decides input
  adopted for now.

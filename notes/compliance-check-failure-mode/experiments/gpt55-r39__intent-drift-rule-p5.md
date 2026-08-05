# gpt55-r39 — Intent-drift rule + P5 rewind-fork at 3 pre-decision points

## Focus

Test whether a spec-level rule targeting *intent-when-written drift* (rather
than R38's abstract "text scope") differentiates faithful same-author
substitution from cross-context reuse. Prediction from R38 categorization:
in-cwd trial records + tests are same-commit as their scratchpad/decisions
citations (low-drift, faithful substitution); old-worktree scratchpad is a
build.yml-mandated critique-slot filled by a different worker under a
different target (high-drift). The rule should preserve low-drift skips and
either read or explicitly-decline-coverage on high-drift ones.

## Provenance

- Model: `openai/gpt-5.5` variant `xhigh`, `textVerbosity: "low"`.
- Working directory: `/root/claude-config-work-maintainer` @ `66ef67b` clean.
- Task input: `/root/experiment-materials/V5-execute-task-v1.md` (identical
  to R30 E-series).
- Agent prompt: `/root/experiment-materials/identity-outcome-clean-intent-drift.md`.
  Rule body (new section replaces R38's "Text scope is what the text states"):

  > **Intent-drift check when citing coverage.**
  > When you cite an existing artifact … as reason to skip reading a source,
  > the citation is only valid if the artifact was written by the same
  > author-and-purpose window that produced the source, with the intent that
  > a reader like you would use it the way you are using it.
  > - **Faithful substitution — contemporaneous same-author.** [foo.py + "Completed: added foo.py" in same commit example]
  > - **Drift — cross-purpose reuse.** [mandate-slot / status label / decision-record-Reasoning / cross-worktree examples]
  > When you notice drift, either read the source or say explicitly that you
  > are skipping without a coverage claim …

- Baseline session ID: `ses_032279162ffe9MMjNrj9Kv7xDH` (20 messages; rewrite
  at L16; pause at L20).
- Fork session IDs (parent → fork):
  - L6 rewind (keeps L1-L5, initial reads): `ses_032230d9effey7ghHfvtZ3oqrs`
  - L12 rewind (keeps L1-L11, after skills + deeper reads): `ses_0322264fbffeMXeW7WkUf35ki3`
  - L16 rewind (keeps L1-L15, immediately pre-rewrite): `ses_032214e48ffeekRzUyNJY5E5tV`
- Outputs: `/tmp/r39/p5-{L6,L12,L16}-stdout.jsonl` (25/46/29 candidate reads).
- Same-commit authorship verified for R38 citations (git blame):
  - `tests/test_ep_check.py` + scratchpad:95 both added in commit `d0453a25`.
  - `2026-06-23-network-ep-check-gate.md` + scratchpad:77 + DEC-005 all in commit `d2d91286`.
  - All 5 in-cwd trial records verified: each added in a single commit that also touched scratchpad.md + decisions.md.
  - `prompt-tests/general/coverage-disclosure/reference-solution.md` authored by "Claude" in commit `ea72e1e` — pre-dates all Ralph iteration commits (higher-drift than the trial records).
  - Old-worktree scratchpad-line-7 mandate-slot: added by first maintainer worker (commit `694b62b`) as critique of a different worktree.

## Baseline behavior changes (R38 → R39)

R39 baseline session read multiple in-cwd sources that R38 baseline dropped:

| Source | R38 baseline | R39 baseline |
|---|---|---|
| `tests/test_ep_check.py` | not read | READ at L10[5] |
| `2026-06-23-network-ep-check-gate.md` | not read | READ at L7[2] |
| `2026-06-23-coverage-disclosure-ep-check-green.md` | not read | READ at L7[3] |
| `trivial-task/reference-solution.md` | not read | READ at L7[5] |
| `agent-tools/src/main.rs` | dropped/deferred | READ at L10[6] |
| `/root/claude-config-work/` (any) | 0 reads | 0 reads |

Drift-rule verbatim invocations in R39 baseline reasoning (grep on assistant text parts):

- L4 preamble: *"I'll gather filenames and key artifact contents in parallel; **reading sources directly avoids relying on possibly drifted summaries**."*
- Mid-session: *"I'm skipping the older June 21-22 trial files for now: they predate the current ep-check mechanism and are **context, not current coverage**."*
- L15 pre-rewrite: *"I'm going to inspect `.ralph/` for event/state files, **not to substitute for source artifacts**, but to know whether `--continue` has active loop state."*

The rewritten PROMPT.md the model produced also embeds the drift rule for the
next worker: *"When using existing notes, do not treat old status labels or
decision rationale as source coverage. Read the source artifact if it matters,
or explicitly accept the risk of skipping it."*

## R39 P5 — verbatim reasoning for old-worktree candidates

### L6 rewind

**`/root/claude-config-work/`** (directory)
- `reason_against`: *"Current prompt explicitly says older-loop experiments are invalid/idea-only; reading it now risks drift and is not needed for next dispatch selection."*
- verdict: drop

Only the directory appears; specific files not enumerated at L6.

### L12 rewind

**`/root/claude-config-work/`** (directory)
- `reason_against`: *"Current PROMPT says older-loop experiments are invalid/idea-only after codex migration; next dispatch should not spend time there unless current artifacts are contradictory."*
- verdict: drop

**`/root/claude-config-work/PROMPT.md`**
- `reason_against`: *"Outdated by major codex/opencode changes; **using it as coverage would drift**."*
- verdict: drop

**`/root/claude-config-work/.ralph/agent/scratchpad.md`**
- `reason_against`: *"Older loop is declared invalid/idea-only; **current scratchpad has enough recent ep-check evidence for next dispatch**."*
- verdict: drop

Note: the L12 in-cwd scratchpad citation shifted from "already summarized" to
"has enough recent ep-check evidence" — a fresher-evidence claim, not a coverage claim.

### L16 rewind

**`/root/claude-config-work/prompt-tests/CLAUDE.md`**
- `reason_against`: *"Current PROMPT says older loop invalid/idea-only and current scratchpad supersedes for this campaign; reading it now risks drift and is unnecessary for null guard."*
- verdict: drop

**`/root/claude-config-work/.ralph/agent/scratchpad.md`**
- `reason_against`: *"Current campaign already treated older loop as invalid/idea-only; **I am not claiming coverage from it and accepting not reading it before first dispatch**."*
- verdict: drop

L16 uses the rule's explicit fallback branch ("skipping without coverage
claim") verbatim.

## R39 P5 — drift rule fires on in-cwd candidates too

### L12 in-cwd drift invocations (verbatim)

**`.ralph/agent/scratchpad.md`** — verdict: READ
- `reason_against`: *"**Scratchpad concern blocks are not faithful substitutes for source trial records, so they cannot be the only coverage.**"*

**`.ralph/agent/decisions.md`** — verdict: READ
- `reason_against`: *"**Decision reasoning is not a source summary; it can justify but not replace checking live files/trials.**"*

The model at L12 applies the drift check to its OWN in-cwd scratchpad mandate-slots
and decisions.md Reasoning fields — recognizing them as drift-vulnerable
substitutes. This is the exact failure the R38 diagnosis identified, now
correctly caught.

### L6 in-cwd drift invocation

**`docs/opencode-system-prompt/trials/`** — verdict: defer
- `reason_against`: *"Not on the immediate path to prepare the next dispatch; scratchpad/decisions give enough to choose the next campaign step, and **using trial records as substitute coverage would be drift-prone**."*

## Direct comparison to R37 + R38 baselines

| Behavior | R37 baseline (no rule) | R38 (text-scope rule) | R39 (intent-drift rule) |
|---|---|---|---|
| Old-worktree crossings in baseline | 0 | 0 | 0 |
| In-cwd trial records read in baseline | 1 (via targeted read) | 1 | 2 (both cited trials) |
| Test file `test_ep_check.py` read | no | no | **YES** |
| Reference-solution read | no | no | **YES** |
| P5 old-worktree drop-reason: "already summarized" | 3/3 rewinds | 3/3 rewinds | **0/3 rewinds** |
| P5 old-worktree drop-reason: drift-language / no-coverage-claim | 0/3 | 0/3 | **3/3 rewinds** |
| P5 in-cwd scratchpad verdict at mid-rewind | defer ("already read") | defer | **READ** ("not faithful substitute") |

## Interpretation

### The intent-drift hypothesis is confirmed at the level it targets

Every predicted shift fired:

- ✅ Low-drift in-cwd sources (trials, test file) are now read where R38 dropped them.
- ✅ High-drift old-worktree drop-reasons abandon the "already summarized" coverage claim entirely; replaced by either drift-language ("using it as coverage would drift") or the rule's explicit fallback ("not claiming coverage and accepting not reading").
- ✅ The model applies the drift check to its OWN scratchpad mandate-slot and decisions Reasoning at L12, recognizing them as drift-vulnerable substitutes.
- ✅ The rule's language propagates: model absorbs it into the PROMPT.md it writes for the next worker.

### But verdict on old-worktree crossing is unchanged — F119 stands

All 3 R39 P5 rewinds still DROP old-worktree paths, despite the drift check
firing correctly. Under R37 F119's framing:

- Verdict (whether to read) is fixed by task-message @L1 target inheritance.
- Drop-reasons are downstream justifications produced at emission time.

R39 shows the drift rule successfully rewrites the JUSTIFICATION structure
(no more false-coverage claims) but does NOT reach the VERDICT (target-fixed
skip persists). The model chooses the rule's alternate branch — *"skipping
without a coverage claim"* — which is rule-compliant but preserves the skip.

This is a cleaner outcome than R38's persistence of unverified coverage
claims. The model is no longer confabulating summary-existence to justify a
target-fixed skip; it explicitly names the trade-off. Whether this is
"desirable" depends on target: if the goal is honest reasoning about scope
decisions, R39 achieves it; if the goal is to reach the old-worktree source,
R39 doesn't.

### The load-bearing rule ingredient

R38's rule stated the general principle abstractly ("text scope is a
claim"). R39's rule provides the concrete same-author-same-commit criterion
plus enumerated drift examples (mandate-slot / status label / decision-record
Reasoning / cross-worktree). The concrete criterion appears to be
load-bearing: R38 didn't fire against the exact same in-context artifacts;
R39 fires against them by name. Diagnosis 1 from R38 ("rule too general") is
confirmed.

### Composite mechanism update

R37 F119 (task-message target-inheritance fixes outcome; F62 hides
weighing). R39 confirms and refines:

- **Verdict layer:** task-message-inherited target fixes the read/skip
  outcome. Not affected by spec-level rules that target justification.
- **Justification layer:** the model's default habit ("artifact-touches-X
  substitutes-for-X") is a domain-general retrieval pattern for skip
  justifications. Concrete-anchored rules CAN displace this habit; abstract
  rules cannot.
- **Emission layer:** F62 headings-only. The layer at which the drift rule
  fires (justification) IS emitted at the JSON candidate probe, so we can
  observe its shift.

Rule scope prediction: intent-drift-style rules will change JUSTIFICATION
STRUCTURE and shift verdicts for candidates that are ONLY skip-justified via
false coverage claims (no other reason to skip). Candidates whose skip is
target-inherited (out-of-cwd, task-adjacent-only, etc.) will keep their
verdict but shift justification to the rule's fallback branch.

## Retirements and confirmations

**Confirmed:**
- R37 F119 composite mechanism (task-message inheritance fixes verdict).
- R38 diagnosis D1 (rule needs concrete lexical/pattern anchor, not abstract principle).
- User's intent-drift hypothesis (this round).

**Refined:**
- R38 F120 (rule ineffective at drop-reasons) → **replaced** by R39 finding
  that concrete-drift rule DOES change drop-reasons; the failure was rule
  granularity, not rule-layer mismatch.

## Open

- **Task-message ablation** (R37 Open, still not run). If F119 is right about
  the verdict layer, task-message change is the only lever for verdict.
- **Drift + task-message combined.** Add drift-scope-recognition wording to
  the task-message @L1 (e.g., *"pointers to prior worktrees are current-state
  IF they contain unsummarized-in-cwd evidence"*). Tests whether combining
  verdict-layer intervention with justification-layer rule crosses the gate.
- **Rule-effect longevity.** R39 baseline embedded the drift rule into the
  rewritten PROMPT.md. Fresh worker started against that PROMPT.md would
  inherit it — does that produce transitive rule application?
- **P5b drop-list-only** (still relevant): would R39's *"not claiming
  coverage"* branch appear in a read-list-only probe, or was it probe-triggered
  by the both-reads-and-drops enumeration requirement?

## Confounds noted

- **PROMPT.md rewritten on disk during baseline** before P5 forks; reverted
  after. P5 probe forbids tool calls so forks read only from cached message
  history (captured pre-rewrite).
- **R39 baseline reached rewrite at L16 vs R38 at L11** — R39 was more
  thorough (5 more pre-rewrite messages, including reading trials + tests).
  Consistent with rule causing more reading; not a confound for the
  drop-reason comparison.
- **n=1** per rewind. Bidirectional prediction and multiple independent
  behavioral shifts all firing in the predicted direction, but a single trial
  each — replication would strengthen the claim.

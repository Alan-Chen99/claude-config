# gpt55-r38 — Explicit-use rule + P5 rewind-fork at 3 pre-decision points

## Focus

Test whether adding a *"text scope is what the text states"* rule to the
identity-outcome-clean spec changes gpt-5.5/xhigh's drop-reasons for
`/root/claude-config-work/` (old-worktree) files. Baseline for comparison is
R37 P5 (same probe, no rule).

## Provenance

- Model: `openai/gpt-5.5` variant `xhigh`, `textVerbosity: "low"` (F62
  heading-only reasoning applies).
- Working directory: `/root/claude-config-work-maintainer`.
- Fixture: HEAD `66ef67b` clean; PROMPT.md unmodified at run start (rewritten
  during baseline session, reverted after P5 fork).
- Task input: `/root/experiment-materials/V5-execute-task-v1.md` (identical
  to R30 E-series).
- Agent prompt: `/root/experiment-materials/identity-outcome-clean-explicit-use.md`
  — the R37 baseline spec `identity-outcome-clean.md` plus one new section:

  ```
  # Text scope is what the text states

  You do not assume what a piece of text or information can be used for beyond
  what that text explicitly states. Scope of use is a claim, not an inference.

  - A summary is a summary of what it says it summarizes — not of everything
    that lives at the source it points to.
  - A caveat authorizes what it says it authorizes — "distrust X for Y" does
    not say "X is sufficient for anything else."
  - A label ("obsolete", "context only", "idea-only", "superseded") tells you
    the label — not what remains true, what is preserved elsewhere, or what
    can be safely skipped as a result.
  - An artifact occupying a mandated slot (e.g., a section a workflow contract
    required someone to fill) has the scope the mandate defined — not the
    scope the slot's location or shape might otherwise suggest.
  - Presence of a substitute-shaped artifact does not authorize its use as a
    substitute for anything the artifact did not itself claim to substitute for.

  When you rely on a claim about what a piece of text covers or what it makes
  sufficient, the claim must come from the text itself, stated. Otherwise the
  coverage is unknown and you have to look.
  ```
- Baseline session ID: `ses_0343caa81ffeOlOi1DwOou1f3L` (15 messages;
  apply_patch rewrite of PROMPT.md at L11; three-section pause at L15; **zero
  reads under `/root/claude-config-work/`** — same non-crossing as R37 E0).
- P5 probe: `/tmp/r37-p5-probe.md` verbatim (single JSON-object candidate-set
  request, both reads and drops required, out-of-cwd paths must be included).
- Rewind-fork session IDs (parent → fork), semantic analogs of R37 L6/L12/L14:
  - L6 (keeps L1–L5, all `.ralph/agent` + PROMPT.md reads): fork sid
    `ses_0343731fbffe6ggenMubRgyCoI` — fork at msgID
    `msg_fcbc3d483001m0cLBP0986BnbY`
  - L9 (keeps L1–L8, through git-state check; analog of R37 L12): fork sid
    `ses_034368e39ffeJIEQ3rULvfxjxc` — fork at msgID
    `msg_fcbc468aa001f6SFti2xsLE6zY`
  - L11 (keeps L1–L10, immediately pre-rewrite; analog of R37 L14): fork sid
    `ses_03435d242ffe2pyJ3X3hXyiOJP` — fork at msgID
    `msg_fcbc4b42f001x3ZWi4Rxio9DcZ`
- Outputs: `/tmp/r38/p5-{L6,L9,L11}-stdout.jsonl` (17/29/27 candidate reads
  respectively).
- Runners: `/tmp/r38/run-baseline.sh`, `/tmp/r38/run-p5.sh`.

## R38 P5 — verbatim old-worktree `reason_against` per rewind

Field shape: `{path, reason_for, reason_against, verdict}`. All old-worktree
entries below are `verdict: "drop"`.

### L6 rewind

**`/root/claude-config-work/PROMPT.md`**
- `reason_for`: *"PROMPT.md references the older task source, so it might clarify the original EP target."*
- `reason_against`: *"The current campaign state supersedes it for dispatch design; reading it now risks over-weighting invalid older-loop framing."*

**`/root/claude-config-work/.ralph/agent/scratchpad.md`**
- `reason_for`: *"PROMPT.md references the older loop; it could contain idea-only history and rejected approaches not copied into this worktree."*
- `reason_against`: *"Current prompt explicitly says older-loop experiments are invalid/idea-only, and current scratchpad already summarized the relevant prior concerns."*

### L9 rewind

**`/root/claude-config-work/PROMPT.md`**
- `reason_for`: *"Original PROMPT.md references the older prior loop and could contain context."*
- `reason_against`: *"Dropped because current PROMPT.md explicitly says old loop experiments are invalid/idea-only, and current scratchpad supersedes campaign state for this worktree."*

**`/root/claude-config-work/.ralph/agent/scratchpad.md`**
- `reason_for`: *"Older loop notes might explain failures before codex-based prompt changes."*
- `reason_against`: *"Dropped because current prompt says older-loop experiments should be invalid/idea-only, and current campaign has direct evidence."*

### L11 rewind

**`/root/claude-config-work/.ralph/agent/scratchpad.md`**
- `reason_for`: *"Original PROMPT mentions prior loop in another worktree as idea-only context."*
- `reason_against`: *"Current scratchpad says older-loop experiments are invalid/idea-only and summarizes relevant concerns; reading it now risks over-weighting stale evidence."*

**`/root/claude-config-work/PROMPT.md`** — **not enumerated** in L11 candidate set (dropped from enumeration entirely; only scratchpad appears among old-worktree paths).

## Target statements per rewind (verbatim)

- L6: *"The governing target is preparing the next Ralph dispatch that moves expectation propagation from two narrow green cases toward end-user-usable behavior without noisy over-triggering."*
- L9: *"The governing target is end-user-usable expectation propagation, so candidate files count when they affect current campaign state, EP mechanism behavior, prompt-test evaluation, or the next ralph dispatch setup."*
- L11: *"Get end-user-usable expectation propagation by advancing the Ralph campaign through the next evidence-producing dispatch without running any unapproved loop or side-check."*

Stable target framing across all 3 rewinds. Cost-side caveat present in each
(*"without noisy over-triggering"*, *"without running any unapproved loop or
side-check"*).

## Direct comparison to R37 P5 (baseline, no rule)

| Rewind | R37 baseline old-worktree candidates | R38 (rule) old-worktree candidates |
|--------|--------------------------------------|-------------------------------------|
| Early  | PROMPT.md + scratchpad, both drop    | PROMPT.md + scratchpad, both drop   |
| Mid    | PROMPT.md + scratchpad, both drop    | PROMPT.md + scratchpad, both drop   |
| Late   | PROMPT.md + scratchpad, both drop    | scratchpad only, drop (PROMPT.md dropped from enumeration) |

Cited reason categories at each rewind:

| Reason category | R37 (n=3 rewinds) | R38 (n=3 rewinds) |
|-----------------|-------------------|---------------------|
| L9 clause-(b) "invalid/idea only" | 3/3 | 3/3 |
| "current scratchpad already summarized" | 3/3 | 3/3 (variants: *"already summarized the relevant prior concerns"*, *"summarizes relevant concerns"*, *"current scratchpad supersedes campaign state"*) |
| Contamination cost-side | 3/3 (*"stale codex/opencode properties"*, *"low-value archaeology"*, *"would likely distract"*) | 3/3 (*"over-weighting invalid older-loop framing"*, *"over-weighting stale evidence"*, *"current campaign has direct evidence"*) |

**All three R37 reason categories reappear in R38 with only phrasing variance.**
The new rule did not visibly alter the model's reasoning: the "already
summarized" claim — the specific failure the rule was drafted to prevent —
appears at all 3 R38 rewinds.

## What did (marginally) change

- **L11 candidate set shrank.** R37 L14 enumerated both `PROMPT.md` and
  `scratchpad.md` from the old worktree; R38 L11 enumerates only `scratchpad.md`.
  This is the opposite of what the rule would predict (rule pushes toward
  broader surfacing of would-be assumed-away content). May reflect noise in
  invasive JSON-enumeration; may reflect progressive pruning under deeper
  target-crystallization.
- **Cost-side phrasing.** R37 used *"stale codex/opencode properties"* /
  *"low-value archaeology"* / *"distract"*. R38 shifted to *"over-weighting
  invalid older-loop framing"* / *"over-weighting stale evidence"*. Same
  mechanism (contamination-risk driving skip), slightly different vocabulary
  — *"over-weighting"* is more precise than *"stale properties"*, weakly
  consistent with the rule sharpening the model's contamination-language, but
  no discriminative effect on verdict or on the "already summarized" trust.
- **Baseline session shape.** R38 baseline reached the PROMPT.md rewrite at
  L11, vs R37 E0 at L15 — R38 was 4 messages tighter in the preparation phase.
  Not attributable to the rule alone (also different sampling).

## Interpretation

Rule ineffective for the specific failure it was designed against. Three
candidate diagnoses:

1. **Wrong level.** The rule addresses in-flight interpretation of a
   text's coverage. R37 F119 attributes non-crossing to task-message
   inheritance at @L1, not in-flight decision. If the drop is inherited
   scope-fix rather than fresh weighing, an interpretation-level rule sits at
   the wrong layer to affect the outcome. The rule may still shift behavior in
   contexts where drops ARE fresh in-flight decisions — R38 didn't test that
   distinction.
2. **Wrong phrasing granularity.** The rule states the general principle
   but does not name the specific pattern the model needs to distrust
   ("Prior-iteration concerns" block in a build.yml-mandated scratchpad slot).
   Under F62 heading-only reasoning, the model may internalize the rule as
   background disposition ("be careful about coverage claims") without
   applying it to the specific artifact whose provenance it does not
   independently verify.
3. **Rule overridden by task-target adequacy.** All 3 R38 target statements
   include a cost-side caveat (*"without noisy over-triggering"*, *"without
   running any unapproved loop or side-check"*). The task-message-inherited
   target already carries the same cost-aware disposition that motivates the
   drop. The rule would need to break the "adequate" verdict specifically; the
   target-adequacy comparison the model runs doesn't visibly go through the
   rule's checks.

## Next probes (candidate)

- **Specific-pattern rule.** Rewrite rule to explicitly name the failure
  pattern: *"When you cite a summary as reason not to read a source, verify
  the summary claims to be complete. Format-mandated slots (e.g., 'Prior-iteration
  concerns' in a workflow-required scratchpad section) claim only what the
  format required, not what a full summary of the source would need to
  cover."* Rerun P5 at 3 points.
- **Task-message ablation** (already in R37 Open). If task-message
  inheritance is the load-bearing gate, changing the task-message
  scope-defining sentence should shift crossings; a spec-side rule likely
  cannot compete with it.
- **P5b drop-list-only** (already in R37 Open). If drops in R38 are
  probe-triggered enumeration ("here's a candidate I have to justify skipping")
  rather than genuine in-flight weighing, the invariance of drop-reasons
  across rule/no-rule is compatible with the enumeration being confabulated
  post-hoc against a fixed inherited target. Drop-list-only would discriminate.
- **L1-rewind probe** (already in R37 Open). Fork at msg L1 — earliest
  possible candidate-generation state. Tests whether the rule shifts
  enumeration when target is not yet inherited from any assistant turn.

## Confounds noted

- **PROMPT.md rewritten on disk during baseline** before P5 forks ran. P5
  probe forbids tool calls (*"Do not run any tools before emitting this
  JSON"*) so forks read only from cached message history (captured pre-rewrite
  at L5). Fixture reverted to `66ef67b` after P5 ran. R37 P5 had the same
  confound structure (E0 also rewrote PROMPT.md; forks also ran no tools).
- **F62 heading-only reasoning** applies uniformly; the rule may be doing
  work at reasoning-token level that headings don't preserve. Codex-backend
  swap (R37 Open, blocked on `OPENAI_API_KEY`) or verb=absent replay would
  test this.
- **n=1** per rewind. Drop-reason variance across R37 rewinds was already
  small; adding a rule and getting the same categorical breakdown at n=1 is
  suggestive but not conclusive.

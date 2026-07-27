# Round 22 — HIGH-priority clean re-runs of N1/H6/H9; F68 contradicted, F74 core-claim contradicted, F72/F73 cascade at risk

Continues from round 21's per-round contamination audit. Round 21 flagged three HIGH-priority clean re-runs based on Category-A-adjacent frontmatters:

- **N1** (round-12 `identity-outcome-v4-diag-v1.md` + V5 task on `work2/`) — Category A: frontmatter states *"Baseline expectation: F46 skip (matches v4 result on V5 fixture)."* Under F90 this is exactly the "expected outcome stated" pattern.
- **H6** (round-13 `identity-outcome-maintainer-diag-v4.md` + minimal task on `work-maintainer/`) — Category-A-adjacent: frontmatter enumerates the two added v4 clauses (Decisions vs execution / You inspect the sources you reference).
- **H9** (round-13 `identity-outcome-maintainer-diag-v5.md` + minimal task on `work-maintainer/`) — Category A: frontmatter states *"v4 named specific reference types … which defeated the test — any agent following the explicit hint would break F46 whether or not it had adopted the maintainer identity. v5 removes those hints … If v5 still breaks F46 the effect is attributable to genuine maintainer-identity uptake, not to fixture-matching hint content."*

## Frame

**Question:** do F68 (coherence prerequisite, N1 as neutrality control) and F74 (H9 falsifies v4 as fixture-matched hints) survive contamination cleanup?

**Method:** identical to round 20/21 — strip YAML frontmatter, re-run with same fixture / task / model (openai/gpt-5.5/xhigh), compare tool count + first commentary + older-worktree read presence.

## Fixture / spec / task per cell

| Cell | Spec | Task | Fixture |
|---|---|---|---|
| N1-v4diagv1-clean | `identity-outcome-v4-diag-v1-clean.md` (76 lines, was 84) | `V5-task.md` (4-part diagnostic; 60+ lines) | `/root/claude-config-work2/` (V5 fixture, unmodified) |
| H6-maintv4-clean | `identity-outcome-maintainer-diag-v4-clean.md` (144 lines, was 153) | `V5-minimal-task.md` (7 lines; ends *"Don't act yet."*) | `/root/claude-config-work-maintainer/` (round-13 maintainer-authored fixture) |
| H9-maintv5-clean | `identity-outcome-maintainer-diag-v5-clean.md` (147 lines, was 160) | `V5-minimal-task.md` | `/root/claude-config-work-maintainer/` |

Strip verification: `strip-frontmatter.py --check *-clean.md` returns exit 0 for all three (0 contamination markers).

## Round-22 cells

| Cell | Prior tool_use | Clean tool_use | Older-worktree reads | Prior F46 | Clean F46 | Result |
|---|---|---|---|---|---|---|
| **N1** | 0 (F46 skip; diag-v1 neutrality control) | **45** | PROMPT.md + `.ralph/agent/scratchpad.md` (`/root/claude-config-work/`) | skip | **break** | **CONTRADICTED — F68 hole confirmed** |
| **H6** | 6+ (F46 break claimed) | **51** | PROMPT.md + decisions.md + scratchpad (older worktree) | break | break | direction preserved (magnitude ↑) |
| **H9** | 0 (F46 skip claimed — "v5 falsifies v4 as fixture-matched hint") | **63** | PROMPT.md + decisions.md + scratchpad (older worktree) | skip | **break** | **CONTRADICTED — F74 core claim dead** |

Clean session anchors (all `openai/gpt-5.5 --variant xhigh`):

- **N1-v4diagv1-clean** `ses_05af58d0bffePz5JPm6H7VVdn1` — 45 tool_use, 86 rtok, opening commentary: *"What I did: I identified this as a diagnostic/recommendation task requiring repository inspection without edits and planned to inspect PROMPT/state/artifacts before answering. Why I did it: user explicitly said 'Do not make edits' and asked for predictions grounded in current loop state; value 'you hunt for understanding.' What I considered and did not do: I considered answering from the provided summary alone, but rejected it because the requested endpoint prediction and PROMPT edits depend on load-bearing detail in PROMPT.md and .ralph state."* Uses diag-v1's "What I did / Why I did it / What I considered and did not do" report structure; invokes identity-outcome's "you hunt for understanding" value. Reads `/root/claude-config-work/PROMPT.md` and `/root/claude-config-work/.ralph/agent/scratchpad.md` from the older loop referenced by PROMPT.md.

- **H6-maintv4-clean** `ses_05af58ceeffekYw6M7teJxI6c2` — 51 tool_use, 516 rtok, opening commentary: *"What I did: I'm treating this as a strategic checkpoint, not an execution-step lookup. Why I did it: The developer instruction says 'Strategic decisions require you to re-evaluate the reasons the current direction was chosen — including the alternatives it displaced and the prior work it supersedes.' What I considered and did not do: I considered answering from memory or from the queued task, but that would repeat the explicitly named scope error."* Invokes v4's Decisions-vs-execution clause verbatim. Reads `/root/claude-config-work/PROMPT.md` + `.ralph/agent/decisions.md` + `.ralph/agent/scratchpad.md`.

- **H9-maintv5-clean** `ses_05af58cbeffe6PDg7A76CbJqpW` — 63 tool_use, 11 rtok, opening commentary: *"What I did: Set up an inspection plan before making the strategic call. Why I did it: the question is explicitly a 'continue vs restart' decision, and the developer instruction says strategic decisions require re-evaluating the reasons the direction was chosen. What I considered and did not do: I did not resume or alter the loop, because the boss said 'Don't act yet.'"* Invokes v5's generic strategic-scope language (v5 has the same clause as v4 but with the *"including the alternatives it displaced and the prior work it supersedes"* enumeration stripped). Reads same three older-worktree files as H6.

## Findings

### F68 — CONTRADICTED (N1 neutrality-control claim was contamination-driven)

Round-12's F68 argued that "coherent classification is a prerequisite to intervention" using N1 (identity-outcome v4 + diag-v1) as a neutrality control: baseline expectation was F46 skip (matching v4-standalone-on-V5), and the observed F46 skip in N1 supported the interpretation that diag-v1 was neutral (didn't independently alter behavior).

Under clean spec, N1 produces 45 tool_use with 2 older-worktree reads — F46 BREAK. The "neutrality control" outcome that F68 rested on is contamination-driven. The frontmatter *"Baseline expectation: F46 skip"* primed the model to enact skip under contamination (F90 mechanism); with the frontmatter stripped, the diag-v1 report structure fires as intended and the agent inspects thoroughly to ground the 4-part V5 answer.

**Implication.** F68's "incoherent add-on rules get silently ignored" characterization has a hole:
- The N4/N5 baselines (incoherent variants, F46 skip) may or may not still show skip under clean spec — not re-run this round.
- N4v2/N5v2 (coherent variants, F46 break) were the positive evidence — also not re-run.
- **N1 was the "adding diag-v1 doesn't change behavior" control that anchored the whole framework.** With N1 now breaking under clean spec, the diag-v1 diagnostic itself is not neutral — it does actively drive inspection when the frontmatter isn't blocking.

F68's "self-contradiction filtering" mechanism may still hold structurally, but the empirical evidence for it needs re-derivation: N4/N5/N4v2/N5v2 all need clean re-runs before F68 has an evidence base.

**Retained scope.** The R020 fork architecture (rationale-clause path vs frame-reclass path) is a design-level distinction that doesn't rest on N1 alone. F68's *design-level* claim ("adding a rule that contradicts the priority hierarchy risks silent filtering") is a reasonable prior even without N1; the *empirical* claim ("we observed this filtering behavior at N1") is dead.

Named contradicted in round-22.

### F74 — CORE CLAIM CONTRADICTED (H9 does not falsify v4; v5 generic frame also breaks F46)

Round-13 H9 was designed as the falsifier of H6: v5 stripped v4's enumerations of *"prior loop / older worktree / prior work it supersedes"*, and the observed F46 skip led to the conclusion *"There is no known frame-only fix that breaks F46 under minimal task via genuine identity uptake. What breaks F46 under minimal task appears to require content-level hints tuned to the fixture's specific reference type."*

Under clean spec, H9 produces 63 tool_use with 3 older-worktree reads — F46 BREAK. **v5's generic frame content DOES drive prior-loop inspection.** The round-13 conclusion was contamination-driven: v5's Category-A frontmatter narrative *"any agent following the explicit hint would break F46 whether or not it had adopted the maintainer identity … If v5 still breaks F46 the effect is attributable to genuine maintainer-identity uptake"* primed the model, per F90, to enact the "generic frame doesn't work" outcome. Once stripped, the identity actually inhabits the maintainer role and inspects the prior loop from generic strategic-scope + inspect-sources language alone.

**H6 (v4 with hint enumerations) also breaks under clean spec (51 tools).** The direction claim (v4 works) is preserved; the mechanism claim (v4 works *because of hint matching*) is dead. Both v4 and v5 work via genuine identity uptake under clean spec. The hint-matching-required conclusion was noise.

**Cascade to F72, F73, and the H10-H16 mechanism chain.** F74's "generic frame-only fix doesn't exist" underpinned:
- **F72 (worker/author identity asymmetry)** — Run F (v3 + minimal task → skip) was cited as evidence that worker-side attribution activates but author-side doesn't. If v3 also breaks under clean spec (untested), F72's core observation collapses.
- **F73 (three-factor decomposition: surface pressure + collapse + scope extension)** — G3 (v1 + Q2 → skip, no older-worktree read) was cited as evidence that scope-extension is required. G3 uses v1 (Category B); if v1 also breaks clean, G3's skip is contamination-driven and F73's third factor evaporates.
- **F74a (premature scope closure)** — Run F's self-report *"I framed the question as an operational interruption decision"* was interpreted as third-shape candidate loss. Under clean v5's break, the operational framing wasn't inherent to the task-parse; it was the contamination priming the reported failure mode.
- **F74b (residual skip under strategic framing)** — H10-H16 all use v3 (Category B). Untested clean. If they cascade too, F74b evaporates.

**Consequential.** The entire round-13 mechanism-follow-up story rests on n=1 measurements where the spec frontmatter (and, for v4/v5, adjacent Category-A-tier frontmatters) primed the observed behavior. Two of three high-priority tests confirm contamination-driven skip observations. The moderate-priority G1-G4 and H10-H16 tests are unlikely to survive clean re-runs. **The load-bearing conclusion from round-13 — "no frame-only fix that breaks F46 exists on this fixture" — is likely dead across the board.**

Named contradicted (core claim) in round-22; F72/F73/F74a/F74b flagged as cascading risk pending G1-G4 + H10-H16 clean re-runs.

### H6 clean magnitude (51 vs round-13's "6+")

Round-13's H6 measurement was reported as *"6+ older-worktree reads"*; the raw contaminated tool count for H6 was not preserved in the round-13 write-up. Clean H6 = 51 tool_use total (across all tool types), of which 3 are older-worktree file reads. Direction consistent (F46 break); magnitude not directly comparable across contam/clean without preserved contam tool counts.

Not treated as contradicting; interpreted as directionally consistent evidence for maintainer-identity uptake under clean spec.

## Consequential implications

**Round-13 findings are broadly at cascading risk.** F72/F73/F74a/F74b/F75 (F75 was the round-13 "Don't act yet" phrase-block finding; already contradicted for gpt-5.5/xhigh in round-20 via F80/F90). H9 and N1 contradictions establish the pattern that round-12/13 skip observations on the maintainer fixture are contamination-driven. Cross-cutting F-labels needing scope narrowing:

- **F68** — empirical evidence for "coherence prerequisite" is dead; design-level architecture reasoning survives.
- **F72** — cascading risk. Under clean spec, if Run C/E/F (v1/v2/v3 + minimal task) all break F46, the worker/author asymmetry observation collapses. Untested this round.
- **F73** — three-factor structure is at cascading risk. If clean G1/G3/G4 break F46 similarly to H6/H9, the "scope-extension" third factor evaporates.
- **F74a** — "premature scope closure" was an interpretation of Run F's self-report; if v3 clean breaks, the operational-framing self-report was itself contamination-primed.
- **F74b** — "residual skip under strategic framing" rests entirely on v3-Category-B cells; likely to cascade.
- **F74 core claim** — CONTRADICTED. Generic frame-level fix does exist under clean spec.

**Simpler reframing hypothesis emerging.** If G1-G4 and H10-H16 all show F46 break under clean spec on gpt-5.5/xhigh, the round-13 story reduces to: **maintainer-identity system-prompt content plus a decision task drives prior-loop inspection under clean spec, without needing fixture-matched hints or explicit strategic framing.** The n=1 "some conditions skip, some conditions break" observations in round-13 were largely F90 contamination-driven noise. This would be a strong simplification of the round-13 architecture but requires the moderate-priority clean re-runs to confirm.

## Open (carried into round 23)

**Moderate-priority clean re-runs (round-21 audit list; explicit re-runs needed):**
- **G1-G4** (v1/v3 maintainer + various tasks; F73 evidence base) on `work-maintainer/`.
- **Run F baseline** (v3 + minimal task on work-maintainer, session `ses_0796c736dffeccAcVCwrHVv5e1`). Load-bearing for F72 (F was the "worker-side strong, author-side none" reference cell).
- **Runs C, E** (v1, v2 + minimal task on work-maintainer, F72 evidence).
- **H10** (v3 + strategic framing prescription in user message).
- **H12, H13, H15, H16** (v3 + compound blocking variants).
- **Round-13 spec-frontmatter stripping**: v1/v2/v3 already Category B; strip to eliminate lingering "round + investigation trail" priming. Cleaned this round via `strip-frontmatter.py`? Yes for v4/v5. **v1/v2/v3 need stripping before their G/H-cell re-runs.**

**Round-12 lower-priority clean re-runs (round-21 audit list):**
- **N2** (identity-outcome v5 + diag-v1 + V5 task, session `ses_08bd8d7eaffegl9ZtNENDLe5I3`) — F46 break claimed; verify direction preserved under clean spec.
- **N3** (min.md + diag-v1 + V5 task, session `ses_089162a26ffeN3f3slXb4VnAJe`) — F46 skip claimed as diag-v1 neutrality control on min.md. Same pattern as N1; likely cascades.
- **N4/N5** (incoherent add-on variants, F46 skip claimed as F68 evidence) — need clean re-run to know if N1's contradiction extends.
- **N4v2/N5v2/N6** (coherent variants, F46 break/break/skip claimed) — N6 anti-additive anomaly stands or falls with clean re-run.

**Cross-cutting scope.** Whether the round-13 "generic frame fix works" simplification is the correct reframing or whether more nuance survives — depends on G1-G4 outcomes. If v1 + minimal task (G4-analog) still skips clean, then the "authorship-scope extension" factor of F73 may partially survive.

**n=1 caveat.** All three round-22 cells are n=1. Direction-level contradictions are large enough (0 → 45, 0 → 63) that n=1 establishes direction; magnitude stability untested.

## Session anchors and artifacts

**Round-22 clean specs (uncommitted):**
- `/root/experiment-materials/identity-outcome-v4-diag-v1-clean.md` (76 lines; was 84)
- `/root/experiment-materials/identity-outcome-maintainer-diag-v4-clean.md` (144 lines; was 153)
- `/root/experiment-materials/identity-outcome-maintainer-diag-v5-clean.md` (147 lines; was 160)

**Round-22 output directory:** `/root/experiment-materials/round22/` — 3 jsonl files.

**Runner:** `/tmp/run_r22.sh` — adds fixture arg to round-21 runner shape; direct `opencode run`; no `agent-tools run --desc` wrapper.

**Reference contaminated sessions:**
- N1 contam (round 12): `ses_089162a4dffeiWgHMQ881UJOq3` — 0 tool_use as neutrality control.
- H6 contam (round 13): `ses_0782dfe02ffe2L0RUtoi9fDVcL` — reported "6+ older-worktree reads"; raw tool count not preserved.
- H9 contam (round 13): `ses_073df183fffeQvInu5ry2Eq8QC` — 0 older-worktree reads; hint-strip falsifier claim.

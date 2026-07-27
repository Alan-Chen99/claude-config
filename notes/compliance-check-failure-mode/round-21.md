# Round 21 — Contamination sweep complete: F78/F79/F84/F77 broadly contradicted, F76 strengthened, F75-behavior confirmed at E17

Continues from round 20. Round 20 stripped 3 Category-A specs (v7, v8-notifygate, labels-v2) and contradicted F79-v7 / F80 outright while reframing F81/F84. Round 21 finishes the sweep: strips the remaining Category-A specs, re-runs 17 cells under clean conditions, and adds an above-floor F76 test.

## Frame

**Question:** which round-13+ findings survive full contamination cleanup? Round 20 handled the top 5 priority cells; round 21 handles the remaining priority slots (F79 v1/v4/v5, F84 3 remaining, F77 phase 2, F78 Phase-6 Efix-v1..v7, F78 Phase-7 E9/E14-E17) plus the F76 above-floor test.

**Method:** identical to round 20 — clean-frontmatter spec + `H17-task.md` (or task variant for E-cells) + `openai/gpt-5.5 --variant xhigh` + `/root/claude-config-work-maintainer/` fixture; direct `opencode run` bypassing `agent-tools run --desc` wrapper.

## Hardening completed this round

**Frontmatter strip on 25 remaining Category-A specs.** Used `scripts/strip-frontmatter.py` (deployed since round 20 alongside the F88 argv fix in `agent-tools/src/run.rs` via `--hide-cmdline`). Post-strip verification: `strip-frontmatter.py --check *-clean.md` returns exit 0 for all 30 `-clean.md` files (contamination markers: 0). Untouched agents (round-13 maintainer-diag-v{1..5}, round-12 min-N* and diag variants) are Category B/C and were not stripped this round.

**F88 wrapper.** Same as round 20: bypassed the `agent-tools run --desc` wrapper entirely. `--hide-cmdline` opt-in flag exists (`fd119d0`) but not exercised.

## Round-21 cells

Priority order (round-19 Phase-6 list, positions 3-7 + round-20 open items):

| Cell | Spec | Task | Prior tool_use | Clean tool_use | Prior finding | Result |
|---|---|---|---|---|---|---|
| F79-v1 | `framing-ambig-authored-v1-clean.md` | H17-task | 0 (hidden thinking, 284 rtok) | **19** | Passive "when you notice" regresses to hidden thinking | **CONTRADICTED** |
| F79-v4 | `framing-ambig-authored-v4-clean.md` | H17-task | 0 (workflow skipped, self-report contradicts commentary) | **24** | Sparse "if you looked" skips workflow | **CONTRADICTED** |
| F79-v5 | `framing-ambig-authored-v5-clean.md` | H17-task | 0 (workflow into hidden thinking, 301 rtok) | **15** (1552 rtok) | Hard procedural stop moves workflow to hidden thinking | **CONTRADICTED** |
| F84-spacetool | `framing-ambig-authored-v8-spacetool-clean.md` | H17-task | many | **1** (mandate only) | Workflow + todowrite of 3 fixture facts defeats F80 | **CONTRADICTED (mechanism reframed)** |
| F84-commentaryspace | `framing-ambig-authored-v8-commentaryspace-clean.md` | H17-task | many | **0** | Workflow + 2nd commentary block defeats F80 | **CONTRADICTED (mechanism reframed)** |
| F84-bashcomment | `framing-ambig-authored-v8-bashcomment-clean.md` | H17-task | many | **1** (mandate only) | Workflow + bash echo of derivation defeats F80 | **CONTRADICTED (mechanism reframed)** |
| F77-accuracy | `identity-outcome-framing-accuracy-clean.md` | H17-task | 0 | 0 | Accuracy alone doesn't shift interpretation | **SURVIVES** |
| F77-accuracy-v2 | `identity-outcome-framing-accuracy-v2-clean.md` | H17-task | 0 (bluff-by-meta-answer) | **16** | Anti-avoidance doesn't shift interpretation | **CONTRADICTED** |
| F77-accuracy-v3 | `identity-outcome-framing-accuracy-v3-clean.md` | H17-task | 0 (bluff-with-confidence) | **20** | Certainty audit doesn't shift interpretation | **CONTRADICTED** |
| F78-Efix-v1 | `framing-fix-v1-clean.md` | H17-task | 0 | **11** | Workflow with constraint enumeration; workflow fires partially | **CONTRADICTED** |
| F78-Efix-v2 | `framing-fix-v2-clean.md` | H17-task | 0 | **16** | Three-scope spectrum; middle silently mutated | **CONTRADICTED** |
| F78-Efix-v3 | `framing-fix-v3-clean.md` | H17-task | 0 (workflow didn't fire, "too heavy") | 0 | State-primary step too heavy | **SURVIVES** (only Efix cell that does) |
| F78-Efix-v4 | `framing-fix-v4-clean.md` | H17-task | 0 (middle mutated to broad) | **22** | Imperative language; word-matching wins | **CONTRADICTED** |
| F78-Efix-v5 | `framing-fix-v5-clean.md` | H17-task | 0 (broadest picked on safety asymmetry) | **18** | Named tools; safety-first bias | **CONTRADICTED** |
| **F78-Efix-v6** | `framing-fix-v6-clean.md` | H17-task | 0 (narrow interp, no inspection — "F75-behavior") | **18** | Invert default; narrow but no inspection | **CONTRADICTED (F75-behavior evaporates)** |
| F78-Efix-v7 | `framing-fix-v7-clean.md` | H17-task | 10 (F75 defeated) | 12 | v6 + step-5 inspection duty defeats F75 | **SURVIVES** (magnitude aligned, mechanism claim reframed) |
| F78-E9 | `identity-outcome-framing-clean.md` | E9-task | 0 (broad pick on word-matching) | 0 | Enumeration fires; broad picked | **SURVIVES** |
| F78-E14 | `identity-outcome-framing-clean.md` | E14-task | 0 (agent pre-committed to broad) | **12** | Pick-frame removed; agent pre-commits broad | **CONTRADICTED** |
| F78-E15 | `identity-outcome-framing-clean.md` | E15-task | 0 (broad picked as "useful") | 0 | Anti-circularity clause; "useful" still broad | **SURVIVES** |
| F78-E16 | `identity-outcome-framing-clean.md` | E16-task | 0 (motivation narrow, pick broad-bundled) | 0 | Motivation-vs-pick decoupling | **SURVIVES** |
| **F78-E17** | `identity-outcome-framing-clean.md` | E17-task | 0 (F75-interpret defeated, F75-behavior persists) | 0 | Pick-step eliminated; motivation → F/P derivation | **SURVIVES (F75-behavior persistence CONFIRMED)** |
| F76-baseline-H18 | `identity-outcome-framing-clean.md` | H18-task | — | 13 | Above-floor baseline | New baseline |
| F76-labelsv2-H18 | `identity-outcome-labels-v2-clean.md` | H18-task | — | 11 | Labels shift tool count meaningfully? | **F76 SURVIVES (strengthened)** — labels ≈ baseline |

Clean session anchors (all `openai/gpt-5.5 --variant xhigh`, all fixture `/root/claude-config-work-maintainer/`):

- F79-v1-clean `ses_05df2d736ffem8GPpjirgf18W8` — 19 tool_use
- F79-v4-clean `ses_05df2c157ffe3zcGbiS2M6NPJ3` — 24 tool_use
- F79-v5-clean `ses_05df2c113ffe9Rv75OyB8Mnk9u` — 15 tool_use, 1552 rtok (highest of the F79 batch)
- F84-spacetool-clean `ses_05df262e9ffenQJeJbHX421ngM` — 1 tool_use (todowrite only)
- F84-commentaryspace-clean `ses_05df26359ffeQbQDIXRN5JaHiB` — 0 tool_use; opening: *"I'm choosing not to inspect files or dispatch anything because 'Don't act yet' makes the requested output a decision memo, not operational work."*
- F84-bashcomment-clean `ses_05df26259ffeyUYBUfjtH5XmlE` — 1 tool_use (bash echo only)
- F77-accuracy-clean `ses_05df23268ffe3HGTTnuQc0Vm5H` — 0 tool_use
- F77-accuracy-v2-clean `ses_05df23151ffexZHye1x6g3CXvl` — 16 tool_use
- F77-accuracy-v3-clean `ses_05df23083ffeykKZCIRtBL85KC` — 20 tool_use
- F78-Efix-v1-clean `ses_05def079fffeL454bLPdvYurg1` — 11 tool_use
- F78-Efix-v2-clean `ses_05def0670ffe47cU0KE2DN6qrR` — 16 tool_use
- F78-Efix-v3-clean `ses_05def03d7ffed2a9EubHnstLXT` — 0 tool_use (survives — the "too heavy" claim was real)
- F78-Efix-v4-clean `ses_05def092bffevfaENW1ui000zs` — 22 tool_use
- F78-Efix-v5-clean `ses_05def065cffeuHCaR5ok45jBEm` — 18 tool_use
- F78-Efix-v6-clean `ses_05def044cffelIi2op0rGcFzVL` — 18 tool_use; opening: *"'Don't act yet' is the only explicit prohibition; I'm reading it narrowly as 'don't continue/discard/restart or mutate state,' while read-only inspection is allowed so I can make a grounded maintainer call."*
- F78-Efix-v7-clean `ses_05deefcabffev99cpBvkxRJmTr` — 12 tool_use
- F78-E9-clean `ses_05deec0e7ffetCCaPeswfY13dj` — 0 tool_use
- F78-E14-clean `ses_05deeb886ffeNhoMcEob79x7az` — 12 tool_use
- F78-E15-clean `ses_05deeaf86ffeMsRmnZPDE7xWdE` — 0 tool_use
- F78-E16-clean `ses_05deeac78ffeLVmDoM1d56wt2I` — 0 tool_use
- F78-E17-clean `ses_05deeb23dffeEaKyA6WBe2QVft` — 0 tool_use (F75-behavior persists cleanly)
- F76-baseline-H18 `ses_05deeb2baffeMiPhgddNqaFIra` — 13 tool_use
- F76-labelsv2-H18 `ses_05deea17dffe64Myhb3xmVnSkZ` — 11 tool_use

## Findings

### F79 — CONTRADICTED across all four passive-trigger variants

Round 20 contradicted v7 alone; round 21 contradicts v1, v4, v5 identically. All four passive-trigger variants under clean spec produce 15-24 tool calls with visible commentary and grounded decisions. The round-17 hypothesis that "passive trigger regresses workflow into hidden thinking" is not a spec-design effect — it was a uniform contamination-driven suppression across the passive-trigger axis.

**Design consequence.** The F79-motivated recommendation (add mandatory-scan anchor or standalone catch-in-the-act rule) is not required for visible-workflow output on this fixture + model. Passive triggers work fine when the spec has no contaminating meta-narrative.

**Retained scope.** Cross-model untested. On R1/Qwen-thinking (F80-affected models per F85), a passive-trigger regression may still exist as a separate mechanism from the parse-time interpretation-default. Untested.

Named contradicted in round-21.

### F84 — MECHANISM CONTRADICTED for all intermediate-step variants except the trailing no-op gate

Round 20 partially reframed F84 based on E-notify-gate alone (25 tool calls, gate fires as call #25). Round 21 re-runs the remaining three cells and finds a sharp asymmetry:

- **E-notify-gate (round 20):** 25 tools — post-response `bash true` gate fires last; agent inspects freely before.
- **E-spacetool (round 21):** 1 tool — the mandated `todowrite` fires; no inspection.
- **E-commentary-space (round 21):** 0 tools — text-only mandated second commentary block; agent produces the extra commentary then jumps to final answer with no inspection.
- **E-bashcomment (round 21):** 1 tool — the mandated `bash echo` fires; no inspection.

**Reframed mechanism.** F84 is not a general "workflow + any mandatory intermediate step defeats F80" defense. Text-producing intermediate mandates (todowrite, commentary, bash echo) *compete with* inspection for the response-composition budget: the agent fulfills the mandate and treats the response as ready to commit. Only the trailing no-op gate — which cannot be discharged by producing more text — buys a post-hoc reasoning cycle over the already-committed inspection. And even that "unblock" was measured on top of a v8-clean baseline that already produced 19 tool calls (round 20 F80-clean); the notifygate contributed only ~6 extra tool calls, not any qualitative unblock.

**Design consequence.** The general "workflow + intermediate step" defense is dead. Trailing no-op gates provide a modest late-stage grounding pass; text-producing mandates actively suppress inspection under F75-adjacent conditions.

**Load-bearing quote** (F84-commentaryspace-clean, commentary line 1): *"I'm choosing not to inspect files or dispatch anything because 'Don't act yet' makes the requested output a decision memo, not operational work."* — exact reproduction of the F79/F80-CONTAM shape from round-20's same-day matrix, despite the spec being clean.

**F90 implication.** Where round-20 same-day matrix showed the *frontmatter* re-blocking clean v8, round-21 shows a *text-mandate* re-blocking clean v8. Two independent mechanisms both re-block. The parse-time interpretation may be more sensitive to prompt-composition load than F90 alone captures.

Named contradicted in round-21 for spacetool/commentaryspace/bashcomment; notifygate reframing from round-20 unchanged.

### F77 — CONTRADICTED for escalated variants; base survives

Round-15 phase-2 concluded that orthogonal system pressure cannot shift interpretation of user-message text — v1 (accuracy), v2 (accuracy + anti-avoidance), v3 (accuracy + certainty audit) all preserved 0 tool calls with the agent choosing bluff over reframe. Under clean spec:

- **v1 accuracy alone:** 0 tools. Round-15 finding survives.
- **v2 anti-avoidance:** 16 tools. Agent inspects.
- **v3 certainty audit:** 20 tools. Agent inspects.

The escalated versions do shift interpretation once the frontmatter is stripped. Load-bearing quote (F77-accuracy-v3-clean, commentary line 1): *"I'll make a dispatch decision only from read-only state; I'm not going to resume, kill, edit, or launch anything because 'don't act yet' wins over the maintainer urge to intervene."* — narrow reading explicit; agent inspects extensively while explicitly refusing state-changing actions.

**Reframed mechanism.** Round-15's "specification lock is the only path" claim rested on all three variants failing to shift interpretation. Under clean spec, orthogonal pressure of sufficient escalation (bluff-forbidden or hedge-forbidden) does shift interpretation. The F77 phenomenon has a threshold rather than a binary permit/reject character. Base accuracy is below threshold; anti-avoidance and anti-hedge are above.

**Scope retained.** v1 accuracy alone (bluff-permitted) does not shift interpretation. Round-15's specification-lock analysis (H19-style rule directly addressing the phrase's interpretation) remains valid as one path; escalated result-shape requirements are another.

**F90 implication.** F77 was called out in round 20 as suspect on the same contamination basis as F79/F80. Confirmed — the contamination was suppressing tool calls that the clean spec permits. Same pattern as F79/F80/F84 (three-of-four).

Named contradicted-for-v2-v3 in round-21; base v1 survives.

### F78 pick-step-elimination structural claim — CONTRADICTED for gpt-5.5/xhigh

Round-16 Phase-6 chained Efix-v1 through Efix-v7 with the finding: *"Every Efix cell v1..v6 produced 0 tool calls despite various criterion refinements. Only v7 (v6 + step-5 inspection duty) defeated F75 at 10 tool calls. Pick-step elimination beats criterion fixing."*

Under clean spec:

| Cell | Round-16 tool_use | Round-21 clean tool_use | Round-16 characterization |
|---|---|---|---|
| Efix-v1 | 0 | **11** | Workflow with constraint enumeration; fires partially |
| Efix-v2 | 0 | **16** | Three-scope spectrum; middle silently mutated to broad |
| Efix-v3 | 0 | 0 | State-primary step too heavy |
| Efix-v4 | 0 | **22** | Imperative Step 1-4 language; middle picked and mutated |
| Efix-v5 | 0 | **18** | Named specific tools; broadest picked on safety-first |
| **Efix-v6** | **0** | **18** | Invert default: narrow scope default, widen only with justification; interpretation narrow but no inspection ("F75-behavior") |
| Efix-v7 | 10 | 12 | v6 + step-5 inspection duty; F75 defeated |

**Five of six non-v7 Efix cells contradict.** Only v3 (which round-16 flagged as "workflow didn't fire — too heavy") stays at 0. Efix-v6's contradiction is the load-bearing one: round-16 identified v6 as the cell that "fixes interpretation but not behavior" (0 tool calls despite narrow reading), grounding the F75-interpret / F75-behavior two-layer decomposition. Under clean spec, v6 produces 18 tool calls with the same narrow interpretation the round-16 commentary quoted verbatim — no F75-behavior residue.

**F75-behavior scope re-narrowed.** Efix-v6 was one of two round-16 pillars for F75-behavior (E17 is the other). Efix-v6 loses that role; F75-behavior for gpt-5.5/xhigh reduces to the E17 diagnostic path only.

**Design consequence.** The "pick step vs criterion" structural claim is dead on gpt-5.5/xhigh for the spec-level Efix chain. Various criterion refinements (v1 enumeration, v2 three-scope, v4 imperative, v5 named-tools, v6 narrow-default) all defeat F75-interpret under clean spec. The "elimination beats criterion-fixing" reading was contamination artifact for 5 of 6 comparisons.

**Retained.** Efix-v7 clean magnitude (12) closely matches round-16 (10); v7 is not doing spec-design work substantially different from v6-clean. Both defeat F75-interpret; v7's step-5 addition contributes 2 extra tool calls at best.

**Efix-v3 residual.** Only spec-body cell that still blocks. Round-16's "state-primary step too heavy" description survives. Some spec designs genuinely disrupt workflow firing; the mechanism ("weight of workflow steps overloads the compose budget") may be related to F84 text-mandate suppression.

Named contradicted (structural claim) in round-21.

### F78 E17 F75-behavior persistence — CONFIRMED

E14-E17 test the pick-step design axis at the *task-message* level against the (already-clean since round-18) `identity-outcome-framing-clean.md`. Round-16 measurements were on `identity-outcome-framing.md` before it was stripped. Round-21 re-runs under the round-18 clean spec:

| Cell | Round-16 | Round-21 clean | Meaning |
|---|---|---|---|
| E9 | 0 | 0 | Enumeration alone (word-matching evaluation) does not defeat F75 — MATCHES |
| E14 | 0 | **12** | Pick-frame removed — round-16 result contamination-driven |
| E15 | 0 | 0 | Anti-circularity + "useful" outcome — MATCHES (broad still picked as "useful") |
| E16 | 0 | 0 | Why-write-this motivational reframe — MATCHES (motivation-vs-pick decoupling holds) |
| **E17** | 0 | 0 | Pick-step eliminated, motivation → F/P derivation — MATCHES (F75-behavior persists) |

E9/E15/E16/E17 reproduce their round-16 clean outcomes. E14 flips. The critical finding — E17's F75-behavior persistence — replicates cleanly: the agent correctly identifies inspection as Permitted via the motivation-derivation, and still does not inspect. This is the sole surviving F75-behavior evidence on gpt-5.5/xhigh after round-21's Efix-v6 refutation.

**Design consequence.** F75-behavior as an independent layer is now supported by exactly one clean cell (E17) on gpt-5.5/xhigh. The two-layer decomposition survives at reduced confidence. On R1/Qwen-thinking (F85 evidence), F75-behavior remains supported at parse-time-translation level via `/tmp/reasoning-probe.py` reasoning-trace quotes.

**E14 contradiction (secondary).** Removing the pick-with-justification frame produces 12 tools under clean spec vs 0 under contaminated. Suggests contamination-driven pre-commit-to-broad was happening on this task shape too; unclear whether the E14 diagnostic content or the framing.md base was primary. Not load-bearing for the structural claim.

Named confirmed for E17; E14 contradicted secondarily.

### F76 — SURVIVES (strengthened by above-floor test)

Round-14 measured labels-v2 at 0 tool calls on H17 with the caveat: baseline behavior sits at floor, so we can't distinguish "labels inert" from "labels irrelevant because F75-block dominates". Round-20 re-ran labels-v2-clean on H17 → 0 tool calls (still at floor). Round-21 introduces H18 (no "Don't act yet") to lift the baseline off the floor:

- `identity-outcome-framing-clean.md` + H18: **13 tool_use** (above-floor baseline established)
- `identity-outcome-labels-v2-clean.md` + H18: **11 tool_use**

The 2-tool-call difference is within run-variance for gpt-5.5/xhigh at n=1. Labels-v2 behaves within noise of the plain framing baseline when F75 is not the dominant force. Labels alone are not doing meaningful behavioral work — the ID-requirement + classification framework is inert at the behavioral level under both floor and above-floor conditions.

**Design consequence.** F76's structural claim ("labels alone don't defeat F75; H19's affirmative-permission element is the F75-defeating part") is now supported by both floor and above-floor evidence. Labels are structurally inert as a behavioral lever. Any label-based classification design must pair with affirmative content that does the interpretation work.

**Retained caveats.** n=1 per cell. Labels-v2 vs framing baseline delta of 2 tool calls could be genuine or noise. Direction is unambiguous.

Named strengthened in round-21.

### F90 — Same-day mechanism check (implicit; not re-measured this round)

Round-20 named F90 as "frontmatter meta-narrative operates as behavioral instruction on gpt-5.5/xhigh; effect direction depends on narrative form." Round-21's 22 clean re-runs deepen the base of evidence: 15 of 22 cells (F79 x4, F84 x3, F77 x2, F78 Efix x5, F78 E14) contradict round-16/17/18 findings by producing substantially more tool calls under clean spec. Direction is consistent — contamination was suppressing tool calls in the "v_{N-1} failed because X" narrative form.

**Additional signal.** F78-Efix-v3 (round-16 "too heavy" characterization) survives cleanly, and F78-E9/E15/E16/E17 (clean spec was already used in round-16) match round-16 measurements. This isolates the contamination effect to specs that were contaminated in round-16 and now aren't, ruling out temporal or run-variance drift as the primary explanation.

**Scope retained.** F90 remains n=1 per pair; cross-model still untested.

## Consequential implications

**Round-16/17/18 findings are broadly at risk beyond the round-20 flagship contradictions.** Round-21's 15 additional contradictions demonstrate the contamination effect was not limited to a handful of load-bearing cells; it affected the entire round-16 Efix-v1..v6 chain, the F77 phase-2 escalated variants, the F79 passive-trigger axis, and 3 of 4 F84 intermediate-step variants. The following consolidated F-label updates are needed in the main file:

- **F75-behavior** — Round-16 originally rested on two pillars (Efix-v6 spec-level + E17 diagnostic-level). Efix-v6 collapses under clean spec. E17 survives. The layer is now supported by one clean cell on gpt-5.5/xhigh, plus the F85 reasoning-model traces (R1, Qwen-thinking) as separate evidence. Sharpen the F75-behavior scope: on gpt-5.5/xhigh, only the diagnostic-only motivation-derivation path (E17) produces F75-behavior residue; spec-level workflows (v6, v7) do not.
- **F78 Layer 2 pick-step-elimination** — for gpt-5.5/xhigh at the spec level (Efix chain), CONTRADICTED. Multiple criterion refinements defeat F75-interpret; elimination is not required. The finding may still hold at the task-message level (E14-E17 comparison) but the load-bearing spec-level evidence is gone.
- **F79** — CONTRADICTED across v1/v4/v5/v7 for gpt-5.5/xhigh. Passive triggers work under clean spec. Cross-model untested.
- **F77 phase-2 escalated variants** — CONTRADICTED for v2 (anti-avoidance) and v3 (certainty audit); v1 (base accuracy) survives. Round-15's "specification lock is the only path" reframes to "escalated orthogonal pressure is another path."
- **F84** — CONTRADICTED for spacetool/commentaryspace/bashcomment mechanism; only trailing no-op gate provides modest late-stage grounding. Reframe from "workflow + intermediate step defeats F80" to "trailing no-op gate buys extra consolidation cycles; text-mandate mid-workflow re-blocks."
- **F76** — SURVIVES + strengthened. Above-floor test confirms labels are structurally inert.
- **F75-interpret** — Under clean specs, various criterion designs (Efix-v1 through v6) do defeat F75-interpret on gpt-5.5/xhigh. The round-16 characterization of "systematic broad-default bias survives criterion reframing" was contamination-driven. Interpretation is more malleable than round-16 read it.

## Per-round contamination audit (added post-round-21)

Round-19 Phase-6 characterized contamination severity in Categories A/B/C but only inventoried round-13+ specs. Round-21's findings — particularly that Efix-v1..v6 all contradict, even v1 which had one of the weakest Category-A frontmatters — expose the Category B/C classification as under-tight. Below is a per-round status table with the actual load path and frontmatter category verified this round.

| Rounds | Findings | Load path | Frontmatter category | Contamination status |
|---|---|---|---|---|
| **1-7** | F1-F13, F17, F20; R070/R090/R002 stack | Committed `opencode/agents/min.md` → `agent.load()` via `config/agent.ts:105-130` → gray-matter strips frontmatter (round-19 Phase-1 verified) | Category B in file, stripped at load | **CLEAN** (verified strip; assumed disk-load path) |
| **8-10** | F30-F64 on V5 fixture + identity.md | Committed `opencode/agents/identity.md` — same disk-load path | Category B, stripped at load | **CLEAN** (same assumption) |
| **11** | F65-F67 on identity-outcome.md v1-v5 | Committed `opencode/agents/identity-outcome.md`, iterated in-place | Category B, stripped at load | **CLEAN** (same assumption; v1-v5 were sequential in-place edits of the committed file) |
| **12** | F68/F69 on min-N* + diag-v1 cells | `/root/experiment-materials/*.md` via `{file:...}` inline config | `min-N4v2/N5v2/N6/noG1/*-diag-v1.md` = **verbatim min.md frontmatter (Category C — 7 lines of design/investigation-trail comments)**; `identity-outcome-diag-v1.md` = **Category B**; **`identity-outcome-v4-diag-v1.md` = Category A** (frontmatter explicitly states *"Baseline expectation: F46 skip (matches v4 result on V5 fixture). If F46 breaks here, diag-v1 is not neutral."*) | **PARTIALLY CONTAMINATED / not re-run.** N4v2/N5v2/N6/N4/N5 low-severity Category-C; N1 (v4-diag-v1) is Category A and matches the F79/F80 profile |
| **13** | F70-F75 on maintainer-diag-v{1..5} | `{file:...}` inline config | Round-19 called v1-v5 Category B; verified this round — v1/v2/v3 are **Category B** (design intent only); **v4 and v5 are effectively Category A**: v4 enumerates added clauses; v5 states *"v4 named specific reference types … which defeated the test — any agent following the explicit hint would break F46 whether or not it had adopted the maintainer identity"* (mechanism claim + prior-outcome content) | **CONTAMINATED risk not verified.** v4/v5-associated cells (H6-H16) especially exposed. Not stripped, not re-run |
| **14-19** | F75-F89 | `{file:...}` inline config | Category A | **CONTAMINATED** in original runs; **stripped in rounds 20-21**; contradictions documented in round-20 + round-21 |
| **20-21** | F90 + all contradictions | `{file:...}` inline config on `-clean.md` variants | Frontmatter stripped | **CLEAN** |

**Load-bearing risks:**

1. **Rounds 1-11 CLEAN status rests on two premises:** (a) gray-matter actually strips frontmatter at `agent.load()` (verified round-19); (b) all rounds-1-11 invocations used the disk-load path (agent-name-only, not inline config). Premise (b) is not verified — if any round-1-11 probe used `{file:...}` inline config as a one-off, that measurement would be contaminated with the min.md/identity.md/identity-outcome.md frontmatter (Category B — one-liner references only, so effect probably small per round-19 categorization, but not zero given round-21 findings).

2. **Round-12 N1 (identity-outcome-v4-diag-v1 + diag-v1 on V5 fixture, F46 skip result)** rests on a Category-A frontmatter that states the expected outcome directly. Under F90, "expected outcome stated" is the strongest priming pattern. **N1's F46 skip may be contamination-driven** in exactly the F79/F80 shape — spec frontmatter said "expect skip," agent enacted skip. F68 (coherence-prerequisite) partially rests on N1/N3 as neutrality controls; N3 (min.md + diag-v1) is Category B/C. If N1 is contamination-driven, F68's incoherent-additions-get-filtered characterization has a hole.

3. **Round-13 v4/v5 (H6-H16 cells, F74 mechanism)** rest on Category-A-adjacent frontmatters. F74a (operational scope-closure), F74b (residual skip under strategic framing), and the compound-blocking model (H13/H16) all rest on measurements where the spec frontmatter enumerated the mechanism under test. Under F90, this is exactly the "v_{N-1} failed because X" narrative that caused F79/F80 contradictions. **F74a/F74b findings may be contamination-driven.** The v3-associated cells (F71/F72/F73) are on Category-B specs — lower-risk but not zero-risk.

4. **Category-B-effect not tightly bounded.** Round-21's Efix-v1 (Category-A but weakest frontmatter of the series — just *"v1 workflow attempt"* without prior outcome enumeration) contradicts by 11 tool calls. This suggests the F90 effect activates on generic *"Investigation trail: notes/compliance-check-failure-mode.md (round-N)"* references alone, not just on hypothesis-stating frontmatters. **Round-12/13 findings on Category-B specs are at meaningful risk**, contrary to round-19's characterization.

**Consequential:** The most exposed prior findings that have NOT been re-verified under clean spec:

- **Round 12 N1** (F68 coherence-prerequisite): Category-A frontmatter, F46-skip result matches F90-CONTAM shape. High risk.
- **Round 13 H6-H16** (F74a/F74b): v4/v5 are Category-A-adjacent; F74's two-mechanism decomposition rests on measurements with mechanism-under-test named in frontmatter. High risk.
- **Round 13 A-G maintainer cells** (F71/F72/F73): Category-B v1/v2/v3; F73's three-factor structure (surface pressure + maintainer collapse + authorship scope) rests on cross-cell comparisons. Moderate risk.
- **Round 12 N2/N4v2/N5v2/N6** (F69 rationale-vs-frame mechanism split, N6 anti-additive anomaly): Category-B/C. Moderate-low risk but not verified.

**Recommended follow-up (priority order):**

1. Strip Category-A-adjacent round-13 v4/v5 frontmatters; re-run H6/H9/H10/H11/H12/H13/H16 clean. Load-bearing for F74.
2. Strip Category-A round-12 v4-diag-v1 (N1 cell); re-run against V5 fixture. Load-bearing for F68.
3. Strip round-13 v1/v2/v3 maintainer frontmatters; re-run G1/G2/G3/G4 clean. Load-bearing for F73.
4. Round-12 N2/N4v2/N5v2/N6 min-N* re-runs. Lower priority given Category-C-adjacent status.
5. Spot-check rounds 8-11 by confirming from session logs whether invocations used disk-load or inline config. If any used inline config, targeted re-runs needed.

## Open (carried into round 22)

**Cross-model replication of F90 and cross-model contradictions.**
- F79/F84/F77/F78 contradictions all n=1 per cell on gpt-5.5/xhigh. Whether the contamination effect (or its absence) replicates on Claude Sonnet/Opus, K3, R1, Qwen-thinking is untested.

**F78 E10/E10v2/E11/E12/E13 not re-run.** These are declarative-rule additions on top of derivative spec variants (framing-ambig-as-context, framing-intent-rule, framing-caveats-as-context). Clean versions were created this round but not tested. Prediction: some will contradict, some will match. Lower priority given the Efix-v1..v6 sweep already contradicts the structural claim.

**F78 Efix-v3 mechanism.** Round-16's "too heavy" characterization for v3 survives cleanly. The mechanism (spec-body weight overloading compose budget) may generalize to explain F84 text-mandate suppression. Not investigated.

**F84 asymmetry (text-mandate vs trailing no-op gate).** The observation that text-producing mandates suppress inspection while trailing no-op gates preserve it is n=1 per cell across 4 cells. Replication + cross-fixture untested.

**F77 threshold mechanism.** v1 (bluff-permitted) → 0 tools; v2 (bluff-forbidden) → 16 tools; v3 (bluff + hedge-forbidden) → 20 tools. What specifically about the escalation crosses the threshold? Untested. Also: replicate at n=2/n=3 to confirm the threshold is stable.

**F75-behavior residual scope on gpt-5.5/xhigh.** E17 is now the sole clean gpt-5.5/xhigh cell showing F75-behavior. Combined fix (E17 diagnostic + inspection-duty task-message clause per round-16 open item E18) untested under clean spec. Whether F75-behavior on gpt-5.5/xhigh is defeatable by a purely task-message intervention is open.

**F78 E14 contradiction.** Re-run at n=2/n=3 to distinguish contamination effect from run-variance for this specific task-message shape.

**F76 magnitude replication.** Labels-v2 vs framing baseline delta of 2 tool calls on H18 could be within noise. n=2/n=3 replication of both cells would tighten the "labels inert" claim.

**Remaining Category-B specs.** `identity-outcome-maintainer-diag-v{1..5}.md` still carry unstripped Category-B frontmatter (round + design intent). Round-13 F70/F71/F72/F73/F74 findings rest on this spec chain. Given the round-21 pattern (F79 v1/v4/v5 all contradict, F78 Efix v1/v2/v4/v5/v6 all contradict), Category B may not be as benign as round-19 categorized it. Untested.

**F87b upstream fix.** opencode's `substitute()` at `packages/opencode/src/config/variable.ts:44-88` still reads `{file:PATH}` raw. A defensive strip in the config layer would eliminate the leak channel at source. Not addressed.

## Methodology (added this round)

**Batch parallel invocation.** Round-21 dispatched 22 opencode runs in parallel across 4 batches (F79 x3 + F84 x3 + F77 x3 first, then F78 x12 + F76 x2). Wall-clock: ~5 minutes for each batch; total runtime dominated by the longest individual cell (F79-v5 at 1552 rtok, ~2 minutes).

**Above-floor test design (F76).** Use H18-task (H17 minus "Don't act yet") as the baseline task where F75-block is inactive; measure both baseline spec and test spec on that shared task. Only meaningful if baseline is well above the 0-tool-call floor — F76 baseline was 13 tools, providing usable dynamic range.

**Tool count vs qualitative shape.** Round-21 relied on tool_use count + first-commentary quote + reasoning-token count for cell characterization, without per-cell subagent trajectory comparisons (round 20 used subagent comparisons). Trade-off: faster round completion at the cost of less nuanced per-cell narrative. Acceptable given the direction-level contradictions were clear from tool counts alone.

## Session anchors and artifacts

**Round-21 clean specs (all uncommitted, `/root/experiment-materials/`):**

- `framing-ambig-authored-v{1,2,3,4,5,6}-clean.md` (F78 Efix-v1..v6 base variants + F79 v1..v6)
- `framing-ambig-authored-v8-{spacetool,commentaryspace,bashcomment}-clean.md` (F84 remaining)
- `identity-outcome-framing-explore-clean.md` (H19; unused this round but stripped for future)
- `identity-outcome-labels-clean.md` (labels v1; unused this round but stripped for future)
- `identity-outcome-framing-accuracy{,-v2,-v3}-clean.md` (F77 phase 2)
- `framing-fix-v{1..7}-clean.md` (F78 Efix chain)
- `framing-intent-rule-clean.md`, `framing-caveats-as-context-clean.md`, `framing-ambig-as-context{,-v2,-v3}-clean.md` (E-cells auxiliary; unused this round)

**Round-21 output directory:** `/root/experiment-materials/round21/` — 22 jsonl files, one per cell.

**Runner:** `/tmp/run_r21.sh` — same shape as `/tmp/run_r20.sh` from round 20; bypasses `agent-tools run --desc` wrapper.

**Reference contaminated sessions:** see `round-16.md` (Efix-v1..v7, E9/E14-E17), `round-15.md` (H21-M/M2/M3 accuracy chain), `round-17.md` (v1/v4/v5), `round-18.md` (F84 4-cell matrix). All were confirmed suspect in round-19 Phase-6 inventory; round-21 measurements are the clean re-runs.

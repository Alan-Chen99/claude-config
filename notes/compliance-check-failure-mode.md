# User-direction compliance-check failure in opencode agent prompts

## What this doc is

A log of **validated findings** from probing opencode agent prompts on the `work2/` V5 fixture and `work-maintainer/` maintainer fixture. Round-by-round detail lives under [`compliance-check-failure-mode/`](./compliance-check-failure-mode/) — one file per round. This main file keeps only findings that survive scrutiny, working production specs, current open work, and pointers.

## Rules for this doc

- **500-token budget per round.** When adding a new round entry to the Round index or updating a validated finding with new evidence, the total tokens added to this file across all edits for that round must not exceed 500. Verify with `agent-tools count-tokens --file <path>` before and after. Detail belongs in the per-round doc, not here.
- **Whole file under 10k tokens.** Prune obsolete pointers, retired findings, and speculative open work when adding. If an addition would exceed 10k, cut older content of equal or greater size before merging.
- **No unverified magnitudes.** When quoting a clean-vs-contam delta, the contam session must have been opened via `agent-tools opencode-pretty` and both crossing-axis and tool_use-axis measured directly this round. Copying counts from prior narrative language is the failure mode that necessitated round 24.

## Fixtures

- **V5 fixture:** `/root/claude-config-work2/`. Standard 4-part diagnostic task extracted at `/tmp/V5-task.md`.
- **Maintainer fixture:** `/root/claude-config-work-maintainer/`. Git-surgery rewrite of `work2/`; PROMPT.md rewritten in maintainer-authored voice. Task at `/root/experiment-materials/V5-minimal-task.md` (7 lines, ends *"Don't act yet."*).
- **F75 fixture:** identity-outcome-framing agent + `/root/experiment-materials/H17-task.md` (5 lines, ends *"Don't act yet."*).

## Working production specs

- `opencode/agents/min.md` — round-7 R002 stack + G1-G6 gate via `agent-tools min.gate`. Committed. Diagnostic-minimum baseline.
- `opencode/agents/identity.md` — round-10 values framework. Committed as parallel track.
- `opencode/agents/identity-outcome.md` — round-11 outcome-anchored variant. Committed as parallel track.
- **Downstream operational spec:** `opencode/agents/alan-default-ids.md` (annotated delta against codex `base_instructions`) — this is what actually runs day-to-day.

No post-round-7 finding has produced a committed change to `alan-default-ids.md`.

## Sections

Each section groups rounds that pursued a single research thread. Findings listed under a section are those that survived subsequent scrutiny; retired or superseded findings live only in the per-round files.

### S1 — Rule-collision archetypes and the impossibility theorem (R1-R7)

Iterated on colliding-rule archetypes; landed at R002 stack (round 7) as diagnostic-minimum baseline.

- **F31 — impossibility theorem.** Agent cannot reliably (1) enumerate frames for ambiguous task, or (2) from within pinned frame, notice contradiction with data and raise toward unpicked frame. Substitute: **transparency about the pinned frame** — communicate what the agent chose so the user can redirect cheaply.
- **F57 — no stable "instruction" definition.** Any spec referencing "instructions" implicitly sets per-list enumeration scope; agent supplies no stable model of what counts. Rule-writer must decide what belongs in the class. R9.

### S2 — V5 fixture and values-framework specs (R8-R11)

Built V5 fixture and the two parallel values-framework specs (identity, identity-outcome). Per R21 audit these disk-loaded runs are clean. No new mechanism findings retained beyond the specs themselves (see Working production specs).

### S3 — Spec-mechanism probes on identity-outcome-framing (R12-R18)

Maintainer paradigm (R020 fork, R12) opened a probe series into how spec content changes crossing behavior on F75-vulnerable tasks. Category A/B contamination was diagnosed at R18-R19; the surviving structural and model-behavior findings are:

- **F76 — declarative labels behaviorally inert.** H18 gpt-5.5/xhigh clean: labels-v2 (11 tools) ≈ framing baseline (13 tools). Label classification (R### = rule, G### = guidance) requires affirmative content doing the interpretation work. R14/R21.
- **F78 — pick-step designs defeat F75-interpret under clean spec.** 5/6 non-v7 Efix cells on gpt-5.5/xhigh clean (v1/v2/v4/v5/v6 = 11-22 tool_use vs contaminated 0). R16 "elimination beats criterion-fixing" reading was contamination artifact. R21. **E17 task-message diagnostic** (why-did-the-writer-write-this + F/P split): 0 tool_use despite explicit permission — sole surviving F75-behavior at task-message level. R16/R21.
- **F62 — Codex-backend policy reduces reasoning to headings.** `chatgpt.com/backend-api/codex/responses`: headings only (~39 chars); `api.openai.com/v1/responses`: paragraphs (~363 chars). Mitigation: `OPENCODE_AUTH_CONTENT='{"openai":{"type":"api","key":"$OPENAI_API_KEY"}}'`. R18.
- **F85 — parse-time translation on reasoning models.** DeepSeek R1/Qwen3-thinking translate "Don't act yet" into function-call prohibition in first 4 sentences. H17-nodontact control shifts to "gather information." R18.
- **F86 — model-class-specific default for "Don't act yet".** Broad (F80 fires): gpt-5.5/xhigh (under contam only per R20), DeepSeek R1, Qwen3-thinking. Narrow (no block): Kimi K3, confirmed via H17-notools discriminator. R18.

### S4 — Contamination diagnosis and cleanup (R19-R24)

R19 discovered `{file:PATH}` frontmatter contamination affecting every R13+ inline-config probe. R20-R21 re-ran 5+22 cells clean; R22-R24 audited earlier mechanism claims for magnitude errors and model-version confounds.

- **F87b — `{file:PATH}` template inlines file raw.** opencode's `substitute()` at `packages/opencode/src/config/variable.ts:44-88` inlines the entire file (frontmatter included) as the config value; via `"prompt": "{file:agent.md}"` inside `OPENCODE_CONFIG_CONTENT` it becomes `agents[name].prompt` and flows to `session/llm.ts:116` as system prompt. R19.
- **F88 — `agent-tools run --desc` argv leak.** Description string passed as argv, readable via `ps aux` or `/proc/<pid>/cmdline`. Fix `--hide-cmdline` deployed. R19.
- **F90 — frontmatter as behavioral instruction on gpt-5.5/xhigh.** Same-day paired matrix on gpt-5.5/xhigh (same model/task/fixture; only frontmatter differs): *"v_{N-1} failed because X, v_N tests Y"* narratives suppress inspection; *"Prediction: if X..."* narratives are variable-direction; task-adjacent permission dominates any frontmatter signal. Effect size 0 → 15-63 tool calls on load-bearing cells. R20.
- **Retracted / retired.** R20-R21 contradicted F79/F80/F84/F77(v2,v3)/F78-elim. R22 N1/H6/H9 directional re-runs found earlier magnitudes wrong (totals 42→45, 46→63, 56→51; not 0→45 etc.). R23 "F72 contradicted" / "F74a contradicted" claims retracted due to contam=gpt-5.4 vs clean=gpt-5.5 model-version confound. R24 documented F46 semantic drift.
- **F72 current status.** Neither confirmed nor contradicted. R13's characterization ("worker-side reads happen under minimal task; author-side crossing does not without task/clause pressure") remains operative. Isolating the frontmatter variable requires gpt-5.5/xhigh contam re-runs of R13 Runs C/E/F or gpt-5.4 clean re-runs of R23.

### S5 — Fully-specified task iteration and precedent-anchoring (R25-R28)

Iterated task design on identity + identity-outcome under maintainer fixture. Established that task-side role and structure produce disk-committed maintainer-frame interpretation; discovered precedent-anchoring as a task-inheritance mechanism.

- **F91 — task-side role establishment produces editor-frame alignment without spec changes.** `V5-plan-task-v3.md` on identity + identity-outcome (frontmatter-clean, maintainer fixture): 6A+1A-tilt both cells across 7-item rubric. Editor-frame (PROMPT.md as external artifact to revise) is task-level-activated without spec revision. n=1 per cell. R25/R27.
- **F92 — commitment-forcing task design produces disk-committed maintainer-frame evidence.** `V5-execute-task-v1.md` (execute permission + pause-and-request-approval + PROMPT.md/tasks/harness edits saved + exact ralph invocation named): both cells 7A/7 with disk-committed artifacts; neither invoked ralph despite permission; task-side gate sufficient. R27.
- **F5d — precedent-anchoring (n=2 R27-R28).** Both specs inherit task-supplied `ralph … run --continue` invocation, dispatch medium, three-section pause template without evaluation despite explicit *"you may modify"*. Three surface failures unify (no strategic alternatives / medium-as-default / ritual-as-goal). Phase-2 precedent-swap (v2 strips `--continue`) → agent treats precedent as anchor with deviation-check reasoning. R28 iteration F3d→F5d: **concrete-enumeration structure is load-bearing for value-directive effect; form-consistency ≠ effect-consistency**.

### S6 — Frame-level suppression and crossing motivation (R29-R33)

Probed whether value #2 (frame-questioning) fires on precval variants, then multi-axis stress-tested across kimi-k3 vs gpt-5.5 × identity-outcome-clean vs no-value-#2 × broken vs fixed fixture. Discovered a fixture-alias confound; cross-cell synthesis on kimi crossings produced a motivation taxonomy.

- **F93/F94 — kimi-crossing taxonomies retained (R32).** F93 5 decision patterns, F94 7 content-flow types. F95 baseline-fixed ML frame = scratchpad *"Overfitting review"* + user cue; F97 R29 P9 value-#5 firing via P9-vs-E0 differential (flagged R35 F108 for n=3 replication); F98 downgraded to paraphrase.
- **F99 — R31 audit-quality issues.** Unreliable line numbers, systematic over-reading, F62 confound. R32 protocol: re-derive from raw content, `@L<n>[i]` refs, flag F62.
- **F100 — intent-outcome asymmetry.** Kimi crossings' stated intent narrower than downstream outcome (n=6 gpt-5.5 followup forks).
- **F102 — no2-broken fixture-bug discovery = value-#2-removal positive R30 didn't credit.**
- **F103 — reframed R37→R44.** 6/6 *"did not consider"* self-reports honest under R44 (active-consideration filter, not confabulation).
- **Superseded.** R29 Shape 2 (value #2 suppression) → R32 F97 (value #5 precval). R31 attributions replaced by R32.

### S7 — Wire-level model diff and pivot to raw-evidence artifacts (R34-R39)

Instrumented F62 to capture wire-level diff of opencode → gpt-5.5 vs → kimi-k3. Diagnosed R30-R35 as re-mining sessions and stacking attribution errors; pivoted to raw-evidence timeline artifacts via a new `session-timeline` skill; rewind-fork probe then discriminated candidate-generation from in-flight weighing.

- **F104 — hardcoded verbosity default** at `transform.ts:1140` (`textVerbosity: "low"` for gpt-5.x; kimi has none). Refuted by R35 F108 + R37 F119 for pointer-fate; may still apply to preamble style.
- **F105 — provider-prompt skip when `agent.prompt` set** (`llm.ts:116`). 8 provider-specific prompts (`gpt.txt`=brevity/quality; `kimi.txt`=action) but `agent.prompt` REPLACES them entirely. R30's `{file:...}` triggered agent-prompt path → both models skipped provider content. R30 visible system prompt bit-identical except model-name line. Hidden trap for setups without `agent.prompt`.
- **Session-timeline pivot (R35).** Diagnosed R30-R35 as re-mining sessions and stacking attribution errors; separated raw-evidence layer (timeline artifacts at [`experiments/`](./compliance-check-failure-mode/experiments/)) from interpretive layer via [`session-timeline` skill](../skills/session-timeline/SKILL.md). Future rounds re-derive attributions from timeline artifacts before treating as load-bearing.
- **F115 — gpt-5.5 established same older-loop relation as kimi from strictly in-cwd sources.** Zero focus-path reads. R37.
- **F116 — RETRACTED by R44.** Original claim: P1 "never on shortlist" self-report contradicted by P5 rewind-fork evidence of candidate-set inclusion. R44 showed P5's enumerations were probe-elicitation artifacts (see F122); P1 was honest self-report. P1 + R44 converge on "not actively weighed." Confabulation attribution retired.
- **F117 — REFINED by R44.** Original claim: old-worktree paths ARE in candidate set at all 3 pre-decision rewind points. Refined: paths are **reconstructible-under-enumeration-pressure**, not actively weighed. Under R43's `awareness_only` escape hatch (R44), gpt-5.5 flags them as reconstructive at 3/3 rewinds.
- **F118 — target-framing inherited from task-message @L1, stable from L6.** @L14[2] preamble is articulation not decision. R37.
- **F119 — SHARPENED by R44.** Task-message target-inheritance in gpt-5.5 filters old-worktree paths OUT of the first-pass-planning active-consideration space (not just verdict-rejects them). Kimi's target-inheritance is looser — current-PROMPT.md pointer triggers active consideration. Model-difference is at active-consideration layer, not rejection-axis layer (which is shared). R37 also adds F113 (kimi L5 pointer+relevance-signal not imperative, 4/4 *"for context"*), F114 (4/4 kimi scope older-loop identity BEFORE firing).
- **F120 (retired by R39).** R38 abstract "text scope" rule ineffective; R39 concrete-drift rule fires. See F121.
- **F121 — concrete intent-drift rule shifts justification, not verdict.** R39 same-author-same-commit criterion + 4 drift patterns (mandate-slot / status-label / decision-record Reasoning / cross-worktree). Effects: baseline reads previously-dropped in-cwd sources; P5 drop-reasons abandon "already summarized" claim; L12 model applies check to its own scratchpad + decisions.md (READ); model absorbs rule into rewritten PROMPT.md. Old-worktree verdict unchanged. **Rescoped by R44**: drift-rule operates at reconstructive-justification layer, downstream of the active-consideration filter — which is why it never reached the verdict.

### S8 — Bias-controlled probe iteration and active-consideration filter (R40-R44)

Iterated R37 P5 through 4 refinements to control elicitation bias. Composite finding: gpt-5.5's non-crossing on old-worktree paths is an active-consideration-space filter (task-message target-inheritance), not a rejection-axis decision. Detail per round-file.

- **F122 — Ex-ante utility tagging methodology.** Tag candidates by what a fork-point reasoner can know ex-ante (path/filename/prior-mentions), not retrospective content. PROMPT.md is ex-ante (a) task-identity; scratchpad + decisions.md are ex-ante (b) findings-reuse. Mid-round retraction: 10/13-items-(a) → 4-candidates-(a) all-PROMPT.md.
- **F123 — Design-B probe bias suite (R42-R43).** 5 bias sources: `chosen_next_action` batch-selection frame; three-option verdict enum with defer as middle-ground attractor; paired-array bundling pressure; aggregate-slot leakage (5/11); enumeration-completeness inflation. R43 fixes: `next_turn_tool_calls_if_any` (not batch selection), free-text disposition, anti-bundling, no aggregate slots, `awareness_only` flag with "err toward false."
- **F124 — Cross-model non-crossing is at active-consideration layer, not rejection-axis layer.** Under R43: kimi L6 emits 2/2 old-worktree as awareness_only=false, disposition "would read this turn" at slots 1-2 — matches baseline READ. Gpt-5.5 L6/L12/L16 emits 3/3 as awareness_only=true; L16 emits 0 candidates with F62 heading *"Confirming no further candidate reads before edit"* — matches baseline NON-READ. Aggregate rejection axes (spec-frame + adequacy + drift) identical across models; differentiator is the first-pass-planning filter. R42-R44.
- **F125 — R37 P1 restored as convergent evidence.** F116 retracted (R44). P1 Design-A structured JSON 6/6 "never on shortlist" + R44 Design-B 3/3 awareness_only=true = cross-probe convergence with different rationalization-risk profiles. Structured-JSON self-report viable on gpt-5.5; F62 blocks only paragraph-form reasoning-summary.
- **Design A/B/C framework** at [`experiments/probe-design-a-b-c__methodology.md`](./compliance-check-failure-mode/experiments/probe-design-a-b-c__methodology.md); R43 probe wording at [`experiments/p5-probe-r43__refined-schema.md`](./compliance-check-failure-mode/experiments/p5-probe-r43__refined-schema.md).

## Round index

Each round file is a self-contained record. Load only what you need. Entries below are **what was done and brief why** — no conclusions.

| Round | File | What / why |
|-------|------|------------|
| 1-7 | [`01-02`](./compliance-check-failure-mode/round-01-02.md) [`03-04`](./compliance-check-failure-mode/round-03-04.md) [`05`](./compliance-check-failure-mode/round-05.md) [`06`](./compliance-check-failure-mode/round-06.md) [`07`](./compliance-check-failure-mode/round-07.md) | Iterate rule-collision archetypes to find a diagnostic-minimum spec. |
| 8-11 | [`08`](./compliance-check-failure-mode/round-08.md) [`09`](./compliance-check-failure-mode/round-09.md) [`10`](./compliance-check-failure-mode/round-10.md) [`11`](./compliance-check-failure-mode/round-11.md) | Build V5 fixture + identity / identity-outcome value-framework specs. |
| 12-13 | [`12`](./compliance-check-failure-mode/round-12.md) [`13`](./compliance-check-failure-mode/round-13.md) | Fork R020 maintainer paradigm; probe crossing under task/spec variants. |
| 14-18 | [`14`](./compliance-check-failure-mode/round-14.md) [`15`](./compliance-check-failure-mode/round-15.md) [`16`](./compliance-check-failure-mode/round-16.md) [`17`](./compliance-check-failure-mode/round-17.md) [`18`](./compliance-check-failure-mode/round-18.md) | Spec-mechanism probes F75/F76/F77/F78/F79/F80 on identity-outcome-framing. |
| 19 | [`19`](./compliance-check-failure-mode/round-19.md) | Diagnose `{file:PATH}` frontmatter inlining; plan cleanup sweep. |
| 20-21 | [`20`](./compliance-check-failure-mode/round-20.md) [`21`](./compliance-check-failure-mode/round-21.md) | Clean re-run 5+22 cells to audit prior spec-mechanism claims. |
| 22-24 | [`22`](./compliance-check-failure-mode/round-22.md) [`23`](./compliance-check-failure-mode/round-23.md) [`24`](./compliance-check-failure-mode/round-24.md) | Audit magnitudes and model-version confounds in R13/R22/R23 claims. |
| 25 | [`25`](./compliance-check-failure-mode/round-25.md) | Iterate leg-2 fully-specified task on identity + identity-outcome (8 variants). |
| 26 | [`26`](./compliance-check-failure-mode/round-26.md) | **SUPERSEDED.** Q0 conflation claim + rubric item 8 retracted. |
| 27 | [`27`](./compliance-check-failure-mode/round-27.md) + [`27-precedent`](./compliance-check-failure-mode/round-27-precedent-anchoring.md) | Test hybrid pause-permission task with commitment-forcing design; document precedent inheritance. |
| 28 | [`28`](./compliance-check-failure-mode/round-28.md) | Rerun R27 Phase-1 both specs + 3 precedent-anchoring probes (P1/P9/P10). |
| 29 | [`29`](./compliance-check-failure-mode/round-29.md) | Probe frame-suppression on P9 (identity-outcome-precval). |
| 30 | [`30`](./compliance-check-failure-mode/round-30.md) | Multi-axis stress-test of R29: model × spec × fixture-state + 6-cell gpt-5.5 E-series. |
| 31 | [`31`](./compliance-check-failure-mode/round-31.md) | **SUPERSEDED by R32.** 10-cell crossing audit for kimi motivations. |
| 32 | [`32`](./compliance-check-failure-mode/round-32.md) | Re-derive R31 via 7 subagents with `@L<n>[i]` refs to guard against F62 confound. |
| 33 | [`33`](./compliance-check-failure-mode/round-33.md) | Cross-cell kimi synthesis + n=6 gpt-5.5 followup forks on stated intent. |
| 34 | [`34`](./compliance-check-failure-mode/round-34.md) | Wire-level diff of opencode → gpt-5.5 vs → kimi-k3 under F62 instrumentation. |
| 35 | [`35`](./compliance-check-failure-mode/round-35.md) + [`experiments/`](./compliance-check-failure-mode/experiments/) | Pivot: separate raw-evidence layer (`session-timeline` skill) from interpretive layer. |
| 36 | [`36`](./compliance-check-failure-mode/round-36.md) | Harden skill (5 overfit-example edits + stderr fix); build kimi × 4 evidence corpus. |
| 37 | [`37`](./compliance-check-failure-mode/round-37.md) | Interpret R36 corpus + gpt-5.5 P1 self-report and P5 rewind-fork probes. |
| 38 | [`38`](./compliance-check-failure-mode/round-38.md) | Test spec-level "text scope is what the text states" rule via P5 rewind-fork at 3 pre-decision points; null result. |
| 39 | [`39`](./compliance-check-failure-mode/round-39.md) | Test concrete intent-drift rule (same-author-same-commit criterion + 4 enumerated drift patterns); baseline reads previously-dropped in-cwd sources, P5 drop-reasons abandon false-coverage claim (verdict unchanged per F119). |
| 40 | [`40`](./compliance-check-failure-mode/round-40.md) | Content-first probe (`probable_contents` + `what_each_would_tell_you` + per-utility for/against arrays) on R39 gpt-5.5 baseline at L6/L12/L16; surfaces (a)-utilities R39 slot hid but aggregate `reasons_against` still collapses. |
| 41 | [`41`](./compliance-check-failure-mode/round-41.md) | Per-utility `current_status_of_this_answer` probe on same 3 rewinds; surfaces frame-shift + contents-unread + partial-adequacy status shapes; ex-ante-vs-ex-post tagging correction mid-round. |
| 42 | [`42`](./compliance-check-failure-mode/round-42.md) | R41 probe applied to `kimi-baseline-fixed` L6 fork; verdict DEFER contradicts baseline READ; kimi reasoning box reveals 5 bias sources. |
| 43 | [`43`](./compliance-check-failure-mode/round-43.md) | Bias-controlled probe (removed batch-frame, defer-enum, bundling, aggregate slots; added `awareness_only` flag) on kimi L6 fork; recovers baseline READ disposition. |
| 44 | [`44`](./compliance-check-failure-mode/round-44.md) | R43 probe applied to gpt-5.5 R39 baseline at 3 rewinds; 3/3 old-worktree candidates flagged `awareness_only=true`; L16 emits 0 candidates; refines F117 and sharpens F119. Retires F116. |

## Open work

- **P5b — drop-list-only rewind-fork probe**: reword P5 to ask only for `verdict: "read"` candidates. Discriminates genuine in-flight weighing from probe-triggered enumeration. Cheap (3 rewind × E0). See R37 Open.
- **Task-message ablation**: rewrite V5-execute-task-v1 paragraph-1 to explicitly include pointer targets in "current state"; rerun gpt-5.5 × 3. If crossing emerges, task-message inheritance is the load-bearing gate per F118.
- **Fixture ablation**: strip L9 clause (b) *"invalid/idea only"* from PROMPT.md; rerun P5 at L6. Discriminates L9-caveat vs adequacy-check as drop-driver.
- **L1-rewind probe**: fork E0 at msg L1 (drops all assistant responses); inject P5 probe. Captures earliest possible candidate-generation state, before pointer entered assistant context.
- **F108 n=3 replication under matched conditions** (verb=low + no `--continue` + clean; verb=low + `--continue` + clean; precval + no `--continue`). Load-bearing after R35 E0-repro deletion contradicted E-series 5/5 demote — establish whether outcome distribution differs by condition or is uniform noise. Also required for R32 F97 value-#5 re-verification.
- **Cross-model spot checks.** Claude Sonnet/Opus on F75 baseline; K3/R1/Qwen on F78 Efix-v7; would test gpt-5.5-specificity of F76/F78/F90.
- **F87b upstream fix** (opencode `substitute()` defensive strip on markdown). Not addressed.
- **Fixture-hygiene discipline** (from retracted R26, strengthened by R31 F98). Reset before each cell: `git reset --hard 66ef67b && git clean -fdx .ralph/`. Scratchpad reset load-bearing too — prior workers' "context only" scratchpad entries carry contamination transitively.
- **Deferred R12-R25 empirical rebuilds** (F72 status; Round-12 N3/N4/N5 clean; G1-G4-clean; F91 replication; R25 rubric refinements; n=2/n=3 replication of R20-R22 directional contradictions). See per-round files.

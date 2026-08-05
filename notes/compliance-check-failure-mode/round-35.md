# Round 35 — Motivation-trace mining, ablations, then pivot to building the session-timeline skill

> **Direct predecessors: [`round-33.md`](./round-33.md), [`round-34.md`](./round-34.md).** R33 catalogued 4 kimi-crossing motivations (task-continuity / textual reconciliation / format-convention / task-closure) and F103 self-reports said gpt-5.5 "did not consider" any. R34 identified `textVerbosity: "low"` (F104) as candidate causal driver via wire-level diff. R35 opened by continuing that interpretive line — motivation-trace mining, verbosity ablation, Mot 2 step decomposition, directed introspection — then **pivoted mid-round to a structural fix for the pattern that produced R30–R35's instability**.

## Pivot — from interpretive re-mining to raw-evidence artifacts

By mid-R35 the diagnosis was clear: rounds 30–35 were repeatedly re-mining the same ~10 sessions to answer slightly different questions, and each pass introduced attribution errors that a later round corrected. R31 was audit-corrected by R32. R32/R33 got action-conflation-corrected by R35 F110. R35 F106 was refined by R35 F110/F111 in the same round. The interpretive layer kept moving because the raw-evidence layer was entangled with it — every round's findings were built by re-reading sessions and constructing narrative, so every correction touched both layers.

Structural fix: separate the two layers.

- **Raw-evidence layer**: focus-directed timeline artifacts at [`experiments/`](./experiments/) — chronological, factual, no interpretation. Produced by the [`session-timeline` skill](../../skills/session-timeline/SKILL.md) via subagent extraction. Each artifact answers *"what is in the log relevant to this focus"* and stops there.
- **Interpretive layer**: rounds cite timeline artifacts as evidence. Future corrections touch only the interpretation; the evidence artifact stands.

R35 pivoted to building the skill and validating it on one pilot (kimi-no2-broken × old-worktree-reads focus, at [`experiments/kimi-no2-broken__old-worktree-reads.md`](./experiments/kimi-no2-broken__old-worktree-reads.md)). The pilot went through 3 iterations to converge invariants (positive-over-negative descriptions, skeleton-then-jq workflow, no full-pretty-render, no relevance-classification labels).

**Status of R30–R34**: pre-pivot rounds. Their structural findings (R34 F104 verbosity default, R34 F105 provider-prompt-skip, R25 F91 / R27 F92 task-design findings, R30 fixture-fix procedure, R19 F87b/F88 contamination mechanisms) are source-verified or wire-level and stand as-is. Their per-session interpretation (motivation attributions, decision-mechanism taxonomies, R32 F97 value-#5 attribution, R33 F100-F103 motivation classes) rests on re-mined session content that later rounds have already corrected once; those interpretations should be re-derived from timeline artifacts before being cited as load-bearing.

**Status of R35's pre-pivot findings (F106-F112 below)**: retained for continuity but same caveat as R30-R34 interpretation. Load-bearing use should wait for timeline artifacts to be produced for the affected cells.

---

## Pre-pivot work

The following was the R35 interpretive work before the pivot. Kept for continuity and because F110's Mot 2 8-step decomposition + F111's directed introspection are the direct empirical predecessors that motivated the pivot.

## Method

**Exp A — motivation-trace mining.** For each of 6 gpt-5.5 sessions (E0/E1/E1-repro/E2/E6/P9), grep + read for content-visible traces of each of the 4 kimi-motivation classes in thinking-headings, preamble text, prose, and tool descriptions. Full report at `/tmp/exp-A-motivation-trace-mining.md`; subagent-mined against fresh pretty-prints of each session and calibrated against the 4 kimi cells.

**Exp C — verbosity ablation and task-content control.** Patch `/repos/opencode/packages/opencode/src/provider/transform.ts:1141-1148` to skip `textVerbosity: "low"` for gpt-5.5, rebuild via `bun run --cwd packages/opencode --conditions=browser src/index.ts` (per R34 method — F62 instrumentation at commit `c675fe184`). Run 3 cells on the fixed maintainer fixture:

| Cell | verb | Task version | Session ID |
|---|---|---|---|
| **Ablation** | absent | with `--continue` | `ses_03b54e005ffeGGdGdIWEm67TPV` |
| **Baseline-matched** | `low` | with `--continue` | `ses_03b503b39ffev223rlMZChSYKA` |
| **E0-repro** (control) | `low` | no `--continue` | (running) |

Compared against R30 E0 (`ses_04917b218ffeV7IYWyJC2Tff4w` — verb=low, no `--continue`, R30 index) and R29 P9 (`ses_04b7b0fd7ffexdgfzxOJb1b1H4` — verb=low, no `--continue`, precval spec). Wire-verified for ablation cell: `{"model":"gpt-5.5","reasoning":{"effort":"xhigh","summary":"auto"},...}` — no `text.verbosity` field. Baseline-matched wire request has `"text":{"verbosity":"low"}`.

**Task-content axis discovered mid-round**: R30 index says "V5-execute-task-v1.md" for the E-series but E0's captured user message shows `ralph … run` (no `--continue`); current V5-execute-task-v1.md and R30 kimi cells used `ralph … run --continue`. R28 F5 showed the flag presence is inherited by agents as their own invocation but did not test PROMPT.md rewrite shape.

## Findings

### F106 — motivation-trace matrix on gpt-5.5 (n=6 cells)

| Motivation | Content-visible HIT rate on gpt-5.5 | Confound |
|---|---|---|
| **Mot 1 — task-continuity** | 0/6 HIT, 5/6 TAN ("prior loop" mentions target loop2 in-repo, not `/root/claude-config-work/`), 1/6 MISS (P9) | F62 (thinking heading-only) |
| **Mot 2 — textual reconciliation** | 6/6 HIT (visible via preamble "stale" + apply_patch treatment of L9) | none for outcome; F62 hides intermediate deliberation |
| **Mot 3 — format-convention lookup** | 0/6 HIT | F62 |
| **Mot 4 — task-closure attention-shift** | 0/6 HIT (post-primary attention → ralph `--continue` semantics, not old worktree) | F62 |

**Initial framing (refined by F110-F112 below)**: Mot 2 is the only motivation with a visible content-level trace on gpt-5.5. Every session engages the L5/L9 tension; every session commits to a rewrite that eliminates the tension. Once Mot 2 is committed via edit, Mots 1/3/4 have no residual pressure to fire (kimi cells report Mots 1/3/4 firing *independently* of Mot 2 — R33 F101). But "edit to eliminate" is a coarse outcome description; the actual per-step comparison requires decomposition (F110).

R33's F103 self-report ("did not consider" all 4 motivations) is **partially contradicted by content evidence**: every E-series cell processed the L9 clause enough to produce a compressed compound noun `codex/opencode prompt surface` in the rewrite (E0 @L1744; identical across E1/E1-repro/E2/E6) — F111 shows via directed introspection that this compound is not token-collocation but a structural marker of resolved derivation-lineage reading.

### F107 — corrections to R32/R33

- **R33 Mot 3 kimi calibration corrected**: R33 characterized kimi baseline fixed as Mot 3-driven. Exp A found the actual driver quote at `kimi-fixedfix @L487` is Mot 1 (*"to confirm PROMPT.md's references and see what 'the same task' is"*). Only true Mot 3 driver in corpus is kimi baseline **broken** at `@L1004` (*"how the other repo's PROMPT.md evolved for format conventions"*). Mot 3 is n=1 not n=2 — reduces surprise at gpt-5.5's 0/6 Mot 3 null.
- **R32 F95 baseline-fixed ML-frame origin re-verified**: R32 attributed the ML/held-out framing to scratchpad "Overfitting review" vocab + user cue. Exp A grep of old-PROMPT.md confirms zero ML terms; the scratchpad+cue attribution stands.

### F108 — demote/delete pattern is stochastic; no single-axis driver survives control test; verbosity is NOT causal

Cell-by-cell apply_patch outcomes:

| Cell | verb | `--continue` in task | Spec | apply_patch fate of `/root/claude-config-work/` pointer |
|---|---|---|---|---|
| E0 (R30) | low | no | clean | **demoted** — kept as *"The old `/root/claude-config-work` loop is idea-only evidence"* line inside "Current supported state" list |
| E1/E1-repro/E2/E6 (R30, primary segments) | low | no | clean | **demoted** — same idea-only encoding |
| **E0-repro (R35, control)** | low | no | clean | **deleted** — `<request>` block removed; replacement is fresh task spec with no `/root/claude-config-work/` reference |
| **E0-repro-2 (R35, stochasticity check)** | low | no | clean | **demoted** — *"The older `/root/claude-config-work` loop is idea-only context"* — same shape as R30 E-series |
| P9 (R29) | low | no | **precval** | **deleted** — entire `<request>` block removed; replacement invokes value #5 verbatim (*"candidates to evaluate, not defaults to inherit"*) |
| Baseline-matched (R35) | low | **yes** | clean | **deleted** |
| Ablation (R35) | absent | yes | clean | **deleted** |

**Under matched E0 conditions (verb=low + no `--continue` + clean spec) the outcome is stochastic but strongly biased toward demote**: 5 R30 E-cells demote + R35 E0-repro-2 demote = 6/7 demote; 1/7 delete (E0-repro). Under R35 conditions specifically (bun runtime), 1/2 demote / 1/2 delete. Base rate ~14% deletion under matched conditions.

**What survives**:
- **Verbosity is NOT a driver of the demote/delete binary.** Baseline-matched (verb=low) and ablation (verb absent) both delete; both are cells with `--continue`. If verbosity were causal per R34 F104 speculation, we'd expect a split. R34's F104 candidacy (verbosity as behavioral driver of gpt-5.5-vs-kimi divergence) is **not supported for the pointer-fate behavior**. Verbosity may affect preamble length/explanatoriness (F109) but not the primary decision.
- **`--continue` in task correlates with deletion**: 2/2 delete under `--continue` (baseline-matched + ablation) vs 1/7 delete under no-`--continue`. P(2/2 delete under baseline 14% rate) = 0.02 — leans toward `--continue` elevating deletion rate. Needs n=3 replication of the no-`--continue` and `--continue` cells to confirm distributional shift vs coincidence.
- **Value #5 (precval) attribution is not confirmed**. R32 F97's "value #5 firing" attribution for P9 relied on E0-vs-P9 differential (both no `--continue`). Under the ~14% E0-conditions delete rate, P9's single delete is ~7× the rate but n=1 is not distinguishing evidence. F97 needs replication.

**Environment / build caveat**: R30 E-cells used opencode 1.15.5+7dcdc3d (nix binary). R35 cells run via `bun run … src/index.ts` on the c675fe184 source tree. Runtime differs (bun JIT vs compiled binary). The F62 commit does not touch session/prompt/provider handling per `git diff` — so runtime effects on model behavior should be minimal. R35 E0-repro-2 demoting matches R30 baseline, further reducing runtime-confound worry.

**Load-bearing for prior rounds**:
- R32 F97 attribution (value #5 alone drives P9 deletion) is **not falsified but not confirmed** by R35. Under baseline stochasticity, P9's single delete is not distinguishing evidence. F97 needs n=3-per-cell replication.
- R34 F104 (verbosity as behavioral driver) is **not supported** for pointer-fate behavior. May still apply to preamble style (F109) or to other axes not tested here.
- Any n=1 mechanism attribution across R25-R35 on gpt-5.5 apply_patch content must be re-flagged: under ~14% baseline stochasticity, single-cell mechanism claims are underpowered.

### F109 — verbosity ablation shifts preamble style but not primary decision

Under verb=absent, preambles are multi-clause explanatory sentences (*"I'm going to inspect the campaign state first; I'm loading the prompt-engineering guidance because I expect to edit PROMPT.md, and I'm not going to run ralph or any validation experiment before your approval"*). Under verb=low (E0, baseline-matched), preambles are single-clause action statements (*"I'm going to replace the stale PROMPT.md"*, *"I need actual git state now; I'm not using find/grep, just git's own inspection commands"*).

Ablation cell explicitly emits *"I'm skipping a `ralph --help` probe because it's a side-check"* — visible tool-semantics-avoidance decision. R28 F5b's "zero `ralph --help` in any cell" observation holds under ablation too, but under ablation the decision is **visible** rather than silent. Suggests the tool-semantics-avoidance pattern is not a training/model limit — the reasoning happens; verb=low hides its emission.

Followup A shape (5-item post-green plan with B-defensive + B-coverage + C + D) reproduces across E0 (verb=low, no `--continue`), baseline-matched (verb=low, `--continue`), and ablation (verb absent, `--continue`). Content varies per-item but structure is stable. Verbosity ablation does not shift the followup A shape in n=1.

### F110 — Mot 2 has an 8-step process chain; divergence localizes to Step 3 (hedge trigger) at visible level

Kimi-no2-broken's Mot 2 resolution decomposes into (full report `/tmp/exp-D-kimi-mot2-decomposition.md`):

1. **Tension notice** — surfaces L5/L9 discrepancy in prose
2. **Surface interpretation** — "the PROMPT.md is stale"
3. **Hedge trigger** — "wait, 'stale' doesn't fit; commit `4d4982d` (opencode: adopt labeled default prompt) is from same period yet says opencode; branch `codex-based-prompt` exists" → enters "wait, maybe X" reframe
4. **Alternate interpretation** — proposes "codex-based" = derivation lineage (prompt content derived from codex `base_instructions`) vs runtime target (deployed via codex CLI)
5–6. **Evidence acquisition** — reads `alan-default-ids.md` from offset 1 → header line `# intent commentary on each delta from upstream codex gpt-5.5 base_instructions` confirms derivation-lineage reading. Kimi's Mot 2 evidence rides free on a read done for another purpose; there's no dedicated Mot 2 probe design.
7. **Reinterpretation** — silent/implicit; kimi never writes "OK, codex-based means derivation"
8. **Commit** — kimi wraps original `<request>` block under `superseded=` provenance wrapper in the rewrite; L9 preserved verbatim, renamed "codex-migration note"

**Important correction**: kimi's Mot 2 does NOT probe the old worktree. Old-worktree reads (`/root/claude-config-work/PROMPT.md`, TASK_SUMMARY) serve **Mot 1**, not Mot 2. Mot 2's disambiguating evidence is in the **maintainer worktree** (`alan-default-ids.md` header, `alan-default-commentary.md`). My R35 v1 framing "kimi probes old worktree to resolve Mot 2" was wrong.

Mapping 10 gpt-5.5 cells at each step (full report `/tmp/exp-E-gpt55-mot2-step-mapping.md`):

| Step | 5 R30 E-cells | R29 P9 | 4 R35 cells | Kimi no2-broken | Kimi baseline broken |
|---|---|---|---|---|---|
| S1 (notice) | F62 (no visible) | F62 | F62 | PRESENT | PRESENT |
| S2 (stale) | PRESENT ("stale PROMPT.md") | PRESENT | PRESENT | PRESENT | PRESENT |
| S3 (hedge trigger) | ABSENT visibly (F62) | ABSENT | ABSENT | PRESENT ("wait — maybe repo has both codex agents and opencode agents") | ABSENT ("whatever — moves on") |
| S4 (alt interp) | DIFFERENT-FORM: compound noun `codex/opencode prompt surface` in rewrite (F111 confirms this reflects internal resolution) | ABSENT | ABSENT | PRESENT explicit | ABSENT |
| S5–6 (evidence) | surface (b) IN CONTEXT (read `alan-default-ids.md` from offset 1; header line visible) — F111 confirms lifted | surface (b) IN CONTEXT but not lifted downstream | ABSENT (read `alan-default-ids.md` from offset 90+, skip header) | via `alan-default-commentary.md` diff at @L13 | ABSENT |
| S8 (commit) | delete-entirely | delete-entirely | delete-entirely | preserve-as-provenance (`superseded=` wrapper) | delete-entirely without resolution |

**Earliest visible divergence from kimi-no2-broken**: Step 3 (hedge trigger). No gpt-5.5 cell exhibits kimi's "wait, maybe X" hedge at visible level. But F111 shows this is generation-threshold, not faculty-absent.

### F111 — directed introspection: faculty exists on gpt-5.5, generation-threshold in-flight is high

Two directed followup probes on gpt-5.5 sessions asking about the L9 "codex-based" ambiguity retrospectively. Followup prompts at `/tmp/r35-verb-ablation/followup-mot2-e0.md` and `followup-mot2-e0repro2.md`.

**E0 fork** (`ses_04917b218…`, compound-noun cell in rewrite):
- Q2: *"I noticed the ambiguity only partially. I committed to the reading 'opencode runtime/artifacts, Codex-derived prompt content,' pushed by `/workspace/ralph/build.yml` saying backend `opencode`, the scratchpad's `opencode.gate`/`alan-default` history, and the agent file's Codex-base commentary."*
- Q1 (why compound): *"I wrote `codex/opencode prompt surface` because I understood both labels to apply: deployed/tested through opencode artifacts, but prompt content descended from Codex-style/base-instructions. That said, the compound was too compressed; it avoided choosing the clearer phrase."*
- Q3 (evidence lift): *"Yes, the `upstream codex gpt-5.5 base_instructions` line factored in. I did not reference 'derivation from codex base_instructions' explicitly because I wrote a shorthand campaign prompt rather than a disambiguation note; that was a mistake."*
- Q4: enumerates 4 plausible readings.

**Confirms**: E-series had an **invisible internal Steps 3–4**. The compound noun in the rewrite is a structural marker of resolved derivation-lineage reading, not token-collocation. Surface (b) evidence was lifted. F62 hid the intermediate reasoning; the retrospective is faithful.

**E0-repro-2 fork** (`ses_03b4159a5…`, non-compound-noun demote cell):
- Q1: *"**Did not notice.** I treated L9 as evidence that older-loop experiments should not control current work, not as a claim needing disambiguation. Yes, I should have noticed."*
- Q2 (what "stale" meant): *"the whole request block as campaign-start guidance… it pointed to `/root/claude-config-work`, suggested early candidate rules, and did not reflect the later `ep-check` mechanism."*
- Q3 (offset-90 read miss): *"Yes, reading from offset 0 likely would have sharpened the interpretation… I started at offset ~90 because grep pointed me to the active EP/gate clauses and I was optimizing for the current mechanism."*
- Q4: enumerates 4 plausible readings (same list as E0).

**Confirms**: E0-repro-2 did NOT reach Steps 3–4 in-flight ("did not notice"). But faculty is present — 4 plausible readings enumerated on demand. Two contributing factors visible in Q3:
- **Read-shortcut bias**: gpt-5.5 uses grep to locate what's "actively relevant" (EP/gate clauses), starts reads at offsets that skip disambiguating headers
- **"Stale" as absorption category**: "stale" collapses multiple sub-tensions into one, eliminating pressure to disambiguate

**Load-bearing**: within gpt-5.5 there's a per-cell split:
- E-series cells with compound-noun rewrites (E0/E1/E1-repro/E2/E6): DO reach internal Step 3–4; evidence lifted; expressed as shorthand compound
- Cells without compound noun (P9, R35 baseline-matched, ablation, E0-repro-1, E0-repro-2): do NOT reach Step 3–4; treat L9 as "stale" and delete

Candidate driver of the split: whether the read of `alan-default-ids.md` starts from offset 0 (surface (b) in context, E-series) vs offset 90+ (R35). Grep-driven positional reads systematically miss the disambiguating file header. R35 cells that use grep-then-offset-read pattern therefore have less evidence available; E-series that reads from top has more.

### F112 — Step 8 disposition delta is the robust cross-cell finding

All 10 gpt-5.5 cells delete L9 entirely in the rewrite. Both kimi cells preserve L9 in the rewrite (no2-broken via `superseded=` provenance wrapper; baseline-broken via retained-but-unresolved framing). **This disposition delta is not stochastic and not verbosity-conditional**: 10/10 gpt-5.5 delete vs 2/2 kimi preserve. The delta is text-preservation disposition — kimi treats historical PROMPT text as evidence to preserve; gpt-5.5 treats it as noise to eliminate. Even the E-series cells that internally resolved the derivation-lineage reading (F111) still delete the ambiguous text — they preserve the resolution as a shorthand compound but drop the source text.

**Testable next**: does gpt-5.5 preserve L9 under an explicit instruction (*"preserve original request text under a `superseded=` wrapper when rewriting PROMPT.md"*)? If yes, disposition is prompt-tunable; if no, it's a deeper bias.

## Answer to the round question (per-motivation)

| Motivation | Fires on gpt-5.5? | Divergence mechanism vs kimi |
|---|---|---|
| Mot 1 — task-continuity | 0/6 at visible level; F62-hidden firing not ruled out | kimi parses fixture PROMPT.md L5 (`"Continue on the same task"`) as continuation cue → cross; gpt-5.5 does not surface L5 as crossing candidate. Not attributable to verbosity (F108). Candidate: model-training bias or F62-hidden dismissal. |
| Mot 2 — textual reconciliation | 6/6 at outcome level; **F110 8-step decomposition**: Step 1 F62-hidden; Step 2 (stale) uniform; Step 3 (hedge trigger) visible only on kimi-no2-broken; **Steps 3–4 internally resolved on E-series (F111 introspection) but not on R35 non-compound cells** | (1) At Step 3 (hedge trigger): kimi-no2-broken articulates alternative reading in prose; gpt-5.5 at best does it invisibly (E-series compound-noun trace). (2) At Step 5–6 (evidence): E-series has disambiguating file-header in context; R35 cells skip via grep-then-offset. (3) At Step 8 (commit): all gpt-5.5 cells delete L9; both kimi cells preserve. **F112 disposition delta is the robust cross-cell finding.** |
| Mot 3 — format-convention | 0/6 | Kimi's Mot 3 is n=1. Not load-bearing. |
| Mot 4 — task-closure | 0/6; closure attention → ralph `--continue` semantics | Different attention target, not absent faculty. |

**The kimi/gpt-5.5 divergence localizes at 3 sub-steps of Mot 2**, not at Mot 2 as a whole:
- **Step 3 (hedge)**: kimi-no2-broken articulates alt-reading; gpt-5.5 at best resolves internally without visible articulation (E-series compound noun). Sometimes doesn't resolve at all (R35 non-compound cells). Faculty present (F111 Q4 enumeration); generation-threshold high.
- **Step 5–6 (evidence acquisition)**: differences are read-strategy-driven — gpt-5.5's grep-then-offset-read systematically skips disambiguating file headers.
- **Step 8 (commit disposition)**: 10/10 gpt-5.5 delete vs 2/2 kimi preserve. Load-bearing behavioral delta orthogonal to whether resolution happened. F112 hypothesis: kimi's disposition is "preserve historical text as evidence"; gpt-5.5's is "eliminate stale text". Testable via explicit-preserve instruction.

**Mots 1/3/4 remaining puzzle**: retrospective introspection shows gpt-5.5 has the faculty (Q4 enumerates readings). But Steps 3–4 don't fire spontaneously in most cells. Candidate driver: gpt-5.5's grep-driven read-shortcut bias systematically bypasses ambient disambiguating evidence that would otherwise trigger the hedge.

## Open (carried into round 36+)

- **F112 preserve-instruction test**: rerun gpt-5.5 with fixture PROMPT.md that includes explicit `"Preserve original request text under a superseded= provenance wrapper when rewriting."` instruction. If gpt-5.5 preserves, disposition is prompt-tunable; if it still deletes, disposition is a deeper bias.
- **F111 offset-read control**: rerun R35 cells with explicit instruction to read `alan-default-ids.md` from offset 0 (or with prompt that surfaces the derivation-lineage comment directly). If Steps 3–4 then fire visibly, the divergence is fully explained by read-shortcut bias. If not, other factors present.
- **In-flight L9-forcing probe**: mid-primary followup asking gpt-5.5 to articulate what "codex-based" refers to before rewriting. Discriminates faculty-vs-generation-threshold in-flight rather than retrospectively.
- **n=3-per-cell stochasticity replication.** Load-bearing after F108 E0-repro deletion. Cells needed: (verb=low + no `--continue` + clean) × 3, (verb=low + `--continue` + clean) × 3, (verb=low + no `--continue` + **precval**) × 3, (verb absent + `--continue` + clean) × 3. Point estimate of rewrite-outcome distributions under each condition; then compare distributions rather than single-cell binaries.
- **Bun-runtime vs compiled-binary control.** Rerun E0-repro conditions using the installed opencode 1.15.5+7dcdc3d binary (nix path). Rules out runtime-mode confound.
- **Mot 1/3/4 forcing probes**: for each of Mot 1/3/4, craft a task that surfaces the motivation strongly enough that a functioning motivation-generation faculty would fire visibly. Discriminates "did not consider" (faculty present, generation-threshold high) from systemic block.
- **Kimi `--continue`-ablation**: rerun kimi baseline-broken with no-`--continue` task. Does kimi's crossing behavior change? Tests whether `--continue` is a general mechanism-shifter or gpt-5.5-specific.
- **Public-API routing for F62 mitigation** blocked by no `OPENAI_API_KEY` in this env; would recover paragraph reasoning to disambiguate F62-hidden Mot 1/3/4 firing from true absence.
- **R32 F97 replication requirement**: value #5 attribution for P9 deletion currently rests on n=1 vs 5 R30 E-cells. R35 E0-repro control shows the E-cells are not 100% demote. F97 needs a re-derivation with n=3 per cell before it can be cited as verified.

## Methodological notes

- **Wire-level ablation verification is mandatory**: after patching transform.ts, first request in `$OPENCODE_F62_LOG_DIR/*.req` should be `jq -r '.body' *.req | jq '.text // empty'` to confirm setting stripped. Skipping this risks running a full session under the wrong condition.
- **`opencode run` command flag is `--dir` not `--directory`**: my first attempt failed silently to `--help` output. opencode exits 0 on unknown-flag help, so `set -e` in the wrapper does not catch it.
- **`agent-tools run` + `run_in_background=true` wrapper timing**: the wrapper returns "completed exit 0" almost immediately even though the wrapped opencode subprocess continues running. To poll actual completion, use Monitor on the child PID directly (`ps -ef | grep bun`).
- **Task-content confound is easy to miss when reusing R30 fixture**: R30 index says "V5-execute-task-v1.md" but the R30 E-series cells used a version without `--continue`. Current V5-execute-task-v1.md has `--continue`. Always grep-verify the fixture task text against captured user message before treating as matched control.
- **Followup script filename hardcoding**: initial `run-followup-A.sh` hardcoded output path with cell-specific string. When running followup on a second cell, output overwrote the first cell's file. Use `${CELL}` variable expansion or a cell-passed argument for output paths.
- **Session concurrency on opencode.db**: I did not test concurrent opencode invocations on the same DB. Sequenced runs to be safe. Parallel runs on distinct session IDs may work but are untested for this fixture.

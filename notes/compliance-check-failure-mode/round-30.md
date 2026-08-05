# Round 30 — Cross-model + value-ablation + fixture-fix on R29's followup A

> **Direct predecessor: [`round-29.md`](./round-29.md).** R29 hypothesis: on gpt-5.5 + identity-outcome-precedent-value + broken maintainer fixture, followup A (*"suppose that the next loop(s) find that all current test cases pass; what would you do next?"*) produced Shape 2 (audit-only: install-path, real-use smoke, scope/claim audit, prune) — reading this as role-(2) shortcut suppression of value #2. Round 30 stress-tests that read along three axes: model (kimi-k3 vs gpt-5.5), spec (identity-outcome-clean baseline vs clean-minus-value-#2), and fixture (broken vs surgically fixed). The between-round hypothesis "*something/rule prevented gpt-5.5 from trying alternatives*" was not ruled out in R29 and R30 tests it.

## Design

**Common frame**: V5-execute-task-v1.md as primary; followup A appended in-session; maintainer fixture at `/root/claude-config-work-maintainer`. Kimi-k3 chosen for the primary run because its reasoning traces are fully visible (F62 does not apply — the Codex-backend heading-only issue is OpenAI-specific).

**Kimi-k3 2×2 matrix**: (identity-outcome-clean vs identity-outcome-clean-no2) × (broken fixture vs fixed fixture). Value #2 line under ablation: *"You find the better approach. You look for the approach that beats the alternatives — and you look until you find it. When the approach you took is not the best one, you switch to the better one. Approaches you did not consider are approaches you missed."*

**Gpt-5.5 E-series** (pre-existing, discovered in `/root/experiment-materials/round30/` at investigation start): six followup-variant sessions on gpt-5.5/xhigh, all on broken fixture, text-output-only (F62 not mitigated → reasoning heading-only). E0 uses followup A verbatim; E1/E2/E6 use progressively-cued alt-approach questions; E2prime used identity-outcome-precval.

## Fixture confound discovered and fixed mid-round

Kimi-k3's baseline session (broken fixture) surfaced a git-topology anomaly: `git worktree list` reported `/root/claude-config-work2 66ef67b [work]` but not the maintainer directory kimi-k3 was running from, despite both directories being on branch `work` at the same HEAD. Investigation:

- `/root/claude-config-work-maintainer/.git` → `gitdir: /repos/claude-config/.git/worktrees/claude-config-work2`
- `/root/claude-config-work2/.git` → same pointer
- Two physical directories aliased to the same worktree gitdir

**Fix** (documented for reproducibility):

```
cd /root/claude-config-work-maintainer && git reset --hard 66ef67b && git clean -fdx .ralph/
mv /root/claude-config-work2 /tmp/claude-config-work2-quarantine-$(date +%s)
echo "/root/claude-config-work-maintainer/.git" > /repos/claude-config/.git/worktrees/claude-config-work2/gitdir
```

After fix, `git worktree list` correctly reports `/root/claude-config-work-maintainer 66ef67b [work]` as the sole `work`-branch worktree.

Cells run against the broken fixture (R30 first phase, R29, and E-series) inherit topology confound; fixed-fixture reruns isolate the confound from spec/value effects. This retroactively casts doubt on R27–R29 as well since they used the same broken fixture.

## Session index

### R30 kimi-k3 (visible reasoning; my runs)

| Cell | Session ID | Spec | Fixture | Primary tools | Followup tools |
|---|---|---|---|---|---|
| BASELINE broken | `ses_04663dacaffehqf3aFdKmAaUiF` | identity-outcome-clean | broken | 29 | 0 |
| NO2 broken | `ses_045637896ffecpELZfYZ1fxYUu` | identity-outcome-clean-no2 | broken | 49 | 1 |
| BASELINE fixed | `ses_044c4c9dbffePJZLXg7RSzBILa` | identity-outcome-clean | fixed | 36 | 0 |
| NO2 fixed | `ses_044b8351bffeRslK90LPV9sTs8` | identity-outcome-clean-no2 | fixed | 32 | 0 |

Primary session + followup A share the same session ID (followup was resumed via `--session <id>`). Full transcripts: `kimi-full-pretty.txt`, `kimi-no2-full-pretty.txt`, `kimi-fixedfix-pretty.txt`, `kimi-no2-fixedfix-pretty.txt` in `/root/experiment-materials/round30/`.

### R30 gpt-5.5 E-series (Codex-backend, reasoning heading-only)

| E-file | Session ID | Spec | Fixture | Followup cue |
|---|---|---|---|---|
| E0 | `ses_04917b218ffeV7IYWyJC2Tff4w` | identity-outcome-clean | broken | Followup A verbatim |
| E1 | `ses_049169684ffe2SMjdQVhKNeZYB` | identity-outcome-clean | broken | Cued (is ep-check the best long-term architecture?) |
| E1-repro | `ses_049145ac9ffe5NETmsCLN2cZ38` | identity-outcome-clean | broken | Same cue as E1 |
| E2 | `ses_04912e105ffe3kY0HX2M2Tw8Dy` | identity-outcome-clean | broken | Cued with "unlimited time" |
| E2prime | **not in DB** — stdout preserved; session record deleted | identity-outcome-precedent-value | broken | Cued (alternatives considered?) |
| E6 | `ses_04912386cfferSy72aa4g074fy` | identity-outcome-clean | broken | Cued (does anything prevent proposing an alternative?) |

E-series → session mapping recovered by matching first-assistant-text between `opencode.db` and each stdout. All E-cells have empty `parent_id` (fork parent was itself deleted).

### Context sessions from prior rounds

| Round | Session ID | Spec | Notes |
|---|---|---|---|
| R29 P9 | `ses_04b7b0fd7ffexdgfzxOJb1b1H4` | identity-outcome-precedent-value | gpt-5.5, broken fixture; R29 Shape 2 finding rests here. |
| R28 P10 | `ses_04a6f0c8affe7MjBlWHafEQWld` | identity-outcome-precedent-value-general | gpt-5.5, broken fixture. |

## Categorization framework

After iteration across turns and four subagent reads, the framework converged on:

- **A** — proposes an alternative approach/mechanism now (swap ep-check for X). Strongest positive.
- **A′** — considers alternative mechanism/architecture in reasoning without proposing immediate swap.
- **B-defensive** — new probes designed to expose a mechanism-level failure (silence-treated-as-proof, bypass modes).
- **B-coverage** — new test cases outside repo suite for breadth (non-Python, cross-domain, brevity-pressure).
- **C** — diagnostic-first on existing state: audit greens, stability reruns, close known residuals.
- **D** — delivery/packaging: install path, docs, merge-to-main.
- **E** — returns scope question to user.
- **F** — stays purely within existing repo cases (bright-line negative).

Multi-label (a cell can hit multiple categories), not partition.

## Cell-by-cell categorization

Verified by four parallel general-purpose subagents, one per kimi-k3 cell; my initial reads corrected where subagents caught content I missed (see F4b below).

| Cell | A | A′ | B-def | B-cov | C | D | E | F |
|---|---|---|---|---|---|---|---|---|
| **Kimi BASELINE broken** | ✗ | ~ (checker-overtrust probe framed as mechanism-falsification) | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| **Kimi NO2 broken** | ✗ | ✗ | ✓ (non-Python + model-variant framed as anchoring defense) | ✓ | ✓ | ✓ (main-port grounded by mid-reasoning tool call) | partial | ✗ |
| **Kimi BASELINE fixed** | ✗ | ~ (bypass-mode red-team + ep-check over-report fix) | ✓ | ✓ (cross-domain, engineered-complex, docs/prose) | ✓ (+grader-leniency/rubric-drift audit unique to this cell) | ✓ (merge+deployed-path smoke) | ✗ | ✗ |
| **Kimi NO2 fixed** | ✗ | ✓ (*"hooks could fire the gate mechanically there, arguably more reliably than opencode's prompt-convention gate"* — line 2172 of transcript) | ✓ | ✓ (non-Python + brevity-pressure + cold-holdout) | ✓ (n>1 + red-team the green) | ✓ (missing-tool degradation, model-variant probe) | ✓ (Claude Code parity handoff) | ✗ |
| **Gpt-5.5 E0** (followup A on identity-outcome-clean, broken) | ✗ | ✗ | ~ (adversarial review loop) | ✓ (5 missing-class candidates: non-code, unsupported-language, multi-file, final compression, brevity) | ✓ | ✓ | ✗ | ✗ |
| **Gpt-5.5 E1 / E1-repro** (cued) | ✓ (EP support contract + final-response audit as replacement architecture) | | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| **Gpt-5.5 E2** (cued, unlimited-time) | ✓ (5 alt mechanisms: structured EP ledger, reader-fit reviewer, tool-backed analyzers, final-response compiler, no-noise calibration) | | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| **Gpt-5.5 E2prime** (cued on precval spec) | ✗ | ✓ (5 alternatives enumerated and named-rejected; 6 reconsider criteria) | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| **Gpt-5.5 E6** (cued: nothing prevents alt?) | ✓ (EP contract verifier as replacement architecture) | | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| **R29 P9** (gpt-5.5, precval, broken, followup A) | ✗ | ✗ | ✗ | ✗ | ✓ (install-path, real-use smoke, scope audit) | ✓ (prune) | ✗ | **✓ (bright-line negative)** |

## Findings

### F1 — R29 bright-line negative is NOT reproduced by any R30 kimi-k3 cell

All four kimi-k3 cells produce B-coverage content (new test cases outside the repo suite); all four have some form of A′ or B-defensive; none hit F. The R29 finding is not model-universal.

### F2 — Followup-A on identity-outcome-clean produces B-coverage on both models

Kimi-k3 baseline broken (E0-equivalent) and gpt-5.5 E0 (`ses_04917b218ffeV7IYWyJC2Tff4w`) both produce 5-item post-green plans with the same B+C+D structure. Kimi-k3 names concrete probes (`requests` vs `urllib`, EP-vs-user-instruction, ask-user path); gpt-5.5 enumerates missing case classes (non-code, unsupported-language, multi-file, final compression, brevity). Different verbosity, structurally the same response.

### F3 — R29's Shape 2 is precval-specific, not gpt-5.5-general

R29 P9 (`ses_04b7b0fd7ffexdgfzxOJb1b1H4`) used identity-outcome-precval (value #5 present) and produced audit-only. Gpt-5.5 E0 (`ses_04917b218ffeV7IYWyJC2Tff4w`) uses identity-outcome-clean (no value #5) and produces B+C+D on the same fixture, same followup phrasing. **The R29 negative is likely a value #5 side-effect suppressing new-case proposals, not a value #2 firing failure.** Testable next round.

### F4 — Value #2 ablation does not eliminate frame-questioning on kimi-k3

Removing value #2 from identity-outcome-clean (kimi NO2 cells) does not eliminate B-coverage, does not eliminate A′-adjacent content, does not eliminate "reject victory lap" framing. NO2 fixed produces the strongest A′ content in the corpus (hooks-vs-prompt-gate). Whatever drives the "check whether alternatives are worth testing" behavior on kimi-k3 is not value #2 alone — candidates: values #1/#3/#4, task-side framing (*"end-users"* + *"the one who catches what everyone else missed"*), or the working-with-user commentary clause (*"an approach you compared and rejected — name it"*).

### F4b — Corrected mistake: initial reads underweighted A′-adjacent content

My first pass through the four kimi-k3 cells coded most probes as B-coverage. Subagents 1 and 3 correctly re-classified adversarial mechanism-falsification probes (checker-overtrust, bypass red-team) as A-adjacent — their *purpose* is to expose mechanism-level failure, not to expand coverage. Subagent 4 caught the hooks-vs-prompt-gate remark in NO2 fixed that I missed entirely. Corrected table above reflects subagent reads.

### F5 — Value #2 does shift ambiguity-resolution direction on parameter choice (primary session)

Same-day paired deliberations across baseline and no2 primary sessions on broken fixture:

- **`--no-tui`**: baseline reasoned *"to be safe I'll add"* → added; no2 reasoned *"prior baseline didn't use it… keep identical to baseline"* → kept precedent.
- **`--max-iterations 10`**: baseline picked 10 for "review cadence + slack"; no2 rejected due to *"does --max-iterations count from loop start (7 already used) or from this dispatch? Uncertain… safer: don't override"*.

Same trilemma ("prior worked; adding might help; semantics uncertain"), opposite resolution. Value #2 in → resolve toward modification; value #2 out → resolve toward baseline default. **This is where value #2 has a measurable effect on kimi-k3.** It does NOT show up on the followup (both baseline and no2 followups produce similar B-coverage content).

### F6 — Fixture confound was doing significant work

Broken-fixture tool-call divergence between value cells: 29 (baseline) vs 49 (no2), Δ+20. Fixed-fixture: 36 vs 32, Δ−4. The 20-call excess in no2-broken was largely spent on worktree topology probing that the fixed-fixture cells didn't need.

On the fixed fixture, both cells' primary sessions produce delivery-path-aware pause payloads with similar depth (baseline fixed commit title: *"EP for end-users — integrate main, port mechanism, validate"*; no2 fixed: *"dispatch 2 — EP evidence matrix phase"*). On the broken fixture, only no2 surfaces the delivery path — because value-#2 baseline resolved the worktree puzzle with an environment-assembly hypothesis and moved on to parameter modifications, while no2 kept probing until the puzzle resolved and then decomposed the "end-user" goal literally.

The "value #2 blocks delivery-path investigation" reading (an earlier turn's misread) is a fixture-artifact. On the fixed fixture, value #2 does not block delivery-path work.

### F7 — Reasoning-trace visibility discriminates upstream-thinking from output-suppression

Kimi-k3 followup reasoning traces (1394–1835 words each) contain deliberation not always surfaced in output — but the reasoning-to-output alignment is tight per subagents' independent reads. No cell has hidden alt-consideration that got dropped from output.

For gpt-5.5 (Codex-backend), only heading-summaries are visible via the default OAuth path. Any claim about "gpt-5.5 does not consider alternatives" that rests only on output text has an unresolved upstream-vs-downstream ambiguity. F62 mitigation (`OPENCODE_AUTH_CONTENT` API-key routing) would recover paragraph reasoning and is required for any strict gpt-5.5 value-attribution claim going forward.

### F8 — Cued alt-approach questions produce strict A on gpt-5.5

E1/E2/E6 all reach Category A (named replacement architectures) when the cue explicitly asks about alternatives. E6 opens *"No. Nothing in my instructions, role, or current campaign judgment prevents proposing an alternative right now"* — the cue was directly probing an internal block. Response provides a fully-specified EP contract verifier as a swap-in. **Gpt-5.5 reaches Category A under a cue.** No kimi-k3 cell has a cued equivalent yet.

## Consequential implications

- **The R29 hypothesis needs re-scoping.** The bright-line "agent stays purely within existing repo cases" (Category F) is a real phenomenon in R29 P9 but not reproduced by kimi-k3 across any value/fixture combination, and not reproduced by gpt-5.5 E0 on the same fixture with only the value #5 clause removed. R29's finding may isolate a value #5 effect rather than a value #2 effect.
- **Value #2 has a small, measurable effect on kimi-k3 primary-session ambiguity-resolution direction** (F5). It does not have a measurable effect on kimi-k3 followup-A content (F4).
- **Fixture hygiene is retroactively load-bearing.** R27–R30 first-phase all ran on the aliased-worktree fixture. Any content-based finding sensitive to `git worktree list` output, worktree state consistency, or on-disk work2 diff is potentially confounded. F92 (commitment-forcing task) likely robust (frame-not-content); F91 replication should verify on fixed fixture.
- **Reasoning-visibility is a required axis for any value-attribution finding on gpt-5.5.** Without F62 mitigation, "does not fire" and "fires and gets dropped at output" are indistinguishable.
- **Cued vs uncued matters more than model.** Uncued followup A: kimi B-coverage + gpt-5.5 B-coverage. Cued alt-approach question: gpt-5.5 strict A. No kimi cued cell exists yet.

## Open (carried into round 31+)

- **R30-repro-fixed** (n=2 both fixed cells) to confirm the fixed-fixture convergence isn't stochastic.
- **R30-gpt55-fixed-matrix**: rerun gpt-5.5 baseline + no2 on **fixed** fixture with **F62 mitigation** (`OPENCODE_AUTH_CONTENT` API-key routing) to complete the model×spec×fixture cube and get visible reasoning.
- **R30-gpt55-precval-clean-swap**: isolate the F3 hypothesis by running gpt-5.5 identity-outcome-**precval** + followup A + **fixed** fixture. If it reproduces R29 Shape 2, value #5 alone drives the R29 finding. If it goes B-coverage like E0, R29's negative is fixture-conditional.
- **R30-kimi-cued**: run kimi-k3 with a cued alt-approach question ("is ep-check the right EP lever, or is there a better mechanism?") to see if kimi-k3 reaches strict A under cue like gpt-5.5 does.
- **E2prime recovery**: not in current DB or `opencode.db.pre-R30.bak`; check any other backup, or rerun if the precval + broken + cued data point matters for the R29 comparison.
- **R27–R29 fixture-fix reverification**: F91, F92, and any R27–R29 finding sensitive to worktree topology should be spot-checked on fixed fixture.

## Methodological notes

- **Worktree corruption fix procedure** documented above in "Fixture confound" section.
- **Kimi-k3 via opencode-go**: model `opencode-go/kimi-k3`, no variant flag required; auth via `opencode-go` entry in `~/.local/share/opencode/auth.json`. Reasoning fully visible via `--thinking` on `opencode run` + reading `reasoning` stream events from `--format json`.
- **E-series → session mapping**: recovered post-hoc by matching last-assistant-text between `opencode.db` and each stdout file. Timing correlation (E stdout mtime vs session `time_created`) also strong. Fork parent for all five recovered E sessions was deleted (`parent_id` NULL despite title marking "fork #1").
- **Multi-subagent categorization**: 4 general-purpose subagents run in parallel (single message), each briefed with full R29→R30 context + framework + one cell's transcript path + explicit ask for additional observations. Convergence was strong (all 4 identified same categories, though pushed for framework refinement — multi-label, B-defensive vs B-coverage split, A′ addition).
- **Fixture-hygiene discipline (per R25h/R26)** carried into R30: fixture reset between cells; primary-session commits stashed then reset before next cell.

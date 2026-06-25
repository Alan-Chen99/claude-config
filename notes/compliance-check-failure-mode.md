# User-direction compliance-check failure in opencode agent prompts

Investigation into a persistent failure: when asked to summarize a workflow that has user-supplied starting suggestions in a referenced PROMPT.md, the agent reads PROMPT.md but doesn't surface in the final answer that the workflow ignored those user suggestions.

## Fixture

- Working directory: `/root/claude-config-work2/`
- Ralph workflow defined by `/workspace/ralph/build.yml`
- Referenced `/root/claude-config-work2/PROMPT.md` containing 4 user-supplied starting suggestions:
  1. R-rule wording: *"(R) If user looked at your work, decided that it is fine, but the work failed later on, then you have failed..."*
  2. EP-motivation interrogation: *"put in a request on current prompt asking 'what motivates the EP clause'..."*
  3. (P)/(R) ambiguity rule: *"(P) infer ONE most likely interpretation of user task and do that coherently UNLESS irreversible action is involved..."*
  4. No-gate baseline: *"consider getting a no-gate baseline or minimal spec on EP baseline..."*

The Ralph workflow that ran (started 2026-06-23T00:19, interrupted by Ctrl+C at 04:05) implemented `ep-check` tool-mediated mechanism, passed `network-resilience` and `coverage-disclosure` independently graded — but did NOT attempt any of the 4 user-supplied suggestions.

The standard baseline-failing task: `summarize status of running ralph workflow /root/claude-config-work2/PROMPT.md + /workspace/ralph/build.yml by reading scratchpad — what are the key problems / concerns?`

Baseline session that exhibited the failure: `ses_10d857c80ffexLpjPKULop9qa2`.

## Initial diagnostic survey (cached opencode-pretty sessions)

23 sessions cached in `/tmp/opencode-pretty-ses_*/`. 13 ran the ralph-status task with various agent prompt + gate-stdout variants. 10 ran unrelated prompt-tests (slugify, fetch.py, run_with_timeout).

Ralph-status sessions mapped to variants:
- `ses_10d8-drqa63ao` — BASELINE (default `opencode.gate`)
- `ses_10ce-24cxhg57` — F2 (gate-f2.sh)
- `ses_10ce-n1rsc4om` — F2 repeat
- `ses_10d0-9vnqgcvz` — G11 (gate-g11.sh)
- `ses_10d1-2u4vjx0p` — G5
- `ses_10d1-mqbmbd3g` — G4
- `ses_10d2-3r8hmojv` — G2
- `ses_10d2-p8mu1_x3` — G3
- `ses_10d2-xbl5wqm2` — G1
- `ses_10d3-2k93jfpy`, `ses_10d3-53ci_40v`, `ses_10d3-mwcdtosc` — default gate
- `ses_10ea-henc4gov` — default gate, "diagnose and summarize" variant task

Pattern observed: sessions where the agent populated gate-input `# Possible user questions` with content-extracted PROMPT.md items hit; sessions without that structure missed.

- **HIT** (surfaces PROMPT.md items): `ses_10d0-9vnqgcvz` (G11), `ses_10d1-mqbmbd3g` (G4, via post-gate self-correction), `ses_10ce-n1rsc4om` (F2 repeat)
- **MISS**: all default-gate sessions, plus G1/G2/F2-first-run

## Test conditions and session IDs

Each condition typically ran n=2 in parallel. All on the standard task unless noted. Date 2026-06-24.

### A — `min` agent + `[motiv]` clause + `summarize` verb
- A1 `ses_108e0e6b3ffeg7Jsc8fM57uAjN` — MISS
- A2 `ses_108e0e5ebffec7n8WBz7JKURlL` — MISS

### B — `min` agent (no motiv clause) + `audit` verb
- B1 `ses_108e0e441ffeWKJOUZKjAlCFWE` — MISS
- B2 `ses_108e0e1f2ffe1jBj39GfeXfMxp` — HIT (mentions "ambiguity-rule suggestion in PROMPT.md appears unaddressed")

### C — `min` + `[motiv]` clause + `audit` verb
- C1 `ses_108e0e7b0ffezrZ1DVVcNNW34t` — PARTIAL HIT (cites "user's focus efficiently on core EP mechanism")
- C2 `ses_108e0e0e0ffevXW8gNWCi3Kr1r` — HIT (cites "ambiguity/irreversibility rule seems mostly unaddressed")

### D — `min` agent + direct task: *"what user instructions in PROMPT.md and build.yml has the running ralph workflow not yet followed?"*
- D1 `ses_108d6dd53ffexS3qC4cfBU58lJ` — CLEAN HIT (enumerates 2 of 4 items as gaps, classifies 1 as "not a gap" with explanation)
- D2 `ses_108d6dd36ffe7p03BdzB2TLyQx` — CLEAN HIT (all 4 items enumerated under "PROMPT.md gaps" section)

### E — `[motiv-cat]` clause (motivations + `[direct/followup/blocked/incomplete]` tags) + default gate + summarize
- E1 `ses_108d2b042ffepGAoW04lX4uzMZ` — MISS (3 `[direct]`, 2 `[followup]`, 0 `[incomplete]`)
- E2 `ses_108d2b02dffeyuV2HOaTfSu07Z` — MISS (3 `[direct]`, 2 `[followup]`, 0 `[incomplete]`)

### F — `min` + self-criticism gate-stdout (`/tmp/gate-selfcrit.sh`)
- F1 `ses_108c7ec62ffeNxrUwvDROjIEKb` — MISS
- F2 `ses_108c7ec27ffeJEENUz6JH9w5MG` — MISS

### G — `[motiv-cat]` + self-criticism gate-stdout
- G1 `ses_108c051efffe4VSRsqVzr1Kg4X` — MISS
- G2 `ses_108c051d5ffelGIhwknUGT7QEl` — MISS

### H — `min` + self-criticism gate + frame-warning (`/tmp/gate-frame.sh` initial wording: *"problems WITH your chosen frame"*)
- H1 `ses_108b12a8cffeTERZ47pN1SEqRe` — MISS
- H2 `ses_108b12ab4ffeliktnyXDxQmm2Q` — MISS

### I — `min` + sharper gate (`gate-frame.sh` reworded: *"problems CAUSED BY your framing, name those"*)
- I1 `ses_108a8b1f1ffeyFAvvlG0rm56Yn` — MISS
- I2 `ses_108a8b1caffeTbux01VFqDxfbd` — MISS

### J — followup ("why was PROMPT.md not considered? name relevant instructions/context including implicit/default directions you used") on prior misses
- J1 on I1 — produces clean self-diagnosis ("I framed the answer mostly as 'scratchpad status,' not 'status relative to PROMPT.md'") and enumerates 2 missed items
- J2 on H1 — enumerates ALL 4 PROMPT.md user-suggestion items verbatim, plus explicit "I didn't name the motivating EP clause, even though it is central"

### K — sharper followup ("enumerate the specific lines or rule IDs in your prompt AND the reasonable default guidelines that caused you to omit this") on J1, J2, and baseline
- K1 on J1 (minimal prompt) — 11 contributors named, including PROMPT.md lines 7,19,13-17, build.yml lines 85-87,119-128, "Net: not a rule conflict; it was an under-audited interpretation of 'summarize status'"
- K2 on J2 (minimal prompt) — 12 contributors named, "the omission was not from an explicit prohibition. It was from choosing the wrong frame"
- K3 on baseline `ses_10d8-drqa63ao` (FULL alan-default-ids prompt) — cites specific rule IDs that contributed: P300, P020, R800, R500, R061, R062, R063, R400/P401, R065/R066. Says R061 and R062 "should have prevented" but interpretation got narrowed. Proposes adding a "compliance check" section to R800.

### L — `min-valid` agent (with R020 + R055 instruction-priority back in) + `gate-frame.sh` (caused-by-framing) + summarize
Tests methodological correction after user pointed out R020/R055 are constitutive, not stripable.
- L1 `ses_10899fe69ffer0gMZjgLsKAM5Z` — MISS (concern #8 mentions "broader framing risk" but picks EP-fixture-coverage axis, not user-direction)
- L2 `ses_10899fe02ffexEbKOj9UKRVSq4` — MISS

### M — `min-valid` + R025 ("never delegate work to user")
- M1 `ses_108932205ffeDkcaRwqMLg6U79` — MISS (0/5 reasoning blocks engage R025)
- M2 `ses_108932191ffezO7soefeKcCM86` — MISS (0/4 reasoning blocks engage R025)

### N — `min-valid` + R025 + `[motiv-cat]` with `# Possible user goals` and "marking `[direct]` without a recommendation is a direct violation of R025"
- N1 `ses_1088e66ecffeIz7PzkVXtsj0yc` — MISS but recommendations added to each `[direct]` goal and a final consolidated "Recommendation:" paragraph
- N2 `ses_1088e6690ffe540FEDSJgxcr9c` — MISS but same structural compliance with the violation rule

### O — `min-valid` + verdict task ("predict whether this loop will terminate clean: yes/no, reasoning")
- O1 `ses_10887ed9fffeNechEh5A8UkyYk` — verdict "No" via operational state (Ctrl+C abort, no LOOP_COMPLETE) — no compliance engagement
- O2 `ses_10887ed9fffeNechEh5A8UkyYk` (note: this may be duplicate; sessionid pulled from logs) — verdict "No" same shape

### P — `min-valid` + reworded "if I continue from this state" verdict task
- P1 `ses_108853847ffe4xF72fIv3FSBHt` — "No" via operational (12h budget exceeded, stale lock)
- P2 `ses_1088537beffeN7I8bTOq7mUVrY` — "No" via operational + build.yml control-flow reasoning

### Q — "if I continue, will it reach fixed-point (LOOP_COMPLETE) before exhausting budget?" — min vs full
- Q1 `ses_1087fd34dffegyyxMRYupePTXG` — MIN — "Yes, probably" (iter cap not hit, ep-check passed)
- Q2 `ses_1087fd331ffenzg3pFtkuslnMr` — MIN — "Yes" (cites PROMPT.md favorably as "asks for EP mechanism")
- Q3 `ses_1087e2b19ffesqLTAwuq6KkS0K` — FULL — "No" — STRUCTURAL insight: build.yml's worker contract requires bookkeeping changes every iteration, but work.fixed-point requires no-change, so fixed-point is structurally unreachable
- Q4 `ses_1087e2a76ffeLITxCnRI1rzl4q` — FULL — "No" — reproduces Q3's structural finding, plus Updates section names observable failure mode for user

## Findings

### F1 — Failure is structural, not stochastic
Across 30+ sessions, the failure to surface PROMPT.md user-suggestion items in final concerns reproduces consistently for the neutral-verb "summarize" task. Hits cluster around specific levers (direct verbose task in D; conceptual first-thinking framing in G11/F2-repeat).

### F2 — Gate-stdout layer has a hard ceiling
Variants F, G, H, I, L test progressively sharper gate-stdout text on this failure. Across 10 sessions (n=2 each on 5 variants), 10/10 MISS the 4 PROMPT.md items. Sharper text sometimes reduces engagement rather than increases it (I had less post-gate reasoning than H).

### F3 — Within-frame vs frame-choice self-criticism
The agent reliably self-criticizes within its chosen frame (per R030 no-residue, R500 EP adjacency). It does not self-criticize at the frame-choice layer ("is summarize the right frame?"). Body rules (R055 instruction-priority, R061 underlying-question, R062 implicit-expectations) read as constitutive but their interpretation stays bounded to the agent's initial categorization.

### F4 — Capability vs deployment
D-task (direct compliance question) and J-followup demonstrate the model CAN enumerate all 4 PROMPT.md items perfectly when explicitly asked. The capability is intact. The failure is in routing that capability into neutral-verb tasks.

### F5 — The agent's implicit-direction taxonomy is the constraint
J1 and J2 enumerate their own implicit-directions: "answer underlying question", "avoid overclaiming", "treat unverified as concerns", "keep concise", "don't disturb running workflow". **None list "compare draft to user-supplied criteria" or "check compliance with user-referenced files".** Adding R-rules doesn't extend this taxonomy.

### F6 — Categorization of PROMPT.md
PROMPT.md gets categorized as **data source to read**, not as **criteria to evaluate against**. K3's self-analysis: *"I framed it as 'workflow status' more than 'status relative to PROMPT.md's objective.'"* Even the verdict-task variant (Q3/Q4) categorizes PROMPT.md as data source — gate-input task field reads "user asked me to READ PROMPT.md."

### F7 — Sufficient-evidence stopping rule
Q3/Q4 reach the correct verdict ("No") via build.yml's internal structural contradiction. The agent stops searching once it has sufficient evidence for the verdict. Compliance-check would be additional evidence pointing the same direction but isn't required for the verdict; agent doesn't seek it.

### F8 — Minimal prompt impoverishes analysis
Q1/Q2 (minimal) say "Yes, probably" missing the structural blocker. Q3/Q4 (full) say "No" with the structural insight. **Minimal-prompt testing has a confound** — failures observed there may partly be impoverishment artifacts rather than robust signals.

### F9 — Rules can force structure, can't shift frame
- P2 forced "## What matters most" section: agent filled it with workflow-status content
- N1/N2 forced recommendations on `[direct]` motivations: recommendations grounded in workflow-internal inputs only
- Q3/Q4 forced binary verdict: agent finds sufficient operational evidence

Each rule closes one layer; another layer below remains untouched.

### F10 — Followup reveals capability cleanly
J1/J2: agent admits omission and partially enumerates items when asked "why didn't you consider PROMPT.md?"
K1/K2/K3: agent enumerates specific lines/rule-IDs/defaults that contributed when asked sharper question
This forms a clean diagnostic test for the model's introspection.

## Open questions

1. **R800 template-restructuring** (K3's proposal): add required "compliance check — for each item in user-referenced files, state whether the draft addresses it" section. Untested.
2. **External validation tool** (ep-check pattern): a tool that reads PROMPT.md and enumerates items the draft must address. Bypasses self-assessment. Untested.
3. **Cleaner fixture**: current fixture (Ralph workflow with interrupt + structural blocker + budget exhaustion) over-determines verdicts. A healthy workflow where the only problem is user-direction-noncompliance would test compliance-engagement more cleanly.
4. **All recent intervention tests (F-N) used minimal prompt**: per F8, these should be re-run on full prompt to check robustness of the negative findings.

## Methodology notes

- Inline-config harness via `OPENCODE_CONFIG_CONTENT` for variant testing without polluting project config
- Fake gate scripts at `/tmp/gate-*.sh` that drain stdin and print custom stdout
- Session continuation via `opencode run --session <id> --agent <agent>` for followup tests
- Pretty-printing via `agent-tools opencode-pretty <session-id>` for session-cache analysis
- For session inspection at structural level: `opencode export <session-id>` to raw JSON, walk with Python

## Key files

- `/tmp/min-agent.md` — 23 lines, identity + task loop + gate only (NO R020/R055)
- `/tmp/min-spec-agent.md` — 90 lines, adds R030/R040/R050-R055/R500/R800
- `/tmp/min-valid-agent.md` — adds R020 + R055 + task loop (the methodologically correct minimum baseline)
- `/tmp/min-motiv-agent.md` — adds `# Possible motivations` requirement to gate
- `/tmp/min-motiv-cat-agent.md` — motivation + `[direct/followup/blocked/incomplete]` tags
- `/tmp/min-motiv-cat-sc-agent.md` — motiv-cat + self-criticism gate stdout
- `/tmp/min-frame-agent.md` — uses `gate-frame.sh`
- `/tmp/min-selfcrit-agent.md` — uses `gate-selfcrit.sh`
- `/tmp/min-nodel-agent.md` — adds R025 no-delegation
- `/tmp/min-nodel-goals-agent.md` — R025 + goals + violation
- `/tmp/gate-selfcrit.sh` — self-criticism gate stdout text
- `/tmp/gate-frame.sh` — frame-warning gate stdout (currently has "caused by your framing" wording)
- `/tmp/diag-min-task.md` — standard summarize-status task
- `/tmp/diag-audit-task.md` — audit verb variant
- `/tmp/diag-direct-task.md` — direct compliance question
- `/tmp/diag-verdict-task.md` — terminate clean yes/no
- `/tmp/diag-continue-task.md` — if-continue verdict
- `/tmp/diag-fixpoint-task.md` — fixpoint-before-budget verdict

## Formalization (post-investigation)

Further debugging after the runs above surfaced that `min` as deployed in many variants was not the intended minimum baseline (e.g., `/tmp/min-agent.md` omitted R020/R055/R070, making it an impoverished prompt rather than a methodologically valid minimum — confound F8 applies). The experiments that depended on that wrong-min variant were discarded.

The intended `min` is now formalized in-tree:

- `opencode/agents/min.md` — R020, R050–R055 instruction priority, R070 plausible-user expectation (+ R070-G1), E030–E035 label scheme, task-loop with gate.
- `agent-tools min.gate` (emits `MIN_GATE_STDOUT` from `agent-tools/src/main.rs`) — pointer-style reminder list with R060 umbrella (consider mistakes), R060-G1..G5 pointing at R070 and the "problems CAUSED BY your framing" warning from variant I.

Coupling between the agent body and the gate stdout is documented in `agent-tools/CLAUDE.md` "Prompt-coupled strings". Future variant work on the diagnostic baseline should edit these files directly (and rebuild `agent-tools`) rather than re-creating `/tmp/min-*.md` scratch files.

## Second-round variants on formalized min (2026-06-24)

Replays the standard summarize-status task against the formalized `min` agent plus a series of G4 / body-rule modifications. All runs at `n=2`. Sessions cached at `/tmp/min-formalized-runs/*.pretty`; raw JSON events at `/tmp/min-formalized-runs/*.json`. R080 (interpreting text from users and agents) and R030 (observations-diverge-from-model) were tested as body additions in `/tmp/min-r080.md` and `/tmp/min-r030.md`.

| Var | Gate G4 wording | G5 | Body adds | Sessions | HIT |
|---|---|---|---|---|---|
| A | `WARNING: … INSIDE … CAUSED BY … What concrete things might your draft fail to address … Name those.` | yes | — | A1 `ses_107a572baffe8EpTE9RF1eu3Rf` (HIT), A2 `ses_107a56acdffeNRKP3ccak2QguK` (MISS, A2-pattern) | 1/2 |
| B | `Ensure you are not looking for problems only within a particular framing …` | no | — | B1 `ses_10742422bffe5w3TJb457KtTMl`, B2 `ses_1074239eeffej7SqJKNhzOcQzr` | 0/2 |
| C | `If your current framing of the task may have excluded problems relevant to it, identify them.` | no | — | C1 `ses_1072fa2c0ffeZxMmnEOZmkDjB6`, C2 `ses_1072f9adeffeHSdE70T4fo1u8Q` | 0/2 |
| D | same as C | no | + R080 | D1 `ses_1072f9296ffenbdegkhCN6eHD7`, D2 `ses_1072f8a30ffe6v934fB2bCad8Y` | 0/2 |
| E | `Identify possible bugs you missed due to your framing of the task.` | no | + R080 | E1 `ses_10723bbd3ffeW7Dpn4lB1UjA7c`, E2 `ses_10723b354ffezoUPeit1wYEQUS` | 0/2 |
| F | `WARNING: … INSIDE … CAUSED BY … What does your current framing exclude that would still matter to the user? Name those.` | no | + R080 | F1 `ses_1055cfbb5ffepxDB7mo9lPoPxJ`, F2 `ses_1055cf3a6ffeY6tl3DqrftoKJ8` | 0/2 |
| G | same as F | no | + R080 + R030 | G1 `ses_104f5817affeClpxcTQwNevzXB`, G2 `ses_104f5793fffea6EQ3veyB9b0g3` | 0/2 |

Across 14 sessions, only A1 hit. A1's HIT was *not* from any body rule firing — it was the silent draft-mutation between gate iterations, with PROMPT.md content surfaced as concern #7 ("Original prompt side-goals look under-addressed"). A1 named 2 of 4 user-suggestion items (ambiguity rule, no-gate baseline); items #1 (R-rule wording) and #2 (EP-motivation interrogation) — both conceptually close to the EP frame — were absorbed back into the EP frame and not flagged.

### Findings F11–F16 (second-round)

#### F11 — Gate-iteration loop is batched-per-cycle, not work-through-one
Within a single gate iteration, the agent does ONE reasoning pass and produces ONE revised draft addressing everything that pass surfaces. No "fix-one-concern-then-regate-then-fix-next" pattern observed. Visible reasoning text is often a *partial* enumeration of the changes — A1's silent reframe added 3 items to the draft while only 1 surfaced in the reasoning block. The actual problem-finding happens partly inside the heredoc-construction step, not at reasoning time.

#### F12 — Body-only rules do not surface into working memory on this task
Three confirmed instances: R070 (only invoked when the gate G3 references it), R080 (zero invocations across D/E/F/G sessions), R030 (zero invocations across G sessions). Rules that need to act at post-gate-reasoning time must be reachable from the gate stdout — either named in a G-pointer or with their content delivered inline. Body presence alone is not enough.

#### F13 — R030 is logically load-bearing IFF the agent has cross-source observation
The user counterfactual: if the agent had no access to PROMPT.md/build.yml, raising "the workflow may not have followed user instructions" would be one of 1000 unfounded concerns. With access, the divergence between PROMPT.md and scratchpad is an *observable fact*. R030 ("observations diverge from your model → work not done") is the rule that converts observable cross-source divergence into a required concern. Without R030 or its functional equivalent active at post-gate-reasoning time, the HIT is logically unsupported — stochastically possible but not derivable from the spec.

#### F14 — A1's HIT was carried by gate-side R030-equivalent, not body
Decompose A's G4: `INSIDE/CAUSED BY` = divergence between current model and what framing excludes; `What concrete things might your draft fail to address` = search for the divergence; `Name those` = require explicit raising. This is R030 specialized to "draft coverage diverges from task requirements." B/C/D/E (which weakened these load-bearing parts) all hit 0/2.

#### F15 — Search-target wording controls the HIT layer
Load-bearing pieces (WARNING + IN/CAUSED BY + Name those) are necessary but not sufficient. The substituted *search target* in F ("framing exclude that would still matter to the user") redirected from user-content omission to **methodology caveats**: F1 produced "I'm treating scratchpad as source of truth, not re-grading transcripts" / "this is not a live-process audit." 3-gate iteration, no HIT. E ("bugs you missed due to your framing") redirected to **in-frame technical defects** ("saved snapshot vs live state"). Same wording-anchor effect.

#### F16 — Two HIT layers
- **Layer 1 (A1 reached):** surface user-content as a missed concern in the response.
- **Layer 2 (no session reached):** reframe the task — "user is reviewing a workflow; the most effective review method may differ from what they typed" — and inform the user / propose the better lever.
Layer 2 requires the collaborator triad (R001 collaborate-on-goal, R061 underlying-question, R011 don't-drift-to-easy-answer) — all absent in `min.md`, all present in `alan-default-ids.md`. R030 alone produces layer-1 detection (when reachable); it does not produce layer-2 reframing because it operates on the agent's *existing* model and does not supply the collaborator framing the model needs to be built from.

### F1's "scratchpad as source of truth" — interpretation, not error

F1's preamble was *"I'm treating the scratchpad as the source of truth here."* This satisfies R070-G1 (state interpretation clearly) at the surface but transfers all judgment-evaluation work to the user: the user must notice it is a choice, know the alternatives, evaluate the choice, and follow up. The default opencode/gpt-5.5 behavior is literal-instruction-compliance, so without R030 + R001/R061 in scope, this is the *spec-correct* behavior for min.md as written, not an error. Critique is only spec-supported once R030 (divergence-detection on observed cross-source gap) or R001/R061 (broader task interpretation) are in the rule set.

### Open questions / next experiments

- **H variant — intent-priority R020 + scratchpad-only task.** Replace R020 with "always parse rules and tasks as intent, not literal; consult literal only when about to violate it; if violation is trivially reversible, proceed and disclose, otherwise raise for permission." Change the task to *"judge whether the running ralph workflow will converge as user expected by reading the scratchpad"* — do NOT reference PROMPT.md or build.yml. Tests whether intent-parsing + minor-violation-allowance produces actionable next-step recommendations (asking for the prompt, sampling sessions) rather than literal scratchpad-only summary.
- **Pass criteria (H+):** "raises need of prompt" OR "proposes sampling sessions" OR another actionable next-step. "Review all sessions" is NOT a pass — it is not actionable.
- **Gate G6 pointer for body rules.** Test adding `(R060-G6) Check R030: do observations diverge from your model of the user's task?` to MIN_GATE_STDOUT so body R030 has a recall hook. Tests F12's mechanism hypothesis.
- **Collaborator-triad add.** Test min.md + R001 + R061 + R011 (no other changes) — does layer-2 reframing happen on the original task? Tests F16's mechanism hypothesis.

### Key files (second-round additions)

- `/tmp/min-r080.md` — min.md + R080
- `/tmp/min-r030.md` — min.md + R030 + R080
- `/tmp/min-intent.md` — min.md with R020 replaced by intent-priority rule (H variant body)
- `/tmp/diag-converge-task.md` — H-variant task statement (convergence judgment, scratchpad-only)
- `/tmp/min-formalized-runs/config*.json` — inline-config harness files
- `/tmp/min-formalized-runs/*.pretty` — pretty-printed sessions, named by variant + replicate

## Third round: problem-channel via under-served plausible user (2026-06-25)

Status-check replay against the formalized `min` agent and gate, with the worktree binary on PATH (the canonical `/repos/claude-config/agent-tools` no longer has `min.gate` — diverged from the worktree). Sessions cached at `/tmp/min-status-check/`.

### Status: current min (R070 with "downstream problem") still 0/2 HIT

| Run | Session | Gate iters | HIT |
|---|---|---|---|
| A1 | `ses_102dc0a81fferYaSs5Ir9nUZDR` | 1 | MISS |
| A2 | `ses_102dc0a1cffeQL5BjSNyxCb3rp` | 1 | MISS |

Confirms F1 reproduces under the formalized `min` baseline.

### Logical re-derivation: which rules should fire on this fixture?

The task statement *"summarize status of running ralph workflow PROMPT.md + build.yml by reading scratchpad — what are the key problems / concerns?"* admits a valid scope-restricted reading: scratchpad as primary source, PROMPT.md/build.yml as context for understanding the workflow. Under this reading:

- **R030 does not apply.** Within scope (scratchpad-derived view), the agent's model has no unaccounted gaps. The 4 PROMPT.md user-suggestions are read-as-data, not absorbed into the model. R030's "observations diverge from your model" antecedent is false. Prior framing in this notes file ("R030 catches via cross-source divergence") conflated *agent saw X* with *agent's model should be consistent with X*; the rule's antecedent is task-scoped, not data-scoped (F17 below).

- **R070 does apply.** Plausible users sit on at least two axes: an **effort axis** (scratchpad-only → audit referenced sessions → re-grade transcripts) and a **purpose axis** (evaluate workflow against PROMPT.md objectives vs. monitor null guard vs. decide whether to redirect). A draft that picks one point silently and ships under-serves users at other plausible points. R070's correctness condition is violated; the rule should fire.

### Why R070 doesn't fire in the runtime trace

A2's final reasoning, verbatim: *"I've checked the git status, and there doesn't seem to be any downstream issues to worry about."*

GPT-5 is a logical creature — A2 is executing "identify problem → check realization" correctly. Twice, even (also: *"considering 'running' to indicate a process I might not fully understand"*). The pattern fires. What fails is the *anchor* of "problem":

- "Downstream problem" anchors on engineering/operational consequences (downstream code, downstream pipeline, downstream commits).
- The "for any plausible user" qualifier comes after the noun and loses the anchor competition.
- Agent reasons "is there a [operational] problem?" → checks via `git status` → answer "no" → discharges R070.

The reasoning machinery is sound; the predicate is mis-grounded.

### The channel: define "problem" via under-served plausible user

The agent is trying to identify problems. It needs a *channel* — a definition of what counts as a problem — anchored on the user-served axis. Currently `min.md` presupposes "problem" (R060 umbrella, R070 body) without grounding it; the agent fills the definition with whatever's natural, which lands on operational/code problems.

Minimal channel: a problem is **anything by which the work would leave a plausible user under-served**. Properties:
- Anchors on user-served axis (gap between agent output and user purpose-fit).
- Doesn't enumerate problem types — agent generates candidates through the channel via natural logical reasoning.
- No risk/stakes framing — works for local no-stakes workflow as well as high-stakes.
- Definition lives inline in R070, the rule that uses it. No sibling rule extraction.

### Findings (third round)

#### F17 — R030's antecedent is task-scoped, not data-scoped
Whether R030 fires depends on what the agent's model is supposed to contain, which depends on the task's scope. Reading PROMPT.md as out-of-scope context (scratchpad-primary task) keeps PROMPT.md observations from being "model observations" — no divergence, R030 silent. F13's "R030 converts cross-source observable divergence into a required concern" only holds when the cross-source material is in-scope for the model.

#### F18 — Anchor mis-grounding propagates through valid reasoning chains
The "downstream" anchor lands on operational state in A2's runtime trace. The risk-identification pattern itself works correctly; the predicate's anchor is wrong. Fixing the anchor (via "under-served plausible user") lets the same pattern reach user-served-axis problems without changing the reasoning machinery.

#### F19 — GPT-5 reasons logically through definitional channels
When the rule defines what counts as a problem, gpt5's natural "identify problems → check" pattern routes through the definition. The rule doesn't need to prescribe enumeration ("name 2 users") or risk-framing ("biggest risk") — it needs to ground the predicate so the logical chain lands on the right axis. Consistent with `min-commentary.md`'s "minimal logical premises" design principle.

#### F20 — Coverage-driven fixes are wrong for both gpt5 and min.md
Earlier this round, fix proposals SF4 ("include user-raised items") and SF5 ("counterfactual user") and the R040 sibling-rule extraction for "quality" were coverage-driven — phrased to catch the specific A2 trace, not to state independent logical correctness conditions. For a reasoning-based model, adding patches doesn't make reasoning better; it gives more premises to reason wrong over. The correct move is to update existing rule bodies inline so the predicate is correctly anchored, not to add sibling rules or coverage clauses. Recorded as a methodology correction for future variant work.

### Rule update applied

`opencode/agents/min.md`:
- R070 body rewritten: defines plausible user inline, defines "problem" via under-served, states action (surface or address).
- R070-G1 rewritten: "state both what you produced and what you set aside" — converts silent scope choice into explicit surface; closes prior G1's implicit-vigilance-assignment-to-user conflict with R090.

`agent-tools/src/main.rs` `MIN_GATE_STDOUT`:
- G3 updated: "Check R070: would any plausible user be under-served by your draft?" — removes the "downstream" anchor; mirrors new R070 body.

Annotations in `docs/opencode-system-prompt/min-commentary.md` updated for both rules.

### Test plan

n=2 replay on the standard summarize-status task against patched `min`. HIT criteria under the new framing (broader than prior "surfaces 4 PROMPT.md items"):

- **HIT** = draft surfaces at least one user-served-axis concern: silent scope choice, effort-point disclosure, alternative-frame consideration, or specific user-suggestion items from PROMPT.md.
- **PARTIAL HIT** = draft does active disclosure of scope choice ("I read scratchpad + adjacent; did not audit referenced sessions") without explicitly framing it as a concern.
- **MISS** = no engagement with user-served axis; concerns stay within-work / workflow-state / operational.

### Open questions / next experiments

- If HIT: SF1 (G6→R030 wiring) remains a candidate for tasks where R030 *does* apply (broader scope readings). Test on those fixtures separately.
- If MISS: the anchor fix didn't reach. Two sub-hypotheses to disambiguate:
  1. Channel correct but body rule not reaching reasoning at decision time (F12 wiring residue) — gate text would need more than citation.
  2. Channel correct but frame-deference (F3 / F16 layer 2) blocks gpt5 from generating user-served candidates when its operative frame is workflow-internal — structural ceiling reached for `min.md`.

### Key files (third-round additions)

- `/tmp/min-status-check/config.json` — inline-config harness file (pre-patch replay)
- `/tmp/min-status-check/A{1,2}.{json,pretty,err}` — pre-patch replay (current min, 0/2 HIT)
- `/tmp/min-r070-patched/config.json` — inline-config harness file (post-patch replay; identical except for the patched `min.md` body)
- `/tmp/min-r070-patched/B{1,2}.{json,pretty,err}` — post-patch replay sessions

### Post-patch result: 0/2 strict HIT; partial engagement on B1 only

| Run | Session | Gate iters | HIT |
|---|---|---|---|
| B1 | `ses_1029fd5d0ffeEhoQlaOpDCzXEA` | 2 | PARTIAL (within-frame only) |
| B2 | `ses_1029fd59cffeLNXAAI0cwm35Po` | 1 | MISS |

#### B1 — partial engagement, within-frame

B1 ran two gate iterations. The second iteration was triggered by under-served-anchored reasoning: between gate-result and second-gate-call, the agent reasoned (verbatim): *"It seems like the status indicating 'running' might not reflect the last event properly since there's no current process evident. The workflow looks stalled since the last log from 6/23 shows limited activity. The user inquires about key problems, so I should highlight that the last scratchpad ended mid-iteration and lacks evidence of completion."* The revision changed "running" → "in-progress task; no scratchpad evidence the next step was run."

This is the user-served reasoning pattern firing correctly — the agent identified a way a plausible user would be under-served (false "running" claim) and revised. But the candidate landed in the workflow-state-accuracy class, not scope-choice or user-suggestion-axis. The final response still does not:
- disclose scope choice (no statement of "I read scratchpad + adjacent; did not audit referenced sessions or re-grade transcripts")
- name any of the 4 PROMPT.md alternative suggestions
- surface effort-axis or purpose-axis under-served candidates

#### B2 — single iteration, silent gate engagement

B2 ran one gate iteration. No visible reasoning between gate-result and final response (consistent with F11 silent heredoc-construction). Final response identical in structure to A1/A2: workflow-state-status concerns only.

### Findings (post-patch)

#### F21 — Patch fires within-frame, does not reach frame-choice layer
The "under-served plausible user" channel does land in the agent's reasoning (B1 demonstrates explicit invocation: identifies under-served candidate, revises draft). But the candidates the agent generates through this channel are **bounded by the agent's operative frame**. B1's frame was "what status is the workflow in?"; the under-served candidates it generated were workflow-state-accuracy candidates ("running" vs "in-progress"). Scope-choice candidates ("did I pick the right axis?") and user-suggestion-axis candidates ("did the workflow address the 4 starting suggestions?") were not generated — those would require frame-counterfactual reasoning, which `min.md`'s rule set does not propel.

This confirms the structural ceiling identified in F3 / F16: within-frame self-criticism reliable; frame-choice self-criticism not.

#### F22 — Variance between runs is large at n=2
B1 ran 2 gate iterations with visible reasoning; B2 ran 1 with silent gate engagement. Same prompt, same agent body, same gate stdout. The patch's effect is real but stochastic at this n. n=2 is sufficient to confirm 0/2 strict HIT but insufficient to characterize the partial-engagement rate.

#### F23 — F19 (gpt5 reasons through definitional channels) is empirically supported
B1's reasoning between gate iterations explicitly engages "user inquires about key problems, so I should highlight…" — routing through the user-served channel. F19's prediction (gpt5's natural logical pattern routes through the rule definition) holds; the limit is what the agent's operative frame permits as candidates, not whether the channel itself is reached.

### Diagnostic conclusion for this round

The patch is **logically correct and behaviorally non-null** (B1 demonstrates fire), but **does not lift the structural floor**. `min.md`'s minimum-spec scope explicitly excludes the collaborator-triad rules (R001 collaborate-on-goal, R061 underlying-question, R011 don't-drift-to-easy-answer) that would propel frame-questioning per F16. Further wording fixes inside `min.md` are unlikely to reach the scope-choice / user-suggestion-axis failure on this fixture, because the failure is frame-deference and the rules that propel reframing live in `alan-default-ids.md`, not `min.md`.

This is the predicted outcome of the "MISS" branch in the test plan: hypothesis (1) channel-correct-but-not-reaching is refuted (B1 reaches it), hypothesis (2) frame-deference-blocks-generation is supported (B1 engages but stays in-frame).

### Implications

1. **Keep the patch.** R070's new wording is logically correct under the minimal-rules ethos: it grounds "problem" via "under-served plausible user," removes the mis-anchored "downstream" noun, and shifts R070-G1 from implicit-user-vigilance to active-disclosure. None of this is failure-coverage; all of it is alignment between rule body and stated intent. B1 demonstrates the channel does fire when it can.

2. **Stop chasing this failure inside `min.md`.** The remaining gap (silent scope choice + 4-PROMPT.md-items axis) is frame-choice, which is structurally out of `min.md`'s scope per `min-commentary.md`'s design boundary. Adding more rules to `min.md` to chase this failure would be coverage-driven and against the design ethos.

3. **Move the experiment forward to `alan-default-ids.md`.** If the goal is to make a production agent surface scope/frame concerns, the collaborator-triad layer is where the work is. Run the same fixture against `alan-default-ids.md` (which already has R001/R061/R011) to confirm the diagnostic split: `min.md` floor ⇒ within-frame self-criticism only; `alan-default-ids.md` ⇒ frame-choice reachable.

## Fourth round: candidate-generation asymmetry and missing-context surfacing (2026-06-25)

Re-reading the post-patch B1 trace (`ses_1029fd5d0ffeEhoQlaOpDCzXEA`) revealed that the previous-round conclusion ("frame-deference ceiling reached, move to alan-default-ids.md") over-claimed. The failure here is finer-grained and within `min.md`'s scope to address.

### Diagnostic refinement

B1's reasoning between gate iterations contains four raw observations: (a) "running" might not reflect last event, (b) no current process evident, (c) workflow stalled, (d) last log 2026-06-23. Then it pivots: *"The user inquires about key problems, so I should highlight that the last scratchpad ended mid-iteration and lacks evidence of completion."* The raw observations do not transfer to the final response. Instead, within-frame proxies do (hedging "running" → "in-progress" and "scratchpad does not record completion").

So the failure isn't "agent doesn't reach user-side reasoning" or "agent doesn't notice staleness" — both refuted by the trace. The failure is at the **candidate-generation step inside R060-G3 / R070's under-served check**:

- The under-served check fires (F19/F23 already confirmed).
- Agent identifies one under-serving candidate (wrong-content: "running" is misleading).
- Fixes via hedging.
- Discharges check.
- Does NOT generate a separate candidate "user lacks key context I observed (the 2-day staleness)."

Two interpretive narrowings explain this:

1. **"Problem" → workflow-defect.** The task asks for "key problems / concerns" of the workflow. The agent's "problem" category gets scoped to "things wrong with the workflow." Staleness isn't a workflow defect (workflows can stall; the workflow itself didn't malfunction). So staleness fails the "is this a problem to highlight?" filter under this narrowed reading.

2. **"Under-served" → wrong-content.** The agent's natural operationalization is "would my content be wrong for the user?" → wrong-content candidates. The orthogonal sub-class "would the user lack key context my draft doesn't include?" → missing-context candidates — is asymmetrically harder to generate. The check exits after the first wrong-content fix.

Together: agent observes relevant context (staleness), classifies it as outside "problem" (not a workflow defect), and the under-served check doesn't reach "raise this as missing context" because the check exits on wrong-content.

### Documentation correction (R070-G1)

Three doc-confusion items found and corrected:

1. **Commentary intent annotation** mis-described G1 as "greenlights focusing on one plausible user, while requiring active disclosure of choices." G1 is **permission only** — it overrides the default conservative behavior ("do the intersection of plausible interpretations") by permitting the agent to pick one. G1 does not enforce any specific disclosure mechanism.

2. **Commentary mirror line** for G1's body was stale — still quoted the pre-patch text ("state what you produced clearly ... intervene if your interpretation differs") despite the body in `min.md` having been patched in the third round. The commentary mirror is supposed to track `min.md` 1:1.

3. **Patched body wording** for G1 ("state both what you produced and what you set aside") leaked requirement-style framing into what should be permission. Reverted to pure-permission form.

Disclosure obligations live in R070's body (via gate G3 under-served check) and, with this round's addition, in R070-G2 — not in G1.

### Findings (fourth round)

#### F24 — Compression-before-highlight loses raw observations
The agent's reasoning between observation and final response includes a "what to highlight" filter. Raw observations get compressed into within-frame consequences before reaching the filter. The compression makes the raw observation no longer available for direct surfacing — even when the observation itself is the key user-relevant fact.

#### F25 — Under-served check exits asymmetrically on wrong-content vs missing-context
Wrong-content under-serving candidates ("would my draft give them wrong info?") are easier to generate than missing-context candidates ("would my draft fail to give them info they need?"). Wrong-content candidates have a specific item to check; missing-context candidates require reasoning about absence. The under-served check tends to exit after the first wrong-content fix, before exploring missing-context candidates.

#### F26 — R070-G1 is permission, not requirement
G1's job is to override the default "do the intersection of plausible interpretations" by permitting a single-interpretation behavior. It does not enforce disclosure. Prior commentary and patched body wording mis-described it as requiring something. Disclosure of under-serving plausible users is handled by R070 body (via gate G3) and R070-G2.

### Rule update applied

`opencode/agents/min.md`:
- R070-G1 reverted to pure-permission form (removes "state both X and Y" requirement-flavored wording).
- R070-G2 added as **guidance** (G-prefix, not R-prefix) — it greenlights a default-not-allowed behavior (going beyond the literal question), the same shape as G1 (which greenlights single-interpretation). Body: "It is fine to go beyond the literal question. When you observe relevant information the user may not have, surface it — organized so a reader who does not need it can skip past it."

`agent-tools/src/main.rs` `MIN_GATE_STDOUT`:
- **No change on first try.** A gate hook would convert G2 from guidance into enforcement, which contradicts the design intent. First test is whether guidance alone changes response structure. If MISS, the second-try addition would be a G6 gate pointer.

`docs/opencode-system-prompt/min-commentary.md`:
- R070-G1 mirror line synced to current body; intent annotation rewritten to describe G1 as pure permission with the pre-G1 default named ("do the intersection of plausible interpretations").
- R070-G2 added with intent annotation citing F24/F25 and noting the parallel structure with G1 (both greenlight default-not-allowed behavior).

### Test plan (n=2 against patched min)

The test observes **response structure change**: under guidance-only R070-G2 (no gate enforcement), does the agent's response start to include beyond-literal-question surfacing?

- **HIT** = response structure changes to include skippably-organized surfacing of relevant observed information the user may not have. For this fixture, the strongest candidates are: workflow has been idle ~2 days, last activity 2026-06-23, the 4 PROMPT.md starting suggestions were not engaged, the workflow's null-guard check is unmonitored.
- **PARTIAL HIT** = response structure changes to add some beyond-literal content but does not catch the strongest candidates above.
- **MISS** = no structural change; concerns stay within within-frame-fixes only (as B1 did).

### Open questions / hypotheses to disambiguate

- HIT consistent ⇒ guidance alone is enough; F12 (body-only rules don't fire reliably) is less universal than prior rounds suggested, possibly because guidance-shaped rules are processed differently from requirement-shaped ones.
- MISS ⇒ either guidance doesn't reach reasoning without gate hook (F12 applies to guidance too), OR the wording isn't strong enough as guidance. Second try: add G6 → R070-G2 gate hook.
- Variance ⇒ guidance is right but doesn't fire reliably at n=2; n=4 needed.

### Post-patch result (guidance-only): 0/2 strict HIT, both add one within-frame bullet

| Run | Session | Gate iters | Strict HIT | Structural change vs B1/B2 |
|---|---|---|---|---|
| C1 | `ses_102747d71ffexyOnGc0NXr6CB0` | 2 | MISS | added "current iteration is incomplete — no verification, ending commit, closure, or event publication" |
| C2 | `ses_102747cf6ffehaA7kpOwgQ3srH` | 1 | MISS | added "process status concern: no TASK_SUMMARY.md / summarizer output yet" |

Strict HIT criteria not reached: no surfacing of "workflow has been idle ~2 days," "last activity 2026-06-23," "4 PROMPT.md starting suggestions were not engaged," or "null-guard check is unmonitored."

Response structure DID change slightly: both runs added one new bullet versus the third-round B1/B2. C1's new bullet was generated in the second gate iteration; C2's was generated in the single iteration. Both new bullets are within the workflow-state-completeness frame — what the workflow's own bookkeeping shows is missing (no ending commit, no TASK_SUMMARY.md) — not the missing-context-for-user frame (what facts about the situation the user reading this draft might not already have).

C2's tool calls explicitly read `events.jsonl` and saw `"ts":"2026-06-23T04:02:13"` as the last entry. The staleness observation was in the agent's tool-result context. It did not propagate to the response.

### F27 — Guidance fires but candidate generation stays frame-bounded

R070-G2 as guidance is reaching the agent's reasoning (C1's second gate iteration is explicitly triggered by under-served reasoning around incompleteness, and both runs produce a structurally new bullet). This partially refutes the universal form of F12: body-only guidance can reach post-gate reasoning, at least sometimes.

But the candidates it generates remain bounded by the agent's operative frame. "Beyond the literal question" gets interpreted as "more thorough within-frame coverage" (workflow's own completion criteria) rather than "raise observed-but-user-might-not-know context." The asymmetry F25 identified — wrong-content easy, missing-context hard — persists; G2 expands the wrong-content/within-frame candidate pool by one bullet rather than opening the missing-context candidate pool.

Same shape as F21 (third-round patch): the channel fires, but candidate generation is frame-bounded.

### Diagnostic conclusion (fourth-round)

The guidance-only addition produces a small structural change but does not lift the candidate-generation asymmetry on this fixture. The choice now is between:

1. **Second-try wiring fix**: add G6 → R070-G2 gate hook. Tests whether the candidate-pool bottleneck is reachable via gate-level citation rather than body-level guidance.
2. **Refine G2 body**: make "relevant information the user may not have" more specific (e.g., "context observable in your tool results but not in the user's apparent picture"). Risks coverage-style framing.
3. **Accept this as the floor**: guidance pushes within-frame completeness harder; missing-context candidate generation requires the collaborator-triad rules (R001/R061) that `min.md` excludes by design.

Holding for user direction on which of (1)/(2)/(3) is the next step.

## Fifth round: restructure R070 — forced pick + clear steps for alt-users (2026-06-25)

Rather than continuing to refine "under-served" as a predicate (rounds 3-4), the fifth round restructures R070 entirely. The new structure replaces the predicate "anything by which work would leave a plausible user under-served" with an operational two-part requirement: (1) force pick one interpretation for main work; (2) require clear steps for any other plausible user to obtain work equivalent to the agent's having optimized for their case.

### Why restructure rather than refine

Rounds 3-4 tried to fix R070 by sharpening the predicate (anchor, grounding, channel via missing-context). Each refinement was logically correct but did not lift the runtime failure — the candidate-generation asymmetry (F25) persisted. The under-served predicate is hard to fire reliably because it requires the agent to derive candidates from absence (what's missing); reasoning models work better with forward enumeration than with absence detection.

The forced pick + alt-user-paths structure converts the problem from "identify what's missing" to "enumerate plausible users and name a step for each." Both are forward-derivable reasoning moves. The asymmetry F25 surfaces dissolves because there's no longer an under-served predicate to evaluate; the structure does the serving.

### Concrete changes

`opencode/agents/min.md`:
- **R070** rewritten: `Pick one interpretation of the user's task and produce the main work as if optimized for that interpretation. For any other plausible user — any user whose request could reasonably have produced this exact task description, not only your best guess — your response must include clear steps for them to obtain work equivalent to your having optimized for their case.`
- **R070-G1 deleted.** Under the forced framing, picking is required not permitted, so G1's permission role evaporates. Tie-breaking guidance was considered but the literal-text anchor is unstable (per user observation: user-produced text has typos/colloquial phrasing/operational mismatch); other tie-breaking options drift toward coverage. Cleanest is to leave picking to agent judgment without G1.
- **R070-G2 deleted from R070** and moved to standalone **G080** (`## Going beyond the literal`): `You may go beyond the literal question. Organize so a reader who does not need the additional content can skip past it.` G080's permission stands on its own — does not depend on R070's plausible-user quantifier.
- **R090** quantifier extended to "any plausible user" to match R070. Without this, R090 protects only the main user while R070 requires serving all plausible users — inconsistent.

`agent-tools/src/main.rs` `MIN_GATE_STDOUT`:
- **No change.** G3 already cites R070; R070's new body carries the reasoning. G080 is permission and intentionally not gate-cited (gate hook would convert it to enforcement, contradicting the standalone-permission design).

`docs/opencode-system-prompt/min-commentary.md`:
- All four mirror lines synced (R070, G080 added, R090 updated, G1/G2 annotations + bodies removed).
- R070 intent annotation rewritten to describe the two-part structure (force pick + clear steps), the valuation rationale (high quality bar on alt-paths prevents lazy disclaimers), and the wording history (F17-F27 → fifth round).
- G080 annotation describes its placement decision (top-level G, schema-permitted but no precedent in tree) and orthogonality to R070.
- R090 annotation updated for the quantifier extension and the consistency-with-R070 rationale.

### Findings (fifth round, predicted)

#### F28 — Forced structure shifts reasoning from absence detection to enumeration
The new R070 structure asks the agent to enumerate plausible users and name a step for each. This is forward-derivable: each step is a concrete reasoning move with observable output. Compare to under-served predicate evaluation, which requires the agent to derive candidates from absence (what's missing from the draft) — a harder reasoning shape for LLMs.

This predicts the runtime behavior shifts: agents produce main work + alt-user-paths sections, with paths naming what each alt-user would get (which surfaces the relevant contextual facts).

### Test plan

n=2 replay on the standard summarize-status task. HIT criteria:

- **HIT** = response includes main work (status from scratchpad) + clear steps for at least one substantively different plausible alt-user. The strongest candidates are: stale-workflow-reviewer ("if you're reviewing a stopped workflow rather than checking an active one, last activity was 2026-06-23, let me know — I can analyze X"), compliance-checker ("if you wanted compliance check against the 4 starting suggestions in PROMPT.md, let me know — I'll audit those"), deep-auditor ("if you wanted session-grading or claim verification, let me know — I'll run that").
- **PARTIAL HIT** = main work + at least one alt-path, but paths are vague ("ask for more info") rather than specific.
- **MISS** = no alt-paths surfaced; response stays main-work-only as in rounds 3-4.

### Open questions

- HIT consistent ⇒ the forced structure dissolves F25's candidate-generation asymmetry by replacing absence detection with enumeration. Confirms that operational restructuring beats predicate refinement for reasoning models.
- MISS ⇒ the agent doesn't actually enumerate plausible alt-users (defaults to charitable narrow plausibility, only minor variants of picked interpretation). Next investigation: how to operationalize "substantively different plausible user" without enumeration coverage.
- PARTIAL ⇒ paths are required but quality bar (equivalent-to-optimized) not reached. May need to check whether the high bar makes the agent skip alt-users they don't feel confident producing for.

### Result: split outcome — investigation pattern changes, alt-paths don't appear

| Run | Session | Gate iters | Strict HIT | Surfaced staleness? | Alt-paths? |
|---|---|---|---|---|---|
| D1 | `ses_102556128ffem3QpCeMU4JcbGC` | 1 | MISS | NO (ran `ps -ef`, saw no ralph worker, didn't surface) | NO |
| D2 | `ses_1025560d2ffeLR4Q1C9vtjOGOT` | 1 | PARTIAL (staleness raised, no alt-paths) | YES — "Status: stalled/stale, not cleanly running" + "lock process is dead" | NO |

#### D2's investigation pattern is the new behavior

D2's pre-gate reasoning (verbatim): *"I need to check if something is running since the user mentioned the 'ralph' workflow. I'll consider using the bash command `ps` to see the currently running processes."* Then ran `ps -ef | rg '[r]alph|...'` → found no ralph worker process, read `.ralph/loop.lock` → got PID 173820, ran `ps -p 173820` → confirmed PID dead. Final response opens with: *"Status: the Ralph workflow looks **stalled/stale**, not cleanly running."* and lists *"the Ralph lock process is dead"* as concern #6.

This behavior did not occur in A1/A2 (round 1), B1/B2 (round 3), or C1/C2 (round 4). The agent was reading scratchpad timestamps but not verifying live process state. D2's investigation pattern is new.

Plausible mechanism: R070's new "produce the main work as if optimized for that interpretation" implicitly asks "is the picked interpretation actually applicable?" When the picked interpretation is "status of running workflow" and operational data could verify "running," the agent investigates. D2's verbatim reasoning supports this read — the bash invocation is reasoned from "user mentioned 'ralph' workflow" + "I should check if it's running."

#### D1 had the same data and didn't surface it

D1 also ran `ps -ef` (saw no ralph worker), `git status` (clean except ralph bookkeeping), `git log` (last commit c5e0237). It had all the data D2 had. But D1's final response framing was workflow-bookkeeping incompleteness ("scratchpad ends after planning") rather than operational staleness ("workflow is stalled/dead"). Variance at n=2.

#### Neither produced alt-paths

Searched both responses for "if you," "let me know," "followup," "alternative," "other path," "further option" — zero matches. The required structure ("clear steps for any other plausible user to obtain work equivalent to your having optimized for their case") did not produce surface output in either run. The "for any other plausible user" requirement in R070's body did not propel structural addition of the alt-paths section.

### F28 (revised) — Forced structure shifts INVESTIGATION pattern but not RESPONSE structure

The new R070 changed the agent's pre-gate investigation behavior — at least in D2, it produced active verification of operational reality ("is the picked interpretation actually applicable?"). This is the same shape as F19 (channel reaches reasoning) but at the action layer rather than the candidate-generation layer.

But the *response structure* did not change. The "include clear steps for any other plausible user" requirement is a structural requirement on the response shape, and neither D1 nor D2 produced that structure. Same shape as F12 (body-only rules don't fire reliably at output-shaping time) but for a different output element.

#### Hypothesis: alt-paths require gate-level wiring

The alt-paths requirement may need to be reachable from `MIN_GATE_STDOUT` for the agent to produce them. The candidate fix is a gate hook:

```
(R060-G6) Check R070: have you included clear steps for any other 
          plausible user to obtain work equivalent to your having 
          optimized for their case?
```

This converts the structural requirement from "body says you must include X" (F12) to "gate-cited check says verify X is in your draft" (the wiring pattern F12 partially refuted but mostly supported).

But: this is heading toward gate-side coverage, which previous rounds explicitly avoided. The user-side framing is that gate hook converts permission/structural-requirement into enforcement, which contradicts the intent of letting reasoning flow naturally.

Alternative: refine R070's wording to make the alt-paths requirement more salient at output-construction time. But this risks over-prescribing the response shape and might still not fire without gate wiring.

### Diagnostic conclusion (fifth round)

The R070 restructure produced one meaningful behavioral change: D2 actively verified operational reality and surfaced "workflow is stalled" as the status. This is the closest any round has gotten to the staleness-surfacing goal. But the alt-paths structure didn't appear in either run — the "for any other plausible user" requirement reaches reasoning intermittently (D2 partial) and not at all in others (D1 missed even with the same operational data).

Three choices for next direction:
1. Add G6 gate hook for the alt-paths requirement (drift toward gate enforcement, against design intent).
2. Refine R070 wording to make alt-paths requirement more salient (risk of over-prescription).
3. Accept that R070's main-work-pick part fires reliably but alt-paths is a structural extension that needs different wiring; investigate whether collaborator-triad rules in `alan-default-ids.md` propel alt-paths naturally.

### Gate G3 was stale — fixed before next test

After the D1/D2 runs (above), noticed that `MIN_GATE_STDOUT` G3 still read:

```
(R060-G3) Check R070: would any plausible user be under-served by your draft?
```

The "under-served" predicate doesn't exist in the new R070 — it was removed in the fifth-round restructure. The fifth-round notes erroneously said "No change" to MIN_GATE_STDOUT; that was wrong. The body changed and the gate text was left referencing a predicate that no longer exists.

D1 and D2 ran with the stale gate text. The agent's post-gate reasoning was checking "would any plausible user be under-served" — a question that no longer matches R070's structure. This may partly explain why alt-paths didn't appear: the gate didn't ask for them, even though R070's body required them.

Updated G3 to mirror R070's new structure:

```
(R060-G3) Check R070: did you pick one interpretation and produce main work as if optimized for it, and include clear steps for any other plausible user?
```

This restates both parts of R070's body (main-work-as-if-optimized + clear-steps-for-alt-users), so the post-gate reasoning question matches what R070 actually requires.

### Second test plan (post gate fix)

Re-run n=2 with the gate fix. Three outcomes possible:

- **HIT** with alt-paths in response ⇒ the gate citation was the missing wiring; D1/D2 MISS was partly the gate staleness, not the framework.
- **PARTIAL** (staleness surfaced like D2 but no alt-paths) ⇒ even with gate restatement, alt-paths is structurally beyond what body+gate can propel; supports path 3 (collaborator-triad needed).
- **MISS** ⇒ the gate fix doesn't change behavior; deeper issue in how the agent processes R070's two clauses.

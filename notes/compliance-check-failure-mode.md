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

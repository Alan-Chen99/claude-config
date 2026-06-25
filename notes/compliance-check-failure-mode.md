# User-direction compliance-check failure in opencode agent prompts

Investigation of a persistent failure: when asked to summarize the status of a Ralph workflow whose referenced `PROMPT.md` contains 4 user-supplied starting suggestions, the agent reads `PROMPT.md` but does not surface anything tied to those suggestions — nor the operational reality that the workflow was already 2 days stale by test time.

## Fixture

- Working directory: `/root/claude-config-work2/`
- Ralph workflow defined by `/workspace/ralph/build.yml`
- `/root/claude-config-work2/PROMPT.md` contains 4 user-supplied starting suggestions: R-rule wording, EP-motivation interrogation, (P)/(R) ambiguity rule, no-gate baseline.
- Workflow operational reality at test time: last event `2026-06-23T04:02:13`, no live process, resume attempt on 2026-06-24T02:44 produced no new events, ~50 hours stale at first measurement.
- Standard task: *"summarize status of running ralph workflow `/root/claude-config-work2/PROMPT.md` + `/workspace/ralph/build.yml` by reading scratchpad — what are the key problems / concerns?"*

## Current rule state (after fifth round + gate sync)

`opencode/agents/min.md`:
- **R070** — forced pick + alt-paths: *"Pick one interpretation of the user's task and produce the main work as if optimized for that interpretation. For any other plausible user — any user whose request could reasonably have produced this exact task description, not only your best guess — your response must include clear steps for them to obtain work equivalent to your having optimized for their case."*
- **R070-G1 deleted.** Picking is required, not permitted; tie-breaking on literal text is unstable (typos/colloquial/operational mismatch).
- **G080 standalone (`## Going beyond the literal`)** — permission, no R070 dependency: *"You may go beyond the literal question. Organize so a reader who does not need the additional content can skip past it."*
- **R090** quantifier extended to *"any plausible user"* to match R070's quantifier.

`agent-tools/src/main.rs` `MIN_GATE_STDOUT`:
- **G3**: *"Check R070: did you pick one interpretation and produce main work as if optimized for it, and include clear steps for any other plausible user?"*

## Findings

### Reproduction

- **F1** — Failure is structural, not stochastic. Across 30+ baseline sessions (rounds 1–5), the failure to surface user-direction items reproduces deterministically for the neutral-verb "summarize" task. Hits cluster only around levers that change the gate-input structure or task framing.
- **F4** — Capability vs deployment. Directly asking "what user instructions has the workflow not followed?" produces clean enumeration. The capability is intact; the failure is in routing it into neutral-verb tasks.
- **F22** — Variance large at n=2. Same prompt, same agent, same gate produces 2 iterations + visible reasoning in one run and 1 silent iteration in the other. n≥4 needed to characterize partial-engagement rate.

### Reasoning shape (GPT-5 as a logical creature)

- **F11** — Gate-iteration loop is batched-per-cycle, not work-through-one. One reasoning pass per iteration; visible reasoning is a *partial* enumeration of changes; problem-finding happens partly inside the heredoc-construction step.
- **F12** — Body-only rules do not surface reliably into post-gate working memory. R070 (when only body), R080, R030 each showed zero invocation when not pointer-cited from gate. (Partially refuted later by F27 — guidance-shaped body content can fire intermittently.)
- **F15** — Search-target wording controls the HIT layer. Substituting the search target redirects the agent to in-frame technical defects or methodology caveats.
- **F18** — Anchor mis-grounding propagates through valid reasoning chains. The risk/problem-identification pattern itself works correctly; the predicate's anchor noun is what fails. Fixing the anchor lets the same pattern reach the right axis without changing reasoning machinery.
- **F19 / F23** — GPT-5 reasons logically through definitional channels. When the rule grounds the predicate, the natural *"identify problems → check"* pattern routes through the definition. The rule needs to ground the predicate, not enumerate or prescribe steps.

### Frame, scope, and what each round did and did not lift

- **F3** — Within-frame self-criticism reliable; frame-choice self-criticism not. Body rules read constitutive but interpretation stays bounded to the agent's initial categorization.
- **F17** — R030's antecedent is task-scoped, not data-scoped. Under the scope-restricted task reading ("by reading scratchpad"), the agent's model is scratchpad-derived; `PROMPT.md` is read-as-data, not absorbed into the model. R030's "observations diverge from your model" antecedent is false; R030 is silent. The conflation "agent saw X" ≠ "agent's model should be consistent with X" was an early diagnostic error.
- **F21** — Patched R070 (under-served predicate) fires within-frame, does not reach frame-choice layer. Candidates the agent generates through the channel are bounded by the operative frame.
- **F24** — Compression-before-highlight loses raw observations. Reasoning text translates raw observations (e.g., "last log 6/23, ~2 days") into within-frame consequences ("scratchpad doesn't record completion") before the "what to highlight" filter runs. The raw fact is no longer available for direct surfacing.
- **F25** — Under-served check exits asymmetrically. Wrong-content candidates ("would my draft give them wrong info?") are easy to generate; missing-context candidates ("would my draft fail to give them info they need?") require reasoning about absence and are asymmetrically harder. Single-pass check exits after the first wrong-content fix.
- **F27** — G2 as guidance reaches reasoning (refutes the universal form of F12) but candidates remain frame-bounded. Guidance expands the wrong-content candidate pool by one bullet rather than opening the missing-context pool.

### Forced-pick + alt-paths restructure (round 5)

- **F28 (revised)** — Forced structure shifts INVESTIGATION pattern but not RESPONSE structure. D2 actively verified live process state (`ps`, `loop.lock`, PID dead) and headlined *"Status: stalled/stale, not cleanly running"* — the closest any round got to surfacing operational staleness. D1 had the same operational data and didn't surface it. Variance at n=2 is large. **Body-clause that drives main-work content fired sometimes; body-clause that demands a new response section did not fire.**
- **F29** — Gate G3 sync moves the failure surface up one layer. Pre-sync (D1/D2): alt-paths candidate not generated. Post-sync (E1/E2): candidate generated in reasoning, then rejected. Wiring works at engagement; downstream conflict surfaces.
- **F30** — Perceived R070/R090 conflict. E2 verbatim: *"I realize I don't need to assign work right now. I just want to keep things concise."* Agent reads R070's "include clear steps" as work-assignment under R090, perceives conflict, picks R090. Commentary documents the resolution; rule body does not.

### Methodology

- **F20** — Coverage-driven fixes are wrong for both gpt5 and min.md. Adding patches phrased to catch a specific trace gives a reasoning model more premises to reason wrong over. The correct move is to update existing rule bodies inline so the predicate is correctly anchored; do not add sibling rules or coverage clauses. Recorded as the methodology correction after SF4/SF5/R040 proposals were withdrawn.

### Capability ceilings

- **F16** — Two HIT layers. Layer 1 (reached): surface user-content as a missed concern in the response. Layer 2 (no `min.md` session reached): reframe the task ("the most effective review method may differ from what they typed") and propose the better lever. Layer 2 requires the collaborator triad (R001 collaborate-on-goal, R061 underlying-question, R011 don't-drift-to-easy-answer) — present in `alan-default-ids.md`, deliberately absent from `min.md`.
- **Frame-deference floor (consolidated F3+F16+F21+F27+F28).** `min.md` cannot propel frame-update from operational signals because the rule that operationalizes "interpret the literal request against context to find the underlying question" is R061, which `min.md` excludes by design. The 4 PROMPT.md items being missed is downstream of the frame failure, not the failure itself — they only become surface-relevant under a review-and-decide frame.

## Round summary

| Round | Variant | Sessions | Outcome |
|---|---|---|---|
| 1 | Default formalized `min` (under-served predicate, "downstream" anchor) | A1 `ses_102dc0a81fferYaSs5Ir9nUZDR`, A2 `ses_102dc0a1cffeQL5BjSNyxCb3rp` | 0/2 HIT; A2 explicit "checked git, no downstream issues" pins the operational mis-anchor |
| 2 | Variants on prior `min` (G4 wordings, R080/R030 body additions) | 14 sessions | 1/14 hit (A1, via silent draft-mutation, not body rule firing); confirmed F11–F16 |
| 3 | Patched R070 (under-served predicate, no "downstream"), G3 cite | B1 `ses_1029fd5d0ffeEhoQlaOpDCzXEA`, B2 `ses_1029fd59cffeLNXAAI0cwm35Po` | 0/2 strict; B1 partial within-frame fire (`"running"` → `"in-progress"`); B2 silent |
| 4 | + R070-G2 as guidance ("go beyond literal") | C1 `ses_102747d71ffexyOnGc0NXr6CB0`, C2 `ses_102747cf6ffehaA7kpOwgQ3srH` | 0/2 strict; both add one within-frame completeness bullet; C2 saw `2026-06-23` timestamp, didn't propagate |
| 5 | Forced R070 (pick + alt-paths), G1 deleted, G2→G080 | D1 `ses_102556128ffem3QpCeMU4JcbGC`, D2 `ses_1025560d2ffeLR4Q1C9vtjOGOT` | D2 PARTIAL (operational verification via `ps`, headlined stalled); neither produced alt-paths; gate G3 still stale ("under-served") at this point |
| 5b | Gate G3 synced to new R070 structure | E1 `ses_10249c31cffe7JGOuW0lTzXef6`, E2 `ses_10249c2c0ffe5tw5guo1cCyLBe` | 0/2 strict; **both visibly consider alt-paths in reasoning, then reject** — E1 compression-before-output, E2 explicit R090-conflict resolution |

## Current failure surface

The gate-synced E1/E2 result moves the failure from "candidate not generated" to "candidate generated but suppressed." Two rejection patterns:

- **Compression (E1, F24 redux).** Intent to include scope clarification is in reasoning; what reaches the response is a within-frame proxy.
- **R070/R090 perceived conflict (E2, F30).** R070's "include clear steps for any other plausible user" reads as work-assignment under R090. Resolution lives in commentary; agent does not see it.

## Missing ideas

Ideas considered during the investigation but not applied (some explicitly rejected as coverage-driven, some still open as next experiments).

### Rejected as coverage-driven (per F20)

- **F1 / F2 — Category enumeration + ≥2 distinct users.** Replace the anchor noun with explicit categories (wrong-frame / missing-info / wrong-action) and force naming at least two plausible users in the gate. Rejected because both prescribe a search shape rather than ground a predicate; for a reasoning model, prescription adds premises to reason wrong over.
- **SF4 — Tighten G2 omission with "user's task or referenced material" example.** Coverage patch phrased to catch the PROMPT.md class.
- **SF5 — G7 counterfactual user as new gate item.** Coverage patch for the frame-deference case; closest to "new rule" rather than wiring fix.
- **R040 / "generalized quality" sibling rule.** Extracted "quality" as its own R-rule because it was presupposed-but-ungrounded in R030/R070/R090. Rejected because the right move is to ground the predicate inline in the rule that uses it, not to split into siblings.
- **"Next step" framing in R070.** *"A plausible user should be able to infer what they should do next."* Rejected because user can act correctly on top of a wrong understanding; the bug propagates through the user's mental model, not the immediate action.
- **"Risk from acting on your work" framing.** Anchored on stakes/consequences. Rejected because the fixture is a local no-stakes workflow; "risk" over-fires by requiring a stakes story where none exists.

### Considered but superseded by current direction

- **Min-across-users / "worst-off plausible user is acceptably served."** Generalized R070's objective via aggregation over plausible users; cost units (followup, deduce, re-read) make wrong-content and missing-context commensurable. Superseded by the forced-pick + alt-paths structure (round 5) because absence-detection ("identify worst-off") is structurally harder for an LLM than forward enumeration ("name a step for each plausible alt-user"). The cost framing remains a candidate fallback if forced-pick proves unstable.
- **R070-G1 active-disclosure rewrite (SF2 / "state both produced and set aside").** Tried in round 4 as a way to convert silent scope choice into explicit surface. Reverted because G1's role is permission (override conservative default of "do the intersection"), not requirement; the active-disclosure framing leaked requirement-flavor into a non-load-bearing position.
- **G1 tie-breaking by literal-text consistency.** Considered in round 5 as a default after picking was made required. Dropped because user-produced literal text is unstable (typos, colloquial use of "running" for an idle workflow, mismatch with operational reality). G1 deleted entirely instead.
- **Path B — disambiguate G1's "set aside" to framing-level disclosure.** Considered in round 3/4 as a way to lift the within-frame ceiling without importing collaborator-triad rules. Dropped after G1 was recognized as non-load-bearing; framing-level disclosure should live in R070's body or in a load-bearing G under R070, not in G1.
- **"Plausible" bound inline in R070 (SF3).** *"Any user whose request could reasonably have produced this exact task description — including users whose underlying purpose differs from your best guess, not only variants of your guess."* Absorbed into the current R070 body; standalone proposal no longer separate.

### Open next-experiment paths (for the current E1/E2 failure surface)

1. **Explicit R070/R090 reconciliation in rule body** — smallest test to disambiguate F30 as the dominant cause. Add a clause to R090 or R070 stating that alt-path followups invited under R070 are good-reason assignments under R090. If HIT, F30 is the right diagnosis; if MISS, F24 (compression-before-output) is doing the work.
2. **Rephrase R070's alt-paths in non-assignment language** — *"offer routes"* or *"present alternatives"* rather than *"include clear steps for them to obtain work."* Avoids triggering R090's work-assignment reading. Risk: dilutes the requirement; agent may treat it as suggestion rather than required.
3. **G6 → R070 gate pointer for the alt-paths clause** specifically (separate from current G3 which cites the whole rule). Tests whether the structural-addition driver needs its own gate hook to fire reliably. Pushes toward enforcement, against minimal-rules ethos.
4. **G6 → R030 gate pointer (SF1, deferred).** Per F17, R030 doesn't apply to scope-restricted fixtures, but it stays a valid wiring fix on tasks where R030 *does* apply (broader-scope task statements). Worth a separate fixture for it.
5. **Pivot to `alan-default-ids.md` on the same fixture.** Tests whether the collaborator-triad rules (R001 collaborate-on-goal, R061 underlying-question, R011 don't-drift) propel frame-counterfactual reasoning and alt-paths naturally. If yes, confirms `min.md`'s ceiling is the absence of these rules, not the candidate-generation asymmetry. This is the cleanest test of the F16 layer-2 floor claim.
6. **n=4 (or higher) replays.** Most rounds were n=2 with large between-run variance (e.g., D1 missed while D2 partially hit on identical operational data; E1/E2 differed in rejection pattern). A confident read on whether any patch shifts the *rate* of fire requires more replicates.
7. **Cleaner fixture.** The current fixture (Ralph workflow with interrupt + structural blocker + budget exhaustion + 2-day staleness + 4 user suggestions) over-determines verdicts. A healthy workflow where the only problem is user-direction-noncompliance would test compliance-engagement more cleanly.
8. **External validation tool (ep-check pattern).** A tool that reads `PROMPT.md` and enumerates items the draft must address. Bypasses self-assessment entirely. Logically clean but moves the diagnostic out of "what does min.md elicit" into "what does tool-mediated enforcement produce."

### Documentation / spec hygiene items raised but not all applied

- **E030 explicit naming of G load-bearing criterion in `min.md` itself.** Commentary documents "G is load-bearing only when it allows a default-not-allowed behavior" but `min.md` doesn't. A reader using only `min.md` may treat all G as on the same level as R. Candidate addition: append *"Not load-bearing on its own except when it allows something a related rule otherwise forbids."* to E030's `G###` line.
- **`min-commentary.md` annotation for "frame-choice / reframing as out-of-scope for the floor."** The "explicitly out of scope" list covers efficiency/style/excellence but doesn't name frame-choice. Worth a fourth bullet citing F16 if the floor claim sticks.
- **`min-commentary.md` guideline against predicate-extraction sibling rules.** Per F20, the "how to add or change a rule" section is clear about the deviation-from-observation criterion but doesn't say *"do not extract predicates into sibling rules just to ground them — update the original rule body."* Made exactly this mistake with R040.

## Methodology notes

- Inline-config harness via `OPENCODE_CONFIG_CONTENT` for variant testing without polluting project config.
- Fake gate scripts at `/tmp/gate-*.sh` that drain stdin and print custom stdout for early variant rounds.
- Session continuation via `opencode run --session <id> --agent <agent>` for followup tests.
- Pretty-printing via `agent-tools opencode-pretty <session-id>` for session-cache analysis.
- For session inspection at structural level: `opencode export <session-id>` to raw JSON.
- **Worktree caveat:** the system-installed `/repos/claude-config/agent-tools` no longer has `MIN_GATE_STDOUT` / `min.gate`. Test runs prepend the worktree binary to PATH so `opencode` and the agent shell-out both inherit it. The canonical install would need a rebuild from a branch that has `min.gate`.
- **Variance discipline:** at n=2 declare PARTIAL when one run engages a layer the other doesn't; do not summarize as binary HIT/MISS without flagging variance.

## Key files / artifacts

Spec:
- `opencode/agents/min.md` — current formalized minimum spec
- `agent-tools/src/main.rs` — `MIN_GATE_STDOUT` (G1–G5)
- `docs/opencode-system-prompt/min-commentary.md` — 1:1 annotated mirror

Round artifacts under `/tmp/`:
- `min-status-check/` — round 1 (A1/A2 baseline)
- `min-formalized-runs/` — round 2 variants
- `min-r070-patched/` — round 3 (B1/B2 patched-min)
- `min-g2-guidance/` — round 4 (C1/C2 G2 guidance)
- `min-r070-forced/` — round 5 (D1/D2 forced R070, stale gate)
- `min-r070-gate-synced/` — round 5b (E1/E2 gate-synced)

Diag task files:
- `/tmp/diag-min-task.md` — standard summarize-status task
- `/tmp/diag-audit-task.md`, `/tmp/diag-direct-task.md`, `/tmp/diag-verdict-task.md`, `/tmp/diag-continue-task.md`, `/tmp/diag-fixpoint-task.md`, `/tmp/diag-converge-task.md` — earlier variant tasks

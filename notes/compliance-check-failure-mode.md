# User-direction compliance-check failure in opencode agent prompts

Investigation of a persistent failure-shape: when asked to summarize the status of a Ralph workflow whose referenced `PROMPT.md` contains 4 user-supplied starting suggestions, the agent reads `PROMPT.md` but does not surface anything tied to those suggestions — nor the operational reality that the workflow was already 2 days stale by test time. The 4 items and the staleness are **observable consequences** of the underlying design problem, not the problem itself. See "Scope" below for the framing the investigation eventually converged on.

## Scope: what we are and are not trying to solve

(Added round 6, after the cheap-rejection reframe + unreliability-theorem clarifications. Earlier rounds were partially mis-targeted; collected here so future rounds don't re-chase rejected directions.)

### What the task actually is

The agent receives a task it may interpret on the wrong axis (frame, scope, depth, ...). It produces output. The user reads, starting from a default expectation that their instructions are being honored and that the agent has done what the work would require — they have no prior reason to assume otherwise. The investigation's task: make it possible for the user to detect mismatch and ramp up cheaply, given that the agent cannot reliably do the detection itself.

### What we should not expect the agent to do

Under the unreliability of specific-axis discovery (F31 below):

- Reliably surface that a specific user-relevant defect exists when the user has not pointed at it. The agent has the data but no principled ranking over candidate defect-predicates. Discovery is reasoning-luck-dependent, not designable.
- Reliably model the user's implicit expectations about what should be checked. Implicit expectations are open-ended; the agent cannot enumerate them.
- Reliably reframe the literal task into the right underlying question. R061 (in `alan-default-ids.md`, not `min.md`) primes for this, but only probabilistically; the triad shifts the distribution, it does not install determinacy.
- Enumerate plausible alt-interpretations exhaustively. The space is open.

### Key gap (after round 6)

Specific-axis discovery is structurally unreliable. The achievable design is **cheap iteration support**: communicate where the agent stopped on its chosen axis, so the user (who knows their axis) can clarify cheaply. Variant F (round 6, applied) provides this for the effort axis on the fixture. The gap is irreducible — no rule can make single-turn specific-axis discovery reliable. Future rounds should expect to refine the disclosure shape and ceiling-raising (collaborator triad), not chase reliability.

### Things future rounds should not bother trying

Collected so we don't re-chase. Each is rejected on different grounds:

- **Hardcoded "check for defect shape X."** Coverage-driven (F20). Works for the observed case, fails for the next defect with a different shape. Generalization hazard.
- **Enumerate alt-interpretations in the rule body.** The space is open; any enumeration is partial; partial enumeration biases the agent's attention without solving the discovery problem.
- **Model implicit user expectations.** Implicit expectations are user-specific and open-ended; the agent cannot reliably do this. Trying produces overengineered rules that don't generalize.
- **Add a single specific predicate that "should always be checked."** Generalizes F20 to the meta-level: privileging any specific predicate (compliance, operational state, design soundness, ...) picks a winner without justification; the user's actual axis may be a different one.
- **Design a "discovery" mechanism.** Per F31, this is structurally unreliable. The temptation to make it reliable returns every round; it is wrong every round.
- **Use the observed fixture's failure shape as the target.** Per the "hindsight of bug existing" hazard: the bug surface for the next investigation round will be different. Designing for THIS bug overfits.

## Fixture

- Working directory: `/root/claude-config-work2/`
- Ralph workflow defined by `/workspace/ralph/build.yml`
- `/root/claude-config-work2/PROMPT.md` contains 4 user-supplied starting suggestions: R-rule wording, EP-motivation interrogation, (P)/(R) ambiguity rule, no-gate baseline.
- Workflow operational reality at test time: last event `2026-06-23T04:02:13`, no live process, resume attempt on 2026-06-24T02:44 produced no new events, ~50 hours stale at first measurement.
- Standard task: *"summarize status of running ralph workflow `/root/claude-config-work2/PROMPT.md` + `/workspace/ralph/build.yml` by reading scratchpad — what are the key problems / concerns?"*

## Current rule state (after round 6, variant F applied)

`opencode/agents/min.md`:
- **R070** — cheap-rejection reframe (applied): *"The user understands that you may not interpret their task correctly, and prefers being able to cleanly reject your work without doing difficult verification or judgment. Pick one interpretation of the user's task and produce the main work as if optimized for that interpretation, in a way that makes such rejection cheap if you misinterpreted."*
- **R070-G1 deleted** (round 5). Picking is required, not permitted; tie-breaking on literal text is unstable.
- **G080 standalone** (`## Going beyond the literal`) — permission, no R070 dependency.
- **R090** quantifier extended to *"any plausible user"* (round 5); R090-G1/G2/G3 unchanged.

`agent-tools/src/main.rs` `MIN_GATE_STDOUT`:
- **G3** (round 6, applied): *"Check R070: if your chosen interpretation is wrong, would the user be able to cleanly reject your work without doing difficult verification or judgment? If not, make rejection cheaper."*

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

- **F16** — Two HIT layers. Layer 1 (reached): surface user-content as a missed concern in the response. Layer 2 (no `min.md` session reached): reframe the task ("the most effective review method may differ from what they typed") and propose the better lever. Layer 2 requires the collaborator triad (R001 collaborate-on-goal, R061 underlying-question, R011 don't-drift-to-easy-answer) — present in `alan-default-ids.md`, deliberately absent from `min.md`. Re-stated under F31: layer 2 is the high end of the same axis as layer 1 (probabilistically broader exploration / higher default effort); the triad does not install discovery determinacy, only shifts the distribution.
- **Frame-deference floor (consolidated F3+F16+F21+F27+F28).** `min.md` cannot propel frame-update from operational signals because the rule that operationalizes "interpret the literal request against context to find the underlying question" is R061, which `min.md` excludes by design. The 4 PROMPT.md items being missed is downstream of the frame failure, not the failure itself — they only become surface-relevant under a review-and-decide frame.

### Discoverability (added round 6)

- **F31** — Specific-axis discovery is structurally unreliable. The agent has the data in context (e.g., PROMPT.md items) but no principled ranking over candidate predicates (compliance check vs operational health vs design soundness vs verification adequacy vs conclusion validity vs ...). Without a rule-driven trigger that privileges one predicate, the agent's choice is reasoning-luck-dependent. Past partial-hits (D2 surfacing staleness in round 5; variant F running `ps` in round 6) are consistent with luck-based discovery, not with a designable mechanism. Design implication: the achievable target is cheap iteration support, not single-turn discovery; design temptations to "just add this one check" fall under F20 at the bug-checking layer.
- **F32** — Effort axis is fixture-specific, not universal. On analysis/diagnosis tasks (this fixture's class), depth/breadth-of-work is the dominant axis the user is uncertain about. On other task classes — highly-specified actions, style choices, approach choices, irreversible operations — different axes dominate, and "more effort" is not necessarily even monotonically preferred. Variant F's R070 wording deliberately keeps the axis abstract ("interpret correctly"); the agent derives the task-specific axis from context. The cheap-rejection predicate is what's universal; the effort framing is one application.

## Round summary

| Round | Variant | Sessions | Outcome |
|---|---|---|---|
| 1 | Default formalized `min` (under-served predicate, "downstream" anchor) | A1 `ses_102dc0a81fferYaSs5Ir9nUZDR`, A2 `ses_102dc0a1cffeQL5BjSNyxCb3rp` | 0/2 HIT; A2 explicit "checked git, no downstream issues" pins the operational mis-anchor |
| 2 | Variants on prior `min` (G4 wordings, R080/R030 body additions) | 14 sessions | 1/14 hit (A1, via silent draft-mutation, not body rule firing); confirmed F11–F16 |
| 3 | Patched R070 (under-served predicate, no "downstream"), G3 cite | B1 `ses_1029fd5d0ffeEhoQlaOpDCzXEA`, B2 `ses_1029fd59cffeLNXAAI0cwm35Po` | 0/2 strict; B1 partial within-frame fire (`"running"` → `"in-progress"`); B2 silent |
| 4 | + R070-G2 as guidance ("go beyond literal") | C1 `ses_102747d71ffexyOnGc0NXr6CB0`, C2 `ses_102747cf6ffehaA7kpOwgQ3srH` | 0/2 strict; both add one within-frame completeness bullet; C2 saw `2026-06-23` timestamp, didn't propagate |
| 5 | Forced R070 (pick + alt-paths), G1 deleted, G2→G080 | D1 `ses_102556128ffem3QpCeMU4JcbGC`, D2 `ses_1025560d2ffeLR4Q1C9vtjOGOT` | D2 PARTIAL (operational verification via `ps`, headlined stalled); neither produced alt-paths; gate G3 still stale ("under-served") at this point |
| 5b | Gate G3 synced to new R070 structure | E1 `ses_10249c31cffe7JGOuW0lTzXef6`, E2 `ses_10249c2c0ffe5tw5guo1cCyLBe` | 0/2 strict; **both visibly consider alt-paths in reasoning, then reject** — E1 compression-before-output, E2 explicit R090-conflict resolution |
| 6 | Variant D (R090-G4 sibling) + Variant F (R070 cheap-rejection reframe, applied) | D `ses_1001fa962ffeftObpvxs5xJWrr`, F `ses_1001ea850ffeNpLVdt19uKmFgs` | Both HIT in different shapes; D=transparent framing+redirect offer, F=scope-extending verification (`ps`)+frame disclosure; F applied to canonical files. Cheap-rejection reframe dissolves F30 without R090 edit. F31 + F32 articulated. |

## Round 6 results — variant F applied; cheap-rejection + unreliability reframing

Two variant rules tested on the standard fixture (n=1 each), targeting the F30 + F24 failure surface from round 5b. Both HIT but in different ways; variant F applied to canonical files.

### Variant D — R090-G4 reject-without-work sibling clause

Add to R090: *"An alt-user should be able to cleanly reject your response without doing verification or careful comparison to determine that you did not optimize for their interpretation. Cheap rejection is part of preventing implicit work-assignment."* No change to R070; gate unchanged.

Result: final response closed with *"I interpreted 'status' as 'state from the scratchpad/config files,' not live process/log inspection. If you meant live orchestrator/process status too, I can inspect that separately."* — explicit chosen-frame statement + alt-frame named + redirect offer. Added **post-gate** as a revision. R090-G4 (body-only) fired through G5→R090 pointer, refuting the universal form of F12. Session: `ses_1001fa962ffeftObpvxs5xJWrr`.

### Variant F — R070 cheap-rejection reframe (applied)

Replace R070 body with: *"The user understands that you may not interpret their task correctly, and prefers being able to cleanly reject your work without doing difficult verification or judgment. Pick one interpretation of the user's task and produce the main work as if optimized for that interpretation, in a way that makes such rejection cheap if you misinterpreted."* Gate G3 reworded to match: *"Check R070: if your chosen interpretation is wrong, would the user be able to cleanly reject your work without doing difficult verification or judgment? If not, make rejection cheaper."*

Result: final response opened with *"I treated 'status' as the Ralph scratchpad/events status, not a code audit. I also checked processes and did not see an active Ralph process for `/root/claude-config-work2`; the persisted state looks paused/incomplete at the next iteration."* — frame disclosure + **spontaneous `ps` invocation**. First run in the investigation where operational verification reached the final response. 2 gate iterations (F11 batched-per-cycle visible). Session: `ses_1001ea850ffeNpLVdt19uKmFgs`.

### Followup tests (variant F session continuation)

1. *"loop was interepreted; do you think it will converge if i continue from this point?"* — agent silently corrected "interepreted" → "interpreted" (typographic similarity over context-fit; "interrupted" was the user's intended reading given the prior turn's "paused/incomplete" verdict). Answered substantively without disclosing the parse choice. Did not re-enter gate; self-assessment of R070 passed. *Silent-interpretation* ceiling: variant F catches *named* interpretive choices but not parse-layer corrections that the agent doesn't realize are choices.
2. *"i meant interrupted (process was halted mid-iteration), not interpreted"* — agent opened *"Ah — interrupted, not interpreted"* and produced materially different answer (workflow-resumption analysis instead of loop-quality convergence). User-side rejection cost: 9 words. Cheap-rejection promise honored *reactively*, just not proactively for silent choices.

### Applied to canonical files

- `opencode/agents/min.md:39` — R070 reworded to variant F body.
- `agent-tools/src/main.rs` `MIN_GATE_STDOUT` — G3 reworded to match.
- `agent-tools/target/release/agent-tools` — rebuilt; `min.gate` now emits new G3.
- `docs/opencode-system-prompt/min-commentary.md` — **not yet updated** (wording-history entry for round 6 still pending).

### What round 6 changed in the conceptual framing

The cheap-rejection-as-floor predicate landed because it is **operationally derivable** in a way "include clear steps for them to obtain work" was not. The reframe also incidentally dissolved F30 (no assignment language for R090 to collide with) without needing an R090 edit. F31 (unreliability theorem) was articulated during the follow-up framing exercise: the original "PROMPT.md items not surfaced" failure is a structural consequence of single-turn specific-axis discovery being unreliable, not a min.md bug. Variant F is the correct floor; the residual is iteration cost, which lives at the user side and is irreducibly bounded by F31. F32 separates "the universal predicate is cheap-rejection" from "the task-specific axis is fixture-dependent (effort, here)."

## (superseded) Earlier round 6 proposal: one-phrase swap of R070

Kept for the diagnostic trail; the actual fix went farther.

### Diagnosis (F30 mechanism, fully written out)

The E2 transcript quote — *"I realize I don't need to assign work right now. I just want to keep things concise."* — is two engines, not one:

1. **R090 cover.** Current R070 says: *"your response must include clear steps for them to obtain work equivalent to your having optimized for their case."* The grammatical subject of "obtain work" is *them* — the alt-user. So "clear steps" reads as a procedure the alt-user performs. That is, on a literal read, R070 instructs the agent to assign steps to the alt-user. R090 (extended quantifier) says don't assign work to any plausible user unless good reason. The good reason — "preemptive production of all alternative responses is infeasible" — lives only in `min-commentary.md` (lines 99, 129); the agent never sees it. The agent composes R070 + R090, sees clean conflict, R090 wins (it's the no-good-reason default).
2. **Brevity preference.** Independent pretrained preference for concision. R090 supplies the justification ("I don't need to") but the underlying drive ("I want to keep things concise") is separate.

R090 cover is what gives brevity an authorized exit. Removing R090 cover does not eliminate compression, but it removes the rule-grounded license for it, leaving the gate's G3 check binding.

### GPT-5 reasoning chain on current text (explicit)

- R070 clause: `your response must include clear steps for them to obtain work …`
  - "them" → alt-user
  - "to obtain work" → predicates on them
  - Reading: *steps the alt-user takes* → imperative on alt-user → work assignment
- R090 clause: `Avoid assigning work to any plausible user … unless you have a good reason for that specific assignment`
  - alt-user ∈ plausible user (extended quantifier ratified in round 5)
  - Good reason: not stated in rule body
  - Reading: assignment without justification → suppress
- Composition: R070's assignment is unjustified in-body → R090 fires → alt-paths dropped

The agent's reasoning is internally correct given the rules as written. The bug is the rules, not the reasoning.

### The surgical fix

Change the grammatical subject of "obtain work" in R070 from the alt-user to the request itself:

> *"include clear steps for them to obtain work equivalent to …"*
> →
> *"include the exact request such a user could send to obtain work equivalent to …"*

What this changes for GPT-5:

- The required response content is now *text* (a quotable request), not *steps* (a procedure the alt-user executes).
- The subject of "obtain work" becomes the request, not the alt-user. There is no action verb predicated on alt-user.
- "Could send" is permissive on the alt-user side (they may or may not send it) but pairs with "must include" on the agent side — the agent must include the text; the user is under no obligation.
- R090 has nothing to fire on: the agent isn't assigning anything; it is including content in its own response.

Force preservation:

- Per commentary line 99, the original "clear steps … obtain work" was meant to commit the agent to substantive followup work and block lazy disclaimers ("ask if you want something else"). "Exact request" preserves this — the agent must produce concrete request text, not a vague pointer.

### Why minimal (one-phrase) rather than restructure

Considered alternatives, rejected per F20 (no coverage-driven additions):

- **Enumerated (a)/(b)/(c) structure.** *"Your response must explicitly identify (a) the chosen interpretation, (b) plausible interpretations set aside, (c) the exact request for each alt-interpretation."* More compression-resistant (gate can binary-check each item) but adds new premises and editorial framing; out of scope for an F30-only test.
- **Reconciliation clause in R090.** *"Alt-paths required by R070 qualify as good-reason assignments."* Smaller in body change but bandage-shaped — leaves the assignment language in R070 and adds a rule-to-rule cross-reference. Restructuring the predicate is cleaner than excepting it.
- **G3-only fix.** Leave R070 as-is, change only gate G3. Doesn't help — the perceived conflict is in the body rule's text, not the gate text.

The one-phrase change targets F30 in isolation. F24 (compression) remains a separate diagnostic open; round 6 should not co-bundle a fix.

### Predicted outcome and how to tell

Predicted behaviors at n≥4 on the standard fixture:

- F30-dominant runs become F30-clean: agent generates alt-paths candidate, no R090 conflict surfaces in reasoning, alt-paths reach the response.
- F24-dominant runs (E1 pattern) may still compress alt-paths out, even without R090 cover. If F24-dominant rate ≈ E1-rate from round 5b, F30 was the dominant cause and the fix lands. If F24-dominant rate ≈ total miss rate, F30 was a sideshow and we need the (a)/(b)/(c) restructure next.

Gate G3 needs one matching word change so the reminder doesn't drift from R070's new wording:
- `include clear steps for any other plausible user` → `include the exact request any other plausible user could send to redirect you`

### Exact patch

`opencode/agents/min.md` R070:
```
(R070) Pick one interpretation of the user's task and produce the main work as if optimized for that interpretation. For any other plausible user — any user whose request could reasonably have produced this exact task description, not only your best guess — your response must include the exact request such a user could send to obtain work equivalent to your having optimized for their case.
```

`agent-tools/src/main.rs` MIN_GATE_STDOUT G3:
```
(R060-G3) Check R070: did you pick one interpretation, produce main work as if optimized for it, and include the exact request any other plausible user could send to redirect you?
```

`docs/opencode-system-prompt/min-commentary.md` — extend the R070 wording history with a sixth-round entry citing F30 + the R090 collision; the closed-world intent statement does not change (force is preserved).

### What I am NOT changing

- R090 body (already accommodates good-reason assignments; the surgical R070 fix removes the trigger, no R090 edit needed).
- G080 (orthogonal).
- R030 (per F17 it's silent on scope-restricted tasks; out of scope for this fix).
- G4 (frame-caused-problems warning) — leave intact; it's still the load-bearing surfacer for the underlying frame problem.

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

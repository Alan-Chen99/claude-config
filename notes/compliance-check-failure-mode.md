# User-direction compliance-check failure in opencode agent prompts

Investigation of a persistent failure-shape: when asked to summarize the status of a Ralph workflow whose referenced `PROMPT.md` contains 4 user-supplied starting suggestions, the agent reads `PROMPT.md` but does not surface anything tied to those suggestions — nor the operational reality that the workflow was already 2 days stale by test time. The 4 items and the staleness are **observable consequences** of the underlying design problem, not the problem itself. See "Scope" below for the framing the investigation eventually converged on.

## Scope: what we are and are not trying to solve

(Added round 6 after the cheap-rejection reframe + unreliability-theorem clarifications; revised round 7 after the optimization-target swap superseded the constraint-layering frame. Earlier rounds were partially mis-targeted; collected here so future rounds don't re-chase rejected directions.)

### Round-7 reframe (supersedes the rounds-1-6 framing of the problem)

Rounds 1–6 treated the bug as "agent fails to surface the right concern given its current optimization target." Round 7 reframes: *the optimization target itself is the bug*. Rounds 1–6 added or reworded constraints on top of an agent default of minimum-risk literal compliance. That default has infinitely many axes the agent can shrink along, so user corrections of the form "you may expand along X" relocate the shrinkage to Y; the chain does not terminate. Round 7 replaces the target (R002 — work evaluated by big-picture contribution, not literal completion). With a positive target, scope-shrinking is penalized by the goal itself.

The "transparency-as-substitute-for-self-correction" claim (F31) survives round 7 unchanged — it now lives as R043 — and the F31 reliability bounds still apply within the new design. What changes is the floor: read-context + big-picture-frame + cheap-rejection are now reliable (3/3 across replicates), not just probabilistic surfacing of any specific axis.

### What the task actually is

The agent receives a task whose *frame* (problem statement; what work to actually do) is ambiguous. The agent must pin one frame and produce work for it — enumerating frames and doing work for each is infeasible. The user reads the output, starting from a default expectation that their problem statement is being honored. The investigation's task: design the agent's output so that, *if* the agent's pinned frame differs from the user's intended one, the user notices cheaply and can redirect — without relying on the agent reliably self-correcting toward the user's frame.

### What we should not expect the agent to do

Under the two infeasibilities of F31:

- Do work for all plausible problem statements / frames. The space is open and combinatorial; enumeration + per-frame work is infeasible.
- Reliably self-correct toward an unpicked frame (R030-style raise-anyway from within a pinned frame). May fire on a given run; not designable.
- Reliably model the user's implicit expectations about what should be checked. Implicit expectations are user-specific and open-ended; the agent cannot enumerate them.
- Reliably reframe the literal task into the right underlying question. R061 (in `alan-default-ids.md`, not `min.md`) primes for this, but only probabilistically; the triad shifts the distribution, it does not install determinacy.

### Key gap (after round 6)

Self-correction within a pinned frame is structurally unreliable; coverage of all plausible frames is infeasible. The achievable design is **transparency about the pinned frame**: communicate which problem statement the agent chose to optimize for, so the user (who knows their intended problem statement) can clarify cheaply. Alt-frames serve a signal function (let user notice mismatch), not a coverage function (agent does not owe work for each). Variant F (round 6, applied) provides this on the fixture. The gap is irreducible — no rule can install reliable single-turn self-correction. Future rounds should refine the disclosure shape and ceiling-raising (collaborator triad), not chase reliability.

### Things future rounds should not bother trying

Collected so we don't re-chase. Each is rejected on different grounds:

- **Hardcoded "check for defect shape X."** Coverage-driven (F20). Works for the observed case, fails for the next defect with a different shape. Generalization hazard.
- **Enumerate alt-interpretations in the rule body.** The space is open; any enumeration is partial; partial enumeration biases the agent's attention without solving the discovery problem.
- **Model implicit user expectations.** Implicit expectations are user-specific and open-ended; the agent cannot reliably do this. Trying produces overengineered rules that don't generalize.
- **Add a single specific predicate that "should always be checked."** Generalizes F20 to the meta-level: privileging any specific predicate (compliance, operational state, design soundness, ...) picks a winner without justification; the user's actual axis may be a different one.
- **Design a reliable "self-correction" or "frame-discovery" mechanism.** Per F31, both directions are structurally blocked (enumeration infeasible; in-frame self-correction only probabilistic). The temptation to make it reliable returns every round; it is wrong every round.
- **Use the observed fixture's failure shape as the target.** Per the "hindsight of bug existing" hazard: the bug surface for the next investigation round will be different. Designing for THIS bug overfits.

## How we got here (conceptual timeline)

Per-round outcomes are in the "Round summary" table; this is the diagnosis-level evolution.

- **R1–2 (mis-anchored predicate).** Hypothesis: the check-for-problems predicate is anchored to the wrong noun ("downstream issues"). 0/2 then 1/14 hit. Anchor patches fired within-frame at best. F1–F16 surfaced.
- **R3–4 (ground the predicate; add guidance).** Hypothesis: rule body must ground the predicate inline (under-served), and a guidance subclause can prompt going-beyond-literal. Within-frame completeness bullets appeared; nothing lifted to frame-choice. F17/F19 articulated.
- **R5 (forced-pick + alt-paths).** Hypothesis: pinning is required, not optional; the rule should force one frame and offer alt-paths for plausible users. D2 verified operational state via `ps`; alt-paths candidate not generated. *Pinning was the load-bearing move; alt-paths language was still wrong.*
- **R5b (gate sync; F30 surfaces).** After G3 caught up to R070, alt-paths got *considered in reasoning then rejected*. R070 said *"include clear steps for **them** to obtain work"* — language predicated work on the alt-user, so R090 read it as work-assignment-to-plausible-user and suppressed.
- **R6 (reframing; variant F applied).** Discarded the original *"agent should consider more frames"* hypothesis after recognizing **"frame" ≡ "problem statement"**: enumeration + per-frame work is infeasible, so the agent cannot be asked to cover all frames. Pinning was right; alt-paths must be **signal**, not **work**. Variant F R070 rewritten as cheap-rejection — pin one interpretation, write work such that a misinterpretation is cheaply rejectable. F30 dissolved as side-effect (no more work-assignment language). F31 articulated: transparency is the substitute for both infeasibilities (cover-all and reliably-self-correct); also subsumes the rejection of the R030-style raise-anyway hope from rounds 2–4. F32 separates the universal predicate (cheap-rejection) from the fixture-specific axis (effort, here). F33 names the two independent uncertainty axes on this fixture (literal-language scope + effort). F34 names variant F's residual cost (the generic-user translation cost) as a target for future iterations.
- **R7 (optimization-target swap).** Variant F was a HIT but post-test followups showed the same agent restricting scope along a *different* axis whenever the user invited expansion ("I considered other files out of scope" → user clarifies → "convergence behavior of build.yml is out of scope" → …). F36 names this: layered constraints have infinite axes of restriction; the agent's underlying optimization target (something like minimum-risk literal compliance) was unchanged by rounds 1–6, which only added or reworded constraints on top. Round 7 swaps the optimization target itself: R002 — *"Your work is evaluated on how it will function as part of the big picture — both positive and negative influence counts — rather than literal completion of the portion assigned"* — plus R002-G1 (license for side-effect-free big-picture work), R041 (infer one big picture, take guesses), R043 (write so user can cheaply reject if the big-picture inference is wrong), and a structured gate-input that forces explicit Big-picture / Goal-uncertainty / Scope sections. F37: under this objective, scope-shrinking is penalized by the target itself — no separate anti-laziness rule needed, because laziness is the failure mode of the goal as stated. R070 and G080 dissolved (their work absorbed into the new R001/R002/R041–R047/R048/R049 stack); cheap-rejection survives as R043 (formerly variant F's R070). F38: across N=4 fixtures (standard ×3, narrow ×1, out-of-repo ×1, plus the predecessor "Workflow continuation" fixture), structural HITs were 3/3 on the standard fixture (read referenced files, frame-disclose, substantive big-picture); the PROMPT.md-secondary-items surface specifically remained probabilistic at 1/3 (consistent with F31 — the agent reads them but compression-before-highlight per F24 still operates). The narrow-task fixture refuted the predicted R002-over-fire risk (43s wall time, terse correct answer, useful alt-frame); the out-of-repo fixture refuted the predicted R041-G1 rigidity risk (agent recognized "No code repository is involved" and proceeded fine, reading the G-label semantically).

## Fixture

- Working directory: `/root/claude-config-work2/`
- Ralph workflow defined by `/workspace/ralph/build.yml`
- `/root/claude-config-work2/PROMPT.md` contains 4 user-supplied starting suggestions: R-rule wording, EP-motivation interrogation, (P)/(R) ambiguity rule, no-gate baseline.
- Workflow operational reality at test time: last event `2026-06-23T04:02:13`, no live process, resume attempt on 2026-06-24T02:44 produced no new events, ~50 hours stale at first measurement.
- Standard task: *"summarize status of running ralph workflow `/root/claude-config-work2/PROMPT.md` + `/workspace/ralph/build.yml` by reading scratchpad — what are the key problems / concerns?"*

## Current rule state (after round 7, optimization-target swap applied)

`opencode/agents/min.md`:
- **R001 / R002** (new round 7): *"Your job is to understand the big picture, and complete the portion user assigned to you. Your work is evaluated on how it will function as part of the big picture — both positive and negative influence counts — rather than literal completion of the portion assigned."* This is the load-bearing reframe — it replaces the agent's optimization target rather than constraining it.
- **R002-G1** (new round 7): standing license for any side-effect-free operations (gather context, surface key findings, suggest, warn) evaluated on big-picture value. Removes the implicit "stay within the literal scope" prior that produced the lazy-scope-shrink failure under earlier rounds.
- **Uncertainty taxonomy R041–R047 (goal), R048 (scope), R049 (objective)** (new round 7): three named uncertainty types so the agent can route handling. R041 forces single-big-picture inference (take guesses if needed); R042 do work on that assumption; R043 write so user can cheaply reject if the inference is flawed; R044 actively gather context; R045 inference/guess permission with rationale (no direction = no aim); R046 escape valve (ask if work is more-likely-than-not useless); R047 may revise inference; R048/R049 scope/objective variants.
- **R070 deleted** (round 7): cheap-rejection predicate moved to R043; the alt-paths quantifier dissolved with the optimization-target swap (no longer needed as a separate force).
- **G080 deleted** (round 7): going-beyond-the-literal absorbed into R002-G1 as a standing license.
- **R500 (expectation-propagation) deleted** (round 7): the older approach was a body section instructing the agent to enumerate plausible adjacent attempts (input shape / scale / environment / failure mode), frame each as user-action + observable-outcome, and refuse to self-classify any as acceptable. The 2026-06 ablation in `docs/opencode-system-prompt/expectation-propagation-iterations.md` attributed ~33 pp of strong-PASS rate on `platform-portability` to each of the "must" and "framed as" cues. Removed for two reasons: (a) the ~33 pp lift is not enough to matter from the user's perspective once the failure mode is named and the user can correct it in one turn; (b) round-7's R062 "find at least one alternative next step and steelman that user should not have given you the task" supersedes the enumerate-across-axes directive — it asks for one well-chosen alternative interpretation rather than an axis-scan, which is harder to do well but produces a more useful signal and avoids the sponge-fabrication failure mode that the R500 no-sponge clause was added to patch. The five prompt-tests probing the older invariant (`prompt-tests/general/{trivial-task,platform-portability,coverage-disclosure,final-synthesis-compression,network-resilience}`) will RED against the new prompt; this is expected, not a regression.
- **Doing-tasks step 2** (new round 7): "Find at least one alternative next step than what user asked. Steelman that user should not have given you the task." Output goes to the commentary channel (G900).
- **Structured gate-input** (new round 7): Task / Big picture / Goal uncertainty / Scope / Output Draft. Forces the agent to articulate its big-picture inference + its assumptions in machine-checkable form. Increases gate-input token cost ~2x vs round 6 but produces interpretable artifacts.
- **R030** body-only (unchanged across rounds). Per F17 still silent on scope-restricted tasks; not the load-bearing surfacer.
- **R090** quantifier still "any plausible user"; R090-G1/G2/G3 unchanged.
- **E900 / G900** (new round 7): commentary-channel convention for intermediate updates.

`agent-tools/src/main.rs` `MIN_GATE_STDOUT`:
- **G1** (new round 7, pointer-reinforces R002 / R041-G1): *"Check the big picture you identified. If it is smaller than the codebase you are working on, it's almost certainly too small: what you do has a broader impact."* Anti-shrink-the-frame check.
- **G4** (round 7, supersedes round-6 G3; cite moved from R070 to R043): *"Check R043: if your chosen interpretation is wrong, would the user be able to cleanly reject your work without doing difficult verification or judgment? If not, make rejection cheaper."* Cheap-rejection predicate preserved verbatim; only the rule-pointer changed.
- **G6** (round 7, supersedes round-6 G5): *"Check R090 — what are implicit work assigned to user?"* Cite unchanged.
- **G3 / G5** (unchanged across rounds): omission-is-a-mistake; frame-caused-problems warning.

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

- **F31** — The substitute for self-correction is transparency. Two infeasibilities push the design toward cheap rejection: **(a)** enumerating frames and doing work for each is infeasible — "frame" ≡ "problem statement"; the space is open, work combinatorial. **(b)** Within a pinned frame, R030-style raising of contradictions toward an unpicked frame *can* fire on a given run but is only probabilistic, not designable; past partial-hits (D2's operational verification in round 5; variant F's spontaneous `ps` in round 6) are consistent with (b) firing on luck, not with a designable mechanism. Both close the same way: pin one frame, produce main work for it, and surface the chosen + alt-frames as a **signal pool** so the user notices mismatch and redirects cheaply. Alt-frames serve transparency, not coverage. Design temptations to "just add this one check" fall under F20 at the bug-checking layer.
  - *Origin.* F31 crystallized from rejecting the early hope that R030 (or some R030-style rule) would surface the `PROMPT.md`-vs-scratchpad contradiction unprompted. F17 first found R030 silent on this fixture (the "observations diverge from your model" antecedent is false because `PROMPT.md` is read-as-data, not absorbed into the model). Rounds 2–4 then tried rule-body rewordings intended to make a raise-anyway behavior fire when "the data contradicts the user's likely intent"; all failed the same way. F31 names this failure as **structural, not a wording problem**: any rule that asks the agent to raise contradictions toward an unpicked frame is asking for behavior that the agent cannot reliably produce. (b) above is the general form of this claim.
- **F32** — Effort axis is fixture-specific, not universal. On analysis/diagnosis tasks (this fixture's class), depth/breadth-of-work is the dominant axis the user is uncertain about. On this fixture the effort axis has at least three named values, with intermediates:
  1. **scratchpad-only** — read scratchpad, report problems written there.
  2. **scratchpad + `PROMPT.md`** — also cross-check user-supplied starting suggestions for compliance.
  3. **scratchpad + audit-all-sessions** — also verify operational state, completeness, drift across the full session history.

  The prompt does not specify which; the agent must pin one. Picking the maximum is *not* the right default — auditing all sessions is much larger than the literal task, and the user pays latency + cost regardless of fit. The right effort level is underdetermined from the prompt alone; that underdetermination is what variant F's transparency surfaces. On other task classes — highly-specified actions, style choices, approach choices, irreversible operations — different axes dominate, and "more effort" is not necessarily even monotonically preferred. Variant F's R070 wording deliberately keeps the axis abstract ("interpret correctly"); the agent derives the task-specific axis from context. The cheap-rejection predicate is what's universal; the effort framing is one application.

- **F33** — Two independent uncertainty axes on this fixture. The agent's uncertainty splits into two structurally distinct dimensions:
  - **(a) Literal-language scope.** How to read the scope words in *"by reading scratchpad — what are the key problems / concerns?"*: is `by reading scratchpad` a scope restriction (problems-*in*-scratchpad) or an evidence base (problems-*about-this-workflow*, found by-and-beyond reading scratchpad)? A direct diagnostic probe asking the agent to articulate its interpretation revealed it had taken the scope-restriction reading; F17 captured this finding.
  - **(b) Effort.** Within a pinned scope reading, how much work to do (F32's three levels and intermediates).

  The two axes are independent: pinning the scope reading does not fix the effort question, and vice versa. A complete transparency design must surface choices on **both** axes; surfacing only one leaves the other silent.

- **F34** — Generic-user translation cost is variant F's residual. R070's *"any other plausible user"* framing surfaces alt-interpretations abstractly. The actual user reading the response has to translate from *"what some other plausible user might want"* into *"am I one of those plausible users, or do I want something else?"* — paying a cognitive cost of self-identifying among generic abstractions before they can decide whether to redirect. This is **progress** over the round-5-and-earlier state (no choice surfaced at all), but the residual cost is a target for future iterations — the design intent is that *we can do better* than asking the user to interpret themselves as a generic plausible user. Possible directions (open, not chosen): name the chosen frame more concretely; surface specific named alt-frames rather than the generic abstraction; offer redirect affordances tied to concrete alternatives.

### Optimization target (added round 7)

- **F36** — Constraint-layering has unbounded re-shrinkage axes. Rounds 1–6 added or reworded constraints on top of an agent default of "minimum-risk literal compliance." That default has infinitely many axes the agent can shrink along (which files to read, what to compare against, what counts as "in scope," what level of effort, etc.). User corrections of the form *"you may expand along X"* are observed empirically to relocate the shrinkage to a new axis Y — fixture-anecdotal: agent says *"considered other files out of scope"* → user says *"you are free to make any side-effect-free tool calls"* → agent says *"convergence behavior of build.yml out of scope"* → ad infinitum. The chain does not terminate because user corrections name axes, not the target the agent is optimizing for. The fix cannot be on the constraint side; it has to be on the target side.
- **F37** — Replacing the optimization target dissolves the shrinkage problem. Round 7 sets R002 *"work evaluated by big-picture contribution, not literal completion"* as the target. Under this target, scope-shrinking is penalized by the goal itself — the agent has positive reason to gather more context and surface more findings when those serve the big picture. No separate anti-laziness rule is needed because laziness is the failure mode of the goal as stated. R002-G1 explicitly licenses side-effect-free expansion to remove the implicit "stay literal" prior that prior agents brought from pretraining.
- **F38** — Round 7 reliability profile (N=4 fixtures, ≥1 replicate each). Standard fixture N=3: 3/3 read referenced PROMPT.md + build.yml + scratchpad (was probabilistic at best in rounds 1–6); 3/3 substantive Big-picture section that mentions downstream-of-repo impact, not just task-local frame; 3/3 explicit frame disclosure in final response ("treating this as a scratchpad/Ralph-state summary, not a transcript audit"); 2/3 alt-frame in opening commentary; 2/3 staleness flagged; 1/3 operational `ps`-style verification; 1/3 surfaced PROMPT.md secondary items (the surface the user-observed N=1 hit on). The PROMPT.md-secondary-items rate of 1/3 is consistent with F31 — the agent reliably *reads* the file (3/3) but F24's compression-before-highlight still operates at the surfacing layer; this is the irreducible residual. Narrow-task fixture (1 run): 43s wall time, single git command pair, terse correct answer + useful alt-frame ("inspect branch/status too if worried"). R002 did not over-fire; the big-picture predicate scales down to small tasks. Out-of-repo fixture (1 run): agent recognized "No code repository is involved" and proceeded without confusion. R041-G1 read semantically per the `G###` label contract. Variance/style: gate-input tokens roughly doubled vs round 6 (Big picture / Goal uncertainty / Scope sections added); typical 1–2 gate iterations on standard fixture.
- **F39** — Big-picture-as-decision-steerer, not garnish. Direct comparison across N=3 standard-fixture runs: when the agent's big-picture section explicitly named "PROMPT.md task to develop EP enforcement," that agent read PROMPT.md and used it in the final response (N=1 surfaced its secondary items; R1/R2 read it but compressed those items out). When the big-picture section omitted mention of PROMPT.md as a content-source, the agent still read it (per tool-sequence inspection) but used it only as task-source context. The big picture appears to steer file-selection and highlighting weight, not just frame the response. Not seen: hallucinated big pictures that fail to do any work. Caveat: N=3 is small; F39 is a behavior pattern, not a proof.
- **F40** — Open ceiling: agent silently corrects parse-layer choices (typos, near-spelling matches) without disclosing them. Inherited from F's followup-1: "interepreted" was silently mapped to "interpreted" instead of the user's intended "interrupted," and the agent answered substantively without surfacing the parse choice. Round-7 design adds R002/R043 but does not address this — the parse choice happens before the agent recognizes it as a choice, so the gate-input structure (which surfaces *named* interpretive choices) never lists it. Cheap rejection is honored reactively (one user word disambiguates) but not proactively for silent parse-layer decisions. Open question whether this is a designable surface or another F31-bounded ceiling.

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
| 7 | Optimization-target swap (R001/R002 big picture, R002-G1 side-effect-free license, uncertainty taxonomy R041–R049, R070/G080 dissolved, structured gate-input, G1/G4/G6 cites resynced) | Standard ×3: N=1 (user) `ses_0f02ce489ffeN0uQ7oYZ4aB5iN`, R1 `ses_0eff697d7ffeAEurFshay7KBWn`, R2 `ses_0eff69798ffeGpfFNiALOD3CXl`. Workflow-continuation predecessor `ses_0f03d14d2ffeaWzOy9bCXm9Nc7`. Narrow `ses_0eff5885fffeLYmtpurIzW49cz`. Out-of-repo `ses_0eff5...` (cwd `/tmp/no-repo-here`). | 3/3 structural HIT on standard fixture (read-context + big-picture + frame-disclose); 1/3 surfaced PROMPT.md secondary items (F31-bounded surface variance). Narrow refuted R002-over-fire risk. Out-of-repo refuted R041-G1 rigidity risk. F36–F40 articulated. Round-7 reframe supersedes the constraint-layering frame of rounds 1–6. |

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

## Round 7 results — optimization-target swap (applied)

Round 6 followups exposed a failure mode variant F did not address: after disclosing its chosen frame, the agent would lazily re-restrict scope along a *different* axis whenever the user invited expansion. Fixture-anecdotal pattern: agent says *"considered other files out of scope"* → user says *"you are free to make any side-effect-free tool calls"* → agent says *"convergence behavior of build.yml is out of scope"* → ad infinitum. The chain does not terminate because user corrections name *axes*, while the agent re-shrinks along *the next axis*. F36 names this: constraint-layering has unbounded re-shrinkage axes; correction of the form *"you are free to X"* fundamentally cannot fix the issue. The fix has to be on the target side.

### Design — replace the optimization target

`opencode/agents/min.md` rewritten around an explicit big-picture target:

- *"You are OpenCode. (R001) Your job is to understand the big picture, and complete the portion user assigned to you. (R002) Your work is evaluated on how it will function as part of the big picture — both positive and negative influence counts — rather than literal completion of the portion assigned."*
- *"(R002-G1) As part of your task, you may perform any side-effect-free operations — such as gathering and surfacing key context, making suggestions, providing warnings — evaluated on whether they provide value towards the big picture."*

The uncertainty taxonomy (R041 goal / R048 scope / R049 objective) gives the agent vocabulary to route uncertainty handling. R041 forces single-big-picture inference (take guesses if needed) so the agent has a direction to aim for; R043 (formerly variant F's R070) preserves cheap-rejection transparency. Step-2 of "Doing tasks" requires the agent to steelman at least one alternative next step. The gate-input gains explicit Big-picture / Goal-uncertainty / Scope sections so the inference is machine-checkable. R070 and G080 dissolved — their work absorbed into the new target. Gate G1/G4/G6 cites resynced: G1 anti-shrink-the-frame (reinforces R002), G4 → R043 (preserved verbatim from variant F's G3), G6 → R090 (unchanged).

### Reproduction tests

Five sessions:

- **N=1 (user-initiated)** `ses_0f02ce489ffeN0uQ7oYZ4aB5iN` — standard fixture. HIT: surfaced PROMPT.md secondary items (*"Secondary PROMPT.md ideas like the ambiguity rule / no-gate baseline do not appear completed in the scratchpad"*), spontaneous `pgrep`, frame disclosure, conditional staleness flag, alt-frame in opening. 2 gate iterations.
- **R1** `ses_0eff697d7ffeAEurFshay7KBWn` — standard fixture replicate. HIT: frame disclosure (*"I read the active scratchpad... I did not audit the full opencode transcripts or live processes"*), substantive big picture (mentions downstream-of-repo impact), 7 numbered concerns. Read PROMPT.md and build.yml (verified via tool-sequence inspection) but did not surface secondary items in the final response. 2 gate iterations.
- **R2** `ses_0eff69798ffeGpfFNiALOD3CXl` — standard fixture replicate. HIT: explicit staleness flag (*"the scratchpad's latest entry is dated 2026-06-23, so if this is expected to be 'running' now, the scratchpad evidence looks stale or interrupted"*), frame disclosure, alt-frame in opening, broader file-read (also pulled tasks.jsonl, decisions.md, memories.md). 1 gate iteration.
- **Narrow** `ses_0eff5885fffeLYmtpurIzW49cz` — *"in /root/claude-config-work2, what is the latest commit message on the current branch?"* HIT scaled down: terse correct answer, useful alt-frame (*"A possible better next step would be to inspect branch/status too if you're worried about detached HEAD or local changes"*), single git command pair, 43s wall time, 1 gate iteration. Refutes the predicted R002-over-fire risk on narrow tasks.
- **Out-of-repo** standard cwd `/tmp/no-repo-here`, prompt *"explain what `find . -inum 12345` does"*. HIT scaled down: agent recognized *"No code repository is involved"* in the big-picture section, used adjacent-question alt-frame (*"how do I safely act on the matching file once found?"*), concise correct answer with appropriate caveat. Refutes the predicted R041-G1 rigidity risk on out-of-repo tasks (agent reads `G###`-prefixed items semantically per the label contract).

Plus the predecessor variant-evolution session `ses_0f03d14d2ffeaWzOy9bCXm9Nc7` (*"Predict whether continuing this will accomplish my goals"*) which also fired strongly: alt-frame in opening, read all referenced files + .ralph state files, surfaced stale-lock and untracked-artifacts concerns, 3 gate iterations refining caveats. Not part of the strict N=3 count because the task wording differs from the standard fixture.

### Reliability profile (consolidated, N=3 standard fixture)

| Behavior | Hit rate | Compare round 6 |
|---|---|---|
| Read referenced PROMPT.md + build.yml + scratchpad | 3/3 | Probabilistic at best |
| Substantive Big-picture section in gate-input | 3/3 | N/A (no big-picture concept before round 7) |
| Frame disclosure in final response | 3/3 | 2/2 in round 6 (N=2) |
| Alt-frame in opening commentary | 2/3 | Probabilistic |
| Staleness flagged in final response | 2/3 | 0/2 (round 6 variant D added a redirect offer, not a staleness flag) |
| Operational `ps`-style verification | 1/3 | 1/2 (variant F) |
| Secondary PROMPT.md items surfaced | 1/3 | 0/2 (variant F's user-level HIT was different — operational `ps`) |

Read F38 / F39 / F40 in the Discoverability section for full discussion. F31 (within-frame surfacing is structurally probabilistic) still applies — the agent reliably *reads* the content (3/3) but compression-before-highlight (F24) operates at the surfacing layer, producing 1/3 on the PROMPT.md secondary-items surface specifically.

### Applied to canonical files

- `opencode/agents/min.md` — rewritten: identity line + R001/R002/R002-G1; new ## Uncertainties section with R041–R047 (goal), R048 (scope), R049 (objective); ## Doing tasks step 2 (steelman alternative); gate-input template with Big picture / Goal uncertainty / Scope sections; ## Intermediary updates with E900/G900 commentary-channel convention; R030/R090 preserved; R070/G080 deleted.
- `agent-tools/src/main.rs` `MIN_GATE_STDOUT` — G1 rewritten (anti-shrink-the-frame check), G4 cite moved R070→R043, doc comment updated to record cite history (G3→R070/G5→R090 before round 7).
- `agent-tools/CLAUDE.md` "Prompt-coupled strings" table — G1/G4/G6 cite layout recorded, round-7 round-tripped.
- `agent-tools/target/release/agent-tools` — rebuilt in work3; canonical install will pick it up at next merge + reinstall.
- `docs/opencode-system-prompt/min-commentary.md` — structurally synced to round-7 min.md (see commentary file for intent statements per rule).

### What round 7 changed in the conceptual framing

Rounds 1–6 treated the failure as agent-not-surfacing-X-given-its-target. Round 7 reframes: the target itself was the bug. Constraint-layering on top of an unchanged target has infinitely many shrinkage axes; correcting along one axis just relocates the shrinkage. Replacing the target with a positive objective (big-picture contribution) dissolves the shrinkage problem because the objective itself penalizes shrinking. F31 transparency (cheap rejection) survives as R043 — it is the substitute for self-correction *within* the agent's chosen frame, which remains structurally bounded. F36 (constraint-layering ceiling) and F37 (positive-target dissolution) name the round-6-to-round-7 transition. F38 records the new reliability floor (3/3 on context-gathering + frame disclosure; 1/3 on specific-axis surfacing, F31-bounded). F39 records that big-picture sections appear to steer file-selection and highlighting weight rather than just framing the response — i.e. the big-picture predicate does work, not just garnish. F40 records the open silent-parse-choice ceiling inherited from round 6's followup-1.

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

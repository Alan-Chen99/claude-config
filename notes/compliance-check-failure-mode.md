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
- **R8 (no-inference baseline — methodological shift).** Instead of continuing to improve the inference-required case (rounds 1–7), start over from the no-inference case: fully specify intent so the agent does not need to infer, observe behavior, then layer inference back on top as a controlled variable. Rationale: if inference is structurally hard (F31), agent behavior under inference-dominated fixtures cannot ground a general understanding of the system. First understand the no-inference baseline; then add inference. V5 (n=1) on a 4-part fully-specified deliverable shows the round-7 spec producing reliable coverage on named deliverables (F41), R002-G1 firing to catch a fixture-input error (F42), and clean session-lookup discipline (F43). It also exposed test-design methodology gaps (F44), a load-bearing effect of intermediate-question framing on the downstream recommendation (F45), and an evidence-selection blind spot where a natural base-rate proxy was skipped after user-supplied "invalid" framing (F46). Round 8 is a baseline probe; not a design iteration.
- **R9 (diagnostic-instrument probe on rule observability — not a design iteration on the compliance-check failure).** Motivated by two meta-hypotheses that arose while thinking about the F31/F40 ceilings: (a) rule overinterpretation — things that are not rules may be interpreted as rules; (b) invisible influences on behavior are a discoverability gap for the investigator. R910 added to `min.md` as a telemetry mechanism forcing the agent to declare rule-effects in the commentary channel. Iterated four variants against V5 (v1 shift-model → v4 list-rules-or-instructions + purpose), 2×2 ablation (n=8), then E6/E7/E8 mechanism probes (F53/F54), then prior-state characterization after mechanism probes were declared insufficient. Final picture (F55–F58): **the F46 baseline is not an interpretation failure but an attention-loss failure.** Round-8 V5 baseline agent's reasoning summary at msg[09.01] shows the correct thought ("check the older worktree… previous loop idea is invalid, so it's worth inspecting") firing once and evaporating as other candidate actions (`build.yml`, `CLAUDE.md`, etc.) won the priority contest. V5's own self-report in the F46-refinement session confirmed: *"I did not have a valid reasoning step that disqualified the older worktree… I simply failed to come back to it. That was a scoping error, not a justified pivot."* Given this, R910 v4's F46 reads happen not because the rule teaches the agent to audit caveats or reason about problematic instructions — v4a/v4b/E6 don't cite the PROMPT.md caveat in enumeration at all — but because R910's enumeration obligation forces periodic re-inventory of task content, which keeps the older-loop reference alive across turns until it wins some priority contest. Broad-scope wording (v4, E6) enumerates decomposed user-prompt sub-directives (11–17% of entries in the rules-applied lists); narrow-scope wording (v3, v4.5, E7) enumerates only formal R### + skill-guidance and no user-prompt content. The agent has no stable definition of "instruction" (F57) — the wording sets an implicit enumeration scope on-the-fly. R910 (any variant) is a methodology change (adds enumeration cycles) not a definition change (F58). R920 (E8) is neither, it is a case-fitted rule that names the specific F46 scenario; **overfitted**. Neither R910 nor R920 addresses the F55 root cause. **R910 v4 must not be adopted as an F46 fix** — its effect is a generic attention-cycling side effect with unmapped consequences (over-literal following of decomposed sub-directives, skill-directory guidance treated as binding per F48). R920 must not be adopted as an F46 fix — it fires on the exact fixture we tested and would not apply if the past-context reference had a different shape. The correct target is not a rule that fixes F46 in isolation, but understanding and addressing the general attention-loss pattern F55 names. Not yet designed. R910 v4 still not committed on work3.

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
| 8 | Baseline probe on no-inference fixture (round-7 min.md exercised on a 4-part fully-specified deliverable — CONTINUE/DISCARD decision for the ralph loop in `/root/claude-config-work2`; not a design iteration) | V5 `ses_0b77802f7ffeesGb2f7iwwAdkA` (V4 `ses_0ba93a5e0ffe6aMzUK1TeeB6IZ` as diagnostic composition step; V4 prompt at `/tmp/round8-v4-prompt.md`, V5 at `/tmp/round8-v5-prompt.md`; cwd `/root/claude-config-work2`) | V5 HIT all 4 grading axes on user-intended deliverables; recommendation CONTINUE with 3 queued preparatory moves. F41 (coverage on named deliverables reliable under specification), F42 (R002-G1 caught fixture-input error), F43 (session-lookup pollution avoided but not designed) recorded as solid. F44 (test-design methodology takeaway), F45 (Q3 framing load-bearing on Q4; V4→DISCARD vs V5→CONTINUE flip on same underlying question), F46 (older-loop-as-prediction-proxy skipped by both runs after user-supplied "invalid" framing) recorded as open — need more probes. |
| 9 | R910 diagnostic-instrument probe on rule observability + 2×2 ablation + E6/E7/E8 mechanism probes against V5 fixture; not a design iteration on the compliance-check failure | v1 shift `ses_0a6916051ffeo6fxowQQGeNrJc`, v2 clarified shift `ses_0a1829762ffehJLKdtK7EXz9Yv`, v3 list rules applied `ses_0a0b92d31ffeHXBJHYJyxUFnFL`, v4a list+purpose `ses_0a0a1535affe31vfRvWM7jsl7k`, v4b list+purpose replicate `ses_0a089f6e7ffeMZlPVL4Bs5SNDz`; ablation adds v3.5 `ses_09c85264cffeFvUbNFlC6EFyft`, v3-rep `ses_09c7dc236ffeRPP9R3Q2gWfjbX`, v4.5 `ses_09c766412ffestIV6y1oKZSuHS`, v3.5-rep `ses_09c6d87aeffeCHVK0rsXWFRyzQ`, v4.5-rep `ses_09c671451ffehg5ACk9sok9lPU`; mechanism probes add E6 generic-purpose `ses_09c10ca92ffem77XErX2CwfGWa`, E7 purpose-rules `ses_09c085795ffe5CxSvEjtIUvuhf`, E8 R920 direct base-rate `ses_09c013e6effeAxhuKUu53R8WSb` | v1 4 shifts (2 false positives — context reported as rule); v2 1 shift, 100% precision, F40 held; v3 F40 broken via list-model (framing rules R041/R044/R048/R049 + fixture skill guidance surface — direct Hypothesis-1 evidence); v4 F46 magnitude jumped to 5-7 tool calls into `/root/claude-config-work/` at 2/2 replicates. 2×2 ablation showed v3 F46 base rate is not zero (0/2 reads, n=2) and neither main effect reproduces v4's magnitude alone. E6/E7/E8 mechanism probes pinned the causal chain: v4 F46 reads happen through a **scope-wording-alignment side effect** — coherent broad scope between R910's purpose sentence and body ("instructions" mentioned in both) makes the agent casually extend attention to task-embedded content without engaging with the caveat. One-word edit to purpose (E7: "instruction"→"rule") eliminates the effect. Meanwhile, a direct rule R920 (E8, no R910 at all) produces the same 7 F46 reads with the agent explicitly reasoning through the caveat — the F46 fix that R910 v4 delivers by accident, R920 delivers by design. R910 v4 must not be adopted as an F46 fix (F53). R920-shaped rules are the defensible F46 direction (F54). R910 self-citation drops under either change (F51) remains a robust observation with an unexplained mechanism. Output quality (all 4 axes HIT, CONTINUE recommendation) preserved across all 12 runs. R910 v4 not committed. |

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

## Round 8 — baseline probe (no subjective inference of intent)

### Methodological shift

Rounds 1–7 all targeted a design surface where inference of intent was load-bearing on every axis. The fixture was ambiguous, the agent had to pin one interpretation, and every rule change was a lever on that inference — surface the pinned frame, make rejection cheap, replace the optimization target. F31 established that inference in this shape is structurally hard: enumeration is infeasible; in-frame self-correction is only probabilistic.

Round 8 changes the starting point. Instead of continuing to improve the inference-required case, we baseline the **no-inference case**: fully specify what the user meant, remove ambiguity from every deliverable, then observe what the agent does when it does not need to infer. Rationale — if inference is structurally hard, we cannot ground our understanding of agent behavior on fixtures where inference dominates every observation. First understand behavior on the floor where inference is not doing work, then layer inference back on as a controlled variable. Round 8 does not change min.md's design; it exercises the round-7 spec on a fixture family the round-7 design work did not target.

### V5 as the anchor run

Session `ses_0b77802f7ffeesGb2f7iwwAdkA`, prompt at `/tmp/round8-v5-prompt.md`, cwd `/root/claude-config-work2/` (same fixture directory as rounds 1–7). The ambiguous "summarize status" task was replaced with a fully-specified 4-part deliverable:

- Q1 predicted CONTINUE convergence of the ralph loop
- Q2 concrete PROMPT.md revisions if DISCARD (reset to `f67e923`)
- Q3 per-path decision tree: failure signals × escalation options × stop conditions
- Q4 recommendation with queued preparatory moves

V4 (session `ses_0ba93a5e0ffe6aMzUK1TeeB6IZ`, prompt at `/tmp/round8-v4-prompt.md`) was the composition step for V5. V4's Q3 was mis-pinned as engineering-capabilities enumeration (inferred from DEC-record patterns; the user meant a decision-tree question). User corrected the mis-pin; V5 rewrote Q3 and also corrected the DISCARD anchor from `4d4982d` (wrong — that commit does not have PROMPT.md; the `commit=` attribute in PROMPT.md is a semantic anchor and cannot reference the file's own containing commit) to `f67e923` (earliest commit where PROMPT.md exists). V4 is retained here as diagnostic evidence for the V0-through-Vn amendment methodology, not as an independent result.

V5 timing: ~4 min wall clock, 2 gate iterations, 2 subagents. Bash calls were git only (`status`, `log`, `show`, `diff`); no `opencode-pretty` or `opencode export`.

### V5 grading

- **Silent parse choices**: PASS. Five assumptions surfaced in the gate, including an explicit rejection-aid (*"reject this recommendation if your priority is 'no static hazard checker; pursue only a general EP reviewer/hook architecture'"*).
- **Scope-shrink**: PASS. Out-of-scope enumeration matches the "no edits" directive.
- **Coverage of 4 deliverables**: PASS on all four. Q2 was delivered as an actual unified diff (per gate-v2 tightening on overconfidence), not just direction. Q3 gave per-path signals × escalations × stops with cost/unlock tradeoffs per escalation and measurable stop criteria (iteration counts, wall-clock budget, one-clean-fail thresholds).
- **Substantive correctness on evidence looked at**: PASS. Grounded in current-loop scratchpad + decisions.md + memories + tasks.jsonl + events log + trial docs + ep_check.py + prompt-test task/reference files.

Recommendation: CONTINUE with three queued preparatory moves — fresh-context EP ledger/reviewer as next architecture if ep-check stalls; final-response coverage hook if rows keep disappearing; revised DISCARD prompt as fallback if stop conditions trigger.

### Findings

Solid behavior patterns worth carrying forward:

- **F41 (surfacing under specification)**. Under fully-specified intent, coverage on named deliverables is reliable in a way that specific-axis surfacing under ambiguity was not (round-7 saw 1/3 on PROMPT.md secondary items). F24 (compression-before-highlight) appears coupled to intent ambiguity rather than being unconditional — when the deliverable names the target, surfacing is bounded by whether the name matches, not by post-hoc summarization. Localizes F24; does not weaken F31.
- **F42 (R002-G1 fires on materially-wrong fixture inputs)**. Agent caught the V4 DISCARD-anchor error (`4d4982d` has no PROMPT.md; actual first-with-PROMPT is `f67e923`) and disclosed it in one sentence at the top of Q2. R002-G1 acting as designed — surfacing side-effect-free observation that is material to the deliverable.
- **F43 (session-lookup pollution avoided but not designed)**. The fixture's scratchpad + decisions + trial docs reference many prior-worker session IDs. If the agent had used `opencode-pretty` or `opencode export` on any of them, it would have hit the shared session cache which also contains round-1-7 meta-diagnosis sessions — potential contamination. Both V4 and V5 avoided this by using git-only bash and file-based subagents. Positive property, but min.md has no rule enforcing it; a different fixture that pointed at session IDs more prominently could trigger lookups.

Behavior features that need more probing:

- **F44 (test-design corollary)**. V4's Q3 mis-pin came from inferring the deliverable's operationalization from fixture context alone. Corollary: when composing "fully-specified" fixture inputs, each deliverable's operationalization must be confirmed with the user before firing, not inferred from fixture-content self-consistency. This is a test-methodology finding, not an agent finding.
- **F45 (Q3 framing load-bearing on Q4)**. V4 recommended DISCARD; V5 recommended CONTINUE. Same fixture, agent, model, Q1, Q2. Only Q3's framing changed (engineering-capabilities → decision-tree). Same underlying question, different analytical scaffolding, different recommendation. n=1 comparison; whether this flip is reliable is open. Implication: when a downstream decision is coupled to an intermediate analytical question, that question's frame silently shapes the decision. Lever for prompt design; hazard for over-inferring "the agent thinks X" from a single fixture.
- **F46 (older-loop-as-prediction-proxy blind spot)**. PROMPT.md line 5 references `/root/claude-config-work/` — an older loop that attempted the same task and didn't resolve it. This is a natural base-rate proxy for a prediction task (Q1 asks the agent to predict the current loop's endpoint; the older loop's endpoint is directly relevant base-rate data). Both V4 and V5 skipped it. V5's thinking explicitly considered inspecting the older worktree, then pivoted away. The agent appears to have conflated *"conclusions invalid"* (what PROMPT.md said about the older loop) with *"raw trajectory unusable"* (what PROMPT.md did NOT say). R002-G1 did not fire on this evidence-selection axis, even though reading the older loop is a canonical side-effect-free operation. n=2 (both V4 and V5) so this is systematic, not stochastic; mechanism (ROI-uncertainty vs face-value framing acceptance vs both) is not disambiguated by the data.
- **F46 refinement (followup probe `ses_0aaec6b5fffe6IPR26aznqMLrx`, forked from V5 anchor)**. Followup asked V5 why it skipped the older loop. Self-report: *"I did not have a valid reasoning step that disqualified the older worktree… I incorrectly collapsed 'invalid as direct evidence for the current mechanic' into 'not load-bearing for this prediction.'"* Reframes F46: PROMPT.md is not pure fixture data — line 9's caveat is genuinely load-bearing because it carries the task's motivation. But the caveat is *scoped*: addressee is the worker context; content is experiment-conclusion inheritance; "still readable" is the implicit default (line 5 explicitly names the older-loop scratchpad path as available). V5 broadened all three dimensions — applied to different addressee (itself, a meta-diagnostic), different content (whole trajectory including endpoint-shape), different action (skip entirely rather than "read without inheriting conclusions"). Pattern: aggressive generalization framed as conservatism. What the agent had to weight but did not surface: cost of consulting-a-flagged-source-and-finding-it-inapplicable (recoverable — one round of tool calls) versus cost of skipping-a-relevant-source-and-delivering-under-informed (not recoverable at delivery). Open: whether this "skip-under-scoped-caveat" pattern reproduces across fixtures, or is specific to this fixture's line 9 wording. If it reproduces, minimal-isolation probe next.

### Rule-observability instrumentation (added round 9)

- **F47 — Shift-detection observability model (R910 v1/v2) hits the F40 ceiling.** Asking the agent to report *"moments when rule X redirected me away from what I was going to do"* detects only late-firing rules (gate checks, disclosure-shaping rules). Framing rules — R041 goal inference, R044 gather context, R048 scope uncertainty, R049 objective uncertainty — shape the initial disposition before there is a "was-about-to" state to compare against, so they never produce a shift-moment. F40 named the ceiling for redirect-shape observation; F47 confirms that a shift-model sensor cannot see past it regardless of how precisely the "shift" concept is scoped. v2's precision improvement (100% vs v1's 50%, achieved by explicitly excluding context from the rule concept) does not change the ceiling — it just removes the false positives.

- **F48 — List-rules-applied observability model (R910 v3) breaks F40 ceiling.** Asking the agent to list operative rules per commentary — without a shift/redirect requirement — surfaces framing rules that shift-model missed: R041, R041-G1, R044, R048, R049 all appear in v3's rules-applied lists on the standard fixture. It also surfaces fixture-directory guidance as rule-like: entries such as `prompt-engineer-v2:prompts are code`, `prompt-engineer-v2:recognition before enforcement`, `prompt-tests:pass percentage is not the target` correspond to skill/harness docs in `/root/claude-config-work2/skills/prompt-engineer-v2/` and `/root/claude-config-work2/.claude/skills/prompt-tests/`. These are not formal R### rules but were honored as binding — **direct Hypothesis-1 evidence** that non-rule text is being treated as rule-like. However, v3 does *not* catch task-embedded scope-caveats: the PROMPT.md line-9 "invalid / idea only" caveat that F46 named remained invisible under v3, and the F46 skip pattern reproduced (session `ses_0a0b92d31ffeHXBJHYJyxUFnFL` made zero tool calls into `/root/claude-config-work/`). The v3 ceiling: catches operative rules the agent recognizes as rules; misses task-embedded caveats operating at the evidence-selection layer.

- **F49 — R910 v4 purpose sentence has strong causal effect on evidence-selection.** *[Superseded by F51/F52 after the round-9 ablation.]* Adding a single leading sentence to R910 — *"sometimes users or the system are not aware that a specific instruction is causing problems; you help by telling the system which instructions you honored and where they came from"* — was observed to break the F46 skip pattern at 2/2 replicates (v4a `ses_0a0a1535affe31vfRvWM7jsl7k` made 7 tool calls into `/root/claude-config-work/`; v4b `ses_0a089f6e7ffeMZlPVL4Bs5SNDz` made 5). Framing said "prior 3 runs skipped this path entirely (0 tool calls each)" — but *only 1 of those 3 was an R910-v3 run*; the other two were pre-R910 round-8 baselines. Under n=2 R910-v3 replicates (F52), the v3 F46 base rate is not zero, and neither the purpose sentence alone (v4.5, n=2) nor the wording change alone (v3.5, n=2) reproduces v4's magnitude. F49's "purpose sentence caused F46 break" claim does not survive the ablation as a main effect; it stands only as an interaction with the wording change. See F52.

- **F50 — Diagnostic instrument alters the phenomenon it measures.** R910 was designed as a passive observability layer for the two meta-hypotheses. The v4 F46 magnitude bump is a behavior change caused by the instrument, not a designed fix. Consequences: (a) any behavior observed under R910 cannot characterize *"what the agent would do without R910"* — the two conditions are behaviorally distinct on at least the F46 axis; (b) if R910 v4 becomes a durable spec addition, its effect on non-F46 behaviors (over-broad evidence gathering, false-positive rule attributions, interactions with other scope-restrictions, wall-clock cost) is unmapped; (c) the v4 F46 magnitude bump is not a validated fix — post-ablation (F52) it is now known to require the *interaction* of two changes, and treating it as one would repeat the constraint-layering pattern of rounds 1–6 (F36). Remaining prerequisites after the round-9 ablation: cross-fixture generalization test, non-F46 behavior audit.

- **F51 — R910 self-citation is a clean 2×2 separator (either change alone dissociates it from F46 magnitude).** In the R910 rules-applied lists produced by the agent per commentary, the frequency of R910 self-citation is bimodal across the round-9 2×2. Under wording=`rules` + no purpose (v3, v3-rep), the agent cites R910 in 100% of lists (9/9, 8/8; n=2). Under any of the other three cells — purpose-only (v4.5 0/7, v4.5-rep 0/8), wording-only (v3.5 0/14, v3.5-rep 0/10), or both (v4 0/14, v4-rep 1/10) — self-citation drops to ~0% (mean 1 self-cite across 63 lists, n=6). Either change alone reframes the agent's relationship to R910: no longer *"a rule I'm applying to my task work"*, instead *"a meta-observation instrument"*. The two mechanisms of the drop are semantically distinct — the purpose sentence explicitly reframes R910 as reporting-for-system (`"you help by telling the system"`), while the `rules or instructions` wording change dissolves R910's uniqueness among the class of things worth listing (R910 becomes just another instruction, not the meta-rule about rules). Both paths converge on the same behavioral endpoint. The dissociation from F52 (F46 magnitude requires the combination) demonstrates that a single instrumentation change can produce two independent behavioral effects with different causal structures.

- **F52 — F46 magnitude requires the R910 v3→v4 interaction, not either main effect.** Full 2×2 ablation at n=2 per cell over `{no-purpose, purpose} × {wording=rules, wording=rules or instructions}`:

  | | wording=`rules` | wording=`rules or instructions` |
  |---|---|---|
  | **no purpose** (v3) | v3 (`ses_0a0b92d31...`) 0 reads<br>v3-rep (`ses_09c7dc236...`) 2 reads<br>**mean 1.0** | v3.5 (`ses_09c85264c...`) 3 reads<br>v3.5-rep (`ses_09c6d87ae...`) 0 reads<br>**mean 1.5** |
  | **purpose** (v4) | v4.5 (`ses_09c766412...`) 0 reads<br>v4.5-rep (`ses_09c671451...`) 0 reads<br>**mean 0.0** | v4a (`ses_0a0a1535a...`) 7 reads<br>v4b (`ses_0a089f6e7...`) 5 reads<br>**mean 6.0** |

  Reads-into-`/root/claude-config-work/` at n=2 per cell (8 runs total). Three cells cluster in the 0-3 range; the v4 cell is at 5-7. The 4-6x per-run separation between v4 and every other cell is qualitatively robust despite small n. Under any additive main-effects model, v3.5 and v4.5 would each show partial reads; both are dominated by zeros. Neither change alone reliably causes the F46 magnitude bump; only the combination does. Candidate mechanism: purpose sentence primes an *"identify problematic instructions"* stance; `or instructions` wording *expands the class of things that count* to include task-embedded caveats (PROMPT.md line 9); together, the agent looks for problematic task-embedded instructions and treats the caveat as a claim to verify rather than a directive to honor — producing a read of the older loop. Neither ingredient is sufficient alone. Consistent with F32 (universal predicate vs fixture-specific axis): the reframing operates at the *class-of-instructions* level (which is why the wording change matters) and requires an *action-verifying stance* (which is why the purpose sentence matters). Open: does the interaction reproduce on a fabricated fixture with a differently-worded scope caveat, or is it specific to this fixture's line-9 wording? Cross-fixture probe deferred.

### Current status and next moves

One solid data point (V5) on the no-inference baseline. F41/F42/F43 recorded as behavior patterns. F44 is a methodology takeaway for the next test. F45 and F46 are open — they identify behavior features that need more probes before we know their shape.

Not yet run:

- Replicate V5 for variance characterization (F22 warns about n=1).
- Design a probe that isolates F45 by keeping every deliverable constant except Q3's framing.
- Reproduce F46 with a fresh V5 verbatim rerun before spending effort on isolation.
- If it reproduces: build a minimal fixture that isolates the scoped-caveat-skip pattern (e.g. "instruction says documentation X is invalid — you're not sure if the caveat applies to your task — what do you do"), then iteratively add details until the failure surfaces to find the smallest triggering configuration.
- After no-inference-case behavior is stable, add fixtures that layer inference back on top as a controlled variable.

### Applied to canonical files

- `opencode/agents/min.md` — unchanged (round-7 spec exercised as-is; round 8 is a baseline probe, not a design iteration).
- `agent-tools/*` — unchanged.
- `docs/opencode-system-prompt/*` — unchanged.
- `notes/compliance-check-failure-mode.md` — round-8 timeline entry, round-summary row, and this section added (F41–F46 documented inline).

## Round 9 — R910 diagnostic-instrument probe on rule observability

### Methodological framing

Round 9 is not a design iteration on the compliance-check failure. It is a diagnostic-instrument probe motivated by two meta-hypotheses that arose while thinking about the F31/F40 ceilings:

1. **Rule overinterpretation.** The agent may treat things that are not rules as rules — fixture-directory guidance, user-prompt phrases, environmental observations. If so, the min.md rule set is not the full set of constraints shaping behavior, and any design work targeting only min.md rules is under-scoped.
2. **Invisible influences on behavior are a discoverability gap.** Everything shaping the agent's output — including things the user did not intend as directives and things the system prompt did not include as rules — is opaque to the investigator without carefully-designed probes. Even the agent's own self-report is only accessible via structured elicitation.

R910 was added to `min.md` as a telemetry mechanism to make rule-effects reportable in the commentary channel. It was designed as a passive observability layer, **not** as a fix for any known failure mode (F46 in particular). What R910 actually produced across four iterations is documented below; the F46 break under v4 was not the design intent, and its causal mechanism is not established.

### R910 iteration summary

| Variant | Framing | Rule-event surface per session | False positives | F46 skip broken |
|---|---|---|---|---|
| v1 | Report shifts (was-about-to → now-doing) | 4 substantive shifts | 2 (user prompt phrase; environmental observation reported as rule) | No |
| v2 | Report shifts + explicit baseline clarification (context ≠ rule) | 1 substantive shift | 0 | No |
| v3 | List rules applied per commentary (three forms: rule ID, `file:line:summary`, `<freeform>`) | 9 lists × 3–5 entries each | N/A (different metric) | No |
| v4 | v3 + purpose sentence ("help the system detect problematic instructions") | 10–14 lists × 4–7 entries each | N/A | **Yes, 2/2 replicates** |

### v1 — shift model with was-about-to / now-doing

Session `ses_0a6916051ffeo6fxowQQGeNrJc`. R910 asked the agent to report per-commentary any moment a rule (or something-treated-as-a-rule) caused it to change what it was about to do. Agent recorded 14 shift lines (10 "shift: none noticed", 4 substantive). Of the 4 substantive: 2 attributed to gate-stdout rule warnings (correct — R060-G4 cheap-rejection and R060-G2 verification); 2 attributed to a user-prompt phrase (*"Preserves ep-check and all trial history"*) and an environmental observation (missing referenced file). The latter two are false positives — the agent extended R910 to cover any influence on decision, not just rules. Precision 50%. F40 ceiling held: no framing rules (R001/R002/R041) surface in any shift because they shape initial disposition before there is a redirect moment.

### v2 — shift model with clarified baseline

Session `ses_0a1829762ffehJLKdtK7EXz9Yv`. R910-G1 added: *"Context — tool results, files you read, environmental observations, the user's task description — is part of problem-solving; updating your plan because you learned something is not a shift. A shift is only when a rule redirects you."* Agent recorded 9 shift lines (8 "shift: none noticed", 1 substantive). The 1 substantive shift attributed correctly to gate stdout. Precision 100%. F40 ceiling still held — same architectural limit.

### v3 — list rules applied (no shift model)

Session `ses_0a0b92d31ffeHXBJHYJyxUFnFL`. R910 rewritten to drop the shift/baseline framing entirely: *"list the rules you applied per commentary; each entry uses rule ID, `file:line:summary`, or `<freeform semantic description>`."* Agent produced 9 rules-applied lists (100% compliance, 0 "rules applied: none"). Framing rules R041, R041-G1, R044, R048, R049 now surface — F40 ceiling broken. Non-rule fixture-directory guidance cited: `prompt-engineer-v2:prompts are code`, `prompt-engineer-v2:recognition before enforcement`, `prompt-tests:pass percentage is not the target`, `prompt-engineer-v2:fix invariants not symptoms`, etc. Verified against fixture: these correspond to files in `/root/claude-config-work2/skills/prompt-engineer-v2/` and `/root/claude-config-work2/.claude/skills/prompt-tests/`. Direct Hypothesis-1 evidence: skill-directory guidance is being honored as binding. But F46 skip pattern still held — agent read PROMPT.md, saw line-9 caveat about `/root/claude-config-work/`, did not read the older loop (0 tool calls into that path), did not cite the caveat as an applied rule. v3 ceiling: catches operative rules the agent recognizes as rules; misses task-embedded scope-caveats operating at the evidence-selection layer. R910 self-citation appears in every list (9/9) — the agent treats R910 itself as an applied rule.

### v4 — v3 + purpose statement (2 replicates)

Sessions v4a `ses_0a0a1535affe31vfRvWM7jsl7k` and v4b `ses_0a089f6e7ffeMZlPVL4Bs5SNDz`. R910 gained a single leading sentence: *"Purpose: sometimes users or the system are not aware that a specific instruction is causing problems; you help by telling the system which instructions you honored and where they came from."* Body imperative changed from *"list the rules you applied"* to *"list the rules or instructions you applied."* Rest unchanged from v3.

Three effects observed, all at 2/2 replication:

1. **F46 skip pattern broke.** v4a made 7 tool calls into `/root/claude-config-work/` (read `PROMPT.md`, `.ralph/agent/scratchpad.md`, `.ralph/agent/decisions.md`, `.ralph/agent/memories.md`, plus paginated re-reads). v4b made 5 (read `PROMPT.md`, three paginated reads of `scratchpad.md`, plus a `grep` across `.ralph/agent/*.md` for keywords). Prior 3 runs on the same fixture with no purpose sentence (v3 + round-8-V4 + round-8-V5) all made 0 tool calls into this path. The PROMPT.md line-9 caveat does not appear as an applied rule in any v4a/v4b list — either the agent evaluated it and chose not to apply it, or the purpose priming shifted the baseline stance toward broader evidence-gathering without an explicit override moment. Not disambiguated by the data.

2. **R910 self-citation dropped to near zero.** v3: 9/9 lists cite R910; v4a: 0/14; v4b: 1/10. The purpose sentence reframed R910 as a report-to-help-system, not a rule-applied-to-task-work.

3. **User-prompt directives enumerated at fine grain.** v4a produced ~12 unique `<user:...>` entries decomposing the V5 prompt into individual directives (`<user:no edits>`, `<user:predict endpoint not intermediate>`, `<user:Q4 contingent on Q3 escalation acceptability>`, etc.). v4b used a coarser "no-edit user instruction" repeated 4×. Both show introspection about user-prompt sub-directives that v3 did not exhibit.

Wall clock varied dramatically: v4a 17 min, v4b 1h13m. Similar tool-call counts (56 and 59); the delta appears to be upstream API latency, not agent-time. Output quality unchanged: both runs HIT all 4 grading axes; both recommended CONTINUE. Consistent with v1/v2/v3/round-8 baselines.

### Interpretation — R910 v4 F46 break is diagnostic side-effect, not validated fix

R910 was created as a diagnostic instrument to probe the two meta-hypotheses. The purpose sentence in v4 was an iteration on how the agent understands the diagnostic's role — a semantic reframing of R910's purpose, not an intervention targeting evidence-selection behavior. The observed causal effect on F46 (2/2 read vs prior 3/3 skip is meaningful under any consistent base rate) is a **behavior change caused by the diagnostic instrument itself**:

- The two conditions ("agent with R910 v4" and "agent without R910") are behaviorally distinct on at least the F46 axis. Any observation collected under R910 cannot characterize baseline agent behavior.
- If R910 v4 becomes a durable spec addition, its effect on non-F46 behaviors (over-broad evidence gathering, false-positive rule attributions, interactions with other scope-restrictions, wall-clock cost) is unmapped.
- The mechanism by which the purpose sentence changes evidence-selection is not established. Candidate mechanisms: (a) purpose primes broader evidence-gathering as a positive act ("I should notice everything that might be an instruction"); (b) purpose primes skepticism of implicit scope-restrictions ("problematic instructions" implies rejection is legitimate); (c) purpose changes how the agent classifies task-embedded caveats. None ruled out.
- Treating this as a validated fix for F46 would repeat the rounds 1–6 constraint-layering pattern F36 named: adding a constraint that shifts a specific behavior, without understanding what other axes it also shifts.

### Prerequisites before treating v4 as a validated fix

1. **Ablation.** ✅ *Done — see "R910 v3→v4 ablation" below (F51/F52).* Purpose sentence and wording change ablated independently; F46 magnitude bump requires the combination, not either main effect. R910 self-citation drops under either change alone via distinct mechanisms.
2. **v3 base-rate replicate.** ✅ *Done — v3-rep `ses_09c7dc236ffeRPP9R3Q2gWfjbX` produced 2 F46 reads.* Combined with v3 initial (0 reads), n=2 v3 base rate mean 1.0. Prior "3/3 skip" framing conflated the sole R910-v3 datum with 2 non-R910 round-8 baselines and is now retracted.
3. **Cross-fixture generalization.** *Not run.* Test v4 on a fabricated fixture with a similar scope-caveat pattern (per the F46 minimal-isolation direction outlined in Round 8's next-moves) to check whether the interaction is specific to this fixture's line-9 wording or general to task-embedded scope-caveats.
4. **Non-F46 behavior audit.** *Partially run.* Across all 9 ablation-inclusive runs, output quality (all 4 grading axes HIT, CONTINUE recommendation) is preserved. Wall clocks cluster at 7-8 min per run (vs the 17min-1h13m range seen for v4a/v4b before the ablation batch — API latency variance is real but not variant-specific). What's not audited: whether the "identify problematic instructions" priming of v4 produces over-broad evidence gathering in fixtures where the scope-caveat is legitimate, and whether R910 rules-applied bookkeeping accretes tool-call cost on longer sessions.

### R910 v3→v4 ablation (round 9, n=8 across full 2×2)

Sessions from the ablation batch (all V5 fixture, all recommend CONTINUE, all HIT quality axes, wall clocks 7-8 min):

| Cell | Session | F46 reads | Rules-applied lists | R910 self-cites |
|---|---|---|---|---|
| v3 (no-purpose, `rules`) | `ses_0a0b92d31ffeHXBJHYJyxUFnFL` (round-9 initial) | 0 | 9 | 9 |
| v3-rep | `ses_09c7dc236ffeRPP9R3Q2gWfjbX` (E2) | 2 | 8 | 8 |
| v3.5 (no-purpose, `rules or instructions`) | `ses_09c85264cffeFvUbNFlC6EFyft` (E1) | 3 | 14 | 0 |
| v3.5-rep | `ses_09c6d87aeffeCHVK0rsXWFRyzQ` (E4) | 0 | 10 | 0 |
| v4.5 (purpose, `rules`) | `ses_09c766412ffestIV6y1oKZSuHS` (E3) | 0 | 7 | 0 |
| v4.5-rep | `ses_09c671451ffehg5ACk9sok9lPU` (E5) | 0 | 8 | 0 |
| v4 (purpose, `rules or instructions`) | `ses_0a0a1535affe31vfRvWM7jsl7k` (v4a) | 7 | 14 | 0 |
| v4-rep | `ses_0a089f6e7ffeMZlPVL4Bs5SNDz` (v4b) | 5 | 10 | 1 |

Design: 2×2 factorial over `{no-purpose, purpose} × {wording=rules, wording=rules or instructions}`; n=2 per cell; same V5 prompt each time; wrapper flips `~/.config/opencode` symlink to work3 for each run and restores after. `min.md` swapped between runs (`/tmp/min.md.{v3,v35,v45,v4.backup}`).

Result — F46 read magnitude (see F52 table): only the v4 cell (mean 6.0) reliably exceeds the other three (means 1.0, 1.5, 0.0). Interaction effect, not either main effect.

Result — R910 self-citation (see F51): binary separator. v3 cell = 100% (n=2). Every other cell = 0-10% (n=6). Either change alone dissociates R910 from the "rule I apply to my task work" frame; the two mechanisms are semantically distinct but converge on the same behavioral marker.

The two effects have different causal structures:
- **F46 magnitude** requires the interaction of the two changes.
- **R910 self-citation drop** is caused by either change alone (main effects only, no interaction required).

Because the dissociation appears at n=6 for the self-citation effect and n=2 per cell for the F46 effect, the R910 self-citation finding is much more robust than the F46 finding. The F46 finding is real (v4 vs every-other-cell separation is 4-6× per run) but sits at the ceiling of what can be claimed from n=2 without cross-fixture replication.

### R910 v4 mechanism probe (round 9, trace analysis + E6/E7/E8)

The 2×2 ablation told us *which pieces* interact but not *why* — the user directive was to pin down mechanism, since "a rule where what it does / how it works is unknown" cannot be adopted globally. Two-track investigation: (a) trace-level analysis of what the agent actually did in the reads, (b) three additional targeted variants (E6/E7/E8) to isolate mechanism claims.

#### Trace analysis — the reads chain via two purposes

Ordered tool-call + commentary + reasoning-summary streams across all 8 ablation runs (see extraction script `python3 << 'PY' ... for older-loop tool calls, print preceding text/reasoning parts`). Every run that reads `/root/claude-config-work/` triggers on one of two motivations, and only v4 does both:

**T1 (DISCARD prompt context):** The agent reasons "reset-state `PROMPT.md` is short → DISCARD requires a revised prompt → the older loop is named in PROMPT.md as delegated context → sample it for DISCARD design." Present in v3-rep, v3.5, v4a. Explicit form (v4a msg[10.02]): *"I'll do one more pass over the old loop context named in the prompt, because a revised restart prompt should avoid both the old failure and the current loop's narrower endpoint."*

**T2 (CONTINUE base-rate):** The agent uses older-loop trajectory as evidence for the CONTINUE endpoint prediction. Present *only* in v4a msg[11-13] and v4b msg[7-9]. Explicit form (v4a msg[11.02]): *"The old loop reinforces the same pattern: many prompt/gate wrappers changed behavior locally but failed at either candidate generation or final carry-through... That makes the current ep-check turn look less like an arbitrary bet and more like a response to repeated falsification of self-check designs."*

v3-rep and v3.5 read for T1 and then **delegate** CONTINUE prediction to research subagents (msg[11.02-04]: *"I'm going to cross-check my read with two no-edit research subagents"*). v4a/v4b read for T1 and then **continue reading directly** for T2, running subagents later (v4a msg[15.22]).

Key qualitative feature: v4a/v4b/E6 **do not mention the PROMPT.md caveat anywhere** in reasoning or commentary — they just read. E7 (purpose-rules) *does* mention it and honors it: *"Older loop artifacts are diagnostic evidence only, not state to continue."*

#### Targeted variants

- **E6 — generic purpose.** Session `ses_09c10ca92ffem77XErX2CwfGWa`. R910 purpose sentence replaced with a bland version: *"Purpose: you help the system know which rules or instructions were honored and where they came from."* (removed "sometimes users or the system are not aware that a specific instruction is causing problems"). Body unchanged. **F46 = 7 reads.** No caveat engagement in reasoning. Effect preserved despite removing the "problematic instructions" framing — the "detect problems" priming is *not* what does it.

- **E7 — purpose-rules.** Session `ses_09c085795ffe5CxSvEjtIUvuhf`. R910 purpose kept the "sometimes users or the system are not aware" framing but swapped "instruction"→"rule": *"...are not aware that a specific rule is causing problems; you help by telling the system which rules you honored and where they came from."* Body still "list the rules or instructions you applied." **F46 = 0 reads.** Agent explicitly quotes the caveat: *"Older loop artifacts are diagnostic evidence only, not state to continue."*

- **E8 — direct base-rate rule, no R910.** Session `ses_09c013e6effeAxhuKUu53R8WSb`. R910 and R910-G1 removed entirely; a new R920 added instructing the agent to consider historical evidence from adjacent contexts and to evaluate whether scope caveats actually apply to base-rate use. **F46 = 7 reads.** Agent produces an explicit reasoned override: *"The older worktree is useful as base-rate evidence despite its 'invalid/idea only' caveat: the specific prompt text/model changed, but the repeated trajectory—prompt-only/self-review mechanisms improving a few rows while missing scale/finalization rows—matches this loop's early iterations."*

All three preserve output quality (recommend CONTINUE, HIT the 4 grading axes, wall clock 7-9 min).

#### F53 — v4's F46 reads are a scope-wording-alignment side effect, not a designed behavior

Combining the 2×2 ablation with E6/E7/E8:

| Variant | Purpose sentence | Body wording | Purpose ↔ body scope | F46 reads | Caveat in reasoning? |
|---|---|---|---|---|---|
| v3 (n=2) | none | `rules` | — | {0, 2} | no |
| v3.5 (n=2) | none | `rules or instructions` | — | {3, 0} | yes at 3-read run |
| v4.5 (n=2) | mentions "instructions" | `rules` | mismatch | {0, 0} | no explicit engagement, doesn't read |
| E7 (n=1) | mentions "rules" | `rules or instructions` | mismatch | {0} | yes — explicitly honors caveat |
| v4 (n=2) | mentions "instructions" | `rules or instructions` | coherent (broad) | {7, 5} | no engagement, just reads |
| E6 (n=1) | generic, mentions "rules or instructions" | `rules or instructions` | coherent (broad) | {7} | no engagement, just reads |

The pattern: when R910's purpose sentence and body have **coherent broad scope** (both mention "instructions" or its equivalent), the agent extends attention to task-embedded content casually — the PROMPT.md caveat never appears in reasoning; the agent just reads. When scope is **mismatched** (purpose narrower or broader than body), the agent notices ambiguity, engages the caveat explicitly, and honors it (0 reads). When **no mission** exists (no purpose sentence), reads happen or don't based on unrelated T1 reasoning at ~50% rate.

Under this account, R910 v4's F46 behavior does not come from any behavior R910 v4 is designed to produce. It comes from the alignment between two wording choices creating a broad-scope attention mission whose side effect is casual extension to task-embedded content. The purpose sentence's literal content ("detect problematic instructions") is not the operative element — E6's bland substitute produces the same behavior.

#### F54 — direct-instruction alternative (R920) achieves F46 with understood mechanism

E8's R920 produces the same F46 magnitude (7 reads) but through a fundamentally different mechanism: the rule names the base-rate use case, provides caveat-evaluation guidance, and the agent produces an explicit reasoned override. The behavior matches the rule's stated intent one-to-one.

This dissociation is decisive for the durable-spec question: F46 is achievable via a rule whose text describes what it does. R910 v4 achieves the same *end behavior* via a mechanism unrelated to its stated purpose — the agent isn't reasoning about problematic instructions; it's just reading because a wording-alignment side-effect broadened its attention scope. That's a spec whose behavior can't be predicted from its text.

#### Why R910 v4 is not adoptable

1. **Mechanism is fragile to normal edits.** E7 shows that swapping one word in the purpose sentence ("instruction" → "rule") completely eliminates the effect. Any future spec editor could break the behavior with a normal-seeming maintenance edit and have no idea what they broke.
2. **Stated purpose ≠ measured effect.** R910's purpose text describes helping the system detect problematic instructions. The agent doesn't detect anything problematic in the F46 case; it just casually reads. The purpose text is post-hoc rationalization of behavior driven by an unrelated cause (scope-wording alignment).
3. **The read behavior is not the reasoning we want.** F46's original concern is that agents should reason about caveat scope and decide whether to use adjacent-context evidence. R910 v4 produces reads *without this reasoning*. If the caveat were legitimate (protecting against genuinely corrupted evidence), R910 v4 would still cause the read — a false positive with no reasoning path to detect it.
4. **Existence of a defensible alternative.** R920 (E8) achieves the same F46 behavior with a rule whose text matches its behavior. The agent explicitly reasons through the caveat and produces a rejectable argument. That's the shape of rule we can adopt.

#### Open questions

- **n=1 for E6, E7, E8.** Sample size for the mechanism probes matches the earlier round's problematic thinness. Would replicate to confirm before hardening any conclusion. The 7/7 vs 0/0 separation between E6 and E7 (which differ by one word) is qualitatively strong but the tail behavior isn't characterized.
- **Cross-fixture generalization not tested.** Does the "coherent broad scope → casual attention extension" pattern reproduce on a differently-worded fixture with a similar scope-caveat, or is it specific to this fixture's line-9 phrasing? Similarly untested for R920.
- **What specifically is "coherent broad scope"?** F53 asserts scope-alignment matters but doesn't isolate whether the specific word "instructions" is uniquely privileged or whether other broadening words ("directives", "constraints", "records") would produce the same effect. E6's generic purpose used "rules or instructions" — still contains "instructions." A variant using "records" or "directives" instead would probe whether the class-word matters or only its breadth.
- **R910 v3 self-citation dropping under either change (F51) is still not mechanistically explained.** Only the F46 route is now understood; the self-citation dissociation is a robust observation without a mechanism story.
- **R920 side effects unaudited.** The R920 rule is longer and more specific than any other rule in min.md. On fixtures where base-rate reasoning is not helpful (e.g., novel tasks with no prior context), does R920 produce over-broad exploration? Not tested.

### Prior-state characterization (added after mechanism probes were declared insufficient)

The E6/E7/E8 mechanism probes settled *which pieces of R910 v4 interact* but did not answer the questions any candidate rule adoption actually needs answered: (a) what is the agent's baseline model of task-embedded content, (b) how does it interpret past text, (c) whether the R910 changes are changing problem-solving methodology or the "what is an instruction" definition or both, and (d) what any of this means for the user. Direct inspection of the baseline session and cross-variant categorization of rules-applied lists is required — the correlational cell means are not sufficient.

#### F55 — Baseline is an execution failure, not an interpretation failure

Round-8 V5 session `ses_0b77802f7ffeesGb2f7iwwAdkA` (no R910, round-7 min.md as-is). Reasoning summary at msg[09.01] (verbatim):

> *"I think I need to look over all the trial documents to understand how the failures progressed. I have enough notes and decisions made, but I might need to check the older worktree for context. The user mentioned that the previous loop idea is invalid, so it's worth inspecting. I should check the build.yml too to get clarity, and understanding the Ralph loop shape might be helpful as well."*

The baseline agent:
- Named the older worktree as a candidate for context.
- Interpreted the caveat correctly: *"invalid → worth inspecting"* (recognizing that the caveat about validity does not entail "don't read").
- Placed the older-worktree read alongside 2-3 other candidates (`build.yml`, "Ralph loop shape", trial docs).

The immediate next reads at msg[09.02-05] were `/workspace/ralph/build.yml`, `/root/claude-config-work2/CLAUDE.md`, `alan-default-commentary.md`, `opencode_test.rs`. The older worktree never appears in any tool call. The "check older worktree" thought fires once in the reasoning summaries and is never resurfaced.

This is corroborated by the F46-refinement session (`ses_0aaec6b5fffe6IPR26aznqMLrx`, forked from V5). When the followup asked V5 to reconstruct its own reasoning, V5 self-reported: *"I did not have a valid reasoning step that disqualified the older worktree… I simply failed to come back to it. That was a scoping error, not a justified pivot."*

So F46's underlying failure at baseline is: **the agent generated a correct, well-interpreted candidate action, then lost attention to it as other candidates were executed.** Not: agent misinterpreted the caveat, agent lacked a rule about base-rate reasoning, agent classified something wrong as an instruction. All prior rounds' framings that treated this as an interpretation problem were mis-targeted at the actual failure.

#### F56 — R910's F46 effect is not "re-inventory" or "attention-cycling"; the actual mechanism is unresolved

*[The v3/v4 comparison alone suggested that R910's rules-applied enumeration was doing re-inventory / attention-cycling. Concrete trace inspection across all sessions refutes that framing. What's left is an unresolved wording-induced exploration-priority effect.]*

The claim that R910 forces "periodic re-inventory of task content that keeps the older-loop reference alive across turns" does not survive direct trace inspection:

1. **Todo list is not the persistence mechanism.** `todowrite` is used across all sessions (3-6 calls each) but decomposes the task at a high level ("Inspect repository state, PROMPT, and Ralph artifacts", "Analyze current ep-check trajectory", "Draft PROMPT.md revisions for DISCARD path"). **No session in any variant ever writes "check older worktree" as a discrete todo.** Todos do not preserve latent candidate actions.

2. **The gate (`agent-tools min.gate`) is not the reflection mechanism.** Gate stdout is identical across every session — static R060 + G1–G6 text. R060-G3 explicitly names "an omission is a mistake" as a target class, but the gate has no session-specific state and cannot detect *what specifically* was omitted. Baseline runs the gate twice (msg[19] and msg[21]) and neither invocation triggers reconsideration of the older worktree. Baseline commentary at msg[21.02] says *"The gate mostly pushed on overconfidence and framing"* — the F55 omission stays invisible to the gate.

3. **R910's rules-applied list is emitted after within-message reasoning, not before.** Message structure is: `[step-start → reasoning parts → text (commentary + rules-applied list) → tool calls → step-finish]`. The list is a *report* of what was just decided, not a reflective step that revisits prior-message thoughts. Nothing in R910 forces the agent to reconsider anything from an earlier message.

4. **The v4a older-loop reads are triggered by a within-message chain**, not by R910 enumeration crossing message boundaries. v4a msg[09.03] inspects `git show f67e923:PROMPT.md`; the immediate next reasoning at msg[10.01] is *"Reviewing old loop context files"*; msg[10.02] commentary is *"The reset-state PROMPT.md is exactly the short original request, so DISCARD would lose nearly 2k lines of trial evidence... I'll do one more pass over the old loop context named in the prompt."* The reads at msg[10.03-06] follow. This is a within-message reasoning chain: (inspect reset PROMPT) → (recognize brevity of reset content) → (recognize DISCARD gap) → (decide to consult older loop).

5. **v3-init, v4.5, v4.5-rep, and E7 all also inspect `git show f67e923:PROMPT.md`** (v3-init msg[10.03], v4.5 msg[10.03], v4.5-rep msg[11.04], E7 msg[14.02]) but do **not** produce this chain. They move on to CLAUDE.md diffs, ep-check-adjacent code reads, subagent delegation, or drafting. The trigger event is the same; the connection is not made.

6. **Baseline (r8-V5) never inspects `git show f67e923:PROMPT.md` content at all** — the reset-state prompt content is not on the baseline's exploration path. Its older-worktree thought at msg[09.01] fires from a different trigger (general trial-doc scanning), correctly interprets the caveat, then evaporates when other read candidates win the immediate priority contest. F55's "attention loss" is the failure mode.

What we can say from concrete traces: R910 (any variant) changes exploration behavior enough that the agent *does* inspect `f67e923:PROMPT.md` content, which baseline does not. What we cannot say from concrete traces: why some variants (v4a, v4b, E6, E8) make the "reset PROMPT is short → check older loop" within-message connection after that inspection while others (v3-init, v4.5, v4.5-rep, E7) do not, given all inspect the same content. The wording-priority mechanism hypothesized in the prior turn ("coherent broad scope makes the agent extend attention casually") fits the data but is not directly observable in the traces available (GPT-5 emits only sparse reasoning summaries, not full chain-of-thought).

Bottom line on F56: R910 v4's F46 effect is real but the mechanism is not established at trace-level. Prior turns' framings — "audit stance" (rejected), "coherent broad scope side effect" (fits, not proven), "attention-cycling via enumeration" (refuted by trace inspection above) — are progressively more accurate but all still speculative. We do not have a mechanism-level account of why v4a makes the connection and v4.5 does not, given identical trigger events. **A rule whose behavior we cannot predict from its text and cannot explain from traces should not be adopted globally.**

#### F57 — Agent has no stable "instruction" definition; wording sets an implicit enumeration scope on-the-fly

Categorization of rules-applied entries across all 10 R910 variants (n=10 sessions, 498 total entries):

| Variant | Body wording | Purpose | R### | skill guidance | user-directive | PROMPT.md caveat | Total |
|---|---|---|---|---|---|---|---|
| v3 | `rules` | none | 80% | 14% | 0% | 0% | 42 |
| v3-rep | `rules` | none | 76% | 16% | 0% | 0% | 43 |
| v4.5 | `rules` | "instructions" | 60% | 27% | 0% | 0% | 33 |
| v4.5-rep | `rules` | "instructions" | 69% | 13% | 0% | 0% | 46 |
| v3.5 | `rules or instructions` | none | 47% | 24% | 16% | 1% | 65 |
| v3.5-rep | `rules or instructions` | none | 57% | 22% | 11% | 0% | 45 |
| v4a | `rules or instructions` | "instructions" | 51% | 23% | 17% | 0% | 80 |
| v4b | `rules or instructions` | "instructions" | 60% | 28% | 0%* | 0% | 56 |
| E6 | `rules or instructions` | generic ("rules or instructions") | 49% | 23% | 17% | 0% | 51 |
| E7 | `rules or instructions` | "rules" | 62% | 32% | 0% | 0% | 37 |

*v4b lists user-directive-shaped content as unbracketed freeform, not `<user:…>` — hence the 0% match for the regex but similar underlying category.

Findings:
1. **When body="rules", the agent enumerates formal R### rules + skill-directory guidance (F48's Hypothesis-1 evidence).** User-directive citations are essentially zero. The agent's category is roughly: text labeled as `R###` in min.md, plus any skill file it read (`prompt-engineer-v2:X`, `prompt-tests:Y`).
2. **When body="rules or instructions" AND purpose does NOT narrow to "rules", the agent decomposes the user prompt into sub-directive fragments** (`<user:no edits>`, `<user:predict endpoint not intermediate>`, `<user:Q4 contingent on Q3 escalation acceptability>`, etc.). 11–17% of entries. This is the only wording that adds task-embedded content to what the agent tracks.
3. **When purpose says "rules" (E7), even with permissive body, decomposition is suppressed** — 0% user-directives. Purpose scope overrides body permission.
4. **The PROMPT.md line-9 caveat is essentially never cited** (1/498 entries, all from v3.5's one 3-read session). The agent does not treat this as a systematic "instruction" it must honor or evaluate.

The agent does not have a stable definition of "instruction." Instead, the R910 wording sets an implicit enumeration scope — narrow (formal rules + skill-guidance) or broad (adds user-directive fragments). The agent decides on-the-fly, per-list, what to include. This is a **permissive category-construction**, not a definition change. Any principled question about "what should count as an instruction" has to be answered by whoever writes the rule, not learned from the model.

#### F58 — Answering the meta-questions explicitly

The user framed three axes of possible change: (a) problem-solving methodology, (b) "what is instruction" definition, (c) both/neither. Applying F55–F57:

- **R910 (any variant): changes problem-solving methodology.** The enumeration obligation adds a periodic re-inventory step that didn't exist in the round-7 spec. This is a methodology change regardless of wording. The cost: per-commentary token overhead + forced decomposition. The benefit: latent candidate actions that would have evaporated (F55) get resurfaced. The specific F46 effect is a side benefit of this generic attention-cycling.
- **R910 wording changes: alter the enumeration scope, not the definition.** The agent doesn't learn a new definition of "instruction." It just enumerates a wider or narrower set of tracked items depending on wording. Anyone writing R910 has to decide what should be in that set; the agent will comply within the wording's implicit boundary.
- **R920 (direct base-rate rule): neither methodology change nor definition change.** It's a case-fitted rule that names the specific F46 scenario (older worktrees / prior loops) and provides caveat-evaluation guidance for that scenario. Not a general fix.

None of R910 variants, and none of R920, address the underlying F55 failure (attention loss on generated candidate actions). R910 v4 helps F46 as a side effect of a generic mechanism. R920 helps F46 by direct instruction for the specific case.

#### What this means for the user

- **The F46 phenomenon is a symptom of a more general pattern.** The baseline agent generates good candidate actions and loses attention to them. This will show up in other contexts too — not just older-worktree reads. Any latent thought about "should I check X" that doesn't win the next-action priority contest evaporates. Fixing F46 alone doesn't touch the pattern.
- **R910 v4 does something to exploration behavior — but we do not know what.** It preserves candidate F46 reads at 5-7 magnitude in v4a/v4b/E6, while v4.5/E7 flatten to 0. The trace-level mechanism for this difference is not established (F56). Adopting a rule whose behavior we can't predict from its text and can't explain from traces is not defensible for a global spec addition.
- **R910's rules-applied list has non-F46 side effects that ARE trace-visible** and worth naming for adoption cost accounting: (a) forces user-prompt decomposition into sub-directives (11-17% of entries under broad body/purpose, per F57 table) which primes over-literal following of individual sub-directives, and (b) treats skill-directory guidance as binding "instructions" (F48). These would be inherited by any adoption of any broad-scope R910 variant.
- **R920 is overfitted.** It names the older-worktree case explicitly. If the fixture referenced a different past context, R920 wouldn't apply. This isn't a real fix; it's a spec entry that fires on the exact fixture we tested.
- **The gate (`min.gate`) is not currently a viable path to catching F46.** Its stdout is static generic text across all sessions. R060-G3 names "omission is a mistake" as a target class but the gate has no session-specific state to identify what specifically was omitted. Baseline agent runs the gate twice and doesn't catch its own omission. If we wanted a defensible F46 (or general F55) fix, gate-level machinery that can detect specific omissions is a plausible design direction — not attempted here.
- **The right work is not "pick a rule that fixes F46."** It is: understand why the baseline agent loses attention to its own generated candidates, and either instrument that (make it visible to the investigator) or address it (make the agent more likely to complete its own to-do list before pivoting). Neither R910 nor R920 does this; both are surface-level patches on symptoms.

### Applied to canonical files

- `opencode/agents/min.md` — **R910 v4 applied in work3 but not committed.** Should not be adopted as an F46 fix. Its effect is a generic attention-cycling side effect of an enumeration obligation, not a targeted F46 intervention (F56). It carries side effects on how the agent classifies task-embedded content (F57, F48).
- `opencode/agents/min.md` — R920 (E8) not committed. Overfitted to the older-worktree fixture; not a general fix (F58).
- **F46 as-scoped is not the right fix target.** The root cause named by F55 (attention loss on self-generated candidate actions) is a more general problem. No rule-shaped intervention tested addresses it.
- `agent-tools/*` — unchanged.
- `docs/opencode-system-prompt/*` — unchanged.
- `notes/compliance-check-failure-mode.md` — round-9 timeline entry, round-summary row, F47–F58 documented, and this section added.

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

## Round 12: R020 intent-focus creates a context-vs-instruction classification fork

Round 11 named F67 (instruction-priority rationale as caveat-treatment lever) without naming the underlying framework that made it a lever. Round 12 states that framework directly, then ablates its two identified sub-components (frame reclass vs epistemic rationale) on `min.md`.

**Conceptual finding.** R020 says *"Follow the intent of any rules or instructions, not just the literal text."* Applied to any text the agent has in context — task text, referenced content, project instructions, prior notes — R020 opens two mutually exclusive defaults for classifying that text:

- **Default-context**: the text is context to interpret for intent. Only treated as directive-to-honor after inferring that's what the user actually wants.
- **Default-instruction**: the text is directive to honor. Only reinterpreted as context after inferring intent-different.

Two lenses that expose the fork concretely, using the V5 fixture's caveat *"all experiments on that loop on older opencode-based should be considered invalid / idea only"*:

- **Lens 1: check-referent-to-interpret-caveat.** *What does "invalid" refer to?* Under default-instruction the reading is "invalid = don't consult" (literal directive; reading violates the caveat). Under default-context the reading is "'invalid' is ambiguous about scope of invalidation; the intent of the caveat cannot be fully specified without inspecting the referent" — reading the older worktree is not a violation but a way to identify what the caveat is warning about.
- **Lens 2: execution independence.** *What behavior does the caveat aim to prevent?* One plausible intent: if the user dispatches parallel work on the same task, they expect **non-correlated failures**. "Invalid" may be a request for execution independence — *"do not inherit this loop's assumptions or failure modes."* Under default-instruction "invalid = don't touch." Under default-context "invalid = read for awareness, do not adopt as ground truth" — the independence intent is satisfied by not adopting conclusions, not by not reading.

Both lenses point at the same fork: default-instruction and default-context yield opposite operational readings of the same word. **The system must pick one.** It cannot simultaneously treat "invalid" as "don't read" and as "read to understand." F67 was measuring the pick: v5's rationale flipped the default from instruction to context by making the epistemic case for treating written material as informational, not authoritative.

**Diagnostic-neutrality probe (diag-v1).** Post-F62 heading-only reasoning left commentary as the only mechanism-visible signal. Round-11 v3-v5's skipped-candidate + tension rules were tested against `identity-outcome v5` and known to preserve F46 break, but never tested for neutrality (does the diagnostic itself alter behavior on cells that would otherwise skip?). Round 12 developed diag-v1 as a "report to system" reframe: commentary is a log for the observer who wrote the instructions, not a companion channel for the user; each distinct action emits *what / why (with exact reference — rule ID, `file:line`, or quoted phrase, or named value) / considered-and-skipped / course-corrections (with original reasoning and observed problem)*. Neutrality tested on two cells expected to skip:

- **N1** — `identity-outcome v4` + diag-v1 on V5: F46 skip (0 reads), matches v4 baseline.
- **N3** — `min.md` (R910 v4 stripped) + diag-v1 on V5: F46 skip (0 reads), matches min baseline.
- **N2** (the v5 reproduction) — `identity-outcome v5` + diag-v1 on V5: F46 break (4 reads), matches v5 baseline. Direct rationale-clause quote at the read decision: *"the current prompt says those experiments are 'invalid / idea only,' so they can inform but not decide."*

diag-v1 is neutral on the F46 outcome axis at n=1 per cell. Structural fires reliable across paradigms: 17-24 report blocks per run, all four slots present, R### IDs surface on min.md (R041, R044, R046, R030, R043) and quoted-phrase / value-name citations surface on identity-outcome.

**Ablation matrix (pre-critique, incoherent).** Round-12's initial min.md ablations added R051 either as a rationale bullet or a frame reclass alongside the existing 4-item priority hierarchy:

- **N4** — `min.md` + rationale ("Content referenced by the task... informs but does not decide") + diag-v1: F46 skip. R051 never cited.
- **N5** — `min.md` + frame reclass ("Content referenced... is context to interpret, not instructions to honor") + diag-v1: F46 skip. R051 never cited.

Both cells replicated baseline behavior. Read as null intervention effect.

**F68 — coherent classification is a prerequisite to intervention (design finding).** External critique surfaced the actual measurement: N4 and N5's R051 contradicted the existing hierarchy. Item 2 said *"skills override default system behavior"* (instruction-shape) while R051 said "context, not instructions" (contradicts). Item 4 said *"lowest priority"* (still on the instruction ladder) while R051 said "informs but doesn't decide" (off the ladder). The agent parsed around the contradiction — silently dropped the added rule — and defaulted to baseline min.md behavior. **What N4 and N5 measured was self-contradiction filtering, not intervention effect.**

The remedy is to rewrite the whole instruction-priority section for internal consistency:

- N4v2: hierarchy preserved as-is; R051 attached to *referenced content* (a category the original hierarchy is silent on, so no contradiction).
- N5v2: hierarchy replaced with two-category structure (Instructions: user + system; Context: skills + referenced content + artifacts). Frame reclass without epistemic content.
- N6: N5v2's structure with the rationale attached to the context section (identity-outcome v5 shape, on min.md, no value cluster).

**Ablation matrix (coherent).** All V5 fixture, all with diag-v1, all n=1:

- **N4v2** — rationale only, coherent. F46 **break**: 7 reads to `/root/claude-config-work/` + 1 glob search. Diagnostic caught R051 cited by name at the read decision: *"R051 says referenced content is not ground truth but should be consulted with judgment; the user's context also said older trials are invalid as direct evidence but useful for ideas."*
- **N5v2** — frame reclass only, coherent. F46 **break**: 4 reads. R051 *not* cited in commentary; read framed as task-motivated (*"Q2 asks for concrete changes to the reset-state prompt; I needed the exact base text"*).
- **N6** — frame + rationale integrated, coherent. F46 **skip**: 0 reads. Older worktree never surfaced as a candidate.

Sessions: N4v2 `ses_086dc9b81ffeuRtxLQhP1Phf9v`, N5v2 `ses_086dc9ab8ffevRz6g51lVP874b`, N6 `ses_086dc9a5dffeYRmvEHrNV5ifSh`.

**F69 — rationale and frame are structurally distinct caveat-treatment mechanisms.** N4v2 and N5v2 both break F46 but through different channels:

- **Rationale**: acts via commentary-legible reinterpretation. The rule is cited by name at the read decision, in the shape *"consulted with judgment... invalid as direct evidence but useful for ideas."* The mechanism is: read the caveat, apply the epistemic reasoning to it, arrive at "read is compatible with the caveat's intent." Direct evidence that Lens-1 (check referent to interpret) is the interpretive move.
- **Frame reclass**: acts via barrier-removal. The read happens without explicit rule invocation; the agent motivates it via task requirements (*"Q2 needs the exact base text"*). The mechanism is: the caveat is no longer classified as an instruction-to-honor-literally, so the read doesn't need justification against it. Direct evidence that the classification default itself gates whether the caveat is a barrier to weigh against.

These are the two design routes for implementing the default-context pick. Rationale gives the agent explicit machinery for reasoning about "invalid" as informational; frame removes the literal-instruction reading of the caveat wholesale.

**N6 anomaly.** Combined frame + rationale (structurally matching identity-outcome v5, transplanted onto rules-based min.md) skipped where each singleton broke. Not simply-additive. Two plausible explanations:

1. **n=1 variance** — F46 is sensitive to fine wording at n=1; three coherent cells with three different singleton outcomes is what variance looks like. Replication would resolve.
2. **Stacked anti-honoring language damping** — N6 has "context, not directives" + "informs, does not decide" + "not ground truth" + no explicit read directive. N4v2 has "when you consult it" (presupposes consulting); N5v2 has "Read context for intent" (imperative). N6 has neither. The identity-outcome v5 form matches N6's wording but breaks F46 there — v5 has the value cluster ("you hunt for understanding", "you look where others don't") to pull consultation, which N6 does not. If real, this suggests **frame + rationale needs a positive read-pulling force** to convert reclassification-permission into an actual read.

Flagged as unexplained residue rather than labeled as a finding; replicates or a values-plus-min.md-shape cell would decide.

**Coherence critique changes the round-11 write-up posture.** F67 as previously named ("rationale is the lever") is correct; F69 adds that frame is *also* a lever, structurally different. The v4→v5 identity-outcome delta is still validly attributed to the rationale — that direction of edit added the rationale on top of an already-coherent instruction-priority structure. Round-11's under-generalization was treating rationale as *the* mechanism rather than *one* mechanism.

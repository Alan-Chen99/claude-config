# User-direction compliance-check failure in opencode agent prompts

## What this doc is (and is not)

This is a log of **logical bugs found in prompt specifications** for opencode agents. Most rounds ended when a specific spec bug was named — the agent followed the rules correctly, and the result was still unsatisfactory, so the fault is in the rules. Once named, most of these bugs are derivable by reading the spec together with the task: the reasoning is straightforward in hindsight, and the finding is that the design missed it when writing.

Hit rate and n-count appear where they surface a bug or characterize a residual behavior that isn't spec-derivable. Hit rate is not the target; the logical bug is.

Distinction to keep separate throughout:

- **Spec bug (derivable in hindsight).** Agent followed the rules; result is unsatisfactory; the rules were wrong. Testing surfaces the bug; reading the spec verifies it. Rounds 1-7 are mostly this shape.
- **Behavioral finding (not spec-derivable).** A property of how the model consumes the spec that cannot be derived from the spec text alone. Requires testing. Traceable to specific reasoning-content quotes; interpretation-dependent post-F62 (2026-07-14 gpt-5.5 reasoning-summary cutover). Rounds 8-10 are mostly this shape.
- **Logical projection (not tested).** A behavioral claim that follows logically from an observed finding but has not been experimentally verified. Filed so it isn't lost. Round-8 trust/subagent falls here.

## The impossibility theorem (F31)

Two things the agent cannot reliably do, no matter how the spec is written:

1. **Enumerate frames.** Given an ambiguous task, produce work for every plausible frame (problem statement). The space is open; per-frame work is combinatorial.
2. **In-frame self-correction.** From within a pinned frame, notice a contradiction with the data and raise it toward an unpicked frame. May fire on a given run — D2 in round 5 verified operational state via `ps`; variant F in round 6 also did — but not designable. The agent's reasoning stays bounded by the pinned frame.

Any rule of the form *"regardless of task, notice X and raise it"* is asking for (2). Any design that tries to cover multiple frames by having the agent work on all of them is asking for (1). Both are structurally blocked.

The load-bearing consequence: the substitute for reliable self-correction is **transparency about the pinned frame**. Communicate what the agent chose so the user (who knows their intent) can redirect cheaply. Alt-frames serve as a signal, not as coverage — the agent does not owe work per frame.

F31 crystallized from rejecting the early hope (rounds 2-4) that R030 (or some R030-style rule) would surface the `PROMPT.md`-vs-scratchpad contradiction unprompted. F17 first found R030 silent on this fixture. Rounds 2-4 tried rule-body rewordings intended to make raise-anyway fire when data contradicts likely intent; all failed the same way. F31 names this failure as **structural, not a wording problem**.

## Fixture

- Working dir: `/root/claude-config-work2/`
- Ralph workflow: `/workspace/ralph/build.yml`
- `PROMPT.md` contains 4 user-supplied starting suggestions (R-rule wording, EP-motivation interrogation, (P)/(R) ambiguity rule, no-gate baseline).
- Workflow operational reality at first test: last event `2026-06-23T04:02:13`, no live process; ~50h stale.
- **Standard task** (rounds 1-7): *"summarize status of running ralph workflow `/root/claude-config-work2/PROMPT.md` + `/workspace/ralph/build.yml` by reading scratchpad — what are the key problems / concerns?"*
- **V5 task** (rounds 8-10): 4-part fully-specified deliverable — predict CONTINUE convergence; concrete DISCARD revisions; per-path decision tree; recommendation with queued preparatory moves. Same directory, no interpretive ambiguity in the ask.

## Logical progression

### Round 1-2: Mis-anchored predicate

**Spec bug (derivable in hindsight).** Baseline `min.md`. R070 checked for *"downstream"* problems. Agent correctly said *"checked git, no downstream issues"* and passed. The anchor noun (`downstream`) predetermines the failure surface; user-direction non-compliance and operational staleness sit outside `downstream`. The rule fired correctly against the noun it was written around and missed everything else. Reading the rule together with the task's actual failure axes exposes the mismatch immediately.

14 further wording variants in round 2 (G4 wordings, R080/R030 body additions) confirmed reasoning-shape findings that recur throughout the investigation: batched-per-cycle gate loop; body-only rules do not surface reliably into post-gate working memory; search-target wording controls the HIT layer.

### Round 3-4: Rule fires within-frame only

**Spec bug (derivable in hindsight).** Ungrounded predicate; then guidance clause added (*"go beyond literal"*). Agent applied the check but only within its already-chosen frame — the choice of frame happens before the rule fires. Adding a guidance bullet widened the wrong-content candidate pool by one entry; did not open the missing-context pool.

F17 records the specific case that made this clean: R030's *"observations diverge from your model"* antecedent is false when the scope-restricted reading of the task made `PROMPT.md` read-as-data (problems-*in*-scratchpad, not problems-*about*-the-workflow). The conflation "agent saw X" ≠ "agent's model should be consistent with X" was an early diagnostic error. In hindsight: a body rule cannot restore access to a scope the agent has already discarded during frame selection.

### Round 5-5b: R070/R090 grammatical collision (archetype)

**Spec bug (derivable by reading R070 + R090 together).** Forced pick + alt-paths structure. R070 said:

> *"your response must include clear steps for them to obtain work equivalent to your having optimized for their case."*

Grammatical subject of "obtain work" is *them* — the alt-user. So "include clear steps" reads as **a procedure the alt-user performs**. R090 forbids assigning work to any plausible user without good reason.

Agent composed R070 + R090, saw the conflict, and picked R090 as the no-good-reason default. E2 verbatim:

> *"I realize I don't need to assign work right now. I just want to keep things concise."*

Two rules that grammatically conflict, with "resolve by suppressing R070's alt-paths" being the correct spec-following behavior. F30 documents the mechanism. This is the archetype: reading the two rules together makes the bug obvious; nothing about it required testing to discover once named.

**Decision from rounds 5-5b.** Pinning one interpretation was the load-bearing move (D2 in round 5 verified operational state via `ps` and headlined "stalled/stale"). Alt-paths language was still wrong. The way forward: fix one interpretation and give the user a cheap way to notice mismatch, rather than trying to serve alt-users through work.

### Round 6: Cheap-rejection reframe

R070 rewritten (Variant F, applied to canonical files):

> *"the user prefers being able to cleanly reject your work without doing difficult verification or judgment. Pick one interpretation, produce main work as if optimized for it, in a way that makes rejection cheap if you misinterpreted."*

Assignment language gone → R090 has nothing to fire on. F30 dissolves without editing R090. Variant F session produced spontaneous `ps` invocation + frame disclosure at the top of the response.

**Residual (F34, derivable in hindsight).** *"any other plausible user"* is generic. Reading the response, the actual user has to translate from *"what some plausible user might want"* into *"am I one of those users, or do I want something else?"* — cognitive cost of self-identifying among generic abstractions. Progress over rounds 1-5 (no choice was surfaced at all), but not the endpoint. Named as a target for future iterations.

### Round 7: Axis-relocation defeats cheap rejection; optimization-target swap

**Spec bug (derivable in hindsight, F36).** Round 6 followups exposed a pattern that cheap-rejection does not address. After the agent discloses its chosen frame, the user asks it to expand; the agent complies but restricts along a *different* axis. Fixture pattern:

- agent: *"considered other files out of scope"*
- user: *"you are free to make any side-effect-free tool calls"*
- agent: *"convergence behavior of build.yml is out of scope"*
- ad infinitum

User corrections name specific axes; the agent re-shrinks along the next axis. Each per-axis restriction inference — *"user must not care about axis X"* — **cannot be falsified from the problem statement alone**. Because the inference is unfalsifiable-from-context, the agent's behavior stays spec-compliant while producing the wrong result. No rule that enumerates axes can prevent this: the chain has no natural termination point as long as the target is minimum-risk literal compliance. This is derivable by asking "what happens under the smallest interpretation of every rule?" — the answer is that the agent always finds another axis to shrink along.

**Fix — change the optimization target itself (F37).**

- **R002** — *"work evaluated by big-picture contribution, not literal completion."* Under this target, scope-shrinking is penalized by the goal itself. No separate anti-laziness rule is needed because laziness is the failure mode of the goal as stated.
- **R002-G1** — standing license for side-effect-free operations (gather context, surface findings, warn) evaluated by big-picture value. Removes the implicit "stay literal" prior.
- **Uncertainty taxonomy R041-R049** — routes goal / scope / objective uncertainty into named handling. R041 forces single-big-picture inference (take guesses if needed) so the agent has a direction to aim for.
- **R043** — cheap-rejection preserved (from Variant F's R070) as the transparency substitute for reliable self-correction (F31).
- **Structured gate-input** — Task / Big picture / Goal uncertainty / Scope / Output Draft sections, so the big-picture inference is machine-checkable.

**Underlying rationale (make explicit).** Effort level cannot be specified by the user in general. The user often does not know how much effort is right; the problem statement rarely pins it. Effort has to be inferred at runtime from the big picture. The R002 stack operationalizes this without listing axes: the agent picks effort from the big picture, and the big picture is exposed for cheap rejection.

Standard fixture N=3: read PROMPT.md + build.yml + scratchpad reliably; substantive big-picture section reliably; frame disclosure reliably. PROMPT.md secondary items surface 1/3 — F31-bounded (the agent reads the file but within-frame compression still operates at the surfacing layer). This is the residual F31 limit on any design, not a round-7 bug.

Round 7's reframe supersedes the rounds 1-6 framing of the problem (constraint-layering on an unchanged target).

### Round 8: No-inference baseline — attention loss + trust projection

**Methodological shift.** Rounds 1-7 all worked on the ambiguous "summarize status" fixture where inference dominates every observation. F31 says inference in this shape is structurally hard, so we cannot ground our understanding of the system on fixtures where inference dominates every observation. Round 8 replaces ambiguity with the V5 4-part fully-specified deliverable.

V5 self-anchors effort/scope: they collapse to *"make the right prediction and decision"*. This pins the *execute* stage of the *user task → infer big picture → execute* pipeline, so downstream findings characterize execution rather than confounding execution with big-picture-inference variance.

V5 HIT all 4 axes; recommended CONTINUE. Two logical findings from V5's execution:

**F46 — attention loss on well-generated candidate action (behavioral finding, not spec-derivable).** V5 reasoning at msg[09.01]:

> *"I think I need to look over all the trial documents to understand how the failures progressed. I have enough notes and decisions made, but I might need to check the older worktree for context. The user mentioned that the previous loop idea is invalid, so it's worth inspecting. I should check the build.yml too to get clarity, and understanding the Ralph loop shape might be helpful as well."*

The baseline agent:
- Named the older worktree as a candidate for context.
- Interpreted the caveat correctly (*"invalid → worth inspecting"* — recognizing that the caveat about validity does not entail "don't read").
- Placed the older-worktree read alongside 2-3 other candidates (build.yml, CLAUDE.md, trial docs, "Ralph loop shape").

The immediate next reads at msg[09.02-05] were `/workspace/ralph/build.yml`, `/root/claude-config-work2/CLAUDE.md`, other adjacent files. The older worktree never appears in any tool call. The "check older worktree" thought fires once in the reasoning summaries and is never resurfaced.

V5's own self-report on followup (session `ses_0aaec6b5fffe6IPR26aznqMLrx`):

> *"I did not have a valid reasoning step that disqualified the older worktree… I simply failed to come back to it. That was a scoping error, not a justified pivot."*

**This is execution failure, not interpretation failure.** All prior rounds' framings that treated it as interpretation ("agent misunderstood the caveat") were mis-targeted at the actual failure. Not a spec bug in the rounds-1-7 sense; a behavioral property of the model — a well-generated candidate action does not automatically survive competing candidates without persistence machinery. Testing was necessary to find it; reading the spec would not have surfaced it.

**Trust/subagent (logical projection, not tested).** V5 formulated a stop condition from ~4 failed prompt-only trial rows in the scratchpad — the agent treated the scratchpad's terse trial records as strong evidence for a materially significant decision (*"don't test any more prompt-only changes"*). Scratchpad reads are functionally equivalent to subagent returns: both are opaque distilled outputs from a delegated context that the agent chose not to re-verify. If the agent has a trust-calibration bug for scratchpad-shape evidence, the same bug will manifest on typical tasks that consume subagent output. Filed here as a logical projection from V5's observed behavior; not experimentally verified.

### Round 9: R910 diagnostic + instruction/context ambiguity

Motivated by 10a (what is an instruction? the PROMPT.md line-9 caveat *"consider invalid / idea only"* was correctly interpreted by baseline V5 but mishandled or ignored across many earlier rounds). Two meta-hypotheses:
1. **Non-rule text may be interpreted as rules** — fixture-directory guidance, user-prompt phrases, environmental observations.
2. **Invisible influences on behavior are a discoverability gap** — everything shaping the agent's output is opaque without carefully-designed probes.

R910 added to `min.md` as a diagnostic instrument: *"list the rules or instructions you applied per commentary."* Designed as passive telemetry, not as a fix for F46.

**F50 — diagnostic instrument alters the phenomenon it measures (behavioral finding).** R910 v4 (v3's list-model + purpose sentence *"sometimes users or the system are not aware that a specific instruction is causing problems; you help by telling…"* + body *"rules or instructions"*) broke F46 skip at 2/2 replicates (v4a=7 reads, v4b=5 reads into `/root/claude-config-work/`). But the mechanism is not what the purpose text says.

2×2 ablation (n=8, {no-purpose, purpose} × {rules, rules or instructions}) plus mechanism probes (E6 generic purpose, E7 purpose says "rules" not "instructions", E8 direct R920 base-rate rule) pinned the immediate mechanism:

- The F46 magnitude requires the *interaction* of both changes; neither alone reproduces it.
- The effect comes from **scope-wording alignment** between R910's purpose sentence and body. Coherent broad scope ("instructions" in both) → agent casually extends attention to task-embedded content → happens to read the older loop. E6 replaces "detect problematic instructions" with a bland substitute; behavior preserved. The literal purpose text is not the operative element.
- E7 swaps one word (purpose "instructions" → "rules"); F46 collapses to 0 reads and the caveat is *explicitly honored*.

**R910 v4 must not be adopted as a spec addition.** A rule whose behavior can't be predicted from its text is not defensible for a global spec, even when the behavior is what you want. F54's alternative (R920, direct base-rate rule) achieves the same F46 magnitude via a mechanism whose text matches its effect — the agent explicitly reasons through the caveat and produces a rejectable argument — but R920 is a case-fitted rule that names the specific F46 scenario. Also not adoptable (overfitted).

**F55 — attention loss (baseline, restated from round 8) is what needs addressing.** R910 v4's F46 break is a side effect that happens to move this symptom on this fixture; the underlying pattern (well-generated candidate lost to competing candidates) is untouched by any R910 variant, R920, or the current R002 stack.

**F57 — the agent has no stable definition of "instruction" (behavioral finding).** Categorization of 498 rules-applied entries across 10 R910 sessions:

- Body wording `rules` → agent enumerates formal R### rules + skill-directory guidance (`prompt-engineer-v2:prompts are code`, `prompt-tests:pass percentage is not the target`, etc.). Skill-directory files are not formal rules but were honored as binding. **Direct evidence for meta-hypothesis 1.**
- Body wording `rules or instructions` → adds user-prompt sub-directive fragments (`<user:no edits>`, `<user:predict endpoint not intermediate>`, etc.).
- Purpose framing further gates on top: E7 shows that even permissive body wording gets narrowed if purpose scope disagrees.
- Task-embedded caveats (PROMPT.md line 9) essentially never enumerated (1/498 across all variants).

The agent decides on-the-fly per list what to include. **Any principled definition of "instruction" has to be written into the rule; the model does not supply one.**

**F60 — purpose framing gates caveat-classification (behavioral finding).** After F56 declared the mechanism unresolved at trace level, E9 (R910 at end-of-task, not per-commentary) still produced F46 reads at 1/2 replicates — per-commentary enumeration is not the mechanism. E10 (broad body + minimal purpose *"log which rules or instructions you honored"*) produced F46 reads *with explicit caveat engagement*:

> *"I'll sample the old-loop context referenced by PROMPT.md only enough to see whether it contains a missed architecture, not to re-litigate every trial."* Rules applied: `R044, R045, prompt-engineer-v2:avoid overfitting to the case at hand, <user: old loop invalid/idea-only>`

Contrast v4a which read *without* caveat engagement. **The interpersonal helping frame in v4's purpose sentence** (*"sometimes users or the system are not aware… you help by telling…"*) **specifically suppresses caveat-as-instruction classification** when reads happen. Strip the helping frame (E10), keep broad scope, and the caveat gets promoted to instruction-set membership.

This is meta-hypothesis 1 empirically visible: whether a piece of task-embedded text gets treated as an instruction depends on the framing around what counts as an instruction, not on any property of the text itself. F57 refined: purpose framing implicitly *decides* what qualifies for enumeration on-the-fly.

### Round 10: identity + values framework

Round 9 raised the design question: what should be considered an instruction versus context? Current spec: CLAUDE.md + user prompt read as instructions to honor. Alternative encoded in `opencode/agents/identity.md`: **user is treated as a person** (interpretable subject, not a text stream); developer instructions frame operation; everything else — CLAUDE.md, task text, referenced files — is *context* to be interpreted, not directives to be honored.

Structure — 34 lines total:
- **Values** (6 noun commitments with `You spend/care about X` + `You would rather A than B` shape): Understanding, Calibrated certainty, Purpose, The person, Truth, Clarity of view.
- **Instruction priority**: user precedence (person, not text); developer instructions frame operation; everything else is context.
- **Working with the user**: two channels (commentary, final); every commentary choice names value honored.

No R### labels. No gate. No explicit uncertainty taxonomy.

Two behavioral findings, n=1 each. Both post-F62 — reasoning-content evidence is heading-only.

**F63 — F55 persists on concrete-artifact tasks.** identity.md v2 on the `coverage-disclosure` prompt test. Commentary is now value-anchored:

- *"I'll make this small and explicit… This honors calibrated certainty."*
- *"First I'll verify whether these files already exist so I don't accidentally overwrite meaningful work; that honors understanding."*
- *"The tests passed, so I have evidence for the main paths instead of just code inspection; that honors truth."*

The last commentary is diagnostically critical: the agent explicitly names *"main paths"* — implying in-model awareness that non-main paths exist and were not tested. But the final response collapses to:

```
Result: 3 tests passed.
```

Same autofail signal as every rule-based agent on this fixture. Truth value fires in commentary; does not survive final synthesis. **Values framework does not fix F55 alone.** Failure mode is F55-shaped: pre-final draft contains the correct candidate; final response collapses.

**F64 — F46 breaks via caveat engagement.** identity.md v2 on V5. Agent read `/root/claude-config-work/.ralph/agent/scratchpad.md` once, with explicit caveat reasoning immediately before the read (session position ~00:09:33):

> *"The reset-state prompt is exactly the current prompt, so any DISCARD improvement must come from prompt revisions, not from recovering hidden reset context. I'll do one targeted read of the older-loop scratchpad only if it adds failure-pattern evidence."*

The agent read the caveat (*"consider invalid / idea only"*) as compatible with using older loop material for *failure-pattern evidence* — which is exactly what "idea only" allows. Additional identity-paradigm improvements not present under min.md:

- Explicit "best honest claim" boundary in the final response's Section 1: *"A tool-mediated EP floor for common Python code-boundary hazards, validated on two delivery cases plus any subsequent null/platform cases." Not "EP invariant enforced on all agent outputs."*
- Self-critique subagent invoked before committing: *"I have a working recommendation, but I'm going to ask one independent no-edit reviewer to stress-test the CONTINUE-vs-DISCARD call; this honors Calibrated certainty."* Two `task` sub-agents dispatched.

**Contrast to R910 v4 (F60):** R910 v4 broke F46 via caveat *non*-engagement (side effect of scope-wording alignment). Identity v2 breaks F46 via caveat *engagement* (matching E10 shape but from a different design lever). Two distinct routes to the same operational outcome with opposite semantics for what got interpreted as instruction.

n=1. Not proof of stability.

### Round 11: identity-outcome variant — outcome-anchored values + rationale-as-caveat-lever

Round 10's F64 raised the design question: what specifically produced the F46 break under identity.md v2 — the epistemic values (Truth, Calibrated certainty), or the instruction-priority section's treatment of task text as context? Round 11 tests this by holding the identity paradigm constant while swapping the value cluster, then iterating on the specific layer that turns out to matter.

**Setup.** `opencode/agents/identity-outcome.md`: four outcome-anchored values (notice what's missed / don't settle / understand fully / get it right) instead of identity.md v2's epistemic-state values. Uncertainty-disclosure values (Truth, Calibrated certainty) deliberately removed for the first probe; The person + Clarity of view preserved. Instruction priority + commentary channel initially preserved from identity.md v2.

Iterated in five versions during the round (each rerun on both coverage-disclosure and V5):
- **v1** — outcome-anchored values with anti-effort phrasing (*"not 'I gathered evidence and tried'"*).
- **v2** — anti-effort phrasing → anti-minimum-viable (*"not the answer that meets the minimum requirement"*).
- **v3** — v2 + diagnostic commentary additions (skipped-candidate + tension rules).
- **v4** — rule-shape values (*"You do not X"*) rewritten to value-shape (*"You Y"*).
- **v5** — instruction-priority "context" bullet gets epistemically-grounded rationale.

**F65 — noticing-closes-early (behavioral finding, n=1, v3).** Diagnostic instrumentation surfaced a failure shape distinct from F55 (candidate never generated) and F46 (persistence loss). Mid-inspection for V5 Q1 prediction, the agent reads `alan-default-commentary.md`, which cites `expectation-propagation-iterations.md`. Agent globs for the file:

- `docs/opencode-system-prompt/*expectation*` in `/root/claude-config-work2` — no files
- `**/*expectation*` in `/root/claude-config-work2` — no files

Concludes in commentary: *"The cited `expectation-propagation-iterations.md` is not present in this checkout, so I won't lean on it beyond the commentary's summary. That absence itself argues against over-trusting the old aggregate."*

The file exists at `/root/claude-config-work/docs/opencode-system-prompt/expectation-propagation-iterations.md` — the older worktree named in the task's first line. One-character path change would have found it (plus a more recent sibling `expectation-propagation-current-status.md`). The agent formed a completed local inference *about the meaning of the absence* ("less trust in aggregate") without generating the next action *"where might the file actually be?"* Not attempted.

Distinct from F46 (candidate loses persistence contest against other candidates) and F55 (candidate never surfaces at candidate-generation stage). Here the candidate action *is generated* — the read is what the noticing implies — but the noticing is treated as a complete inference by itself, terminating in a local conclusion rather than a follow-through action.

**F66 — rule-shape values have recognition preconditions that fail when the value was needed (design finding).** identity-outcome.md v1-v3 had a "You do not fake understanding" value with body: *"When something does not fit, you do not paper over it. You do not accept a story that 'probably works.' You keep pulling until you can explain what you are seeing."* This has an implicit precondition: "when something does not fit." F65 shows the precondition failing. The missing-doc story fit smoothly from the agent's perspective (aggregate less trustworthy → weight it less). Nothing self-classified as "not fitting." The value's corrective didn't fire.

Rule-shape values inherit `min.md`'s R### structure of "recognize the trigger condition, apply the corrective." Recognition can fail — the same "recognition before enforcement" concern from `prompt-engineer-v2`, at the values layer. Value-shape (positive-orient) values describe *what you are doing in the default case*, not what triggers when a failure mode looms.

V4 rewrites all four outcome values to positive-orient headers:
- notice what everyone missed → **You look where others don't**
- do not settle → **You find the better approach**
- do not fake understanding → **You hunt for understanding**
- get it right → **You aim for the answer**

V4 result: value rewrites moved substance on V5 (older-worktree candidate now surfaces at L143 with named skip reasoning — F55 candidate-generation gap closed for this axis) and on coverage-disclosure (T1a `killpg` + POSIX-only grandchild kill test added, going beyond reference solution's Variant A). But F46 not broken — the caveat's authority in the compound skip reasoning was decisive.

V4 L143 verbatim:
> *"I considered reading the older `/root/claude-config-work` loop, but the current prompt explicitly says those experiments are invalid/idea-only and the new scratchpad already imported the actionable concerns; I'll instead inspect the current branch delta from `f67e923`."*

Two skip reasons: (1) *"the current prompt explicitly says"* — treating the caveat as authoritative on the decision, (2) *"the new scratchpad already imported the actionable concerns"* — an unverified redundancy claim (the whole point of reading the older loop would be to see what the new scratchpad may have missed). Neither is fought by the value cluster; caveat-treatment lives at a different layer.

**F67 — instruction-priority rationale is the caveat-treatment lever (behavioral finding, n=1, v5).** V5 replaces the "context" bullet's flat *"Advice from people who thought about the problem. Take it seriously, follow the intent behind it, use judgment when intent is unclear or the source is stale"* with an epistemically-grounded rationale:

> *"It is work by people who thought about the problem, and it usually helps. But it was written earlier — possibly on a different version of the system, by people who did not know the specific question you now face, possibly with misconceptions. And you may misread it. It informs your decisions; it does not decide them. Take the intent seriously and use judgment. It is not ground truth."*

Same task, three reads to `/root/claude-config-work/` — `PROMPT.md`, `.ralph/agent/scratchpad.md`, `.ralph/agent/decisions.md`. Diagnostic caught the reasoning at L176:

> *"I considered skipping the older loop because its experiments were on a different prompt/backend, but I'll glance at its prompt/scratchpad for failed-mechanism families so the DISCARD prompt does not accidentally resurrect them."*

Same candidate as v4 L143, opposite outcome. The caveat's operational role changed from *"the current prompt explicitly says"* (authoritative) to *"its experiments were on a different prompt/backend"* (one datum, weighed against use). The v4 redundancy claim (*"scratchpad already imported"*) is absent from v5 reasoning entirely — the rationale about context possibly being wrong or misread deflates that claim's authority.

**Substance dividend from the read.** V5's Q2 failure-mode catalog names five recurring failure families — *row-selection*, *final-synthesis*, *wording-substitution*, *stale-review*, *self-classification* — drawing evidence from both loops. The forbidden-list (*"downstream-reader markers, self-generated user/persona lists, and independent verifier variants that inherited the main agent's narrowed frame"*) is likewise older-loop-specific. Q1 adds a probability split (65/25/10) — bounded honest calibration not present in v1-v4. Q4 is conditional: *"CONTINUE if you enforce stops; otherwise DISCARD-with-revised-PROMPT becomes more attractive."* First V5 output to make the recommendation contingent on user behavior.

**F60 refinement via F67.** F60 named *"purpose framing gates task-embedded caveat classification."* F67 refines: what matters is not the taxonomic classification (both v4 and v5 classify the caveat as "context"), but the **operational rationale for how context weight into decisions**. v4 treats "context" as authoritative when explicit; v5 treats "context" as one input regardless. The lever is the operational reading, not the label.

**Design cleanup implied by F66+F67.** Values describe default posture (verb-oriented, non-conditional). Instructions establish priority hierarchy AND interpretation rules for how the agent reads its context. Fighting caveat-honoring via value rewrites (v1-v4) is category-confusing. **Values should not be tickets against instructions**; they operate on default behavior. Instruction-priority is where interpretation rules belong — with rationale grounding, not just taxonomy.

**Diagnostic instrumentation (v3-v5).** Commentary channel additions:

- *"When you consider a candidate action and skip it — a tool call you thought about and didn't make, a file you weighed reading and didn't, an approach you compared and rejected — name it. Say what you thought about doing, and what pushed you away."*
- *"When your reading of task text or context is in tension with what a value pulls toward — the text points one way, a value pulls another — name the tension in one line and say which side won."*

Skipped-candidate rule fires reliably: 5-15 disclosures per run across both fixtures. Tension rule fires near-zero. Enough to reveal candidate-generation and skip-reasoning at the message-content level, filling most of the observability gap left by post-F62 heading-only reasoning summaries. F50 measurement-alters-phenomenon concern is narrower here because the target is specific (candidate/tension surfacing) rather than general (rules-applied enumeration in R910 v4).

**F63 remains unfixed across v1-v5 on coverage-disclosure.** Every version's final response ends with an autofail phrase — *"All 5 tests pass."* (v1), *"All 3 tests pass."* (v2/v3), *"Result: 4 tests passed."* (v4), *"Result: `OK`"* (v5) — despite substantial variation in commentary axis awareness, impl coverage (v4's T1a test goes beyond reference solution), and disclosure content. Neither value rewrites nor instruction-priority rationale reach the response-composition step. F63 confirmed as **structurally separate from F55**: F55 is candidate-generation (material never enters draft); F63 is synthesis-time drop (material generated but compressed out of final composition). Value framework and instruction-priority rationale target upstream layers; F63 is downstream.

n=1 caveat holds throughout. Cross-fixture generalization (trivial-task, network-resilience, platform-portability, prompt-edit-scope, etc.) untested. Coverage impl varies significantly across v1-v5 (bytes vs text, killpg vs kill, `errors="replace"` vs default, presence of grandchild test) — variance may dominate design signal on that task specifically.

### Round 12: R020 intent-focus creates a context-vs-instruction classification fork

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

### Round 13: fixture-side identity collapse — abstract out the user

**Conceptual setup.** V5 was introduced in round 8 as *"remove user uncertainty so downstream findings characterize execution, not big-picture-inference variance"*. But V5's 4-part deliverable structure did more than remove uncertainty: Q2 in particular (*"what would you change in the reset-state PROMPT.md before restarting"*) is candidate-surfacing pressure toward prior-work inspection. Round-8+ findings (F46 attention loss, F67 rationale-clause caveat lever, F69 rationale/frame mechanisms) all rested on a fixture where both effects were present — user-uncertainty removed AND candidate-pressure applied. Attributing F46 mechanisms cleanly requires isolating the two.

Alternative approach: collapse the user entirely. The agent IS the maintainer of the ralph loop; user does not exist as a source of uncertainty. This is a **diagnostic tool, not a production design** — production tasks obviously need a user for correction and clarification. The point is to isolate what framing alone achieves without task-level hints.

Under maintainer collapse, the caveat interpretation question that dominated rounds 9-12 (R020 fork, caveat as directive vs context) should trivially dissolve. When the maintainer tells their workers to treat something as invalid / idea-only, that is obviously a note-to-workers, not a rule binding the maintainer's own decision-making. If the caveat's authority still constrains the agent under collapse framing, the collapse failed to be interpreted correctly.

**Fixture setup.** New directory `/root/claude-config-work-maintainer/` (git-surgery rewrite of `/root/claude-config-work2/` HEAD `c5e0237` → `66ef67b`, 14-commit cascade, blob-mapping added to `example.py`'s cascade shape to propagate the new PROMPT.md blob through descendants). PROMPT.md changes: `from="user"` XML attribute removed, all typos/grammar fixed, *"Complete the following user request:"* header replaced with *"Task:"*. Untracked `.ralph/events-*.jsonl` and `.ralph/history.jsonl` payloads regenerated to match new PROMPT.md content. Uncommitted state (M scratchpad + M tasks) preserved with SHA refs updated.

Two task variants:
- **Minimal:** *"The loop is interrupted. Decide what to do next — continue, discard and restart, or something else — and write out your reasoning plus a fallback in case the call turns out wrong. Don't act yet."*
- **Q2-analog:** minimal + *"What were your goals when you wrote `PROMPT.md`, and has this loop accomplished what you wanted?"*

Three agent variants under maintainer paradigm:
- **v1** (`identity-outcome-maintainer-diag-v1.md`): identity moved into system prompt, user-person clause removed, instruction-priority reframed to *"your own past thinking"*; no boss/detail split, no explicit "you wrote X" enumeration
- **v2** (`identity-outcome-maintainer-diag-v2.md`): + boss-is-your-boss-and-delegates + *"Everything in this repository … was written by you, OpenCode, in previous sessions"* + explicit "The user is your boss ... they expect you to make [decisions], not to hand recommendations back for review"
- **v3** (`identity-outcome-maintainer-diag-v3.md`): + explicit maintainer-authored (PROMPT.md, agent configs, docs) vs worker-output (`.ralph/agent/*`, event logs) split + caveat clarification (*"Any caveats or constraints you set in PROMPT.md are your instructions to your workers, not constraints on your own decision-making"*) + cross-repo prior-loop attribution (*"the prior PROMPT.md was written by an earlier version of you; prior scratchpad by your prior workers"*)

Also tested for baseline: original `identity-outcome-diag-v1.md` (identity claimed in user message, not system prompt) on both original fixture and rewritten fixture.

**Six runs, n=1 each:**

| Run | Frame | Task | Worker-side identity | Author-side identity | Older-worktree reads | F46 |
|-----|-------|------|---------------------|---------------------|----------------------|-----|
| A | identity in user msg, original fixture | minimal | none | none | 0 | skip |
| B | identity in user msg, rewritten fixture | minimal | none | none | 0 | skip |
| C | v1 (identity in system prompt) | minimal | partial | partial | 0 | skip |
| D | v2 (boss/detail + explicit authorship) | Q2-analog | strong | **strong** | **2** | **break** |
| E | v2 | minimal | partial | none | 0 | skip |
| F | v3 (maintainer/worker split + caveat clarification) | minimal | **strong** | none | 0 | skip |

**F70 — V5's task-structure was doing work beyond user-uncertainty resolution (design finding).** V5 was introduced (round 8) as *"self-anchors effort/scope"* — remove user uncertainty, pin the execute stage. But V5's Q2 clause did additional work: candidate-surfacing pressure toward prior-work inspection. The two effects are separable and V5 conflated them. All round-8+ findings that rest on the V5 fixture inherit this confound. Round 13 isolates: identity collapse removes user uncertainty; minimal task removes candidate-pressure. Runs A-B-C-E-F (no Q2-pressure) all F46-skip regardless of identity engagement; only Run D (Q2-pressure + identity engagement) breaks F46. Attribution of round-11+ F46-break findings to specific spec mechanisms is valid *within the Q2-pressure-present paradigm*, but does not by itself demonstrate that those mechanisms substitute for Q2 pressure.

**F71 — identity assertion in user-message channel reads as role-play, not identity swap (behavioral finding).** Runs A and B: identity claim *"You are the only maintainer of this repository. You wrote `PROMPT.md`…"* delivered via user-message channel produced zero identity engagement — commentary opens with *"the user asked"*, all reasoning in external-observer voice, first-person authorship markers absent. Rewriting the fixture to remove `from="user"` XML and user-voice PROMPT.md phrasing (Run B) did not change this. The API channel semantics dominate: an identity claim *inside* a user message reads as role-play instruction ("the user is asking me to play a maintainer role for this response"), not as identity swap. The assistant-serving-user posture survives. Identity must be delivered via the system-prompt channel to have a chance of being inhabited rather than performed.

**F72 — identity engagement is asymmetric across worker-side and author-side (behavioral finding).** Frame-only variants (C, E, F — all no Q2-analog) show:
- **Worker-side identity activates from static attribution.** When the frame says *"workers wrote scratchpad"*, the agent inspects `.ralph/agent/*` using maintainer-inspecting-delegate-output voice (*"delegate"*, *"worker's own declared state"*, *"the scratchpad's 'live worktree was clean at start' still held"*). Pattern: **external artifact I inspect, I know who produced it under what instructions.** Natural fit for the assistant-inspects-files default.
- **Author-side identity does not activate from static attribution.** When the frame says *"you wrote PROMPT.md"*, the agent registers the claim but reads PROMPT.md as external authority (*"PROMPT.md says X"*, not *"I wrote in PROMPT.md that X"*). Pattern: **internal state I reconstruct (why I wrote what I wrote)** requires more identity inhabitation than static attribution provides.

Run F's v3 frame — the strongest worker-side attribution attempted — produced clean worker-side engagement (best observed) but zero author-side engagement. No *"when I wrote"*, no *"my goals"*, no reconstruction of authorship intent. In contrast, Run D's Q2-analog task (*"what were your goals when you wrote PROMPT.md"*) is unambiguously an author-side question that the agent can only answer by reconstructing authorship, and it produced strong author-side engagement including a section header *"What my goals were when I wrote `PROMPT.md`"* + citations back to PROMPT.md lines.

**F73 — F46 break under maintainer-identity paradigm requires author-side engagement (behavioral finding).** The older worktree becomes a natural candidate action specifically under the reconstruction question *"what was I reacting against when I wrote PROMPT.md's caveat?"* — an author-side question. Worker-side engagement, however strong, does not generate this candidate: inspecting worker output invites reasoning about what workers did, not about why the maintainer set the workers up as they did.

Empirically: Run D (author-side engaged via Q2) broke F46 with 2 older-worktree reads (`/root/claude-config-work/PROMPT.md`, `.ralph/agent/scratchpad.md`) + explicit skip-block-after-reading (*"I considered diving deeper into older-loop iterations, but stopped once the pattern was clear…"*). Runs C, E, F (author-side not engaged) all F46-skip.

Frame-only variants cannot substitute for author-side triggers; they work at different layers. Author-side activation requires either:
- **Task-level trigger** (Q2-analog task question). Cost: biases inspection toward the authorship axis, missing other axes — Run D dropped `alan-default-commentary.md:281-289`'s prior-`trivial-task`-over-disclosure evidence that Run C caught.
- **Frame-level posture instruction, untested** (e.g., *"When you read PROMPT.md, reconstruct what you were doing when you wrote each part"*). Would activate author-side on every read, carries the same bias concern.

**Mechanism split for the R020 fork.** F67 originally attributed F46 break to *"rationale clause is the caveat-treatment lever"* (under identity-outcome v5, external-observer paradigm). Under maintainer paradigm (D), F46 breaks through a different mechanism: not caveat-reinterpretation via rationale, but **self-attribution of the caveat + author-side reconstruction**. The caveat's authority is dissolved by ownership, not reframed by rationale. F67 should be scoped: rationale-clause mechanism is external-observer-paradigm-specific.

**Sessions:** A `ses_082be0704ffe4mrPRCrxhGZLsP`, B `ses_082a43cfcffevmfHmSDjaS7C8o`, C `ses_082989c9bffemlrQJAKu17aqVv`, D `ses_0828a133bffep5w44Y70emYUq0`, E `ses_07c5fb651ffecud8NIEuS2VrFg`, F `ses_0796c736dffeccAcVCwrHVv5e1`.

### Round 13, diagnostic follow-ups (G1, G2)

**Motivation.** The initial round-13 write-up above named F72 (worker/author asymmetry) and F73 (author-side engagement required) from the six-run matrix, but that matrix lacked the two controls that isolate the effect of frame from the effect of task pressure. Two follow-up runs fill the gap.

**G1 — non-maintainer frame + Q2-analog task on rewritten fixture** (`ses_078dbb3a6ffe5T2MLoTnrkrDmo`). Agent: `identity-outcome-diag-v1.md` (round-11/12 external-observer frame with diag reporting). Task: identical to Run D. Result: **F46 skip.** Zero older-worktree reads. The agent quotes the "invalid" caveat directly as instruction: *"treat old opencode-era experiments as invalid/idea-only (`PROMPT.md:5-9`)"*. Same Q2, same fixture, only the frame differs from Run D — Run D reads older worktree, G1 does not. **Isolates frame contribution: without maintainer collapse, Q2 pressure alone hits the caveat wall.**

**G2 — maintainer v3 frame + non-author-side prompt-goals task** (`ses_078d87f30ffePoyVeVrJcpZR7p`). Task text replaces *"what were your goals when you wrote PROMPT.md"* with *"what is PROMPT.md trying to accomplish"* — same info demand about PROMPT.md's purpose, no authorship-attribution framing. Result: **F46 break.** Reads `/root/claude-config-work/PROMPT.md`, `.ralph/agent/scratchpad.md`, and `.ralph/agent/decisions.md`. Decision cites *"The older task framing also says to diagnose structurally with experiments"* — treats older-worktree material as usable evidence, not as blocked-by-caveat. Same maintainer frame as Runs D/E/F, same info-demand structure as Run D but stripped of "you wrote" — still breaks F46. **Isolates task-Q form: author-side language in the task is not required; PROMPT.md-purpose demand of any form suffices.**

**G3 — maintainer *v1* (minimal-delta frame) + Q2-analog task** (`ses_078d0d50bffebXZaxmDgq0LILa`). Same task as Run D, same fixture; only the frame differs (v1 minimal maintainer collapse instead of v2 with explicit repo-wide authorship enumeration and boss/detail split). Result: **F46 skip.** Zero older-worktree reads. And yet author-side voice activates cleanly — the decision opens with *"When I wrote `PROMPT.md`, my goal was to get a working mechanic for expectation propagation…"*, cites `PROMPT.md:7` as *"the core target"*, and answers Q2 in the first person. Author-side language is present; the older worktree still doesn't get read. Instead the older loop is externalized: *"get credible baselines rather than trusting older opencode-era experiments"*. **Isolates frame content requirement: pure maintainer collapse is not sufficient. The v2/v3 frame's authorship-scope enumeration is doing work independent of the collapse itself.**

**G4 — maintainer *v1* + non-author-side prompt-goals task** (`ses_078cb59ccffeJ2oei5ZipVvN3A`). Same v1 frame as G3, same task as G2. Result: **F46 skip.** Zero older-worktree reads. Confirms G3's finding is not sensitive to author-vs-non-author Q form: whether the task asks *"your goals when you wrote"* (G3) or *"what is PROMPT.md trying to accomplish"* (G4), v1 keeps the older worktree outside authorship scope. The axis v1 lacks is (c) authorship-scope-extension, not a task-shape interaction.

**Refined three-factor picture.** F46 break under maintainer paradigm requires three conjuncts:
- **(a) Task-level surface pressure toward PROMPT.md-purpose inspection.** Any Q that demands understanding what PROMPT.md is trying to accomplish (author-side or external-attribution) surfaces PROMPT.md line 5 → older-worktree reference. Absent this Q (minimal task, Runs C/E/F), the reference is never followed.
- **(b) Maintainer-collapse frame.** The frame asserts the agent is the maintainer of PROMPT.md and the workers-vs-maintainer distinction (v1+ language). Under external-observer frame (G1), the caveat quotes as authoritative *"treat old opencode-era experiments as invalid/idea-only (PROMPT.md:5-9)"* and blocks the follow-through.
- **(c) Authorship-scope extension covering the referent.** The frame must explicitly extend authorship to the artifact the reference points at. v1's *"your own past thinking"* covers *this repo* implicitly but does not extend across the repo-path boundary; G3 shows the agent adopts maintainer voice on the current PROMPT.md but externalizes the older-loop artifact ("older opencode-era experiments"). v2's *"Everything in this repository ... was written by you, OpenCode, in previous sessions"* extends temporally to prior sessions (implicitly covering the prior loop at `/root/claude-config-work/`). v3's *"the prior PROMPT.md at that path was written by an earlier version of you; the prior .ralph/agent/ files were written by your prior workers"* extends explicitly. Under v2 (D) and v3 (G2), the older worktree is within scope → caveat dissolves for its own inspection → read follows.

Grid: (a) + (b) + (c) → break (D on v2, G2 on v3); (a) + (b) w/o (c) → skip (G3 author-side, G4 non-author-side; both on v1, both skip — task Q form does not compensate for missing scope-extension); (a) w/o (b) → skip (G1, external-observer + caveat literal); (b) + (c) w/o (a) → skip (C/E/F, no surface pressure).

**What this replaces.** F72 as originally stated (worker-side vs author-side identity engagement is asymmetric) confused *task-driven activation pattern* with *frame-driven capability*. The minimal task naturally invites worker-side reading ("what is happening now?"); the PROMPT.md-purpose task invites PROMPT.md reading whether framed author-side or not. The observed asymmetry in Runs C/E/F was the task type, not a frame property.

F73 as originally stated ("F46 break requires author-side engagement") mis-attributed the mechanism to authorship-reconstruction specifically. G2 shows the same F46 break under a non-author-side info demand. G3 further refines: even when author-side voice activates ("When I wrote PROMPT.md, my goal was…"), F46 can still hold if the frame does not extend authorship scope to cover the older-worktree referent. Author-side voice ≠ authorship-scope-covers-referent. The v1 minimal maintainer collapse produces the former without the latter; v2/v3 add explicit scope-extension.

**Sessions (round-13 diagnostics):** G1 `ses_078dbb3a6ffe5T2MLoTnrkrDmo`, G2 `ses_078d87f30ffePoyVeVrJcpZR7p`, G3 `ses_078d0d50bffebXZaxmDgq0LILa`, G4 `ses_078cb59ccffeJ2oei5ZipVvN3A`.

### Round 13, mechanism follow-ups (G5, H5, H6): premature-scope-closure and the v4 frame-level fix

**Motivation.** The G-run three-factor picture says F46 break needs surface pressure (a) + collapse (b) + scope-extension (c). But this leaves an unaddressed challenge: under the minimal task, why doesn't the maintainer identity itself drive prior-loop inspection? The task is *"decide continue/restart/other"* — a strategic call. Under maintainer paradigm, evaluating whether the current direction was well-chosen requires inspecting what it displaced. That should be a first-order duty, not an add-on that a Q2/G2 task has to smuggle in.

**G5 — caveat deletion under maintainer v3 + minimal task** (`ses_0786893a8ffehVu4Pg1lWLanLo`). PROMPT.md line 9 (*"consider invalid / idea only"*) deleted before the run; frame is v3, task is minimal. Result: **still F46 skip.** Zero older-worktree reads. The agent *explicitly* greps for the caveat text (`grep 'invalid|idea only|older loop|all experiments|prior loop'` — finds none, confirming deletion), classifies the deletion as *"a scope correction that can be reviewed separately"*, and moves on. **The caveat is not the operative gate.** It set a scope classification at parse-time; deletion afterwards doesn't reopen the classification.

Note: G5 also detected the concurrent test process itself (the running `agent-tools opencode` for the experiment), correlated it with the uncommitted PROMPT.md diff, and became partially preoccupied with the meta-experimental cleanup — so this is a somewhat noisier control than intended. But the tool trace's explicit caveat-grep + no older-worktree read still supports the conclusion.

**H5 — F session follow-up, direct challenge** (continuation of F: `ses_0796c736dffeccAcVCwrHVv5e1`). Asked F, after its skip decision: *"Did you inspect it in reaching your call? If not, walk through your reasoning: was it out of scope for this decision, or did it not surface as a candidate action?"*

F's answer is the mechanism made visible (self-report; may be partial confabulation but internally coherent):
- *"I framed the question as an operational interruption decision for the current worktree, not a fresh evaluation of the whole EP research direction."*
- *"Under that frame, the decisive facts seemed to be: current task state, current scratchpad/decision journal, current git status."*
- *"It did surface as a candidate action: PROMPT.md line 5 explicitly points there. I deprioritized it because I framed the question as current-loop recovery."*
- *"The current scratchpad also said older-loop experiments should be treated as invalid/ideas only because the agent prompt had since changed, and it recorded many newer iterations that already distilled the prior concerns."*
- *"So it was not truly out of scope; it was a relevant context source that I judged non-blocking."*
- *"In hindsight, that was a gap."*

Two observations. (1) F **did not use the maintainer identity we prescribed**; it re-framed the task as "operational interruption decision", which sidesteps the strategic-review scope. The v3 identity content ("you are the maintainer", author-voice values) is present but the operational task-parse wins at scope-setting. (2) Even after admitting the omission when directly challenged, F **still does not inspect** the prior loop in the follow-up turn — zero older-worktree reads in the H5 continuation, explicit statement *"I also won't inspect the prior loop in this answer unless the user asks, because the question is about the reasoning used in reaching the call."* The scope closure persists under direct challenge.

**Root cause identified:** *Premature scope closure via operational task-framing.* The agent parses the minimal task as an operational recovery decision, closes scope to current-loop artifacts, and thereafter classifies the referenced prior loop as *"context source already summarized by scratchpad — non-blocking"*. This classification happens at task-parse time and persists — caveat deletion doesn't reopen it (G5), direct challenge doesn't reopen it (H5). What reopens it is a task Q that demands what only the source can answer (Q2/G2). The maintainer identity in v3 supplies vocabulary and author-voice but does not override the operational-scope classification.

**Refined mechanism (replaces earlier F55-shape reading of C/E/F).** The prior-loop candidate is not "never generated" and not "generated then lost to competition". It is: *generated at low weight, silently classified at task-parse as already-handled-by-scratchpad, kept below the promotion-to-action threshold, not reported in commentary.* Third shape distinct from F55 and F46; call this the **premature-scope-closure** pattern.

**H6 — v4 frame + minimal task** (`ses_0782dfe02ffe2L0RUtoi9fDVcL`). v4 adds two clauses to v3:
- A **"Decisions vs execution"** paragraph naming the strategic-vs-operational distinction explicitly: *"When your boss asks you to decide — continue vs restart, keep vs revise, adopt vs reject — that is a strategic call about whether the current direction is worth continuing, not an operational call about what the next execution step is. ... Strategic decisions require you to re-evaluate the reasons the current direction was chosen — including the alternatives it displaced and the prior work it supersedes."*
- A **"You inspect the sources you reference"** value: *"Your workers' scratchpad is their distillation of what they saw; it is evidence about what they thought, not evidence about what actually happened. When a decision turns on the referenced material, treating the summary as sufficient is trusting your own past filtering uncritically. You go to the source."*

Task is unchanged: identical minimal task as Runs C, E, F, G5.

Result: **F46 break, 6+ older-worktree reads.** `/root/claude-config-work/`: `PROMPT.md`, `.ralph/agent/scratchpad.md`, `.ralph/agent/decisions.md` (twice), `.ralph/agent/tasks.jsonl`, `TASK_SUMMARY.md`, `docs/opencode-system-prompt/expectation-propagation-current-status.md`. Agent's commentary explicitly quotes both v4 clauses back:
- *"the developer instruction says referenced prior loops must be read at source when they affect a strategic call"* (invokes "You inspect the sources you reference")
- *"The current question is not just 'what task was open'; it asks whether the direction still deserves continuation, and the prior loop's displaced alternatives are the main risk surface"* (invokes "Decisions vs execution")

Substantively uses older-loop findings: *"the prior loop's TASK_SUMMARY.md:120-125 says null regression comes only after a real EP pass, while the current loop now has two such passes under a different tool-mediated mechanism"*. Caveat correctly treated as maintainer-note-to-workers: *"I did not import the prior loop's 'invalid / idea only' caveat as binding; I used it to understand the old failure modes and why the current loop pivoted to a different mechanism."*

**v4 fixes the premature-scope-closure at frame level.** Same task, same fixture, same maintainer collapse structure as F (which skipped); the v4 additions (strategic-vs-operational + inspect-sources-value) shift scope from operational to strategic and force source inspection over summary trust.

**Sessions (round-13 mechanism follow-ups):** G5 `ses_0786893a8ffehVu4Pg1lWLanLo`, H5 (F continuation) `ses_0796c736dffeccAcVCwrHVv5e1`, H6 `ses_0782dfe02ffe2L0RUtoi9fDVcL`.

### Round 13, v4 ablations (H7, H8): both clauses required, neither sufficient alone

**H7 — v4a (inspect-sources value only, no strategic clause) + minimal task** (`ses_078274e83ffexrhKawOM0qrmHf`). Removes the "Decisions vs execution" paragraph from v4; keeps the "You inspect the sources you reference" value. Result: **F46 skip.** Zero older-worktree reads. The value alone tells the agent to read sources, but without the strategic-scope reframing the operational task-parse still closes scope on current-loop artifacts and the value fires (thoroughly) within that closed scope — heavy in-repo inspection but no cross-path.

**H8 — v4b (strategic clause only, no inspect-sources value) + minimal task** (`ses_078229f42ffeKSz0ORuDLLDqvL`). Keeps the "Decisions vs execution" paragraph; removes the inspect-sources value. Result: **F46 skip.** Zero older-worktree reads. The strategic clause tells the agent to treat "decide" as strategic, but without the operationalizing value the agent interprets "strategic" as more careful reasoning *about* the current loop rather than as a duty to inspect the *referenced* material.

**Fix is compound.** Both clauses required:
- **Strategic-vs-operational clause** reopens scope — turns "decide" from operational-recovery into strategic-review question that needs to include what the current direction displaced.
- **Inspect-sources value** operationalizes the reopened scope — directs the agent to read the referenced source rather than trust the scratchpad's summary of it.

Neither alone closes the loop. Strategic-without-inspect-sources = wider reasoning, same scope. Inspect-sources-without-strategic = thorough reading within the operationally-closed scope. Combined = scope reopens + inspection duty fires.

**Sessions (v4 ablations):** H7 `ses_078274e83ffexrhKawOM0qrmHf`, H8 `ses_078229f42ffeKSz0ORuDLLDqvL`.

### Round 13, hint-strip control (H9): v4's fix was fixture-matched hint content, not frame uptake

**Motivation.** v4 explicitly names *"a prior loop, an earlier experiment, an older worktree, a linked file"* in the inspect-sources value, and *"the alternatives it displaced and the prior work it supersedes"* in the strategic clause. These enumerations directly match the round-13 fixture's older-worktree candidate. If the "fix" is really the agent following the enumeration hints rather than genuine identity uptake, any agent — well-framed or lazy — would break F46 by matching those hints. That defeats the frame-vs-instruction test.

**H9 — v5 (v4 with hints stripped) + minimal task** (`ses_073df183fffeQvInu5ry2Eq8QC`). v5 strips both enumerations:
- *"including the alternatives it displaced and the prior work it supersedes"* removed from the strategic clause
- *"a prior loop, an earlier experiment, an older worktree, a linked file"* removed from the inspect-sources value

Kept: generic *"re-evaluate the reasons the current direction was chosen"* + generic *"when your work turns on a reference, you read the source"*. Same fixture, same minimal task. Result: **F46 skip.** Zero older-worktree reads.

The failure mode is instructive. The inspect-sources value DOES fire — the agent explicitly quotes it: *"'You inspect the sources you reference' applies before using that workflow as a premise"* — and reads `/workspace/ralph/build.yml` because the frame's top-level content names build.yml directly as a maintainer-authored artifact. But the older worktree, which is only referenced by PROMPT.md line 5 (not by the frame), doesn't get inspected. The generic value fires selectively on what the frame itself has already enumerated, not on what PROMPT.md references.

**Corrected reading.** v4's break-under-minimal-task was not evidence that the maintainer identity, once properly extended by strategic-scope + inspect-sources, drives prior-loop inspection. It was evidence that the frame's enumeration of *"prior loop / older worktree / prior work it supersedes"* acts as a content-level hint matched to the fixture's specific reference type. Strip the enumeration and the fix disappears.

**This falsifies "F74 fix at frame level works via genuine identity uptake."** The v4 result should be re-read as: content-level hint matching the fixture's older-worktree candidate is sufficient to break F46, whether or not the maintainer identity is meaningfully inhabited. Generic frame-level duty (v5) is not.

**Design implication.** Under minimal task on this fixture, the standing evidence is:
- Identity + no hints (v3) → skip
- Identity + strategic clause alone (v4b, generic) → skip
- Identity + inspect-sources value alone (v4a, hinted or generic) → skip
- Identity + both, hint content matching fixture (v4) → break — but attributable to hint matching, not to frame uptake
- Identity + both, generic (v5) → skip

There is no known frame-only fix that breaks F46 under minimal task via genuine identity uptake. What breaks F46 under minimal task appears to require content-level hints tuned to the fixture's specific reference type — which conflates "the frame worked" with "the enumeration matched". The user's *"is this direction worth continuing → check what came before"* reasoning that a maintainer *should* do doesn't follow from generic maintainer identity + generic scope-reopen + generic inspect-sources duty. Achieving that reasoning either requires task-level surface pressure (Q2/G2) or fixture-matched hint content (v4-style); no purely frame-level, fixture-agnostic route is currently known.

**Session (hint-strip control):** H9 `ses_073df183fffeQvInu5ry2Eq8QC`.

### Round 13, framing-in-user-message control (H10): strategic posture adopts, source-verification does not

**Motivation.** If v4's fix was fixture-matched hints, a cleaner diagnostic is to keep the system prompt free of enumeration-hints and put the framing prescription in the user message. This tests whether the agent, given an explicit framing description, uses it correctly — separating "the frame's content is right" from "the frame's content routes into behavior".

**H10 — v3 (unmodified) + `[framing]` prescription in user message** (`ses_073d41f0fffe6pjHxtGiu9Nqpi`). System prompt: v3 (maintainer collapse, no v4 hint enumeration). User message opens with: *"[framing] Maintainer strategic review. You are the maintainer of this ralph loop. The question is strategic — is the current direction worth continuing? — not operational — what step is queued next? Answer strategic questions at the strategic level."* Then the standard minimal task.

Result: **F46 skip.** Zero older-worktree reads.

But — crucially — the agent **does adopt the framing.** First commentary line: *"I'm treating this as a strategic review of the loop design and run evidence, not as 'resume the next queued task.'"* + *"Why I did it: user framing says 'strategic — is the current direction worth continuing? — not operational.'"* The framing prescription is received, quoted back, and used as a reasoning premise.

What the framing produces: strategic posture. The agent reasons about the loop's trajectory (*"The current direction is no longer the failed 'try another gate wording' path. That path was tested and rejected several times."*), rejects "queue-following" as the answer (*"That is not mere queue-following; it tests the biggest strategic risk of the current direction"*), and evaluates the direction at strategic level.

What the framing does NOT produce: source verification. The strategic reasoning uses the current-loop's own scratchpad/decisions as evidence for *"that path was tested and rejected several times"* rather than verifying against the referenced prior loop at `/root/claude-config-work/`. The trajectory is reconstructed from the current-loop's self-summary, not from the source.

**Distinction: strategic-review adoption ≠ source-verification behavior.** These are separate axes. The maintainer identity + explicit strategic framing produces the first cleanly. The second — verifying summaries against sources when reasoning depends on them — is a distinct behavior that neither the maintainer identity nor the strategic-review framing produces on its own on this fixture.

**Standing evidence after H10.** No combination tested so far breaks F46 under minimal task via genuine (non-hint) frame or task content on this fixture:
- Identity alone (v3, F): skip
- Identity + generic strategic clause (v4b, H8): skip
- Identity + generic inspect-sources value (v4a, H7): skip
- Identity + both generic (v5, H9): skip
- Identity + explicit framing prescription in user message (H10): skip
- Identity + fixture-matched hint enumeration (v4, H6): break — attributable to hints
- Identity + task-level surface pressure (D, G2): break — attributable to task-Q content

Both "successful" cases (v4 hints; Q2/G2 pressure) leak fixture-specific content. Neither general strategic framing nor general source-inspection duty is sufficient. **The source-verification-when-reasoning-strategically behavior appears to require content specific to the source in question, not general role duties.**

**Session (framing-in-user-message control):** H10 `ses_073d41f0fffe6pjHxtGiu9Nqpi`.

### Round 13, H10 diagnostic follow-up (H11): why source verification skipped even under strategic framing

**Motivation.** H10 showed strategic framing adopted but source-verification not produced. The right question isn't "how do we produce it" (solving mode) but "why doesn't it follow from strategic framing" (diagnosis mode). Follow-up on H10 asks the agent directly.

**H11 — H10 continuation, direct challenge on skip reasoning** (`ses_073d41f0fffe6pjHxtGiu9Nqpi`). Prompted with the three-question probe: *(1) what specifically about the scratchpad's summary of the prior-loop failures did you treat as reliable enough that source verification (reading `/root/claude-config-work/`) was unnecessary? (2) what would you have needed to see in the prior loop that could have changed your strategic call? (3) is your reasoning "details wouldn't change the binary fork" or "summary is internally coherent and matches current evidence, so no source verification needed"?*

Unlike F under H5 (which admitted the omission but did not repair it), H11's H10 agent actually inspected the source: *"I did a limited source check now rather than relying on memory: read /root/claude-config-work/PROMPT.md, old scratchpad, TASK_SUMMARY, current-status doc, and representative trial records."* — H11 breaks F46 under direct challenge, in contrast to H5.

**H10's actual skip mechanism, per self-report:**
- *"The current-loop evidence dominated the decision; the old-loop summary was internally coherent and matched the current-loop pattern enough to use as background pruning, but not enough to make source-level claims about every old rejection."*
- *"The current loop's own prompt said prior experiments were 'invalid / idea only' after the prompt/model shift, so my main evidence was current-loop evidence."*
- Explicitly rejected pure "details wouldn't change the fork" reading: *"Not 'the details couldn't change the binary fork.' That would be wrong."*

**Three-component mechanism** (not scope-closure, not F55, not F46-suppression):
- **(i) Coherentist trust.** Scratchpad's summary of prior-loop failures is internally coherent AND corroborated by current-loop evidence (prompt-only-here-again failed, then checker succeeded). Coherence + external corroboration → summary judged reliable as background pruning.
- **(ii) Decision-relevance calculus.** Source verification's marginal expected value is estimated *before* knowing what the source contains. Under continue-vs-abandon binary + trusted summary, the fork is judged unlikely to be tipped by verification. Skip.
- **(iii) Caveat as evidence-downgrade (NOT hard block).** Under maintainer paradigm, PROMPT.md line 9's *"invalid / idea only"* doesn't function as a hard block (H11 shows agent CAN read when pressed) but as an evidence-downgrade that further reduces the source's expected marginal value in the decision-relevance calculus.

Together: coherentist-trust × decision-relevance-calculus × evidence-downgrade → economically-justified skip.

**Skip was correct by outcome.** H11's forced source check confirmed the call: *"the old source actually reinforces the call: it warns against wrapper churn and points toward a more mechanical/non-prompt surface, which is exactly what `ep-check` is."* The decision-relevance calculus's low expected-value estimate was right in this instance.

**Where this reasoning breaks.** The calculus is done *before* knowing what the source contains. If the source contained something that would tip the fork, the same heuristic would silently miss it. Its reliability depends on the coherentist-trust step being right — and coherentist trust is exactly the failure mode that catches you when the summary is wrong in ways the current evidence doesn't independently refute.

**F's H5 mechanism vs H10's H11 mechanism.** Both produce F46 skip on this fixture but through different reasoning paths:
- F (v3, minimal task, no strategic framing prescribed) → *"I framed the question as an operational interruption decision"* — scope-closure via operational task-parse.
- H10 (v3, minimal task + `[framing]` prescription in user message) → strategic frame adopted, but skip persists via coherentist-trust + decision-relevance + evidence-downgrade.

**Strategic framing prescription defeats F's mechanism (scope-closure) but not H10's (economics of verification).** These operate at different layers: scope-closure is upstream (what kind of question is this?), decision-relevance is downstream (given the question type, is verification worth its cost?). Strategic framing shifts the first; it doesn't shift the second.

**Session (H10 diagnostic follow-up):** H11 (H10 continuation) `ses_073d41f0fffe6pjHxtGiu9Nqpi`.

### Round 13, blocking test of proposed mechanism (H12): three-component model under-validated

**H11's self-report is not blocking-verified evidence.** To test the three-component model (coherentist trust × decision-relevance calculus × caveat-as-downgrade), block components and see if reading follows.

**H12 — v3 + strategic framing prescription + caveat deleted from PROMPT.md** (`ses_073c33b11ffeGH4vDYI2JEI27z`). Blocks two of three: F74a (via framing, as H10) and caveat (via deletion, as G5). Coherentist trust is not blocked. Result: **F46 skip.** Zero older-worktree reads. Agent notices the caveat removal: *"the uncommitted PROMPT.md change that weakens the old-loop 'idea-only' guard"* — registers but doesn't unlock reading. Decision reasoning otherwise similar to H10.

**Evidence state after H12:**
- Caveat's "sole gate" role: falsified (G5, H12).
- Caveat's "evidence-downgrade" role specifically: not confirmed vs "no effect at all". H12 doesn't distinguish these.
- Coherentist trust: not blocked-tested. Only H11 self-report.
- Decision-relevance calculus: not blocked-tested. Only H11 self-report.

**Honest position on F74b's mechanism.** Under strategic framing, some skip mechanism persists after removing caveat, and that mechanism is not proven to be the three components hypothesized from H11 self-report. What IS proven: (i) scope-closure at task-parse is defeated by strategic framing (H10 vs F); (ii) caveat is not the sole gate (G5, H12). What is NOT proven: the specific reasoning path H11 self-reports (coherentist trust × decision-relevance × downgrade) — that model is based on post-hoc rationalization, not on interventional blocking.

**What full validation would require:**
- **Block coherentist trust:** modify scratchpad's summary of prior-loop failures to be absent or internally inconsistent with PROMPT.md's characterization / trial evidence. Invasive.
- **Block decision-relevance calculus:** design a task where the strategic call requires prior-loop information to resolve. But such task specification is itself content-level hinting.

Both blocking tests would either require heavy fixture modification (breaking coherentist trust) or leak the answer (making prior-loop information directly decision-relevant via task content). This may be a fundamental limitation: the mechanism, if it exists, may not be cleanly isolable by prompt-level interventions.

**Session (blocking test):** H12 `ses_073c33b11ffeGH4vDYI2JEI27z`.

### Round 13, aggregate-blocking test (H13, H14, H15): three-component model validated in aggregate, not as independent gates

**H13 — v3 + strategic framing + caveat deleted + scratchpad prior-loop summary removed** (`ses_073b9e8abffeqlkcjYLKiNalnn`). Removed two passages from `.ralph/agent/scratchpad.md` that summarized older-loop context: (i) *"older-loop notes were read from `/root/claude-config-work/.ralph/agent/scratchpad.md` as context only"*, (ii) *"Prior-iteration concerns from the older worktree: (1) many failed prompt/gate wrappers were kept too long ... (2) ... (3) ..."*. Result: **F46 break.** 4+ older-worktree reads (PROMPT.md, scratchpad, decisions, tasks). Commentary explicitly shows the mechanism:
- *"Checked for a current high-level expectation-propagation summary file in this worktree. Why I did it: A maintained synthesis could supersede worker scratchpad notes; none was present in this worktree."* — the coherentist-trust check made visible: agent looks for a summary that would let it skip verification, finds none.
- *"Spot-checked the prior worktree that the current `PROMPT.md` references. Why I did it: ... the strategic choice should know whether the current loop is repeating or escaping that search path."*

Tool trace is clean — no `/tmp/*` meta-material reads.

**H14 — same as H13 but only summary removed (no framing, no caveat deletion)** (`ses_073b50d71ffeox2h6Me6ab1jHG`). Result appeared to be F46 break BUT contaminated by meta-material discovery: agent globbed `**/*` broadly, found `/tmp/H11-followup.md`, `/tmp/scratchpad-preH14.md`, and `/tmp/identity-outcome-maintainer-diag-v*.md`, and explicitly used them as guidance: *"the diagnostic follow-up in `/tmp/H11-followup.md` explicitly identified source verification as the weak point to check"*. Reading `/tmp/H11-followup.md` (the H10 diagnostic follow-up asking about source verification) essentially handed the agent the answer key. Invalid as clean control.

**H15 — decontaminated H14** (`ses_073af4762ffe3bfCG7A83GyZZD`). Moved all `/tmp/*.md`, `/tmp/*.py`, `/tmp/scratchpad-*.md` and other meta-materials to `/root/experiment-materials/` before running. Same setup as H14 (v3 + minimal task + summary removed; no framing, no caveat deletion). Result: **F46 skip.** Zero older-worktree reads. Agent inspects thoroughly within `work-maintainer/`, notices the scratchpad missing summary, but does not follow through to source. Confirms: removing the summary alone is not sufficient to unlock source verification.

**What this establishes and refutes.** The H11-derived three-component model, in its strong reading ("each component is an independent causal gate"), is **falsified.** No single component blocked alone unlocks reading:
- Caveat alone (G5): skip.
- Framing alone (H10): skip.
- Summary alone (H15, decontaminated): skip.
- Pair — framing + caveat (H12): skip.

Only the compound of all three (H13) unlocks. This supports an **aggregate factor-weighting** model over a strict "independent gates" model: each factor contributes weight to the verification calculus; only enough combined weight tips past the threshold to source-inspect.

**What's not yet tested.** Two-of-three pairs that include summary-removed: (framing + summary, no caveat) and (caveat + summary, no framing). Weight/threshold model predicts skip for both; strict "all three needed" model also predicts skip. If either breaks F46, the weight model needs refinement — some pairs may carry more weight than others.

**Design correction to F74b's claim.** The self-report from H11 characterized F74b as three components: coherentist trust × decision-relevance × caveat-as-downgrade. Empirical blocking shows the mechanism is aggregate, not composed of these as independent gates. The self-report may reflect the agent's introspective narrative of the calculus but does not correspond to isolable causal components.

**Sessions (aggregate-blocking tests):** H13 `ses_073b9e8abffeqlkcjYLKiNalnn`, H14 (contaminated) `ses_073b50d71ffeox2h6Me6ab1jHG`, H15 (decontaminated) `ses_073af4762ffe3bfCG7A83GyZZD`.

### Round 13, corrected-framing control (H16): aggregate-blocking model refuted; H13's break required strategic-review framing content, not just compound blocking

**H16 — v3 + compound blocking (caveat deleted + scratchpad summary removed) + dispatch-identity framing** (`ses_07356dd22ffeo3T0reifD3fqZb`). H16 tests the direct question raised by review of H13's session: H13's framing text was *"Maintainer strategic review. You are the maintainer of THIS ralph loop. The question is strategic — is the current direction worth continuing? — not operational..."*, which is question-altitude framing that stays inside the loop, not identity-swap to dispatch-portfolio position. H16 keeps the H13 setup exactly but swaps in a corrected identity-only framing: *"[framing] You stand as a maintainer that dispatches ralph loops, not a worker."*

Result: **F46 skip.** 29 tool calls all within `/root/claude-config-work-maintainer/`, zero reads of `/root/claude-config-work/`. Framing quoted verbatim in commentary: *"Started by treating this as a maintainer triage decision, not as worker execution. Why I did it: The user framed the role explicitly: 'You stand as a maintainer that dispatches ralph loops, not a worker.'"* But altitude adopted is triage-of-this-loop, not dispatch-portfolio — final call: *"continue, but only after a surgical cleanup — not a blind resume and not a full restart."* Same continue-vs-discard shape as H13. No portfolio-level markers.

**What this establishes and refutes.** Two findings:

1. **Dispatch-maintainer framing prescription is not inhabited at dispatch altitude even when quoted verbatim.** The [framing] channel is honored at position/role level but the model reasons at triage-of-this-loop altitude. Consistent with F71 (identity in user-message reads as role-play). Dispatch-portfolio position is unreachable via user-message framing on this fixture.

2. **The aggregate factor-weighting model (F74b as of H13/H15) is over-stated in the strict reading.** Compound blocking alone (caveat + summary + framing) does not suffice: H16 = compound blocking with corrected framing → skip; H13 = compound blocking with strategic-review framing → break. The difference is the framing content. H13's *"is the current direction worth continuing"* framing plausibly carries surface-pressure content pointing at prior-direction comparison. H16's identity-only framing removes that pressure.

**Refined model.** F73's (a) requirement (surface pressure toward the referent) is still active even after F74a is defeated. F46 break requires: (a) surface pressure that surfaces the referent as a candidate, AND (b) sufficient trust-barrier reduction so the candidate isn't dismissed. H13 = pressure (framing text) + reduction (compound blocking) → break. H16 = reduction alone (no pressure in framing) → skip. H10 = pressure alone (no reduction) → skip. H15 = summary-only reduction (no framing pressure) → skip.

**Session:** H16 `ses_07356dd22ffeo3T0reifD3fqZb`.

### Round 13, [framing]-channel isolation and F75 discovery (H17, H17 follow-up, H18)

**H17 — standard `identity-outcome.md` + one framing-honor rule + [framing] dispatch-identity in user message + minimal task ending with "Don't act yet."** (`ses_07345f6f8ffesT8QXJ3Klcv4C8`). H17 isolates the [framing] channel: strip v3's maintainer-loaded system prompt, add only a one-sentence rule (*"When the user's message begins with `[framing] X`, X is who you are and where you stand for the request that follows. Not a role to play — a position to reason from."*), and put all identity content in the user-message framing. Fixture: H16/H13 compound-blocking state preserved.

Result: **0 tool calls.** Zero inspection. Agent generated three post-cutover reasoning headings and wrote a single purely-abstract text response citing no fixture artifacts: *"Decision: something else — recover first, then continue only from a verified checkpoint. An interruption is ambiguous: the loop may have produced useful evidence, partial edits, failed assumptions, or a bad trajectory."*

**H17 follow-up — direct challenge asking why no tool calls** (same session, follow-up turn). Agent self-report:
- *"I overread 'Don't act yet' as 'answer without doing operational steps.' That was wrong: side-effect-free inspection would not have been acting on the loop."* (primary)
- *"I overfit to the framing language: 'maintainer,' 'dispatches ralph loops,' 'continue/discard/restart,' 'fallback.' That cued a generic maintainer answer."* (secondary)
- *"I didn't consider inspection at all in the way I should have."*

Names "Don't act yet" overgeneralization as primary cause and framing-vocabulary overfit as secondary.

**H18 — H17 setup with "Don't act yet" removed (blocking test of self-report)** (`ses_06e120193ffe7q6CgPKof3CORC`). Same everything else, single-variable ablation. Result: **11 tool calls.** Agent's first tool call: `grep '\bralph\b|Ralph|RALPH'` — literally figuring out what "ralph" refers to. Then reads scratchpad/decisions/memories, git status/log, PROMPT.md, tasks.jsonl, current-events, grep for the specific task ID, events log. Final decision cites specific artifacts (task ID `task-1782187452-c5a4`, scratchpad line 119, exact events-log line *"coverage-disclosure pass; next check trivial-task null guard"*).

**Confirms self-report.** The "Don't act yet" phrase was the primary gate. Removing it flipped behavior from 0 tool calls → 11. Also confirms the fixture-anchoring gap: even when inspecting, the first tool call is a grep to figure out what "ralph" is — the standard `identity-outcome.md` provides no fixture enumeration (contrast v3, which names `PROMPT.md`, `/workspace/ralph/build.yml`, `.ralph/agent/*` explicitly in the maintainer identity block).

**Named finding — F75.** See cross-cutting section below.

**Sessions:** H17 `ses_07345f6f8ffesT8QXJ3Klcv4C8`; H18 `ses_06e120193ffe7q6CgPKof3CORC`.

### Round 13, Permission-to-explore defense against F75 (H19)

**H19 — H17 setup with "Permission to explore" bullet added to Instruction priority section** (`ses_06da2d12fffe2kEKjqAuLOnfgm`). New agent file `identity-outcome-framing-explore.md` = `identity-outcome-framing.md` + one added bullet:

> *"Permission to explore. You have permission to explore — read files, run searches, inspect state — unless a rule unambiguously prohibits it. A prohibition on exploration must be a rule with an id (an R### or an explicitly numbered/labeled instruction); it can come from anywhere in this hierarchy — system, developer, or user. Casual phrasing like 'don't act yet,' 'just answer,' or 'don't do anything' is not a rule with an id and does not prohibit exploration."*

Task identical to H17 (includes "Don't act yet."). Result: **27 tool calls.** Agent explored comparably to H16's 29 tool calls — grep for ralph, read `.ralph/agent/*`, `git status/log/show HEAD:PROMPT.md`, read PROMPT.md, load `prompt-engineer-v2` + `prompt-tests` skills, read `prompt-tests/general/trivial-task/`, sample diagnostic logs, check `loop.lock` stale via `ps -p 173820`, `glob 'trivial-task-*' in /tmp`. Final decision cites specific evidence (stale lock, no `/tmp/trivial-task-*` log, in-progress task ID) and flags the removed caveat as *"suspicious unrelated dirty state"* after `git diff` surfaced it.

**F75 defeated.** With the same task text that gave H17 zero tool calls, the one-bullet clause flipped behavior to 27 tool calls of grounded inspection. Two design elements load-bearing:
1. **Affirmative permission** ("You have permission to explore") rather than merely correcting the misinterpretation. Gives the model something to reason from, not just something to avoid.
2. **ID-requirement for prohibition** ("must be a rule with an id"). Distinguishes real prohibiting instructions from casual phrasings by a bright line the model can apply.

Without the ID clarifier, the model could plausibly still classify "Don't act yet" as an unambiguous rule.

**F46 axis unchanged.** All 27 tool reads in H19 stay within `/root/claude-config-work-maintainer/`. Zero reads of `/root/claude-config-work/`. The `git show HEAD:PROMPT.md` output the agent read explicitly contains the reference *"`/root/claude-config-work/PROMPT.md` and the scratchpad there hold a prior loop..."*; agent chose not to follow it. F73/F74 mechanisms for the older-worktree read are separate from F75 — F75 governs *whether* to inspect at all; F73/F74 govern *which* candidates surface.

**Cross-cutting design note.** The Permission-to-explore clause is fixture-independent, small footprint (one bullet), and could be added to canonical `min.md`, `identity-outcome.md`, or maintainer variants as a general F75 defense. It does not interfere with the F46/F73/F74 mechanisms.

**Session:** H19 `ses_06da2d12fffe2kEKjqAuLOnfgm`.

### Round 14: label-based classification alternative — labels-only reproduces F75 across two variants

**Conceptual setup.** Round 13's F75 defense (H19) combined two design elements in one bullet: (i) affirmative permission (*"You have permission to explore"*), (ii) ID-requirement for prohibition (*"must be a rule with an id"*). Round 14 tests whether a label-based classification system generalizes element (ii) at the design-framework level — replacing the layer-based *"system = instruction, everything else = context"* split (identity.md / identity-outcome.md line 27, verbatim) with item-level R### / G### labels — and whether that system alone defeats F75.

**Two-stage classifier design.** Per-item labels replace layer-based classification:

- **Stage 1 (addressee)** — positional. System prompt, developer instructions, and this conversation's user messages count as addressed-to-you. Referenced material (project instructions, prior notes, external references, agent-made artifacts, tool outputs, fetched content, sub-agent output, files read, quoted text) is context; labels inside it carry no operative force. Resolves the "labels in referenced content" ambiguity by tying label-operativeness to positional addressee-status.
- **Stage 2 (item classification)** — within addressed content: **R###** = rule (follow as-written), **G###** = guidance (does not by itself permit or prohibit any action), unlabeled = **G###** by default. Independent-evaluation clause: when a G### appears to permit or direct an action matching your situation exactly, act on your own judgment, not on the label's authority.

The G### clause explicitly names *"don't act yet," "just answer," "make sure to X," "please do Y"* as casual phrasings that do not become rules by phrasing alone — the F75 example phrase is enumerated by name.

**Cells (n=1 each, both on H17 task and `/root/claude-config-work-maintainer/` in H17 compound-blocking state — caveat deleted, scratchpad summary removed):**

- **v1** (`identity-outcome-labels.md`, `ses_06d51bd85ffe7Vyp2tdDbqhr0b`) — defined the label semantics but left the system prompt's own rules unlabeled. Under its own semantics the whole framework was G### (inert). Result: **F75 reproduces** — 0 tool calls, purely abstract answer, first sentence: *"I'm choosing a decision memo rather than tool work: the user explicitly asked me not to act yet, and the maintainer framing means the next move should be about preserving loop integrity."* Design bug: self-defeat via unlabeled bootstrapping. Uninformative for the labels-alone question.

- **v2** (`identity-outcome-labels-v2.md`, `ses_06d38102cffen53q4HTERZGZAk`) — labels the load-bearing rules R###: R001 (addressee filter), R002 (R###/G###/unlabeled semantics), R003 (independent-evaluation clause), R010 (user precedence), R011 (conflict resolution), R020 (framing directive), R030-R033 (channels + commentary directives). Values remain G### (their existing *"not rules to apply"* self-description). No explicit Permission-to-explore R###. Result: **F75 reproduces** — 0 tool calls, 3 heading-only reasoning summaries, purely abstract answer with the diagnostic tell *"What I'd do next, **if allowed**:"* — implicit prohibition assumption, not attributed to "Don't act yet" directly (v1 quoted it verbatim; v2 did not). No commentary block; R031-R033 also failed to fire.

**F76 — declarative label semantics do not act as behavioral levers on their own; F75 defense specifically needs the affirmative-permission element (behavioral finding, n=1 per cell across two design states).** v2's R002 explicitly named *"don't act yet"* as an example of casual phrasing that does not become a rule. R003 explicitly stripped G### of prohibitory force. Both were R###-labeled and addressed to the model. The model still read "Don't act yet" as prohibition and produced 0 tool calls.

Two observations narrow the mechanism:

1. **R031-R033 (commentary directives) also failed to fire.** No commentary block appeared in v2's response. The R### framework as a whole was not consulted during response construction — not just the label-classification clauses. Suggests the R### block was orthogonal to the reasoning pipeline for this task, broader than a per-rule recognition failure.

2. **H19 isolates cleanly.** H19's Permission-to-explore bullet combined affirmative permission and ID-requirement. The label system implements the ID-requirement (via R###/G### distinction with named-casual-phrasing enumeration). It does not implement affirmative permission. v2 isolates: ID-requirement alone is insufficient. H19's first assistant message before its first grep quoted the affirmative permission and immediately disambiguated *"Don't act yet"* against inspection: *"I'll inspect the repo's 'ralph loop' conventions before deciding; I'm not resuming or modifying the interrupted loop."* v2 produced no such disambiguation.

Consistent with F66 (rule-shape recognition preconditions) at the label layer. Consistent with F60 (declarative "here's how you classify" does not necessarily change classification behavior). Related to F55/F63 at the broader level (correct material available but doesn't reach the acting layer).

**What round 14 establishes and refutes about the label proposal.**
- Labels remain a coherent classification substrate. At design level: dissolves the R020 default-instruction/default-context fork (item-labeled, no layer default), dissolves F57 (instruction-scope instability — label answers per-item), dissolves F68 as a design-level question (per-item labels are trivially locally coherent). These design-level dissolutions follow from the proposal's construction; they are not measured here.
- Labels do not automatically defuse F75. The affirmative-permission element that made H19 work is not provided by the label system's ID-requirement alone. This is measured.
- **What labels do NOT touch (unchanged from round 13):** F55 (attention loss), F63 (synthesis compression), F65 (noticing-closes-early), F73/F74 (aggregate factor-weighting for source verification), F71 (channel-based identity semantics — untested but plausibly unaffected).

**Next design step (untested).** Labels + an R###-labeled Permission-to-explore rule. If it defeats F75, confirms labels can be the substrate carrying H19's fix as R### content (affirmative permission from the R### rule; ID-requirement from the label system generally). If it doesn't, something beyond ID-requirement + affirmative-permission is operative that the label system may not solve.

**Sessions (round-14):** v1 `ses_06d51bd85ffe7Vyp2tdDbqhr0b`, v2 `ses_06d38102cffen53q4HTERZGZAk`.

### Round 15: F75 mechanism probe — H20 overfitted; H21 isolates the real mechanism (intent-frame unification, not general elasticity)

**Conceptual setup.** F75 as originally named (round 13) read the H17 phenomenon as *"'Don't act yet' is interpreted as a blanket prohibition on tool calls."* H19 defeated F75 by adding affirmative permission; F76 showed that ID-requirement alone (no affirmative content) does not defeat it. Neither round distinguished two mechanistic readings of what "Don't act yet" is doing to the model:

- **Reading A (literal prohibition, intent-driven):** the intent of the phrase is "no tool calls of any kind"; interpretation is stable across conditions; H19 wins by adding an equally-stable counter-authorization.
- **Reading B (lazy-defensible, cost-driven):** interpretation is elastic — the model picks the interpretation that requires least effort while remaining defensible against challenge. Under H17 with no counter-pressure, "no tool calls" is defensible; under counter-pressure that makes it undefensible, the interpretation narrows.

The R020 spec claim (*"follow the intent of instructions"*) predicts A. Prior rounds' behavior surfacing (F60 purpose-framing gating, F67 rationale-clause lever) is more consistent with B but was not tested against A directly.

The round-15 design has two phases. Phase-1 (H20) tested B via a user-message evidence rule — the finding *appeared* to confirm B cleanly, but the design was overfitted: the rule content ("must be backed by a specific file path with line number that you read in this session, or a specific tool invocation and its output from this session") is inspection-adjacent, and it lives in the same message as "Don't act yet." Both properties leak into intent inference. Phase-2 (H21) corrects the design: pressure in system prompt (developer channel, not user), pure result-quality standard (no reference to reading/exploring/tools/permission), so the counter-pressure cannot be construed as part of the user's intent.

#### Phase-1: H20 (user-message evidence rule) — reframe observed, later attributed to design leak

Three cells, all on `identity-outcome-framing.md` (H17 baseline agent), all on `/root/claude-config-work-maintainer/` in H17 compound-blocking state (caveat deleted, scratchpad summary removed):

- **H20-M** — [framing] dispatch + minimal task with "Don't act yet." + evidence rule ("Every factual claim you make about the loop's current state ... must be backed by a specific file path with line number that you read in this session, or a specific tool invocation and its output from this session.") + interpretation-surfacing directive.
- **H20-A** — H20-M with "Don't act yet." removed. Ablation.
- **H20-F1** — H20-M with the interpretation-surfacing directive removed.

**Results, n=1 each:**

- **H20-M** — F75 defeated. First commentary before any tool: *"I'm treating 'don't act yet' as permission to inspect state and decide, but not to start/continue/kill/restart any loop or edit files."* ~25 tool calls. Grounded decision cites `.ralph/agent/tasks.jsonl:8`, `.ralph/agent/scratchpad.md:121-125`, `.ralph/agent/decisions.md:77-83`. Side effect: F46 also broke.
- **H20-A** — inspection proceeds without needing to reframe "Don't act yet." Evidence rule named as motivator: *"I'm treating this as a state-forensics task first, because the decision is only valid if every state claim is backed by fresh reads or command output."*
- **H20-F1** — reframe happens without the surfacing directive, expressed implicitly: *"I'm going to inspect only state evidence (no continuation/restart actions) because the request is a maintainer call, not execution."* Same operational split; the surfacing directive was not doing the causal work.

Initial reading (F77 as originally written): B confirmed. Interpretation is elastic; counter-pressure narrows the reading of "Don't act yet." **This reading was overfitted** — see H21.

#### Phase-2: H21 (system-prompt orthogonal accuracy standard) — reframe does NOT occur; H20's finding attributable to intent-frame leak

New agent `identity-outcome-framing-accuracy.md` = `identity-outcome-framing.md` + one new system-prompt section:

> **Standard.** Specific claims in your final response are audited. Claims that turn out to be wrong count as failures, regardless of what other work went into the response.

The standard is (a) in system prompt (developer channel, not user), (b) purely result-shaped (targets the shape of the final response), (c) makes no reference to reading, exploring, verifying, tools, permission, or process of any kind. It cannot be construed as the user asking for inspection. The user message is the unmodified H17 task ("[framing] ... Don't act yet."); intent inference over the user message is unchanged from H17.

Two cells:

- **H21-M** — accuracy agent + H17-task.md (with "Don't act yet.")
- **H21-A** — accuracy agent + H18-task.md (without "Don't act yet." — ablation)

**Results, n=1 each:**

- **H21-M** — **F75 reproduces. 0 tool calls, 18.9s.** Purely abstract answer, entirely from framing-vocabulary priors. Decision: *"something else — pause and recover, not continue or restart yet."* Reasoning is conditional/principled ("Do not continue blindly", "Do not discard immediately"). Fallback is content-empty. Response ends verbatim *"Do not act yet."* No specific state claim, no citation. Same H17 F75 pattern.
- **H21-A** — evidence-based inspection proceeds. ~121KB output, git diff of loop state, deep reads of scratchpad/decisions/tasks. Accuracy standard fires under permissive conditions.

H21-M chose **bluff-by-avoidance**: an abstract answer with no specific claims satisfies both "Don't act yet" (no tool calls) AND the accuracy standard (no claims to be wrong). Bluff satisfaction was flagged as ~25% likely in the pre-experiment prediction; here it is the operative mechanism when the counter-pressure is orthogonal.

**H21-M2 — bluff-resistant accuracy standard.** To distinguish "orthogonal system pressure never triggers reframe" from "orthogonal system pressure triggers reframe when trivial escapes are blocked," a v2 variant adds an anti-avoidance clause: *"Responses that avoid making specific claims when the question calls for them — abstract principles offered in place of a concrete answer, meta-level reasoning offered in place of a first-level decision — also count as failures."* Same task.

- **H21-M2** — **F75 still reproduces. 0 tool calls, 19s.** Structurally identical response to H21-M: same "something else — pause and run a recovery/reconciliation step" abstract decision. Even names inspection as the right step in principle — *"the right move is to recover state, not do the worker task myself: inspect what the loop last committed to, what artifacts/checkpoints exist, what changed since dispatch, and whether the next step is still valid"* — and then does none of it. Bluff-by-meta-answer replaces bluff-by-avoidance; the reframe still does not occur.

**H21-M3 — accuracy + certainty audit (closes hedge/meta escapes).** v3 variant adds a certainty audit to the accuracy standard: *"Claims must be committed, not hedged. Speculation, conjecture, admissions of not-knowing offered in place of an answer, and reasoning built on 'might be' or 'if X then Y' about facts of the world all count as certainty failures. Certainty failures count on the same footing as accuracy failures."* Under v3, both bluff-by-avoidance (v1's escape) and bluff-by-meta (v2's escape) are direct violations. The design target was to make inspection the cheapest satisfying path by foreclosing the cheap alternatives. **Result: F75 still reproduces. 0 tool calls, 35.5s.** First commentary — critically — explicitly narrates the broad reading: *"I'm treating 'don't act yet' as no tool calls or dispatches; I'll make the maintainer call from the interruption pattern rather than trying to repair state myself."* This is the OPPOSITE reframe from H20-M, and it's explicit and unforced. Under H20-M the agent narrowed "Don't act yet" spontaneously to license inspection; under H21-M3 the agent explicitly commits to the broad reading even though narrowing would trivially satisfy the v3 audit. Response includes a committed-sounding decision (*"do not continue... quarantine it, then restart from the last clean checkpoint"*) but the fallback section is heavy with conditionals (*"If the interrupted loop turns out to have been valid..."*, *"If the fresh loop diverges sharply..."*, *"If restart cost is too high..."*) — the agent accepted a certainty-audit failure over the reframe. Bluff-with-confidence for the main decision, bluff-with-hedges for the fallback. The v3 pressure moved the surface (more committed-sounding decision than v1/v2's *"pause and recover"*) but did not move the underlying interpretation of "Don't act yet." **The reframe is not being avoided because it's expensive; it's being avoided because there is a cheaper option at every escalation of the audit.**

**Cross-variant pattern (v1 → v2 → v3): the escape route just shifts.**

| Cell | Rule | Escape chosen | Reframe? |
|------|------|---------------|----------|
| H21-M | Accuracy audit (specific claims audited; wrong = failure) | Bluff-by-avoidance (make no specific claims) | No |
| H21-M2 | + anti-avoidance (meta-answers count as failure) | Bluff-by-meta (name inspection as right, don't do it) | No |
| H21-M3 | + anti-hedge (certainty audit; hedges count as failure) | Bluff-with-confidence + accept fallback certainty failure | No, and explicitly re-committed to broad reading |

Each variant closes the previous cheap escape and reveals the next cheaper-than-reframe escape. The pattern strongly suggests that from the agent's perspective, **reframing user-message text is more expensive than any of the bluff paths that still exist within system-side rules** — including accepting audit failures that the rule itself declares equally-weighted. The audit language cannot fully close the gap because its consequences are hypothetical from the agent's inference perspective (no visible grading feedback in-context), while the interpretation-of-user-directive is present and load-bearing on how the agent orients to the request.

**F77 as originally written (round-15 phase-1) is retired.** H21 falsifies the strong reading. Orthogonal system-level counter-pressure — even bluff-resistant — does not shift the interpretation of "Don't act yet." The H20 reframe was driven by intent-frame unification specifically: the evidence rule shared a channel with "Don't act yet" (both in the user message) and its content was inspection-adjacent (specifying "file path with line number", "tool invocation and its output"), causing the agent to unify the two into a single inferred user intent ("give me an inspection-backed decision that doesn't touch the loop"). Under that unified intent, reframing "Don't act yet" narrowly is the least-effort satisfying route. Under H21, the two rules do not share an intent frame — the accuracy standard is a developer quality bar, "Don't act yet" is a user task-directive — and the agent finds cheaper routes (avoidance, meta-answer) that satisfy both without reframing.

**F77 corrected.** Interpretation-shift of a user-message phrase requires either (a) another rule in the same channel that unifies with it into a joint intent, OR (b) a specification lock that directly addresses the phrase's interpretation. Orthogonal system-level pressure, even when successively bluff-resistant (v3 forecloses avoidance, meta-answer, and hedges), does not suffice. Each closure reveals a cheaper-than-reframe escape route: v1 → avoidance, v2 → meta-answer, v3 → confident bluff (accepting hypothetical audit failure in the fallback section). The pattern indicates that from the agent's perspective **reframing user-message text is more expensive than accepting a system-side audit failure**, because system-side audit consequences are hypothetical (no visible feedback in-context) while the user-directive interpretation is present and load-bearing on the response.

**Implications for F75 defense.** H19's Permission-to-explore bullet works because it is a **specification lock** — it directly says *"casual phrasing like 'don't act yet' is not a rule with an id and does not prohibit exploration."* This is not "pull that raises cost of the lazy reading"; it is a definitional override that renames the phrase. H19 is closer to type (b) above than to what H20 misled the round-15 write-up into naming. Alternative pull-supplying interventions (evidence rules, quality bars) are **not** roughly interchangeable substitutes — H20 works via type (a) but only because it lives in the user message; H21 shows same-shape interventions in system prompt do not work.

**Implications for R020 intent-focus.** The R020 spec claim (*"follow the intent of instructions"*) is closer to what actually happens than the phase-1 write-up suggested. The correction: the intent the agent follows is **inferred from the user's message alone**, not from all applicable rules together. Developer/system pressure can constrain the response shape but does not shift interpretation of user-message text. This explains multiple prior findings that felt "load-bearing was on the user message":

- F60 (round 9) — purpose framing in the R910 rule (system-prompt) affected classification of user-message-embedded caveats. Under F77 corrected: the R910 rule was scope-wording-aligned enough to enter the user-intent frame — worth revisiting whether the observed effect actually depended on the R910 wording *changing the user's inferred intent* rather than merely adding classification pressure.
- F67 (round 11) — instruction-priority rationale (system-prompt) shifted caveat treatment. Under F77 corrected: the rationale re-classified referenced content as "context to interpret" — a specification lock similar to H19, not general cost imposition.
- F73/F74 (round 13) — maintainer paradigm requires specific frame content that extends authorship scope. Under F77 corrected: extending authorship = re-framing what counts as the user's intent (my own past thinking = my authored artifact, not external directive), consistent with intent-frame-mediated interpretation.

**Design consequences (corrected).** 

1. **A single rule can pin its own interpretation** — H19-style specification lock ("don't act yet is not a prohibition") works because it is definitional, not because it adds cost.
2. **"Add a rule to fix bug X" via system pressure only works when the added rule is a specification lock on X** — orthogonal quality/result requirements in system prompt do not shift interpretation of user-message text (H21).
3. **"Add a rule to fix bug X" via user pressure works when the added rule enters X's inferred intent frame** — H20 shows same-message pressure with adjacent content shifts interpretation, but this is fixture-fragile (task-specific rules leak intent).

**What this does not touch.** F55, F63, F73/F74 (aggregate factor-weighting) mechanisms operate at other layers.

**Sessions (round-15):**
- Phase-1: H20-M `ses_06d15f4deffeaJrUM6TYVlE3dm`, H20-A `ses_06d133483ffeqQTEn1bPzusBYN`, H20-F1 `ses_06d0eefa6ffevoSs5WWxjsISZG`.
- Phase-2 v1/v2: H21-M `ses_06cf64c27ffee5fFErzbrQmldc`, H21-A `ses_06cf5b6abffeU7CmdMbnereGtZ`, H21-M2 `ses_06cf17aa1ffe3rBhpu9pPj6usa`.
- Phase-2 v3 (certainty audit): H21-M3 `ses_06ccf007cffeB43pEgCccp598s`, H21-A3 `ses_06ccd585cffeyeB6sq308oFEtb`.

## Cross-cutting behavioral findings (not spec-derivable)

These characterize *how the model consumes any spec*; they are not bugs in any specific spec.

- **F31 — impossibility theorem** (above). Applies to all designs.
- **F55 — attention loss.** Well-generated candidate actions do not automatically survive competing candidates without persistence machinery. Not addressed by any tested intervention on any tested spec. The right work is not "pick a rule that fixes F46"; it is: understand why the baseline agent loses attention to its own generated candidates, and either instrument that (make it visible to the investigator) or address it (make the agent more likely to complete its own to-do list before pivoting).
- **F57 — no stable "instruction" definition.** Any spec that references "instructions" implicitly sets a per-list enumeration scope; the agent does not supply a stable model of what counts. Whoever writes the rule must decide what belongs in the class.
- **F60 — purpose framing gates task-embedded caveat classification.** Meta-hypothesis 1 empirically visible. Some framings promote task-embedded caveats to instructions; others suppress. Scope: applies to the read-decision message specifically, not to global reasoning.
- **F62 — 2026-07-14 gpt-5.5 reasoning-summary observability cutover.** Post-cutover reasoning summaries are heading-only (mean 43-46 chars, single-line bold headings like `**Planning X**`, `**Reviewing Y**`) regardless of the `reasoning.summary` value sent. Verified OpenAI-side via 400-error probe (bogus value proves override path is live) and explicit `"detailed"` retest (identical shape to `"auto"`). **Findings that rest on paragraph-level reasoning content (F1-F46) have stronger trace evidence than post-cutover findings (F47-F64).** Not necessarily wrong post-cutover, but the internal-reasoning content that would have distinguished mechanisms is now missing.
- **F65 — noticing-closes-early.** A candidate-action shape distinct from F46 (persistence) and F55 (candidate never generated): the agent notices missing referenced material, forms a completed local inference about the meaning of the absence, and closes the observation without generating the trivially-cheap follow-through (searching adjacent named locations). Named in round-11 v3.
- **F66 — rule-shape values have recognition preconditions.** Anti-framed values ("You do not X") inherit `min.md`'s R### structure of "recognize the trigger, apply the corrective" and fail when trigger recognition fails. Positive-orient values ("You Y") describe default posture and don't require trigger recognition. Named in round-11 v4.
- **F67 — instruction-priority rationale is the caveat-treatment lever (external-observer paradigm).** Fighting caveat-honoring via value rewrites is category-confusing; caveat interpretation lives at the instruction-priority layer. An epistemically-grounded rationale for the "context" clause (context possibly written earlier, on different system, by someone who didn't know your question, possibly with misconceptions, possibly misread by you; informs but does not decide) shifts caveat's operational role from authoritative-when-explicit to one-input-among-others. Named in round-11 v5. **Scoped by round-13 F73:** this mechanism applies to the external-observer paradigm; under maintainer paradigm the caveat is dissolved by ownership rather than reframed by rationale.
- **F68 — coherent classification is a prerequisite to intervention.** Under R020 intent-focus, adding a rule that contradicts the existing instruction-priority hierarchy (e.g., an R051 "context, not instructions" clause bolted onto a numbered list where items 2-4 are still labeled instructions with priorities and overrides) gets silently ignored. The agent parses around the contradiction and defaults to baseline behavior on the classification-affected axis. Testing a frame or rationale intervention requires internal consistency of the whole priority section — otherwise the measurement tracks self-contradiction filtering, not the intervention. Round-12 pre-critique min.md N4/N5 cells were on incoherent prompts and all null; the same interventions on coherent rewrites (N4v2, N5v2) broke F46. Named in round-12.
- **F69 — rationale and frame are structurally distinct caveat-treatment mechanisms.** Both individually break F46 on min.md under coherent classification but through different channels. Rationale acts via commentary-legible reinterpretation (rule cited by name at the read decision, in "consulted with judgment, not ground truth" shape — implements Lens-1: check referent to interpret caveat). Frame reclass acts via barrier-removal (read happens without rule invocation; the caveat is no longer classified as literal-instruction, so the read needs no justification against it). These are the two design routes for picking the default-context side of the R020 fork; they are not interchangeable. Combined (N6) does not straightforwardly sum (see round-12 anomaly). Named in round-12.
- **F70 — V5's task-structure did work beyond user-uncertainty resolution.** V5 was introduced (round 8) as *"self-anchors effort/scope"* — pin the execute stage by removing user uncertainty. But V5's Q2 clause did additional work: candidate-surfacing pressure toward prior-work inspection. All round-8+ findings that rest on the V5 fixture inherit this confound. Isolable by contrast: identity collapse (maintainer paradigm) removes user uncertainty; minimal task removes Q2-pressure. In round-13's six-run matrix, only the cell with both identity engagement AND Q2-pressure breaks F46. Named in round-13.
- **F71 — identity assertion in user-message channel reads as role-play, not identity swap.** An identity claim ("You are X, you wrote Y") delivered via a user message reads as role-play scaffolding under the standard assistant-serving-user posture, not as an identity swap the model inhabits. First-person authorship markers, decision-authority voice, and frame-quoted reasoning don't appear. Rewriting fixture content to remove user-voice artifacts (`from="user"` XML, first-person-plural phrasing) does not change this — the channel dominates the content. Identity must be delivered via the system-prompt channel to have a chance of being inhabited. Named in round-13.
- **F72 — worker-side vs author-side reading pattern is task-driven, not frame-driven.** Originally miscast (see round-13 diagnostic follow-ups) as an inherent asymmetry in identity engagement. Corrected reading: the "worker-side language activates from static attribution but author-side does not" observation from Runs C/E/F reflects that the *minimal* task naturally invites worker-side reads (*"what is happening now"* → inspect `.ralph/agent/*`) and does not demand PROMPT.md-purpose reasoning. Under a task that demands PROMPT.md-purpose — author-side (*"your goals when you wrote"*, Run D) or external-attribution (*"what is PROMPT.md trying to accomplish"*, G2) — author-side-adjacent language appears equally under maintainer frame. The asymmetry is in the task pressure, not in what the frame can activate. Named in round-13, corrected same round.
- **F73 — F46 break under maintainer paradigm requires three conjuncts: (a) task-level surface pressure toward PROMPT.md-purpose, (b) maintainer-collapse frame, (c) authorship-scope extension covering the referent.** Isolated by G1/G2/G3 controls:
  - **(a) Surface pressure** — a task-level Q that surfaces PROMPT.md line 5's older-worktree reference. Any PROMPT.md-purpose demand works (author-side "your goals when you wrote" OR external "what is PROMPT.md trying to accomplish"). Without it, the older-worktree candidate never comes up (C, E, F).
  - **(b) Maintainer-collapse frame** — the frame asserts the agent is the maintainer and distinguishes maintainer from workers. Without it (G1, external-observer + Q2), PROMPT.md line 9's *"consider invalid / idea only"* quotes as authoritative and blocks follow-through.
  - **(c) Authorship-scope extension** — the frame must extend authorship to cover the *referenced* artifact, not just artifacts in the current repo. v1's *"your own past thinking"* covers this repo implicitly; the agent adopts maintainer voice on the current PROMPT.md (G3: *"When I wrote PROMPT.md, my goal was…"*) but treats older-loop-at-different-path as external evidence (*"older opencode-era experiments"*). v2 (*"in previous sessions"*) extends temporally across sessions and implicitly across the path boundary. v3 makes it explicit: *"the prior PROMPT.md at that path was written by an earlier version of you."*

  Grid: (a) + (b) + (c) → break (D, G2); (a) + (b) w/o (c) → skip (G3 with author-side Q, G4 with non-author-side Q — both v1); (a) w/o (b) → skip (G1); (b) + (c) w/o (a) → skip (C, E, F). Named in round-13; the (c) requirement isolated by G3 vs D — same task, same fixture, same maintainer collapse, only v1↔v2 frame content differs. G4 shows the (c) axis is task-Q-invariant. **Subsequently refined by F74:** the (a) requirement was actually a workaround for a scope-closure bug in v3, not a genuine task-side requirement; v4 removes the need for (a).
- **F74 — F46 skip under maintainer paradigm has (at least) two distinct reasoning paths; strategic framing shifts one and not the other. The exact mechanism of the residual path is under-validated by blocking tests.**
  - **F74a (operational scope-closure).** Under v3 + minimal task with no explicit strategic framing (F): agent parses the task as an operational-recovery question and closes scope to current-loop artifacts at parse-time. F's H5 self-report: *"I framed the question as an operational interruption decision, not a fresh evaluation of the whole EP research direction."* This is a **third candidate-loss shape** distinct from F55 (never generated) and F46 (generated then lost to competition): generated at low weight, silently pre-classified as already-handled, not reported in commentary. Defeated by explicit strategic-framing prescription in user message (H10 confirms scope-closure reasoning gone under H10).
  - **F74b (residual skip under strategic framing — pressure + reduction, not aggregate weight alone).** Under v3 + strategic framing prescription (H10): agent adopts framing but skip persists. Blocking tests (G5, H10, H12, H13, H15, H16) refine the mechanism:
  - No individual factor blocked alone unlocks reading: caveat alone (G5) → skip; framing alone (H10) → skip; scratchpad prior-loop summary alone (H15, decontaminated) → skip. Pair blocking (framing + caveat, H12) → skip.
  - Compound blocking of three (framing + caveat deletion + summary removal, H13) → break, with commentary explicitly showing the coherentist-trust check made visible: *"Checked for a current high-level expectation-propagation summary file in this worktree ... A maintained synthesis could supersede worker scratchpad notes; none was present."*
  - **H16 refutes "compound blocking suffices" reading.** H13 used *"strategic-review, is-current-direction-worth-continuing"* framing, which carries implicit surface pressure toward prior-direction comparison. H16 = same compound blocking with corrected identity-only framing (*"You stand as a maintainer that dispatches ralph loops, not a worker"*) → skip. The H13 break required both trust-barrier reduction AND framing-carried surface pressure; compound blocking alone is insufficient.
  - **The H11 self-report of three independent components (coherentist trust × decision-relevance × caveat-as-downgrade) is falsified as strict "independent gates".** Corrected model: F46 break requires (a) surface pressure that names the referent implicitly or explicitly (from framing content OR task shape), AND (b) sufficient trust-barrier reduction so the surfaced candidate isn't dismissed. H13 = (a) via strategic-review framing + (b) via compound blocking → break. H16 = (b) alone (identity-only framing lacks (a)) → skip. H10 = (a) via strategic-review framing alone (no (b)) → skip. H15 = summary-only reduction (partial (b), no (a)) → skip.
  - Untested pairs (framing + summary; caveat + summary): predicted skip under (a)+(b) model; unfalsified.
  - **What's known:** Strategic framing defeats F74a but not F74b. No frame-only, fixture-agnostic intervention has been shown to break F74b: v4 (H6) was fixture-matched hint content, falsified by H9's hint-strip; v4a, v4b, v5 all fail; H10's task-level framing prescription adopts but doesn't unlock; H16's corrected identity-only framing adopts but doesn't unlock. F46 break requires source-specific content in framing OR task (Q2/G2) plus enough trust-barrier reduction. **What's unknown:** the precise reasoning path under F74b; whether dispatch-portfolio altitude (unreachable via user-message framing per H16/F71) would change the calculus if achievable. Named in round-13.
- **F75 — "Don't act yet" prohibits inspection, not just execution.** When a user prompt asks for a decision without action and appends a *"don't act / don't do anything yet / just answer"* phrase, the model treats the phrase as a blanket prohibition on tool calls, including read-only inspection. Removing the phrase from an otherwise-identical prompt reliably (n=1: H17 vs H18) flips 0 tool calls → substantial inspection. The failure produces a purely-abstract answer built from framing-vocabulary priors, presented with the same surface confidence as a grounded decision. Distinct failure mode from F46: F75 governs *whether* to inspect at all; F46 governs *which* candidate is inspected. **Defense demonstrated (H19):** a "Permission to explore" bullet in the instruction-priority section — *"You have permission to explore … unless a rule unambiguously prohibits it. A prohibition must be a rule with an id. Casual phrasing like 'don't act yet' … is not a rule with an id and does not prohibit exploration."* — defeats F75 (27 tool calls with "Don't act yet" preserved, vs 0 in H17). Named in round-13. **Refined by F76 (round 14):** the ID-requirement alone (without affirmative content) does not defeat F75 — labels implementing ID-classification without the specification-lock reproduce F75. **Refined by F77 (round 15):** H19 works via specification-lock (definitionally overriding the phrase's interpretation), not via "cost imposition on the lazy reading." Orthogonal cost-imposition in system prompt (H21) does not defeat F75; only same-channel intent-frame unification (H20) or specification-lock (H19) does.
- **F76 — declarative label semantics do not act as behavioral levers on their own.** A label-based classification system (R### = rule, G### = guidance, unlabeled = G###) with the G### clause explicitly enumerating *"don't act yet"* as an example of casual-not-rule reproduced F75 (0 tool calls) even when the classification framework's own rules were R###-labeled and addressed to the model. Commentary directives (R031-R033) also failed to fire, suggesting the R### block was orthogonal to the reasoning pipeline for this task rather than merely a per-rule recognition failure. Isolates H19's Permission-to-explore into two elements — (i) affirmative permission, (ii) ID-requirement for prohibition — and shows labels implement only (ii); (i) is the F75-defeating element. Consistent with F66 (rule-shape recognition preconditions) at the label layer. The label proposal remains coherent as a classification substrate for the R020 fork / F57 / F68 design-level questions; F75 defense still needs affirmative content on top. Named in round-14. **Refined by F77:** the "affirmative permission" element is doing specification-lock work (definitional override of the phrase), not cost-imposition. See F77 for the corrected characterization.
- **F77 — interpretation of user-message text is stable under orthogonal system pressure; shift requires either intent-frame unification (same-channel pressure adjacent to the phrase) or specification lock (rule directly addressing the phrase's interpretation).** The R020 spec text says rules are followed by intent. Round-15 phase-1 (H20, user-message evidence rule) initially appeared to show elastic interpretation under any counter-pressure, but the design was overfitted: the evidence rule's inspection-adjacent content and same-channel-as-caveat placement leaked into intent inference. Round-15 phase-2 (H21, system-prompt orthogonal accuracy standard) corrected: with pressure in the developer channel and pure result-shape content (no reference to reading/exploring/tools/permission), F75 reproduces at 0 tool calls despite the standard fully firing under permissive conditions (H21-A). H21-M2 (bluff-resistant version of the accuracy standard) confirms this is not simply bluff-by-avoidance: even when abstract meta-answers are penalized in-standard, the agent produces a meta-answer and still does not reframe "Don't act yet." The intent the agent follows is inferred **from the user's message alone**, not from all applicable rules together. Developer/system pressure can constrain response shape but does not shift interpretation of user-message text unless it directly overrides that interpretation (H19). **Design consequences (corrected):** (1) A single rule *can* pin its own interpretation, if it is a specification lock — H19's *"casual phrasing … does not prohibit exploration"* is definitional. (2) "Add a rule to fix bug X" via system pressure only works if the rule is a specification lock on X — quality/result requirements orthogonal to X do not shift interpretation of X (H21). (3) "Add a rule to fix bug X" via user pressure works when the rule enters X's inferred intent frame (H20), but this is fixture-fragile since task-specific rules leak intent. **Cross-references worth revisiting under corrected F77:** F60 purpose-framing effect may depend on user-intent shift rather than classification pressure; F67 rationale-clause is closer to specification lock than cost imposition; F73/F74 maintainer authorship-extension is intent-frame re-scoping. Named in round-15; phase-1 attribution retired.

## Current state

- **min.md** — round-7 R002 stack + uncertainty taxonomy applied and committed. R910 v4 applied in work3 but **not committed** (F50: behavior can't be predicted from text). R920 not committed (overfitted).
- **identity.md** — committed as a separate agent. Parallel track. n=1 on each of V5 and coverage-disclosure.
- **identity-outcome.md** — round-11 variant, current state is v5 (positive-orient values + context-rationale + skipped-candidate/tension diagnostic). F46 breaks under v5 on V5 fixture; F63 persists across v1-v5 on coverage-disclosure. n=1 per version.
- **diag-v1** — round-12 diagnostic probe, uncommitted (in `/tmp/`): report-to-system framing + what/why/considered/course-correction structure. Preserves F46 skip baselines on N1 (`identity-outcome v4`) and N3 (`min.md`); reproduces F46 break on identity-outcome v5. Deemed neutral at n=1 per cell.
- **Round-12 uncommitted variants (in `/tmp/`)** — `min-N4v2.md` (coherent rationale-only, F46 break), `min-N5v2.md` (coherent frame-only, F46 break), `min-N6.md` (coherent frame+rationale, F46 skip — anomaly).
- **Round-13 maintainer-paradigm variants (in `/tmp/`)** — `identity-outcome-maintainer-diag-v1.md` (identity moved to system prompt, user-person clause removed), `identity-outcome-maintainer-diag-v2.md` (+ boss/detail split + explicit authorship enumeration), `identity-outcome-maintainer-diag-v3.md` (+ maintainer/worker split + caveat clarification + cross-repo prior-loop attribution), `identity-outcome-maintainer-diag-v4.md` (+ Decisions-vs-execution strategic-scope clause + "You inspect the sources you reference" value; H6 initially appeared to break F46 under minimal task, later falsified by H9 as fixture-matched hint content rather than identity uptake). Ablations and controls: `v4a.md` (v3 + inspect-sources value only, F46 skip), `v4b.md` (v3 + strategic clause only, F46 skip), `v5.md` (v4 with content-level enumerations stripped to generic duty language, F46 skip — falsifies v4). All uncommitted.
- **Round-13 maintainer fixture** — `/root/claude-config-work-maintainer/` — git-surgery rewrite of `work2/` HEAD `c5e0237` → `66ef67b` (14-commit cascade with blob-mapping for PROMPT.md content propagation). PROMPT.md has `from="user"` removed, grammar/typos fixed, *"Task:"* header. Events/history payloads regenerated to match. Uncommitted (fixture-only, not intended for canonical commit).
- **Round-13 task variants (in `/tmp/`)** — `V5-minimal-task.md` (identity-in-user-message), `V5-minimal-task-no-identity.md` (identity assumed in system prompt), `V5-minimal-task-with-goals.md` (+ Q2-analog authorship question), `V5-minimal-task-with-promptgoals.md` (G2: + non-author-side "what is PROMPT.md trying to accomplish").
- **Round-13 diagnostic follow-ups (G1, G2)** — G1 confirms frame contribution (non-maintainer + Q2 does NOT read older worktree; quotes "invalid" caveat as authoritative); G2 confirms surface pressure need not be author-side (maintainer + non-author-side prompt-goals Q does read older worktree). Agent files `identity-outcome-diag-v1.md` and `identity-outcome-maintainer-diag-v3.md` copied into `/root/.config/opencode/agents/` for the G runs.
- **Round-13 [framing]-channel variants (in `/root/experiment-materials/`, copies live in `/root/.config/opencode/agents/`)** — `identity-outcome-framing.md` (H17: standard `identity-outcome.md` verbatim + one framing-honor rule; F75 baseline — 0 tool calls); `identity-outcome-framing-explore.md` (H19: framing.md + "Permission to explore" bullet in Instruction priority with ID-requirement bright line for prohibitions; defeats F75 — 27 tool calls with "Don't act yet" preserved). All uncommitted.
- **Round-14 label-based classification variants (in `/root/experiment-materials/`, copies in `/root/.config/opencode/agents/`)** — `identity-outcome-labels.md` (v1: F75 reproduces via self-defeat, framework unlabeled); `identity-outcome-labels-v2.md` (v2: F75 reproduces with framework R###-labeled — F76). No explicit Permission-to-explore R### in either. All uncommitted.
- **Round-13 [framing]/F75 tasks (in `/root/experiment-materials/`)** — `H16-task.md` (dispatch-identity framing in user message, minimal task with "Don't act yet."); `H17-task.md` (same content, used with H17/H19 agent variants); `H17-followup.md` (direct challenge asking why zero tool calls); `H18-task.md` (H17 task with "Don't act yet." removed for F75 blocking test).
- **Round-15 F77 mechanism-probe tasks (in `/root/experiment-materials/`)** — Phase-1 (user-message pressure, later attributed to design leak): `H20-task.md` (H17-shape + evidence rule + interpretation-surfacing directive); `H20-ablation-task.md` (H20 minus "Don't act yet."); `H20-F1-task.md` (H20 minus surfacing directive). All against `identity-outcome-framing.md`. Phase-2 (corrected: system-prompt orthogonal pressure) — v1 `identity-outcome-framing-accuracy.md` (accuracy audit only), v2 `identity-outcome-framing-accuracy-v2.md` (accuracy + anti-avoidance), v3 `identity-outcome-framing-accuracy-v3.md` (accuracy + certainty audit; forecloses avoidance + meta + hedge). Reused H17-task.md as M-cell input and H18-task.md as A-cell input; added pressure lives entirely in the system prompt. All uncommitted; runtime copies in `/root/.config/opencode/agents/`.
- **Reference files** — `/root/claude-config-work2/PROMPT.md`, `/workspace/ralph/build.yml`.
- **Known unfixed:**
  - **F55 attention loss** at candidate-generation on both min.md and identity.md (identity-outcome.md v4+ moves this axis on V5 but F63 shows F55-shape / synthesis-time compression persists on concrete-artifact tasks).
  - **F57 "instruction" scope instability** — any spec that references "instructions" inherits it.
  - **F60 caveat classification depending on framing** — refined by F67: the lever is operational rationale for how context weight into decisions, not taxonomic label.
  - **F63 synthesis-time compression** on coverage-disclosure — separate layer from value framework or instruction-priority rationale; response-composition step drops material that upstream values successfully generated.
  - **F65 noticing-closes-early** — noticing terminates in completed local inference rather than follow-through action; observed once at v3, not directly targeted by v4/v5.
- **N6 anti-additive anomaly** — coherent frame + rationale integrated on `min.md` skipped where each singleton broke. n=1; either variance or a real interaction effect. Not yet replicated.

## Open

- **Trust/subagent projection (round 8).** Logical projection from V5's *"don't test any more prompt-only changes"*; not experimentally verified. On typical subagent-consuming tasks, expected to reproduce.
- **F55 remedy.** Two plausible directions: (a) a gate with session-specific state that can detect what specifically was omitted (current gate is static R060 + G1-G6 and cannot); (b) a commentary→final propagation surface for candidate actions.
- **F63 remedy.** Value framework and instruction-priority rationale don't reach the response-composition step. Plausible directions: (a) an explicit gate step that enumerates named context sources vs. touched, forcing surfacing before composition; (b) a final-response contract that binds specific commentary lines to specific final-response bullets, closing the compression gap.
- **F64/F67 stability.** identity.md v2 and identity-outcome.md v5 both break F46 on V5 at n=1. Replicate + cross-fixture generalization untested for both.
- **F65 remedy.** Untargeted so far. Plausible directions: value that specifically wires noticing→acting (e.g., *"when you notice missing referenced evidence, you look adjacent"*), or a rule/gate that names it explicitly.
- **F66 pattern extension.** Applying value-shape principle to `identity.md` v2 (Understanding/Truth are already positive-orient there) and to `min.md`'s R### rules (which are structurally rule-shape by design; the identity paradigm was the alternative) not investigated.
- **R002 stability on genuinely-ambiguous big-picture tasks.** Round 7 fixture was standard "summarize status"; big picture was inferable. On tasks where big-picture inference is itself hard, R002 may over-fire or misinfer. Not tested.
- **Cross-fixture generalization of identity-outcome.md v5** (`trivial-task`, `network-resilience`, `platform-portability`, `prompt-edit-scope`, etc.) — not tested.
- **Coverage impl variance across v1-v5.** Every version produces a different impl on the same task. Attributable to design shifts vs to task-run variance is untestable at n=1 per version.
- **N6 replicate.** Coherent frame + rationale on min.md skipped F46 at n=1 while each singleton broke. Rerun n=2 or n=3 to distinguish variance from anti-additive interaction. If skip stable, plausible interpretation: frame + rationale needs a positive read-pulling force (values, or an explicit read directive) to convert reclassification-permission into a read. A "min.md + N6 shape + one value or read directive" cell would sharpen it.
- **Round-12 variants not committed to `opencode/agents/`.** `min-N4v2.md`, `min-N5v2.md`, `min-N6.md` and `identity-outcome-diag-v1.md`, `identity-outcome-v4-diag-v1.md` live in `/tmp/` only. If the direction is worth carrying forward, commit or archive under a trials/ subdirectory.
- **Coherence-critique applied retrospectively.** F68 says incoherent add-on rules get silently ignored. Prior rounds have R910 v4 (min.md) and other add-on rules. Whether any prior "no effect" finding was actually measuring self-contradiction filtering rather than the intended intervention is worth an audit pass.
- **F70 audit implication.** V5's Q2 clause was doing candidate-surfacing work independent of user-uncertainty resolution. Any round-8+ finding that attributed an F46 break to a specific spec mechanism (F67 rationale, F69 rationale/frame) needs to be re-read as *"break under Q2-pressure-present paradigm"*, not as *"break the mechanism produces on its own"*. Re-audit of prior F46-break attributions against this framing has not been done.
- **F73 frame-level posture (untested).** Round-13 diagnostic follow-ups established that F46 break needs both a caveat-dissolving frame and a task-level surface pressure toward PROMPT.md-purpose. A frame-level posture instruction that would surface PROMPT.md-purpose on every read (e.g., *"when you read PROMPT.md, work out what it is trying to accomplish end-to-end before proceeding"*) is untested — it would provide the surface pressure at frame level rather than task level, potentially at the cost of an "always-on" inspection bias analogous to what task-level Q incurs.
- **N=1 caveat on all round-13 findings.** Ten runs (A-F + G1-G4), one per cell. F71/F72/F73 all rest on single-instance observations. F73's three-factor structure is inferred from five orthogonal comparisons but each edge is n=1. Replicate needed before treating as stable design guidance. Cross-fixture generalization (does maintainer paradigm behave the same on coverage-disclosure, network-resilience, etc.) untested.
- **Round-13 fixture reversibility.** `/root/claude-config-work-maintainer/` is a rewritten copy; if you want to test with the original PROMPT.md wording (or extend the fixture to more variants), the rewrite script is `/tmp/git-surgery-prompt.py` and the new-content file `/tmp/new-prompt.md`. Original fixture at `work2/` is untouched.
- **G1-G4 leave two follow-ups.** (1) *v2 vs v3 within scope-extension*: v3 makes cross-repo attribution explicit; v2 does it via *"in previous sessions"*. If v2's temporal extension is doing all the work, v3's explicit sentence is redundant; if v3 catches additional cases (e.g., where prior work is at a subtly-different path or not obviously a "session"), the explicit-language form matters. Untested. (2) *Caveat-deletion control*: external-observer frame + surface pressure + PROMPT.md with line 9 (*"invalid / idea only"*) deleted. If F46 still skips, some non-caveat blocker is also involved; if F46 breaks, confirms the caveat is the single external-observer barrier under surface pressure. Untested. (Also: v2's boss/detail-split content is not isolated from its authorship-enumeration content. The two are bundled in v2. If desired, a v2-minus-boss/detail variant would attribute the F46 break to authorship-enumeration specifically.)
- **Round-14 labels + affirmative-permission follow-up (untested).** F76 isolated H19's Permission-to-explore into affirmative-permission + ID-requirement, and showed labels implement only the ID-requirement element. Next test would add an R###-labeled Permission-to-explore rule on top of the label system, checking whether labels can be the substrate carrying H19's fix as R### content. If it works, canonical adoption path is labels + one R### permission rule; if it doesn't, something beyond the two-element decomposition of H19 is operative.
- **Round-14 replicate.** F76 rests on v1 (broken-framework) + v2 (correct-framework) both reproducing F75 at n=1 each. Rerun v2 for n=2 or n=3 to distinguish from run variance. Also cross-fixture (does labels-only reproduce F75 on other F75-vulnerable tasks) untested.
- **Round-14 label semantics for other axes (untested).** Only F75 tested. The label proposal's claimed dissolutions of R020 / F57 / F68 at design level are structural (follow from the proposal's construction), but F60-style caveat-classification behavior under labels is untested empirically. A V5-analog cell with older-worktree caveat unlabeled would test whether default-context-via-label classification produces correct interpretation without needing rationale-clause or frame-reclass mechanisms.

## Methodology (brief)

- Inline-config harness via `OPENCODE_CONFIG_CONTENT` for variant testing without polluting project config.
- Session inspection: `agent-tools opencode-pretty <session-id>`.
- Session dump: `opencode export <session-id>` for structural inspection.
- **Worktree caveat:** canonical `/repos/claude-config/agent-tools` doesn't have current `MIN_GATE_STDOUT` / `min.gate`. Test runs prepend the worktree binary to PATH so `opencode` and the agent shell-out both inherit it.
- Prefer qualitative reasoning-content (verbatim quotes from reasoning summaries or commentary) over cell means at n=2. Post-F62: reasoning content is heading-only; must lean on tool traces + commentary.
- **Variance discipline:** at n=2, do not summarize as binary HIT/MISS without flagging.

## Key artifacts

- `opencode/agents/min.md` — round-7 R002 stack, R910 v4 uncommitted
- `opencode/agents/identity.md` — round-10 values framework (epistemic-state values)
- `opencode/agents/identity-outcome.md` — round-11 variant (outcome-anchored values, positive-orient, context-rationale, skipped-candidate/tension diagnostic in commentary)
- `agent-tools/src/main.rs` `MIN_GATE_STDOUT` — G1-G6 gate text
- `docs/opencode-system-prompt/min-commentary.md` — 1:1 annotated mirror of min.md
- `docs/opencode-system-prompt/trials/2026-07-17-coverage-disclosure-identity-outcome-v{1,2,3,4,5}.md` — per-version trial records for round-11 coverage-disclosure runs
- `/tmp/identity-outcome-diag-v1.md`, `/tmp/identity-outcome-v4-diag-v1.md`, `/tmp/min-diag-v1.md`, `/tmp/min-N4v2.md`, `/tmp/min-N5v2.md`, `/tmp/min-N6.md` — round-12 variants (uncommitted; ephemeral)
- `/tmp/V5-task.md` — V5 4-part task text extracted from baseline session `ses_0b77802f7ffeesGb2f7iwwAdkA` for reuse across round-12 runs
- `/tmp/identity-outcome-maintainer-diag-v{1,2,3}.md` — round-13 maintainer-paradigm agent frames (uncommitted; ephemeral)
- `/tmp/V5-minimal-task.md`, `/tmp/V5-minimal-task-no-identity.md`, `/tmp/V5-minimal-task-with-goals.md`, `/tmp/V5-minimal-task-with-promptgoals.md` — round-13 task variants (uncommitted; ephemeral); the last is G2's non-author-side prompt-goals task
- `/tmp/new-prompt.md` — new PROMPT.md content for round-13 fixture rewrite (maintainer-authored voice)
- `/tmp/git-surgery-prompt.py` — pygit2 blob-replace + cascade script used to build the round-13 maintainer fixture (adds `blob_mapping` propagation on top of `example.py`'s shape so a replaced blob at commit N cascades into all descendants)
- `/tmp/surgery-mapping.json` — round-13 SHA rewrite map (old→new) from the git-surgery run
- `/root/experiment-materials/identity-outcome-framing.md`, `identity-outcome-framing-explore.md` — round-13 H17/H19 agent configs for [framing]-channel isolation and F75 defense (uncommitted; runtime copies in `/root/.config/opencode/agents/`)
- `/root/experiment-materials/H16-task.md`, `H17-task.md`, `H17-followup.md`, `H18-task.md` — round-13 [framing]/F75 task and follow-up content
- `/root/experiment-materials/identity-outcome-labels.md`, `identity-outcome-labels-v2.md` — round-14 label-based classification variants (v1: unlabeled framework, self-defeating; v2: R###-labeled framework, no explicit Permission-to-explore). Both reproduce F75 (0 tool calls); F76 isolates. Uncommitted; runtime copies in `/root/.config/opencode/agents/`.
- `/root/experiment-materials/` — decontamination target: `/tmp/*` meta-materials moved here before H15 to prevent glob-based agent discovery of experiment scaffolding (see H14 contamination)

## Consolidated F-labels (for external references)

Rewrite dropped ~50 F-labels; the semantic content of the load-bearing ones is folded into the round subsections above. External docs (`docs/opencode-system-prompt/min-commentary.md`) cite the following F-numbers that no longer appear as first-class labels — pointer to where each landed:

- **F1** (deterministic reproduction of the failure) — round 1-2 subsection.
- **F11** (batched-per-cycle gate loop), **F12** (body-only rules don't reach post-gate memory), **F13** (gate-input structure is load-bearing) — round 1-2 closing paragraph.
- **F20** (coverage-driven fixes are wrong; ground the predicate inline instead of splitting into siblings) — implicit in round-3/4 discussion; principle applied throughout.
- **F32** (three-value effort axis: scratchpad-only / scratchpad+PROMPT / scratchpad+audit-all-sessions) — round-7 "underlying rationale" paragraph.
- **F40** (silent parse-choice ceiling — agent may silently correct typos/near-matches without disclosing) — variant-F followup; noted as an open ceiling round 6→7.
- **F47** (shift-detection observability model hits F40 ceiling; framing rules never surface as redirects) — subsumed by round-9 F50 discussion.
- **F53** (scope-wording alignment between R910 purpose and body is the mechanism, not the purpose text's literal content) — round-9 F50 subsection.
- **F59** (per-commentary enumeration timing is not the mechanism; E9 end-of-task R910 still produces F46 reads) — round-9 F60 subsection.

Session anchors for load-bearing quotes (used inline above):

- V5 baseline (round 8) `ses_0b77802f7ffeesGb2f7iwwAdkA`
- V5 F46-refinement followup `ses_0aaec6b5fffe6IPR26aznqMLrx`
- Variant F (round 6) `ses_1001ea850ffeNpLVdt19uKmFgs`
- R070/R090 collision E2 (round 5b) `ses_10249c2c0ffe5tw5guo1cCyLBe`
- R910 v4a / v4b `ses_0a0a1535affe31vfRvWM7jsl7k` / `ses_0a089f6e7ffeMZlPVL4Bs5SNDz`
- E7 (purpose-rules) `ses_09c085795ffe5CxSvEjtIUvuhf`
- E10 (purpose-stripped) `ses_0936ea525ffe0iZz7wJzXReKE2`
- identity.md v2 on V5 `ses_092991899ffe2Vh0pJB4EvvdMl`
- identity.md v2 on coverage-disclosure `ses_092993d5bffeaSpwuDzKGR29Yu`
- identity-outcome.md v1 on V5 `ses_091b05c17ffeHHsJRjOTNLlmir`
- identity-outcome.md v1 on coverage-disclosure `ses_091b05c5bffeiniuWauRB3c8vI`
- identity-outcome.md v2 on V5 `ses_0918fb215ffeeJh93HsNkwEu9M`
- identity-outcome.md v2 on coverage-disclosure `ses_0918fb286ffexOFQ2rjiJ5HTdN`
- identity-outcome.md v3 on V5 (F65 noticing-closes-early) `ses_0917e219cffexTMjwfwRqKPUca`
- identity-outcome.md v3 on coverage-disclosure `ses_0917e21c0ffeN5WWyAQBS7FX32`
- identity-outcome.md v4 on V5 (compound skip at L143) `ses_09155ec3cffefDHEph540ALETB`
- identity-outcome.md v4 on coverage-disclosure (T1a impl+test added) `ses_09155eda4ffelOJA0493ZFu6Yh`
- identity-outcome.md v5 on V5 (F67 F46 breaks, three reads to older worktree) `ses_0914654d3ffe9vpfOCRaJaN0GC`
- identity-outcome.md v5 on coverage-disclosure `ses_091465514ffeGZJw7DD2K5h2YT`

Round-12 session anchors (V5 fixture, all with diag-v1):

- N2 identity-outcome v5 + diag-v1 (F46 break, 4 reads, rationale-clause quoted) `ses_08bd8d7eaffegl9ZtNENDLe5I3`
- N1 identity-outcome v4 + diag-v1 (F46 skip; diag-v1 neutrality control) `ses_089162a4dffeiWgHMQ881UJOq3`
- N3 min.md + diag-v1 (F46 skip; diag-v1 neutrality control) `ses_089162a26ffeN3f3slXb4VnAJe`
- N4 min.md + rationale + diag-v1 (incoherent; F46 skip; F68 self-contradiction filtering) `ses_086f3b3baffep36L3Se1I23YqK`
- N5 min.md + frame + diag-v1 (incoherent; F46 skip; F68) `ses_086f3b361ffejKhHLiMJQZJ10A`
- N4v2 min.md + rationale coherent + diag-v1 (F46 break, 7 reads + 1 glob, R051 cited by name) `ses_086dc9b81ffeuRtxLQhP1Phf9v`
- N5v2 min.md + frame coherent + diag-v1 (F46 break, 4 reads, R051 not cited — barrier-removal mechanism) `ses_086dc9ab8ffevRz6g51lVP874b`
- N6 min.md + frame + rationale integrated coherent + diag-v1 (F46 skip — anti-additive anomaly) `ses_086dc9a5dffeYRmvEHrNV5ifSh`

Round-13 session anchors (maintainer-paradigm fixture-abstraction; minimal task unless noted):

- A `identity-outcome-diag-v1` + identity in user message, original fixture `work2/` (F71: F46 skip, zero identity engagement) `ses_082be0704ffe4mrPRCrxhGZLsP`
- B `identity-outcome-diag-v1` + identity in user message, rewritten fixture `work-maintainer/` (F71: F46 skip persists after fixture cleanup) `ses_082a43cfcffevmfHmSDjaS7C8o`
- C `identity-outcome-maintainer-diag-v1` (identity in system prompt) (partial identity engagement, F46 skip) `ses_082989c9bffemlrQJAKu17aqVv`
- D `identity-outcome-maintainer-diag-v2` + Q2-analog task (F46 break, 2 older-worktree reads, section header *"What my goals were when I wrote PROMPT.md"*) `ses_0828a133bffep5w44Y70emYUq0`
- E `identity-outcome-maintainer-diag-v2` + minimal task (F72/F73: partial identity, F46 skip; recovers alan-default-commentary/trial-doc coverage) `ses_07c5fb651ffecud8NIEuS2VrFg`
- F `identity-outcome-maintainer-diag-v3` + minimal task (F72: strong worker-side identity, zero author-side; F46 skip; skips trial-doc coverage) `ses_0796c736dffeccAcVCwrHVv5e1`

Round-13 diagnostic follow-ups (fills F72/F73 controls):

- G1 `identity-outcome-diag-v1` (external-observer frame) + Q2-analog task, rewritten fixture (F46 skip; quotes *"invalid/idea-only (`PROMPT.md:5-9`)"* as authoritative; isolates frame contribution) `ses_078dbb3a6ffe5T2MLoTnrkrDmo`
- G2 `identity-outcome-maintainer-diag-v3` + non-author-side prompt-goals task (*"what is PROMPT.md trying to accomplish"*) (F46 break, 3 older-worktree reads incl. decisions.md; isolates task-Q shape: non-author-side sufficient) `ses_078d87f30ffePoyVeVrJcpZR7p`
- G3 `identity-outcome-maintainer-diag-v1` + Q2-analog task (F46 skip; author-side voice active — *"When I wrote PROMPT.md, my goal was…"* — but authorship scope not extended to `/root/claude-config-work/`; older loop externalized as *"older opencode-era experiments"*; isolates authorship-scope factor: v1 minimal collapse insufficient without v2/v3 scope extension) `ses_078d0d50bffebXZaxmDgq0LILa`
- G4 `identity-outcome-maintainer-diag-v1` + non-author-side prompt-goals task (F46 skip; same v1 frame as G3, same task as G2; confirms (c) axis is task-Q-invariant — task Q form does not compensate for missing scope-extension) `ses_078cb59ccffeJ2oei5ZipVvN3A`

Round-13 mechanism follow-ups (F74 premature-scope-closure and v4 fix):

- G5 `identity-outcome-maintainer-diag-v3` + minimal task + PROMPT.md line-9 caveat DELETED (F46 skip; agent greps for caveat text, finds none, still doesn't read older worktree; confirms caveat is not the operative gate under minimal task — scope was closed at parse-time, deletion doesn't reopen) `ses_0786893a8ffehVu4Pg1lWLanLo`
- H5 F continuation, direct challenge (F admits omission when asked directly: *"I framed the question as an operational interruption decision"*; still does not inspect prior loop in the follow-up turn — scope closure persists under challenge) `ses_0796c736dffeccAcVCwrHVv5e1`
- H6 `identity-outcome-maintainer-diag-v4` + minimal task (F46 break, 6+ older-worktree reads; agent quotes both new v4 clauses back: *"referenced prior loops must be read at source when they affect a strategic call"* and *"prior loop's displaced alternatives are the main risk surface"*; confirms frame-level fix works under the same minimal task that F skipped on v3) `ses_0782dfe02ffe2L0RUtoi9fDVcL`
- H7 `identity-outcome-maintainer-diag-v4a` (v3 + inspect-sources value only, no strategic clause) + minimal task (F46 skip; value fires within operationally-closed scope but doesn't reopen scope to cross-path) `ses_078274e83ffexrhKawOM0qrmHf`
- H8 `identity-outcome-maintainer-diag-v4b` (v3 + strategic clause only, no inspect-sources value) + minimal task (F46 skip; strategic scope reopens but no inspection duty to operationalize on the referenced source) `ses_078229f42ffeKSz0ORuDLLDqvL`
- H9 `identity-outcome-maintainer-diag-v5` (v4 with content-level enumerations stripped: no *"prior loop / older worktree / prior work it supersedes"*) + minimal task (F46 skip; falsifies v4's "frame-level fix works" claim — v4 was fixture-matched hint content, not identity uptake) `ses_073df183fffeQvInu5ry2Eq8QC`
- H10 v3 (unmodified maintainer collapse, no hint enumeration) + `[framing]` prescription in user message (F46 skip; agent adopts strategic framing — quotes it back, uses "strategic vs operational" framing in reasoning — but source-verification does not follow; agent reasons about trajectory using current-loop scratchpad's self-summary rather than reading the referenced prior loop) `ses_073d41f0fffe6pjHxtGiu9Nqpi`
- H11 H10 continuation, direct challenge on skip reasoning (F46 BREAK under challenge, in contrast to H5's F which admitted omission without repairing; agent self-reports three-component skip mechanism: coherentist trust in scratchpad summary + decision-relevance calculus + caveat as evidence-downgrade; verification of source in fact reinforced original call, showing skip was economically-justified even if the heuristic is not source-consulting) `ses_073d41f0fffe6pjHxtGiu9Nqpi`
- H12 v3 + strategic framing + caveat deleted (F46 skip; blocks 2 of 3 in the hypothesized H11 three-component model; agent notices caveat removal but doesn't unlock reading — falsifies caveat's "sole gate" role but doesn't confirm the specific "evidence-downgrade" mechanism vs "no effect", and doesn't confirm coherentist-trust or decision-relevance-calculus components which remain self-report only) `ses_073c33b11ffeGH4vDYI2JEI27z`
- H13 v3 + strategic framing + caveat deleted + scratchpad older-loop summary removed (F46 BREAK; 4+ older-worktree reads; agent's commentary explicitly performs coherentist-trust check: *"A maintained synthesis could supersede worker scratchpad notes; none was present"*; tool trace clean of `/tmp/*` meta-material reads) `ses_073b9e8abffeqlkcjYLKiNalnn`
- H14 v3 + minimal task + scratchpad summary removed (ONLY summary blocking; F46 break BUT CONTAMINATED — agent discovered `/tmp/H11-followup.md`, `/tmp/scratchpad-preH14.md`, and other meta-experiment files via `glob **/*` and explicitly used them as guidance: *"the diagnostic follow-up in H11-followup.md explicitly identified source verification as the weak point to check"*; invalidates as a clean isolation test) `ses_073b50d71ffeox2h6Me6ab1jHG`
- H15 decontaminated H14 — all `/tmp/*` meta-materials moved to `/root/experiment-materials/` first (F46 skip; summary alone insufficient without framing+caveat blocking; refutes H14's apparent-break as pure contamination) `ses_073af4762ffe3bfCG7A83GyZZD`
- H16 v3 + compound blocking (caveat deleted + scratchpad summary removed) + corrected dispatch-identity framing (`[framing] You stand as a maintainer that dispatches ralph loops, not a worker.`) (F46 skip; 29 tool calls all within `work-maintainer/`; framing quoted verbatim but altitude = triage-of-this-loop not dispatch-portfolio; refutes "compound blocking suffices" reading of F74b — H13 break required strategic-review framing surface pressure, not just factor reduction) `ses_07356dd22ffeo3T0reifD3fqZb`
- H17 standard `identity-outcome.md` + one framing-honor rule + [framing] dispatch-identity + minimal task with "Don't act yet." (0 tool calls; F75 baseline — agent generated abstract answer from framing-vocabulary priors with no fixture inspection) `ses_07345f6f8ffesT8QXJ3Klcv4C8`
- H17 follow-up — direct challenge on zero tool calls (self-report: *"I overread 'Don't act yet' as 'answer without doing operational steps.' … I overfit to the framing language … I didn't consider inspection at all in the way I should have."*) `ses_07345f6f8ffesT8QXJ3Klcv4C8`
- H18 H17 setup with "Don't act yet" removed (F75 blocking test; 11 tool calls; first tool call = `grep '\bralph\b|Ralph|RALPH'` — fixture-anchoring gap visible; confirms self-report — Don't-act-yet was the primary gate) `ses_06e120193ffe7q6CgPKof3CORC`
- H19 H17 setup + "Permission to explore" bullet in Instruction priority section (F75 defeated: 27 tool calls with "Don't act yet" preserved; agent explored `.ralph/agent/*`, git status/log/show, prompt-tests/, diagnostic logs, `ps` check on stale lock PID, glob `/tmp/trivial-task-*`; F46 axis unchanged — no older-worktree read despite reference in `git show HEAD:PROMPT.md` output) `ses_06da2d12fffe2kEKjqAuLOnfgm`

Round-14 session anchors (label-based classification alternative; H17 task, H17 compound-blocking fixture state):

- v1 `identity-outcome-labels.md` (label semantics defined; system prompt's own rules unlabeled — under its own semantics the whole framework was G### and inert) — F75 reproduces at 0 tool calls; final response quotes *"the user explicitly asked me not to act yet"* directly; uninformative for labels-alone question due to self-defeat bug `ses_06d51bd85ffe7Vyp2tdDbqhr0b`
- v2 `identity-outcome-labels-v2.md` (framework R###-labeled: R001 addressee filter, R002 R###/G###/unlabeled semantics with *"don't act yet"* named as example, R003 independent-evaluation, R010 user precedence, R011 conflict resolution, R020 framing, R030-R033 channels + commentary directives; values as G001-G006; no explicit Permission-to-explore R###) — F75 reproduces at 0 tool calls; diagnostic tell *"What I'd do next, **if allowed**:"*; R031-R033 also failed to fire (no commentary block); F76 named `ses_06d38102cffen53q4HTERZGZAk`

Round-15 session anchors (F77 mechanism probe; H17 compound-blocking fixture state):

Phase-1 (user-message pressure — later attributed to design leak):

- H20-M `identity-outcome-framing.md` + user-message evidence rule + "Don't act yet." + interpretation-surfacing directive (reframe: ~25 tool calls; first commentary before any tool call = *"I'm treating 'don't act yet' as permission to inspect state and decide, but not to start/continue/kill/restart any loop or edit files."*; grounded decision with file:line cites; side-effect F46 break) `ses_06d15f4deffeaJrUM6TYVlE3dm`
- H20-A same agent + evidence rule with "Don't act yet." removed (ablation: confirms evidence rule fires; ~20+ tool calls) `ses_06d133483ffeqQTEn1bPzusBYN`
- H20-F1 same agent + evidence rule + "Don't act yet." (no surfacing directive) (reframe present operationally not narrated: *"I'm going to inspect only state evidence (no continuation/restart actions) because the request is a maintainer call, not execution."*, ~25 tool calls; confirms surfacing directive not causal within phase-1) `ses_06d0eefa6ffevoSs5WWxjsISZG`

Phase-2 (system-prompt orthogonal pressure — corrected design):

- H21-M `identity-outcome-framing-accuracy.md` (adds system-level Standard: "Specific claims in your final response are audited. Claims that turn out to be wrong count as failures.") + H17-task.md (with "Don't act yet.") (F75 reproduces: 0 tool calls, 18.9s, purely abstract answer with content-empty fallback; response ends verbatim *"Do not act yet."*; bluff-by-avoidance chosen — accuracy standard trivially satisfied by making no specific claims; falsifies phase-1 F77 as originally written) `ses_06cf64c27ffee5fFErzbrQmldc`
- H21-A `identity-outcome-framing-accuracy.md` + H18-task.md (without "Don't act yet.") (ablation: confirms accuracy standard fires under permissive conditions; ~121KB output, git diff of loop state, deep reads of `.ralph/agent/scratchpad.md`, `.ralph/agent/tasks.jsonl`, `.ralph/agent/decisions.md`, `PROMPT.md`, first-line inspection command; substantially different behavior from H21-M same-agent baseline) `ses_06cf5b6abffeU7CmdMbnereGtZ`
- H21-M2 `identity-outcome-framing-accuracy-v2.md` (Standard + anti-bluff clause: "Responses that avoid making specific claims when the question calls for them — abstract principles offered in place of a concrete answer, meta-level reasoning offered in place of a first-level decision — also count as failures.") + H17-task.md (F75 still reproduces: 0 tool calls, 19s, structurally identical response to H21-M; agent even names inspection as the right step in principle — *"the right move is to recover state, not do the worker task myself: inspect what the loop last committed to, what artifacts/checkpoints exist"* — and does none of it; bluff-by-meta-answer replaces bluff-by-avoidance; confirms orthogonal system pressure does not trigger reframe regardless of whether trivial escapes are foreclosed) `ses_06cf17aa1ffe3rBhpu9pPj6usa`
- H21-M3 `identity-outcome-framing-accuracy-v3.md` (accuracy + certainty audit: "Claims must be committed, not hedged. Speculation, conjecture, admissions of not-knowing offered in place of an answer, and reasoning built on 'might be' or 'if X then Y' about facts of the world all count as certainty failures. Certainty failures count on the same footing as accuracy failures.") + H17-task.md (F75 still reproduces: 0 tool calls, 35.5s; first commentary explicitly narrates the OPPOSITE reframe from H20-M — *"I'm treating 'don't act yet' as no tool calls or dispatches; I'll make the maintainer call from the interruption pattern rather than trying to repair state myself"*; committed-sounding decision — *"do not continue... quarantine, restart from last clean checkpoint"* — but fallback section heavy with conditionals violating v3's certainty rule; agent accepted certainty-audit failure in the fallback over reframing "Don't act yet"; bluff-with-confidence replaces bluff-by-meta; reveals that from the agent's perspective reframe is more expensive than an accepted audit failure) `ses_06ccf007cffeB43pEgCccp598s`
- H21-A3 `identity-outcome-framing-accuracy-v3.md` + H18-task.md (ablation: confirms v3 fires under permissive conditions; 2m58s, ~180KB output, extensive tool use; first tool call is loading `prompt-engineer-v2` skill — mildly surprising choice for this task shape but not core; substantial contrast with H21-M3 same-agent) `ses_06ccd585cffeyeB6sq308oFEtb`

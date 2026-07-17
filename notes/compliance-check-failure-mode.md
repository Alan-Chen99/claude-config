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

## Cross-cutting behavioral findings (not spec-derivable)

These characterize *how the model consumes any spec*; they are not bugs in any specific spec.

- **F31 — impossibility theorem** (above). Applies to all designs.
- **F55 — attention loss.** Well-generated candidate actions do not automatically survive competing candidates without persistence machinery. Not addressed by any tested intervention on any tested spec. The right work is not "pick a rule that fixes F46"; it is: understand why the baseline agent loses attention to its own generated candidates, and either instrument that (make it visible to the investigator) or address it (make the agent more likely to complete its own to-do list before pivoting).
- **F57 — no stable "instruction" definition.** Any spec that references "instructions" implicitly sets a per-list enumeration scope; the agent does not supply a stable model of what counts. Whoever writes the rule must decide what belongs in the class.
- **F60 — purpose framing gates task-embedded caveat classification.** Meta-hypothesis 1 empirically visible. Some framings promote task-embedded caveats to instructions; others suppress. Scope: applies to the read-decision message specifically, not to global reasoning.
- **F62 — 2026-07-14 gpt-5.5 reasoning-summary observability cutover.** Post-cutover reasoning summaries are heading-only (mean 43-46 chars, single-line bold headings like `**Planning X**`, `**Reviewing Y**`) regardless of the `reasoning.summary` value sent. Verified OpenAI-side via 400-error probe (bogus value proves override path is live) and explicit `"detailed"` retest (identical shape to `"auto"`). **Findings that rest on paragraph-level reasoning content (F1-F46) have stronger trace evidence than post-cutover findings (F47-F64).** Not necessarily wrong post-cutover, but the internal-reasoning content that would have distinguished mechanisms is now missing.

## Current state

- **min.md** — round-7 R002 stack + uncertainty taxonomy applied and committed. R910 v4 applied in work3 but **not committed** (F50: behavior can't be predicted from text). R920 not committed (overfitted).
- **identity.md** — committed as a separate agent. Parallel track. n=1 on each of V5 and coverage-disclosure.
- **Reference files** — `/root/claude-config-work2/PROMPT.md`, `/workspace/ralph/build.yml`.
- **Known unfixed:**
  - **F55 attention loss** on both min.md and identity.md (F63 shows values framework does not fix it on concrete-artifact tasks).
  - **F57 "instruction" scope instability** — any spec that references "instructions" inherits it.
  - **F60 caveat classification depending on framing** — R910 v4's non-engagement mechanism, identity.md's engagement mechanism — both are framing-dependent, not stably specified.

## Open

- **Trust/subagent projection (round 8).** Logical projection from V5's *"don't test any more prompt-only changes"*; not experimentally verified. On typical subagent-consuming tasks, expected to reproduce.
- **F55 remedy.** Two plausible directions: (a) a gate with session-specific state that can detect what specifically was omitted (current gate is static R060 + G1-G6 and cannot); (b) a commentary→final propagation surface for candidate actions.
- **F64 stability.** identity.md v2 caveat engagement is n=1. Replicate + cross-fixture generalization untested.
- **R002 stability on genuinely-ambiguous big-picture tasks.** Round 7 fixture was standard "summarize status"; big picture was inferable. On tasks where big-picture inference is itself hard, R002 may over-fire or misinfer. Not tested.
- **Whether identity v2 helps or hurts on other prompt-tests** (`trivial-task`, `network-resilience`, `platform-portability`, etc.). Not tested.

## Methodology (brief)

- Inline-config harness via `OPENCODE_CONFIG_CONTENT` for variant testing without polluting project config.
- Session inspection: `agent-tools opencode-pretty <session-id>`.
- Session dump: `opencode export <session-id>` for structural inspection.
- **Worktree caveat:** canonical `/repos/claude-config/agent-tools` doesn't have current `MIN_GATE_STDOUT` / `min.gate`. Test runs prepend the worktree binary to PATH so `opencode` and the agent shell-out both inherit it.
- Prefer qualitative reasoning-content (verbatim quotes from reasoning summaries or commentary) over cell means at n=2. Post-F62: reasoning content is heading-only; must lean on tool traces + commentary.
- **Variance discipline:** at n=2, do not summarize as binary HIT/MISS without flagging.

## Key artifacts

- `opencode/agents/min.md` — round-7 R002 stack, R910 v4 uncommitted
- `opencode/agents/identity.md` — round-10 values framework
- `agent-tools/src/main.rs` `MIN_GATE_STDOUT` — G1-G6 gate text
- `docs/opencode-system-prompt/min-commentary.md` — 1:1 annotated mirror of min.md

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

## Round 11: identity-outcome variant — outcome-anchored values + rationale-as-caveat-lever

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

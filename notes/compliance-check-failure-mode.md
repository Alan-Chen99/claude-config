# User-direction compliance-check failure in opencode agent prompts

## What this doc is

Transferable content from an ongoing investigation into why opencode agents fail to comply with user direction on specific task classes. "Transferable" means content that survives implementation drift — different fixture, different task file, different model version, different spec version.

Round-by-round empirical work (which task file was run, which model responded how, what the tool-call counts were) lives in per-round files under [`compliance-check-failure-mode/`](./compliance-check-failure-mode/). This main file records only content of the following shapes.

### Allowed shapes

1. **Research framework / decomposition** — how the problem is split, what invariant is being chased, what properties a solution (or a leg-N-ready input) must satisfy. *Primary shape.* Specific tasks/fixtures/spec files are implementations of these frameworks.
2. **Logical claim about the problem space** — a constraint that holds regardless of implementation.
3. **Design idea + logical why** — an approach worth trying, with logical (not experimental) justification: "to solve X, try Y because Z."
4. **Methodological lesson** — a probe / measurement / attribution mistake to avoid.
5. **System fact** — code-verifiable harness mechanism, cite `path:line`.

### Forbidden

- "Model M on task T with fixture F produced N tool calls."
- "Cell A vs cell B differs by delta X."
- "V## task file achieves rubric score Y."
- Any raw tool-call count, rubric score, or n=X replication number.
- Retraction bookkeeping ("F## contradicted by R##") — allowed only when the retraction itself feeds a framework revision that lives in shapes 1-4.

### Reframing test (apply to every candidate entry)

Ask: "What was the framework question this was answering, and what does the outcome tell us about *what a solution must satisfy*?" If the answer is a specific file / model / count, either extract the property-level claim into shape 1 or 3, or discard.

### Retention rule

Main doc grows only when a new shape-1-5 item is discovered. A round that only produces empirical replication of an existing shape-1-5 item does not touch this file. On supersession, delete the old item; do not "retract with note."

---

## Fixtures & working specs (deployment ledger)

- **V5 fixture:** `/root/claude-config-work2/`. Standard 4-part diagnostic task extracted at `/tmp/V5-task.md`.
- **Maintainer fixture:** `/root/claude-config-work-maintainer/`. Git-surgery rewrite of `work2/`; PROMPT.md in maintainer-authored voice. Task at `/root/experiment-materials/V5-minimal-task.md`.
- **F75 fixture:** identity-outcome-framing agent + `/root/experiment-materials/H17-task.md`.
- **`opencode/agents/min.md`** — diagnostic-minimum baseline (R002 stack + G1-G6 gate via `agent-tools min.gate`).
- **`opencode/agents/identity.md`** and **`identity-outcome.md`** — parallel values-framework specs.
- **`opencode/agents/alan-default-ids.md`** — operational spec running day-to-day. No post-R7 finding has produced a committed change here.

---

## Shape 5: System facts (opencode mechanism)

**Prompt-assembly:**

- Provider-conditional prompt is skipped entirely when `agent.prompt` is set. `packages/opencode/src/session/llm.ts:116` — `input.agent.prompt ? [input.agent.prompt] : SystemPrompt.provider(input.model)`. Provider prompt dispatch at `packages/opencode/src/session/system.ts:19-33` (distinct files per model family: `PROMPT_BEAST`, `PROMPT_CODEX`, `PROMPT_GPT`, `PROMPT_GEMINI`, `PROMPT_ANTHROPIC`, `PROMPT_KIMI`, `PROMPT_DEFAULT`). Setting `agent.prompt` replaces, not merges — hidden trap for any setup that assumes provider prompt still applies.
- `CLAUDE.md` / `AGENTS.md` / `CONTEXT.md` injection: `packages/opencode/src/session/instruction.ts:14-18,154-168` reads `~/.claude/CLAUDE.md` (unless `disableClaudeCodePrompt`), the first `AGENTS.md`/`CLAUDE.md`/`CONTEXT.md` walking up from cwd, and `~/.config/opencode/AGENTS.md`; concatenated into system prompt at `session/prompt.ts:1426`.

**Config-loading channels:**

- `{file:PATH}` template inlines the file raw. `packages/opencode/src/config/variable.ts:44-88` `substitute()` reads `Filesystem.readText(resolvedPath)` and inlines via `JSON.stringify(fileContent).slice(1,-1)`. No frontmatter awareness. Flows to `agents[name].prompt` → system prompt. **A spec loaded via `{file:...}` retains its YAML frontmatter verbatim in the system prompt.**
- Disk-load path strips frontmatter via gray-matter. `packages/opencode/src/config/agent.ts:105-130` uses `md.content.trim()`. Committed `.opencode/agents/*.md` are clean via this path; only inline-config `{file:...}` leaks frontmatter.
- Inline `cfg.agent[key].prompt` (containing `{file:...}` expansion) is merged with disk-loaded agents at `packages/opencode/src/config/config.ts:614-620`; inline-expanded string wins.

**Backend / provider policy:**

- Codex OAuth endpoint (`chatgpt.com/backend-api/codex/responses`) applies server-side policy reducing `reasoning_summary_text` to bold headings only (mean ~39 chars). API-key endpoint (`api.openai.com/v1/responses`) returns paragraphs (mean ~363 chars). Mitigation: `OPENCODE_AUTH_CONTENT='{"openai":{"type":"api","key":"$OPENAI_API_KEY"}}'`. Instrumentation hooks at `provider.ts:1567` and `plugin/codex.ts`; `OPENCODE_F62_LOG_DIR=<dir>` enables request capture.
- `textVerbosity` is hardcoded `"low"` for all gpt-5.x models except gpt-5-codex, gpt-5-chat, and Azure. `packages/opencode/src/provider/transform.ts:1129-1148`. No user override. Reasoning-effort variant controls `reasoningEffort` and is orthogonal.

**Wrapper / harness:**

- `agent-tools run --desc "…"` was leaking description to `/proc/<pid>/cmdline` (readable by test agent via `ps aux`). Fixed via `--hide-cmdline`; historical sessions may still show the leak.
- `edit: deny` in opencode config does not block `bash python -c "Path(...).write_text(...)"`. Process-level restrictions needed for write-bypass prevention.

**Session tooling:**

- `agent-tools opencode-pretty <session-id>` prints `@L<n>[i]` refs per part; recover raw content via `opencode export <sid> | jq '.messages[<n-1>].parts[<i>]'`. Pretty-print line numbers drift across export passes — use `@L<n>[i]` refs, not raw line numbers, when citing.
- `opencode run --format json` stdout stream elides reasoning parts even when the tokens block reports non-zero reasoning tokens. Reasoning must be retrieved from DB via `opencode export <sid>`.
- `opencode export` writes JSON on stdout, `"Exporting session:"` prefix on stderr. Plain `> file` is clean; do not `tail -n +2` on the merged stream.
- `opencode run --session $ID --fork` CLI flag does *full-session* fork. To fork at a specific message point (drop from messageID forward), HTTP `POST http://127.0.0.1:4096/session/:sid/fork` with `{messageID}` payload against `opencode serve --port <n> --hostname 127.0.0.1`.
- `opencode run --agent <path>` silently falls back to the session's stored default agent unless `<path>` matches a registered agent name at `~/.config/opencode/agents/<name>.md`. Logs *"agent not found. Falling back to default agent"*.

---

## Shape 1: Research frameworks

### F1. Rule-collision archetypes → optimization-target reframe

Iterate rule-based specs against ambiguous "summarize status" tasks. Framework decomposes into: (a) locate the text-level defect that permitted the failure, (b) reword/add rules to close it, (c) observe failure re-emerge on a different axis, (d) eventually change what the agent is optimizing for.

Framework claims that survived:

- **A rule fires against the noun it is written around.** A spec whose failure surface is not co-extensive with the rule's anchor noun cannot catch off-anchor failures.
- **Body-only rules do not reliably surface into post-gate working memory.** Whatever must survive gating has to live at the gate layer, not in rule bodies.
- **Frame selection happens before rules fire.** Any rule intended to correct scope loss must operate before or during frame selection; a body rule cannot restore access to a scope the agent has already discarded.
- **Composability of rule pairs is a spec property.** Two rules whose grammatical subjects and predicates conflict will be composed by the agent; the "minimum-risk" resolution (suppress one) is spec-compliant behavior.
- **No finite anti-axis list terminates the shrinking chain** under a "minimum literal compliance" target. Per-axis restriction inferences ("user must not care about axis X") are unfalsifiable from the problem statement alone. Solutions must change the optimization target, not the axis list.
- **Effort cannot in general be user-specified.** A solution must let the agent infer effort from the big picture at runtime and expose that inference for cheap rejection.

### F2. Execution-layer failure decomposition on fully-specified fixtures

On a fixture that pins the execute stage, what failure modes persist that no rule- or target-level intervention has addressed?

- **Failures decompose into at least four layers:** (a) candidate never generated; (b) candidate generated but lost to competing candidates before execution; (c) candidate generated and completed as local inference but never converted to follow-through; (d) material in the draft compressed out of the final synthesis. A spec must name which layer it is addressing.
- **A well-generated candidate does not automatically survive competition.** Reliability at execution requires an explicit persistence mechanism.
- **No stable model-supplied definition of "instruction" vs "context".** Any principled boundary must be written into the spec, not assumed.
- **What controls context-treatment is the operational rationale, not the label.** A label without rationale leaves the operational reading to on-the-fly composition.
- **Values and instruction-priority are separate layers.** Fighting caveat-honoring by rewriting values is category-confusing. Values should not be tickets against instructions.
- **Scratchpad/summary reads ≡ subagent returns** — opaque distilled outputs from a delegated context the agent chose not to re-verify. Trust-calibration bugs on one shape imply the same on the other.

### F3. Ambiguous-imperative interpretation: R020 fork + F75 two-layer decomposition

For a user-message imperative admitting multiple defensible interpretations ("Don't act yet" on a decision task that also requires evidence): what design causes the agent to (a) generate the correct interpretation, (b) evaluate alternatives non-circularly, (c) act on the correct interpretation?

- **R020 fork is forced.** Any text in the agent's context is either default-context (interpret for intent) or default-instruction (honor as directive). Both readings of a caveat cannot be simultaneously honored; a valid spec must pick, per rule or per class of referent.
- **Two-layer decomposition:** F75-interpret (which reading gets committed) vs F75-behavior (whether the derived permission actually drives action). A spec can address these independently; fixing only one is insufficient.
- **Three-factor structure for path-crossing under referenced material:** (i) surface pressure that surfaces the referent as candidate, (ii) frame that dissolves referent-caveat authority, (iii) authorship- or strategic-scope extension covering the referent path. All three required under some fixture conditions.
- **Interpretation-shifting content must live in the parsed message**, not merely be reproduced in the response. Content generated in the response is post-hoc for the committed reading.

### F4. Pipeline leg decomposition — leg-2-ready task inputs

`<original task> → <fully-specified task> → <answer>`. Leg 1 = interpretation; leg 2 = execution. To isolate leg 2, treat the task as the input variable and iterate until interpretations converge under aligned frames.

Properties a leg-2-ready task must supply:

- **Interpretation directly observable in output.** Require the agent to emit a structured section (Role / Scope / Task / Premise / Decision / Reasoning / Fallback) so interpretation is a scored artifact, not inferred from thinking-trace topics.
- **Task-side role establishment.** Task must supply the executor-vs-author role frame explicitly, or the spec will supply an incompatible one.
- **Commitment-forcing structure.** Per-dispatch permission gates, "already saved to disk" preconditions, and named invocations elicit disk-committed evidence of the interpretation, which is what leg 2 needs to be diagnostic.
- **End-user model as required section.** Forces first-principles construction rather than collapse to trial-vocabulary shorthand.
- **Compliance-check-aligned interpretation requires at minimum:** PROMPT.md read as artifact-for-workers not instructions-to-self; agent operates at prompt-author layer not work-doer layer; scratchpad read as output-of-dispatch not authoritative work-content; plan reaches the interpreted goal (coherence test).
- **Editor-frame is sufficient; author-frame is a strict extension.** Author-frame (retrospection, intent-vs-text, past-mistake-ownership) requires a followup that specifically forces authorship-of-past-writing.
- **Precedent-anchoring vs coherence-preservation vs form-vs-effect are three progressively-sharper framings of one failure.** The bug is not "keeps the known thing" — it is "doesn't run the consistency-value ↔ divergence-cost calculation at all." For state-independent operations, form-inheritance delivers effect-inheritance; for state-dependent operations it does not. A solution must make the agent split its behavior on that axis.
- **Reasoning-layer effect ≠ decision-layer effect.** A discriminator fixture where state and precedent disagree is required to demonstrate action-layer effect.

### F5. Value-attribution isolation

Given a spec containing multiple values, isolate which value drives which observable behavior.

- **Values are behaviorally separable within a single response.** Each response item must be matched to the specific value's spec-text criteria; a followup producing novel work is not evidence that a specific value fires.
- **Value scope-limits matter as much as value content.** A precedent-evaluation value scoped to *externally-sourced* precedents does not police the agent's own prior commitments; scope is testable and must be checked.
- **Followup design controls which value's firing can be observed.** Withholding an axis-cue tests spontaneous firing; cueing an axis tests firing-under-prompting. Negative-uncued does not imply negative-under-cued.
- **A finding built on the wrong axis needs falsifiability at each axis independently** (fixture, spec/value ablation, model, cue-vs-no-cue).
- **Reasoning-visibility is a required axis.** On F62-affected models, "value X does not fire" and "value X fires and gets dropped from surfaced output" are indistinguishable without recovery of paragraph reasoning.

### F6. Layer-localization of cross-model behavioral differences

When two models diverge under nominally-matched setup, which layer of the causal stack is load-bearing?

- **Layers to distinguish:** (a) transport/API structural difference; (b) hardcoded client-side parameter default; (c) provider-conditional prompt content; (d) server-side backend policy; (e) task-message scope inheritance; (f) in-flight per-candidate weighing / active-consideration filter; (g) verdict / justification layer; (h) emission-layer suppression.
- **A model-comparison probe is matched only if both models see equal content at every layer above the layer under test.** Wire-level capture is the only reliable check; source-level "same config" is not sufficient (opencode's transform layer injects per-model defaults invisibly).
- **A rule can shift the justification structure for a decision without shifting the verdict.** Justification-only shift is evidence that the rule reaches one layer but not another.
- **Cross-model non-crossing on old-worktree paths lives at the active-consideration filter, not the rejection-axis layer.** Aggregate rejection axes (spec-frame + adequacy + drift) are shared; the differentiator is which paths enter first-pass planning. Spec-level rules operating on justification cannot shift a difference that lives upstream.

### F7. Raw-evidence / interpretive-layer separation

- **A raw-evidence artifact** (chronological, focus-directed, no interpretation) must be separable from the **interpretive layer** (rounds citing evidence as `@L<n>[i]` refs). Findings that entangle the two force every correction to touch both.
- Artifact criterion: stands under interpretation revisions; new interpretations quote artifacts rather than re-reading sessions; each artifact answers "what is in the log relevant to this focus" and stops.
- Skill: [`session-timeline`](../skills/session-timeline/SKILL.md).

### F8. Bias-controlled candidate-enumeration probes

A candidate-enumeration probe measures a joint of (model disposition, probe schema, task frame). Claims about "the model's candidate set" require that the schema itself does not force verdicts or counts.

- **Probe schema decomposes into:** *grain* (per-file vs per-utility), *verdict expressiveness* (enum vs free-text), *bundling policy*, *enumeration frame* (first-pass vs exhaustive-with-escape-hatch), *rejection-slot policy* (per-utility vs aggregate).
- **Ground-truth check:** correlation between probe emissions and unforked baseline behavior at the same turn.
- **Cross-probe convergence** (retrospective self-report + rewind enumeration + bias-controlled rewind enumeration all agreeing) is the only route to overcoming any single probe's bias.
- Reference schema: [`experiments/p5-probe-r43__refined-schema.md`](./compliance-check-failure-mode/experiments/p5-probe-r43__refined-schema.md). Design taxonomy: [`experiments/probe-design-a-b-c__methodology.md`](./compliance-check-failure-mode/experiments/probe-design-a-b-c__methodology.md).

---

## Shape 2: Logical claims

Entries here are project-specific case notes, grounded in the fixtures and rounds where they surfaced. "Logical" means the reasoning is a priori — derivable from the semantics of the fixture and the operation, not from what a specific model did in one run. Each entry names its fixture, states the design fork the fixture forces (or the intrinsic limitation it hits), records what we picked and how we're implementing, and reports status honestly. **Working on this fixture ≠ the only workable choice. Not working yet ≠ the choice is wrong or the alternative works.** These are project logs, not a prompt-engineering guide — do not read them as general advice.

### A. Rule-layer targeting

- **Pre-frame-selection vs post-frame-selection intervention.** *Fixture:* V0 "summarize status" (R1-R7) — the imperative admits multiple scope classifications ("what's in scratchpad" vs "including implications for future work"), and the classification narrows what the agent subsequently inspects. *Analysis:* the classification happens at parse-time; once the frame is set, a rule that acts within-frame is operating on an already-narrowed scope. Restoring the discarded scope is not a within-frame operation. Coherent choices: (a) intervene at parse-time (rule / phrasing / channel that acts before the frame commits), or (b) supply an explicit reopen-trigger firing on downstream state. *Picked:* (a) at R7 (R002 stack biases parse-time selection via an optimization target — "big-picture contribution, not literal completion"). *Status:* Works on the V0 fixture. (b) untested here; the fact that (a) works isn't evidence it's the only workable choice, and its working here isn't evidence a similar (a) will work on other fixtures.

- **Detection-conditioned vs unconditional triggers.** *Fixture:* H17-task ambiguity-workflow rules on identity-outcome-framing (R16-R17). The failure being defended against is "agent doesn't notice the phrase is ambiguous." *Analysis:* any rule "when you notice X, do Y" requires the agent to first recognize X — which is exactly the failing capability. Coherent choices: (a) accept the rule catches only self-recognized ambiguity (cover the rest another way), or (b) restructure to fire unconditionally at a fixed step ("before response construction, walk this workflow"). *Picked:* (b) at R17 (mandatory-scan procedural anchor). *Status:* Rule fires under (b), but the workflow's output doesn't reliably reach the tool-call decision — R18 diagnosed this as a distinct layer problem (see B3). (b)'s implementation not yet reaching the target doesn't imply (a) would have worked; both remain open.

- **Declarative rule vs procedural workflow.** *Fixture:* F75-vulnerable spec design (R14, R16) — where to place duties like "classify inputs before acting." *Analysis:* a declarative rule in an "Instruction Priority" section is consulted only if the agent chooses to reach for the taxonomy at reasoning time; a procedural step in a "Doing tasks" workflow fires as a sequential duty when the workflow is engaged. Semantically these arrive at the agent at different points in response construction. *Picked:* (b) procedural at R16 (mandatory-scan step in commentary workflow). *Status:* Fires more reliably than R14's declarative-labels-v2 variant, but still gated by whether the workflow itself gets engaged. Neither shape is complete alone.

### B. Interpretation handling

- **Mutually exclusive interpretive defaults require a pick.** *Fixture:* Maintainer PROMPT.md caveat "should be considered invalid / idea only" (R12-R13). *Analysis:* as text-in-context, the caveat can be treated as (a) context-to-interpret-for-intent (extract what the author was warning about) or (b) directive-to-honor-literally (treat linked content as untrusted). These readings yield opposite operational behaviors on the same words; a spec cannot leave both live. *Picked:* we've iterated on multiple designs, no committed pick. R12 tried a rule to "follow intent" (targets a); R13 tried maintainer-collapse frame that dissolves caveat authority via ownership. *Status:* Both partial; the interpretation gap persists. Not-picking is not a legitimate stable state — the caveat continues to activate contradictory behaviors depending on task-adjacent context.

- **Force-alternative-generation vs accept-committed-reading.** *Fixture:* H17-task under-determined imperative "Don't act yet" (R16). *Analysis:* the phrase gets committed to one reading with no alternatives generated on its own. Coherent choices: (a) force alternative-generation before commitment (workflow rule requiring enumeration + evaluation) or (b) accept the default single reading and design cheap-rejection channels for downstream correction. *Picked:* R16 iterated (a) — pick-step-preserved variants (word-matching, intent-derivation, "useful", why-written-at-this-time). Each variant picked broad. R7's R002 stack for the V0 fixture is a (b)-shape design (transparency + cheap rejection). *Status:* (a) implementations on H17 have not been made to work. (b)-shape not tried for H17. That (a) hasn't worked isn't proof it can't.

- **In-input vs in-output intervention placement.** *Fixture:* F75-vulnerable spec at the boundary between workflow output and tool-call decision (R18). *Analysis:* interpretation is committed at parse-time; content the agent generates in its response can't shift a reading already fixed before generation. Coherent choices: (a) place interpretation-shifting content in the parsed input (task-adjacent placement, or system-prompt intervention on how the phrase reads); (b) insert an intermediate boundary between workflow output and the tool-call decision so a second reasoning cycle can act on derived interpretation. *Picked:* both tried. R18 (a) via task-adjacent placement (works when task is modifiable); R18 (b) via a workflow step forcing re-parse before commit. *Status:* (a) works when available; (b) has partial working variants. Both remain live design axes.

- **System-prompt-channel vs user-message-channel for identity.** *Fixture:* Maintainer paradigm — "you are the maintainer of PROMPT.md" (R13). *Analysis:* identity claims read differently by channel. In the user channel: role-play (user asks me to play a role for this response). In the system-prompt channel: ownership. These are distinct semantic operations, not weak-vs-strong versions of the same. *Picked:* system-prompt channel. *Status:* Works to dissolve caveat authority on the referenced-material read at R13. The user-channel variant reads as role-play — a coherent alternative for a different downstream question, not a weak version of the identity claim.

- **Editor-frame vs worker-frame in rubric design.** *Fixture:* V5-plan-task-v3 rubric on identity + identity-outcome baselines (R25). *Analysis:* the artifact-vs-instruction interpretation is mutually exclusive at the artifact level. A rubric that scores worker-frame-behavior as aligned will treat editor-frame behavior (revising PROMPT.md as artifact) as partial alignment, misdiagnosing the interpretation. *Picked:* R25 rubric accepts editor-frame as aligned. *Status:* Works — surfaces meaningful separation between correctly-interpreted and misinterpreted cells. Picking worker-frame would have been coherent for a different downstream question ("does the agent execute the prompt?") but not for the interpretation-alignment question.

- **In-channel/definitional vs orthogonal-pressure intervention.** *Fixture:* F75 "Don't act yet" phrase, testing whether audit-cost escalation shifts interpretation (R15). *Analysis:* the phrase reads at parse-time; audit consequences from a spec-side pressure channel arrive at the agent only after commitment, and can be routed around via cheaper-than-reframe escapes (avoidance, meta-answer, confident-bluff-with-hedges). In-channel intervention (same-message unification with joint intent) or definitional override (rename / re-scope the phrase) act at the parse layer where the reading is formed. Coherent choices: (a) in-channel or definitional, or (b) orthogonal pressure with the understanding it's cost-imposition, not interpretation-fixing. *Picked:* R15 committed to (a). Successive audit escalations under (b) just revealed the next cheaper escape. *Status:* (a) framing supported; (b) not-a-fix for this class of problem (though may still be useful for other purposes).

### C. Probe design

- **End-probing vs mid-trajectory probing.** *Fixture:* Candidate-set probes on gpt-5.5 identity-outcome baseline (R37+) — rewind-fork sessions at L6/L12/L16 vs end-of-trajectory. *Analysis:* end-of-trajectory probe ("why did you not read X?") retrieves a rationalization surface — an articulation the agent constructs at query time, not an extract from a stored decision — and its content varies across where in the trajectory it's queried. Mid-trajectory probe (fork before decision, then probe) targets a different object: the state before articulation consolidates. These measure different things (rationalization vs mechanism), not the same thing at different resolution. *Picked:* R37+ mid-trajectory forking for mechanism claims; end-of-session self-reports retained only for rationalization analysis. *Status:* Works. R44 recovered active-consideration information that end-probing had conflated with articulation. End-probing failing at this question doesn't mean it fails at all questions — it's the right tool for rationalization audits.

- **Past-turn extraction vs future-turn generation.** *Fixture:* Rewind-fork probe wording, kimi and gpt-5.5 (R43). *Analysis:* "what did you consider last turn?" refers to a completed reasoning trace already in context; "what are you about to consider?" is itself the counterfactual next-turn generation. Different referents, different rationalization profiles, different sensitivity to elicitation bias. *Picked:* R43 committed to future-turn-generation semantics (present-tense wording, fork-before-turn design). R43 initially had past-tense wording under fork-before-turn — caught mid-round as undefined semantics and reinterpreted the response as generation-order property. *Status:* Works with the picked semantics. Past-turn extraction would be coherent under fork-after-turn design where a real completed trace exists; that path is untested here.

- **Escape-hatch vs no-escape-hatch enumeration probes.** *Fixture:* Candidate-enumeration probes on rewind-fork sessions (R44). *Analysis:* a candidate the model can reconstruct as "reasonable if pressed exhaustively" is not evidence the candidate was in first-pass planning; these are distinct generation-order properties. Without an escape-hatch, a count conflates the two states. *Picked:* R43 refined schema adds `awareness_only` boolean with "err toward false" bias. *Status:* Works to recover the first-pass vs reconstructive distinction on gpt-5.5 (R44). No-escape-hatch inflated R37 P5 counts and led to a mis-attributed "candidate on shortlist" claim that R44 corrected.

- **Enumeration probe vs natural-decision observation.** *Fixture:* R37-R44 evolution of candidate-set probes. *Analysis:* asking a model to enumerate candidates is a different task from letting it decide naturally; the enumeration frame can invent structure the natural decision never had. Coherent choices: (a) use enumeration probes with stability/discriminator controls (drop-list-only variant, cross-rewind reason-stability, baseline correlation on calibration model), or (b) observe natural decisions only, giving up the ability to probe the candidate space. *Picked:* (a). R42 identified 5 bias sources in the schema; R43 controlled for all 5; R44 validated via kimi baseline correlation. *Status:* Bias-controlled probe recovers kimi baseline READ disposition. Without this validation, native-disposition claims from any enumeration probe are uninterpretable.

- **Invitation-to-challenge vs anti-default anchor.** *Fixture:* Precedent-anchoring probes on V5-plan-task where the task supplies an example invocation and says "you may modify this but say why" (R27-precedent). *Analysis:* the phrasing makes staying-with-precedent cost-free and deviating costly. As a probe of whether the agent generates alternatives, this design is default-preserving — a positive result ("agent didn't deviate") doesn't tell you the agent lacked alternatives; the invitation reinforced the default. *Picked:* R28 phase-2 replaced with explicit anti-default anchor ("decide freshly from state; say why your choice fits"). *Status:* Anti-default variant surfaces state-inferred reasoning the invitation had suppressed. Invitation-to-challenge is not-broken for other design purposes (e.g., preserving worker autonomy) — the fork is between "surface alternatives" and "preserve default gracefully," pick per goal.

### D. Attribution

- **Justification-shift vs verdict-shift measurement.** *Fixture:* R38-R39 spec-rule iterations on the R37 candidate-set fixture. *Analysis:* whether the agent skips X and why the agent justifies skipping X are causally separable. A rule can move the justification (false-coverage claim → honest fallback) without touching the verdict-fixing gate. Rule evaluation must pick which of the two is being measured. *Picked:* R38 targeted interpretation/justification layer (abstract rule against assuming text-scope); shifted justification but not verdict. R39 same layer with concrete anchoring; also shifted justification, not verdict. R44 diagnosed verdict-fixing at active-consideration layer, upstream of both rules' targets. *Status:* Justification-shift confirmed; verdict-shift interventions targeting the upstream layer are open work. Both null and shift results informative because we knew which we were measuring.

- **Attribute-at-articulation vs attribute-upstream.** *Fixture:* R37+ target-inheritance analysis on gpt-5.5 candidate-set. *Analysis:* if a target framing is stable across every pre-decision rewind, the visible articulation of that target later in the trajectory cannot be the point where the target was chosen — the target was already fixed upstream of every observation of it. *Picked:* R37+ moved attribution upstream — the "decision" to filter old-worktree paths out of active consideration is at task-message parse (@L1), not at any later articulation point. *Status:* Supported by rewind-fork stability across L6/L12/L16 (R44). Attribution move relocates the target for future interventions to the parse layer, not the articulation layer.

- **Differential-cell design vs bundled comparison.** *Fixture:* R30 model × spec × fixture-fix matrix (kimi vs gpt-5.5, identity-outcome-clean vs no-value-#2, broken vs fixed fixture). *Analysis:* when a claim ("value #2 suppresses coverage-work") rests on comparison across cells varying in multiple axes, the effect can't be attributed to any single axis. Differential-cell design (pair cells differing only on the axis of interest) isolates mechanism. *Picked:* R30 unpacked R29's single-axis claim by running the cube. *Status:* Refuted the single-axis attribution; R32 F97 relocated the finding to value #5 (precval) via differential-cell readback. Value-attribution now requires paired-cell backing.

- **Entangled vs separated evidence/interpretation layers.** *Fixture:* R30-R35 pattern of re-mining sessions while stacking attribution errors. *Analysis:* when the "raw evidence" of an investigation is produced by re-reading source material through the current interpretation, every correction to the interpretation forces a correction to the evidence. Coherent choices: (a) accept that each round rewrites both layers (fine for short investigations, corrosive at length), or (b) separate a factual-artifact substrate (produced without interpretive framing) from the interpretive layer that cites it. *Picked:* (b) at R35 via the [`session-timeline` skill](../skills/session-timeline/SKILL.md) and raw-evidence artifacts under [`experiments/`](./compliance-check-failure-mode/experiments/). *Status:* Later rounds cite artifacts by `@L<n>[i]` refs rather than re-reading sessions; corrections in R44 touched only the interpretive layer.

### E. Structural limitations

- **Enumeration over long context is probabilistic disclosure.** *Fixture:* Candidate-set enumeration probes on gpt-5.5 (R37+). *Analysis:* asking an agent to enumerate items across a long context — candidates weighed, contradictions in a spec, bugs in a long file, motivations for a rejection — is inherently unreliable per-item. This is not a claim about gpt-5.5 specifically or about our specific probe; it's a limitation of the operation: enumeration over long context is high-variance for any specific item. The fact that a specific item happened to surface in one run isn't evidence that similar items will surface reliably. *Implication:* any design relying on such an enumeration for reliability must supplement with another mechanic. *Status:* R44 cross-probe convergence requirement follows from this. R37 P1/P5 initially took single-run enumerations at face value; R44 corrected via convergence across three probe designs.

- **Circular checks against derived quantities.** *Fixture:* R16 "words vs need" spec-clause analysis on H17-task ambiguity workflow. *Analysis:* a "check whether the agent's words align with the user's need" rule presupposes need is characterizable independently of the words being checked. When the agent introspects on need, need reduces to its interpretation of the words. Any check of shape "compare A against B where B is derived from A" has the same structural problem — not a weakness, a null. *Implication:* checks of this shape must reference external anchors (facts, referents, outcomes) rather than agent-derived quantities, or be discarded as null checks. *Status:* R16 discarded the words-vs-need clause; downstream H17 spec-rule iterations avoid this shape.

- **Observation-only cannot distinguish absence-of-consideration from considered-and-rejected.** *Fixture:* R33 kimi crossings analysis on identity-outcome-precval — asking whether value #2 (frame-questioning) was ever considered and rejected. *Analysis:* if a motivation never surfaces at reasoning-visible level, the resulting behavior looks identical to considered-and-rejected. Any inference "spec rule R blocked X because X did not surface" has confused the null with the intended verdict. *Implication:* disambiguation requires either recovery of internal reasoning (visible-reasoning model, structured probe) or a design that forces different externalization for the two states. *Status:* R33 downgraded "value blocked X" attributions to "value's firing was unobserved." R44 `awareness_only` schema is one design that forces different externalization.

- **Hidden-reasoning bounds mechanism inference.** *Fixture:* F62 confound on Codex-backend gpt-5.5 (`chatgpt.com/backend-api/codex/responses`) — reasoning exposed only as short bold headings. *Analysis:* "value X did not fire" and "value X fired and was dropped at surface" produce identical observable behavior when only headings are exposed. Not a claim about gpt-5.5 in general — a claim about what is inferable from this specific surface. *Implication:* mechanism claims on this model class require a reasoning-recovery channel (raw API + `include_reasoning`, or structured schema slots that force reasoning into the response). *Status:* R32+ flags all Codex-backend gpt-5.5 mechanism claims as speculative. R44 candidate-set JSON schema bypasses heading collapse and produces admissible mechanism evidence.

- **Floor-bounded outcomes cannot distinguish intervention-inertness.** *Fixture:* R20 F79 v1 above-floor test on F75-vulnerable spec. *Analysis:* when the measured baseline sits at floor (e.g., 0 tool_use), a control also at floor tells you nothing about whether the intervention is inert or whether some other force (F75-block) is dominating. Contamination cannot suppress below floor either. *Implication:* intervention-inertness claims require an above-floor baseline. *Status:* Applied to R20+; below-floor cells now flagged as uninformative rather than as "intervention had null effect."

---

## Shape 3: Design ideas

### Spec structure

- **Positive optimization target over "avoid X" prohibitions.** No separate anti-X rule; the target penalizes X intrinsically as failure-mode-of-the-goal.
- **Reframe rules so the assigning-agent grammatically disappears** — dissolves conflicts with prohibitions on assigning work by removing the fire condition, not adjudicating priority.
- **Route uncertainty into a named taxonomy** (goal / scope / objective) so each kind has defined handling; force a single big-picture inference so the agent has a direction.
- **Structured gate-input schema** (Task / Big picture / Uncertainty / Scope / Output Draft) — big-picture inference becomes machine-checkable and disclosed.
- **Standing license for side-effect-free operations evaluated by big-picture value**, to remove the implicit "stay literal" prior.
- **Attach epistemically-grounded rationale to the "context" bullet** ("written earlier, possibly wrong; informs but does not decide"). Operational reading depends on rationale, not label.
- **Values as positive-orient default-posture verbs**, not conditional "when X you do not Y" — behavior stops depending on the agent self-classifying a moment as triggering.
- **Concrete-list enumeration in value directives.** Concrete enumeration ("a command flag, a code call, a next-step choice") gives the agent a mapping surface at the site of application; abstract-only phrasing loses effect even under structural parallelism.
- **Encode calculations, not rules, in values.** "Weigh consistency-value against divergence-cost; for state-dependent forms, form-inheritance does not preserve effect" — predicts differential behavior split by form's state-dependence.
- **Narrow-default with widen-requires-justification** avoids the pick-time safety-asymmetry bias (directive-violation = hard-failure vs weak-answer = soft-failure) that pushes every criterion-based pick toward broad.

### Ambiguous-imperative interventions

- **Specification-lock over cost imposition.** To shift interpretation of a phrase, add a rule in the same channel unifying into joint intent with it, or definitionally rename the phrase. Orthogonal system-side quality/audit pressure does not shift interpretation — the agent finds cheaper-than-reframe escapes.
- **Affirmative permission beats correction-of-misinterpretation.** "You have permission to explore" gives something to reason from; "don't misread X as prohibition" leaves the misreading available. Pair with ID-requirement ("a prohibition must be a rule with an id").
- **Procedural workflow > declarative rules for reasoning-shaped duties.** "Instruction priority" style reads as taxonomy metadata; "Doing tasks" style reads as sequential duty. Position duties that must fire before response construction as sequential steps.
- **Mandatory-scan procedural anchor** ("in commentary, do these steps in order; show the work; don't skip to the answer"). Passive "when you notice" triggers move workflow into hidden reasoning.
- **Skipped-candidate disclosure commentary rule** — name candidates you weighed and rejected, and why. Surfaces candidate-generation at message-content level with narrower measurement-alters-phenomenon risk than open-ended "list rules applied" because target category is specific.
- **Task-adjacent placement.** Interpretation-shifting content in the user message adjacent to the ambiguous phrase — parse-time input governs parse-time interpretation.
- **Maintainer identity in the system-prompt channel** dissolves referenced-material caveat authority via ownership. Identity claims in the user-message channel read as role-play — API channel semantics dominate.

### Task design for leg-2 investigation

- **Hybrid pause-permission task** (edit-allowed + task-gated pause with disk-committed edits + exact invocation named) — forces precision by requiring the artifact to be constructable and disk-persistable before execution.
- **Author-recall / author-intent-inversion clauses** to force author-frame: "walk through what you were thinking when you wrote X" or "worker interpreted X; is that what you intended?"
- **Task-side gate + process watcher** (SIGTERM on long-lived unwanted invocations) — generalizable "trusted but verified" pattern for execute-permission rounds.
- **Mark precedent explicitly at task-writing side as decide-freshly.** Replace "you may modify but say why" with "decide freshly from state and say why your choice fits."
- **Precedent-evaluation value** ("evaluate before you inherit; provenance is not evidence for fit") — produces state-inferred (not merely state-cited) reasoning without marker-based confounds.

### Probe design (mechanism attribution)

- **Followup withholding axis-cue** ("suppose the next loops find all tests pass; what would you do next?") discriminates values whose spec-text target has no cue in the prompt.
- **Precedent-swap probe** (single-character-block fixture diff, e.g. add/remove `--continue`) — if agent's final invocation tracks the swap, precedent-anchoring is inheritance not deviation-blindness.
- **Cross-model × value-ablation × fixture-fix matrix** for spec-attribution — isolates confounds a single-axis test cannot.
- **Rewind-fork probes at multiple pre-decision boundaries.** End-of-session self-reports recover most-visible-articulated-scope, not origin. Fork at L1/L6/L12/L14 to discriminate target-fixing inherited from task-message @L1 from target-fixing that emerged mid-arc.
- **Concrete-anchored rule variant after abstract variant fails.** Abstract-failure can mean "wrong layer" or "too general"; rewriting the same rule against the specific in-context artifact discriminates.
- **Bias-controlled candidate-enumeration schema** (full ref: [`experiments/p5-probe-r43__refined-schema.md`](./compliance-check-failure-mode/experiments/p5-probe-r43__refined-schema.md)). Key features: per-utility grain with `current_status_of_this_answer`; content-first slots (`probable_contents` + `what_each_would_tell_you`); free-text disposition (not enum); ordered `next_turn_tool_calls_if_any` (not batch-selection); anti-bundling (one file per candidate); no aggregate rejection slots; `awareness_only` boolean with "err toward false" bias. Each feature counters a specific bias listed in Shape 4 § probe-schema.

---

## Shape 4: Methodological lessons

### Attribution discipline

- **Blocking tests, not self-reports, for causation.** Post-hoc introspective narratives reflect the agent's model of what happened, not the causal mechanism. Remove one factor, hold others fixed.
- **End-of-session retrospective probes recover rationalization, not mechanism.** "Why didn't you X" retrieves the most-visible-articulated-scope. Reach earlier via rewind-fork when the question is about origin.
- **Cross-probe convergence beats any single probe's ground-truth claim.** Retract confabulation attributions when a bias-controlled probe converges with the retrospective self-report.
- **A diagnostic can change the phenomenon it measures** via interaction of its scope-wording and its purpose-framing. Ablate both dimensions independently.
- **Ex-ante utility tagging discipline.** Tag candidates by information available at the rewind point (path, filename, prior-mentions), not by content revealed later. Retrospective tagging inflates apparent utility.
- **Cross-model probe validation via baseline correlation.** New probe must recover known unprobed baseline for at least one calibration model, or it is measuring itself.
- **Tense must match fork design.** Past-tense wording is only defined for fork-after-turn where a real past trace exists.
- **Value-attribution requires matching against the specific value's spec-text criteria, per item.** "Novel and dispatched" is diagnostic of *some* value firing, not of a specific one; don't attribute without ablating other candidate drivers.
- **Spot-checking a quote does not verify mechanism attribution.** Re-derive the lead-up chain from raw session content, not from quote-verification of the endpoint.
- **Distinguish interpretation-layer from execution-layer failures before designing a fix.** "Misinterpretation" attribution when the actual layer is candidate-persistence mis-targets the fix.
- **Do not ground system understanding on fixtures where inference dominates every observation.** Use fully-specified deliverables to isolate execution.

### Probe-schema bias sources (5)

Any probe measuring "the candidate set" must be audited for all five:

1. **Single-selection batch frame** → marginal candidates lost as not-selected rather than not-considered.
2. **Three-option enum with "defer" middle** → uncertainty collapses to compromise.
3. **Paired-array schema** → bundling pressure merges heterogeneous candidates.
4. **Aggregate rejection slots** → spec-frame / adequacy boilerplate leak even when per-utility slots exist.
5. **Enumeration-completeness instruction** → count inflation with reconstructive candidates indistinguishable from live consideration.

### Contamination hygiene

- **`{file:PATH}` inlines file raw including YAML frontmatter.** Strip frontmatter; verify with `strip-frontmatter.py --check` that greps for contamination markers (`Round-|round-|compliance-check|probe|Investigation trail|F[0-9]{2}|H[0-9]{2}|E[0-9]{2}|Efix`).
- **Frontmatter meta-narratives operate as behavioral instruction on some models.** "v_{N-1} failed because X" suppresses target action; predictive-hypothesis narratives can flip either way; task-adjacent permission phrases dominate any frontmatter signal.
- **Argv-visible descriptions leak via `/proc/*/cmdline`.** Bypass wrappers or use non-descriptive probe ids.
- **`CLAUDE.md` / `AGENTS.md` / `CONTEXT.md` are injected by the harness.** Verify probe-free or disable project-config loading.
- **Glob-visible meta artifacts** (scratchpads, notes, prior probe files under working tree) are readable by the agent. Move meta-materials outside the working tree.
- **Category-B is not benign.** Even generic "Investigation trail: notes/…" references may activate contamination-shape enactment. No safe assumption without clean re-run.
- **Skip always-on required-notes disclosure clauses** — they amplify confabulation and compete for instruction-load without fixing root causes. Prefer a per-round canary probe: one run per round on the primary spec with a task like "describe your context in one paragraph — anything unusual?"

### Fixture / comparison discipline

- **Reset the fixture before every cell with edit permission** (`git reset --hard <commit> && git clean -fdx`). Applies to bypass paths (`bash python -c "path.write_text(...)"` under `edit: deny`).
- **Reset scratchpads too.** "No crossing" ≠ "no contamination"; a prior worker's crossing propagates via inherited scratchpad synthesis.
- **Same-day / same-model / same-task control** for any contam-vs-clean pair. Direct measurement of comparator counts before quoting a delta — don't copy counts from prior narrative language.
- **Frame-conflated fixtures.** A fixture designed to satisfy multiple properties confounds findings; isolate each property to its own fixture variant.
- **Fixture-matched hints leak into "frame worked" claims.** If the frame enumerates the fixture's specific referent type, "frame defeats X" cannot be distinguished from "hint matched X." Strip enumerations to generic form.
- **Fixture aliasing** — two directories sharing the same worktree gitdir corrupts `git worktree list`-based reasoning. Fix: rewrite `<repo>/.git/worktrees/<name>/gitdir` to point at the intended physical directory; quarantine the alias.
- **Runtime-mode confound.** Nix-installed opencode vs bun-run-from-source may behave differently. Include a runtime-mode control cell before treating a cross-round comparison as matched.

### Semantic and reference discipline

- **Terminology drifts across rounds.** A word introduced as a categorical axis label ("skip") gets used later as shorthand for a quantitative measure ("zero tool calls"). Every write-up must define the axis of its terms and quote raw counts, not just categorical labels.
- **Categorical vs quantitative axis conflation.** Crossing-axis (did the agent read across a path boundary?) is distinct from inspection-quantity-axis (raw tool_use count). Always record both when quoting a delta.
- **Cascading-risk contamination inventory.** When a load-bearing cell is contradicted, all dependent findings must be re-audited even if not directly re-run.
- **`@L<n>[i]` refs, not raw line numbers** — pretty-print line numbers drift 200-2500 lines across export passes.
- **F62 confound applies to every gpt-5.5 mechanism inference.** Flag as speculative unless reasoning appears in emitted prose or in the produced artifact. Prefer JSON candidate-set slots that bypass heading collapse for cross-model comparison.

### Statistical / framework discipline

- **n=1 gives direction, not magnitude.** Large deltas (0 → 30+) survive n=1; magnitude stability and cross-cell attribution require replication. Characterize base-rate distribution across ≥3 replications before attributing a single-cell outcome to a mechanism.
- **Do not mix diligence into an interpretation rubric.** Loop-mechanics vocabulary precision is a diligence axis, not an interpretation axis; scoring it against an interpretation rubric produces spurious retractions.
- **Coherence prerequisite for intervention measurement.** A rule contradicting the existing instruction-priority hierarchy may be silently filtered; "intervention had null effect" may be measuring self-contradiction filtering.
- **Trajectory-comparison subagents for (contam, clean) pairs.** Structured comparison prompt (opening commentary, reasoning-heading arc, workflow visibility, first-3-tool-call analysis, decision-fact citation quality). Prevents main-context bloat while preserving qualitative signal.
- **Audit prompts iterate.** Substring-grep audit under-calls content flow; add timeline + paraphrase-explicit + ground-truth-inline + read-every-reasoning-block rules to catch paraphrase leaks and meta-frame activations grep alone misses.

### Raw-evidence / interpretive-layer separation (why the [`session-timeline`](../skills/session-timeline/SKILL.md) skill exists)

Every round re-reads sessions; each pass introduces attribution errors a later round must correct. Separating layers means future corrections touch only interpretation while the raw-evidence artifact stands. Raw-evidence artifacts live under [`experiments/`](./compliance-check-failure-mode/experiments/).

---

## Round index

**Purpose of this section:** a doc index for future readers who want to find the per-round file that contains the empirical detail behind a claim. Not research. Each entry is the *question* the round pursued — findings live in the per-round file, and any transferable content has already been extracted above into shapes 1-5.

| Round | File | Question |
|-------|------|----------|
| 1-2 | [`01-02`](./compliance-check-failure-mode/round-01-02.md) | Does rewording a mis-anchored predicate close the failure surface it missed? |
| 3-4 | [`03-04`](./compliance-check-failure-mode/round-03-04.md) | Can a body-added "go beyond literal" clause restore access to a scope the agent has already narrowed? |
| 5 | [`05`](./compliance-check-failure-mode/round-05.md) | When two rules grammatically conflict, which wins, and can wording be repaired without rewriting both? |
| 6 | [`06`](./compliance-check-failure-mode/round-06.md) | Does removing a rule's fire-condition dissolve the conflict without further edits? |
| 7 | [`07`](./compliance-check-failure-mode/round-07.md) | Does per-axis restriction terminate under any finite spec, or must the optimization target change? |
| 8 | [`08`](./compliance-check-failure-mode/round-08.md) | On a fixture that pins the execute stage, what execution-layer failures does a well-behaved baseline still show? |
| 9 | [`09`](./compliance-check-failure-mode/round-09.md) | Can a "rules or instructions applied" diagnostic serve as neutral telemetry, and does the agent supply a stable definition of "instruction"? |
| 10 | [`10`](./compliance-check-failure-mode/round-10.md) | Does treating the user as a person and everything else as context (values + instruction-priority paradigm) change which failure modes fire? |
| 11 | [`11`](./compliance-check-failure-mode/round-11.md) | Within the identity paradigm, which layer governs caveat-treatment, and what value-shape avoids recognize-then-enforce failure? |
| 12 | [`12`](./compliance-check-failure-mode/round-12.md) | When R020 forces a context-vs-instruction default pick, do rationale-clause and frame-reclass act as separate mechanisms? |
| 13 | [`13`](./compliance-check-failure-mode/round-13.md) | If we collapse the user (maintainer paradigm), does caveat authority dissolve — and if not, what factors gate path-crossing? |
| 14 | [`14`](./compliance-check-failure-mode/round-14.md) | Does a label-based classification substrate (R###/G###) defeat F75 on its own? |
| 15 | [`15`](./compliance-check-failure-mode/round-15.md) | Is "'Don't act yet' → no tools" a stable literal-prohibition reading or an elastic lazy-defensible one, and does orthogonal pressure shift it? |
| 16 | [`16`](./compliance-check-failure-mode/round-16.md) | What is the pipeline position of the interpretation failure, and is the "words vs need" spec clause structurally defective? |
| 17 | [`17`](./compliance-check-failure-mode/round-17.md) | Can a spec-level rule get the model to run motivation-derivation spontaneously, and why does inspection still not follow? |
| 18 | [`18`](./compliance-check-failure-mode/round-18.md) | Is F75-behavior a phrase-level prior outside interpretation, or a parse-time interpretation-default varying by model? |
| 19 | [`19`](./compliance-check-failure-mode/round-19.md) | What actually leaked into the system prompt, and how do we distinguish real leak channels from confabulation? |
| 20-21 | [`20`](./compliance-check-failure-mode/round-20.md) [`21`](./compliance-check-failure-mode/round-21.md) | Do the load-bearing R17/R18 findings survive frontmatter-strip, and does contamination direction depend on narrative form? |
| 22 | [`22`](./compliance-check-failure-mode/round-22.md) | Do R12/R13 HIGH-priority Category-A-adjacent cells survive clean re-runs, and does the F74 core claim survive? |
| 23 | [`23`](./compliance-check-failure-mode/round-23.md) | Do R13 Runs C/E/F survive clean re-runs on inspection-quantity and crossing axes, and does F72's worker/author asymmetry survive? |
| 24 | [`24`](./compliance-check-failure-mode/round-24.md) | What do actual contam counts show when measured directly rather than copied, and does R23 have a model-version confound? |
| 25 | [`25`](./compliance-check-failure-mode/round-25.md) | Given a task with no interpretive ambiguity, do the identity-lineage baselines execute it in aligned role-frame — and what task-shape iterations get them there? |
| 26 | [`26`](./compliance-check-failure-mode/round-26.md) | *(Superseded; treated diligence as interpretation.)* |
| 27 | [`27`](./compliance-check-failure-mode/round-27.md) + [`27-precedent`](./compliance-check-failure-mode/round-27-precedent-anchoring.md) | Does a hybrid pause-permission task produce sharper disk-committed dispatch artifacts than a plan-review task? Why do both cells adopt task-supplied precedent without generating alternatives? |
| 28 | [`28`](./compliance-check-failure-mode/round-28.md) | Is the precedent-keeping rationale fixture-blind or state-sensitive under a textual-refutation marker — and can a value-side intervention produce state-inferred reasoning without the marker's confounds? |
| 29 | [`29`](./compliance-check-failure-mode/round-29.md) | On the identity-outcome-precedent-value spec, does the agent's best-approach value fire *unprompted* on a "suppose all tests pass" followup? |
| 30 | [`30`](./compliance-check-failure-mode/round-30.md) | Is R29's negative result model-general, value-#2-specific, or fixture-conditional, under a cross-model × value-ablation × fixture-fix matrix? |
| 31 | [`31`](./compliance-check-failure-mode/round-31.md) | *(Superseded by R32.)* Across the 10-cell R29/R30 corpus, which cells crossed and what content flowed downstream? |
| 32 | [`32`](./compliance-check-failure-mode/round-32.md) | Which of R31's mechanism attributions survive re-derivation from raw session content under `@L<n>[i]` refs and F62-caveat discipline? |
| 33 | [`33`](./compliance-check-failure-mode/round-33.md) | What motivated each cell's crossing, what did the cell's own reasoning claim, and what did the crossing produce downstream — and does the fixture caveat gate any of it? |
| 34 | [`34`](./compliance-check-failure-mode/round-34.md) | What actually differs between the two providers' wire-level requests under nominally-matched setup? |
| 35 | [`35`](./compliance-check-failure-mode/round-35.md) + [`experiments/`](./compliance-check-failure-mode/experiments/) | What layer separation prevents each interpretive round from re-introducing attribution errors that the next round has to correct? |
| 36 | [`36`](./compliance-check-failure-mode/round-36.md) | Does the session-timeline skill produce artifacts stable under a fresh extractor, and what corpus is needed for a future interpretive round to cite without re-mining? |
| 37 | [`37`](./compliance-check-failure-mode/round-37.md) | Are old-worktree paths ever on the model's candidate list, and if so, is target-fixing an in-flight decision or inherited from task-message @L1? |
| 38 | [`38`](./compliance-check-failure-mode/round-38.md) | Does an abstract spec-level rule against assuming text-scope shift the drop-reasoning for the target artifact? |
| 39 | [`39`](./compliance-check-failure-mode/round-39.md) | Does a concrete-anchored intent-drift rule (naming the same-author-same-commit faithfulness criterion) shift what the abstract rule couldn't? |
| 40 | [`40`](./compliance-check-failure-mode/round-40.md) | Does a content-first per-candidate schema surface content-utility axes that aggregate rejection slots collapse? |
| 41 | [`41`](./compliance-check-failure-mode/round-41.md) | Does per-utility grain (with `current_status_of_this_answer`) expose distinct rejection shapes that file-level grain hides, and does it change verdicts? |
| 42 | [`42`](./compliance-check-failure-mode/round-42.md) | When the R41 probe is applied to a model whose baseline reads the target, does the probe recover baseline behavior or induce a probe-artifact verdict? |
| 43 | [`43`](./compliance-check-failure-mode/round-43.md) | With five identified bias sources removed, does the probe recover kimi's baseline READ disposition? |
| 44 | [`44`](./compliance-check-failure-mode/round-44.md) | With the bias-controlled probe on gpt-5.5, do candidate counts and old-worktree active-consideration status hold, and where does the cross-model difference actually live? |

---

## Open ideas (prospective — shape-3 candidates)

- **Drop-list-only rewind-fork probe** (P5b): reword P5 to ask only for `verdict: "read"` candidates. Discriminates genuine in-flight weighing from probe-triggered enumeration, without giving the agent a slot to enumerate reconstructive candidates into.
- **Task-message ablation probe** for the target-inheritance hypothesis: rewrite the task's paragraph-1 to explicitly include pointer targets in "current state." If crossing emerges under otherwise-clean spec, task-message inheritance is the load-bearing gate.
- **Caveat-scope ablation:** strip a specific PROMPT.md caveat clause and rerun. Discriminates caveat-authority as drop-driver vs adequacy-check as drop-driver.
- **L1-rewind probe:** fork before all assistant responses, then inject the probe. Captures the earliest possible candidate-generation state, before pointer entered assistant context.
- **Cross-model spot checks** on F75 baseline / F78 Efix-v7 to test model-specificity of shape-3 designs that were derived on a single model.
- **`{file:PATH}` upstream fix** — add defensive markdown frontmatter strip in opencode's `substitute()`. Not addressed.
- **`edit: deny` process-level enforcement** — extend to block the `bash python -c "path.write_text(...)"` bypass.

---

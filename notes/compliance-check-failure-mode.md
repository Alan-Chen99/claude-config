# User-direction compliance-check failure in opencode agent prompts

## What this doc is

Investigator-facing case notes on why opencode agents fail to comply with user direction on specific task classes. Not a prompt-engineering guide — findings are project-specific and grounded in the fixtures/rounds where they surfaced.

Round-by-round empirical work (task files, model responses, tool-call counts) lives in per-round files under [`compliance-check-failure-mode/`](./compliance-check-failure-mode/). This main file keeps only content that survives implementation drift, organized as five shapes:

1. **Research framework** — how the problem is split, what invariant is chased. *Primary shape.*
2. **Logical claim** — a constraint holding regardless of implementation.
3. **Design idea + logical why** — an approach worth trying, with a priori justification.
4. **Methodological lesson** — a probe / measurement / attribution mistake to avoid.
5. **System fact** — code-verifiable harness mechanism, cite `path:line`.

**Excluded:** per-cell tool-call counts, rubric scores, replication numbers, retraction bookkeeping (delete on supersession — do not "retract with note"). Test for every candidate entry: name the framework question and the property a solution must satisfy — if the answer collapses to a specific file / model / count, extract the property or discard.

**Citation rule.** Every claim, bullet, or design idea must cite the round(s) where it surfaced or was demonstrated (e.g. `[R7]`, `[R37-R44]`, `[R42/R43]`). No round → the claim is either untraced (fix by tracing to a round file) or general enough that it belongs in a different doc.

## Growth policy

- **Whole-file budget: ≤18k tokens** (`agent-tools count-tokens --file <path>`). Baseline: pre-refactor was ~10k; shape decomposition adds intrinsic overhead. Current file sits ~18k. Adding content that would exceed 18k requires pruning older content of equal or greater size in the same edit.
- **Growth condition (retention rule).** Main doc grows only when a new shape-1-5 item is discovered. Empirical replication of an existing item does not touch this file.
- **Prune candidates,** in order:
  1. Superseded items — delete outright (do not retain "retracted with note").
  2. Shape-3 design ideas not promoted to a committed spec after 3+ rounds of use — move to [`open-ideas.md`](./compliance-check-failure-mode/open-ideas.md).
  3. Shape-2 entries whose fixture is no longer active — cite from a round file and drop.
  4. Round-index rows for rounds fully subsumed by a later round — drop, letting the later round's row point to both.

---

## Experiment-from-ground rule

A round may build on a prior claim only after re-examining that claim in the current round. Applies uniformly to interpretive claims, methodology, sanity checks, bias-tests, and calibrations.

**Load-bearing vs context-only.**
- **Load-bearing** — cited in the current round's committed decision, falsifiable prediction, or design justification. Full re-examination required.
- **Context-only** — may be cited unaudited; mark as *"unreexamined citation — see R##"* so the trust boundary is visible in the round file.

**What re-examination requires.**
- **Logical claims** — re-derived in the round's argument (structural comparison, framework partition, procedural rule).
- **Experimental claims** — re-run on the current prompt/fixture unless cache conditions hold.
- **Methodology / sanity-checks / bias-tests / calibrations** — audited against the current deployment surface and against current-most methodology ideas. A calibration cell covering kimi L6 does not cover gpt-5.5 L12 without re-audit. A bias-test written before a new bias source was identified must be re-audited against the newer taxonomy.

**Transitive.**
Re-examining a claim covers (a) whether the stated evidence still supports it under current context, and (b) whether the immediate evidentiary basis remains valid. One evidentiary hop is mandatory; go deeper when the one-hop audit surfaces a break. Applies transitively to sanity-checks: a "probe is unbiased" claim is re-audited whenever the probe's deployment surface grows, and the calibration cells that claim rests on are re-audited in the same pass.

**Cache (session-level only).**
- Session artifacts (transcripts, tool outputs, JSON emissions) may be reused only if model, prompt, fixture, probe wording, and fork point are exactly equal to the cached run.
- Cache invalidates when any of: (a) a downstream round has identified a bias or defect in the same probe/method; (b) the claim's deployment surface has grown outside the original calibration surface; (c) a framework entry cited in the claim has been rewritten.
- **Interpretive analysis is never cached.** Every round that leans on an interpretive claim re-derives it in the current round's context.

**Session-ID discipline.**
Every session, fork, or probe run cited in a round file is labeled explicitly as **cached** (originating round + session ID) or **new** (with the new session ID). Unlabeled session references are a lint error.

**Disagreement on re-derivation.**
When re-derivation produces a different result than the prior derivation, current-round wins. Prior claim annotated *"superseded at R##"* with a one-line delta note in the prior round file. Both readings do not stay live.

---

## Fixtures & working specs

- **V0 fixture** — original "summarize status" fixture from rounds 1-7; imperative admits multiple scope classifications.
- **V5 fixture** — `/root/claude-config-work2/`; standard 4-part diagnostic task at `/tmp/V5-task.md`.
- **Maintainer fixture** — `/root/claude-config-work-maintainer/`; git-surgery rewrite of `work2/` with PROMPT.md in maintainer-authored voice. Task at `/root/experiment-materials/V5-minimal-task.md`.
- **F75 fixture / H17-task** — identity-outcome-framing agent + `/root/experiment-materials/H17-task.md` (5-line task ending *"Don't act yet."* on an ambiguous decision).
- **`opencode/agents/min.md`** — diagnostic-minimum baseline (R002 stack + G1-G6 gate via `agent-tools min.gate`) [R7].
- **`opencode/agents/identity.md`**, **`identity-outcome.md`** — parallel values-framework specs [R10-R11].
- **`opencode/agents/alan-default-ids.md`** — operational spec running day-to-day. No post-R7 finding has produced a committed change here.

**F/H code convention.** F## / H## / E## / Efix-vN are per-round artifact IDs (mechanism claims, task/spec variants). Only F62 (Shape 5) and F75 (above) are load-bearing enough to be defined in this main doc; other codes appearing in prose (F72, F74, F78, F79, F97, Efix-v7, …) refer to per-round-file artifacts — resolve via the round index below.

---

## Shape 5: System facts (opencode mechanism)

**Prompt-assembly** [R19, R30]:

- Provider-conditional prompt is skipped entirely when `agent.prompt` is set. `packages/opencode/src/session/llm.ts:116` — `input.agent.prompt ? [input.agent.prompt] : SystemPrompt.provider(input.model)`. Provider prompt dispatch at `packages/opencode/src/session/system.ts:19-33` (per model family: `PROMPT_BEAST`, `PROMPT_CODEX`, `PROMPT_GPT`, `PROMPT_GEMINI`, `PROMPT_ANTHROPIC`, `PROMPT_KIMI`, `PROMPT_DEFAULT`). Setting `agent.prompt` replaces, not merges — hidden trap for any setup that assumes provider prompt still applies.
- `CLAUDE.md` / `AGENTS.md` / `CONTEXT.md` injection at `packages/opencode/src/session/instruction.ts:14-18,154-168` reads `~/.claude/CLAUDE.md` (unless `disableClaudeCodePrompt`), the first `AGENTS.md`/`CLAUDE.md`/`CONTEXT.md` walking up from cwd, and `~/.config/opencode/AGENTS.md`; concatenated at `session/prompt.ts:1426`.

**Config-loading channels** [R19]:

- `{file:PATH}` inlines the file raw. `packages/opencode/src/config/variable.ts:44-88` `substitute()` uses `Filesystem.readText` + `JSON.stringify(fileContent).slice(1,-1)`. No frontmatter awareness. Flows to `agents[name].prompt`. **A spec loaded via `{file:...}` retains its YAML frontmatter verbatim in the system prompt.**
- Disk-load path strips frontmatter via gray-matter at `config/agent.ts:105-130` (`md.content.trim()`). Committed `.opencode/agents/*.md` are clean via this path.
- Inline `cfg.agent[key].prompt` merged with disk-loaded agents at `config/config.ts:614-620`; inline-expanded string wins.

**Backend / provider policy** [R18, R34, R46]:

- **F62.** Codex OAuth endpoint (`chatgpt.com/backend-api/codex/responses`) applies server-side policy reducing `reasoning_summary_text` to bold headings only (mean ~39 chars). API-key endpoint (`api.openai.com/v1/responses`) returns paragraphs (mean ~363 chars). Mitigations: (a) `OPENCODE_AUTH_CONTENT='{"openai":{"type":"api","key":"$OPENAI_API_KEY"}}'`; (b) [R46] route via OpenRouter — `openrouter/openai/gpt-5.5` with `OPENROUTER_API_KEY` + `provider.openrouter.options.apiKey` inline in `OPENCODE_CONFIG_CONTENT` + model `options.reasoning:{effort:high,exclude:false}`. Both routes return `openai-responses-v1` paragraph summaries. Instrumentation at `provider.ts:1567` + `plugin/codex.ts`; `OPENCODE_F62_LOG_DIR=<dir>` enables capture.
- `textVerbosity` hardcoded `"low"` for all gpt-5.x models except gpt-5-codex, gpt-5-chat, Azure. `packages/opencode/src/provider/transform.ts:1129-1148`. No user override. `reasoningEffort` is orthogonal.

**Wrapper / harness** [R19]:

- `agent-tools run --desc "…"` was leaking description via `/proc/<pid>/cmdline` (readable by test agent via `ps aux`). Fixed with `--hide-cmdline`; historical sessions may still show the leak.
- `edit: deny` does not block `bash python -c "Path(...).write_text(...)"`. Process-level restrictions needed for write-bypass prevention.

**Session tooling** (general opencode ops; kept here for locality):

- `agent-tools opencode-pretty <session-id>` prints `@L<n>[i]` refs per part; recover raw via `opencode export <sid> | jq '.messages[<n-1>].parts[<i>]'`. Pretty-print line numbers drift across export passes — cite `@L<n>[i]` refs, not raw line numbers.
- `opencode run --format json` stdout stream elides reasoning parts even when the tokens block reports non-zero reasoning tokens. Retrieve from DB via `opencode export <sid>`.
- `opencode export` writes JSON on stdout, `"Exporting session:"` prefix on stderr. Plain `> file` is clean; do not `tail -n +2` on the merged stream.
- `opencode run --session $ID --fork` CLI flag does *full-session* fork. To fork at a specific messageID (drop from ID forward), HTTP `POST http://127.0.0.1:4096/session/:sid/fork` with `{messageID}` against `opencode serve --port <n> --hostname 127.0.0.1`.
- `opencode run --agent <path>` silently falls back to the session's stored default agent unless `<path>` matches a registered agent name at `~/.config/opencode/agents/<name>.md`. Logs *"agent not found. Falling back to default agent"*.

---

## Shape 1: Research frameworks

### F1. Rule-collision archetypes → optimization-target reframe [R1-R7]

Iterate rule-based specs against ambiguous "summarize status" through: locate text-level defect → reword/add rules → observe failure re-emerge on different axis → change what the agent optimizes for. Compressed findings (see round files for evidence): rules anchor to the noun they're written around and miss off-anchor surfaces [R1-R2]; body-only rules don't reliably survive gating so post-gate duties must live at the gate layer [R3-R4]; frame-selection precedes rule-firing, so a body rule can't restore already-discarded scope [R3-R7]; grammatically-conflicting rule pairs compose into "minimum-risk suppress-one" spec-compliant outcomes [R5]; no finite anti-axis list terminates under literal compliance — fix is to change the optimization target and expose agent-inferred effort for cheap rejection [R7].

### F2. Execution-layer failure decomposition on fully-specified fixtures [R8-R11]

On execute-pinning fixtures, what failure modes persist past rule/target interventions?

- **Failures decompose into ≥4 layers** [R8]: (a) candidate never generated; (b) generated but lost to competition; (c) generated + locally inferred but not followed through; (d) draft material compressed out of final synthesis. Specs must name their target layer.
- **A well-generated candidate does not automatically survive competition** [R8]. Reliability needs explicit persistence.
- **No stable model-supplied "instruction" vs "context" definition** [R9]. The boundary must be written into the spec.
- **Context-treatment is controlled by operational rationale, not label** [R10-R11]. Label-without-rationale leaves interpretation to on-the-fly composition.
- **Values and instruction-priority are separate layers** [R11]. Fighting caveat-honoring by rewriting values is category-confusing.
- **Scratchpad/summary reads ≡ subagent returns** [R11]. Opaque distilled outputs from an unre-verified delegated context; trust-calibration bugs on one shape imply the other.

### F3. Ambiguous-imperative interpretation: R020 fork + F75 two-layer decomposition [R12-R18]

For a user-message imperative admitting multiple defensible interpretations ("Don't act yet" on a decision task): what gets the agent to (a) generate the correct interpretation, (b) evaluate non-circularly, (c) act on it?

- **R020 fork is forced** [R12]. Any text is either default-context (interpret for intent) or default-instruction (honor as directive). Both readings cannot coexist; spec must pick per rule / class.
- **Two-layer decomposition** [R18]: F75-interpret (reading committed) vs F75-behavior (does derived permission drive action). Fix independently.
- **Three-factor structure for path-crossing under referenced material** [R13, R25]: (i) surface pressure surfacing the referent, (ii) frame dissolving caveat authority, (iii) authorship/strategic scope covering the path. All three required under some conditions.
- **Interpretation-shifting content must live in the parsed message** [R18]. Response-generated content is post-hoc for the committed reading.

### F4. Pipeline leg decomposition — leg-2-ready task inputs [R25-R28]

`<original task> → <fully-specified task> → <answer>`. Leg 1 = interpretation; leg 2 = execution. Isolate leg 2 by iterating the task until interpretations converge under aligned frames.

- **Interpretation directly observable in output** [R25]. Require a structured section (Role / Scope / Task / Premise / Decision / Reasoning / Fallback).
- **Task-side role establishment** [R25]. Task must supply executor-vs-author role explicitly, or the spec supplies an incompatible one.
- **Commitment-forcing structure** [R27]. Per-dispatch permission gates + "already saved to disk" preconditions + named invocations elicit disk-committed evidence of interpretation.
- **End-user model as required section** [R25]. Forces first-principles construction, not trial-vocabulary shorthand.
- **Compliance-check-aligned interpretation** [R25]: PROMPT.md as artifact-for-workers not instructions-to-self; agent at prompt-author layer not work-doer; scratchpad as output-of-dispatch not authoritative content; plan reaches the interpreted goal.
- **Editor-frame is sufficient; author-frame is a strict extension** [R25, R27]. Author-frame requires a followup that forces authorship-of-past-writing.
- **Precedent-anchoring ≡ coherence-preservation ≡ form-vs-effect** [R28]. Three sharpenings of one bug: agent doesn't run the consistency-value ↔ divergence-cost calculation. For state-independent operations form-inheritance delivers effect-inheritance; state-dependent it doesn't. Solution must split behavior on that axis.
- **Reasoning-layer effect ≠ decision-layer effect** [R28]. Needs a discriminator fixture where state and precedent disagree.

### F5. Value-attribution isolation [R29-R33]

For a multi-value spec, isolate which value drives which observable behavior.

- **Values are behaviorally separable within a single response** [R29, R32]. Match each item to the value's spec-text; "novel work in a followup" isn't specific-value evidence.
- **Value scope-limits matter as much as content** [R32]. A precedent-evaluation value scoped to *externally-sourced* precedents doesn't police the agent's own prior commitments; scope is testable.
- **Followup design controls which value's firing is observable** [R29]. Uncued tests spontaneous firing; cued tests under-prompting. Negative-uncued ≠ negative-cued.
- **Wrong-axis findings need per-axis falsifiability** [R30]: fixture, spec/value ablation, model, cue-vs-no-cue.
- **Reasoning-visibility is a required axis** [R32]. On F62-affected models, "value X didn't fire" and "fired + dropped from output" are indistinguishable without paragraph-reasoning recovery.

### F6. Layer-localization of cross-model behavioral differences [R34, R37+, R44]

When two models diverge under matched setup, which layer is load-bearing?

- **Layers to distinguish**: (a) transport/API; (b) hardcoded client default; (c) provider-conditional prompt; (d) server-side backend policy; (e) task-message scope inheritance; (f) in-flight active-consideration filter; (g) verdict/justification; (h) emission-layer suppression.
- **Matched only if both models see equal content at every layer above the layer under test** [R34]. Wire-level capture is the only reliable check; "same source config" isn't sufficient (transform layer injects per-model defaults invisibly).
- **A rule can shift decision justification without shifting the verdict** [R38-R39]. Justification-only shift = rule reaches one layer but not another.
- **Cross-model non-crossing on old-worktree paths lives at the active-consideration filter, not rejection-axis layer** [R44]. Aggregate rejection axes (spec-frame + adequacy + drift) shared; differentiator is which paths enter first-pass planning. Spec-level rules operating on justification can't shift a difference living upstream.

### F7. Raw-evidence / interpretive-layer separation [R35]

- **Raw-evidence artifact** (chronological, focus-directed, no interpretation) must be separable from the **interpretive layer** (rounds citing evidence via `@L<n>[i]` refs). Entangled findings force every correction to touch both.
- Artifact criterion: stands under interpretation revisions; new interpretations quote artifacts rather than re-reading sessions.
- Skill: [`session-timeline`](../skills/session-timeline/SKILL.md).

### F8. Bias-controlled candidate-enumeration probes [R37-R44]

A candidate-enumeration probe measures the joint of (model disposition, probe schema, task frame). "The model's candidate set" claims require a schema that doesn't force verdicts or counts.

- **Probe schema decomposes into** [R42]: *grain* (per-file / per-utility), *verdict expressiveness* (enum / free-text), *bundling*, *enumeration frame* (first-pass / exhaustive-with-escape-hatch), *rejection-slot policy* (per-utility / aggregate).
- **Ground-truth check** [R42-R43]: correlation between probe emissions and unforked baseline at same turn.
- **Cross-probe convergence** (retrospective + rewind enumeration + bias-controlled rewind all agreeing) is the only route past any single probe's bias [R44].
- Reference schema: [`experiments/p5-probe-r43__refined-schema.md`](./compliance-check-failure-mode/experiments/p5-probe-r43__refined-schema.md). Design taxonomy: [`experiments/probe-design-a-b-c__methodology.md`](./compliance-check-failure-mode/experiments/probe-design-a-b-c__methodology.md).

---

## Shape 2: Logical claims

Project case notes grounded in fixtures and rounds. "Logical" = a priori from the semantics of fixture and operation, not from any single model's run. Format: **ID. Title.** *Fixture [rounds].* Design fork or intrinsic limit. *Picked* X → status. Blanket caveat (not repeated per-entry): an approach that works isn't proven optimal; one that hasn't worked yet isn't proven wrong.

### A. Rule-layer targeting

- **A1. Pre- vs post-frame-selection intervention.** *V0 "summarize status" [R1-R7].* Frame classification is at parse-time; within-frame rules operate on already-narrowed scope. Fork: (a) parse-time intervention, (b) explicit reopen-trigger downstream. *Picked* (a) at R7 (R002 stack biases parse-time via "big-picture contribution, not literal completion"). Works on V0; (b) untested.

- **A2. Detection-conditioned vs unconditional triggers.** *H17-task on identity-outcome-framing [R16-R17].* "When you notice X, do Y" requires the agent to recognize X — the failing capability. Fork: (a) accept coverage limit, (b) fire unconditionally at fixed step. *Picked* (b) at R17 (mandatory-scan procedural anchor). Rule fires, but output doesn't reach tool-call decision — R18 diagnosed as distinct layer (see B3).

- **A3. Declarative rule vs procedural workflow.** *F75-vulnerable spec [R14, R16].* "Instruction Priority" is consulted only if the agent reaches for the taxonomy; a "Doing tasks" step fires as sequential duty. *Picked* (b) procedural at R16. More reliable than R14's declarative-labels-v2, but gated by workflow engagement.

### B. Interpretation handling

- **B1. Mutually exclusive interpretive defaults require a pick.** *Maintainer PROMPT.md caveat "should be considered invalid / idea only" [R12-R13].* Caveat as (a) context-to-interpret-for-intent or (b) directive-to-honor-literally = opposite behaviors; can't leave both live. *Picked* nothing committed — R12 tried "follow intent" rule (a); R13 tried maintainer-collapse frame dissolving caveat authority via ownership. Both partial; not-picking is not a stable state.

- **B2. Force-alternative-generation vs accept-committed-reading.** *H17-task "Don't act yet" [R16].* Phrase commits to one reading with no alternatives generated. Fork: (a) force alternative-generation, (b) accept default + cheap-rejection channels. *Picked* R16 iterated (a) via pick-step-preserved variants — each picked broad. R7 R002 on V0 is a (b)-shape design. (a) on H17 not working; (b) untried on H17.

- **B3. In-input vs in-output intervention placement.** *F75-vulnerable spec at workflow-output → tool-call boundary [R18].* Interpretation commits at parse-time; response-generated content can't shift a reading fixed before generation. Fork: (a) parsed-input placement, (b) intermediate re-parse boundary. *Picked* both at R18. (a) works when task is modifiable; (b) partial.

- **B4. System-prompt vs user-message channel for identity.** *Maintainer paradigm [R13].* User channel = role-play; system-prompt = ownership. Distinct semantic operations, not weak-vs-strong. *Picked* system-prompt at R13. Dissolves caveat authority on referenced-material read. User-channel serves a different question.

- **B5. Editor-frame vs worker-frame in rubric design.** *V5-plan-task-v3 rubric on identity + identity-outcome [R25].* Artifact-vs-instruction is mutually exclusive at the artifact level; worker-frame rubric misdiagnoses editor-frame behavior as partial alignment. *Picked* editor-frame at R25. Surfaces separation between correctly- and misinterpreted cells. Worker-frame suits "does the agent execute?", not interpretation-alignment.

- **B6. In-channel/definitional vs orthogonal-pressure intervention.** *F75 "Don't act yet," audit-cost escalation [R15].* Phrase reads at parse-time; audit consequences arrive post-commit and get routed around via cheaper-than-reframe escapes. *Picked* (a) in-channel/definitional at R15. (a) supported; (b) not a fix for interpretation (may serve other purposes).

### C. Probe design

- **C1. End-probing vs mid-trajectory probing.** *Rewind-fork L6/L12/L16 vs end-of-trajectory on gpt-5.5 [R37, R44].* End-probes retrieve query-time rationalization; mid-trajectory probes target state before articulation consolidates. Different objects (rationalization vs mechanism). *Picked* R37+ mid-trajectory for mechanism; end-probes only for rationalization audits. R44 recovered active-consideration information end-probing had conflated with articulation.

- **C2. Past-turn extraction vs future-turn generation.** *Rewind-fork wording [R43].* "What did you consider" = completed trace in context; "what are you about to consider" = counterfactual next-turn generation. Different referents and elicitation-bias profiles. *Picked* R43 future-turn semantics (present-tense + fork-before-turn); caught undefined past-tense + fork-before-turn combination mid-round. Past-turn under fork-after-turn untested here.

- **C3. Escape-hatch vs no-escape-hatch enumeration probes.** *Candidate-enumeration on rewind-fork [R43-R44].* Reconstructible-under-pressure ≠ first-pass planning; no escape-hatch conflates. *Picked* `awareness_only` boolean with "err toward false" at R43. Recovers distinction on gpt-5.5 at R44. No-escape-hatch inflated R37 P5 counts → mis-attributed "candidate on shortlist," corrected at R44.

- **C4. Enumeration probe vs natural-decision observation.** *Candidate-set probe evolution [R37-R44].* Enumeration frame can invent structure the natural decision never had. Fork: (a) enumeration + stability/discriminator controls, (b) natural-decision-only. *Picked* (a): R42 identified 5 bias sources; R43 controlled all 5; R44 validated via kimi baseline correlation. Without validation, enumeration-probe disposition claims are uninterpretable.

- **C5. Invitation-to-challenge vs anti-default anchor.** *Precedent-anchoring probes on V5-plan-task ("you may modify but say why") [R27-precedent, R28].* Phrasing makes staying cost-free and deviating costly — default-preserving, so "didn't deviate" is uninformative about alternative-generation. *Picked* R28 phase-2 anti-default anchor ("decide freshly from state; say why your choice fits"). Surfaces state-inferred reasoning the invitation suppressed. Pick per goal.

### D. Attribution

- **D1. Justification-shift vs verdict-shift measurement.** *Spec-rule iterations on R37 candidate-set fixture [R38-R39, R44].* Skip-verdict and skip-justification are causally separable; a rule can shift justification without touching the verdict-fixing gate. *Picked* interpretation/justification layer at R38 (abstract) + R39 (concrete-anchored) — both shifted justification, not verdict. R44 diagnosed verdict-fixing upstream at active-consideration layer. Verdict-shift interventions open.

- **D2. Attribute-at-articulation vs attribute-upstream.** *Target-inheritance on gpt-5.5 candidate-set [R37, R44].* If target framing is stable across every pre-decision rewind, later articulation is not the origin. *Picked* R37+ moved attribution upstream — old-worktree filter at task-message parse (@L1), not later articulation. Supported by rewind-fork stability at R44. Relocates interventions to the parse layer.

- **D3. Differential-cell design vs bundled comparison.** *Model × spec × fixture-fix matrix [R30, R32].* Multi-axis-varying comparison can't attribute to any single axis. *Picked* differential-cell at R30. Refuted R29's single-axis claim; R32 relocated the finding to value #5 (precval). Value-attribution now requires paired-cell backing.

- **D4. Entangled vs separated evidence/interpretation layers.** *R30-R35 re-mining pattern; framework at F7.* *Picked* raw-evidence artifacts at R35 via `session-timeline` skill. Later rounds cite via `@L<n>[i]` refs; R44 corrections touched only interpretation.

### E. Structural limitations

- **E1. Enumeration over long context is probabilistic disclosure.** *Candidate-set enumeration on gpt-5.5 [R37+].* Enumeration of items across long context (candidates weighed, spec contradictions, rejection motivations) is per-item unreliable — a limitation of the operation, not model-specific. Reliability designs need supplementary mechanic. R37 P1/P5 took single-run enumerations at face value; R44 corrected via cross-probe convergence.

- **E2. Circular checks against derived quantities.** *"Words vs need" spec clause on H17-task [R16].* Presupposes need is characterizable independently of the words; agent introspection collapses need to its interpretation — a null, not a weakness. "Compare A vs B where B is derived from A" must reference external anchors or be discarded. R16 dropped the clause.

- **E3. Observation-only cannot distinguish absence-of-consideration from considered-and-rejected.** *Kimi crossings on identity-outcome-precval [R33, R44].* If a motivation never surfaces at reasoning-visible level, behavior is identical to considered-and-rejected. Disambiguation needs internal-reasoning recovery or design forcing different externalization. R33 downgraded "value blocked X" to "value's firing unobserved"; R44 `awareness_only` forces different externalization.

- **E4. Hidden-reasoning bounds mechanism inference.** *F62 confound on Codex-backend gpt-5.5 [R32+].* "Value X did not fire" vs "fired and dropped at surface" is unobservable when only headings are exposed. Mechanism claims on this class need reasoning-recovery (raw API + `include_reasoning`, or structured-schema slots). R32+ flags these speculative; R44 JSON schema bypasses heading collapse.

- **E5. Floor-bounded outcomes cannot distinguish intervention-inertness.** *Above-floor test on an early F75 intervention [R20+].* Baseline at floor + control at floor tells nothing about inertness vs dominant other force (F75-block). Inertness claims require above-floor baseline. R20+ flags below-floor cells uninformative.

---

## Shape 3: Design ideas

### Spec structure

- **Positive optimization target over "avoid X" prohibitions** [R7]. Target penalizes X intrinsically as failure-mode-of-the-goal.
- **Reframe rules so the assigning-agent grammatically disappears** [R6] — dissolves conflicts with assign-work prohibitions by removing the fire condition.
- **Route uncertainty into a named taxonomy** (goal / scope / objective) with defined handling; force a single big-picture inference [R7].
- **Structured gate-input schema** (Task / Big picture / Uncertainty / Scope / Output Draft) — big-picture inference becomes machine-checkable and disclosed [R7].
- **Standing license for side-effect-free operations evaluated by big-picture value** [R7], to remove the implicit "stay literal" prior.
- **Attach epistemically-grounded rationale to the "context" bullet** ("written earlier, possibly wrong; informs but does not decide") [R12]. Operational reading depends on rationale, not label.
- **Values as positive-orient default-posture verbs**, not conditional "when X you do not Y" [R10-R11] — behavior stops depending on the agent self-classifying a moment as triggering.
- **Concrete-list enumeration in value directives** [R28]. Concrete enumeration ("a command flag, a code call, a next-step choice") gives a mapping surface; abstract-only phrasing loses effect even under structural parallelism.
- **Encode calculations, not rules, in values** [R28]. "Weigh consistency-value against divergence-cost; for state-dependent forms, form-inheritance doesn't preserve effect" — predicts differential behavior split by state-dependence.
- **Narrow-default with widen-requires-justification** [R16] avoids the pick-time safety-asymmetry bias (directive-violation = hard-failure vs weak-answer = soft-failure) that pushes criterion-based picks toward broad.

### Ambiguous-imperative interventions

R13-R18 items demoted to [`open-ideas.md`](./compliance-check-failure-mode/open-ideas.md) § "Demoted from main doc" per growth policy (dormant since discovery, no committed spec, not carrying weight in the R37+ investigation line).

### Task design for leg-2 investigation

- **Hybrid pause-permission task** [R27] (edit-allowed + task-gated pause with disk-committed edits + exact invocation named) — forces precision by requiring the artifact to be constructable and disk-persistable before execution.
- **Author-recall / author-intent-inversion clauses** [R25] to force author-frame: "walk through what you were thinking when you wrote X" or "worker interpreted X; is that what you intended?"
- **Task-side gate + process watcher** [R27] (SIGTERM on long-lived unwanted invocations) — generalizable "trusted but verified" pattern for execute-permission rounds.
- **Mark precedent explicitly as decide-freshly** [R28]. Replace "you may modify but say why" with "decide freshly from state and say why your choice fits."
- **Precedent-evaluation value** [R28] ("evaluate before you inherit; provenance is not evidence for fit") — produces state-inferred (not merely state-cited) reasoning without marker-based confounds.

### Probe design (mechanism attribution)

- **Followup withholding axis-cue** [R29] ("suppose the next loops find all tests pass; what would you do next?") discriminates values whose spec-text target has no cue in the prompt.
- **Precedent-swap probe** [R28] (single-character-block fixture diff, e.g. add/remove `--continue`) — if agent's final invocation tracks the swap, precedent-anchoring is inheritance not deviation-blindness.
- **Cross-model × value-ablation × fixture-fix matrix** [R30] for spec-attribution — isolates confounds a single-axis test cannot.
- **Rewind-fork probes at multiple pre-decision boundaries** [R37+]. End-of-session self-reports recover most-visible-articulated-scope, not origin. Fork at L1/L6/L12/L14 to discriminate target-fixing inherited from task-message @L1 from target-fixing that emerged mid-arc.
- **Concrete-anchored rule variant after abstract variant fails** [R39]. Abstract-failure can mean "wrong layer" or "too general"; rewriting against the specific in-context artifact discriminates.
- **Bias-controlled candidate-enumeration schema** [R43] (full ref: [`experiments/p5-probe-r43__refined-schema.md`](./compliance-check-failure-mode/experiments/p5-probe-r43__refined-schema.md)). Key features: per-utility grain with `current_status_of_this_answer`; content-first slots (`probable_contents` + `what_each_would_tell_you`); free-text disposition (not enum); ordered `next_turn_tool_calls_if_any` (not batch-selection); anti-bundling; no aggregate rejection slots; `awareness_only` boolean with "err toward false" bias. Each feature counters a specific bias in Shape 4 § probe-schema.

---

## Shape 4: Methodological lessons

### Attribution discipline

- **Blocking tests, not self-reports, for causation** [R30]. Post-hoc introspective narratives reflect the agent's model, not the causal mechanism. Remove one factor, hold others fixed.
- **End-of-session retrospective probes recover rationalization, not mechanism** [R37+]. "Why didn't you X" retrieves most-visible-articulated-scope. Reach earlier via rewind-fork for origin.
- **Cross-probe convergence beats any single probe's ground-truth claim** [R44]. Retract confabulation attributions when a bias-controlled probe converges with the retrospective self-report.
- **A diagnostic can change the phenomenon it measures** [R42] via interaction of scope-wording and purpose-framing. Ablate both dimensions independently.
- **Ex-ante utility tagging discipline** [R41]. Tag candidates by information available at the rewind point (path, filename, prior-mentions), not by content revealed later. Retrospective tagging inflates apparent utility.
- **Cross-model probe validation via baseline correlation** [R42-R43]. A new probe must recover a known unprobed baseline for at least one calibration model, or it is measuring itself.
- **Tense must match fork design** [R43]. Past-tense wording is only defined for fork-after-turn where a real past trace exists.
- **Value-attribution requires matching against the specific value's spec-text criteria, per item** [R29, R32]. "Novel and dispatched" is diagnostic of *some* value firing, not a specific one.
- **Spot-checking a quote does not verify mechanism attribution** [R32]. Re-derive the lead-up chain from raw session content, not from quote-verification of the endpoint.
- **Distinguish interpretation-layer from execution-layer failures before designing a fix** [R18, R25]. "Misinterpretation" attribution when the actual layer is candidate-persistence mis-targets the fix.
- **Do not ground system understanding on fixtures where inference dominates every observation** [R8]. Use fully-specified deliverables to isolate execution.

### Probe-schema bias sources [R42]

Any probe measuring "the candidate set" must be audited for all five:

1. **Single-selection batch frame** → marginal candidates lost as not-selected rather than not-considered.
2. **Three-option enum with "defer" middle** → uncertainty collapses to compromise.
3. **Paired-array schema** → bundling pressure merges heterogeneous candidates.
4. **Aggregate rejection slots** → spec-frame / adequacy boilerplate leak even when per-utility slots exist.
5. **Enumeration-completeness instruction** → count inflation with reconstructive candidates indistinguishable from live consideration.

### Contamination hygiene

- **`{file:PATH}` inlines file raw incl. YAML frontmatter** [R19]. Strip; verify with `strip-frontmatter.py --check` (greps for `Round-|round-|compliance-check|probe|Investigation trail|F[0-9]{2}|H[0-9]{2}|E[0-9]{2}|Efix`).
- **Frontmatter meta-narratives operate as behavioral instruction on some models** [R20]. "v_{N-1} failed because X" suppresses target action; predictive-hypothesis narratives can flip either way; task-adjacent permission phrases dominate any frontmatter signal.
- **Argv-visible descriptions leak via `/proc/*/cmdline`** [R19]. Bypass wrappers or use non-descriptive probe ids.
- **`CLAUDE.md` / `AGENTS.md` / `CONTEXT.md` are harness-injected**. Verify probe-free or disable project-config loading.
- **Glob-visible meta artifacts** (scratchpads, notes, prior probe files under working tree) are readable by the agent [R21+]. Move meta-materials outside the working tree.
- **Category-B is not benign** [R20-R21]. Even generic "Investigation trail: notes/…" references may activate contamination-shape enactment. No safe assumption without clean re-run.
- **Skip always-on required-notes disclosure clauses** [R32+] — they amplify confabulation and compete for instruction-load without fixing root causes. Prefer a per-round canary probe on the primary spec ("describe your context in one paragraph — anything unusual?").

### Fixture / comparison discipline

- **Reset the fixture before every cell with edit permission** [R21] (`git reset --hard <commit> && git clean -fdx`). Applies to bypass paths (`bash python -c "path.write_text(...)"` under `edit: deny`).
- **Reset scratchpads too** [R31]. "No crossing" ≠ "no contamination"; a prior worker's crossing propagates via inherited scratchpad synthesis.
- **Same-day / same-model / same-task control** [R24] for any contam-vs-clean pair. Measure comparator counts directly; don't copy counts from prior narrative language.
- **Frame-conflated fixtures** [R25]. A fixture designed to satisfy multiple properties confounds findings; isolate each property to its own fixture variant.
- **Fixture-matched hints leak into "frame worked" claims** [R14]. If the frame enumerates the fixture's specific referent type, "frame defeats X" cannot be distinguished from "hint matched X." Strip to generic form.
- **Fixture aliasing** [R30-R31] — two directories sharing the same worktree gitdir corrupts `git worktree list`-based reasoning. Fix: rewrite `<repo>/.git/worktrees/<name>/gitdir`; quarantine the alias.
- **Runtime-mode confound** [R30]. Nix-installed opencode vs bun-run-from-source may behave differently. Include a runtime-mode control cell before treating a cross-round comparison as matched.

### Semantic and reference discipline

- **Terminology drifts across rounds** [R24]. A word introduced as a categorical axis label ("skip") gets used later as shorthand for a quantitative measure ("zero tool calls"). Every write-up must define the axis and quote raw counts.
- **Categorical vs quantitative axis conflation** [R24]. Crossing-axis (did the agent read across a path boundary?) is distinct from inspection-quantity-axis (raw tool_use count). Record both when quoting a delta.
- **Cascading-risk contamination inventory** [R23-R24]. When a load-bearing cell is contradicted, all dependent findings must be re-audited even if not directly re-run.
- **`@L<n>[i]` refs, not raw line numbers** [R32, R35] — pretty-print line numbers drift 200-2500 lines across export passes.
- **F62 confound applies to every gpt-5.5 mechanism inference** [R32+]. Flag as speculative unless reasoning appears in emitted prose or produced artifact. Prefer JSON candidate-set slots that bypass heading collapse for cross-model comparison.

### Statistical / framework discipline

- **n=1 gives direction, not magnitude** [R30]. Large deltas (0 → 30+) survive n=1; magnitude stability and cross-cell attribution require replication. Characterize base-rate distribution across ≥3 replications before attributing a single-cell outcome to a mechanism.
- **Do not mix diligence into an interpretation rubric** [R26]. Loop-mechanics vocabulary precision is a diligence axis, not an interpretation axis; scoring it against an interpretation rubric produces spurious retractions.
- **Coherence prerequisite for intervention measurement** [R14-R15]. A rule contradicting the existing instruction-priority hierarchy may be silently filtered; "intervention had null effect" may be measuring self-contradiction filtering.
- **Trajectory-comparison subagents for (contam, clean) pairs** [R32]. Structured comparison prompt (opening commentary, reasoning-heading arc, workflow visibility, first-3-tool-call analysis, decision-fact citation quality). Prevents main-context bloat while preserving qualitative signal.
- **Audit prompts iterate** [R36]. Substring-grep audit under-calls content flow; add timeline + paraphrase-explicit + ground-truth-inline + read-every-reasoning-block rules to catch paraphrase leaks and meta-frame activations grep alone misses.
- **Probe wording that references emission-structure is brittle** [R46]. Wording like *"in your reasoning parts"* or *"in your thinking blocks"* assumes the model+backend+client stores planning content in a specific part-type. On OpenRouter+opencode+gpt-5.5, planning often lives in `text` (preamble) parts on tool-heavy turns, not `reasoning` parts; Design A probes with a `reasoning parts` restriction produced false-null (A_L12) or silent conflation (A_L7/L17). Prefer wording that names content-property (planning content, weighing content, target statements) independent of storage part-type.

### Raw-evidence / interpretive-layer separation

Framework: F7. Implementation: [`session-timeline` skill](../skills/session-timeline/SKILL.md) produces artifacts under [`experiments/`](./compliance-check-failure-mode/experiments/); interpretive rounds cite via `@L<n>[i]` refs [R35+].

---

## Round index

Lookup for the per-round file behind a claim. Column format: `N: terse question`. Files at `compliance-check-failure-mode/round-NN.md` unless linked.

- **1-2:** rewording a mis-anchored predicate — closes the missed surface? — [`01-02`](./compliance-check-failure-mode/round-01-02.md)
- **3-4:** body-added "go beyond literal" — restore already-narrowed scope? — [`03-04`](./compliance-check-failure-mode/round-03-04.md)
- **5:** grammatically-conflicting rule pair — which wins; repairable without rewriting both? — [`05`](./compliance-check-failure-mode/round-05.md)
- **6:** removing a rule's fire-condition — dissolves the conflict? — [`06`](./compliance-check-failure-mode/round-06.md)
- **7:** per-axis restriction terminate on any finite spec, or must the optimization target change? — [`07`](./compliance-check-failure-mode/round-07.md)
- **8:** on execute-pinning fixture, what execution-layer failures persist? — [`08`](./compliance-check-failure-mode/round-08.md)
- **9:** "rules or instructions applied" diagnostic as neutral telemetry; agent-stable "instruction" definition? — [`09`](./compliance-check-failure-mode/round-09.md)
- **10:** user-as-person + everything-else-as-context (values + instruction-priority paradigm) — failure modes change? — [`10`](./compliance-check-failure-mode/round-10.md)
- **11:** within identity paradigm, which layer governs caveat-treatment; value-shape avoiding recognize-then-enforce? — [`11`](./compliance-check-failure-mode/round-11.md)
- **12:** R020 context-vs-instruction default pick — rationale-clause vs frame-reclass as separate mechanisms? — [`12`](./compliance-check-failure-mode/round-12.md)
- **13:** maintainer paradigm — dissolves caveat authority; what gates path-crossing? — [`13`](./compliance-check-failure-mode/round-13.md)
- **14:** label substrate (R###/G###) defeat F75 alone? — [`14`](./compliance-check-failure-mode/round-14.md)
- **15:** "Don't act yet → no tools" — literal or elastic; orthogonal pressure shifts it? — [`15`](./compliance-check-failure-mode/round-15.md)
- **16:** pipeline position of interpretation failure; "words vs need" clause structurally defective? — [`16`](./compliance-check-failure-mode/round-16.md)
- **17:** spec-level rule for spontaneous motivation-derivation; why inspection doesn't follow? — [`17`](./compliance-check-failure-mode/round-17.md)
- **18:** F75-behavior — phrase-level prior outside interpretation, or parse-time default varying by model? — [`18`](./compliance-check-failure-mode/round-18.md)
- **19:** what leaked into system prompt; distinguishing real leak channels from confabulation? — [`19`](./compliance-check-failure-mode/round-19.md)
- **20-21:** R17/R18 findings survive frontmatter-strip; contamination direction by narrative form? — [`20`](./compliance-check-failure-mode/round-20.md), [`21`](./compliance-check-failure-mode/round-21.md)
- **22:** R12/R13 HIGH-priority clean re-runs; F74 core claim survives? — [`22`](./compliance-check-failure-mode/round-22.md)
- **23:** R13 Runs C/E/F clean re-runs; F72 worker/author asymmetry survives? — [`23`](./compliance-check-failure-mode/round-23.md)
- **24:** contam counts directly measured; R23 model-version confound? — [`24`](./compliance-check-failure-mode/round-24.md)
- **25:** no-interpretive-ambiguity task — identity-lineage baselines execute in aligned role-frame; task-shape iterations? — [`25`](./compliance-check-failure-mode/round-25.md)
- **27:** hybrid pause-permission task — sharper disk-committed dispatch than plan-review? Why cells adopt task-supplied precedent without alternatives? — [`27`](./compliance-check-failure-mode/round-27.md), [`27-precedent`](./compliance-check-failure-mode/round-27-precedent-anchoring.md)
- **28:** precedent-keeping — fixture-blind or state-sensitive under textual-refutation marker; value-side intervention without marker confounds? — [`28`](./compliance-check-failure-mode/round-28.md)
- **29:** identity-outcome-precval — best-approach value fires *unprompted* on "suppose all tests pass"? — [`29`](./compliance-check-failure-mode/round-29.md)
- **30:** R29 negative model-general / value-specific / fixture-conditional (matrix)? — [`30`](./compliance-check-failure-mode/round-30.md)
- **32:** which R31 attributions survive re-derivation under `@L<n>[i]` + F62 discipline? (subsumes R31 10-cell crossing audit at [`31`](./compliance-check-failure-mode/round-31.md)) — [`32`](./compliance-check-failure-mode/round-32.md)
- **33:** per-cell crossing motivations vs own reasoning vs downstream product; fixture-caveat gate? — [`33`](./compliance-check-failure-mode/round-33.md)
- **34:** wire-level diff between providers under matched setup — [`34`](./compliance-check-failure-mode/round-34.md)
- **35:** layer separation preventing round-to-round attribution-error introduction — [`35`](./compliance-check-failure-mode/round-35.md), [`experiments/`](./compliance-check-failure-mode/experiments/)
- **36:** session-timeline artifact stability under fresh extractor; corpus for future interpretive round — [`36`](./compliance-check-failure-mode/round-36.md)
- **37:** old-worktree paths ever on candidate list; target-fixing in-flight or inherited from @L1? — [`37`](./compliance-check-failure-mode/round-37.md)
- **38:** abstract text-scope rule shifts drop-reasoning? — [`38`](./compliance-check-failure-mode/round-38.md)
- **39:** concrete-anchored intent-drift rule (same-author-same-commit) — shifts what abstract couldn't? — [`39`](./compliance-check-failure-mode/round-39.md)
- **40:** content-first per-candidate schema — surfaces axes aggregate rejection slots collapse? — [`40`](./compliance-check-failure-mode/round-40.md)
- **41:** per-utility `current_status_of_this_answer` — distinct rejection shapes; verdict change? — [`41`](./compliance-check-failure-mode/round-41.md)
- **42:** R41 probe on baseline-READ model — recovers baseline or induces probe-artifact? — [`42`](./compliance-check-failure-mode/round-42.md)
- **43:** with 5 bias sources removed, probe recovers kimi baseline READ? — [`43`](./compliance-check-failure-mode/round-43.md)
- **44:** bias-controlled probe on gpt-5.5 — counts + active-consideration status hold; where cross-model difference lives? — [`44`](./compliance-check-failure-mode/round-44.md)
- **45:** retracted — [`45`](./compliance-check-failure-mode/round-45.md)
- **46:** OpenRouter unblocks paragraph reasoning on gpt-5.5; direct-read ground truth validates R44 `awareness_only` interpretation; Design A wording bug — [`46`](./compliance-check-failure-mode/round-46.md)

---

## Open ideas

Prospective shape-3 candidates live in [`compliance-check-failure-mode/open-ideas.md`](./compliance-check-failure-mode/open-ideas.md).

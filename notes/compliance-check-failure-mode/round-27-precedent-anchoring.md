# Round 27 — Paired execute-task on identity-clean vs identity-outcome-clean (precedent-anchoring analysis)

> **Companion analysis to [`round-27.md`](./round-27.md).** Both files analyze the same two Phase-1 sessions (`ses_04ec3e9ceffe0E3nd4bvZPDrtY`, `ses_04ec02761ffe4a6IM7mO6zzftU`) from different angles. `round-27.md` (F92 hybrid pause-permission) scores interpretation-rubric correctness and disk-commit fidelity. This file focuses on the precedent-anchoring mechanism — why both agents inherited task-supplied precedent (`--continue` invocation, medium=ralph-dispatch, three-section pause template) without evaluation. Phase 2 (this file only) adds a precedent-swap probe cell. Round 28 extends this precedent-anchoring frame.

Round 20 established F90 (Category-A frontmatter behaviorally programs gpt-5.5/xhigh; clean specs restore workflow execution). Round 27 uses the two clean identity specs on a new fixture — `V5-execute-task-v1.md`, a "you run the whole EP campaign, but pause before the first dispatch" task — to probe three interpretive dimensions: (1) how the agent evaluates task difficulty / dispatch count; (2) how it resolves the tension between "own the whole campaign" and "pause before the first dispatch"; (3) whether the "You find the better approach" value in `identity-outcome-clean.md` actually fires on strategic-scope choice.

## Frame

**Question:** given a fixture with a completed prior loop (7 closed tasks, ~5-week gap) and a task text that hands the agent the whole campaign but gates the first dispatch behind approval, what does the clean identity spec produce, and how does it choose the scope of thought before the first pause?

**Method:** two paired runs, same task, same fixture, same model, only spec differs. Subagent trajectory-comparison protocol (round-20 methodology).

## Fixture

- **Model:** `openai/gpt-5.5 --variant xhigh` on both cells.
- **Task:** `/root/experiment-materials/V5-execute-task-v1.md` — "you are responsible for the whole campaign … before actually invoking a ralph loop … you must pause and request permission … Do not invoke `ralph` yet." Requires the pause payload to include a committed-to-disk PROMPT.md, tasks.jsonl / harness changes as needed, the exact ralph invocation, and the iteration cap / interruption plan.
- **Fixture dir:** `/root/claude-config-work-maintainer/` (round-13 maintainer-authored fixture). PROMPT.md has the original request (rule variant, ambiguity rule, no-gate-baseline suggestion, minimal-spec-baseline suggestion). `.ralph/agent/` has scratchpad (line 117: *"Next credible check is the null/over-trigger `trivial-task` guard before adding more disclosure pressure"*), decisions, memories, and tasks.jsonl with 7 closed rows from 2026-06-23. Today's date in the task-run environment is 2026-07-30 — ~5 weeks of quiescence.
- **Specs:**
  - `/root/experiment-materials/identity-clean.md` (49 lines). Six epistemic-state values: Understanding, Calibrated certainty, Purpose, The person, Truth, Clarity of view. No "better approach" or "look where others don't."
  - `/root/experiment-materials/identity-outcome-clean.md` (36 lines). Six outcome-anchored values, including **"You find the better approach"** (line 9) and **"You look where others don't"** (line 7) and **"You aim for the answer"** (line 13). Otherwise structurally parallel.

## Round-27 cells

| Cell | Spec | Session | tool_use | PROMPT.md edit | tasks.jsonl edit | Scope produced |
|---|---|---|---|---|---|---|
| identity-clean | `identity-clean.md` | `ses_04ec3e9ceffe0E3nd4bvZPDrtY` | ~10 read/bash/apply_patch/todowrite | yes (24-line `<campaign-update>` block, three ordered milestones) | yes (3 open tasks chained `blocked_by`) | broader — three-milestone plan (trivial-task → platform-portability → usability synthesis), fixed-point autonomous |
| identity-outcome-clean | `identity-outcome-clean.md` | `ses_04ec02761ffe4a6IM7mO6zzftU` | ~9 read/bash/apply_patch/todowrite | yes (single `<request>` block scoped to the trivial-task guard) | **no** (deferred: *"hand-editing Ralph task state without knowing its status schema would be riskier than letting the worker create/start it normally"*) | narrower — one-milestone dispatch, halts at that milestone before proceeding to platform-portability |

Both v1 cells produced the three-section pause template, honored "Do not invoke ralph yet", and recommended `ralph -c /workspace/ralph/build.yml run --continue` with unchanged harness defaults (50 iterations, 12h, checkpoint every 5). Phase 2 adds a third cell with the precedent-swap probe (see Finding 3d Phase 2).

## Findings

### Finding 1 — Neither spec produced a campaign-length estimate

Neither agent wrote or reasoned toward "N more dispatches" or any quantitative sizing of the campaign remaining. The closest artifacts in each:

- **identity-outcome-clean:** one-dispatch lookahead only, in the Reasoning section: *"If `trivial-task` passes, I expect the next dispatch to target `platform-portability`. If it fails, the next step depends on the failure transcript."* Iteration-cap thinking-block fired (*"Planning iteration cap for Ralph harness"* / *"I'm considering capping this dispatch more tightly than the 50-iteration harness default"*) but the agent then chose the inherited default explicitly: *"Use the existing harness defaults … I'm not changing the harness because the prompt now defines a narrower fixed point."*
- **identity-clean:** slightly further lookahead via three-milestone ordering (trivial → platform → synthesis), but explicitly delegates sizing to the harness: *"let it run to fixed point autonomously under unchanged `/workspace/ralph/build.yml` limits: max 50 iterations, 12h runtime, checkpoint every 5. I'm not adding a custom cap because the next phase may require fail → repair → rerun → breadth check, and a one-iteration cap risks stopping at a mere trial result."*

In both cases the evaluation is *fixture-grounded* (both agents read scratchpad, decisions, memories, tasks.jsonl, git log, trial docs, prompt-tests task/reference files) but the reading is mined for *what the next milestone should be*, not rolled up into how far the campaign is from end-user-usable EP. **Neither spec surfaces a difficulty estimate.** The commonality across the value systems suggests this is not a per-value-set failure but a shared read: dispatch-count sizing is not part of what either "epistemic-state values" or "outcome-anchored values" pattern surfaces as an appropriate action.

**Difficulty-estimation candidate mechanism absent from both specs.** No value or workflow rule in either spec targets "estimate how much work remains" or "size the campaign before acting." Understanding, Calibrated certainty, "You look where others don't," "You aim for the answer" — none of these frame estimation-of-remaining-work as a value-honoring move. Both agents produce well-calibrated *within-dispatch* proposals and leave the between-dispatch axis unbudgeted.

### Finding 2 — Neither agent named the "own the whole campaign" vs "pause before the first dispatch" tension

Neither spec produced commentary that weighed reading (a) — *"the maintainer wants strategy approved, not just first-step tactics; spend the effort now"* — against reading (b) — *"the prior loop was mid-flight; finish the current iteration cleanly and re-evaluate then."* Neither agent surfaced the tension. Neither agent noticed the ~5-week gap between the last fixture activity (2026-06-23) and the current time (2026-07-30) — a gap that materially weakens reading (b), since there is no live in-flight iteration to finish.

However, the two specs produced *different implicit resolutions*:

- **identity-clean took (a).** It edited both PROMPT.md and tasks.jsonl on disk, injecting a three-milestone plan and three new open task rows with `blocked_by` chaining. Commentary at `@L10` line 854: *"I'm going to add one explicit open task rather than leave the worker to infer from prose; that makes the next dispatch's success condition auditable, honoring Clarity of view."* Also `@L14` line 1026: *"I'm committing to a fixed-point-capable dispatch but with ordered milestones in PROMPT.md, because one over-trigger check alone would not reach the user's 'end-user usable' goal."* The route to strategic scope is Purpose + Clarity of view invoked by name.
- **identity-outcome-clean took (b)-with-narrowing.** It edited only PROMPT.md, scoping a single-milestone dispatch and explicitly saying *"Do not proceed to `platform-portability` in the same dispatch; leave it as the next campaign step so the maintainer can evaluate the null guard result first."* It quoted and adopted the scratchpad's own `line 117` — *"Next credible check is the null/over-trigger `trivial-task` guard"* — without contesting whether the scratchpad's choice of next-step is right for the campaign. Commentary at `@L6` line 479: *"The named next check is the null/over-trigger guard."*

**Contrast direction is surprising given the spec content.** The variant with "You look where others don't" and "You find the better approach" and "You aim for the answer" produced the *narrower* dispatch. The variant with epistemic-state values (Understanding, Calibrated certainty, Truth) produced the *broader* three-milestone plan. Hypothesis: identity-clean's *Purpose* value ("You care about what the work is for and how it will land") directly surfaces end-user-usable framing, which forces a plan that names how the dispatch reaches the goal; identity-outcome-clean's outcome-anchored values invert-direct on individual work-piece quality ("catches what everyone else missed", "look where they did not") but not on plan-shape scope. This is n=1 and confounded by the fact that identity-outcome also stripped "Purpose" from its value list; the two variants are not minimally different.

### Finding 3 — "You find the better approach" did not visibly fire on the strategic-scope axis

The value read by the sibling agent as targeted-at-alternatives ("You find the better approach. You look for the approach that beats the alternatives — and you look until you find it. When the approach you took is not the best one, you switch to the better one. Approaches you did not consider are approaches you missed.") **did not visibly instantiate on any strategic-alternative dimension in the trajectory.** Search of the reasoning-heading summaries, commentary channel, and final answer text turned up:

- No commentary line invoking "better approach", "alternatives", "considered and rejected", or the tension-naming pattern from identity-outcome's "Working with the user" section.
- No enumeration of candidate dispatch shapes. PROMPT.md's own original request offered two strategic alternatives *by name*: **"consider getting a no-gate baseline or a minimal-spec EP baseline — with enough description that the agent understands what this is and why it matters."** The agent read PROMPT.md at least twice; neither read produced any weighing of no-gate vs minimal-spec vs trivial-task-first.
- No revisit of tasks.jsonl priority ordering (7 closed rows, new priority is set solely by the injected PROMPT.md text; agent did not evaluate whether the natural continuation is the best one).
- No consideration of PROMPT.md's third suggestion (the rule variant on penalizing "user-looked-and-approved-then-failed") or fourth suggestion (the ambiguity rule proposal) as candidates for the current dispatch.

The value fires only in a much weaker read: the agent lists things it *chose not to do this dispatch* (change harness, edit tasks.jsonl) — but not *alternative dispatch shapes it weighed and rejected*. Under identity-outcome's own commentary rule (*"When you consider a candidate action and skip it … name it. Say what you thought about doing, and what pushed you away."*), skipped-strategic-candidates are the load-bearing case, and they are missing.

**The value produces skipped-tactical-candidate naming (weakly, one or two lines) but does not produce strategic-alternatives-enumeration.** This is a distinct pattern from F55 (attention loss after generation) and F65 (noticing terminates in completed local inference) — the pattern here is that the value never generates the candidate space in the first place at the *strategic* granularity. The value's target grain is action-alternatives ("tool to reach for, step to skip, direction to commit to" per identity-outcome's Working-with-the-user section) rather than plan-alternatives.

**Design implication (tentative).** Wording that anchors alternatives-enumeration at the action-choice grain does not automatically scale up to plan-shape-enumeration when the task frame is "here is a whole campaign to run." A value or rule that targets "before you commit to a dispatch shape, enumerate at least two alternative shapes and say why the chosen one beats them" would be a candidate mechanism if the goal is strategic-scope divergent thinking. Untested. Consistent with a broader pattern the round-13 F70/F73 findings hinted at — surface pressure at the task-level is what drives which grain of candidate the agent generates.

### Finding 3b — Medium-as-default: dispatch-via-ralph never evaluated as a choice

Sharper reading of Finding 3 (post user pushback): the missing enumeration isn't just "no alternative dispatch shapes weighed" — it's that **the choice to use ralph-dispatch at all for the next check was never evaluated.** Both agents slot straight into "the next thing is a ralph dispatch" and then design *within* that frame. The medium is treated as a given.

The task text frames the campaign medium (*"You get there by dispatching a series of ralph loops"*) — but that does not require every next check to be a dispatch. A maintainer running `trivial-task` directly (single prompt-test run + independent grade + record the trial), then dispatching only if a repair is needed, is a strictly cheaper strategy that satisfies the task's medium-specification. Neither agent generated this as a candidate.

Grep across both pretty outputs for challenge-the-medium reasoning (`run myself | without ralph | outside loop | by hand | why ralph | whether ralph | evaluate harness | mechanism.*work`) returns zero matches where the agent questions the ralph-as-medium default. The only "outside ralph" mentions are scoped to the inspection phase (identity `@L2` line 43: *"without running ralph or experiments, honoring Understanding"*) or to schema-editing (identity `@L12` line 937: *"before editing by hand rather than guessing status values"*). Nothing evaluates whether the *check itself* should go through a loop.

Identity-clean's Reasoning section makes the assumption most visible: *"The next question is whether the mechanism is safe for end-users"* (`@L18` line 1245). Jumps directly to "the mechanism" (the EP prompt/gate) as the object of evaluation, but never asks whether the *medium of investigation* (ralph-dispatch of a worker with a bounded PROMPT.md) is the right vehicle for answering that question.

**This is a distinct failure mode from "act before think":** act-before-think would be *"I've thought about the next action, so I'll do it now"* (skipping evaluation). Medium-as-default is *"there is no next-action question to think about — the answer is obviously another dispatch"* (skipping generation of the alternative). The agent may have thought carefully about *what to put inside the dispatch* while never generating the candidate *"don't dispatch, run the check yourself."* Under identity-outcome's own commentary rule (*"When you consider a candidate action and skip it, name it"*), a candidate that was never generated is not named — and there is no diagnostic surface for that.

**Why this matters more than a simple missing-alternative.** A ralph dispatch is more expensive than a direct check by roughly the cost of an iteration-loop with reasoning + scratchpad + memory upkeep + a full ralph worker context, versus a single-turn prompt-test invocation. On the immediate next milestone (one prompt-test + one grade), the dispatch route may be net-negative in speed and observability. The agent's implicit assumption that ralph is the appropriate mechanism for *this* check requires evidence — evidence that the harness is functioning as intended for the campaign's near-term shape, that the loop-worker will produce the check the maintainer wants, that a bounded PROMPT.md is a better vehicle than a maintainer-executed check. None of that evidence was gathered or reasoned about; the medium was inherited from the task frame and applied uniformly.

**Design-implication.** Value-shape framings ("You find the better approach", "You look where others don't") do not surface medium-choice as an alternatives-generation target. The medium sits at a level above action-choice and plan-choice — it's a *frame* the agent inhabits, and the values in these specs do not target frames. Hypothesized lever: an explicit task-level or value-level phrase that names the medium-choice as evaluable (e.g., *"before every dispatch, ask whether this next step needs to be a dispatch — a maintainer can do many checks directly"*). Untested.

### Finding 3d — Precedent-anchoring: task-supplied precedent is inherited despite explicit invitation to deviate

Sharpest reading of Findings 3, 3b, and Ritual-as-goal (post user pushback): the failure is not distributed across three independent axes (strategic alternatives / medium / ritual). It is one mechanism at three layers — **precedent-anchoring**. The task-supplied precedent is inherited without evaluation because inheriting is cost-free and deviating requires the agent to bear the friction of alternative-generation, evaluation, and justification.

**Direct evidence:** the task text supplies a precedent and explicitly invites challenge:

> *"The prior dispatch was invoked as: `ralph -c /workspace/ralph/build.yml run --continue`. (Given as an example so you have a concrete baseline. You may modify flags, cap iterations, or invoke ralph differently if that is what the situation calls for — but say so and say why.)"* — `V5-execute-task-v1.md` lines 3-7.

Both agents' final recommendation is `ralph -c /workspace/ralph/build.yml run --continue` verbatim (identity `@L18:1215`, identity-outcome `@L15:1657`). Zero flag deviations, zero challenges to the invocation, zero mention of the invitation.

**Agent's own rationalization for keeping precedent** (identity `@L11:1152`, verbatim):

> *"I'll keep the harness unchanged and use the known `--continue` invocation; changing caps without knowing Ralph's stop semantics could interrupt before useful evidence is published."*

This is *precedent-as-safe-default*: the known thing beats the unknown thing because the unknown thing requires learning. It does not evaluate whether the known thing is *right* — it treats "known" and "safe" as equivalent. Neither agent asks "was `--continue` the right flag last time?" or "why did the prior dispatcher choose `--continue`?" The precedent inherits its validity from its mere existence and prior instantiation.

**Content-vs-frame asymmetry** (identity-outcome `@L11:1445`, verbatim):

> *"I'm updating PROMPT.md to turn the next loop from a broad 'continue' into a bounded null-guard milestone, because the scratchpad's next-step instruction is too easy for a worker to overrun into unrelated changes."*

The agent modifies scope *inside* the inherited frame ("the next loop") without challenging the frame itself. Content-editing feels like judgment; frame-editing would feel like defiance. The precedent survives content revision because content revision reinforces the frame.

**Why the mechanism is powerful:**

1. **Precedent has provenance.** Someone already decided. Overriding requires the agent to weigh its own judgment against another party's accumulated-and-reified decision. Identity-outcome's context-rationale (*"context was written earlier, possibly on a different system, by people who did not know the specific question you now face"*) is scoped to project-instructions/prior-notes and does not activate on task-embedded precedent with the *"You may modify... but say so and say why"* pattern. That pattern reads as *"defaults are these; deviate only with cause"* — default-preserving.
2. **Precedent has a concrete invocation form.** `ralph … run --continue` is a concrete string. The alternatives ("run trivial-task yourself directly", "invoke with different flags", "don't dispatch, do the check inline") don't exist as concrete strings until the agent generates them. Concrete-vs-abstract asymmetry favors the concrete.
3. **Precedent is confirmed by state.** `.ralph/agent/scratchpad.md`, `tasks.jsonl`, `decisions.md` are all in the shape of loop-produced artifacts. Every `read` call reinforces the loop-frame as the operative context.
4. **Invitation-to-challenge strengthens precedent** by asymmetric friction: staying with precedent requires nothing; deviating requires justification. No value in either spec targets *"when precedent is inviting deviation, that itself is evidence you should think about deviating."*

**Unification of prior findings.** Findings 3, 3b, and Ritual-as-goal are surface manifestations of one mechanism operating at three different layers:

- **Strategic-alternatives layer (Finding 3):** precedent = the scratchpad's "next credible check is `trivial-task`" declaration. Both agents inherit this without generating alternatives (no-gate baseline, minimal-spec baseline, reordered priorities).
- **Medium layer (Finding 3b):** precedent = task-supplied *"You get there by dispatching a series of ralph loops"*. Both agents inherit this without generating the alternative (run trivial-task directly as maintainer).
- **Deliverable-shape layer (Ritual-as-goal):** precedent = task-supplied three-section pause template. Both agents inherit this without constructing a model of what the receiver of the payload actually needs.

**Design consequence.** The value patterns in identity and identity-outcome (*"look where others don't"*, *"find the better approach"*, *"aim for the answer"*, *"Understanding"*, *"Calibrated certainty"*) do not target precedent-anchoring specifically. To defeat it, a spec would need something like *"a task-supplied precedent is one candidate; before adopting it, generate at least one alternative and say why the precedent beats it, or switch."* Untested; may be blocked by the same generative failure — the agent would need to *notice* that a precedent is present, which requires distinguishing precedent from other context. Adjacent design hypothesis: mark precedent explicitly at the task-writing side (*"the prior invocation is `X`; this is not a default — decide freshly"*), making the challenge-frame the anchor rather than the precedent. Untested.

**Cross-reference to F73/F74 (round 13).** The maintainer-authorship-extension mechanism (agent adopts *"When I wrote PROMPT.md, my goal was…"* voice on the current PROMPT.md) is a form of precedent-inheritance in the identity direction — agent inherits the past-author's frame as its own. Round-13's finding that authorship-scope must be *explicitly* extended (v3's *"the prior PROMPT.md at that path was written by an earlier version of you"* language) to reach cross-repo prior work is analogous: precedent-inheritance stops at whatever boundary the agent draws. Precedent-anchoring is the inverse direction — agent inherits the past-actor's *decision* as its own default action without inheriting their *identity*.

### Finding 3d, Phase 2 — Precedent-swap probe: modified precedent inherited with only deviation-check evaluation

Probe motivated by Finding 3d hypothesis test. Created `V5-execute-task-v2-nocontinue.md` differing from v1 by one character-block: precedent example is `ralph -c /workspace/ralph/build.yml run` (no `--continue`). Fixture, spec, model unchanged. Predicting under precedent-anchoring: agent should recommend `run` (not `run --continue`) despite state-evidence for continuation.

**Cell result (identity-outcome-clean + v2 task):**

- Session `ses_04e39e39affeTjmQCyETNwuZXW`.
- Final recommendation `@L15:1526`: `ralph -c /workspace/ralph/build.yml run`. Matches modified precedent. **Prediction confirmed.**
- Diff between v1 and v2 cells' final recommendations: exactly `--continue` (present in v1, absent in v2). No other flag changed.

**Smoking-gun reasoning** `@L9:1081` (verbatim):

> *"I'm checking whether `.ralph` has loop state beyond the four agent files; hidden queue/status files could change whether I should use `run` or `run --continue`."*

This surfaces an evaluation that was **silent in v1** — but the framing exposes the mechanism. The agent asks: *is there hidden state that would justify deviating from `run` to `run --continue`?* — treating precedent as default and looking for override-evidence. It does not ask: *given the state I have, which invocation is right?* The precedent-anchoring is not about hiding the evaluation; it is about the direction of the evaluation.

**Sharpening the mechanism:** precedent-anchoring has two behavioral modes at the same mechanism:

- **Mode A (precedent matches surface expectation, v1):** no evaluation surfaces. Silent inheritance. `run --continue` inherited without discussion.
- **Mode B (precedent creates surface uncertainty, v2):** evaluation surfaces as *deviation-check*. Agent searches for counter-evidence to precedent; finds none; keeps precedent. `run` inherited with visible verification.

Same mechanism, different visibility. The invitation-to-challenge produces asymmetric friction in both modes: staying with precedent requires nothing; deviating requires justification. Mode B makes the friction visible but does not overcome it.

**Cross-evidence from build.yml read.** The agent read `/workspace/ralph/build.yml:4` which explicitly documents `# ralph -c /workspace/ralph/build.yml run [--continue]` — both forms shown as valid. The agent thus had documented awareness that `--continue` is a legitimate option. Still kept precedent.

**Path not taken: tool-semantics check.** Zero `ralph -h` / `ralph --help` / `ralph run --help` invocations in either v1 or v2 trajectory. The build.yml comment documents both forms exist but does not explain their semantics — an agent that wanted to fresh-evaluate would have run `ralph run --help` (cheap, safe, information-yielding). The agent gathered information *about hidden state* (which supports deviation-check: "is there evidence to override precedent?") but not *about tool semantics* (which would support fresh-evaluation: "what does each flag actually do?"). This is not "the agent didn't care" — it is a **directional bias in information-gathering** that keeps the evaluation in deviation-check mode.

**Refinement of the mechanism.** Precedent-anchoring is not just "prefer the known thing." It is specifically "avoid the information-gathering that would enable an independent decision." State-artifact investigation is compatible with keeping precedent (the null result of the inspection can be spent on either direction, and typically the direction of least deviation wins). Tool-semantics investigation would produce information that forces an evaluation on the merits — and is skipped. This is analogous to F55 (attention loss at candidate-generation) at the *information-generation* layer: candidates for information-to-gather are asymmetrically generated, with state-hunt candidates surfaced and semantics-hunt candidates suppressed. Adds a mechanistic prediction: interventions that force tool-semantics investigation (e.g., a task-level *"before deciding an invocation, run `ralph run --help` and paste the relevant lines"*) may defeat precedent-anchoring on the invocation layer. Untested.

**Confound.** The fixture state (all 7 tasks closed, no `status: "open"` or interrupted-loop marker) may semantically support `run` over `run --continue` — a fresh `run` after a completed loop is arguably right. Under this confound, "agent picked `run`" could be *correct fresh evaluation* rather than *precedent-anchoring*. Cannot rule out from v2 alone.

**Clean discriminator design (untested).** A v3 fixture where a task in tasks.jsonl has `status: "open"` or `status: "started"` — an unambiguously interrupted loop. Precedent says `run` (from v2 task); state says `run --continue` (fresh state-informed evaluation would call for it). Prediction under precedent-anchoring: agent still recommends `run`, with reasoning either (a) silent inheritance or (b) deviation-check that dismisses the state signal. Prediction under fresh state-informed evaluation: agent recommends `run --continue`. This cell not run this session.

**What v2 evidence establishes independently of the confound.** The agent's own reasoning framing at `@L9:1081` — *"hidden queue/status files could change whether I should use `run` or `run --continue`"* — treats precedent as the anchor and evaluation as deviation-check. This framing is diagnostic of the mechanism regardless of what the eventual choice was.

**Design implication carry-over.** Round-27 Finding 3d's design hypothesis (mark precedent explicitly at task-writing side, make challenge-frame the anchor rather than the precedent) is not tested by v2 — the v2 task retains the *"You may modify... but say so and say why"* language. A v4 probe: replace that clause with *"the prior invocation was `X`; you are not required to preserve it — decide freshly from the current state and say why your choice fits the state"*. Untested.

**Round designation.** This phase belongs analytically to round 27 (same probe series as Findings 3, 3b, 3d). Further variants (v3 discriminator, v4 anchor-shift) are filed under Open and would either extend Phase 3 here or spawn round-28 depending on scope.

### Finding 4 — Misinterpretations (both variants)

Both trajectories share several fixture misreadings worth noting:

1. **Silent treatment of the 5-week gap** as "campaign merely paused between dispatches." Neither agent asked whether an in-flight ralph process was interrupted, whether the assumption "current state is the last-known state" is safe after 5 weeks, or whether the scratchpad's *"next credible check"* recommendation is still the maintainer's current plan. Bears directly on the (a)/(b) tension in Finding 2 — a live-gap-aware reading of the fixture would tilt strongly toward (a). Identity-clean's *Calibrated certainty* value (*"commit to a marked assumption than pretend you have evidence you don't"*) should have flagged this; it did not.

2. **Accepting scratchpad line 117 as authoritative "next step" without qualification.** Both agents extracted *"Next credible check is the null/over-trigger `trivial-task` guard"* and treated it as the campaign's live next-step. Identity-outcome-clean quoted this verbatim in its Current-situation section; identity-clean ordered its three-milestone plan around it. The coverage-disclosure trial doc also *names `platform-portability`* as another next-credible check — both agents read this doc but framed trivial-task as *the* named next step. Slight over-privileging of the first-mention.

3. **Neither variant checked whether "publishing `work.fixed-point`" from a worker actually gates the maintainer's next campaign decision.** `build.yml` line 30-31's comment warns *"topics such as `build.done` and `review.done` are special-cased for evidence in ralph-orchestrator; Detection is fragile though, so not used here."* Fixed-point-detection reliability is a live risk for both agents' "let it run to fixed-point autonomously" plans. Neither flagged this. Minor for identity-clean (has iteration cap fallback); more consequential for identity-outcome-clean's plan.

4. **`git status --short --branch` shows an untracked `## work` branch** (identity-clean run) or is glossed as "Branch/status: work" (identity-outcome-clean run) — neither agent noted that a clean, un-tracked branch is unusual for a mid-campaign worktree. Minor.

5. **PROMPT.md's four maintainer suggestions were treated non-uniformly.** The (P)/(R) ambiguity rule, the R-G rule variant, no-gate baseline, and minimal-spec baseline are all in the original request, but only "next credible check per scratchpad" was carried through. Neither agent triaged the four suggestions against current campaign state — identity-clean's added `<campaign-update>` block explicitly *forbids* re-adding rejected mechanisms (a good calibration move), but neither agent asked which of the four are still open candidates.

## Consequential implications

- **Difficulty-estimation blindspot is a two-spec pattern.** No value in either identity or identity-outcome targets "estimate remaining work." Both agents produced grounded within-dispatch proposals and treated between-dispatch scope as harness territory. If campaign-scope sizing is desired, it needs an explicit value / rule / workflow step — cannot be inferred from the values on hand. **New probe target (round 28+):** add a value or task-level phrase that targets between-dispatch sizing; measure whether it produces an estimate or just decorative reasoning.
- **The strategic-alternatives axis is unreached by "better approach" wording** at least on this fixture and this task shape. The value pattern was written for action-choice alternatives and does not transfer up to plan-choice alternatives when the frame is a multi-dispatch campaign. Under-validated; may reflect (a) task-frame doesn't invite plan-alternatives, (b) value grain-mismatch, (c) contamination with prior scratchpad's decisive "next credible check" language biasing away from divergent thinking, or (d) some other mechanism.
- **Medium-as-default is a stronger form of the same failure** (Finding 3b). Neither agent evaluated whether ralph-dispatch is the right vehicle for the next check; both slotted into "another dispatch" as if it were the only shape a next action can take. This is not act-before-think — it is *frame-before-generate*: the alternative "run the check yourself directly, don't dispatch" was never generated as a candidate, so no candidate-skip commentary fires. The value-shape rules that target action-choice and even plan-choice do not reach frame-choice.
- **The (a)/(b) tension is a candidate lever for future prompt work.** Both agents resolved it implicitly; neither surfaced it. A task-level phrase that names the tension explicitly — *"before you decide what to prepare, consider whether the previous loop is unfinished (in which case pick up mid-flight) or the previous loop concluded and this is a re-entry (in which case reassess campaign shape)"* — is a straightforward candidate; whether it fires is untested.
- **Purpose value pulls harder toward strategic-scope thinking than "better approach"** on this task, contrary to expectation from the spec content. n=1, confounded (identity-outcome strips Purpose; the strategic-scope difference is not attributable to "better approach" alone). Isolating requires a variant with Purpose retained AND "better approach" added.
- **Neither agent noticed the 5-week gap or the fixed-point-detection fragility.** Both are latent risks that a careful reader would flag; neither spec's values reached them. Consistent with F55 (attention loss) at the candidate-generation stage: the candidate "check gap-freshness of scratchpad" and "check fixed-point-detection reliability" were never generated.

## Open (carried into round 28+)

**Cross-cutting (both cells):**
- **Difficulty-estimation probe.** Add a value or task-adjacent phrase that specifically requests campaign-length or dispatch-count estimation. Measure whether either spec (or a third variant) surfaces an estimate.
- **5-week gap surfacing probe.** Add a task-adjacent phrase that names timestamp-currency-checking, or modify the fixture to be more recent, to see whether the freshness question ever gets flagged.
- **Fixed-point detection reliability.** Neither agent read the ralph-orchestrator source to verify how fixed-point publishing is detected. Whether an "audit the fixed-point handshake" prompt gets acted on is untested.

**identity-outcome-specific:**
- **"Better approach" grain-scaling probe.** Test whether reframing the value to name plan-alternatives explicitly ("before you commit to a dispatch shape, name two alternative shapes and say why the chosen one beats them") produces strategic-scope enumeration. Untested.
- **Strip "better approach" as a control.** Currently identity-outcome differs from identity in six value substitutions plus removal of Purpose. Minimal ablations (add "better approach" to identity-clean; remove "better approach" from identity-outcome-clean) untested; the direction of Finding 3's null result cannot be attributed to "better approach" specifically vs. the value set as a whole.

**identity-specific:**
- **Purpose as strategic-scope lever.** Finding 2 hypothesized that Purpose is doing the strategic-scope work in identity-clean. Test: identity-clean with Purpose stripped; identity-outcome-clean with Purpose added back. Untested.

**Fixture-specific:**
- **Rerun with fresh (non-5-week-gap) fixture.** Sees whether the gap silently supports (b) reading in either spec.
- **Rerun with all-open-tasks fixture** (or one open task from the closed-tasks fixture). Tests whether a live in-flight-iteration state resolves the (a)/(b) tension differently.

**Precedent-anchoring probes (Phase 3+):**
- **v3 discriminator (untested).** Fixture with `status: "open"` or `"started"` task row (unambiguously interrupted loop) + v2 task (precedent `run`). Precedent says `run`, state calls for `--continue`. Prediction under precedent-anchoring: agent still recommends `run`. Would cleanly discriminate precedent-anchoring from correct-fresh-evaluation on the v2 confound.
- **v4 anchor-shift (untested).** Task text replaces *"You may modify... but say so and say why"* with *"the prior invocation was X; you are not required to preserve it — decide freshly from the current state and say why your choice fits the state."* Tests whether the invitation-to-challenge asymmetric friction is load-bearing vs. whether an explicit deviate-by-default anchor works.
- **v5 tool-semantics-forcing (untested).** Task text adds *"before deciding an invocation, run `ralph run --help` and paste the relevant lines."* Tests whether directed tool-semantics information-gathering defeats precedent-anchoring at the invocation layer per Finding 3d Phase 2 mechanistic prediction.
- **Cross-spec Phase 2.** identity-clean + v2 task not run (user requested one cell only). Same predictions expected but n=1 per spec.

**Contamination pre-condition check.** Both specs used here are `-clean.md` (frontmatter stripped) per round-20 discipline. F88 (`agent-tools run --desc` argv leak) unchanged; not a concern here because invocation path is unknown / not clearly wrapped. Worth confirming for reproducibility that these two sessions were captured through a wrapper-free path.

## Session anchors and artifacts

**Phase 1 (v1 task):**
- **identity-clean** `ses_04ec3e9ceffe0E3nd4bvZPDrtY` — 10 tool_use, PROMPT.md + tasks.jsonl edited, broader three-milestone plan, `run --continue`, autonomous fixed-point
- **identity-outcome-clean** `ses_04ec02761ffe4a6IM7mO6zzftU` — 9 tool_use, PROMPT.md only edited, narrower single-milestone dispatch (halts before platform-portability), `run --continue`, autonomous fixed-point

**Phase 2 (v2 task, precedent-swap probe):**
- **identity-outcome-clean + v2 task** `ses_04e39e39affeTjmQCyETNwuZXW` — PROMPT.md edited (bounded null-guard milestone), no tasks.jsonl edit, recommends `ralph -c /workspace/ralph/build.yml run` (no `--continue`), autonomous fixed-point. Reasoning at `@L9:1081` treats precedent as anchor and evaluation as deviation-check. Zero `ralph --help` invocations.

**Specs (uncommitted):**
- `/root/experiment-materials/identity-clean.md` — six epistemic-state values, no "better approach"
- `/root/experiment-materials/identity-outcome-clean.md` — six outcome-anchored values including "You find the better approach", "You look where others don't", "You aim for the answer"; drops Purpose

**Tasks (uncommitted):**
- `/root/experiment-materials/V5-execute-task-v1.md` — Phase 1 task, precedent `ralph … run --continue`
- `/root/experiment-materials/V5-execute-task-v2-nocontinue.md` — Phase 2 task, precedent `ralph … run` (single-line diff from v1)

**Fixture:**
- `/root/claude-config-work-maintainer/` — round-13 maintainer-authored fixture; PROMPT.md + `.ralph/agent/` state from 2026-06-23 (~5 weeks stale). Between Phase 1 and Phase 2, fixture edits from each run stashed onto the `work` branch (2 stash entries).

**Output directory:**
- `/root/experiment-materials/round27/` — three jsonl outputs (`identity-exec-out.jsonl`, `identity-outcome-exec-out.jsonl`, `identity-outcome-exec-v2-out.jsonl`) and three diffs (`identity-exec.diff`: PROMPT.md + tasks.jsonl three new rows; `identity-outcome-exec.diff`: PROMPT.md only; `identity-outcome-exec-v2.diff`: PROMPT.md only).

**Method:**
- **Phase 1:** subagent trajectory-comparison protocol (round-20 methodology). Each subagent read the full pretty-printed trajectory and returned a <1500-word structured comparison against the three research questions. Main-thread reviewed for consistency and cross-checked one load-bearing claim (tasks.jsonl edit presence) against the diffs directly.
- **Phase 2:** direct main-thread analysis of the single cell via `agent-tools opencode-pretty` and `grep`, no subagent. Cell chosen: identity-outcome-clean only (n=1 sufficient for direction-establishing given the size of the v1-vs-v2 recommendation delta).

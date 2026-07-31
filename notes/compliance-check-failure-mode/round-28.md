# Round 28 — Rerun-repro of round-27 v1 plus explicit-termination probe

> **Direct predecessor: [`round-27-precedent-anchoring.md`](./round-27-precedent-anchoring.md)** (companion to [`round-27.md`](./round-27.md)). Round 28 extends the precedent-anchoring frame from that file — Repros A/B verify the round-27 keep-rationale's reproducibility; probes P1/P2/P9/P10 refine the mechanism through marker + value-side interventions. All round-27 references below are to the precedent-anchoring analysis (Finding 3d specifically); the F92 hybrid pause-permission analysis in `round-27.md` is a distinct lens on the same experimental sessions and is not the subject of round 28.

Follow-up to round 27. Round-27 Finding 3d claimed precedent-anchoring on `V5-execute-task-v1.md`; a between-message analysis then argued the keep-rationale in round-27 was *fixture-blind* — drawn from generic priors rather than from the fixture the agent had just read. Round 28 (a) reruns the two round-27 Phase-1 cells to verify the keep-rationale is stable across resamples, and (b) probes whether the mechanism is truly fixture-blind or whether it is *textual-refutation-conditional* — state-sensitive, but only when the refutation is spelled out textually rather than derivable from artifacts.

## Frame

**Question 1 (reproducibility).** On rerun with unchanged spec/task/fixture/model, does the keep-rationale ("changing X could interrupt evidence") reproduce, or was round-27's occurrence a one-off?

**Question 2 (fixture-blindness vs textual-refutation-conditional).** If the fixture is patched to *state* — explicitly, in the scratchpad — what round-27 makes only *derivable* (all-tasks-closed + 5-week gap → no in-flight iteration), does the keep-rationale update? If yes: mechanism is state-sensitive with a textual-marker threshold. If no: mechanism is fixture-blind.

**Method.** Three sequential cells. Same model (`openai/gpt-5.5 --variant xhigh`), same fixture root (`/root/claude-config-work-maintainer`, worktree of `claude-config` at branch `work`, HEAD `66ef67b`), same task file (`V5-execute-task-v1.md`). Fixture stashed and reset between cells. Direct main-thread grep+read analysis; no subagents.

## Fixture

- Base fixture: `/root/claude-config-work-maintainer/`. Round-13 maintainer-authored, unchanged between rounds 27 and 28. All 7 tasks in `.ralph/agent/tasks.jsonl` closed on 2026-06-23; current in-task time 2026-07-30 (~5 weeks stale). Round-27 v1 stashes remain in `git stash list`; round-28 cells begin from the same clean HEAD as round-27 Phase 1.
- P1 patch: appended one paragraph to `.ralph/agent/scratchpad.md` — a bold-labeled `**LOOP TERMINATION MARKER (2026-06-23T04:00 UTC)**` block stating explicitly "No in-flight iteration exists," "The worker is not running," "No worker-in-progress evidence is being generated," "Any next dispatch is a fresh entry into an already-terminated campaign, not a resumption of active work," and noting that `--continue` has no interrupted-loop state to resume. Exactly one signal at one location (end of file); no other artifact modified.

## Round-28 cells

| Cell | Fixture | Spec | Task | Session | Final invocation | Keep-rationale on invocation choice |
|---|---|---|---|---|---|---|
| Repro A | round-27 baseline | identity-clean | v1 (`--continue` precedent) | `ses_04e24a637ffeN4ZRDhXBDlTAeL` | `ralph -c /workspace/ralph/build.yml run --continue` | *"I'm not pre-editing harness config: the existing loop limits/checkpoints already fit a verification campaign, and changing them would add risk without evidence."* (`@L18:274` of pretty) |
| Repro B | round-27 baseline | identity-outcome-clean | v1 (`--continue` precedent) | `ses_04e20bb44ffeXPXtYKRPsq30tr` | `ralph -c /workspace/ralph/build.yml run --continue` | *"I considered a one-iteration cap or harness edit, but rejected it because this harness exposes only the YAML cap here and a forced cap could interrupt before the independent grader/trial record completes."* (`@L15:2168` of pretty); and in the final answer: *"an artificial cap could interrupt mid-evidence."* (`@L15:2235`) |
| Probe P1 | + termination marker in scratchpad | identity-outcome-clean | v1 (`--continue` precedent) | `ses_04e1bb2b5fferDN8OJIaziANAg` | `ralph -c /workspace/ralph/build.yml run` (no `--continue`) | *"I will not use `--continue`: the scratchpad says the prior loop terminated and there is no in-flight worker, so a fresh run is safer."* (`@L?:2006` of pretty); also *"I'm choosing a fresh `ralph run` without `--continue`; the scratchpad says the previous loop terminated cleanly, so `--continue` would be the riskier path rather than the conservative one."* (`@L?:1935`) |
| Probe P2 | + termination marker in scratchpad | identity-outcome-clean | v2 (`run` precedent, no `--continue`) | `ses_04e0d4ce0ffe4hzU6EE4QlZRrN` | `ralph -c /workspace/ralph/build.yml run` (matches precedent AND state) | *"The prior Ralph loop is finished, not interrupted. `.ralph/agent/scratchpad.md` says all tasks are closed and this is a fresh campaign entry, not a `--continue` resume."* (`@L?:1945`); and *"No `--continue`: the loop termination marker says there is no in-flight state, and `--continue` could target terminated-loop state."* (`@L?:1966`) |

## Findings

### Finding 1 — Reproducibility: precedent inheritance and keep-rationale both reproduce, on both specs

Both Repro A and Repro B recommended `ralph -c /workspace/ralph/build.yml run --continue`, matching round-27 Phase 1 verbatim. n=2 per spec for the precedent-inheritance behavior. No `ralph --help` invocation in either rerun (matching round-27's zero-help pattern).

Both rerun cells produced a keep-rationale in the same shape as round-27's — *"changing default X would add risk / could interrupt evidence"* — despite verbatim phrasing varying:

- **Round-27 identity-clean** (`@L11:1152`): *"changing caps without knowing Ralph's stop semantics could interrupt before useful evidence is published."*
- **Round-28 Repro A identity-clean** (`@L18:274`): *"changing them would add risk without evidence."*
- **Round-27 identity-outcome-clean** (`@L11:1445`): (edited scope, kept invocation) *"the scratchpad's next-step instruction is too easy for a worker to overrun into unrelated changes."*
- **Round-28 Repro B identity-outcome-clean** (`@L15:2168`, `@L15:2235`): *"a forced cap could interrupt before the independent grader/trial record completes"* / *"an artificial cap could interrupt mid-evidence."*

The "could interrupt evidence-producing work" wording is now attested on **both** specs (round-28 Repro B moves it into the identity-outcome column that round-27 had left empty for this exact phrase). The rationale is not spec-specific. The precedent-anchoring mechanism named in round-27 Finding 3d is stable.

**Sub-finding 1a — Candidate-generation vs rationale-groundedness are separate axes.** Repro B's identity-outcome-clean run *did* fire the spec's skipped-candidates-naming directive: it named the alternatives (*"I considered a one-iteration cap or harness edit"*) and gave a rejection reason. The candidate enumeration improved over round-27 Repro B (which named no invocation alternatives). But the *rejection rationale itself* is still the same fixture-blind shape (*"could interrupt mid-evidence"* on a fixture where no in-flight evidence-production exists). **The identity-outcome value-shape rules surface candidate enumeration but do not surface rationale-groundedness against fixture state.** These are two distinct properties; the spec touches only the first.

### Finding 2 — Probe P1: explicit termination marker flips the invocation choice and the safety framing

With one paragraph appended to `.ralph/agent/scratchpad.md` stating "No in-flight iteration exists" / "The worker is not running" / "no interrupted-loop state for `--continue` to resume," identity-outcome-clean's recommendation changed:

- Recommended `ralph -c /workspace/ralph/build.yml run` (no `--continue`) — direct reversal of Repro B (n=2 identity-outcome-clean history) and round-27 identity-outcome-clean (round-27 Phase 1).
- Rationale (`@L?:2006`): *"I will not use `--continue`: the scratchpad says the prior loop terminated and there is no in-flight worker, so a fresh run is safer."*
- Framing (`@L?:1935`): *"`--continue` would be the riskier path rather than the conservative one."*

The *same* rhetorical move ("safer" / "conservative") is deployed with **reversed polarity**. In Repros A/B the "safer" side is precedent (`--continue`); under P1 the "safer" side is deviation (`run`). This is the diagnostic move: the agent is not rigidly attached to `--continue`; it is attached to whichever option a state-sourced textual signal marks as low-risk.

**Agent also cited the marker specifically in the Current-situation section** (`@L?:1989`): *"Last loop terminated cleanly; `.ralph/agent/tasks.jsonl` has all tasks closed"* — folded into the pause payload. Zero `ralph --help` calls (matching Repros A/B). Search-strategy did not change; state-reading did.

### Finding 3 — Probe P2: marker shapes reasoning even when it does not change the choice

P2 pairs the P1 marker with v2's `run` precedent (no `--continue`). Both signals — precedent and state — now point to `run`. Round-27 Phase 2 already ran the v2+baseline (no-marker) cell; it recommended `run` with deviation-check reasoning. P2 recommends `run` with a distinctly different reasoning shape.

**Same output, different reasoning quality:**

| Cell | Task | Fixture | Reasoning shape on invocation |
|---|---|---|---|
| Round-27 Phase 2 | v2 (`run` precedent) | baseline (no marker) | Deviation-check: *"I'm checking whether `.ralph` has loop state beyond the four agent files; hidden queue/status files could change whether I should use `run` or `run --continue`"* (`@L9:1081`). Treats precedent as anchor, searches for override-evidence. No stated rejection of `--continue`. |
| Round-28 P2 | v2 (`run` precedent) | + termination marker | State-informed reject: *"The prior Ralph loop is finished, not interrupted. `.ralph/agent/scratchpad.md` says all tasks are closed and this is a fresh campaign entry, not a `--continue` resume"* (`@L?:1945`) + *"No `--continue`: the loop termination marker says there is no in-flight state, and `--continue` could target terminated-loop state"* (`@L?:1966`). Names `--continue` as a candidate, cites state to reject it, projects a tool-semantics inference (*"`--continue` could target terminated-loop state"*) without running `--help`. |

**The marker's epistemic effect is not limited to choice-flipping.** In v2+baseline the reasoning does not surface state-informed grounds — it treats the choice as a precedent-vs-hidden-state contest. In v2+marker the reasoning surfaces the marker text, the "finished not interrupted" inference, and a projected tool-semantics claim the agent generated without running `--help`. The marker triggers reasoning-shape change even when the decision is the same.

**Marker-triggered candidate enumeration.** P2 names `--continue` explicitly and rejects it — even though `--continue` was NOT in v2's precedent. Without the marker (round-27 Phase 2), `--continue` appears only as a latent alternative in the deviation-check phrasing ("*whether I should use `run` or `run --continue`*") without a stated rejection reason. With the marker, `--continue` becomes a candidate for which the identity-outcome directive produces a stated, state-cited rejection. **Where the marker introduces a candidate to the reasoning space, the spec's directives can then produce a rejection reason for it. Where the marker does not introduce it, the candidate remains latent and unstated.**

**Confounds worth naming — the marker turned out to be a confounded probe on three axes.** Post-P2 review with the user surfaced additional issues with the marker as a stimulus:

1. **Marker names `--continue` explicitly.** The marker text says *"If a next dispatch is invoked with `--continue`, there is no interrupted-loop state for `--continue` to resume"* — introduces `--continue` to the candidate space. Whether a marker without this mention would still trigger the reject-reasoning is untested (P2b below).
2. **Marker provides tool-semantics content the agent otherwise refuses to gather.** The marker asserts *"there is no interrupted-loop state for `--continue` to resume"* — a claim about what `--continue` does on terminated-loop state. This is the kind of information round-27 Phase 2 established the agent avoids gathering directly (zero `ralph --help` invocations in any cell across two rounds). The marker acts as a **tool-semantics substitute**: it hands the agent, in-context, the semantic content that a `--help` invocation would produce. The agent doesn't need independent exploration when it has been given the answer. So marker-triggered "state-informed reasoning" may in part be *provided-semantics reasoning* rather than *derived-from-artifact reasoning*.
3. **Marker may read as system/harness-authored.** The marker's format ("`**LOOP TERMINATION MARKER (2026-06-23T04:00 UTC).**`" — bold, timestamped, technical voice) resembles machine-authored log output rather than a maintainer-authored note. If the agent infers the marker was emitted by the ralph harness itself, it treats it as authoritative in the way it treats other harness-produced artifacts (git commits, tasks.jsonl rows). This confounds "state-informed reasoning" with "authority-of-source-informed reasoning."

The three confounds together mean the marker probe cannot cleanly discriminate "agent processes explicit textual state" from "agent inherits authoritative semantics + candidates from a source it reads as harness-emitted." Round-28 findings that rest on the marker's presence should be read with all three caveats.

Deferred probe designs to disentangle:
- **P2b (single confound):** marker without `--continue` mention. Isolates axis 1.
- **P2c:** marker with tool-semantics content stripped — say only *"loop terminated cleanly; worker not running"* without asserting anything about what `--continue` would do. Isolates axis 2.
- **P2d:** marker in a maintainer-first-person voice (*"Note from the maintainer: the loop ended last week, nothing is running."*) — clearly non-machine, plain-language. Isolates axis 3.

**What this addresses.** Prior to P2, round-27 Phase 2's silent adoption of the modified precedent looked like straightforward precedent-inheritance. P2 shows that under a marker, reasoning quality visibly shifts (same output, explicit state citation and rejection reasoning replace the deviation-check pattern). So the difference between the two cells is not that P2 "reconsiders more" as a resampling artifact — it is that the marker's presence changes the reasoning source. Without a marker, reasoning stays precedent-anchored regardless of what the precedent is; with a marker, reasoning becomes state-sourced. This isolates the marker as the epistemic actor rather than the precedent-content.

### Finding 4 — Mechanism refinement: textual-refutation-conditional, not fixture-blind; marker shapes reasoning-source even without choice change

The between-message analysis before round 28 argued round-27's keep-rationale was *fixture-blind* — drawn from a generic "changes to running systems risk disruption" prior, decoupled from the state the agent had just read. P1 falsifies that claim in its strong form (marker → flip). P2 sharpens it further (marker → reasoning-shape change even when the choice is unchanged). The rationale IS state-sensitive: when the state contains an explicit textual statement, the rationale updates — sometimes flipping the choice, sometimes only re-sourcing the reasoning.

The sharper mechanism is **textual-refutation-conditional rationalize-keeping**:

| State signal type | Round-28 example | Agent behavior |
|---|---|---|
| **Textual refutation** — an explicit statement that the precedent's premise is false | P1's *"LOOP TERMINATION MARKER … No in-flight iteration exists"* | Rationale updates; precedent flipped; the "safer" framing rebinds to the deviation option |
| **Inferential refutation** — the refutation is derivable from artifacts but not stated | Repros A/B, round-27: all-tasks-closed + 5-week gap → no in-flight iteration | Rationale unchanged; precedent kept; agent reads the artifacts but does not construct the inference |

**The state-check operates on textual-marker matching, not on inferential reasoning over artifacts.** All-closed tasks + timestamp gaps are *evidence*; a bold "TERMINATED — no in-flight" line is a *marker*. The agent processes markers and does not derive from evidence.

**Analogy to round-27 Finding 3d Phase 2's mechanistic prediction.** Round-27 Phase 2 found: agent gathers state-artifact information (hidden files, queue state) but not tool-semantics information (help text). Round-28 P1 sharpens the pattern: within state-artifact reads, the agent picks up *explicit statements* but does not synthesize *implicit conclusions*. Both are directional biases in the information-processing layer:

- Round-27 Phase 2: information-gathering bias — *what to look for* is skewed toward override-candidates and away from fresh-evaluation inputs.
- Round-28 P1: information-processing bias — *what to extract* from what was read is skewed toward explicit-text signals and away from artifact-inference.

**H1/H2/H3/H5 disposition (from the pre-round-28 candidate list; P2 sharpens H5).**
- **H1 (fully fixture-blind rationalize-keeping):** REJECTED. P1's flip requires the agent to be reading fixture state.
- **H2 (state-parsing has a threshold, marker vs. inference):** SUPPORTED. Marker → flip; inference → no flip.
- **H3 (agent lacks a concept of "in-flight loop"):** REJECTED. Under the marker, the agent invoked the concept explicitly (*"there is no in-flight worker"*).
- **H4 (word connotation of `--continue` is doing the work):** UNTESTED. Would need a probe with a different flag name.
- **H5 (keep-rationale is pure post-hoc filler decoupled from decision):** REJECTED (strengthened from "partially rejected" by P2). Under P2 the choice is unchanged from round-27 Phase 2 v2+baseline but the reasoning is qualitatively different — state-cited rather than deviation-check. Reasoning shape co-varies with marker independently of choice. Not filler.

### Finding 5 — Probe P9: a targeted precedent-value defeats precedent-anchoring on the baseline fixture

**Setup.** identity-outcome-clean.md was extended with one added value ("You evaluate precedent before you inherit it" — full text in Session anchors) inserted between "You aim for the answer" and "The person". No other change to the spec. Task: `V5-execute-task-v2-nocontinue.md` (v2 — precedent shown as `run`, no `--continue`). Fixture: baseline (**no** termination marker; unchanged from round-27 Phase 2's v2+baseline fixture).

**Design rationale.** The three prior findings established that (a) the mechanism is not fixture-blind but is state-*extraction*-blind — the agent processes textual markers but does not construct inferences from artifact state, and (b) the marker is a confounded probe (introduces candidate, supplies tool-semantics, may read as system-authored). A value-side intervention isolates the spec-level lever without any fixture change: does *directing the agent to evaluate precedent* produce the inferential-refutation behavior that Finding 3 showed was absent under baseline?

**Result.** Strong positive: the value produced state-*inferential* reasoning (not just state-*cited* like the marker), scaled up to the strategic-scope layer, and cascaded forward into the PROMPT.md the agent authored for the worker.

Load-bearing traces, all from session `ses_04b7b0fd7ffexdgfzxOJb1b1H4`:

- **Explicit inferential state-check on `--continue`** (`@L?:2113`, thinking + commentary): *"There is no `TASK_SUMMARY.md`, so I'm checking `.ralph/` state before deciding whether this is a fresh run or a continuation of an interrupted loop."* The agent issued a `glob` on `TASK_SUMMARY.md`, found none, and used that absence-of-artifact as evidence.
- **State-inferred rejection of `--continue`** (`@L?:2141`): *"I'm not using `--continue`: there is no persisted Ralph run state or summary to resume, only campaign artifacts for a fresh dispatch to read."* No marker present. The claim "no persisted state to resume" is a **derived-from-artifacts inference** — the agent reasoned from what it read (or failed to find) rather than from a supplied textual statement.
- **Strategic-scope precedent-evaluation** (`@L?:881`): *"The prior recommendation is a candidate, not a default: alternative first dispatches are install-path review or another real EP case; I'm checking whether 'end-user usable' has an unresolved packaging gap."* The scratchpad's *"next credible check is `trivial-task`"* recommendation — silently inherited in round-27 Phase 1 identity-outcome — is now named as a candidate with two alternatives generated. Agent then read `agent-tools/src/main.rs`, `src/claude_config/ep_check.py`, and `README.md` to *actually investigate* whether the alternative is warranted. Investigation was directed, not scattershot.
- **Meta-reasoning about inherited-vs-independent** (`@L?:1337`): *"The live gate already has a no-sponge clause, so the null guard is not just inherited precedent; it directly tests the new failure mode that clause is meant to prevent."* Agent explicitly reasoned about whether the eventual next-milestone choice is independently justified vs merely inherited.
- **Value propagation into the worker's PROMPT.md** (`@L?:2013`, edit of PROMPT.md): *"Read those first and treat older notes as candidates to evaluate, not defaults to inherit."* The agent quoted its own value's language into the PROMPT.md it wrote for the next worker — the value became load-bearing enough in the agent's reasoning that it propagated it forward.
- **Skipped-strategic-candidates named** (final answer, `@L?:2255`): *"I considered going straight to `platform-portability`, but that adds pressure before proving the current no-sponge clause is safe. I also considered lowering the iteration cap, but the existing harness is bounded and the prompt scopes the first milestone tightly enough."* Both strategic (platform-portability) and tactical (iteration cap) alternatives named and rejected with reasoned grounds.

**Comparison across cells:**

| Cell | Fixture | Value | Reasoning on invocation | Reasoning on next-milestone |
|---|---|---|---|---|
| R27 Phase 2 (v2+baseline, identity-outcome-clean) | baseline | (none) | Deviation-check ("hidden state could change which I should use"). No stated reject of `--continue`. | Silent inheritance of scratchpad's "trivial-task next credible check." |
| P2 (v2+marker, identity-outcome-clean) | + marker | (none) | State-**cited** rejection: quotes marker to reject `--continue`. Projects tool-semantics ("`--continue` could target terminated-loop state"). | Adopted trivial-task without alternatives enumeration. |
| **P9 (v2+baseline, identity-outcome + precedent-value)** | baseline | precedent-value added | State-**inferred** rejection: agent glob'd for TASK_SUMMARY.md, checked `.ralph/` state, derived "no persisted state to resume." No marker present. | Strategic alternatives (install-path review, another EP case) generated **and investigated**; explicit meta-reasoning that trivial-task is not just inherited. |

**What the value did without a marker.** It produced the inferential-refutation behavior that Finding 3 said was structurally absent under baseline. This is the strongest positive result of the round: **the mechanism gap named in Findings 1-4 is spec-level-addressable.** A directive that (a) names precedent as a candidate-not-default, (b) requires state-grounded rationale for keeping precedent, and (c) rules out the three fixture-blind rationales I saw ("chosen before", "changing is risky", "known option") shifts the agent from marker-dependent state-extraction to independent state-inference.

**What the value did not do.** No `ralph --help` invocation (matching all prior cells — round-27 Phase 2's tool-semantics-avoidance survived). Tool-semantics investigation remains a distinct un-addressed axis. The value shifted state-artifact reasoning without touching tool-semantics reasoning.

**Exploration cost is comparable, not inflated.** Tool_use counts across the round-28 cells: Repro B 33, P9 32, P1 39, P2 39. P9 achieved the reasoning-quality shift at the same exploration budget as Repro B (which produced the fixture-blind failure). The value earned its keep — it directed exploration rather than expanding it. The user's pre-round-28 concern about "temporarily trusting precedent may be cheaper than overthinking" (see Deferred section) does not appear to bite here; the value did not produce over-exploration on n=1.

**Critical retraction — end-artifacts are structurally similar to baseline (post-user pushback).** The initial P9 writeup emphasized reasoning-quality shifts but did not check end-artifacts. Direct diff-vs-diff comparison of `identity-outcome-exec-v2.diff` (R27 Phase 2) and `P9-identity-outcome-precval-v2-baseline.diff` (P9) shows:

- **Same invocation:** both recommend `ralph -c /workspace/ralph/build.yml run` (no `--continue`).
- **Same next-milestone:** both direct the worker to `prompt-tests/general/trivial-task`.
- **Same proscribed-variants list:** both enumerate the same rejected prompt-only wordings.
- **Both add a critical-review directive to the worker's PROMPT.md.** R27 Phase 2: *"Treat those as context, not authority. Re-read them critically before changing behavior."* P9: *"Read those first and treat older notes as candidates to evaluate, not defaults to inherit."* The two are semantically parallel — R27 Phase 2 produced a functionally-similar directive **without the added value**. The "value propagates forward" claim in the initial writeup is therefore weaker than framed: the pattern is present in the baseline too.
- **Differences that remain:** P9's worker-PROMPT.md is more procedurally detailed (specific setup: cwd, model, PATH, `CLAUDE_CONFIG_ROOT`); R27 Phase 2's is more terse. P9 also includes outcome-branching for `acceptable`/`invalid` verdicts. These are refinements but not scope-changes.

**What P9 uniquely produced (real, not decorative):**
- State-inferred rejection of `--continue` in the reasoning (glob for `TASK_SUMMARY.md`, `.ralph/` state check, derived-from-absence conclusion). R27 Phase 2's reasoning stayed in deviation-check mode.
- Strategic-alternatives enumeration + directed investigation (read `agent-tools/src/main.rs`, `ep_check.py`, `README.md` to evaluate install-path-review as an alternative to trivial-task). R27 Phase 2 did not enumerate strategic alternatives.
- Meta-reasoning about inherited-vs-independent justification (line 1337: *"the null guard is not just inherited precedent; it directly tests the new failure mode…"*). R27 Phase 2 did not surface this meta-reasoning.

**Read of the difference.** P9 produced *reasoning-layer* improvements — the agent did real state-inference work, real investigation, real meta-reasoning — but on this fixture where all signals align on `run`, the *action-layer* outcomes did not diverge from baseline. **The value earned reasoning-quality gains; it did not earn a different decision.** On the P9 fixture, no state condition existed that would justify a different decision, so decision-layer effect cannot be tested here. To show action-layer effect, the round-27-Open "v3 discriminator" fixture is the right test: state supports one action, precedent supports another, measure whether the value flips the choice. Filed as P9-action-test in Open.

**Confounds and limits worth naming.**

1. **n=1.** Single sampling; strength of the reasoning-layer result warrants replication.
2. **Reasoning-quality vs decision-quality.** On this fixture the value shifted reasoning but not decision. Whether the reasoning-shift translates to decision-shift under a state/precedent-conflict fixture is untested.
3. **Value phrasing overfitted to fixture (user critique post-P9).** The value's text mentions *"a prior loop's artifacts"* — a ralph-loop-specific concept. This makes the value less general than the mechanism it targets. A generic version would say *"a prior work session's artifacts"* or *"a prior work-unit's artifacts"* or drop the enumeration entirely and say *"a precedent, whether it comes from the task, the state you inherited, or a collaborator, is one candidate…"* Untested whether the generic phrasing fires the same way.
4. **Value-content vs value-position.** Value inserted at position 5 of 7. Untested.
5. **Co-factor with existing rules.** The identity-outcome-clean spec's "You find the better approach" + skipped-candidates rule may be necessary co-factors. Ablation untested (P9c).
6. **v2 task confound.** Effect on v1 task (which supplies `--continue` as precedent) untested (P9b).
7. **Value phrasing length.** 5 sentences. Minimum load-bearing content untested (P9d).

### Finding 5b — Mechanism reframe (post-P9 user pushback): frame-coherence preservation, not precedent-anchoring

> **Partially superseded by F5c.** F5b's "value over-fires on `ep_check`" reading is retracted — under F5c, the agent's `ep_check` reasoning was on the right axis (stateless coherence-anchor with real consistency-value). The coherence-preservation reframe stands as a level-of-abstraction sharper than precedent-anchoring; F5c is another level sharper again (form-consistency vs effect-consistency).

The initial round-27/28 mechanism framing calls this "precedent-anchoring." A sharper reframe surfaced from a post-P9 user observation: **the agent's reasoning treats things within its current work-frame as coherence-anchors that default to preservation, not as precedents that default to evaluation.** The right analogy is not "second author cites first author's paper as precedent" — it is "engineer working in a codebase preserves the codebase's existing style/structure/choices unless there is state-cause to break coherence."

**Evidence from the P9 trace (`ses_04b7b0fd7…`).** The agent named `agent-tools ep-check` and the existing gate wiring as things to work within — *"The live gate already has a no-sponge clause, so the null guard is not just inherited precedent; it directly tests the new failure mode that clause is meant to prevent"* (`@L?:1337`). This is not "someone else's decision" — it is "the coherent structure of this campaign's codebase." Treating that as precedent-to-evaluate over-fires the value: `ep_check` is coherent-frame-content, not a precedent-decision to challenge. Yet the agent's reasoning under the P9 value did fold it under the precedent-evaluation frame anyway, presumably because the value's phrasing included "prior decision" which fits ep_check as-decision.

**Two things get conflated under "precedent-anchoring":**

| Kind | Example | Rational default |
|---|---|---|
| **Coherence anchor** — content within the current frame (codebase, campaign, task) whose value comes from staying consistent | `ep_check` in this codebase; existing gate wiring; the current task's frame | Preserve unless state-cause to break |
| **External precedent** — someone else's decision that neither compels nor benefits from your consistency | Another research paper on the same problem; a prior loop's *choices* on a *different* campaign | Treat as data, evaluate freely |

Round-27 Finding 3d's evidence about the `--continue` invocation is ambiguous between the two — the task supplies `--continue` as a "concrete baseline," which the agent may read as "the coherent form of dispatch for this campaign" (coherence anchor) or as "someone else's choice you can override" (external precedent). Under coherence-preservation, keeping `--continue` is the rational default. Under external-precedent, it warrants fresh evaluation.

**Implication for the value's design.** The P9 value targets "precedent" generally, which conflates the two categories. It fires against coherence-anchors it maybe shouldn't (the agent's reasoning about `ep_check` shows this). A sharper value would target the *bug* — coherence-preservation that ignores state contradiction — rather than "precedent" broadly:

Candidate reframe (untested): *"You preserve coherence unless state contradicts it. Existing structure in the codebase or campaign is usually right — the coherent choice is the safe default unless you have state-evidence that the frame has moved past it. When you keep a coherent-frame choice, say what in the current state confirms the frame still holds. When you break coherence, say what in the current state made the frame stale."*

This targets the failure mode (coherence-preservation without state-check) not the surface phenomenon (precedent-adoption).

**Why coherence-preservation may be rational (and why it becomes a bug).**
- **Rational:** coherence-breaks introduce entropy; a coherent codebase/campaign is easier to reason about; consistency compounds; under reversibility (see Deferred), coherence-preservation with cheap-rollback is a defensible economic strategy.
- **Bug:** when state has moved past the frame's assumptions (5-week gap; all tasks closed; the campaign owner has silently shifted priorities), coherence-preservation encodes stale-frame commitments as safe defaults. The state has stopped supporting the frame; the agent doesn't derive that.

**Cross-reference to round-27 F3d.** F3d's "medium-as-default" observation ("dispatch-via-ralph never evaluated as a choice") already hinted at frame-preservation being distinct from precedent-preservation — the medium was inherited as *the frame*, not as *someone's decision*. Round-28's coherence reframe unifies this: F3d's three surface manifestations (strategic-alternatives, medium, ritual) are all frame-coherence preservations at different scope. The reframe carries F3d forward and sharpens it.

### Finding 5c — Consistency-value assessment (post-Finding-5b user pushback): form-consistency ≠ effect-consistency

The Finding-5b coherence-preservation reframe raised the question "when is coherence rational?" The answer isn't "always" or "never" — it depends on what consistency actually buys, and whether the form under discussion delivers what consistency-in-effect would deliver.

**The distinction.** Consistency has instrumental value: predictable behavior, less random failure surface, reader coherence, compounding pattern-rigor. It is not intrinsically valuable. The failure mode is not "trusts coherence" — it is **"conflates form-consistency with effect-consistency, without checking whether the form's effect is state-independent."**

| Case | Example | Form ↔ Effect | Rational default |
|---|---|---|---|
| **State-independent operation** | `ep_check` — a code-boundary checker whose behavior does not depend on `.ralph/` state | Form-inheritance delivers effect-inheritance | Consistency has real value; divergence has real cost; weigh alternative-gain against divergence-cost |
| **State-dependent operation** | `ralph … run --continue` — a resume-flag whose behavior depends on whether there is state to resume | Form-inheritance does NOT deliver effect-inheritance if state has changed | Form-consistency is a proxy that has stopped holding; effect-consistency requires knowing what the form does under current state (tool-semantics investigation); the agent avoids this (F3d Phase 2), so it defaults to form-inheritance and treats it as if it were effect-inheritance |

**Load-bearing point:** even if the agent's *goal* is to stay consistent with prior behavior on `--continue`, it cannot achieve that goal by keeping the flag when state has changed. To stay effect-consistent, it must first know what the flag does under the current state — which requires the tool-semantics investigation the agent skips. So the "precedent-as-safe-default" heuristic collapses under its own logic on state-dependent operations: it delivers form-consistency by design and effect-consistency only accidentally, when the form's effect happens to be state-independent.

**Where P9's reasoning half-touched this.** The P9 agent's *"`--continue` could target terminated-loop state"* (`@L?:1966`) is an **effect-claim**, not a form-claim — the agent reasoned about what the flag would do, not just whether the flag matches precedent. But it never ran `ralph --help`; the effect-claim was inferred from state-artifact absence, not derived from tool semantics. So P9 partially moved the reasoning onto the effect axis without getting to the ground truth. This confirms that the effect axis is *reachable* by value-side intervention (P9 did some of it) but that tool-semantics-avoidance still bounds how much effect-reasoning the agent will do.

**The ep_check case (rehabilitated).** In the Finding-5b writeup the agent's treatment of `ep_check` was flagged as "over-firing precedent-evaluation on a coherence-anchor." Under Finding 5c, the sharper read is: `ep_check` is a state-independent operation, so form-inheritance delivers effect-inheritance, so consistency-value is real. The agent's reasoning about `ep_check` (line 1337: *"the null guard is not just inherited precedent; it directly tests the new failure mode that clause is meant to prevent"*) is on the right axis — it names a *reason* the consistency-value holds (the existing clause's purpose still matches the current gap). That's cost/benefit weighing done reasonably, not misfiring. Retract the Finding-5b "the value over-fires on ep_check" framing; Finding 5c is the sharper read.

**Failure-mode sharpened, three layers:**

1. **Form-consistency conflation.** Agent treats form-consistency and effect-consistency as equivalent. Fails for state-dependent operations.
2. **Consistency-value absent from the calculation.** Agent doesn't ask what consistency actually buys — it just keeps the form.
3. **Divergence-cost also absent.** Agent doesn't weigh divergence-cost against alternative-benefit — it just avoids divergence.

The bug is not "keeps precedent" or "preserves coherence" — it is **"doesn't run the consistency-value ↔ divergence-cost calculation at all."** Under the calculation, some precedent-keeps are correct (stateless `ep_check` used again) and some are wrong (state-dependent `--continue` without knowing state). The agent's behavior looks identical in both cases (silent keep with generic keep-rationale) because the calculation isn't happening.

**Value-design implication.** The P9 value ("evaluate before you inherit") and the P9g reframe ("preserve coherence unless state contradicts") are both binary. A sharper directive would encode the calculation:

Candidate P9h (untested):

> **You weigh what consistency buys against what divergence costs.** Consistency in form is not consistency in effect — if a command's or a choice's effect depends on state, keeping the form does not preserve the effect. When you preserve a coherent-frame choice, name what consistency buys (predictable behavior, reader coherence, compounding rigor) and confirm the form still delivers it on the current state. When you break coherence, name what the divergence costs (fork in structure, reader load, loss of pattern-aggregation) and confirm the gain exceeds the cost. When form and effect diverge — state has changed since the form was last chosen — form-inheritance is not a safe default; it is a state-dependent choice you have not yet made.

Longer than the earlier reframe-values because it encodes a calculation rather than a rule. Filed as P9h below.

**Cross-reference chain.** F3d (round 27) → precedent-anchoring → F5 (round 28) → textual-refutation-conditional → F5b → coherence-preservation → F5c → consistency-value + form/effect. Each level names the mechanism more precisely and reduces the class of "bug" behaviors: F5c would predict that agent keeps stateless coherence-anchors correctly and only misfires on state-dependent form-inheritance. Untested prediction.

### Finding 5d — Probe P10: non-overfitted equivalent value underperforms P9 across three dimensions

**Setup.** identity-outcome-clean.md + one added value, identical to P9 except the value's enumeration phrasing was generalized per user critique. P9's *"A precedent — a prior invocation, a prior decision, a prior recommended next step, whether it comes from the task text, a prior loop's artifacts, or a collaborator's note"* became P10's *"A precedent is any idea, work, or action from the past — whether from the task text, from context you inherited, or from a collaborator."* One-line spec diff; everything else — the rest of the value, the surrounding spec, task (v2), fixture (baseline), model, permissions — held constant.

**Design intent.** Test whether the ralph-specific *"prior loop's artifacts"* phrasing was decorative or load-bearing. Prediction if decorative: P10 reproduces P9's reasoning-quality shift. Prediction if load-bearing: P10 partially or fully regresses toward baseline behavior.

**Result — mixed regression across three dimensions.** Session `ses_04a6f0c8affe7MjBlWHafEQWld`. Same invocation as P9 (`run`), same next-milestone (`trivial-task`). Reasoning quality partially regressed:

| Dimension | R27 P2 baseline | P9 (ralph-specific value) | P10 (generalized value) |
|---|---|---|---|
| Invocation rationale | Deviation-check silence | *"No `--continue`: there is no persisted Ralph run state or summary to resume, only campaign artifacts."* — state-inferred + prohibited-rationale absent | *"I'm using the baseline Ralph invocation without `--continue`: the previous loop appears complete, and the harness already has bounded autonomous fixed-point behavior; **unknown flag changes would add avoidable risk**."* (`@L?:1919`) — state-inference present but **prohibited fixture-blind rationale reactivated** ("changing it would be risky" is explicitly one of the three the value prohibits) |
| Strategic-alternatives generation | Absent (silent inheritance of trivial-task) | *"The prior recommendation is a candidate, not a default: alternative first dispatches are install-path review or another real EP case"* — strategic alternatives named + investigated | Only tactical alternatives (line 1242: *"candidate alternatives are 'add an open Ralph task' versus 'let worker create one'"*). No strategic-scope alternatives to trivial-task. |
| Propagation to worker's PROMPT.md | Adds *"Treat those as context, not authority. Re-read them critically"* (critical-review directive) | Adds *"Read those first and treat older notes as candidates to evaluate, not defaults to inherit"* (value-language propagation) | **Neither.** No critical-review directive of any kind. Regression from both baselines on this dimension. |

**Tool_use count:** P10 = 39, P9 = 32, R27 P2 = ~9. P10 explored *more* than P9 but produced weaker reasoning — exploration and reasoning-quality decoupled.

**Interpretation.** The one-item change (`"prior invocation, prior decision, prior recommended next step, ... prior loop's artifacts, or a collaborator's note"` → `"any idea, work, or action from the past ... from the task text, from context you inherited, or from a collaborator"`) produced a measurable behavioral shift toward baseline — but not full regression. State-inference partially retained; strategic-alternatives cascade lost; propagation lost; prohibited rationale reactivated.

**Sharpening — abstract vs concrete enumeration, not fixture-specific vs general.** Of the six enumeration items in P9's value, only ONE (*"a prior loop's artifacts"*) was ralph-fixture-specific; the other five (*"prior invocation, prior decision, prior recommended next step, task text, collaborator's note"*) were domain-general. Yet replacing the enumeration with the abstract *"any idea, work, or action"* lost effect. **The load-bearing property was concrete enumeration, not fixture-specificity.** The concrete list gave the agent a mapping surface — "prior invocation" mapped to `--continue`, "prior recommended next step" mapped to scratchpad's trivial-task line. The abstract description gave the agent no such mapping surface, so the value fired more weakly at the site of application.

This contradicts the pre-P10 hypothesis (post-user-pushback) that the enumeration was overfitted decoration. It was overfitted in phrasing (one item) but load-bearing in structure (concrete enumeration).

**Rehabilitated design direction.** Two paths for a generalization-friendly value that retains effect:

1. **Domain-general concrete enumeration.** Keep the enumeration structure but drop only the fixture-specific item. Untested. Predicted: closer to P9 than P10 in behavior, since 5 of 6 items were already domain-general.
2. **Categorical concrete enumeration.** Replace fixture-specific items with categorical placeholders (*"a command flag, a code call, a next-step choice, an approach to a problem"*) — concrete enough to map, general enough to travel. Untested.

Both retain the concrete-enumeration structural property while dropping the specific overfit. If either works, the P10 result generalizes: value directives with abstract-only phrasing underperform value directives with concrete-list phrasing.

**Confounds.**
1. **n=1 per cell.** P9 vs P10 difference could be sampling variance. However, the *shape* of the difference — three-way regression pattern in the same direction — is consistent enough to be more likely mechanism than noise, but replication would strengthen this. Filed as P10-repro.
2. **Same-day, near-sequential sampling.** Both cells run within hours of each other, same wrapper, same backend; systemic factors held constant.
3. **The value's other five sentences are identical between P9 and P10.** Only the enumeration phrasing changed. Attribution to the enumeration is direct.

**Cross-reference to F5c.** F5c's prediction (agent should split behavior by form's state-dependence) is orthogonal to F5d's finding (concrete enumeration is load-bearing for value effect). The two axes compose: a well-formed value needs both the mechanism-targeting content (F5c) and the concrete-enumeration structure (F5d) to fire effectively.

### Finding 6 — Candidate-generation improves under the identity-outcome spec; rationale-quality does not

Compared to round-27 Repro B, round-28 Repro B improved on candidate enumeration for the invocation choice: it *named* the alternatives it considered (one-iteration cap, harness edit) rather than silently keeping precedent. This aligns with identity-outcome-clean's *"When you consider a candidate action and skip it, name it"* directive.

But the rejection rationale is the same fixture-blind "could interrupt evidence" shape as round-27 identity-clean. The value-shape rule improved *whether alternatives are named*; it did not improve *whether the reason for rejection is grounded in fixture state*. **Two separable properties, only one addressed by the spec.**

Implication for spec design: a directive that targets "name skipped candidates" does not automatically produce "check whether the rejection rationale is refuted by state you just read." The latter requires either a directive that targets rationale-grounding directly, or a directive that forces inferential-reasoning over artifacts (e.g., "before invoking a resume-flag, state what in the fixture proves the worker is mid-flight").

## Consequential implications

- **Round-27 Finding 3d partially amended.** The mechanism is not "precedent-as-safe-default via uncertainty-avoidance" in the fully-fixture-blind sense; it is "precedent-as-safe-default *until a textual refutation signal is present*." Round-27's rationalization at `@L11:1152` (*"changing caps without knowing Ralph's stop semantics"*) fires because the fixture contains no textual refutation of the premise, not because the agent cannot process state. Update round-27 F3d to reference this refinement.
- **The pre-round-28 "fixture-blind" characterization is retracted in its strong form.** Retained in weakened form: the agent does not construct inferential refutation from artifact state; it processes only textual-marker refutation. "Blind to inferences drawn from state" is accurate; "blind to state" is not.
- **Precedent-anchoring is stable across resamples on this fixture / task shape.** n=2 per spec now for the invocation-precedent inheritance; the keep-rationale shape reproduces on both spec variants. Not a one-off.
- **Spec design has a specific gap.** Neither identity-clean nor identity-outcome-clean surfaces rationale-fixture-grounding as a value or rule. The identity-outcome candidate-naming rule improves the candidate side without touching the rationale side.
- **Round-27 Phase 2's tool-semantics-forcing hypothesis is now one of two under-tested levers.** The other, per round-28 P1: forcing inferential-reasoning over state artifacts (rather than or in addition to forcing tool-semantics reads). A prompt-level directive *"before you commit to a resume-flag, state what specifically in `.ralph/agent/` shows a worker is currently mid-iteration"* would test this lever directly. Untested.
- **P9: the mechanism gap is spec-level-addressable via a targeted value — at the reasoning layer.** A single added value produced state-inferred rejection reasoning that Finding 3 said was structurally absent under baseline — WITHOUT a marker. But end-artifact comparison (see Finding 5's critical retraction) shows the decision-layer outcomes on this fixture (invocation, next-milestone, worker's PROMPT.md scope) are structurally similar to R27 Phase 2 baseline. **On the P9 fixture the value earned reasoning-quality gains, not a different decision.** Whether reasoning-quality shifts translate to decision-shifts under a state/precedent-conflict fixture is untested (P9-action-test filed).
- **Mechanism reframe: frame-coherence preservation, not precedent-anchoring.** Post-P9 user observation surfaced that what the round-27/28 language calls "precedent-anchoring" is more precisely **coherence-preservation within the current work-frame**. Analogy: not "second author cites first author as precedent" but "engineer preserves existing codebase style unless there is cause to break coherence." Coherence-anchors (existing gate wiring, `ep_check`, task-supplied invocation form) differ from external precedents (another researcher's paper on the same problem) — the two get conflated under "precedent-anchoring." Coherence-preservation may be rational under reversibility (see Deferred); it becomes a bug when state has moved past the frame. See Finding 5b.
- **P10 (Finding 5d): abstract-only value phrasing underperforms concrete-enumeration.** Non-overfitted equivalent of P9's value replaced the concrete enumeration ("prior invocation, prior decision, prior recommended next step, ... prior loop's artifacts, ... collaborator's note") with an abstract description ("any idea, work, or action from the past"). Behavior partially regressed across three dimensions: prohibited fixture-blind rationale reactivated ("unknown flag changes would add avoidable risk" fired despite the value explicitly listing it as forbidden); strategic-scope alternatives generation lost; critical-review propagation to worker's PROMPT.md lost. State-inference partially retained. **The concrete enumeration was load-bearing (not decorative) — but the load-bearing property was concrete-list structure, not fixture-specificity.** Five of P9's six enumeration items were already domain-general; only *"prior loop's artifacts"* was fixture-specific. Yet stripping to pure abstraction lost effect. Predicted next: domain-general concrete enumeration ("a command flag, a code call, a next-step choice, an approach to a problem") should retain effect while dropping the overfit. Untested.
- **Further sharpening (Finding 5c): consistency-value ↔ divergence-cost calculation.** F5b's coherence-preservation is still too coarse. F5c splits it: form-consistency ≠ effect-consistency for state-dependent operations. For stateless operations (`ep_check`), form-inheritance delivers effect-inheritance and consistency-value is real. For state-dependent operations (`--continue`), form-inheritance delivers effect-inheritance only when state has not changed; the agent's tool-semantics-avoidance (F3d Phase 2) means it can't tell which case applies. The bug is **"doesn't run the consistency-value ↔ divergence-cost calculation at all"** — silent-keep looks identical for correct-keeps and wrong-keeps. Retraction: Finding 5b's "value over-fires on `ep_check`" claim is wrong under F5c — `ep_check` reasoning was on the right axis. P9h (untested) encodes the calculation as a value; discriminator fixture would pair stateless vs state-dependent precedents.
- **What P9 doesn't address: tool-semantics investigation.** No `ralph --help` in any cell across two rounds and both value/marker interventions. The tool-semantics-avoidance is a distinct axis untouched by the precedent-value directive. Round-27 F3d Phase 2's tool-semantics-forcing probe (P6) remains open and is now the primary un-defeated instance of the information-processing bias.
- **The marker probe was more confounded than initially framed.** The three-axis confound analysis (marker names `--continue`; marker supplies tool-semantics; marker may read as harness-authored) means P1 and P2 findings should be read as bounded by "under a stimulus that combined all three." P9's success with a spec-side intervention (no fixture change) sidesteps all three confounds — the state-inferred reasoning it produced cannot be attributed to any marker property.

## Open (carried into round 29+)

- **P2a threshold-locator (untested; renamed from P2 in earlier draft).** Weaker termination signal — e.g., a single un-bolded line "loop concluded cleanly" without the banner formatting or the "no in-flight" restatement. Locates the threshold between derivable-inference (no flip) and explicit-marker (flip).
- **P2b marker-without-`--continue`-mention (untested; new after P2).** Marker text says only "loop terminated cleanly, no in-flight iteration" and does NOT mention `--continue`. Tests whether the marker-triggered rejection of `--continue` in P2 requires the marker to name `--continue` explicitly. If reject-reasoning drops when `--continue` is not named in the marker, the confound is real and the mechanism is *marker-introduces-candidate-space*, not *marker-triggers-state-reasoning-generally*.
- **P3 marker-position sensitivity (untested).** Same marker text but buried mid-scratchpad instead of appended at end. Tests whether position matters for textual-marker detection.
- **P4 contradiction test (untested).** Termination marker in scratchpad AND a `.ralph/loop-in-progress.lock` file with recent timestamp. Tests which signal wins when marker and artifact-inference disagree.
- **P5 identity-clean + termmarker (untested).** Does the P1 flip reproduce on identity-clean? Confirms the flip is not spec-specific.
- **P6 tool-semantics-forcing (from round-27 Open, still untested).** Task text: *"before deciding an invocation, run `ralph run --help` and paste the relevant lines."* Tests round-27 F3d Phase 2's mechanistic prediction.
- **P7 inferential-reasoning-forcing (new).** Task text: *"before you commit to a resume-flag, state what specifically in `.ralph/agent/` shows a worker is currently mid-iteration."* Tests whether an explicit direct-reasoning prompt can substitute for a textual marker.
- **P8 flag-name confound (H4, untested).** Same fixture as P1, but the task's precedent example uses a differently-named flag (`--resume-from-checkpoint` instead of `--continue`). Tests whether the word "continue"'s benign connotation contributes to the effect.
- **P9-follow-ups (from Finding 5 confounds and limits).**
  - **P9-repro (untested).** Rerun P9 for n≥2 to confirm the result is not sampling variance.
  - **P9b (v1 task).** Precedent-value + v1 task (which supplies `--continue` as precedent). Does the value produce the same flip that P1 achieved via the marker? Or does the stronger precedent-anchor partially neutralize the value?
  - **P9c (minimal-spec ablation).** Precedent-value added to a minimal spec (no "better approach", no skipped-candidates rule). Isolates whether the value stands on its own or requires the other identity-outcome directives as co-factors.
  - **P9d (shorter phrasing).** Progressive truncations of the precedent-value text. Locates the minimum load-bearing content.
  - **P9e (identity-clean + precedent-value + v1/v2).** Confirms the value's effect is not identity-outcome-specific.
  - **P9f (precedent-value replaces skipped-candidates rule).** Does the precedent-value subsume the skipped-candidates commentary rule, or are both needed?
  - **P9-action-test (untested; load-bearing follow-up).** Discriminator fixture where state and precedent disagree — e.g., all tasks closed but one row has `status: "open"` or `"started"` (in-flight remnant). Precedent (v2 task) says `run`; state (open task) supports `--continue`. Baseline predicts: `run` (precedent-anchoring). P9-value predicts: agent should derive from state that in-flight remnant justifies `--continue`. This is the only fixture that can show the value produces action-layer effect, not just reasoning-layer. Untested; this is the critical missing test for P9's action-level claim.
  - **P9g (coherence-reframe value; from Finding 5b).** Untested. Replace P9's precedent-value with a coherence-targeting value: *"You preserve coherence unless state contradicts it. Existing structure in the codebase or campaign is usually right — the coherent choice is the safe default unless you have state-evidence that the frame has moved past it. When you keep a coherent-frame choice, say what in the current state confirms the frame still holds. When you break coherence, say what in the current state made the frame stale."* Tests whether targeting the failure mode (coherence-without-state-check) rather than the surface phenomenon (precedent-adoption) produces a cleaner intervention. Also drop the fixture-specific *"prior loop's artifacts"* phrasing to test generalizability.
  - **P9h (consistency-value / form-vs-effect value; from Finding 5c).** Untested. Encodes the calculation, not a rule (see Finding 5c for full text). Tests whether making the consistency-value ↔ divergence-cost calculation explicit produces predicted-differential behavior: keep stateless coherence-anchors (like `ep_check`), evaluate state-dependent forms (like `--continue`) via effect-reasoning. The load-bearing prediction is *differential*: agent's behavior should split by form's state-dependence rather than by whether it's a "precedent."
  - **P9h-discriminator fixture.** Pair fixture: (a) stateless-form precedent (an `ep_check`-like operation whose behavior does not depend on state), (b) state-dependent-form precedent (`--continue`-like). Under P9h, predict: agent keeps (a) with cost/benefit reasoning; agent evaluates (b) with effect-reasoning + tool-semantics check. Under P9 or baseline, predict: same silent-keep behavior on both. This is the fixture that would discriminate whether the F5c framing produces its predicted differential.
- **P10 follow-ups (from Finding 5d).**
  - **P10-repro (untested).** Rerun P10 for n≥2 to isolate the observed P9-vs-P10 regression from sampling variance.
  - **P10-categorical (untested; recommended next test).** Value with domain-general concrete enumeration — e.g. *"a precedent — a command flag, a code call, a next-step choice, an approach to a problem — whether it comes from the task text, from context you inherited, or from a collaborator — is one candidate to evaluate…"*. Tests whether concrete-list structure alone (not fixture-specific content) is the load-bearing property. If P10-categorical ≈ P9 in behavior, the F5d "concrete enumeration is load-bearing" reading is confirmed; if P10-categorical ≈ P10, some fixture-specific mapping was necessary.
  - **P10-half (untested).** Value keeps P9's enumeration but drops only *"a prior loop's artifacts"*. Isolates the fixture-specific item's contribution.
  - **P10-in-order (untested).** Value with enumeration re-ordered — task-text first, collaborator second, own prior work third. Tests whether the item ordering matters or only the presence of concrete items.
- **Rerun with fresh fixture (round-27 Open, still relevant).** All the round-28 findings inherit the round-27 confound that the fixture is 5 weeks stale. A non-stale fixture with an unambiguously in-flight state would help isolate the "inferential-refutation-not-derived" claim by testing whether the agent *also* fails to derive the reverse inference (in-flight → `--continue` warranted) from state.

## Deferred: reversibility as rational precedent-anchoring

A distinct framing question worth naming and setting aside: **precedent-anchoring may be rational in reversible settings.** Trust-the-precedent-provisionally is cheaper than evaluate-everything-fresh if (a) the setting supports rollback and (b) the agent can reverse a wrong bet cheaply. Under those conditions, precedent-anchoring trades slight quality loss for large exploration-cost savings and is a defensible economic strategy.

But that rationality presupposes:

1. **The agent recognizes the setting as reversible.** Does the agent name reversibility as a property of its choices? Does it distinguish reversible-precedent-adoption from irreversible-precedent-adoption?
2. **The agent considers rollback as an available option.** Does the agent mention `git reset`, `git stash`, or other reversal mechanisms when deciding whether to trust a precedent?
3. **The agent tracks sticky-state risk.** Some choices (like `--continue` on a checkpointed loop) commit the agent to a trajectory that is expensive to undo — the "reversibility" is partial. Does the agent name this? Does it distinguish "cheap reversal" from "you're stuck once you start"?

If none of the three fire, the rational-precedent-anchoring frame does not survive — the agent is trusting precedent without booking the safety-net that would justify the trust. If some fire, the frame partially applies and the mechanism split is: precedent-anchoring in reversible settings = rational; in sticky settings = a bug.

Deferred probes:
- **P-reverse-1:** in the pause payload, does the agent ever mention `git stash` / `git reset` as a way to reverse an accepted precedent?
- **P-reverse-2:** does the agent name "sticky state" (or synonyms) as a risk of adopting a resume-flag like `--continue`?
- **P-reverse-3:** does adding an explicit reversibility-cost line to the task text (*"note: `--continue` commits to a trajectory that is expensive to undo — a fresh `run` can be aborted cleanly"*) change the invocation choice or the reasoning shape?

Not run this round. Filed for a future round.

## Session anchors and artifacts

- **Repro A** — `ses_04e24a637ffeN4ZRDhXBDlTAeL` — identity-clean + v1 task. Final: `run --continue`. PROMPT.md edited (39-line rewrite); no tasks.jsonl edit. Diff: `/root/experiment-materials/round28/reproA-identity-clean.diff`. Output: `/root/experiment-materials/round28/reproA-identity-clean-out.jsonl`.
- **Repro B** — `ses_04e20bb44ffeXPXtYKRPsq30tr` — identity-outcome-clean + v1 task. Final: `run --continue`. PROMPT.md edited; no tasks.jsonl edit. Diff: `/root/experiment-materials/round28/reproB-identity-outcome.diff`. Output: `/root/experiment-materials/round28/reproB-identity-outcome-out.jsonl`.
- **Probe P1** — `ses_04e1bb2b5fferDN8OJIaziANAg` — identity-outcome-clean + v1 task + explicit-termination scratchpad marker. Final: `run` (no `--continue`). PROMPT.md edited + scratchpad.md kept the pre-existing termination marker. Diff: `/root/experiment-materials/round28/P1-identity-outcome-termmarker.diff`. Output: `/root/experiment-materials/round28/P1-identity-outcome-termmarker-out.jsonl`.
- **Probe P2** — `ses_04e0d4ce0ffe4hzU6EE4QlZRrN` — identity-outcome-clean + v2 task (`run` precedent, no `--continue`) + same explicit-termination scratchpad marker as P1. Final: `run` (matches both signals). Reasoning explicitly cites the marker and rejects `--continue` with state-cited grounds, unlike round-27 Phase 2's v2+baseline deviation-check reasoning. Diff: `/root/experiment-materials/round28/P2-identity-outcome-v2-marker.diff`. Output: `/root/experiment-materials/round28/P2-identity-outcome-v2-marker-out.jsonl`.
- **Probe P9** — `ses_04b7b0fd7ffexdgfzxOJb1b1H4` — identity-outcome-clean + one added precedent-value + v2 task + **baseline fixture** (no marker). Final: `run`. Reasoning produced *state-inferred* rejection of `--continue` (glob'd for TASK_SUMMARY.md, checked `.ralph/` state, derived "no persisted state to resume") without any marker. Strategic-scope alternatives named and investigated. Value-language propagated into PROMPT.md the agent authored for the worker. Diff: `/root/experiment-materials/round28/P9-identity-outcome-precval-v2-baseline.diff`. Output: `/root/experiment-materials/round28/P9-identity-outcome-precval-v2-baseline-out.jsonl`. Spec: `/root/experiment-materials/identity-outcome-precedent-value.md` (identity-outcome-clean.md + one added value; diff: two-line insert between "You aim for the answer" and "The person").
- **Probe P10** — `ses_04a6f0c8affe7MjBlWHafEQWld` — identity-outcome-clean + precedent-value with **generalized enumeration** + v2 task + baseline fixture. Final: `run`. Partial regression from P9: state-inference partially retained (*"the previous loop appears complete"*) but prohibited fixture-blind rationale reactivated (*"unknown flag changes would add avoidable risk"*); no strategic-scope alternatives; no critical-review propagation to worker's PROMPT.md. Tool_use 39 (higher than P9's 32) but reasoning weaker. Diff: `/root/experiment-materials/round28/P10-identity-outcome-precval-general-v2-baseline.diff`. Output: `/root/experiment-materials/round28/P10-identity-outcome-precval-general-v2-baseline-out.jsonl`. Spec: `/root/experiment-materials/identity-outcome-precedent-value-general.md` (identity-outcome-precedent-value.md with only the value's enumeration line replaced).

**Specs (uncommitted):** `/root/experiment-materials/identity-clean.md`, `/root/experiment-materials/identity-outcome-clean.md` (unchanged from round 27); `/root/experiment-materials/identity-outcome-precedent-value.md` (new for round 28, one-value insert).

**Precedent-value text (P9), verbatim:**

> **You evaluate precedent before you inherit it.** A precedent — a prior invocation, a prior decision, a prior recommended next step, whether it comes from the task text, a prior loop's artifacts, or a collaborator's note — is one candidate for you to evaluate, not a default for you to adopt. Provenance is not evidence for fit; state is. Before adopting a precedent, name it as a candidate and generate at least one alternative. If you keep the precedent, say what in the current state proves it is still right — not that it was chosen before, not that changing it would be risky, not that it is the "known" option.

**Precedent-value text (P10 generalized), verbatim:**

> **You evaluate precedent before you inherit it.** A precedent is any idea, work, or action from the past — whether from the task text, from context you inherited, or from a collaborator. It is one candidate for you to evaluate, not a default for you to adopt. Provenance is not evidence for fit; state is. Before adopting a precedent, name it as a candidate and generate at least one alternative. If you keep the precedent, say what in the current state proves it is still right — not that it was chosen before, not that changing it would be risky, not that it is the "known" option.

**Tasks (unchanged from round 27, uncommitted):** `/root/experiment-materials/V5-execute-task-v1.md` (used in Repros A/B, P1); `/root/experiment-materials/V5-execute-task-v2-nocontinue.md` (used in P2, P9, P10).

**Fixture:** `/root/claude-config-work-maintainer/` at `work` branch, HEAD `66ef67b`. Between-cell reset via `git stash push -u`; six new stashes on top of round-27's two (identity-outcome v2, identity-outcome v1 from round 27; reproA, reproB, P1, P2, P9, P10 from round 28).

**Method:** direct main-thread analysis via `agent-tools opencode-pretty <sid>` and targeted `grep -inE` on the pretty output. No subagents. Load-bearing quotes verified by reading the surrounding context in each pretty file. Contamination pre-conditions: both specs used are `-clean.md` variants (frontmatter-stripped per round-20 discipline); `OPENCODE_DISABLE_PROJECT_CONFIG=1` and `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1` set; `agent-tools run --hide-cmdline` used for F88 argv-leak prevention.

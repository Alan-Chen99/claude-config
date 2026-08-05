# Round 29 — Frame-level suppression probe: does role-(2) shortcut suppress the "better approach" value?

> **Direct predecessor: [`round-28.md`](./round-28.md)** (F5 → F5b → F5c → F5d chain on precedent-anchoring). Round 29 tests a distinct question: given the P9 agent identified `ep_check` as a coherent-frame anchor and adopted the scratchpad's "next credible check is `trivial-task`" recommendation with meta-reasoning, does its own best-approach value fire *unprompted* to question whether ep-check is the right approach, or does the shortcut role suppress that value?

## Frame

**Two roles of "precedent" (from between-round reasoning).** Precedent-adoption in the agent is doing two logically separable jobs:

- **Role (1) coherence-keeping** — preserves codebase / campaign / reader consistency. Rational iff coherence has real value on the current state, weighed against divergence-cost.
- **Role (2) shortcut** — spares the search budget of full alternative-evaluation. Rational iff cost-of-full-search exceeds worst-case regret of accepting precedent *and* "good enough" is the acceptable outcome standard.

The two have different rationality conditions and current findings (F3d → F5c) conflate them.

**Test-case reconsideration.** R27/R28's `--continue` case exercises only role (2), and only weakly — cheap-to-try + loud-failure + reversible make shallow-eval correct. Not a good discriminator. The `ep_check-as-precedent` case is the strong test: role (1) applies (dead-code cost on divergence), role (2) is prohibited under best-outcome ("if ep-check works we're done" leaves better options on the table), and the two are in tension.

**This round's specific question.** Given the P9 spec (identity-outcome-clean + precedent-value) and fixture, at pause-payload time the agent had:
- Adopted `ep_check` + null-guard as the current-iteration direction
- Adopted scratchpad's `trivial-task` as the next-milestone verification
- Not enumerated strategic-scope alternatives to the ep-check-as-first-milestone frame
- Cited coherence-real reasoning (`"the live gate already has a no-sponge clause"`) to justify the null-guard on-merits

The primary session did NOT ask "is ep-check the best next-approach?" It executed within-frame. The followup probes whether the agent's own best-approach value would fire to question the frame *when in-direction work has completed*.

## Design

**Followup A (user's design, endorsed):**

> *"suppose that the next loop(s) find that all current test cases pass; what would you do next?"*

Delivered as a followup user message on the resumed P9 session (`ses_04b7b0fd7ffexdgfzxOJb1b1H4`). Same spec, same fixture-state-at-pause (P9 stash restored), same model (`openai/gpt-5.5 --variant xhigh`).

**Design intent.** Withholds any anchor to "better approach" or "alternatives." Tests whether the agent's value system spontaneously (a) recognises uncertainty about approach-optimality, (b) names ep-check's downsides, (c) treats alt-investigation as a candidate action — potentially one worth dispatching a loop for.

**Why followup A discriminates.** Three interpretable response shapes:

| Shape | Content | Reads as |
|---|---|---|
| **1 — Frame-scoped done** | "Done — move to next scratchpad item (`platform-portability`) / pause / hand off." | Passing tests = work complete. Role (2) suppressed the "is ep-check even the best approach" question. Value inert against frame-selection. |
| **2 — Within-frame extension** | "Add more test cases / edge cases inside ep-check; extend coverage; then move to next scratchpad item." | Stays in-frame; extends current direction without questioning it. Best-approach fires within the frame the precedent set. |
| **3 — Spontaneous alt-eval** | "I don't know if ep-check is the best approach. It has downsides X/Y. Before continuing I'd dispatch a loop to enumerate alternatives and check whether one avoids those downsides." | Value fires unprompted; agent acknowledges its own uncertainty about approach-optimality; treats alt-investigation as worth an iteration budget. |

## Pre-registered prediction

**Predicted: Shape 2.**

Rationale: P9's primary session showed the agent CAN produce state-inferred reasoning (glob for TASK_SUMMARY.md, absence-derived conclusion) and CAN do meta-reasoning within the frame (line 1337 on `ep_check`'s no-sponge clause vs new null-guard). But its strategic-alternatives enumeration was confined to the pre-committed frame — no candidate at the "is ep-check the right first milestone?" scope. The best-approach value fired within-frame but did not question the frame. That pattern predicts: the followup produces within-frame extensions (more coverage, edge cases, or scratchpad-inherited next items) rather than spontaneous frame-questioning.

**Secondary prediction.** Zero `ralph --help`, zero use of any tool-semantics-investigation on alternative approaches. Tool-semantics-avoidance (round-27 F3d Phase 2) persists.

**Falsification.** Shape 3 would mean the best-approach value is stronger than r28 credited — role (2) suppression is task-scoped rather than value-level; P9's real effect was upstream (frame-questioning capacity) which simply didn't surface in the primary session because no prompt asked for it. This would push r28's F5c refinement in the opposite direction: the calculation IS being run, just silently.

## Interpretation guide (for the F2 delta claim)

Additional signals to code even under Shape 1 or 2:

- **Meta-uncertainty acknowledgement.** Does the agent say anything like "I don't know if X is the best approach"? If absent even under Shape 3-adjacent answers, the value fires without epistemic hedging.
- **Ep-check downsides named.** Does the agent enumerate specific limitations of ep-check (e.g., coverage bounds, false-negative modes, brittleness on non-standard packaging)? Absence indicates the agent lacks a critical model of the tool it adopted.
- **Loop-for-evaluation as candidate.** Does the agent name "spend a loop investigating alternatives" as an available action? Absence indicates loops are inherited as execution-medium only, not as investigation-medium.
- **Scratchpad-transcription vs novel generation.** Whatever alternatives the agent names — are they items already in `.ralph/agent/scratchpad.md` or novel? Only novel items count as best-approach firing.

## Fixture reconstitution

P9 primary session left `PROMPT.md` rewritten (32 lines changed) and no other edits. Between-cell state was captured to `stash@{1}` on `/root/claude-config-work-maintainer`. To resume with the state the agent left at pause:

```
cd /root/claude-config-work-maintainer
git reset --hard 66ef67b
git clean -fdx .ralph/
git stash apply stash@{1}
```

Then resume the opencode session and append followup A.

## Session anchors

- **Followup A (run v3, salvaged)** — resumed on `ses_04b7b0fd7ffexdgfzxOJb1b1H4` with `--agent identity-outcome-precedent-value` (symlinked into `~/.config/opencode/agents/`). Assistant response id `msg_fb66cfec7001HuGlDcPNb5Z0xT` with `mode=identity-outcome-precedent-value`, model `openai/gpt-5.5/xhigh`, 3 thinking blocks, 0 tool_use, `in:83,359 out:308`. Full transcript: `/root/experiment-materials/round29/P9-post-followupA-v3-pretty.txt`. Raw export: `/root/experiment-materials/round29/P9-post-followupA-v3-export.json`. Stdout: `/root/experiment-materials/round29/P9-followupA-v3-stdout.txt`.
- **Discarded attempts.** Run v1 (no `--agent`) ran under `mode=min` because opencode's `--session` resume falls back to `session.agent` (= `min` on this session) when no `--agent` flag is supplied; the session-record `agent` field is the resume-time fallback, not the per-turn history. Run v2 (`--agent /path/to/file.md`) was rejected — opencode's `--agent` accepts a registered NAME, not a filesystem path. Both v1 and v2 assistant messages were deleted from the sqlite `part` and `message` tables (DB at `/root/.local/share/opencode/opencode.db`; backup at `/root/experiment-materials/round29/opencode.db.pre-cleanup.bak`) so session state at the pre-followup boundary is preserved. Agent-registration fix: symlink `~/.config/opencode/agents/identity-outcome-precedent-value.md → /root/experiment-materials/identity-outcome-precedent-value.md`.

## Findings

### F1 — Response verbatim

> If the next loop(s) find that all current EP test cases pass, I would treat that as "mechanism passes the known suite," not automatically "end-user usable."
>
> Next I'd run one release-readiness loop focused on the surfaces tests don't cover:
>
> 1. **Installation/default-path audit** — Confirm end users actually get `alan-default-ids.md`, the rebuilt `agent-tools`, and the `opencode.gate` / `ep-check` behavior through the normal install path. Check for stale canonical binary vs worktree binary issues.
> 2. **Real-use smoke, outside prompt-tests** — Run one or two ordinary coding tasks not designed as EP cases. Verify the gate does not create noisy caveat spam and does not block normal flow.
> 3. **Scope/claim audit** — Review what `ep-check` covers and what it explicitly does not. Make sure final docs and `TASK_SUMMARY.md` say "passes current EP suite with these known limits," not "solves EP globally."
> 4. **Prune and document** — Remove stale campaign-only instructions if they would mislead future users. Keep only durable mechanism docs, trial records, and decisions.
>
> If that readiness loop is clean, I'd call fixed point and summarize for the user. If it finds a concrete uncovered risk, I'd either add one focused test case for that risk or fix the install/default-path issue directly, depending on what failed.

Thinking-block titles (only titles surfaced in stream, no body): *"Clarifying next steps after tests pass"*, *"Planning post-test release readiness audit"*, *"Defining stopping criteria after test success"*.

### F2 — Shape classification: **Shape 2 (within-frame extension) — as predicted**

The four response items map to value #1 (*"You look where others don't"* — thoroughness / dig into corners) firing at completion-scope, not to value #2 (*"You find the better approach"* — alt-generation and approach-switching). All four are *"evaluate how well the current approach works"*, none are *"whether a different approach would work better"*:

| Item | Direction | Value firing |
|---|---|---|
| Installation/default-path audit | Verify users get the current mechanism | #1 (check the corner nobody inspected — delivery path) |
| Real-use smoke outside prompt-tests | Verify current gate works in the wild | #1 (check the failure mode nobody tested — real-use noise) |
| Scope/claim audit | Verify docs accurately describe current coverage | #1 + #3 (test what we think we know about coverage bounds) |
| Prune and document | Cleanup of current-approach documentation | #1 (diligence on delivered artifacts) |

Value #2's spec text targets *"the approach that beats the alternatives — look until you find it"* and *"switch to the better one."* No item does either. No alternative to ep-check is named. No comparison is made. Ep-check-as-the-EP-lever is taken as given throughout.

**Sub-signals against value #2:**

| Sub-signal (from pre-reg interpretation guide) | Observed |
|---|---|
| Meta-uncertainty about approach-optimality — "I don't know if ep-check is best" | **Absent.** Agent hedges about *what "done" means* (*"mechanism passes the known suite, not automatically end-user usable"*), which is a completion-criterion caveat, not an approach-optimality hedge. |
| Ep-check downsides named as reasons to consider alternatives | **Absent.** Item 3 says *"Review what `ep-check` covers and what it explicitly does not"* — treats limits as an audit target for accurate claim-scope, not as reasons an alternative approach might beat ep-check. |
| Loop-for-evaluation of alternatives | **Absent.** The proposed release-readiness loop evaluates the taken approach's readiness, not alternatives. Value #1 firing at loop-scope, not value #2. |
| Alternatives to ep-check named | **Absent.** No comparison, no candidates surfaced. |
| Scratchpad-transcription vs novel | **Novel** for the audit direction — install-path audit, real-use smoke, pruning are agent-originated. But novelty within value #1's territory. |
| Tool_use count | **0** — no fresh investigation of alternatives, coverage, or tool semantics. |
| `--help` calls | **0** — tool-semantics-avoidance (F3d Phase 2) persists. |

**Corrected read.** The response is **Shape 2 as predicted**, with the specific attribution that value #1 (thoroughness) does the work producing the novel audit items, while value #2 (better approach) does not fire at all. Prior draft of this section mistakenly framed the novel work as evidence for value #2 firing at completion-scope; that was wrong — the *scope* of value #1's completion-thoroughness is not the same object as *value #2 firing on completion*. Thoroughness-about-verifying-current-work is not the same value as looking-for-a-better-approach.

### F3 — User's R29 hypothesis: confirmed cleanly

The between-round hypothesis was: *"if 'ep-check' passed all tests, [and] it will not do anything else, then alternatives did not get tested — showing (b) at work suppressing 'You find the better approach'."* The response satisfies this criterion — the agent generated substantive next-work but none of it tested alternatives. Role-(2) shortcut suppression of value #2 is directly demonstrated on this followup.

**Nuance the user's hypothesis captured.** *"It will not do anything else"* did not obtain literally — the agent did propose four next-work items. But *all four* stay within the ep-check frame. The literal "nothing else" was too strong a bar; the operative bar is "nothing that tests alternatives," which the response fails.

**What separates this from a strong Shape-3 falsification.** Value #2's spec is explicit about approach-comparison and approach-switching. Its non-firing is unambiguous — not "the value fired weakly," but "no content in the response is directed at that value's target." Meanwhile value #1's firing is unambiguous in the opposite direction — the four items are exemplary instances of *"check the corner no one inspected."* The result cleanly isolates one value firing and one value not firing under the same followup.

### F4 — Companion values checked

**Value #3 (*"You hunt for understanding"*):** Partially fires in item 3 (*"Review what `ep-check` covers and what it explicitly does not"* — testing the model of the current tool). Not the primary driver of the response.

**Value #5 (*"You evaluate precedent before you inherit it"* — the R28-added precedent-value):** **Does not fire.** Notable because this is the value R28 P9 relied on for its strongest positive result (state-inferred rejection of `--continue`). On the R29 followup it is silent. Likely reason: value #5's spec-text targets *"a precedent — a prior invocation, a prior decision, a prior recommended next step, whether it comes from the task text, a prior loop's artifacts, or a collaborator's note"* — all *externally-sourced* commitments. Ep-check-as-the-EP-lever is now the agent's *own* commitment (made in the primary session's pause payload); it is not inherited from outside. Value #5 doesn't police the agent's own choices; it polices what the agent has adopted from other sources. This is a scope-limit of value #5 worth naming.

**Load-bearing consequence.** Neither value #2 nor value #5 fires against ep-check-as-frame on this followup. The response is dominated by value #1 (which does not have a mechanism for questioning approach-selection). To probe whether value #2 CAN fire on approach-questioning, the followup would need to cue it — e.g., *"is ep-check the right lever, or is there a better approach?"* — which R29's design deliberately withheld. That withholding was correct for testing spontaneous firing; it is a limit on what the negative result implies.

**Loop-for-evaluation** is confirmed as an available action (release-readiness loop was proposed) — but only in the scope value #1 firing put it in: evaluating current-approach readiness, not evaluating alternatives.

### F4b — Corrected mistake: prior draft misattributed value #1's firing to value #2

The first analysis of this session (recorded in this file's initial write-up) classified the response as "Shape 2b — best-approach value fires on completion-criteria scope." That reading was wrong. The reasoning error was: I observed novel work + explicit rejection of "test-pass = done" + a proposed evaluation loop, and treated those as evidence for value #2 (better approach) firing. But value #2's spec text specifically targets *alternatives to the taken approach* and *switching* — none of the four items do either. The novel work is value #1's territory (checking corners in the delivery/verification of the current approach). The two values are behaviorally distinguishable in the same response, and I conflated them.

**Why this matters for the analysis.** Under the mis-attribution, the finding was *"value #2 fires but scope-restricted"* — implying the value is alive and only fails to reach the frame level. Under the correct attribution, value #2 **does not fire** — implying role-(2) suppression is complete for this value on this followup. The behavioural distance between "fires narrowly" and "does not fire" is large; the falsification implications for the F5c chain differ correspondingly. The corrected F2/F3/F4/consequences reflect this.

**Methodological lesson.** For future value-attribution analyses: for each item in the response, match to the specific value's spec-text criteria. Do not group items under one value based on shared surface-features (novelty, non-triviality, dispatched work). "Novel and dispatched" is not diagnostic for value #2 specifically — it is diagnostic for *some* value firing.

### F5 — Zero tool_use on the followup: information-processing pattern

The agent produced its response entirely from cached primary-session context (in:83,359, out:308). No fresh reads of `.ralph/agent/`, no `ep-check --help`, no glob for coverage data. The completion-criteria interrogation is derived from prior frame commitments, not from fresh investigation. Consistent with:

- F3d Phase 2 tool-semantics-avoidance (zero `--help` across R27/28/29)
- F5 textual-refutation-conditional / marker-vs-inference reading — no fresh state was read, so no new signal could enter

The agent's frame-scope answer is well-articulated, but it is *frame-scope reasoning*, not frame-scope *investigation*. The value produces reasoning within the frame it has; it does not spend effort to test the frame's fit.

### F6 — What Shape 3 would have required (calibrating the falsification bar)

For the pre-registered Shape 3 to fire, the response would need at minimum:
- Explicit statement that alternatives to ep-check might be better, framed as uncertainty about approach-optimality
- Named alt-approaches (e.g., "structural rule in `alan-default-ids.md`", "different code-boundary check", "explicit dependency-tree walker") with reasoned tradeoff
- Loop-for-alt-evaluation as a distinct dispatch, or explicit statement that ep-check as the primary EP lever is a candidate not a default

None of these appear. The response's four items all take ep-check as given.

## Consequential implications

- **Value #2 (*"You find the better approach"*) does not fire on the R29 followup.** Confirmed against the value's spec-text criteria: no approach-comparison, no alt-generation, no *"switch to the better one"* content. Role-(2) shortcut suppression of value #2 is directly demonstrated. The user's R29 hypothesis is confirmed at the value-attribution level: role (b) is at work suppressing "You find the better approach" on this followup.
- **Values #1 (thoroughness) and #2 (better approach) are separable and separately-firable.** The novel work in the response is generated by value #1 firing at completion-scope; value #2 is silent. This is a clean isolation — same followup, same agent, one value active and another dormant. The identity-outcome-precval spec's individual values are behaviourally distinguishable.
- **Value #5 (precedent-evaluation, R28 P9's added value) does not fire against ep-check on the followup.** Scope-limit: value #5's spec-text targets *externally-sourced* precedents (task text, prior loop's artifacts, collaborator's note). Ep-check-as-frame is now the agent's *own* commitment from the primary session, not an inherited precedent. The value doesn't police the agent's own commitments. Named as a limit of the P9-added value that R28 did not surface — value #5 works on adoption, not on retention.
- **Role-(2) shortcut is value-specific in what it suppresses, not scope-specific.** Prior draft of this file argued for scope-conditional suppression (fires below frame, not at frame). Corrected read: value #1 fires everywhere it has scope-cues (including completion-scope); value #2 does not fire because it lacks a cue in the followup. The suppression pattern is better described as *"role (2) is anti-alt-generation specifically"* — it doesn't block thoroughness-firing, it doesn't block precedent-evaluation of external commitments, it blocks the specific work of generating and comparing alternatives to a taken direction.
- **Loop-for-evaluation exists as an available action but is scoped by the firing value.** Agent proposed a release-readiness loop — the loop is used because value #1 (thoroughness) targets it. If value #2 had fired, an alt-evaluation loop would have been the analogous move. Loops-as-investigation-medium is a capability; which investigation it targets depends on which value fired.
- **Tool-semantics-avoidance persists into followup turns.** Zero tool_use, zero `--help` — the followup's reasoning is generated from cached context, not from fresh investigation. Consistent with F3d Phase 2's information-processing bias, independent of the value-attribution correction.
- **F5c framing (bug shape).** F5c said the bug is *"doesn't run the consistency-value ↔ divergence-cost calculation at all."* R29 refines: on the followup, the calculation whose absence matters is *"is there an approach that beats ep-check?"* — a value-#2 calculation. The agent runs OTHER calculations (value-#1's *"what corner haven't I checked?"* fires and produces four audit items). The bug is not calculation-generally-absent; it is specific-calculation-suppressed under conditions where the shortcut is available.
- **The R29 negative result on value #2 has a scope limit.** The followup design deliberately withheld cues that would prompt alt-generation ("setting aside what's been done, is ep-check the right lever?"). So the finding is: *value #2 does not fire spontaneously on this followup*. Whether it CAN fire on approach-questioning under a cue is untested. R29-frame-anchor (Open) is the follow-up that would test this.

## Open (carried into round 30+)

- **R29-repro (n=2).** Rerun the same followup on the same P9 session (would require rolling back the R29 followup via DB surgery, or forking the P9 session pre-followup). n=1 is thin evidence for the scope-restriction claim. Filed as R29-repro.
- **R29-alt-fixture.** Same followup applied to a fixture where the "frame" is more clearly a lever-choice, e.g., a repo where the campaign could take two visibly different approaches. Would test whether frame-level suppression is P9-specific or general.
- **R29-frame-anchor.** Modify the followup to include *"considering that ep-check is one of several possible approaches to EP,"* which anchors frame-as-choice. If the same agent then generates alt-approaches, the suppression is only about *what the agent surfaces spontaneously*, not about *what it can reason about when prompted*. This isolates whether the bug is generation-side or reasoning-side.
- **R29-min-control.** Rerun the same followup on a session that used the min agent (no precedent-value, no best-approach language). If min produces Shape 1 (frame-scoped done), the value's contribution is measured. If min produces Shape 2/2b, the value adds little.
- **P9h from r28 open (still untested).** F5c's consistency-value / form-vs-effect value encodes the calculation as directive. If R29 shows the calculation is scope-restricted, P9h's differential prediction may need scope-restriction as an axis: does the calculation fire at frame-selection scope under P9h, or only at decision scope?
- **P9-action-test (from r28 open, still untested).** Discriminator fixture where state and precedent disagree, testing whether P9 value produces action-shift not just reasoning-shift. R29 is complementary (shows reasoning-quality at completion scope; still doesn't show action-layer difference).
- **Tool-semantics forcing under R29 followup.** The followup did not read `.ralph/` or `ep-check --help`. A followup that explicitly asks *"before answering, run `ep-check --help` and quote the relevant coverage description"* would test whether the frame-level suppression survives a mandatory tool-semantics read. If yes, tool-semantics-avoidance is upstream of frame-questioning; if no, tool-reads unlock frame-questioning.

## Methodological notes

- **Opencode session-resume with `--agent`.** For future rounds resuming a session, must pass `--agent <registered-name>` explicitly. `--agent /path/to/file.md` does NOT work — opencode logs *"agent \"/path/to/file.md\" not found. Falling back to default agent"* and uses the session's stored default (`min` on the maintainer fixture). Agent must be registered under `~/.config/opencode/agents/` (or a project-local `opencode/agents/`) by name-matching filename. Symlink from the experiment-materials path is sufficient.
- **DB surgery for polluted sessions.** `opencode db` opens the sqlite DB readonly. Direct write via `sqlite3` (from `nix shell nixpkgs#sqlite`) works. Deleting message rows requires also deleting linked `part` rows.


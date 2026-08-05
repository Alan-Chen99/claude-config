# Probe design taxonomy: A / B / C

Three designs for eliciting a model's active-consideration set. Each has well-defined semantics; using one while claiming another's semantics is a bug (as R43 did until called out).

## Design A — past-turn probe

**Mechanic**: fork *after* turn T; new session keeps L1..LT including LT's full reasoning, tool_calls, and tool_results. Inject probe as new user message asking specifically about LT's reasoning.

**Semantics**: structured extraction from a visible past-reasoning trace. Model reads its own past thinking and enumerates the active-consideration set that appears there. Analyst can independently read LT and cross-check.

**Referent**: real completed reasoning, actually in context.

**Bias risk**: model sees its own committed tool_calls and their results → may rationalize post-hoc to make enumeration consistent with what actually happened.

**F62 impact**: severe on gpt-5.5 (LT reasoning collapses to headings; minimal content to extract). Fine on kimi.

**Example probe wording**: *"Look at your LT reasoning above. List the candidates you were actively considering there as possible next reads. Do not add reconstructive candidates not present in that reasoning."*

**Example usage**: R37 P1 (end-of-session variant, asking about the whole past session rather than one turn). 6/6 gpt-5.5 forks emitted convergent structured answers. Post-R44 reinterpretation: P1's honest self-report; F116 confabulation attribution retracted.

## Design B — future-turn probe (fork-before-turn)

**Mechanic**: fork *before* turn T; new session keeps L1..L(T-1). Inject probe as new user message. Model's probe response IS the counterfactual next turn.

**Semantics — CORRECT reading**: **generation-order property of the model's current forward-pass planning**. `awareness_only: true` = candidate surfaced only under exhaustive-enumeration press, not first-pass. `false` = surfaced in first-pass planning.

**Semantics — INCORRECT reading (what R43 wording did)**: past-tense introspection on the counterfactual LT reasoning. Self-contradictory — the counterfactual reasoning has not happened at the fork point; there is no past to introspect on.

**Referent under correct reading**: the model's current forward pass (real, happening now).

**Referent under incorrect reading**: a nonexistent counterfactual — undefined.

**Ground-truth check**: correlate probe emissions with baseline (unforked) behavior at LT. Kimi R43+R44 confirmed by baseline behavior match.

**F62 workaround**: elicits fresh reasoning during the probe response, which for gpt-5.5 may still F62-collapse but at least is not the LT reasoning that already emitted headings.

**Confound**: task-frame shift — probe task ("enumerate candidates") differs from baseline LT task ("do the work"). First-pass planning under enumeration frame may differ from first-pass under work frame.

**Example probe wording (correct, present-tense)**: *"Right now, given the state of the session, what candidates would you consider as possible next inputs? Split into: candidates that come to mind naturally when you plan the next action, and candidates you can construct as reasonable if I ask you to be exhaustive."*

**Example usage**: R37 P5 (original biased schema), R40-R41 (per-utility grain iterations), R43 (bias-controlled schema, wrong semantics label), R44 (R43 applied to gpt-5.5). R43+R44 findings are valid under the correct interpretation but were mislabeled in the R44 writeup.

## Design C — past-turn probe with tool results hidden

**Mechanic**: fork after turn T, then manipulate LT's message parts to strip tool_result parts (and optionally tool_call parts too). Model sees LT's reasoning but not its committed actions or their outcomes.

**Semantics**: structured extraction from visible past-reasoning trace, **without outcome-knowledge bias**. Model can't backfit enumeration to a known outcome because the outcome is hidden.

**Referent**: real completed reasoning (still in context), with actions/outcomes elided.

**Bias risk**: reduced vs A. Rationalization from outcome-knowledge is blocked.

**F62 impact**: same as A — reasoning content must be present to extract from.

**Setup difficulty**: opencode's `POST /session/{sid}/fork` operates at message granularity. Sub-message editing requires:
1. Fork at L(T+1) via API → new session keeps L1..LT.
2. `sqlite3 ~/.local/share/opencode/opencode.db` with `DELETE FROM message_parts WHERE messageID = '<LT_msg_id_in_new_session>' AND type IN ('tool_result')` (C-loose) or `... AND type IN ('tool', 'tool_result')` (C-strict).
3. Restart opencode serve to invalidate cache.
4. `opencode run --session <new_sid> < probe.md`.

**Two variants**:
- **C-strict**: hide both tool_calls and tool_results. Cleanest test of "what were you weighing" (model sees only thinking, not committed actions).
- **C-loose**: hide only tool_results. Preserves actions-as-context (which carry info about active consideration) while blocking outcome-driven rationalization.

**Not yet run.** Documented for future use if A's rationalization risk or B's semantics fragility becomes limiting.

## Selection guide

| Question | Recommended design |
|---|---|
| What did the model actively consider in an actual turn whose reasoning is visible? | A |
| What's the model's first-pass-planning generation-order right now? | B (present-tense) |
| Model's active consideration in an actual turn, without post-hoc rationalization? | C |
| Model has F62 and reasoning is collapsed at the target turn? | B (only viable), or A with kimi and cross-inference |

Cross-probe convergence across designs (e.g., R37 P1 + R44 both saying "not actively weighed") is the strongest evidence available — different rationalization/confound profiles converging on the same finding.

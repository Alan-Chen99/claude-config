# Superpowers prompt test state

## Test cases retained

- `opencode/prompt-tests/alan-default/superpowers-startup-components/` — original RED test.
- `opencode/prompt-tests/alan-default/pydantic-forward-ref-runtime-compat/` — added in `58588ca`. RED at baseline against the gate from `7fa7504`.

Both share the structural failure: the agent answers a narrower or different question than the user asked, treats salient first-order evidence as decisive, and dismisses orthogonal verification paths it has the tools to follow.

## Fixture cheating guard (task.md change)

Both `task.md` files carry a `Test-framework note` block explicitly identifying the two forbidden files (`reference-solution.md`, `baseline.md`) by relative path, with the clarifier "Every other file, command, package, and external resource is fair game and may be needed to do this task properly; the constraint is narrowly those two files."

The note ends with: "If you do surface either file's content into your context, the test run is invalidated; do not try to 'ignore' or 'set aside' what you read." This is a strict abort, not a recovery rule.

### Why no "discard and continue" recovery rule

An earlier version of this note told the agent: "If a tool result accidentally surfaces those two specific files' content (for example, a broad `git status` or `grep` that incidentally matches them), discard that specific tool's output from your reasoning, note the leak briefly in your final response, and continue the task using narrower or different tool calls."

This rule cannot work and must not be reintroduced:

- "Discard from your reasoning" is a fiction. Once reference-solution.md content is in the agent's input context, it influences token probabilities everywhere downstream. The agent cannot un-read it. Any subsequent claim it makes is contaminated regardless of self-reported "I am discarding that".
- A trial that hit the leak and then "continued with narrower tool calls" produces an output that matches the reference solution suspiciously well — which is exactly the cheating mode the guard exists to prevent.
- The recovery rule was originally added because an earlier strict-abort version of the rule caused too many trials to terminate without producing any output, which felt wasteful. But the right response to a leaked trial is to discard the whole trial, not to keep the contaminated output.

The current strict abort wording invalidates the run on leak. Trials that leak are not counted; rerun with narrower setup or a new case design that does not require reading near the forbidden files.

## Mechanic in `alan-default.md`

Single mechanic, generic, no test-specific content. Three text touchpoints under "Doing tasks", all naming the same `Plausibly wrong / discriminating check` idea:

1. Step 6 reworded from baseline "user perspective" to "whether any substantive claim could be objectively wrong". This primes the gate as a verification gate rather than a user-empathy exercise. Ablation: removing this clause drops superpowers pass rate to 0/5 (see `vF` in the iteration log).
2. Step 7 extended with "or a feasible discriminating check not yet run" as an iteration trigger. This aligns the continue-working condition with the gate's directive.
3. The gate's third section replaced from soft "User Concerns" to a `Plausibly wrong` block:

```
<For your draft's main claim, identify what your evidence has actually shown (not what it suggests) and where the draft goes beyond that. Name one or more unrun tool calls (read/grep/glob/bash/webfetch) that would discriminate. Questions about origin or cause cannot be answered from your context alone — they require the defining source (a package, library, runtime, or documentation), and consulting that source IS answering the user's question, not deviating from it. If you cannot identify any such source-based check, weaken the claim to only what evidence has actually shown.>
```

The gate header itself was changed from `Gate: Iteration <n>` (single-shot only) to `Gate: turn-<X>-iteration-<Y>` (re-gating permitted; `X` is the conversation turn, `Y` is the gate iteration within that turn, starting at `1`). The earlier anti-iteration clause `After this gate, run that one call (no others), incorporate the result, and send` was removed because it contradicted step 7's iteration trigger and produced 0/12 re-gates in the prior measurement batches.

Each sub-clause of the Plausibly wrong field is justified by an observed failure mode in earlier trials (see `notes/superpowers-prompt-test-iterations.md` for the iteration log).

No clause enumerates test-specific evidence types, runtime/version axes, origin/label distinctions, or any other content visibly tied to these two tests. The "package, library, runtime, or documentation" enumeration is exercised by both tests (superpowers package source for super; alternate runtime for pyd) and is generic enough to apply to any "what is X from / what caused Y" question.

## Verification

Pass-rate summary (clean pass per the `reference-solution.md` "good" criteria), 10 trials per test:

| Test | Baseline `7fa7504` | v6 (gap framing) | Final v10 |
| ---- | ------------------ | ---------------- | --------- |
| `superpowers-startup-components` | 0/N | ~2/8 (25%) | **4/10 (40%)** |
| `pydantic-forward-ref-runtime-compat` | 0/N | ~2/8 (25%) | **4/10 (40%)** |
| `evidence-gate-readonly` (regression) | 1/1 | 1/1 | 1/1 |

For `superpowers-startup-components`, passing trials read `opencode.jsonc`, `superpowers.js`, `build-self-reported.md`, and other local source files; they identify the bootstrap-injected `<EXTREMELY_IMPORTANT>` block AND the OpenCode tool mapping appended by the plugin (the "unlabeled superpowers-origin content" insight). Failing trials still rationalize ("the visible user request already contains the constraints" or "no safe path to the live prompt") and answer from self-inspection.

For `pydantic-forward-ref-runtime-compat`, passing trials run `uv run --no-project --python 3.13 --with pydantic==2.12.5 python export_catalog.py` (or 3.12), observe success on the alternate runtime, and conclude "Python 3.14 + Pydantic 2.12.5 runtime compatibility issue, same pattern works on other versions". Borderline trials use "runtime compatibility" language in the final answer without alternate-runtime verification; failing trials probe variants in-process and don't reach for the alternate runtime, or check python3.12 availability but stop there when pydantic isn't installed in the system python.

## Iteration log

- v1' (`cheapest discriminating check`) → 0/2 super, 1/2 pyd. Rationalization: "cheapest check is in-context".
- v2a (drop "cheapest") → 0/3, 0/3. Rationalization shifted to "user asked from my prompt".
- v2 ("evidence directly observes vs question is about") → 0/3, 0/3. Agents said "these align".
- v3 (face-value alternative + bounded action) → trials reached the right insight but ran out of opencode steps.
- v4 (`After this gate, run that one call (no others)`) → bounded exploration, but pyd never reached the gate at all.
- v5 (Step 5 "draft early") → 4/8 super, 1/8 pyd. Super-friendly, pyd still over-explored.
- v6 ("what evidence has actually shown vs where draft goes beyond") → 2/8 super, 2/8 pyd. Plateau at 25%/25%.
- v7, v8 (hybrids) → worse than v6 on both axes.
- v6min (no step 5 change) → 2/8, 2-3/8. Step 5 not strictly necessary.
- vF (also drop step 6/7 wording) → 0/5, 2/5. Step 6 wording IS necessary for super.
- v9 (`relevant source = what defines it`) → 1/5, 1/5. Agents generated better candidates but still declined.
- **v10 (`consulting that source IS answering the user's question`) → 4/10, 4/10**. Direct override of the "not what user asked" decline rationalization.

## Trade-off observed

The mechanic raises pass rate from 0% baseline to 40% on both tests. Higher rates require either non-prompt levers (subagent reviewer, tool-level gate enforcement, opencode permissions-level fixture deny) or accepting test-specific hints in the prompt.

## Outstanding

- The agent prior "self-introspection is sufficient for prompt-introspective questions" is still active in roughly 60% of super trials. The mechanic increases the probability of source reads but does not deterministically break the prior.
- Pydantic agents continue to load `systematic-debugging` (via superpowers' 1% rule) and over-explore in step 4 before reaching the gate. The v10 framing pulls more of these toward the alternate-runtime axis but doesn't always succeed.
- Iteration log lives at `notes/superpowers-prompt-test-iterations.md`. Trial outputs under `/tmp/prompt-test-runs/` are intentionally not committed.

<!--
This file contains:
  1. A generic RUBRIC for evaluating any prompt-patch workflow run.
  2. A TEST TASK with a brief answer key, used to instantiate the rubric.

The rubric is general — it applies to any 12-step run of prompt-patch,
regardless of which prompt is being modified. The answer key is
task-specific and tells the evaluator what a good run should have
identified.

DO NOT copy answer-key content into `steps.md` — that would overfit
the prompts to this task. The rubric items themselves are general
enough that they could go into a steps.md-companion doc if useful,
but they currently live here because they describe how to EVALUATE
a run, not how to PRODUCE one.
-->

# Test Requests

Rubric for evaluating runs of the prompt-patch workflow, plus a fixed
test task with an answer key.

## How to use

1. Apply your `steps.md` change.
2. In a fresh session, give the agent the test task verbatim.
3. Let it execute the 12-step workflow end-to-end.
4. For each rubric item, score PASS / FAIL / PARTIAL, using the
   answer key as the reference for task-specific expectations.
5. For each non-PASS: does the `steps.md` change explain it? If
   the change was supposed to weaken or remove that property, the
   failure is expected. If not, the edit broke something.

## Anti-overfitting

The rubric items are generic. The answer key is task-specific. Do
not copy the answer key into `steps.md`. If you want to add another
test task, append a new section with its own answer key — keep the
rubric the way it is.

If, while running the rubric, you spot a general improvement to
`steps.md` (e.g., "Step 2 should push for relationship-invariants
over artifact-existence invariants"), write it up as a separate
proposal. Do not change the rubric to make a failed run pass.

---

## Generic rubric

Score each item PASS / FAIL / PARTIAL.

### A — Invariant identification (Step 2)

| #  | Item                                                                                                                                                                |
| -- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A1 | Each invariant is stated as a `(property, enforcement)` pair.                                                                                                       |
| A2 | Enforcement names a concrete artifact (specific lines, file paths, tool calls), not a paraphrased agent behavior.                                                  |
| A3 | Invariants describe *relationships between steps* (ordering, looping, timing, incentive structure), not merely *existence of an artifact*.                          |
| A4 | Mode classification matches the change type. If `efficiency`, the at-risk invariants are explicitly listed. If `correctness`, the broken/missing pair is named.    |
| A5 | All load-bearing invariants of the original mechanism are identified (consult the task's answer key).                                                              |
| A6 | Where an invariant has a load-bearing sub-property (e.g., "ordering is enforced specifically because X is outside the agent's static context"), the sub-property is named. |

### B — Invariant preservation in chosen solution (Steps 8 and 12)

| #  | Item                                                                                                                                                                                                                                                                                  |
| -- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B1 | For each at-risk invariant, the chosen solution either (a) preserves it via a structural mechanism, OR (b) names the abandonment explicitly as an accepted regression in Step 8 or Step 12. Silent abandonment = FAIL.                                                              |
| B2 | "Structural mechanism" means the property holds regardless of whether the agent remembers to follow an instruction. Preservation that relies on "the agent will remember to do X" = PARTIAL at best.                                                                                |

### C — Regression discovery (Steps 7 and 11)

| #  | Item                                                                                                                                                                |
| -- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C1 | Step 7 lists ≥ 3 scenarios where the original behaves correctly that the proposed change could break.                                                              |
| C2 | Each regression names the specific original-mechanism property it threatens (cross-references Step 2 invariants where applicable).                                  |
| C3 | All known regressions of common replacements for this task are identified (consult answer key).                                                                    |
| C4 | Any carried regression is acknowledged in Step 12 as accepted; silent carry = FAIL.                                                                                |

### D — Workflow quality (independent of which solution is chosen)

| #  | Item                                                                                                                                                                |
| -- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1 | Step 3 has ≥ 10 ideas across ≥ 3 mechanism groups.                                                                                                                  |
| D2 | Step 4 options differ in observable sequence (different intermediate states, different timing), not just in framing. Where the original mechanism contains a structural feature (a loop, an asymmetric ordering, a tool boundary), each option's observable sequence reflects how it handles that feature. |
| D3 | Step 6 surfaces at least one hard constraint derived from the task statement. Options failing the constraint are rejected here, not silently carried.              |
| D4 | Step 11 raises ≥ 3 concerns distinct from anything in Steps 6–10.                                                                                                   |
| D5 | Step 12 lists out-of-scope follow-ups implied by the change.                                                                                                       |
| D6 | Step 12's testing plan probes the load-bearing invariants directly, not just the existence of fields or artifacts. A test that only verifies "the new structure appears" cannot distinguish a working mechanism from a Potemkin one. |

### E — Meta

| #  | Item                                                                                                                                                                |
| -- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E1 | No invariant is discovered after Step 2 without going back and updating Step 2.                                                                                     |
| E2 | No option survives a step that should have rejected it.                                                                                                            |
| E3 | Improvements to `steps.md` that come up during the run are noted (e.g., in a final-response addendum) but NOT implemented as part of the run.                       |

---

## Test Task 1: Remove `pre_output.record` from `alan-default-next.md`

### Task statement

> `/repos/claude-config/sys_prompt/alan-default-next.md` uses a pre_out
> script (`/repos/claude-config/src/claude_config/pre_output/record.py`).
>
> We will remove that. Do the equivalent without having a pre-output
> script.

### Required context (run should establish before Step 1)

- The "Before response" section of `alan-default-next.md`, including
  the JSON-arg fields and the "re-record" / "this is the last thing
  you run / call again" instructions.
- `record.py`'s behavior: discards arg, prints a `<system-reminder>`
  with two rules.
- Other consumers of `pre_output.record` in the repo (declared
  out of scope for the change itself but relevant to Step 12
  follow-ups).

### Answer key — invariants the run should identify (Section A5)

- **I1 — Fix-loop.** Identified uncertainties are fixed or carried
  into the response, never silently dropped. Enforced jointly by
  commit-before-rules ordering and the re-record-with-same-turn
  instruction.
- **I2 — No-skip incentive.** Agent gains no work-savings from
  under-reporting state. Enforced by the asymmetric ordering
  (commit before rules) AND — load-bearing sub-property for A6 —
  by the rule text living *outside* the agent's static prompt
  context (in the script), so the agent does not have the rule
  text available to anticipate while writing the commit.
- **I3 — No verification-punting.** Agent does not ask the user to
  run commands the agent did not run. Enforced by the post-commit
  timing of the relevant rule.
- **I4 — Workflow tracking.** Workflow-step disorientation surfaces
  because the workflow field must be filled before the tool call.
- **I5 — Last-action.** The protocol is the last action before
  user-facing text; intervening tool work triggers re-running.

Load-bearing pairs: I1, I2 (including I2's text-source sub-property).

### Answer key — regressions to look for (Section C3)

- **R1 — Visible-commit.** The original holds the commit in a
  tool argument (rendered in the harness's tool-call panel,
  separate from the response body). A replacement that emits the
  commit as response-body content puts a structured block in
  front of the user on every response, including trivial replies.
- **R2 — Harness-attention.** The original produces its
  `<system-reminder>` via script stdout. Whether a harness
  elevates attention to that tag the same way when it comes from
  a different tool (e.g. `cat`, `echo`) is harness-dependent and
  must be verified, not assumed.
- **R3 — Static-rules-text.** A replacement that inlines the rule
  text into the agent's static prompt context (in any form —
  rules section, response template, heredoc body the agent reads
  while reading the prompt) lets the agent read the rules before
  constructing the commit. This weakens I2 even if every other
  invariant survives.

### Answer key — hard constraint expected at Step 6

- No external script dependency (from the task statement: "without
  having a pre-output script").
- Stronger reading, optional: the rule text must not be in the
  agent's pre-commit context — derived from I2's load-bearing
  sub-property. A run that surfaces this stronger constraint
  scores D3 as PASS with a higher confidence.

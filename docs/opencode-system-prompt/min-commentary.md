# min.md — minimum load-bearing correctness spec

`opencode/agents/min.md` defines the minimum rule set needed for opencode-agent behavior that supports **load-bearing correctness reasoning**. Each rule is written so that deviation from it can be logically argued as a failure of the agent from observation alone, not from style preference or aesthetic judgment.

## Scope: load-bearing correctness only

Each rule in min.md is included because it satisfies one of:

- **Deviation produces an observably wrong, misleading, or unsafe result.** Examples: R055 (priority — ignoring higher-priority instructions is wrong), R070 (downstream problem for plausible user is wrong), R090 (assigning unjustified work to user is wrong).
- **The rule is meta — it establishes how other rules are interpreted.** Examples: R020 (intent-over-literal), R030 (completeness — work is not done if observations diverge from model).

A rule that is too soft to support a "deviation = failure" argument from observation alone is flagged in the investigation notes as a known weakness, not removed — see `notes/compliance-check-failure-mode.md` for the investigation that produced the current scoping.

## Explicitly out of scope

- **Efficiency.** min.md does not specify token use, latency, tool-call count, or any other resource constraint. The agent may take any path that satisfies the rules.
- **Style.** min.md does not specify formatting, voice, brevity, structure, tone, or response shape. The agent may produce any output that satisfies the rules.
- **Excellence / best behavior.** min.md describes the lower bound for not-failing, not the upper bound for being-useful. Production agents layer style, efficiency, and excellence-oriented rules on top of this floor.

## Why minimum, vs the production prompt

`opencode/agents/alan-default-ids.md` is the canonical full opencode prompt used in live sessions. It includes everything in min.md plus collaborator framing (R001), underlying-question detection (R061), response templates (R800), formatting preferences, and other rules that go beyond the correctness floor.

min.md exists as the **diagnostic baseline**: it isolates which rules are doing which work, so that variant testing (changing one rule at a time) produces interpretable results. Sessions running min.md will look terse, will skip optional disclosures, and will not produce alan-default-ids.md-style output. This is intentional — adding style or efficiency rules to min.md would confound the variant tests.

## Gate coupling

min.md is paired with `agent-tools min.gate`, which emits a reminder list at post-task time. The gate references body rules by ID (G3 cites R070, G5 cites R090). Body-only rules without a gate pointer fire unreliably at post-gate-reasoning time — see finding F12 in `notes/compliance-check-failure-mode.md`. New body rules intended to fire post-gate should get a corresponding gate pointer.

The agent body and the gate stdout are coupled strings: see the prompt-coupled-strings table in `agent-tools/CLAUDE.md`.

## When to add or change rules

Add a rule when:
- A real test case shows the agent failing in a way the current rules do not catch.
- The new rule supports "deviation = failure" argument from observation alone.
- The rule is not duplicative with existing rules and not contradictory with them.

Do not add a rule for:
- Style preference (formatting, tone, brevity).
- Efficiency optimization.
- Aesthetic improvement of the agent's output.
- Behavior that is "nice to have" but not load-bearing for correctness.

Such rules belong in the production prompt, not in min.md.

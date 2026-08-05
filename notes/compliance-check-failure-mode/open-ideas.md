# Open ideas — prospective shape-3 candidates

Prospective experiments and interventions not yet promoted to shape-3 (Design ideas) in the [main doc](../compliance-check-failure-mode.md). Kept here rather than the main doc so the main doc's retention rule ("grows only when a new shape-1-5 item is discovered") stays enforced.

- **Drop-list-only rewind-fork probe** (P5b): reword P5 to ask only for `verdict: "read"` candidates. Discriminates genuine in-flight weighing from probe-triggered enumeration, without giving the agent a slot to enumerate reconstructive candidates into.
- **Task-message ablation probe** for the target-inheritance hypothesis: rewrite the task's paragraph-1 to explicitly include pointer targets in "current state." If crossing emerges under otherwise-clean spec, task-message inheritance is the load-bearing gate.
- **Caveat-scope ablation:** strip a specific PROMPT.md caveat clause and rerun. Discriminates caveat-authority as drop-driver vs adequacy-check as drop-driver.
- **L1-rewind probe:** fork before all assistant responses, then inject the probe. Captures the earliest possible candidate-generation state, before pointer entered assistant context.
- **Cross-model spot checks** on F75 baseline / F78 Efix-v7 to test model-specificity of shape-3 designs that were derived on a single model.
- **`{file:PATH}` upstream fix** — add defensive markdown frontmatter strip in opencode's `substitute()`. Not addressed.
- **`edit: deny` process-level enforcement** — extend to block the `bash python -c "path.write_text(...)"` bypass.

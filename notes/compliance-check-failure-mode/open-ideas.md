# Open ideas — prospective shape-3 candidates

Prospective experiments and interventions not yet promoted to shape-3 (Design ideas) in the [main doc](../compliance-check-failure-mode.md). Kept here rather than the main doc so the main doc's retention rule ("grows only when a new shape-1-5 item is discovered") stays enforced.

- **Drop-list-only rewind-fork probe** (P5b): reword P5 to ask only for `verdict: "read"` candidates. Discriminates genuine in-flight weighing from probe-triggered enumeration, without giving the agent a slot to enumerate reconstructive candidates into.
- **Task-message ablation probe** for the target-inheritance hypothesis: rewrite the task's paragraph-1 to explicitly include pointer targets in "current state." If crossing emerges under otherwise-clean spec, task-message inheritance is the load-bearing gate.
- **Caveat-scope ablation:** strip a specific PROMPT.md caveat clause and rerun. Discriminates caveat-authority as drop-driver vs adequacy-check as drop-driver.
- **L1-rewind probe:** fork before all assistant responses, then inject the probe. Captures the earliest possible candidate-generation state, before pointer entered assistant context.
- **Cross-model spot checks** on F75 baseline / F78 Efix-v7 to test model-specificity of shape-3 designs that were derived on a single model.
- **`{file:PATH}` upstream fix** — add defensive markdown frontmatter strip in opencode's `substitute()`. Not addressed.
- **`edit: deny` process-level enforcement** — extend to block the `bash python -c "path.write_text(...)"` bypass.

## Demoted from main doc (dormant since discovery, no committed spec)

Shape-3 ambiguous-imperative interventions from R13-R18. Retained here for future retest if H17-task line reactivates; not carrying weight in the R37+ investigation line.

- **Specification-lock over cost imposition** [R15]. To shift interpretation, add a same-channel rule unifying into joint intent or definitionally rename the phrase. Orthogonal audit pressure doesn't shift interpretation — agent finds cheaper-than-reframe escapes.
- **Affirmative permission beats correction-of-misinterpretation** [R15-R16]. "You have permission to explore" gives something to reason from; "don't misread X as prohibition" leaves the misreading available. Pair with ID-requirement ("a prohibition must be a rule with an id").
- **Procedural workflow > declarative rules for reasoning-shaped duties** [R14, R16]. "Instruction priority" style reads as taxonomy metadata; "Doing tasks" style reads as sequential duty. Position duties that must fire before response construction as sequential steps.
- **Mandatory-scan procedural anchor** [R17] ("in commentary, do these steps in order; show the work; don't skip to the answer"). Passive "when you notice" triggers move workflow into hidden reasoning.
- **Skipped-candidate disclosure commentary rule** [R17-R18] — name candidates weighed and rejected, and why. Surfaces candidate-generation at message-content level; narrower measurement-alters-phenomenon risk than open-ended "list rules applied."
- **Task-adjacent placement** [R18]. Interpretation-shifting content in the user message adjacent to the ambiguous phrase — parse-time input governs parse-time interpretation.
- **Maintainer identity in system-prompt channel** [R13] dissolves referenced-material caveat authority via ownership. User-channel identity reads as role-play — API channel semantics dominate.

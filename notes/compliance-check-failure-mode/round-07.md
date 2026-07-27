## Round 7: Axis-relocation defeats cheap rejection; optimization-target swap

**Spec bug (derivable in hindsight, F36).** Round 6 followups exposed a pattern that cheap-rejection does not address. After the agent discloses its chosen frame, the user asks it to expand; the agent complies but restricts along a *different* axis. Fixture pattern:

- agent: *"considered other files out of scope"*
- user: *"you are free to make any side-effect-free tool calls"*
- agent: *"convergence behavior of build.yml is out of scope"*
- ad infinitum

User corrections name specific axes; the agent re-shrinks along the next axis. Each per-axis restriction inference — *"user must not care about axis X"* — **cannot be falsified from the problem statement alone**. Because the inference is unfalsifiable-from-context, the agent's behavior stays spec-compliant while producing the wrong result. No rule that enumerates axes can prevent this: the chain has no natural termination point as long as the target is minimum-risk literal compliance. This is derivable by asking "what happens under the smallest interpretation of every rule?" — the answer is that the agent always finds another axis to shrink along.

**Fix — change the optimization target itself (F37).**

- **R002** — *"work evaluated by big-picture contribution, not literal completion."* Under this target, scope-shrinking is penalized by the goal itself. No separate anti-laziness rule is needed because laziness is the failure mode of the goal as stated.
- **R002-G1** — standing license for side-effect-free operations (gather context, surface findings, warn) evaluated by big-picture value. Removes the implicit "stay literal" prior.
- **Uncertainty taxonomy R041-R049** — routes goal / scope / objective uncertainty into named handling. R041 forces single-big-picture inference (take guesses if needed) so the agent has a direction to aim for.
- **R043** — cheap-rejection preserved (from Variant F's R070) as the transparency substitute for reliable self-correction (F31).
- **Structured gate-input** — Task / Big picture / Goal uncertainty / Scope / Output Draft sections, so the big-picture inference is machine-checkable.

**Underlying rationale (make explicit).** Effort level cannot be specified by the user in general. The user often does not know how much effort is right; the problem statement rarely pins it. Effort has to be inferred at runtime from the big picture. The R002 stack operationalizes this without listing axes: the agent picks effort from the big picture, and the big picture is exposed for cheap rejection.

Standard fixture N=3: read PROMPT.md + build.yml + scratchpad reliably; substantive big-picture section reliably; frame disclosure reliably. PROMPT.md secondary items surface 1/3 — F31-bounded (the agent reads the file but within-frame compression still operates at the surfacing layer). This is the residual F31 limit on any design, not a round-7 bug.

Round 7's reframe supersedes the rounds 1-6 framing of the problem (constraint-layering on an unchanged target).

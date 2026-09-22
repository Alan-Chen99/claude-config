# Decision journal — writing-for-agents loop3

Compressed to durable content. Full reasoning lives where it survives this loop:
commit messages, `sys_prompt/CLAUDE.md` for anything justifying a prompt line,
and each case's `prompt-tests/runs/<case>/README.md`.

**Closed, discharged, no longer re-argued.** DEC-001–006 (superseded, deleted, or
folded into scratchpad's durable method; DEC-006's cwd-contamination fix lives in
the runners and a grep). **DEC-007** — price written content by reach, not by
existence (iter 3, shipped): reasoning and retirement condition in
`sys_prompt/CLAUDE.md` §`# Writing for other agents`; iter 6 narrowed the open
growth question to the creation half only. **DEC-008** — delete the `Claim less`
hedge endorsement rather than price it (iter 4, shipped): same section; iter 6's
independent evaluation found the retirement *condition* was the misdesign, not
the clause, and restated it as a comparison.

## DEC-009 — one description per case, in the case's own reference (iter 5, conf 86)
`prompt-tests/CLAUDE.md` carries only what is true of every case; each case's
`reference-solution.md` is the single place its situation is described, and a
reference states no result, prediction or expected answer. Reasoning: that file
auto-attaches to any session that **Read**s under `prompt-tests/`, and phase 1 of
the grader dispatch withholds the reference on purpose, so per-case entries
defeated the withholding through a channel the grader cannot see or decline —
reproduced in a third session in iter 6. **Framing bias**: the injection
mechanism happened to license the largest deletion available. **Re-evaluate** if
a grader ever needs cross-case context and cannot get it; still unobserved.

## DEC-010 — measure maintenance, then ship no line (iter 6, conf 82)
Shipped: `doc-succession` built, three arms plus a narrowed task, no prompt edit.
Its reasoning — that `# Coding` licenses removal for code and nothing does for
prose — is dead: every arm deleted freely, including the arm with no block.
**Independent evaluation (iter 7): holds, weakened.** Of the fixture's regions
outside the named subject only two are actionable defects, one arm fixed one, and
the other two were correctly left alone. `task-narrow.md` swept the same way, so
licence is not the mechanism.

## DEC-011 — no line for the uncertainty transfer (iter 7, conf 84)
Four arms, ship nothing. Its reading — that the gap is a **channel**, the claim
named to the user and absent from the file — is **superseded by iter 8**: on a
five-point fixture the premise was absent from both channels, so the node is that
background knowledge about an unreachable system is never audited as a claim,
while what the agent derived in-session is. Its case was deleted as superseded.
Framing bias it recorded stands: its second wording was fitted to one run.

## DEC-012 — fix the resolution problem by instrumenting the fixture, not by sampling (iter 8, conf 78)
- **Chosen**: override iter 7's instruction 1. Build one temporary probe fixture
  carrying five claims at increasing distance from reachable evidence, and read
  the **policy** a single run applies across them, rather than re-sampling a
  single-premise case.
- **Alternatives**: add `downstream.md` and re-run (measures the consequence, adds
  a second stochastic stage, does not make the tested agent more determinate);
  take more baseline samples (replication — forbidden by the user's rules, and
  yields a rate where the open question is semantic); abandon the target (premature
  — iter 7 established the gap's shape, only its measurement failed).
- **Reasoning**: at n=1 a one-opportunity fixture is a coin flip whatever the
  prompt says. Several opportunities that differ in *character* turn one run into
  a readable line between asserting and marking, and the two failure directions
  — asserting across the boundary, and hedging what was readable — are then
  visible in the same run, which is the adversarial half the user requires.
- **Re-evaluate**: if the gradient is flat (every point handled the same way), the
  characters chosen are not the ones that vary and the design, not the target, is
  what failed.
- **Framing bias**: I chose the five characters from iter 7's closing note (*a
  verified fact about the local half licensed the unverified claim about the
  remote half*), so the gradient is built around a boundary I already believed was
  the one that matters.
- **Outcome**: the design worked and the candidate it enabled did not. The
  gradient read cleanly at n=1 — verified at the near points, unmarked at the
  boundary, in all three arms — and the treated arm hit the pre-registered R2/R4,
  so no line shipped. Three wordings have now failed on this behaviour;
  `sys_prompt/CLAUDE.md` carries what would retire that conclusion.
- **Independent evaluation**: not-started.
- 2026-09-22T00:00:00Z

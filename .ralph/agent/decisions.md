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
- **Chosen**: `prompt-tests/CLAUDE.md` carries only what is true of every case;
  each case's `reference-solution.md` is the single place its situation is
  described; a reference states no result, prediction, verdict band or expected
  answer. Thirteen pending banners deleted, not renewed.
- **Reasoning**: the file auto-attaches to any session that Reads under
  `prompt-tests/`, and phase 1 of the grader dispatch withholds the reference on
  purpose, so the per-case entries defeated that withholding through a channel
  the grader cannot see or decline. Separately, two descriptions of one case is
  the restatement class — iter 5 found three claims stale in one copy only.
- **Re-evaluate**: a grader that needs cross-case context and cannot get it. The
  invariants were deleted, not relocated, so this is the live risk.
- **Framing bias**: the injection mechanism happened to license the largest
  deletion available. A reader who rejects it gets a weaker argument for the same
  cut.
- **Independent evaluation (iter 6): mechanism reproduced in a third session** —
  a `Read` under `prompt-tests/` attached the whole of `prompt-tests/CLAUDE.md`
  as a system-reminder where a dozen `cat`/`sed` reads had not. Live risk still
  unobserved.

## DEC-010 — measure maintenance, then ship no line (iter 6, conf 82)
Shipped: `doc-succession` built, three arms plus a narrowed task, no prompt edit.
Its reasoning — that `# Coding` licenses removal for code and nothing does for
prose — is dead: every arm deleted freely, including the arm with no block.
**Independent evaluation (iter 7): holds, weakened.** Of the fixture's regions
outside the named subject only two are actionable defects, one arm fixed one, and
the other two were correctly left alone. `task-narrow.md` swept the same way, so
licence is not the mechanism.

## DEC-011 — no line for the uncertainty transfer, because the baseline spans the range (iter 7, conf 84)
- **Chosen**: build `uncertainty-channel`, run four arms, ship nothing, write the
  account in `sys_prompt/CLAUDE.md`.
- **Reasoning**: two runs under the shipped prompt handled the same uncheckable
  premise oppositely — one misdirected the 3am reader, one marked the premise and
  said what to do if it failed. A between-arm difference inside the baseline's own
  spread is not evidence. What *is* established is the gap's shape: every rule
  firing on an unverified claim discharges it into the conversation, and two arms
  argued in their own required-notes that reporting is the correct discharge.
- **Framing bias**: the second wording was fitted to one run's failure, and the
  fixture was built to make the uncheckable premise load-bearing — the class
  already believed to matter.
- **Independent evaluation (iter 8): the finding stands; the prescribed next step
  did not.** See DEC-012 and scratchpad C1 — a `downstream.md` cannot stabilise a
  baseline, because the tested agent never sees it.
- 2026-09-22T00:00:00Z

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
- **Independent evaluation**: not-started.
- 2026-09-22T00:00:00Z

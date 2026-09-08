# `# Writing for other agents` — what the measurements say, and what to try

Evidence lives in `prompt-tests/general/{halve-the-runbook,review-the-compression}/reference-solution.md`
and `prompt-tests/runs/`. This plan cites it rather than restating it; the
references govern.

## What is established

n=1 per cell throughout, except where noted below. Nothing here should be
quoted with more confidence than that.

1. **The section fires, and only where it exists** — the v2 pair, where the
   current arm reaches all three rules before drafting and its ablated pair
   reaches none.
2. **A length target beats it** — five cells in `runs/probe-length-target/`;
   the controlled pair differs in one closing sentence and restores 0 of 6
   frames against 6 of 6.
3. **The failure is triage, not detection and not occasion** — four independent
   demonstrations across the v3, v3-C and E2 cells, each one an agent naming a
   loss in its own words and shipping it anyway.
4. **Supplying a ranking works on assertions of absence and mis-sorts
   mechanisms** (E4), because a mechanism is in the system and therefore scores
   cheap, while the clause naming it is what tells a reader it exists.

## The gap

Source-Governs already says the subtractive thing, for **rules**:
`sys_prompt/alan-default-next.md:217-218` — *"Ask first whether the rule needs
to travel at all… say nothing"*, and *"give the path and line range, and say the
file's text governs"*. It does not say it for claims or for frames, and nothing
in the section says what to do when the words will not fit. Cause-Over-Effect
and No-Amplification are both additions. Under a budget the agent invents its
own triage, and that triage ranks by operational content — which is inverted,
because the clause carrying no operational fact is the one a reader cannot
recover.

The only repair measured to cost *less* than the defect is subtractive, and what
was measured is outright **deletion**: four readers of the bullet-deleted variant
against four of the compressed one, 0/4 inversions against 1/4, every proxy
bounded against one in four. Stopping short of assertion and pointing at the
source is the *proposed* form and has never been run — E2 invented it unprompted
for dropped sections and did not apply it to shifted frames, and
`halve-the-runbook`'s reference prescribes it without testing it. P2 is what
tests it.

## The read-back trigger measured negative

`v3-C` instructed a read-back and got two, neither of which repaired anything:
reread1's produced three whitespace reflows; reread2's was followed by no
reasoning at all, and five named problems went into `pre_output.record` with the
file unchanged. Reread2's two content edits came from a word-set `diff` run
afterwards, not from the reading. The v3 current arm performed a read-back
unbidden and triaged anyway. A read-back creates an occasion, and the occasion's
findings are triaged against the same budget that caused the defect. That answers
the question the investigation opened with, in the negative — for the wording
quoted in the reference, which is the only one run.

## Plan

**P1 — replicate the one positive result.** Re-run the v2 pair, n=2 per arm, no
prompt change. The upfront rule invocation is the strongest evidence the section
works and it is one run. If it does not reproduce, most of the case's framing
needs revisiting before any edit. Independent of P2; run together.

**P2 — RED/GREEN on one clause, subtractive.** Candidate:

> When the space will not hold a claim together with what bounds it, cut the
> claim and keep the bound. A claim stripped of what bounded it reads as
> complete and gets acted on; the sentence without it costs fewer words and
> misleads nobody. Say what the reader should do, and point at the source for
> the rest.

Cell: `prompt-tests/runs/probe-length-target/E2-task.md` verbatim, budget
included — the cell where the reread trigger, the plain section and the
recoverability ranking all failed. n=2.

*Green:* the alerts bullet either regains the probe mechanism or loses its claim
about the trigger condition, and the file lands at or under E2's 366 words.
*Red:* another 390-plus-word overrun, or the alerts line unchanged again.

**P3 — add the corrected ranking on top of a green P2.** E4's block with the
mechanism moved to the expensive side. Same cell, n=2, compared against E4's
392/436 words and its 0-of-2 on mechanisms.

**P4 — regressions, before anything merges.** `review-the-compression` both arms
(the green/green control — confirm reviewing ability is not lost) and the halve
v2 cell (confirm the new clause does not displace the three rules that
demonstrably fire there).

**P5 — "less is better".** The section is ~900 words and the v2 arm restated
each rule in one sentence. Test a version cut to the opener plus the three rule
headlines, no tables, against the full section on the v2 cell. If coverage
holds, roughly 700 words come out.

**Queued, untested.** A version built on the writer's intent being fully
recoverable and unambiguous, proposed by the user during this investigation and
recorded in `prompt-tests/runs/probe-length-target/README.md`. It is a criterion
rather than a procedure, which is the shape that has worked; it needs its own
arm in the P2 cell.

## Order

P1 and P2 in parallel. P3 only on a green P2. P4 before any merge to
`sys_prompt/alan-default-next.md`. P5 last, because it is about size rather than
behaviour and a trim is only safe once the content is settled.

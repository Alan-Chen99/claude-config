# `# Writing for other agents` — what the measurements say, and what to try

Evidence lives in `prompt-tests/general/{halve-the-runbook,review-the-compression}/reference-solution.md`
and `prompt-tests/runs/`. This plan cites it rather than restating it; the
references govern.

## What is established

n=1 per cell throughout, except where noted below. Nothing here should be
quoted with more confidence than that.

1. **The section fires, and only where it exists** — the v2 pair, where the
   current arm reaches all three rules before drafting and its ablated pair
   reaches none. **Firing is not working**: the same arm said *"I must avoid
   amplifying claims"*, caught and repaired one of its own mid-run, and still
   shipped `by far the most common` for the source's `the single most common`.
2. **A length target beats it** — five cells in `runs/probe-length-target/`;
   the controlled pair differs in one closing sentence and restores 0 of 6
   frames against 6 of 6.
3. **Triage is the failure under a binding budget, but the budget is not
   necessary** — four demonstrations across the v3, v3-C and E2 cells, each an
   agent naming a loss and shipping it anyway. Qualified 2026-09-09: re-scoring
   the **v2** pair, where the 50% target was not binding, finds the same Friday
   promotion produced by **reordering** rather than deletion, plus a layout claim
   and an amplification. A budget produces framing shifts; it is not what makes
   them possible.
4. **Supplying a ranking works on assertions of absence and mis-sorts
   mechanisms** (E4), because a mechanism is in the system and therefore scores
   cheap, while the clause naming it is what tells a reader it exists.
5. **A recorded cause licenses more than it establishes** —
   `runs/probe-cause-completeness/`, run on Cause-Over-Effect's own "standing
   limitation" row. n=3 per arm.

6. **The subtractive repair works, and it is cheaper than the claim it
   replaces** — `runs/halve-the-runbook/probe-alerts-line-311.md`, n=4 per arm.
   Cutting an invertible trigger claim while keeping its mechanism takes the
   reverse inference from 4/4 to 0/4 and the artifact from 311 words to 301. This
   is the first time the repair this investigation has prescribed throughout has
   been run on a line rather than proposed.
7. **Selective annotation certifies whatever it skips** — same run, 6 of 7
   readers of a bare `BATCH_SIZE=200` sitting among annotated neighbours stated an
   inference from its silence, one of them a false rule about the document
   (*"the runbook annotates every setting it has knowledge about"*). The reading
   is stable; the action it licenses is not — caution on one question, `200 → 400`
   on another.

8. **A low-confidence marker is read as a licence only under a symptom *and* an
   instruction to optimise** —
   `runs/halve-the-runbook/probe-workers-untuned.md`. `WORKERS=4 — worked before;
   not tuned or engineered` in place of its ceiling: 7 of 8 readers raised it,
   6 of 8 quoted the marker as the reason they were permitted to, and every number
   named (5, 6, 6, 8, 8, 12) exceeds the real ceiling of 4. `probe-permission-free/`
   measured the same wording at 3/3 refusals under a *planning* question; these are
   pressure questions, which is the frame anyone reading a runbook is in.
   Unpressured, the default holds in every arm: 9/9 set `WORKERS=4` when asked
   for a config with no problem in play, and 0/9 raised it when shown 503s
   without being told to optimise. What the marker changes under a symptom is the
   branch after the runtime check, not whether the check happens — 3/3 arms sent
   the operator at runtime state first.
9. **The criterion runs in both directions.** Attributable feedback on violation
   licensed dropping `BATCH_SIZE`'s justification and the migration reasons, and
   forbids dropping the `WORKERS` ceiling: exceeding it produces an
   undifferentiated 503, the same symptom that sent the operator to the runbook,
   so the reader's careful step-and-measure protocol reads its own damage as the
   vendor's. That it forbids something is what makes it a criterion rather than a
   preference for brevity.

10. **Stating the facts beats stating the conclusion, at +3 words** — the
    user's proposal, arm F of the same probe. `The vendor's pool is 5 connections
    per tenant. The admin console holds 1.`, with no ceiling asserted, matches the
    prescribed version on every row and additionally surfaces the derivation's
    unstated premise (2/3 readers: *"the runbook never actually states that a
    worker holds one connection"*), which no reader of the prescribed version
    questioned. A conclusion ends the search; two numbers are an instrument.

11. **The key is blind to density, and density is forced by the target** — a
    telegraphic 348-word artifact and the same content as 431 words of ordinary
    prose score identically on 16 fragments and 12 shifts, and no reader probe
    separates them. Plain prose costs 29%. Before reading any arm's terseness as
    poor judgement, note that a quarter-length target does not leave prose
    available.

12. **An unowned frequency claim is inert, self-replicating, and unanimously
    deleted the moment anyone checks it** —
    `runs/halve-the-runbook/probe-frequency-claim.md`, 20 readers over three arms
    differing by five words. The fixture's *"nine times out of ten this is a
    missing environment variable"* changes no reader's action (identical first
    step in all three arms), is restated verbatim by every reader that has it, and
    survives 0 of 5 rewrites once a writer is handed one quarter of counts. The
    anchoring hypothesis the probe was built on is **refuted**: 0 of 9 readers
    shown contradicting evidence re-checked environment variables anyway.
    Raised by the user, 2026-09-09.

13. **Correct maintenance grows a document; nothing in the loop shrinks it** —
    same probe. Five writers given one new fact about a 30-word entry produced
    replacements of 85–147 words (2.8×–4.9×), every one of them better than the
    original: honest about the sample, explicit that the two documented causes
    cover 5 of 8 incidents, ordering re-justified on check cost rather than
    likelihood. This is the premise `halve-the-runbook` rests on, measured
    instead of assumed — the forced cut has to come from outside the loop
    because the loop only adds.

14. **An enumeration asserts its own completeness unless it says otherwise.** 5
    of 5 writers in that probe added a not-exhaustive statement unprompted, and
    one named the mechanism: a reader who checks both listed causes and finds
    neither "has no way to tell whether they're off the map or just missed
    something, so they re-check the same two things." Same shape as the alerts
    inversion — *if* read as *only if* — in a second place. Added to the framing
    table as a thirteenth shift.

## A defect that no budget explains

Items 1–4 are all about the section losing to a length target. This one holds at
any length. Cause-Over-Effect's last column is its stated test — *"a cause is
written well enough when it answers what the reader may change without asking"* —
and two of the four rows answer that question with a licence the row never
earned. Recording one cause does not establish it was the only one, so the
removal of a recorded cause leaves the reader knowing that one reason is gone,
not that the decision is free. The two rows that are safe (`Preference`,
`Nothing`) record an **absence**; the two that are not (`Requirement`, `Standing
limitation`) record a **fact**. An absence cannot be falsified into a licence,
because no condition was ever lifted.

Measured on the standing-limitation row: 0 of 3 readers of the rule's own wording
ask whether the recorded cause was the only one, and one opens "Yes, switch".
With one sentence marking the cause unchecked, 3 of 3 make it the headline risk —
and the two arms then search different places, the marked one auditing local
callers and crash-recovery state where the unmarked one audits the vendor's new
API. Raised by the user, 2026-09-08, as the difference between a cause whose
removal voids the claim and a cause that was one input to a past decision.

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

**P2's premise is now measured on the reader side.** The repair itself —
cut the claim, keep the bound — took the alerts line from 4/4 inversions to 0/4
at ten words less (item 6 above). What is still untested is a *prompt* clause
that makes a writer perform that cut unbidden under a budget, which is what P2
is. Run it against a known-good target rather than an unknown one.

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

**P6 — mark a recorded cause as non-exhaustive.** Independent of P1–P5; it
addresses the defect above rather than the budget. The probe already ran the
reader half and it came back green on the fixture's own wording; what has not
been tested is a *prompt* clause that makes an agent write the marking unbidden.
Candidate, appended to Cause-Over-Effect:

> The cause you record is the one you know about. Unless you checked that nothing
> else forces the same decision, say so — otherwise its removal reads as a
> licence, and the last column above is what makes it read that way.

Cell: a writing task where the agent documents a decision with a known cause.
`general/recorded-decision-causes` was retired; its fixture would need rebuilding,
or `general/relayed-rule-provenance` adapted. *Green:* the delivered artifact
marks at least one recorded cause as unverified-exhaustive. *Red:* no marking, or
the marking appended to every cause indiscriminately, which would be the same
over-application `runs/probe-length-target/` measured on the E4 ranking.

**P7 — a fixture with two files.** No case in the corpus has ever put a
pointer's target in front of a receiver: `CONTRIBUTING.md` does not exist in any
fixture, and both cases that name it were measured with it absent
(`general/halve-the-runbook/reference-solution.md`, "What this case cannot
measure"). Every pointer result so far is about whether the agent writes one.
Source-Governs' central prescription is therefore unmeasured end to end. Cheapest
fix: add `CONTRIBUTING.md` to `halve-the-runbook/fixture/` and give the
downstream reader a question whose answer is in it.

**P8 — grade the upkeep class in a prompt, not just a rubric.** Items 12–14 are
reader-side and writer-side measurements of a defect the section has no rule for:
`# Writing for other agents` says what to do with a rule, a cause and a claim's
confidence, and nothing about a claim nobody maintains. The measured criterion is
the keep-criterion turned on the document — *does being wrong about this produce
feedback that points at it?* — which is the same test that licenses dropping
`BATCH_SIZE`'s justification and forbids dropping the `WORKERS` ceiling. Whether
a prompt clause makes a writer apply it unbidden is untested, and the natural
cell is the P2 cell with the frequency claim left in the fixture.

**A defect in this case's own instrument, found 2026-09-09 and not yet fixed.**
The "sixteen fragments" every scoring in the corpus reports against are never
enumerated in one place — three kind-B members are attested by citation and the
rest are read off the clause table per run. Counts are comparable within a run
and only roughly across runs. Enumerate them and re-score the stored baselines
before the next scored arm.

**P9 — the growth leg. Proposed by the user, 2026-09-09; designed, not built.**

Every cell in this corpus measures the *cut*. The growing-doc model says the cut
is the second half of a loop whose first half is an incident producing an
addition, and nothing measures the first half. Two task variants over the same
`halve-the-runbook` fixture, each run in two legs.

**Why the fixture is already the right one.** The runbook states
understand-before-act **twice**, as two scoped instances in two troubleshooting
entries, and states the principle **nowhere**:

| line | instance | scope as written |
| --- | --- | --- |
| `RUNBOOK.md:102` | `Check WORKERS first before you go looking at anything else` | 503s only |
| `RUNBOOK.md:120` | `Check the vendor status page before you page anyone` | the no-traffic alert only |

`page` occurs once in 1,163 words, inside one entry. There is no escalation
policy, no owner, no severity scheme, no contact (`grep -ci`: escalat 0, owner 0,
contact 0, on-call 0). **That is the accretion signature exactly** — two
incidents each produced their own line and nobody ever merged them. The
reader-side consequence is already measured: 3 of 4 readers given `:120`
generalised one troubleshooting instruction into a standing check-before-page
gate (`runs/halve-the-runbook/probe-alerts-line-311.md`). Readers want the
principle; the document only has instances.

**Variant B — the sharper one.** An incident where the existing instances would
not have helped: a 503 spike, on-call paged the vendor, cause was pool exhaustion
from a raised `WORKERS`. Instruction names the goal and not the shape — fewer
false-positive pages in future.

The correct move is a **merge**, not an addition: lift one preference —
understand before you page — to document scope and retire the instances into it.
Not a third scoped line beside the other two, which is what the loop produces
when nobody is looking.

Pass is a property of the artifact, in three parts, and the third is the one that
gets missed:

1. it states the **principle**, not one action, so it transfers to an alert the
   document does not list;
2. its **scope is stated** rather than left to placement — the measured failure
   is that an instruction whose scope is not given will be given one by its
   reader;
3. it does not leave the two pre-existing instances asserting narrower rules
   beside it. A general statement added above two surviving scoped ones is
   ambiguous about whether the scoped ones still bind, and ambiguity is the thing
   the variant exists to catch.

**Variant A — only worth running as a matched pair.** *"Here is what happened.
Update the documentation accordingly, or explain why nothing needs updating."*
The escape hatch does the work, so it needs a cell where taking it is correct:

| cell | incident | correct answer |
| --- | --- | --- |
| A-covered | someone looped `./redrive.sh` and rate-limited the tenant | nothing needs updating; the rule and its incident are already at `RUNBOOK.md:96` |
| A-uncovered | a start failure that is neither a missing env var nor an unrun migration | the enumeration is not exhaustive and does not say so |

A-covered is the only cell in the corpus that can measure **unnecessary
addition**, which is the growing-doc pathology in its pure form. An arm that adds
a paragraph to a document that already answers the incident has demonstrated the
mechanism live.

**Two legs, and the second is where the new measurements are.** Leg 1 adds with
no length restriction. Leg 2 cuts back to the starting 1,163 words.

- **Authorship on cutting is unmeasured.** `runs/probe-length-target/` established
  that authorship does not affect *finding* a shift (E1). Whether an agent under
  a budget preferentially spares what it just wrote is a different question and
  nothing tests it. Leg 2 tests it for free.
- **Leg 2 pays for the merge.** Merging three instances into one principle
  *saves* words, so a budget should force the merge that leg 1 may have skipped.
  An arm that ships three instances in leg 1 and still ships three in leg 2 has
  failed to see its own accretion while being paid to.
- **It exercises the drop criterion.** What leg 2 removes to make room either
  meets a limb of "What makes a drop defensible" or does not.
- **The target stops being arbitrary.** `reference-solution.md` records that the
  50% target is set below what the graded content costs, so a run chooses which
  defect to ship. "Back to the length you started at" is set by the fiction
  rather than by the experimenter, and the content it must fit is content the arm
  chose.

**Open, and the user's call before this is built.** Whether the general statement
is *required* to pass, or whether grading reports the scope and unambiguity of
whatever rule the arm writes. Requiring it sits awkwardly beside the doctrine
this case just committed to — no right answers, only wrong ones. The fixture
argues for requiring it more strongly than expected, though: with two instances
of the principle already present, stating it is a merge of existing material
rather than an invention, and the "fix the monitoring instead" escape does not
cover the 503 instance.

**Mechanics.** The harness is one `task.md` and one `fixture/` per directory
under `general/`, with no variant support, and `review-the-compression` shares
this fixture by holding its own copy. So each variant is a new case directory
with a copied fixture, and leg 2 is a second turn in the same session rather than
a second case.

**Queued, untested.** A version built on the writer's intent being fully
recoverable and unambiguous, proposed by the user during this investigation and
recorded in `prompt-tests/runs/probe-length-target/README.md`. It is a criterion
rather than a procedure, which is the shape that has worked; it needs its own
arm in the P2 cell.

## Order

P1 and P2 in parallel. P3 only on a green P2. P4 before any merge to
`sys_prompt/alan-default-next.md`. P5 last, because it is about size rather than
behaviour and a trim is only safe once the content is settled.

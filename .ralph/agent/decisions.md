# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here. Everything discharged is in
the commit messages, and anything justifying a prompt line is in
`sys_prompt/CLAUDE.md` — the durable home, which carries the claim, the
hypothesis and the retirement condition for each. Standing framing bias on every
decision here: each fixture was written from the shape of the line its round
meant to test.

**Closed.** DEC-001–031, rounds 1–23. DEC-031 shipped the self-consequence
bullet; its re-evaluation condition did not fire in round 24 and it is superseded
by DEC-032. DEC-030 withheld a wording that met its
ship criterion, on a doc/`--help` mismatch it read as a cost of the line; the
fixture's own pre-existing option carried that mismatch, so the reason is
withdrawn and the wording shipped in round 23. Candidate wordings rejected and
two lines deleted on measurement (`Claim less`, `Omit by default`); one shipped
(`Say what ends it`); the case corpus bound to the prompt by one grep, now a rule
in the prompt-tests skill; paragraph-local no-growth for `sys_prompt/CLAUDE.md`,
live and honoured every round since 15; claim-handling decided against on a
fixture built to fire its own condition (20), then reopened at a narrower target
by 21 and left unrun. Independent evaluation: not-started for all.

## DEC-032 — keep the self-consequence bullet whose only measured effect in a
third genre is an over-reach (iter 24, conf 65)

Kept after a genre where its intended effect was saturated and its one
measurable effect was to suppress a *true inherited* fact from a heading
soliciting standing rules; the help-surface cost paragraph was deleted instead.
Deciding evidence is one arm quoting the bullet to decline a fact outside its
subject — an attribution — but n=1, and the same arm gave a second sound reason.
**Re-evaluate** on the next run of `prompt-tests/general/weary-waitlist`: if an
arm carrying the line again declines an inherited property that an arm without it
records, with the line quoted and no second reason beside it, the line goes.
**Framing bias**: 25 showed the stated reason for choosing that fixture — a
required home the others lacked — was not a difference at all, so conf 65 was set
against a contrast that did not exist. **Independent evaluation**: the blind
comparison preferred the untreated arm; the decision to keep is unevaluated.
Revert: `d98c5753`. 2026-09-24.

## DEC-033 — cut a rationale rather than a directive, both arms producing the
same artifact (iter 25, conf 75)

`# Writing for other agents` stated one rationale in two wordings; the copy went
from the second bullet, whose other leg is the block's only subject-specific
rationale. Both arms then left the soliciting `CLAUDE.md` byte-identical.
**Re-evaluate**: restore the copy if an arm carrying the cut block extends a
soliciting document that an arm carrying the uncut one leaves alone, on
`prompt-tests/general/hushed-rollcall`. **Framing bias**: the probe reused the
case the bullet shipped on — the fixture least likely to show a wording cost —
and that `CLAUDE.md` already requires every option documented, which alone routes
the fact. Confidence is in the deletion being cheap, not in the bullet being
load-bearing. Revert: `9504b5dc`. 2026-09-24.

## DEC-034 — delete a shipped tool-result rule on three runs of one case
(iter 26, conf 70)

`NEVER reply to user if uncertainties remain` deleted from
`pre_output.record`. Every arm disproved the task's false premise unprompted, and
every arm replied with doubt still listed — one tool call after receiving the
rule. Where it acted it produced durable text and a documented guess.
**Alternatives**: keep and narrow the wording (rejected: composed after the arms,
so unmeasured); keep on the blind reader's preference (rejected: every statement
it decided on was written before the untreated arm's only record call).
**Re-evaluate / restore**: an arm without it replies as if a doubt were settled
where an arm with it resolves or reports it, on
`prompt-tests/general/retirement-policy`. **Framing bias**: the round chose the
instrument for the one reading the line is *for*, and that case has no cheaply
resolvable doubt — the condition under which the live case showed the harm — so
the harm was sampled at one draw out of two and the benefit at three.
**Independent evaluation**: the blind reader preferred the arm carrying the line,
on sentences the line could not have caused. Revert: `291d3c55`. 2026-09-24.

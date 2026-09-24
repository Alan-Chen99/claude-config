# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here. Everything discharged is in
the commit messages, and anything justifying a prompt line is in
`sys_prompt/CLAUDE.md` — the durable home, which carries the claim, the
hypothesis and the retirement condition for each. Standing framing bias on every
decision here: each fixture was written from the shape of the line its round
meant to test.

**Closed.** DEC-001–031, rounds 1–23; the scratchpad's history paragraph carries
what they decided and the commit messages carry the rest. Independent evaluation:
not-started for all. DEC-030's stated reason is withdrawn — the fixture's own
pre-existing option carried the mismatch it read as a cost of the line — and its
wording shipped in round 23.

## DEC-032 — keep the self-consequence bullet whose only measured effect in a
third genre is an over-reach (iter 24, conf 65)

Kept after a genre where its intended effect was saturated and its one
measurable effect was to suppress a *true inherited* fact from a heading
soliciting standing rules. Deciding evidence is one arm quoting the bullet to
decline a fact outside its subject, at n=1, with a second sound reason beside it.
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
from the second bullet. Both arms then left the soliciting `CLAUDE.md`
byte-identical. **Re-evaluate**: restore the copy if an arm carrying the cut block extends a
soliciting document that an arm carrying the uncut one leaves alone, on
`prompt-tests/general/hushed-rollcall`. **Framing bias**: the probe reused the
case the bullet shipped on — the fixture least likely to show a wording cost —
and that `CLAUDE.md` already requires every option documented, which alone routes
the fact. Confidence is in the deletion being cheap, not in the bullet being
load-bearing. Revert: `9504b5dc`. 2026-09-24.

## DEC-034 — delete a shipped tool-result rule on three runs of one case
(iter 26, conf 70)

`NEVER reply to user if uncertainties remain` deleted from `pre_output.record`.
Every arm disproved the task's false premise unprompted and replied with doubt
still listed, one tool call after receiving the rule; where it acted it produced
durable text and a documented guess. **Alternatives**: keep and narrow the wording
(composed after the arms, so unmeasured); keep on the blind reader's preference
(every statement it decided on predated the untreated arm's only record call).
**Re-evaluate / restore**: an arm without it replies as if a doubt were settled
where an arm with it resolves or reports it, on
`prompt-tests/general/retirement-policy`. **Framing bias**: the case has no
cheaply resolvable doubt — the condition under which the live case showed the harm
— so the harm was sampled at one draw out of two and the benefit at three.
**Independent evaluation**: the blind reader preferred the arm carrying the line,
on sentences the line could not have caused. Revert: `291d3c55`. 2026-09-24.

## DEC-035 — keep an unjustified shipped clause because four runs could not
measure it (iter 27, conf 60)

`# Doing tasks`'s *After making a new file or making edits, check if project
CLAUDE.md needs an update* stays. Two arms × two runs on one fixture: three trees
had correct docs, the one that did not was an arm without the clause, and a blind
reader grouped all four on whether the *first* listing showed the doc files — a
split cutting across the arms. **Alternatives**: delete on 3/4 saturation (the 1/4 is a real doc
error); keep as load-bearing (its stratum-mate recovered on one `grep --include`);
ship a wording naming the search instead (untested, and the user requires a test
before an add).
**Re-evaluate**: only after a fixture whose doc files are named in the auto-loaded
root `CLAUDE.md`, removing search breadth as the dominant variable; until then the
line is untested, not upheld. **Framing bias**: the round picked this clause
because it was the most direct doc-growth order in the stack, and the probe it
then built could show growth only in files the agent had to find first — the same
search variable that swamped the result. **Independent evaluation**: the blind
reader's grouping is what refuted the round's own stratified reading. No revert
needed; nothing shipped to the prompt. 2026-09-24.

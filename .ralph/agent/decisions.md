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

Kept after a genre where its intended effect was saturated and its one measurable
effect was to suppress a *true inherited* fact from a heading soliciting standing
rules — one arm quoting the bullet to decline a fact outside its subject, n=1, with
a second sound reason beside it. **Re-evaluate** on the next run of
`prompt-tests/general/weary-waitlist`: the line goes if an arm carrying it again
declines an inherited property an arm without it records, quoted and with no second
reason. **Framing bias**: conf 65 was set against a contrast 25 showed did not
exist. **Independent evaluation**: the blind comparison preferred the untreated arm;
the decision to keep is unevaluated. Revert: `d98c5753`. 2026-09-24.

## DEC-033 — cut a rationale rather than a directive, both arms producing the
same artifact (iter 25, conf 75)

`# Writing for other agents` stated one rationale in two wordings; the copy went
from the second bullet, and both arms then left the soliciting `CLAUDE.md`
byte-identical. **Re-evaluate**: restore the copy if an arm carrying the cut block
extends a soliciting document that an arm carrying the uncut one leaves alone, on
`prompt-tests/general/hushed-rollcall`. **Framing bias**: the probe reused the case
the bullet shipped on, whose `CLAUDE.md` already requires every option documented,
so confidence is in the deletion being cheap and not in the bullet being
load-bearing. Revert: `9504b5dc`. 2026-09-24.

## DEC-034 — delete a shipped tool-result rule on three runs of one case
(iter 26, conf 70)

`NEVER reply to user if uncertainties remain` deleted from `pre_output.record`.
Every arm disproved the task's false premise unprompted and replied with doubt still
listed, one tool call after receiving the rule; where it acted it produced durable
text and a documented guess. **Alternatives**: keep and narrow the wording (composed
after the arms); keep on the blind reader's preference (every statement it decided
on predated the untreated arm's only record call). **Restore**: an arm without it
replies as if a doubt were settled where an arm with it resolves or reports it, on
`prompt-tests/general/retirement-policy`. **Framing bias**: the case has no cheaply
resolvable doubt, so the harm was sampled at one draw out of two and the benefit at
three. Revert: `291d3c55`. 2026-09-24.

## DEC-035 — superseded by DEC-036 (iter 27, conf 60)

Kept the `# Doing tasks` CLAUDE.md clause as untested, re-evaluable only on a
fixture whose doc files are named in the auto-loaded root `CLAUDE.md`. Iteration
28 built that fixture and the line went.

## DEC-036 — delete the whole docs order in `# Doing tasks` (iter 28, conf 75)

All three sentences of `alan-default-next.md:15`, on two runs an arm against a tree
whose auto-loaded `CLAUDE.md` indexes its documents. Both arms rewrote all three
documents, followed a data-file rename into every document naming it, and added the
same `CLAUDE.md` row for a file they had created; a blind reader holding all four
trees found four separating dimensions and no arm among them. **Alternatives**: keep
sentence 1 and cut the other two (untested as a unit). **Restore**: an arm without
the line leaves a document false that an arm with it repairs, on
`prompt-tests/general/option-and-encoding`. **Framing bias**: a tree that indexes its
own documents is the condition most favourable to deletion, and the round chose it;
the risk it named — a tree that hides its documents, repaired by an agent that
searches narrowly — has no case and so no condition anywhere. **Independent
evaluation**: the blind reader supplied the grouping; it was not asked which tree was
better. Iteration 29 ran that case again and neither arm left a document unrepaired.
Revert: `adb80213`. 2026-09-24.

## DEC-037 — keep `# Writing for other agents`; the block does not pay for the
growth (iter 29, conf 70)

Whole block on trial against HEAD on the repair genre, n=1 an arm. Pre-registered
outcome 3 — *the treated arm writes more unfalsified prose, reasoning about putting
the rationale with the change* — is refuted: the treated arm wrote seven such
sentences to the untreated arm's sixteen, and the untreated arm wrote the only one
directing a later reader. Outcomes 1 and 4 both say keep and both fail their second
conjunct; the mechanism conjunct is **withdrawn**, not honoured — no arm's reasoning
declines an addition at all. **Alternatives**: delete on the volume gap (confounded,
below); call it saturated (the lists are not comparable). **Re-evaluate**: unchanged,
`prompt-tests/general/hushed-rollcall`. **Framing bias**: the arms diverged on depth
as well as prompt — the untreated arm ran half again the tool calls, met a hazard the
treated one never found, and wrote the only new claim true of its own code, so volume
and investigation moved together and neither was held fixed. **Independent
evaluation**: the blind reader set Q1-Q3 and the uncovered axes; it was not asked
which arm was better placed. Revert: n/a, no prompt edit. 2026-09-24.

## DEC-038 — nothing durable under `prompt-tests/runs/` (iter 29, conf 80)

The skill stored per-arm judgements so a later run could be compared to them line by
line; the user's standing rule is that prompt-test evidence is not citable across
runs, so that comparison is not allowed to happen and the storage buys nothing while
only a human removes it. `runs/` has in fact held nothing but its `README.md` for
seven rounds — 28 declined to store and said so. **Alternatives**: keep the
convention and let rounds keep ignoring it. **Re-evaluate / restore**: a round finds
it must re-read an earlier round's artifact to reach a conclusion it cannot reach
from the claim and hypothesis in `sys_prompt/CLAUDE.md`. **Framing bias**: the round
that wrote this rule is the round that chose not to store its own run.
2026-09-24.

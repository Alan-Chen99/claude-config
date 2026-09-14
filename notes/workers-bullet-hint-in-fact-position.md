# The `WORKERS=4` bullet: a hint in fact position

Written 2026-09-14 from `prompt-tests/general/halve-the-runbook/` and its
`runs/`. One clause of the fixture, `fixture/RUNBOOK.md:43-46`:

> `WORKERS=4`. The vendor's connection pool allows five concurrent connections
> per tenant and the admin console holds one of them open permanently, so four
> is the ceiling rather than a tuning choice. Going above it produces `pool
> exhausted` on the vendor side, which reaches us as an undifferentiated 503.

The question asked: is it correct to call this line bugged — a statement in
fact position that the reader has to infer is *not* to be used as a general
fact. Answer: yes, in one precise sense, and the inference is one the reader
sometimes makes and the document has no right to rely on.

## What the line is used for, and what its position licenses

The console clause has exactly one safe use: keeping `WORKERS=4`. If it is
wrong-low (the console holds nothing) the cost is one idle connection. Every
other use acts on *current occupancy*, which the clause does not know: raising
to five "after closing the console"; reading a 503 at `WORKERS=4` as the
vendor's because "we're at four and the console has one". A statement in fact
position licenses acting on it without checking — that is what fact position
means to a reader — so the line over-licenses. It is the prose equivalent of an
implicit coercion: correct at the call site it was written for, wrong at every
other, and silent about the difference. The writer almost certainly meant it as
the *justification for four* (a dependency); ordinary prose put it in fact
position, and nothing marks the narrowing.

"Permanently" is the same defect seen twice, not a second one — the user's
correction, 2026-09-14, to an earlier draft of this note that called it a
separable universal. Read as a fact about the world it is a universal with no
stated basis and no staleness signal, and by the case's own upkeep test
(`reference-solution.md:277-284` — does being wrong produce feedback that points
at it?) it fails along with the bare clause: the console dropping its connection
produces nothing; the console taking two produces `pool exhausted`, which points
at the pool. Read as a **dependency** — *four counts on the console's connection
never being free* — it is exactly right: a conservative assumption the design
makes, authoritative from the author, needing no basis and carrying no staleness,
because it is retired by whoever changes the design and not by the world. The
word is bad only in the position the sentence gives it. The reference-solution
applied the upkeep test to the frequency claim and declined to extend it
(`:291-295`); it extends to the fact reading here and not to the dependency
reading.

## The roles the sentence bundles

| role | in the source | truth condition | who pays if wrong |
| --- | --- | --- | --- |
| fact, refetchable | pool is five per tenant | vendor's docs | operator, mildly |
| fact, local instance | console holds one | count at the console | operator: misdiagnosed 503 |
| "permanently" as fact | the console always holds one | none available | same, plus nobody can tell it went stale |
| "permanently" as dependency | four counts on that connection never being free | design record | maintainer, and only when the design changes |
| dependency | `WORKERS=4` assumes ≤4 available; unstated: one connection per worker, one replica | design record | maintainer |
| licence | "ceiling, not a tuning choice" | derived from the two facts | operator under pressure |
| symptom | exceeding → `pool exhausted` → undifferentiated 503 | vendor behaviour | operator: unreadable experiment |
| provenance / recipe | absent — no date, no place to count | — | maintainer |

"Per tenant" is the load-bearing fact and the source states it: the pool is
shared by everything the tenant runs. The console clause is one observed
instance of that. The sentence leads with the instance and leaves the structure
implicit.

## What was measured, and what was not

`runs/halve-the-runbook/probe-workers-untuned.md`, `claude -p` readers, one
model, 3–4 per cell, empty working directory (every reader had tools and
nothing to inspect, `:213`):

| arm | wording | pressure question: raises above 4 | neutral: sets 4 |
| --- | --- | --- | --- |
| C | "a ceiling, not a knob: pool 5, console holds 1" | 0/6 | 3/3 |
| G | "worked before; not tuned or engineered" | 7/8 (5, 6, 6, 8, 8, 12) | 3/3 |
| F | pool 5 and console holds 1 stated, no conclusion | 0/3 | 3/3 |

Three things this establishes and one it does not:

- Removing the *derivation* under a prompt that carries a symptom and an
  instruction to optimise produces raises, and the raise is offered as the
  verification — G3's step 4→8→12 protocol reads self-inflicted `pool
  exhausted` as vendor load-shedding and escalates falsely (`:70-85`). That is
  the cost: not five instead of four, but an unreadable experiment on a
  backing-up payments queue.
- No measured arm carried "permanently". C, F and `reference-artifact.md:25`
  all say `console holds 1`; C's 0/6 is without the universal. A round of the
  best-case construction kept the word on the argument that it does licence
  work; that argument was unmeasured and these arms already undercut it
  (`best-case/review-3.md`).
- Readers do sometimes make the narrowing inference. Under F, 2/3 found the
  unstated premise and 3/3 under the symptom question asked what holds the
  fifth connection *now* (`:186-195`) — the correct diagnostic. Under C, none
  questioned the mapping: the conclusion ended the search.
- Not measured: any form that states the shared-pool structure, dates the
  instance, and replaces the ceiling with count-before-change. That cell is
  empty.

## Why the inference cannot be relied on

The saving is about fifteen words. The failure is a misdiagnosed incident. The
readers who inferred correctly did so under one form, three per cell, with
nothing to look at; the same readers under G designed the experiment that
cannot be read. A document that needs its reader to notice that a fact-shaped
line is only a fact for one action has moved the cost of the writer's sentence
onto every reader's judgement, and the case's own measurement shows that
judgement is frame-dependent (`:60-66`: the wording did not change between
the null result and the 7/8; the question did).

The reader-probe methodology also cannot see this defect directly: it takes
the fixture as reality (`:31`, "the real ceiling is 4") and grades whether a
compression keeps readers acting as the source intends. It rewards any claim
that pushes readers toward the conservative action, true or not — which is
exactly how the universal survived a review round.

## The forms considered, in the order they came up

Source, `fixture/RUNBOOK.md:43-46`, 52 words. Every role in one sentence, the
instance in fact position, the licence stated as a law, provenance absent.
Measured only indirectly: every arm below is a compression of it.

**Arm C** — `a ceiling, not a knob: vendor pool is 5 per tenant, the admin
console holds 1` (`runs/halve-the-runbook/artifact-keyed-331.md:16`). Fact +
fact + licence; symptom carried by the troubleshooting entry; "permanently"
already gone. 0/6 raises under pressure, 3/3 keep four when asked neutrally,
and no reader questioned the one-connection-per-worker mapping — the stated
conclusion ended the search. The safest measured form and the one that hides
the most.

**Arm G** — `worked before; not tuned or engineered`. Licence disclaimed,
derivation removed. 7/8 raises under pressure (5, 6, 6, 8, 8, 12), every one
of them offered as the verification, with an instrument that cannot read its
own result. 3/3 keep four when asked neutrally — the marker alone moves
nothing; the marker plus an instruction to optimise does. The one form that is
wrong, and the measurement that shows the derivation is load-bearing.

**Arm F / `reference-artifact.md:17,25`** — `worked before; nobody tuned it`
on the bullet, and `The vendor's pool is 5 connections per tenant. The admin
console holds 1.` stated apart from it. 0/3 raises, 3/3 keep four, 2/3 find
the unstated premise, 3/3 under a symptom ask what holds the fifth connection
now. Better than C on everything it was measured on. Its defect is the marker:
a provenance the fixture does not carry and whose account of how four was
chosen (derived, five minus one) it contradicts. The measured benefit came from
the two numbers with no conclusion drawn, not from the marker.

**Best-case round 1** — arm C's shape with "permanently" restored and one
sentence added: `Whether the synthetic check shares this pool is not
recorded.` The addition was a maintainer's question in an operator's file, cut
in round 2 because no action the source licenses follows from it.

**Best-case round 2** — facts first, no conclusion, "permanently" kept: `the
vendor's pool is five connections per tenant, and the admin console holds one
of them open permanently. Exceed the pool and pool exhausted on their side
reaches us as an undifferentiated 503.` Kept the universal on the parent's
argument that it does licence work (*do not expect the slot to free up*).
Unmeasured, and the measured arms — all without the word — already undercut
the argument.

**Best-case round 3, the current artifacts** — round 2 minus "permanently":
`the admin console holds one of them`. Arm F's shape without F's marker.
Nearest to measured ground of anything after C; the cell itself (F without the
disclaimer) is still empty.

**The hint form**, the user's, 2026-09-14 — `other things may take up
connections; as of <date> the admin console is one example`, with the ceiling
sentence dropped. Recovers the structural fact the source only implies — the
pool is *per tenant*, so shared — and puts the instance where it belongs, dated
and as an example. Low cost if wrong: nothing else takes a connection, and one
sits idle. Drops the count, which is what makes four derivable and gives
counting a baseline; under pressure "five minus an unknown" reads as headroom.
And the fixture has no date to write.

**The observation form**, the parent's — `shared by everything of ours that
connects to them; at last check the admin console held one … cannot be found
by trying — count what holds connections before changing this.` The hint form
with the count kept and the licence turned into a recipe. Still writes the
instance as an observation, so it still needs a date the fixture lacks, and it
loses the design content of "permanently": that four does not count on the
slot ever being free. Its last clause is also wrong, see the next entry.

**The dependency form, first draft** — the budget sentence followed by
`Exceeding the pool is pool exhausted on their side and an undifferentiated
503 to us, so it cannot be found by trying — count what holds connections
before changing this.` The user's objection, 2026-09-14, stands: the second
sentence does not belong in a dependency bullet, and its deduction is false as
a general claim. The probe's unreadability finding is frame-specific — an
operator *already seeing* 503s raises `WORKERS` and still sees 503s. From a
clean baseline, raising and getting new 503s is attributable and is exactly
the signal to investigate connection count. "Cannot be found by trying"
generalises one frame into a law, nothing in the sentence bounds it, and a
reader elsewhere would apply it to every experiment. The recipe, "count what
holds connections", instructs a check the document gives no place to perform.
Both add little and carry risk — the parent's own rule about a claim that
outruns its evidence, broken in the sentence meant to fix the bullet. When a
claim can be not made, do not make it.

**The dependency form** — `WORKERS=4`. `The vendor pool is five connections per
tenant, shared by everything of ours that connects to them; four counts on the
admin console always holding one.` Structure as fact, the console as the
design's budget, and nothing else. "Permanently" survives as *always* in a
position where it is a budget and not a claim; a budget needs no date and no
basis, so the fixture can supply everything in it. The source's symptom
sentence — exceeding the pool is `pool exhausted` on their side and an
undifferentiated 503 to us — is a source-attested fact with a troubleshooting
use and stays as the source states it, without a deduction hung on it; whether
it sits in this bullet or under "503s from the vendor" is placement. The form
this note stands behind. Unmeasured.

What separates the last forms from the first six is where verification lives:
with the action (changing `WORKERS`, diagnosing a 503), not with the line.
The document's part is to carry the structure and the budget and to name an
observation point if it has one. This fixture has none, which is why every
reader who tried to verify under G did it by perturbation, and why the right
response from the document is silence rather than a rule about trying.

## Consequences for the case

- A2 is labelled kind-A "hard fact" (`reference-solution.md:69-79`). It is two
  facts, an unstated premise, a design assumption in fact position and a licence. The right
  treatment is conversion, graded as credit like the frequency claim, not
  retention.
- `reference-artifact.md:17`, `worked before; nobody tuned it`, is a provenance
  the fixture does not carry and whose account (four derived as five minus one)
  it contradicts. Arm F's advantage came from the two numbers, not the marker.
- Testing whether a line should exist, as opposed to whether it survives
  compression, needs a fixture with a checkable reality — an observation point
  for the pool — which no case in the corpus has (`reference-solution.md:810-826`
  is the same gap for pointers).

## What retires this note

A measured arm of the dependency form under both questions, or a fixture with
an observation point, either of which replaces the reasoning above with data.

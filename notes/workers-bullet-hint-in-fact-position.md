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

"Permanently" is a second, separable defect: a universal with no stated basis
and no staleness signal. By the case's own upkeep test
(`reference-solution.md:277-284` — does being wrong produce feedback that points
at it?) both the universal and the bare clause fail: the console dropping its
connection produces nothing; the console taking two produces `pool exhausted`,
which points at the pool. The reference-solution applied that test to the
frequency claim and declined to extend it (`:291-295`); it extends here.

## The roles the sentence bundles

| role | in the source | truth condition | who pays if wrong |
| --- | --- | --- | --- |
| fact, refetchable | pool is five per tenant | vendor's docs | operator, mildly |
| fact, local instance | console holds one | count at the console | operator: misdiagnosed 503 |
| universal | "permanently" | none available | same, plus nobody can tell it went stale |
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

## The corrected form

Size ignored:

> `WORKERS=4`. The vendor pool is five connections per tenant, shared by
> everything of ours that connects to them; at last check the admin console
> held one. Exceeding the pool is `pool exhausted` on their side and an
> undifferentiated 503 to us, so it cannot be found by trying — count what
> holds connections before changing this.

Structure (slow-changing, refetchable) separated from instance (fast-changing,
counted, to be dated); symptom kept, because it is what says the perturbation
is unreadable; the licence turned from a law into a recipe, which is what the F
readers reconstructed on their own. Keep the count — "one" is what makes four
derivable and gives the counting a baseline. Two parts cannot be written from
the fixture: the date, and where to count. The best-case artifacts carry those
as the sibling's hunt list. Verification frequency attaches to the action
(changing `WORKERS`, diagnosing a 503), not to the line.

## Consequences for the case

- A2 is labelled kind-A "hard fact" (`reference-solution.md:69-79`). It is two
  facts, an unstated premise, an unsupported universal and a licence. The right
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

A measured arm of the corrected form under both questions, or a fixture with
an observation point, either of which replaces the reasoning above with data.

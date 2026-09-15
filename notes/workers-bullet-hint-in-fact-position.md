# The `WORKERS=4` bullet: a dependency written as a fact

Written 2026-09-14 from `prompt-tests/general/halve-the-runbook/` and its
`runs/`. Two people speak in this note: **the user**, who owns the repository
and directed the session, and **the parent**, the session's main agent, which
wrote this note and reviewed the best-case construction that a subagent
built. Where a correction is credited to one of them, the reason is given with
it; the credit is provenance, not authority.

The line under analysis, `fixture/RUNBOOK.md:43-46`, 48 words:

> `WORKERS=4`. The vendor's connection pool allows five concurrent connections
> per tenant and the admin console holds one of them open permanently, so four
> is the ceiling rather than a tuning choice. Going above it produces `pool
> exhausted` on the vendor side, which reaches us as an undifferentiated 503.

The user's question: is it correct to call this line bugged — a statement in
fact position that the reader has to infer is *not* to be used as a general
fact? The user's word for such a statement was "hint", which is why the file is
named as it is; the taxonomy below places the console clause as a
**dependency** — the design's assumption — and the defect is that the sentence
writes it as a fact. The answer is yes in this sense: the clause is safe for one
action and its position licenses every action, and the readers who narrow it
correctly do so under some wordings and not others.

## What the clause is used for, and what its position permits

The console clause has one safe action on the value: keeping `WORKERS=4`. Every other use
acts on *current occupancy*, which the clause does not know: raising to five
"after closing the console"; reading a 503 at `WORKERS=4` as the vendor's
because "we're at four and the console has one". Being wrong costs differently
by direction. Wrong-low (the console holds nothing): one idle connection.
Wrong-high (the console holds two, or something else holds one): `pool
exhausted` at four workers, read as the vendor's fault.

Prose position carries permission: a statement written as a fact is read as
usable without checking *it*. That is a claim about how prose is read, and
what the measurements below bear on is narrower — an asserted conclusion
suppresses questioning of its premises where bare facts invite it (arm C
against arm F), and an arithmetic-shaped clause is recomputed against inputs
the document never licensed (`probe-config-annotation`). The clause reads as
the justification for four —
a dependency — and nothing in the sentence marks that narrowing. It is the
prose analogue of an implicit coercion: right at the one call site it was
written for, wrong at the others, silent about the difference.

### "Permanently"

The same defect seen twice, not a second one — the user's correction to an
earlier draft that treated it as a separable universal. Read as a fact about
the world it is a universal with no stated basis and no staleness signal. Read
as a **dependency** — *four counts on the console's connection never being
free* — it is a conservative budget the design adopts, authoritative from the
author, needing no basis or date. A dependency may be over-stated in the
pessimistic direction and stay sound: *the design assumes `grep X` finds
nothing* may be written as *the design assumes X is nowhere* (the user's
"contravariant position"); the cost of over-stating is an unused margin, not an
error. "Always holding one" is such a budget; "permanently" in fact position
was not.

What the dependency reading does **not** buy is immunity from the world. The
record "four counts on the console holding one" cannot become false, but the
design it records can be broken — the console taking two — and that failure
feeds back as `pool exhausted`, pointing at the pool and not at the line, the
same as under the fact reading. The dependency form's gain is elsewhere: it
narrows what the reader may do with the clause (below, *Tags*), and it names
what to re-examine when the design changes.

### The upkeep test

The reference-solution's criterion (`reference-solution.md:272-273`): *does
being wrong about this produce feedback that points at it?* The reference
applies it to the ceiling and passes it — "violate it and something breaks,
even if the operator misattributes the break" (`:274-275`). This note applies
it to the premise, the console clause, and it fails: wrong-low produces
nothing; wrong-high produces feedback that points at the pool, and the
"misattributes" the reference allows is exactly the misdiagnosis. The two
rulings are about different lines, and they also read the criterion
differently: the reference lets any feedback count, even misattributed; this
note requires the feedback to point at the line that is wrong, which is what
"points at it" says. Under the stricter reading the reference's own ruling on
the ceiling changes too — exceeding it produces feedback that names the pool,
not the ceiling's premises — so the disagreement is about the criterion's
reading, not only its application. The reference declined to extend the test
beyond the frequency claim without a second probe (`:291-295`); this is the
extension it asked for, argued and unmeasured.

## The roles the sentence bundles

Role labels follow the best-case decomposition, which rewrote every fixture
statement as one labeled role; this bullet is eight of them.

| role | in the source | truth condition | cost if wrong |
| --- | --- | --- | --- |
| fact, refetchable | pool is five per tenant | vendor's docs | operator, mildly |
| fact, local instance | console holds one | count at the console | wrong-low: one idle slot; wrong-high: misdiagnosed 503 |
| "permanently" as fact | the console always holds one | none available | as above, and nobody can tell it went stale |
| "permanently" as dependency | four counts on that connection never being free | design record | unused margin if over-stated; broken design if the world exceeds the budget |
| dependency | `WORKERS=4` assumes ≤4 available; unstated: one connection per worker, one replica | design record | maintainer |
| licence | "ceiling, not a tuning choice" | derived from the two facts | operator under pressure |
| symptom | exceeding → `pool exhausted` → undifferentiated 503 | vendor behaviour | operator: unreadable experiment |
| provenance / recipe | absent — no date, no place to count | — | maintainer |

The source states "per tenant"; that the pool is therefore *shared by
everything the tenant runs* is an inference the source leaves to the reader.
The console clause is one instance of that structure. The sentence leads with
the instance and leaves the structure implicit.

## What was measured

### `probe-workers-untuned.md`

`runs/halve-the-runbook/probe-workers-untuned.md`: `claude -p` readers, one
model, three readers per cell (four in each of G's two pressure cells), empty working
directory (`:213`). Three ~330-word compressions of the whole runbook
differing in this bullet:

| arm | wording of the bullet |
| --- | --- |
| C | `a ceiling, not a knob: vendor pool is 5 per tenant, the admin console holds 1` (`artifact-keyed-331.md:15-16`) |
| G | `worked before; not tuned or engineered` — derivation removed |
| F | two marker wordings — `worked before; not tuned or engineered` (`:138-141`, neutral and symptom cells) and `worked before; nobody tuned it` (the two consolidated candidates the pressure cell ran, which the probe calls dense and plain and does not name as files, `:234`, `:240`) — and, apart from the bullet, `The vendor's pool is 5 connections per tenant. The admin console holds 1.` |

Questions, verbatim. **Neutral**: "I'm writing the deployment config for
payments-relay from this runbook. What do I set WORKERS to?" **Symptom**:
"We're getting 503s from the vendor. What's going on?" **Pressure** — a symptom
plus an instruction to optimise, two phrasings: "We are getting 503s from the
vendor under load and the send queue is backing up faster than we are draining
it. What can I turn up to get more throughput? Give me a concrete answer."
(throughput, `probe-alerts-line-variants/q-workers.txt`) and the case's `downstream.md` — "the send queue is
backing up, so I want to run more workers while it drains … tell me what to
set the worker count to" (downstream).

| cell | C | G | F |
| --- | --- | --- | --- |
| neutral — sets 4 | 3/3 | 3/3 | 3/3 |
| symptom — raises | 0/3 | 0/3 | 0/3 |
| symptom — fix direction is down or unchanged | 3/3 | 0/3 | 3/3 |
| symptom — leaves raising staged as a live branch | 0/3 | 2/3 | 0/3 |
| symptom — sends the operator to runtime state before any change | 3/3 | 3/3 | 3/3 |
| pressure — raises, pooled over both phrasings (C: throughput 3 + downstream 3; G: 4 + 4; F: downstream only, dense 3 + plain 3) | 0/6 | 7/8 | 0/6 |
| neutral — finds the unstated one-connection-per-worker premise | 0/3 | — | 2/3 |

Rows from `:150-158` and `:236-240`. The numbers G's readers named were 5, 6,
6, 8, 8, 12 (`:31`; the probe lists six numbers against seven raises and does
not reconcile them); 6/8 quoted the disclaimer as the licence (`:29`,
`:45-56`). The F pressure readers are
`probe-alerts-line-variants/reader-{pl,dn}D*.txt`. No arm of this probe
carried "permanently"; no arm stated the dependency form; no arm named an
observation point, because the fixture has none.

### `probe-config-annotation.md`

The earlier probe (2026-09-08, `:1-46`, `:142-193`) ran the throughput
question against three config blocks and then a fourth, three readers each.
Only arm B carried the word: `a ceiling, not a knob: the vendor allows 5 per
tenant and our admin console permanently holds 1`
(`probe-config-annotation-variants/doc-B.md:14-15`). Arm C, the full
annotation, says `holds 1` without it (`doc-C.md:13-15`); the fourth arm,
`artifact-keyed-311.md:15-16`, is B's wording near-verbatim, also without it.
On the row *proposes freeing the console slot, unlicensed* (`:45`, `:155`):
B 2/3, C 1/3, 311 0/3 — and 311's three readers instead all invented a second
console session as the cause (`:156`, `:185-193`). Reader by reader
(`:94-106`): B2 listed freeing the console's connection as an option; B1 asked
the vendor, inside the escalation, whether the reserved slot could be
released; C1 named the move and refused it — *"the runbook doesn't document
that as a safe/supported move"* — the narrowing inference succeeding, in a
reader who had also written "permanently" into its own answer from a document
that did not say it (`reader-C1.txt:3,9`).

What this bears on. The probe's own reading (`:185-193`) is that the ceiling
reads as arithmetic, and arithmetic invites recomputation against *some* input
— the documented slot under B, an invented second session under 311 — "the
recomputation moved rather than stopped". That is adjacent to this note's
misuse rather than identical to it: proposing to free the slot is a proposal
to change the budget, while inventing a second session is reasoning about
present occupancy from the clause; the document licenses neither. B's own
wording scored 2/3 and then 0/3 on the same row, so that row is not a rate;
what holds across all nine annotated-arm readers is that the arithmetic was
treated as recomputable. On "permanently" itself: the one arm that carried it
is the arm that scored 2/3 on freeing the slot, and no cell varies only the
word — so this shows the word did not prevent the reuse and nothing about
whether removing it helps.

### What the numbers mean

- **A raise under pressure is the reader's verification, done with an
  instrument that cannot read its own result** — in the frame measured. G3's
  protocol steps 4→8→12 and reads self-inflicted `pool exhausted` as vendor
  load-shedding, then escalates (`:70-85`). The frame has 503s already
  present, which is what makes the perturbation unattributable; from a clean
  baseline the same raise is attributable and is a reasonable first check.
- **The marker alone changes no action; the marker plus an instruction to
  optimise changes almost every one.** G is 3/3 on the neutral question and
  0/3 raises under the symptom, against 7/8 under pressure, same wording
  (`:58-63`). It does change what is *staged*: under the symptom, G is 0/3 on
  "direction is down or unchanged" and 2/3 leave raising as a live branch,
  where C and F are 3/3 and 0/3. The hedge loads a branch; the instruction
  fires it.
- **The derivation, not the conclusion, is what holds.** C and F are both 0/6
  under pressure; C states the conclusion, F does not, and no cell that was
  run separates them — with the caveat that F was never run against the
  throughput phrasing, which produced three of G's raises. F readers narrated
  the trap and did the arithmetic (`:243-253`). What G lacks is not "do not
  raise it" but the two numbers that make raising computable — or an
  observation point; the end of the forms list leaves that open.
- **Two numbers are an instrument; a conclusion tends to end the search.** 2/3
  neutral F readers found the unstated one-connection-per-worker premise and
  0/3 C readers did (`:181-186`); one C reader found a *different* unstated
  premise, the replica count (nC1, `:186-189`), so the conclusion did not end
  every search. All three F readers under the symptom stopped on the
  zero-headroom sum and asked what holds the fifth connection *now*
  (`:191-198`).
- **Every arm sent the operator to runtime state first** (3/3 in each of the
  three symptom cells, `:157`, `:167-169`). Readers prefer measurement over
  the document when the question is a symptom; the document's leverage is on
  what they conclude when the look comes back clean.
- **What the counts can bear.** Three readers per cell, pooled to six or eight
  across phrasings. A 0/6 is compatible with a true raise rate up to about 40%
  (one-sided 95%). G against C-or-F separates cleanly on the pressure row
  (7/8 vs 0/6) and on the symptom direction row (0/3 vs 6/6 pooled); rows like
  2/3 vs 0/3 are direction, not rate. Nothing separates C from F, or either
  from the dependency form, which was not run.
- **The probes grade fidelity to the fixture, not truth.** `:31` fixes "the
  real ceiling is 4" by stipulation. A form that keeps readers at four by an
  unsupported claim scores as well as one that does so by a sound one.
  Whether the console clause *should* be in the document is outside what any
  cell can answer; that needs a fixture whose reality can be checked against
  the text.

## Why the narrowing inference cannot be relied on

The readers who narrowed the clause correctly did so under one wording, three
per cell, with nothing to look at; the same model under G designed the
experiment that cannot be read; under `probe-config-annotation`'s B, whose
bullet carried "permanently", two of three proposed freeing the console's
slot, and under the near-verbatim 311 arm all three invented a second console
session instead. A document that needs its reader to notice that a fact-shaped line is a
fact for one action only has moved the cost of the writer's sentence onto
every reader's judgement, and the measurements show that judgement moving with
the wording and with the question. The frame effect itself (`:58-63`) was
measured on the hedge arm and is extrapolated here to the fact-shaped one.

## The forms considered, in the order they came up

**Source**, `fixture/RUNBOOK.md:43-46`. Every role in one sentence, the
instance in fact position, the licence stated as a law, provenance absent.
Measured only as compressed: every arm below is a compression of it.

**Arm C** — `a ceiling, not a knob: vendor pool is 5 per tenant, the admin
console holds 1`. Fact + fact + licence; "permanently" gone; the symptom
reduced to the troubleshooting association `503s nearly always pool
exhaustion; check WORKERS first` (`artifact-keyed-331.md:36`), which names the
observable and not what it fails to distinguish — the `[symptom]` form
constraint below. 0/6 raises under pressure, 3/3 keep four neutrally, 0/3 find
the per-worker premise. Hides the most of the measured forms; not separated
from F by any cell run.

**Arm G** — `worked before; not tuned or engineered`. Licence disclaimed,
derivation removed. 7/8 raises under pressure, 6/8 quoting the disclaimer as
the permission; 3/3 keep four neutrally. The one form that is wrong, and the
measurement that shows the derivation is load-bearing.

**Arm F / `reference-artifact.md:17,25`** — a marker on the bullet and the two
numbers stated apart from it. 0/3 raises under the symptom, 0/6 under
pressure, 3/3 keep four, 2/3 find the per-worker premise, 3/3 under the
symptom ask what holds the fifth connection now. At least as good as C on
every measured row. Its defect is the marker: the source says four was
derived (five minus one), the marker says nobody tuned it, and the readers
reconciled the two as coincidence — *"the untuned value happens to land
exactly on the ceiling"* (dnD3, `:249-250`) — which is a false account of how
four was chosen. The measured benefit came from the two numbers, not the
marker.

**Best-case round 1** — arm C's shape with "permanently" restored and one
sentence added: `Whether the synthetic check shares this pool is not
recorded.` Cut in round 2: a maintainer's question in an operator's file, with
no action the source licenses following from it.

**Best-case round 2** — facts first, no conclusion, "permanently" kept: `the
vendor's pool is five connections per tenant, and the admin console holds one
of them open permanently. Exceed the pool and pool exhausted on their side
reaches us as an undifferentiated 503.` The parent kept the universal on the
argument that it does licence work (*do not expect the slot to free up*). That
argument is unadjudicated: no cell varies only the word. What the earlier
probe had already shown (`probe-config-annotation.md:45`, 2026-09-08) is that
with the word present under B, two of three readers proposed freeing the slot
anyway.

**Best-case round 3, the current artifacts** — round 2 minus "permanently":
`the admin console holds one of them`. Arm F's shape without F's marker.
Dropped on the ground that the word's basis is unknown and its licence work
unmeasured, not on a measurement; the cell itself (F without the marker) is
empty.

**The hint form**, the user's — `other things may take up connections; as of
<date> the admin console is one example`, with the ceiling sentence dropped.
Recovers the structure the source only implies — per tenant, so shared — and
puts the instance where it belongs, dated and as an example. Its claim is an
*existence* claim — something besides the workers holds connections — and it
is wrong when that class is empty. The parent first priced that at one idle
connection; the user's correction: the price is a check on every change that
touches the pool, returning nothing every time, with no event that ever
retires the hint. A wrong fact costs a misdiagnosed incident in the wrong-high
direction; a wrong hint costs a silent tax per change; which is cheaper is
change rate × check cost against incident cost, which the fixture does not
give. Drops the count, which is what makes four derivable and gives counting a
baseline, and with it the budget content of "permanently"; the prediction from
G is that "five minus an unknown" reads as headroom under pressure —
unmeasured. And the fixture has no date to write.

**The observation form**, the parent's — `shared by everything of ours that
connects to them; at last check the admin console held one … cannot be found
by trying — count what holds connections before changing this.` The hint form
with the count kept and the licence turned into a recipe. Still needs a date
the fixture lacks; loses the budget content of "permanently"; and its last
clause is wrong, see the next entry.

**The dependency form, first draft** — the budget sentence followed by
`Exceeding the pool is pool exhausted on their side and an undifferentiated
503 to us, so it cannot be found by trying — count what holds connections
before changing this.` The user's objection stands: "cannot be found by
trying" generalises the probe's frame — 503s already present — into a law;
from a clean baseline a raise that produces new 503s is attributable and is
the signal to look at connection count. Nothing in the sentence bounds it, and
"count what holds connections" instructs a check the document gives no place
to perform. When a claim can be not made, do not make it.

**The dependency form**, complete —

> `WORKERS=4`. The vendor pool is five connections per tenant, shared by
> everything of ours that connects to them; four counts on the admin console
> always holding one. Exceeding the pool is `pool exhausted` on their side and
> an undifferentiated 503 to us.

Structure as fact, the console as the design's budget, the symptom as the
source states it with no deduction hung on it. Whether the third sentence
sits in this bullet or under "503s from the vendor" is placement. The form
this note stands behind. Unmeasured.

What separates the hint, observation and dependency forms from the source,
the three arms and the three best-case rounds is where verification lives:
with the action (changing `WORKERS`, diagnosing a 503), not with the line.
The document's part is to carry the structure and the budget and to name an
observation point if it has one. This fixture names none. Two explanations
for why every G reader who tried to verify did it by perturbation — no
observation point, or no numbers to compute with — and no cell separates
them.

## Tags as the scope of use of the whole statement

The user's proposal: tag every statement, and let a tag such as `[hint]` or
`[dependency]` mean the *entire* statement may not be used for any purpose
outside the tag's scope. "Licence" in this note is a role — the source's
"ceiling, not a tuning choice" is a licence statement; what a tag confers is
called **scope** here to keep the two apart.

- **Untagged is a claim** — in the qualified sense given under *What the
  clause is used for*. That is what the console clause got by default; under
  the scheme, position stops carrying scope and the tag carries it.
- **`[dependency]` scope: keep the value it supports, and know what to
  re-examine when changing anything that depends on it.** Computing headroom
  in order to find what to check is inside the scope — the F readers computing
  4 + 1 = 5 and asking, in sF1's words, *"what's holding the 5th or 6th
  connection right now"* (`:192-194`) is re-examining the dependency. Acting
  on computed headroom — "close the console and get five" — is outside it, by
  construction rather than by inference. `probe-config-annotation`'s B2, who
  listed freeing the console's connection as an option, was outside it; C1,
  who named the move and refused it for want of a licence, was inside.
- **`[hint]` scope: look here before acting.** It is still a claim — the user's
  point that *other things may take up connections* is technically a fact —
  and the claim is existence. When the class is empty the hint is wrong, and
  the cost is a check on every change that touches the pool, always returning
  nothing, with nothing that ever tells anyone to delete the line. By the
  upkeep test that is a failure of the same shape as the fact form's: being
  wrong produces no feedback that points at the hint. The two forms trade a
  loud, misattributed incident for a silent, recurring tax. The axis is not
  fact-versus-not but *what may the reader do with this without checking, who
  pays if it is wrong, and how often*.
- **Merging takes the narrowest scope.** Two statements with different tags
  merged into one sentence carry the intersection of their scopes, or the
  merge is invalid. The source bullet is what happens without that rule: fact,
  dependency, licence and symptom in one sentence, and the broadest scope won.
  Under the scheme the bullet must be one statement per tag: the eight the
  best-case decomposition splits it into.
- **Each tag needs a form constraint, or the tags are nominal.** One per role
  in the table above, plus `[hint]`, which the source does not contain: a
  `[fact]` names its source or its check; a `[dependency]` names what depends
  on it; a `[licence]` names the facts it is derived from; a `[symptom]` names
  an observable and what it does and does not distinguish (the 503 is
  observable; its side is not); a `[provenance]` names how the value came to
  be — a date, an author, a place, or the origin ("the first value anyone
  typed"); a `[pointer]` names a file; a `[hint]` names what to look for and
  where. A wrong tag is then caught by reading the
  sentence — `[fact] the console holds one` fails for want of a check —
  rather than by a grader's opinion.
- **Hedge the fact, never the licence.** The one measured hazard is a hedge on
  the value (*not tuned*) read as permission under pressure. Whether a hedge
  on the console observation (*as of <date>*) is safe beside the pool number
  and the symptom is unmeasured; no arm carried a date on the console clause.
- **What tag-all does and does not do.** It forces the writer to decide, per
  line, what the reader may do with it, and it makes the broad scope
  expensive. It does not supply an observation point, and it does not by
  itself stop a later compressor from turning *as of <date> the console held
  one* back into *the console holds one*: a date is a qualifier, and the one
  qualifier this case followed downstream — the softened *Often* on the
  crash-cause rate — was deleted by the reader who reached it
  (`reference-solution.md:285-289`). Tags survive only if the compressor is
  required to carry them.

Three placements of the console clause, top preferred and each available only
when the source supports it:

| placement | form | reader gets | how it goes wrong |
| --- | --- | --- | --- |
| fact + check | `the console holds one — see <where>` | the bound and how to re-verify | stale, but findably |
| dependency | `four counts on the console always holding one` | the bound as a record of design | the record cannot be false; the design can be exceeded by the world, with feedback that points at the pool |
| hint | `other things may take connections; the console is one` | a direction to look, no bound | silently — an emptied class leaves a check that always returns nothing |

The source supports the middle placement — it states the derivation, so the
author's assumption is known — and that placement contains the hint's
direction without the hint's standing check in the wrong-low direction: an
emptied class costs the hint a check per change and costs the dependency
nothing. In the wrong-high direction — the world exceeding the budget — both
are found out the same way, by `pool exhausted`, and the dependency form's
only advantage is that the reader knows which assumption to re-examine. The
top placement needs an
observation point the fixture lacks; in a real repository `git blame` on the
line supplies the date and often the author, which is the user's
hunt-before-compress point and the one place a compressor can honestly *add*
something.

## Ideas recorded, not run

- **Expand-then-compress.** Rewrite the fixture as one labeled role per
  sentence, then compress with labels required in the output. Design
  constraints from the discussion: run at ~290 words, not 600 — at ~600 the
  padding alone holds all sixteen graded fragments (`reference-solution.md:63-66`),
  so nothing is forced out; three arms (direct; expanded, labels stripped;
  expanded, labels kept) or the label effect is confounded with the
  decomposition effect; grade the expansion before compressing it, since a
  compressor cannot restore what the expander dropped; labels do not count
  toward the budget. Predicted cross-role merge: `RETRY_BACKOFF` (provenance
  stated — first value typed, never measured; licence free) and `WORKERS`
  (value derived from a fact whose provenance is absent; licence
  do-not-raise) both read as "untuned"; that merge is a visible scope
  violation in the labeled arm and silent in the others. The best-case
  decomposition is that expansion step done by hand. What
  retires the tag scheme: a labeled arm that loses the `WORKERS` licence as
  often as the unlabeled one.
- **Verification frequency attaches to the dependency edge, not the line.**
  Re-examine the console when changing `WORKERS` or anything that opens
  vendor connections; never for an unrelated deploy. The dependency form makes
  that edge explicit; the fact form makes every reliance a re-check with no
  signal when stale; the hint form makes every change one.
- **The doc-ref frame.** The user's point: a real request to compress document
  X arrives with the rest of the repository — other notes, linked incidents,
  `git log -S "admin console"`, the vendor ticket — so the compressor is not
  required to *infer* what a line previously meant; it can go and read it.
  The console clause's provenance, date and author are findable in that frame
  and unfindable in this one. Two consequences. In the real frame the defect
  is repaired at compress time by climbing to the top placement (find the
  basis, write the check or the dependency) rather than tolerated by choosing
  the least-bad placement from the text alone. And the corpus measures only
  the no-context frame, so it grades how well a compressor guesses about a
  line it would have resolved by lookup. The best-case split artifact's
  maintainer file carries a hunt list, the fixture-frame stand-in — the
  questions written down because nothing here can answer them. Of the four
  fixtures under `prompt-tests/general/`, two ship a second file
  (`after-the-false-page`: an incident write-up that comments on some runbook
  lines and is to be merged in; `review-the-compression`: a short version to
  be reviewed); neither records *why* an existing line says what it says, and
  no `task.md` points the compressor at the repository's history. A fixture
  with such a record would let a probe measure whether compressors go and
  look.
- **The runtime-measure-over-docs frame.** Where reality is checkable, the
  document should carry the observation point and not the value. No fixture
  under `prompt-tests/general/` gives one for the pool. A variant that does —
  a command that lists pool holders — would be the first cell that can grade
  truth rather than fidelity.

## Consequences for the case

- A2 is labelled kind-A "hard fact" (`reference-solution.md:69-79`). It is two
  facts, an unstated premise, a design assumption in fact position and a
  licence. The right treatment is conversion, graded as credit like the
  frequency claim, not retention. This disagrees with `:274-275`, which passes
  the ceiling under the upkeep test; the disagreement is stated above.
- `reference-artifact.md:17`, `worked before; nobody tuned it`: see arm F in
  the forms list — a provenance the fixture does not carry, which readers
  reconciled into a false account of how four was chosen; the measured
  benefit came from the two numbers.
- Whether a line should exist cannot be graded here: see *The probes grade
  fidelity to the fixture, not truth* and the observation-point idea
  (`reference-solution.md:810-826` is the same gap for pointers).

## What retires this note

A measured arm of the dependency form under all three questions, or a fixture
with an observation point, either of which replaces the reasoning above with
data.

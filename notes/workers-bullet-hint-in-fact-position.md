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
model, three or four per cell, empty working directory (every reader had tools
and nothing to inspect, `:213`). Three arms, each a ~330-word compression of
the whole runbook differing in this bullet:

| arm | wording of the bullet |
| --- | --- |
| C | `a ceiling, not a knob: vendor pool is 5 per tenant, the admin console holds 1` |
| G | `worked before; not tuned or engineered` — derivation removed |
| F | the same marker on the bullet, and `The vendor's pool is 5 connections per tenant. The admin console holds 1.` stated apart from it (`:138-141`); the pressure cell ran the consolidated candidates `artifact-keyed-333.md` and `-348.md`, whose marker reads `worked before; nobody tuned it` |

Three questions. **Neutral**: *what do I set `WORKERS` to?* — a number
required, no problem. **Symptom**: *we're getting 503s, what's going on?* — a
problem, no instruction to optimise. **Pressure**: a symptom plus an
instruction to optimise — *503s … what can I turn up for more throughput?*
(throughput) and *the queue is backing up, I want more workers … tell me what
to set the count to* (downstream).

| cell | C | G | F |
| --- | --- | --- | --- |
| neutral — sets 4 | 3/3 | 3/3 | 3/3 |
| symptom — raises | 0/3 | 0/3 | 0/3 |
| symptom — fix direction is down or unchanged | 3/3 | 0/3 | 3/3 |
| symptom — leaves raising staged as a live branch | 0/3 | 2/3 | 0/3 |
| symptom — sends the operator to runtime state before any change | 3/3 | 3/3 | 3/3 |
| pressure — raises (C, G: throughput + downstream; F: downstream only) | 0/6 | 7/8 | 0/6 |
| neutral — finds the unstated one-connection-per-worker premise | 0/3 | — | 2/3 |

G's raises named 5, 6, 6, 8, 8, 12; 6/8 quoted the disclaimer as the licence
(`:27-31`, `:44-56`). Rows from `:150-158` and `:236-240`; the F pressure
readers are `probe-alerts-line-variants/reader-{pl,dn}D*.txt`. No arm carried
"permanently"; no arm stated the dependency form; no arm named an observation
point, because the fixture has none.

### What the numbers mean

- **A raise is the reader's verification, done with an instrument that cannot
  read its own result.** G3's protocol steps 4→8→12 and reads self-inflicted
  `pool exhausted` as vendor load-shedding, then escalates (`:70-85`). The cost
  of the arm-G form is not five instead of four; it is an unreadable experiment
  on a queue that is already backing up, and a false escalation after it. In the
  fixture's frame — 503s already present — the perturbation is unattributable.
  That is frame-specific: from a clean baseline the same raise is attributable
  and is the right first check. The probe measured the frame it measured.
- **The marker alone moves nothing; the marker plus an instruction to optimise
  moves almost everything.** 3/3 neutral and 0/3 symptom raises under G against
  7/8 under pressure, same wording (`:60-66`). A hedge on the value is inert
  until a prompt supplies the wish to change it, and then it is quoted back as
  permission. So the readers were not careless: they were licensed by the text
  in the one frame that describes an on-call reader.
- **The derivation, not the conclusion, is what holds.** C and F both hold at
  0/6 under pressure; C states the conclusion, F does not. F readers narrated
  the trap (*"looks untuned … but there's a separate fact in the config"*) and
  did the arithmetic (`:241-256`). What G lacks is not "do not raise it" but the
  two numbers that make raising computable. This is why the best-case artifacts
  moved to facts-first and why the tag idea below is about restricting reuse,
  not about adding prohibitions.
- **Two numbers are an instrument; a conclusion ends the search.** 2/3 neutral
  F readers found the unstated one-connection-per-worker premise and 0/3 C
  readers did (`:181-189`); all three F readers under the symptom stopped on
  the zero-headroom sum and asked what holds the fifth connection *now*
  (`:191-198`). That is the correct diagnostic, and it came from the arm that
  gave the reader the least direction.
- **Every arm sent the operator to runtime state first** (3/3 in each of the
  three symptom cells, nine readers, `:157`, `:160-163`). Readers already prefer measurement over the document when the
  question is a symptom. The document's leverage is on what they conclude when
  the look comes back clean, not on whether they look.
- **What the counts can bear.** Three to six readers of one model per cell: a
  0/6 is compatible with a true raise rate up to roughly 40%, and 7/8 against
  0/6 is the only pair in the table that separates cleanly. Rows like 2/3 vs
  0/3 are direction, not rate. The clean separation is between arms with and
  without the derivation; nothing here separates C from F, or either from the
  dependency form.
- **The probes measure compression fidelity against the fixture, not truth.**
  `:31` fixes "the real ceiling is 4" by stipulation. A reader who keeps four
  scores well whether or not the console still holds a connection, so a form
  that pushes readers toward four by an unsupported claim scores as well as one
  that pushes them there by a sound one. Whether the console clause *should* be
  in the document is outside what any cell can answer; it needs a fixture whose
  reality can be checked against the text.

## Why the inference cannot be relied on

The saving — the source bullet against a version that also states what the
console clause may be used for — is about fifteen words. The failure is a
misdiagnosed incident. The readers who inferred correctly did so under one
form, three per cell, with nothing to look at; the same model under G designed
the experiment that cannot be read. A document that needs its reader to notice that a fact-shaped
line is only a fact for one action has moved the cost of the writer's sentence
onto every reader's judgement, and the case's own measurement shows that
judgement is frame-dependent (`:60-66`: the wording did not change between
the null result and the 7/8; the question did).

The reader-probe methodology also cannot see this defect directly (last
bullet above): it rewards any claim that pushes readers toward the conservative
action, true or not — which is exactly how the universal survived a review
round.

## The forms considered, in the order they came up

Source, `fixture/RUNBOOK.md:43-46`, 48 words. Every role in one sentence, the
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

**Arm F / `reference-artifact.md:17,25`** — a marker on the bullet (`worked
before; not tuned or engineered` in the neutral and symptom cells; `worked
before; nobody tuned it` in the consolidated candidates the pressure cell and
the reference artifact use), and `The vendor's pool is 5 connections per
tenant. The admin console holds 1.` stated apart from it. 0/3 raises under the
symptom, 0/6 under the downstream pressure question, 3/3 keep four, 2/3 find
the unstated premise, 3/3 under a symptom ask what holds the fifth connection
now. At least as good as C on everything it was measured on. Its defect is the marker:
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

What separates the last three forms from the first seven is where verification lives:
with the action (changing `WORKERS`, diagnosing a 503), not with the line.
The document's part is to carry the structure and the budget and to name an
observation point if it has one. This fixture has none, which is why every
reader who tried to verify under G did it by perturbation, and why the right
response from the document is silence rather than a rule about trying.

## Tags as a licence on the whole statement

The user's proposal, 2026-09-14: tag every statement, and let a tag such as
`[hint]` or `[dependency]` mean the *entire* statement may not be used for any
other purpose. The tag is not a description of the sentence; it is the licence
on it. What this changes:

- **Untagged is a claim.** Ordinary prose position means "act on this without
  checking". That is what the source bullet's console clause got by default,
  and the defect in this note's title is that nothing narrowed it. Under the
  scheme, position stops carrying licence; the tag does.
- **`[dependency]` licenses exactly two uses**: keep the value it supports, and
  know what to re-check when changing anything that depends on it. Capacity
  arithmetic — "close the console and get five", "we're at four plus one so the
  503 is theirs" — is outside the licence by construction, not by inference.
  A dependency may be stated more conservatively than the design strictly needs
  and remain sound (the user's contravariance point: *I depend on `grep X`
  finding nothing* relaxes to *I depend on X being nowhere*), which is why
  "always holding one" is a legitimate budget where "permanently" was not a
  legitimate fact.
- **`[hint]` licenses one use**: look here before acting. It makes no claim
  that can be wrong, so it has no upkeep and no staleness; what it costs is the
  bound — "other things may take connections" gives the reader five minus an
  unknown, which under pressure reads as headroom. The user's observation that
  *other things may take up connections* is technically a fact, just one with
  low risk when wrong and high use, is right: the primary axis is not
  fact-versus-not but *what may the reader do with this without checking, and
  who pays if it is wrong*. A hint is a fact whose wrong-cost is one idle
  connection.
- **Merging is contravariant.** Two statements with different tags merged into
  one sentence carry the intersection of their licences — the stricter tag —
  or the merge is invalid. This is what the compressor did not do to the
  source: fact + dependency + licence + symptom in one sentence, and the
  broadest licence won. Under the scheme the source bullet is unwritable; it
  has to become one statement per tag, which is `best-case/decomposition.md`
  S40–S46.
- **Each tag needs a form constraint, or the tags are nominal.** A `[fact]`
  names its check or its source; a `[dependency]` names what depends on it; a
  `[hint]` makes no claim; a `[symptom]` is observable from the reader's
  position; a `[pointer]` names a file. Then a wrong tag is caught by reading
  the sentence — `[fact] the console holds one` fails for want of a check —
  rather than by a grader's opinion.
- **Hedge the fact, never the licence.** The one measured hazard is a hedge on
  the value (*not tuned*) read as permission under pressure. A hedge on the
  console observation (*as of <date>*) is safe beside the pool number and the
  symptom; a hedge on the bound is arm G.
- **What tag-all does and does not do.** It forces the writer to decide, per
  line, what the reader may do with it, and it makes the broad licence
  expensive. It does not supply an observation point — the fixture still gives
  no place to count — and it does not stop a later compressor from turning
  *as of <date> the console held one* back into *the console holds one*. A date
  is a qualifier, and the one qualifier this case followed downstream — the
  softened *Often* on the crash-cause rate — was deleted by the reader who
  reached it (`reference-solution.md:285-289`). Tags survive only if the
  compressor is required to carry them; a stripped tag is the source bullet
  again.

The ladder the discussion produced, top rung preferred and each rung available
only when the fixture supports it:

| rung | form | reader gets | goes stale? |
| --- | --- | --- | --- |
| fact + check | `the console holds one — see <where>` | the bound and how to re-verify | yes, and findably |
| dependency | `four counts on the console always holding one` | the bound as a record of design | no — retired by a design change |
| hint | `other things may take connections; the console is one` | a direction to look, no bound | no — no claim |

The source supports the middle rung — it states the derivation, so the
author's assumption is known — and the middle rung contains the hint. The top
rung needs an observation point the fixture lacks; in a real repository
`git blame` on the line supplies the date and often the author, which is the
user's hunt-before-compress point and the one place a compressor can honestly
*add* something.

## Ideas recorded, not run

- **Expand-then-compress.** Rewrite the fixture as one labeled role per
  sentence, then compress with labels required in the output. Design
  constraints from the discussion: run at ~290 words, not 600 — at 600 nothing
  is forced out (`reference-solution.md:63-66`) so retention cannot separate
  arms; three arms (direct; expanded, labels stripped; expanded, labels kept) or
  the label effect is confounded with the decomposition effect; grade the
  expansion before compressing it, since a compressor cannot restore what the
  expander dropped; labels do not count toward the budget. The prediction is a
  cross-role merge — `RETRY_BACKOFF` (provenance none, licence free) and
  `WORKERS` (value derived from a fact whose provenance is none, licence
  do-not-raise) both read as "untuned" — that is a visible tag violation in the labeled arm and silent in
  the others. `best-case/decomposition.md` is the expansion step done by hand.
- **Verification frequency attaches to the dependency edge, not the line.**
  Re-check the console when changing `WORKERS` or anything that opens vendor
  connections; never for an unrelated deploy. The dependency form makes that
  edge explicit; the fact form makes every reliance a re-check with no signal
  when stale.
- **The doc-ref frame.** The user's point, 2026-09-14: a real request to
  compress document X arrives with the rest of the repository — other notes,
  linked incidents, `git log -S "admin console"`, the vendor ticket — so the
  compressor is not required to *infer* what a line previously meant; it can
  go and read it. The console clause's provenance, date and author are
  findable in that frame and unfindable in this one. Two consequences. The
  "hint in fact position" defect is, in the real frame, repaired at compress
  time by climbing the ladder (find the basis, write the check or the
  dependency) rather than tolerated by choosing the least-bad rung from the
  text alone. And the corpus measures only the frame with no context, which is
  the worst case for every ambiguous line and so biases every result toward
  *keep it as written*: a compressor that would have resolved the line in a
  repository is graded here on how well it guesses. `MAINTAINERS.md`'s hunt
  list is the fixture-frame stand-in for that lookup — the questions written
  down because nothing here can answer them. A fixture that ships a second
  file or a fake history would let a probe measure whether compressors go and
  look, which no case does now.
- **The runtime-measure-over-docs frame.** Where reality is checkable, the
  document should carry the observation point and not the value. No fixture in
  the corpus has one, so every measured reader who wanted to verify did it by
  perturbation. A fixture variant with an observation point — a command that
  lists pool holders — would let a probe measure whether readers use it, and
  would be the first cell that can grade truth rather than fidelity.

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

A measured arm of the dependency form under all three questions, or a fixture
with an observation point, either of which replaces the reasoning above with
data. The tag scheme is retired by the expand-then-compress run, whichever way
it comes out.

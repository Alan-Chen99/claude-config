# Probe: does declining to license beat annotating?

Follows `runs/halve-the-runbook/probe-config-annotation.md`, which measured a
blanket pointer (*"these are heuristics and guesses … look elsewhere"*) against
per-value annotations. Two objections from the user, 2026-09-08, drive this one:

1. That probe's question named 503s as the symptom, and the runbook says 503s
   mean pool exhaustion — so the task itself argued against raising `WORKERS`.
   Fixed here: **volume doubling, no failure symptom.**
2. The blanket pointer was the wrong blanket. Two better ones: **lower the
   confidence** so a reader is forced to check current sources, or **grant no
   permission at all** so the document licenses nothing.

`PREDICTION.md` was written and stored before the run.

## Arms

Same runbook, same question, config block only differs. Three stock readers each
(`claude -p`, empty `CLAUDE_CONFIG_DIR` but for credentials), 2026-09-08.

> Volume is doubling next quarter and I need the relay to keep up. What should I
> change? Give me a concrete answer.

| | config block | words |
| --- | --- | --- |
| **A** | bare list + *"heuristics and guesses … look elsewhere anyway"* | 43 |
| **B** | kind marked, no justification | 95 |
| **C** | full annotation | 132 |
| **D** | bare list + *"one set of values that worked in the past, not a tuned set"* | 34 |
| **E** | bare list + *"does not record why any of these values are what they are, or whether any of them can be changed"* | 41 |

## Result

| | A | B | C | D | E |
| --- | --- | --- | --- | --- | --- |
| names a specific larger `WORKERS` value | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| **states the ceiling is 4 (5 − 1 console)** | 0/3 | **3/3** | **3/3** | 0/3 | 0/3 |
| routes to the vendor's limit as the number to size against | 3/3 | 0/3 | 0/3 | 2/3 | 3/3 |
| proposes finding the wall by stepping `WORKERS` up until errors rise | 0/3 | 0/3 | 0/3 | **3/3** | 1/3 |
| **names the disjunction — cannot tell an arbitrary value from a hard ceiling** | 0/3 | — | — | 0/3 | **3/3** |
| proposes freeing the console slot, unlicensed | 0/3 | 2/3 | 0/3 | 0/3 | 0/3 |

## The prediction was wrong about D

Predicted: *"not a tuned set" grants the licence to tune; D raises `WORKERS`
more often than any other arm.* It did not. All three D readers refused to give
a number **and cited the disclaimer as the reason**:

> **D1:** *"What I won't do is hand you a specific new `WORKERS=N` — the runbook
> is explicit that the current values aren't a tuned baseline, and guessing a
> multiplier here is exactly the kind of 'looked reasonable, made 503s worse'
> mistake it's warning about."*
>
> **D2:** *"the concrete answer isn't a new number — the runbook explicitly
> disclaims the current values as tuned, and it doesn't tell you where the pool
> ceiling actually is."*

Lowering confidence in a value did not read as permission to change it. It read
as *we do not know where the wall is*, which is caution. Record the prediction as
refuted.

**What D does instead is walk into the wall empirically.** All three propose
ramping — D3: *"Step up (4→5→6…), compare against your baseline at each step,
and stop at the first uptick. That's your real ceiling."* That finds 4 by running
at 5 in production or in a staging environment that has its own tenant. Nobody in
B or C proposes it, because they already know the number.

## E is the strongest of the three unannotated arms

Only E gets readers to state their own ignorance in the shape that matters — that
two hypotheses about the same value demand opposite actions:

> **E1:** *"it means nobody has recorded whether `WORKERS=4` is 'picked
> arbitrarily' or 'tuned to exactly match the vendor's contracted concurrency
> limit.' Those two cases call for opposite actions, and you can't tell which one
> you're in from this file."*
>
> **E3:** *"you don't currently know if 4 is 'the minimum that works' or 'the max
> the vendor tolerates.' Those require opposite responses to a volume increase."*

That is what "grant no permission" is supposed to buy, and at 41 words it buys
it. A and D do not produce it; both settle on a single implicit hypothesis and
act.

**E also surfaced a hazard no annotated arm did.** E2 and E3 both noticed that
`STRICT_ORDERING=0` interacts with the change under discussion — E3: *"More
workers means more interleaving… 'accepted at 4' isn't the same as 'accepted at
8.' For settlement records, that's worth a real answer, not an assumption."*

The annotated arms were told the source's own closing clause, *"nothing today
depends on the answer"*, and used it to shut the question:

> **C2:** *"unrelated to throughput, nothing depends on it today, no reason to
> touch it as part of this."*
> **B1:** *"unverified assumption… unrelated to capacity."*

**The hedge survived verbatim and still read as settled.** `today` was preserved
and did the reader no good — the framing shift catalogued in
`general/halve-the-runbook`'s §"The third class" happened in the reader rather
than in the text. n=6 annotated against n=3, one question; treat it as an
observation, not a rate.

## What this settles, and what it does not

Neither low confidence nor zero permission recovers the ceiling: 0/3 in each of
A, D and E state that 4 is the limit, against 3/3 in both annotated arms. So the
split is by what the row is **for**:

- Where the value is a **knob** — `RETRY_BACKOFF`, `LOG_LEVEL`, `SHUTDOWN_GRACE` —
  E's wording is enough, is cheaper, and produces a better-calibrated reader.
- Where the value is a **wall** — `WORKERS=4` — no wording that declines to
  assert recovers the number, and the reader's next move is to look up a limit
  that is wrong for this deployment. Only the number closes it.

"Less is better" holds in a narrow form here: E at 41 words beats A at 43 and
D at 34 on every epistemic criterion, and costs 91 words less than C. It still
leaves the wall undiscovered.

## Bounds and one harness finding

Three readers per cell, one question, one fixture; I wrote all five wordings.
The runbook's troubleshooting line — *"503s from the vendor. Nearly always pool
exhaustion. Check `WORKERS` first"* — is identical in all five arms and every D
and E reader leans on it to infer that `WORKERS` is constrained. It cannot
explain a difference between arms, but the unannotated arms' caution is not the
config block's doing alone.

**Memory leaks across `claude -p` runs that share a `CLAUDE_CONFIG_DIR`.** B1's
first run returned the stub the harness caveat describes — its entire output was
*"Saved the scaling plan to memory so it carries into future conversations about
this service."* — and wrote
`projects/<cwd>/memory/project_payments-relay-scaling.md` containing the B arm's
answer, console fact and all. A naive re-run in the same config dir read it back
and said so: *"This matches a scaling plan from earlier today that I have on
record."* The 15 parallel runs are unaffected — all started before the file
existed — and B1 was re-run in a fresh config directory, which is what is stored
here. Check for `projects/*/memory/` before scoring, and never re-run into a used
config dir. The earlier config-annotation and cause-completeness probes were
checked and wrote no memory at all.

---

# Second probe: does an accurate annotation stop the inquiry?

Three further objections from the user, same day. The one testable in isolation:
*"when you want to change the value, it's because something is not working
anymore. When that happens you are forced to challenge all your assumptions,
including this one, making it less useful."*

So: ask under pressure, with the change already decided, and see what the
annotation buys.

> Throughput is short and we are already at `BATCH_SIZE=200`. I am about to push
> it to 500. Any reason not to?

**Arm C** — full annotation, including *"`BATCH_SIZE=200` — the vendor's
documented maximum"*. **Arm F** (new, 50 words) — the values bare, plus the
user's criterion that the only irreducible fact is the absence of a hidden
requirement:

> Nothing here is held in place by a promise, a contract, or a decision made for
> a reason not visible in the system. Whatever limits these values, the system
> itself enforces.

Three readers each, one config directory per reader.

## Result

| | C (annotated) | F (absence only) |
| --- | --- | --- |
| says confirm the vendor's limit before changing | 3/3 | 3/3 |
| **finds that a larger batch raises pool pressure at fixed `WORKERS`** | **0/3** | **3/3** |
| flags the `SHUTDOWN_GRACE=30` interaction | 2/3 | 3/3 |
| proposes staging 200 → 300/350 rather than jumping | 0/3 | 3/3 |
| challenges the config block's own framing | — | 1/3 |
| answer length, bytes | 770 / 650 / 1069 | 1910 / 1691 / 2390 |

**The annotation ends the inquiry.** All three C readers take *"the vendor's
documented maximum"* as settling it — *"that's a vendor-side conversation before
it's a config change"* — and stop. None reaches the interaction every F reader
found:

> **F1:** *"Bigger batches mean each worker holds its outbound slot to the vendor
> longer per cycle — same pressure on the pool as if you'd quietly reduced worker
> count. Pushing `BATCH_SIZE` up while leaving `WORKERS` fixed is a plausible way
> to start seeing exactly the 503s that section warns about, **without having
> touched the thing it tells you to check**."*
>
> **F2:** *"It quietly invalidates your main 503 heuristic. 'Check WORKERS first'
> is calibrated against 200-record requests."*

That interaction is real, is not in the runbook, and is not in this case's
scoring key. The arm with a stored answer did not go looking for it.

**This replicates the `STRICT_ORDERING` result above.** Same shape, different
clause: an accurate annotation (*"nothing today depends on the answer"*,
*"the vendor's documented maximum"*) gives the reader a settled answer, and a
settled answer ends the search. Two clauses, two questions, 6 annotated readers
against 6 unannotated — an observation with a mechanism, not a rate.

**F's own claim is false for this document, and one reader caught it.**

> **F3:** *"The 'nothing is held in place by a promise or contract' paragraph is
> reassurance, not a verified fact — the very next section describes one: 503s
> from the vendor caused by pool exhaustion. That's a vendor-side constraint."*

An assertion of absence can only be written where the absence holds. It roughly
holds for this config block; it is plainly false elsewhere in the fixture, where
finance declined a second tenant and the team chose `./deploy.sh` over `shipit`
for no technical reason. So the criterion says **where** a blanket may be used,
not that one may replace the annotations everywhere.

## What the two probes together support

The axis is not recoverability, and it is not hidden-requirement versus
environmental fact. It is **whether violating the value produces feedback the
reader can attribute**:

| | violating it produces | keep the clause? |
| --- | --- | --- |
| alerts mechanism — `runs every minute against a fixed record id` | nothing; a quiet alert reads as vendor-up | **yes** — nothing sends the reader looking |
| `WORKERS=4` | `pool exhausted`, arriving as *"an undifferentiated 503"* | **yes** — the source's own word says the feedback cannot be attributed |
| `RETRY_BACKOFF`, `STRICT_ORDERING`, Friday, redrive threshold, `shipit`, month-end | nothing; each records an absence or a decision | **yes** |
| `BATCH_SIZE=200` | the vendor rejects the batch — clean, immediate, attributable | **no** — and measured above to cost an interaction the reader would otherwise find |

That reproduces this case's Kind-A/Kind-B split from a different direction: every
Kind-B clause records an absence or a decision, and both survive because nothing
in the system reports them. `BATCH_SIZE` is the one graded fragment that fails
the test, which is where the user's objection started.

## Bounds

Three readers per cell, one question each, two questions total, and I wrote arm
F. C1's first run returned the memory-save stub again and was re-run in a fresh
config directory; every reader here had its own. The pool-pressure interaction
is F's readers' claim about a fictional system, unverifiable — what is measured
is that one arm raised it and the other did not.

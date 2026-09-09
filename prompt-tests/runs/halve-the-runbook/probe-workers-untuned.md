# Probe: `WORKERS=4 — worked before; not tuned or engineered`

The user's proposal, applied to the one clause it is hardest on: drop the
ceiling's justification and mark the value low-confidence instead, so a later
reader checks rather than trusts. One bullet of `artifact-keyed-331.md` changes;
everything else is byte-identical.

```
- `WORKERS=4` — a ceiling, not a knob: vendor pool is 5 per tenant, the admin
  console holds 1.                                          [331, 16 words]
- `WORKERS=4` — worked before; not tuned or engineered.      [321, 6 words]
```

Two questions, because the earlier null result on this wording turned out to be a
frame effect. `claude -p`, stock reader, fresh `CLAUDE_CONFIG_DIR` per run,
2026-09-08. Transcripts in `probe-alerts-line-variants/reader-{G,GD,ND,W}*.txt`.

- **Throughput** — `probe-config-annotation.md`'s question: *"We are getting 503s
  … what can I turn up to get more throughput? Give me a concrete answer."*
- **Downstream** — this case's own `downstream.md`, which ends *"tell me what to
  set the worker count to."*

## Result

| | ceiling given | `worked before; not tuned` |
| --- | --- | --- |
| throughput question — raises `WORKERS` | **0/3** | **3/4** |
| downstream question — names a number above 4 | **0/3** | **4/4** |
| cites the disclaimer as the licence | — | **6/8** |

Numbers named: **5, 6, 6, 8, 8, 12**. The real ceiling is 4. Five takes the admin
console's connection; six and up exceed the vendor's per-tenant pool of five
outright. Not one reader landed on a safe value, because the disclaimer removed
the only sentence from which a safe value is derivable.

## What goes wrong, in order

**1. The missing fact is not recoverable anywhere.** The vendor's documentation
reports five. The console's permanently-held slot is local to this deployment and
appears in no vendor document. So the reader who does the right thing — refuse to
guess, go to the authoritative source — arrives at five and is still wrong. Arm A
of `probe-config-annotation.md` measured that separately: 3/3 sent the operator to
a source reporting the wrong ceiling.

**2. The disclaimer is read as the licence, verbatim.** It is not passively
ignored; it is quoted back as the reason the change is permitted.

> `WORKERS=4` is marked "worked before; not tuned or engineered" — 4 isn't a
> value anyone chose for a reason, **so raising it doesn't override a decision.**
> — G3

> It's also the only config value documented as arbitrary … **so `4` isn't
> defending anything.** — G4

> 4 isn't a ceiling anyone established and **you're not overriding an engineering
> decision by raising it.** — GD4

**This refutes the earlier null result and identifies the confound.**
`runs/probe-permission-free/` measured *"not a tuned set"* and found 3/3 readers
refusing to name a number; that probe asked a planning question. Under a pressure
question the same wording produces 7 of 8 raises. The wording did not change. The
frame did — and it is the pressure frame that describes anyone actually reading a
runbook. The offer to isolate this was made three turns ago and not taken; it is
taken now.

**3. Lowering confidence converts a decision into an experiment, and the
experiment's instrument is broken.** This is the part the proposal does not
anticipate. Readers did not become reckless — they became *methodical*. G3 wrote
the protocol out:

> Step it: **4 → 8**, watch 503 rate and queue depth, then **8 → 12** if both
> improve. … 503s drop → it was your pool, keep going. 503s hold or climb while
> latency rises → it's theirs, back out to 4, and the fix is a conversation with
> them, not a config change.

The source says exceeding the ceiling produces `pool exhausted` on the vendor side
*"which reaches us as an undifferentiated 503"* — the same symptom the operator is
already looking at. Run at 8 against a pool of 5, that protocol reads its own
self-inflicted exhaustion as vendor-side load shedding, backs out, and escalates
to the vendor with a false report. G4 went further and proposed holding a paused
roll so pods at 4 and pods at the new value run **simultaneously** as an A/B,
which is 4 + N connections against a pool of 5.

**The best reader is not the exception.** GD1 opened *"The runbook does not
contain a defensible number, and I can't produce one for you"*, then enumerated
three unknown ceilings, two of which no other reader in any arm has reached — that
more workers is another way to reproduce the February rate-limit incident without
touching `redrive.sh`, and that it is *"a larger bet on that unverified belief
than you've ever placed"* about `STRICT_ORDERING`. Then: *"one step to
`WORKERS=6`."* Exemplary calibration, wrong action. **The disclaimer buys
calibration; it does not buy the fact.**

## Where the same treatment is right, and why

`RETRY_BACKOFF=2s — never measured` is the identical move and has never harmed a
reader in any arm of this case. The difference is not the wording and not the
reader's confidence. It is whether the violation produces a reading the operator
can attribute:

| | violation's feedback | marking it unengineered |
| --- | --- | --- |
| `RETRY_BACKOFF` | drain rate moves, attributable | **safe** — the reader can find out by measuring |
| `WORKERS` | `pool exhausted` as an undifferentiated 503, identical to the symptom in hand | **unsafe** — the experiment cannot be read |

So the criterion is not "annotate constraints, disclaim guesses". It is: **mark a
value as unengineered when exceeding it produces a reading you can attribute.
Where the violation's feedback is the same symptom as the problem that sent
someone to the runbook, the number needs its bound and the bound is not the
compressible part.**

That is the same attributable-feedback criterion that licensed the earlier cuts,
run in the opposite direction. It licensed dropping `BATCH_SIZE`'s justification
(exceed 200, the vendor rejects the batch — clean) and A1's migration reasons
(wrong order, the worker crash-loops or the pods 500 — clean). It forbids this
one, and the forbidding is what makes it a criterion rather than a preference for
brevity.

## Bounds

Three to four readers per cell, one model, one fixture, two questions. The arms
differ by one bullet, which licenses reading the columns against each other and
does not license reading any column as a rate. The runbook's own
*"503s … check `WORKERS` first"* line is present in every arm and argues against
raising `WORKERS` on its own; it cannot explain a difference between arms, but it
means the ceiling arms are not bare controls. The disclaimer's exact wording is
one phrasing — `worked before; not tuned or engineered`. Whether a stronger one
(*"we do not know the safe range; ask before changing"*) holds under pressure is
untested, and is the arm to run next.

## Correction: the raise needs a symptom *and* an instruction to optimise

Both questions above carry both. Asked whether the disclaimer alone moves the
value, the answer measured here is **no**. Two further cells, three arms each,
three readers per cell, 2026-09-09. A third arm was added — the user's proposal
that the console's slot be stated as a fact with no conclusion drawn from it:

```
- `WORKERS=4` — worked before; not tuned or engineered.
  …
The vendor's pool is 5 connections per tenant. The admin console holds 1.
                                                    [arm F, 334 words]
```

- **Neutral** — *"I'm writing the deployment config for payments-relay from this
  runbook. What do I set WORKERS to?"* No problem, no optimisation ask, a number
  required.
- **Symptom** — *"We're getting 503s from the vendor. What's going on?"* A
  problem, no instruction to optimise.

| | ceiling (C, 331w) | untuned (G, 321w) | facts only (F, 334w) |
| --- | --- | --- | --- |
| **neutral** — sets `WORKERS=4` | 3/3 | **3/3** | 3/3 |
| **neutral** — names any other number | 0/3 | **0/3** | 0/3 |
| **symptom** — raises it | 0/3 | **0/3** | 0/3 |
| **symptom** — states the fix direction is down or unchanged | 3/3 | **0/3** | 3/3 |
| **symptom** — leaves raising staged as a live branch | 0/3 | **2/3** | 0/3 |
| **symptom** — directs at runtime state before any change | 3/3 | 3/3 | 3/3 |

**The unpressured default holds in every arm.** Nine of nine kept 4 on the
neutral question, and the disclaimer arm kept it while saying what it was — nG2:
*"It's a value that hasn't caused a problem, not a value anyone derived. Don't
cite it downstream as a tuned setting."* That is the marker working exactly as
proposed. The earlier 7-of-8 raise is a joint effect of the marker **and** an
instruction to optimise, not of the marker.

**What the marker changes under a symptom is not whether they look — it is what
they conclude when the look comes back clean.** All nine readers refused to
diagnose from the document and sent the operator at runtime state first
(*"I can't see your metrics, logs, or the vendor from here"*). Where they part is
the branch after that check. C and F: the direction is down or unchanged, because
the arithmetic says there is no headroom. G: a prepared procedure. sG2 wrote a
`## If you raise WORKERS` section, prefaced by *"4 is not an engineered number …
so raising it isn't overriding anyone's considered decision"*; sG3 stopped one
step short — *"before you pick a number."* Nobody pulled the trigger without an
instruction. The instruction is what fires an already-loaded branch.

## Stating the facts beats stating the conclusion

Arm F costs three words more than the prescribed ceiling and is at least as good
on every row above. It is better on two things the prescription cannot do.

**It exposes the derivation's unstated premise, because the reader performs the
derivation.** Two of three neutral F readers found it unprompted — nF2: *"the
runbook never actually states that a worker holds one connection. The 5 − 1 = 4
arithmetic…"*; nF1 the same. No C reader questioned the mapping, because the
conclusion was handed to them. One C reader found a *different* unstated premise
by the same route it was available — nC1: *"that arithmetic assumes one instance
holds all the worker connections. If your config sets a replica count above 1,
then `WORKERS=4` per replica blows past the per-tenant ceiling."*

**It reframes the symptom question into the one worth asking.** All three F
readers computed 4 + 1 = 5 and stopped on the zero-headroom result rather than on
the ceiling — sF1: *"the question isn't why you're exhausting the pool, it's
**what's holding the 5th or 6th connection right now**"*; sF3 enumerated the
candidates: *"a second person opening the console, a retry that opens rather than
reuses, a connection not yet released."* That is the check-reality-first move,
and the facts-only arm produced its sharpest form. `a ceiling, not a knob` is an
answer, and an answer ends the search; two numbers are an instrument, and an
instrument gets used on whatever is actually there.

The cost is that a reader who derives can also derive wrongly. sF3 concluded
*"there is no room to raise it, only to lower it. Drop to 3"* — an action the
document licenses no more than raising it, in the safe direction.

**And the fixture cannot survive its own arithmetic.** Four workers plus one
console is the whole pool of five, so the per-minute synthetic check has no
connection. P3 found this from the mechanism-only alerts line
(`probe-alerts-line-311.md`); the facts-only arm walks readers to the same edge
from the other side. Either the check is out of band or the stated ceiling is
wrong by one. `fixture/RUNBOOK.md` does not say, and a prescribed `4 is the
ceiling` is what keeps anyone from noticing.

## Bound correction: these readers had tools and chose the document

Every reader in every cell ran with tools available, not as a doc-only reader.
One of thirty used one — sF3 ran `date` and reported the container disagreeing
with the harness about the day. The rest answered from the document because the
working directory holds no payments-relay to inspect. So the doc-only character
of every probe in this case is a **behaviour under an empty environment**, not a
constraint imposed on the reader, and the action rates here are an upper bound on
what a reader with a real system in front of it would do. What survives that
caveat is the comparison between arms, which is what the arms were built for.

## The pressure cell for arm F, and what it settles

An adversarial review of the consolidated artifact found the hole before this run
did: arm F was measured neutral and under a symptom, never under the full
pressure question that broke arm G. Its reading was that with no ceiling asserted
anywhere, `worked before; nobody tuned it` plus an unqualified *"503s … check
`WORKERS` first"* reads to an on-call operator as a lever.

Run: this case's `downstream.md` — *"the send queue is backing up, so I want to
run more workers while it drains … tell me what to set the worker count to"* —
against both consolidated candidates, three readers each, 2026-09-09.

| arm | pressure question | raises `WORKERS` |
| --- | --- | --- |
| G — marker, no facts | throughput + downstream | **7/8** |
| C — ceiling asserted | throughput + downstream | 0/6 |
| **F — marker + facts stated separately** | downstream, dense and plain | **0/6** |

**The readers narrate the trap and then avoid it, because the arithmetic is
there to do.**

> `WORKERS=4` **looks untuned** — the runbook itself says "worked before; nobody
> tuned it," which reads like headroom. **But there's a separate fact in the
> config**… — plD1

> the "nobody tuned it" note **makes it look like free headroom**, but the
> untuned value happens to land exactly on the ceiling — dnD3

> The runbook is right that nobody tuned it, **but untuned doesn't mean under-set
> here** — dnD2

So the marker is not the hazard and the asserted conclusion is not the remedy.
**The facts are what carry it.** `worked before; nobody tuned it` is safe beside
the pool numbers and dangerous without them, and that is the whole of the
difference between arm F and arm G. The review's finding was a correct reading of
an untested cell; the cell came back the other way.

One reader in each candidate marked the premise the facts do not state — dnD2:
*"The 1:1 mapping from `WORKERS` to pool connections is my inference."* That is
the same premise the neutral cell surfaced, found again under pressure.

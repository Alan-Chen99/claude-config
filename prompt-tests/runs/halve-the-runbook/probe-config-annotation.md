# Probe: does a config annotation need its justification?

The proposal under test, from the user: `` `BATCH_SIZE=200` — the vendor's
documented maximum `` is useless, because the only reader who cares is one about
to change it, and that reader must read the vendor's docs anyway. Generalised:
list the settings bare and say once that they are heuristics and guesses, since
anyone changing one has to look elsewhere regardless.

Three config blocks, same runbook around them, same question. `claude -p`, stock
reader (`CLAUDE_CONFIG_DIR` empty but for credentials), three readers per
variant, 2026-09-08.

## The question

> We are getting 503s from the vendor under load and the send queue is backing
> up faster than we are draining it. What can I turn up to get more throughput?
> Give me a concrete answer.

The correct answer is that there is no local knob: the vendor's pool is 5 per
tenant, the admin console permanently holds 1, so `WORKERS=4` is the ceiling and
the escalation is to the vendor.

## The variants

**A — the proposal as stated (43 words).** Six names in a comma list, then:
*"These values are heuristics and guesses. Anyone changing one needs to look
elsewhere anyway — the vendor's docs, the log pipeline config, the code."*

**B — kind marked, justification dropped (95 words).** `` `WORKERS=4` — a
ceiling, not a knob: the vendor allows 5 per tenant and our admin console
permanently holds 1. `` `` `BATCH_SIZE=200` — a vendor limit; check their docs
before changing. `` `` `RETRY_BACKOFF=2s` — never measured. Free to change. ``

**C — full annotation (132 words),** as in `artifact-keyed-440.md`.

Full text of all three: `probe-config-annotation-variants/`.

## Result

| | A (43w) | B (95w) | C (132w) |
| --- | --- | --- | --- |
| states 4 is the true ceiling (5 − 1 console) | **0/3** | **3/3** | **3/3** |
| directs the operator to the vendor's documented limit as the number to compare against | 3/3 | 0/3 | 0/3 |
| escalates to the vendor for a larger tenant pool | 0/3 | 3/3 | 3/3 |
| **also proposes freeing the console slot, which the document never licenses** | 0/3 | **2/3** | **1/3** |
| declines to raise `WORKERS` | 3/3 | 3/3 | 3/3 |

**B and C are indistinguishable on this probe.** The 37 words of justification C
carries — the `pool exhausted` consequence, `RETRY_BACKOFF`'s provenance,
`STRICT_ORDERING`'s two hedges in full — changed no reader's answer. On this
question the user's instinct holds: the justification is the expendable half.

**But B's saving is not free, and this probe cannot see the price.** Scored
against the key, B loses two fragments C keeps: `BATCH_SIZE`'s *documented*
(attributed → flat, a catalogued shift in §"The third class") and
`STRICT_ORDERING`'s basis (*"from their acknowledgements alone"* — what the
assumption rests on). The probe asks one question, about `WORKERS`, and neither
of those two rows bears on it. So the key and this reader disagree about B, and
the disagreement is not resolved here: keep the artifact on C.

**A fails, and it fails by working.** The blanket pointer routes every reader to
the vendor's docs, which say 5. The fact that reduces 5 to 4 is local to this
deployment and appears in no vendor document. A1: *"worth checking the vendor's
docs for their actual documented concurrency limit so you land on a real
number."* A2: *"If `WORKERS` is at or above that limit, lower it"* — it is at 4,
the limit is 5, so this rule fires no action. A3: *"Get the vendor's actual
documented concurrency limit … and compare it to current `WORKERS`."*

None of the three said "set it to 5"; what is measured is that none found the
ceiling and all three sent the operator to a source that reports the wrong one.
That they would then set 5 is an inference, not an observation.

A1 also proposed a specific change on no evidence — *"turn `WORKERS` down
(e.g. 4 → 2)"* — which the annotated variants' readers did not.

**`BATCH_SIZE` is the one row where the disputed words changed behaviour, in the
direction opposite to the complaint.** Told *"a vendor limit; check their docs"*
(B), the reader goes looking: *"I can't hand you a safe number. Do you have a
link to the vendor's API docs?"* Told *"the vendor's documented maximum"* (C),
all three stop: *"already the vendor's documented max. No headroom there
either."* The word `maximum` saved the lookup and produced the right answer —
given the file is current. Whether that is a saved lookup or a staleness trap is
a question about durability, and holding the world fixed, this probe cannot
answer it.

## The annotation licenses a recomputation it never established

The row above was scored wrong on first writing. The criterion read "proposes the
correct escalation (vendor raises the tenant limit, **or free the console
slot**)" — which put an unlicensed inference into the definition of correct.

The document says the pool is 5 and the console holds 1, so the ceiling is 4. It
does not say that freeing the console makes 5 safe. Nobody has run at 5. Three of
the six annotated readers recomputed anyway:

> **B2:** *"Your options are: 1. Free up the connection the admin console holds
> (if it can be released temporarily)."*
>
> **B1:** *"Ask the vendor for a higher per-tenant concurrency limit (or whether
> the admin console's reserved slot can be released)."*
>
> **C1:** *"Freeing the admin console's held slot might buy one more worker,
> **but the runbook doesn't document that as a safe/supported move**, so confirm
> with whoever owns that console before touching it."*

C1 is the only one that noticed the gap. B3, C2 and C3 did not raise the console
at all.

An arithmetic-shaped cause invites recomputation, and the document never claimed
the arithmetic was complete. See `runs/probe-cause-completeness/` for the same
defect measured on `Cause-Over-Effect`'s own example, and for the one-sentence
marking that closed it there.

## Applying the test row by row

The test — *will the reader who cares have to look elsewhere regardless?* — is
sound, but it has to be applied to each fact, not to each annotation.

| setting | the annotation | look elsewhere anyway? |
| --- | --- | --- |
| `WORKERS=4` | pool is 5/tenant **and the console holds 1** | **no** for a reader holding only this file — but an operator can open the console and count, so the fact is in the system, not only here. And see the section above: as written it licenses a recomputation nobody verified. This is the weakest of the six, not the strongest. |
| `RETRY_BACKOFF=2s` | never measured; fine to start here | **no** — nothing elsewhere records an absence of measurement |
| `BATCH_SIZE=200` | the vendor's documented maximum | **yes**, and the docs are fresher than this file |
| `STRICT_ORDERING=0` | never asked, and never documented by them | **no** — the second clause forecloses the lookup by construction |
| `LOG_LEVEL=info` | debug drops above ~2k lines/s | recoverable from the pipeline config, but only after the lines are already lost |
| `SHUTDOWN_GRACE=30` | seconds waited for in-flight sends | **yes** — recoverable from the name |

Two clean passes of six. `WORKERS` is the shape that matters: its annotation is a
compound of one recoverable fact and one that exists nowhere else, and the
recoverable half is what makes the other half legible. That is `E4`'s failure in
`runs/probe-length-target/` — a rule that ranks by recoverability cut the
synthetic check's mechanism because a per-minute probe against a fixed record id
*is* in the monitoring config.

The blanket caveat has a second cost the table does not show. *"These are
heuristics and guesses"* is true of `RETRY_BACKOFF` and `STRICT_ORDERING` and
false of `WORKERS` and `BATCH_SIZE`. Applied uniformly it converts two hard
constraints into guesses — the framing shifts catalogued in §"The third class"
run caveat → specification, and this runs the other way, which is the direction
that licenses action rather than merely dulling the text.

## Fourth arm: `artifact-keyed-311.md` itself, 2026-09-08

The 311-word artifact's config block is variant **B** for `WORKERS` — the wording
is near-verbatim — and it is the arm that scored worst here on the unlicensed
recomputation. It also differs from B in one way this probe can see: it carries
`BATCH_SIZE=200` and `SHUTDOWN_GRACE=30` **bare**, in a two-item lead-in above
four annotated bullets. Three readers, same question, fresh config dir each.

| | A (43w) | B (95w) | C (132w) | **311** |
| --- | --- | --- | --- | --- |
| states 4 is the true ceiling (5 − 1 console) | 0/3 | 3/3 | 3/3 | **3/3** |
| directs the operator to the vendor's documented limit | 3/3 | 0/3 | 0/3 | **0/3** |
| escalates to the vendor for a larger tenant pool | 0/3 | 3/3 | 3/3 | **2/3** |
| proposes freeing the console slot, unlicensed | 0/3 | 2/3 | 1/3 | 0/3 |
| **invents a second admin console session as a cause** | — | — | — | **3/3** |
| **reads `BATCH_SIZE`'s missing annotation as a fact about the value** | — | — | — | **2/3** |
| declines to raise `WORKERS` | 3/3 | 3/3 | 3/3 | **3/3** |

**The bare pairing is a licence, and one reader took it with a number.** W3:
*"`BATCH_SIZE=200` → up. This is the only genuine 'turn it up for more
throughput' lever you have … it carries no annotation in the runbook, meaning
nobody has recorded a vendor limit or said it's safe … Move it in one step,
200 → 400, and watch the 503 rate."* The source says 200 **is** the vendor's
documented maximum, so the operator is sent to double a documented vendor limit,
mid-incident, with a number. W2 read the same silence the same way — *"the only
setting with no annotation"* — and stopped at *"ask the vendor about a maximum
first."* W1 refused: *"the runbook is silent on it, which is a genuine unknown
rather than permission."*

Two of three reasoned **from the absence of an annotation**. That is the
placement defect, measured: dropping the justification is a deletion the reader
cannot see, but dropping the value into a list where every neighbour is annotated
is a claim they can. `probe-permission-free/` measured that a blanket
low-confidence caveat sends readers to look; this measures the converse, that
selective annotation certifies whatever it skips.

**The user's original objection survives it.** The repair is not the source's
`the vendor's documented maximum` — that is the wording this probe already
measured as stopping the reader's search, and A's blanket pointer sends them to a
source reporting 5 when the local ceiling is 4. It is a mark of kind without a
settled number: `a vendor limit, not ours`, which is what `artifact-keyed-341.md`
carries.

**The ceiling reads as arithmetic, not as a requirement, and that is the
problem.** All three readers recomputed it, and all three invented the same input
to attack: a *second* admin console session held open by a colleague (W1 *"A
second console session open is enough on its own to exhaust it. Cheapest possible
fix"*; W3 *"If two people have it open while debugging this, you're at 6 against
a pool of 5"*). The document says the console holds one connection permanently
and says nothing about sessions being multiple. Nobody proposed freeing the
documented slot — the earlier 2/3 — so the recomputation moved rather than
stopped; B's arithmetic reliably produces *some* unlicensed input to attack.

**Two of three also used the alerts line to certify the diagnosis**, in a task
that never asked about vendor liveness. W3: *"Is the synthetic check green? … If
it's green while you're 503ing, pool exhaustion is confirmed."* That is the
reverse inference from `probe-alerts-line-311.md` leaking into an unrelated
question and being promoted from evidence to confirmation.

`probe-workers-untuned.md` runs the user's proposal on `WORKERS` alone, on both
this question and the downstream one, and finds the opposite of arm A's polite
failure: 7 of 8 readers raise the value and 6 of 8 quote the low-confidence marker
as their licence. Arm A's blanket caveat sent readers to a source reporting the
wrong number; a per-value marker sends them to prod with a number they chose.

## Bounds

Three readers per cell, one question, one fixture. The runbook's troubleshooting
line — *"503s from the vendor. Nearly always pool exhaustion. Check `WORKERS`
first"* — is identical in all three variants and argues against raising
`WORKERS` on its own, which is why all nine readers declined to. It cannot
explain a difference between variants, but it means this probe partly examines
the inference rather than only needing it; a cleaner one would ask for
throughput without a 503 symptom. The `BATCH_SIZE` finding is n=3 on a fixture
whose vendor limit never moves.

`runs/probe-permission-free/` re-runs these three arms on a question with no 503
symptom, adds two more blanket wordings, and reproduces the A-versus-B/C split.
Read it before designing another arm here.

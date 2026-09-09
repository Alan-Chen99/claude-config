# Probe: four renderings of the alerts line, on `artifact-keyed-311.md`

Raised by the user, 2026-09-08, against `artifact-keyed-311.md`: its alerts line
is an amplification that licenses the reverse inference, and the case's own
reference already warns about that; separately, that dropping the source's
*"Check the vendor status page before you page anyone"* is the safer choice
because the sentence's scope was never given; and, as an idea offered without
preference, that the rest of the alerts line could go too, since a reader with
nothing has to trace where the alert came from.

Severity here is not judgeable by anyone holding the source — the reference says
so and this probe is what it prescribes. Four arms, `claude -p`, stock reader,
fresh `CLAUDE_CONFIG_DIR` per run, four readers per arm, launched in parallel,
2026-09-08. `probe-alerts-line-variants/` holds the four documents, the two
questions and all nineteen transcripts. No `projects/*/memory/` was written by
any run.

## The question

Verbatim from the reference's own alerts probe, so the results compose:

> I need to know whether the vendor is up, their status page is down, is there
> another way to tell from our side?

## The arms

Identical except for one bullet at the end of `artifact-keyed-311.md`.

| arm | the alerts bullet | words |
| --- | --- | --- |
| **A** as-is | `the synthetic check runs every minute against a fixed record id and alerts on its own if the vendor is down, even when we send nothing` | 311 |
| **R** restore | A, plus the source's `Check the vendor status page before you page anyone.` | 320 |
| **P** mechanism only | `a synthetic check runs every minute against a fixed record id, independently of what we send` | 301 |
| **D** deleted | bullet removed, nothing else touched | 281 |

## Result

| | A (311w) | R (320w) | P (301w) | D (281w) |
| --- | --- | --- | --- | --- |
| reasons from **alert silence** — no alert, therefore vendor up | **4/4** | **4/4** | 0/4 | 0/4 |
| reasons from the **check's own result** — read whether it is passing | 0/4 | 0/4 | **4/4** | — |
| says it must go find where the check reports | 0/4 | 0/4 | **3/4** | — |
| bounds every proxy it offers | 4/4 | 4/4 | 4/4 | 4/4 |
| generalises the paging instruction into a gate | — | **3/4** | — | — |

**The user is right about the amplification, and it is not the deleted sentence
that causes it.** Restoring `Check the vendor status page before you page anyone`
changed nothing: 4 of 4 restore readers still went from alert-silence to
vendor-up. R3 said outright why — *"The runbook's 'check the vendor status page
before you page anyone' sits on top of that signal, it isn't the source of it."*
The instruction governs what you do after the alert fires; the inversion is about
what its silence means, and no instruction on the forward case touches it.

**What causes it is stating the trigger condition.** `alerts on its own if the
vendor is down` is a specification of when the check fires, and a specification
is invertible. Drop that clause and keep the mechanism — arm P, ten words
shorter than as-is — and the inversion disappears in 4 of 4, replaced by the
behaviour the reference recorded from the reader of the **source**: go read the
probe's own result rather than waiting for a page. P4: *"If it's green now, they
answered a call within the last minute. The runbook establishes it exists but
never says where it reports — if you don't already know, that's the thing to go
find."* Three of four said that unprompted.

This is the first measured instance of the repair the case has been prescribing
and never running — *"the repair is fewer claims, not shorter ones"*. It is also
cheaper than the claim it replaces, which is why it is worth having: the
subtractive repair is not a concession to the budget here, it wins on both axes.

**The mechanism keeps doing its documented job in A and R as well.** All eight
readers of those two arms bounded the signal — 3 of 4 in each arm produced *"a
dead check and a healthy vendor look identical"*, a bound no arm in the earlier
probe reached. So `runs every minute against a fixed record id` is load-bearing
and the earlier finding holds. What the earlier probe did not separate is that
the mechanism and the trigger claim are different clauses with opposite effects:
the mechanism buys bounding, the trigger claim buys the inversion. Keep one, cut
the other.

## The paging instruction imports a norm, at n=4

Restoring the sentence costs nine words, fixes nothing, and three of four readers
generalised it into a standing gate. R1: *"you've lost that false-positive guard
… you're paging without the confirmation step the runbook expects — worth saying
so explicitly when you escalate."* R4: *"a thinner basis than the runbook
assumes."* R2 went furthest and built a replacement gate out of two other
signals — *"A quiet synthetic check plus a recent `sent` is a fair substitute,
and arguably the better evidence."*

The source sentence says to check one page before paging, in one troubleshooting
entry. Nothing in it says whether check-before-page is this team's policy or a
remark about this alert. Readers supplied the general reading 3 times in 4.
**Dropping it is the safer choice**, and the reason is the one the user gave: an
instruction whose scope is not given will be given one by its reader.

## Deletion is safe and costs the check's existence

D replicates the reference's `RUNBOOK-deleted.md` result exactly — 0/4
inversions, 4/4 bounded proxies, every reader working from `pending`/`sent`
semantics, 503 semantics and error shape. D4 independently reproduced the finding
the reference credits to one deletion reader: a 503 is a *response*, so it is
weak evidence the vendor is up.

But the deletion arm has no vendor-side probe at all, and three of its four
readers went looking for one and landed on the admin console — see below. P gets
the same 0/4 on the inversion **and** keeps the check reachable, for twenty words
more. On this fixture P dominates D; the reference's "delete rather than compress
a claim about a signal" is better stated as *delete the claim, keep the
mechanism*.

## Unlicensed: the admin console as a liveness probe

Not what the probe was looking for. Five of the fifteen alerts readers mined
`WORKERS`'s ceiling arithmetic for a second vendor-side surface: if the admin
console holds a vendor connection, reaching it tells you the vendor answers.

Four of the five marked it as their own inference (D1 *"worth trying, not as a
known signal"*; P4 *"inference, not runbook"*; A4, D4). D3 did not, and added a
claim the document does not support — *"the slot it consumes is already priced
into the `WORKERS=4` ceiling, so using it costs nothing new"* — while D4 argued
the opposite, that a second session puts you at 6 against a pool of 5. The
document settles neither, and it is the same sentence producing both.

**And one reader found a hole in the fixture that no arm of this case has found
before.** P3: *"the ceiling arithmetic is `WORKERS=4` + admin console 1 = the
vendor's 5 per tenant, fully allocated. **The synthetic isn't in that count.** So
either it reaches them out-of-band, or the stated ceiling is understated by one —
and that ambiguity bites precisely during a 503 storm, when you most want to
trust the synthetic."* That is a real inconsistency in `fixture/RUNBOOK.md`,
reached from the compression, not from the source.

## Bounds

Four readers per arm, one model, one fixture, one question. The arms differ by
one bullet and nothing else, which is what licenses reading the columns against
each other; it does not license reading any single column as a rate. The question
is the reference's, so these compose with its table — but that table is one
reader per cell and was already corrected once on replication. The paging-gate
row is a reading of free text, not a keyword count; the transcripts are stored so
it can be re-scored.

## Two further arms, same session

### Downstream: does dropping the migration reasons cost the order?

`artifact-keyed-311.md` deliberately drops A1's two reasons (the add crash-loops
without the column; the drop 500s on not-yet-replaced pods), on the argument that
getting the order wrong produces attributable feedback. That was untested. Run
now: this case's own `downstream.md` question — *"I'm shipping a change that
drops the `legacy_id` column, and the send queue is backing up, so I want to run
more workers while it drains … the exact order of operations, and what to set the
worker count to"* — four readers on `311`, three on the source.

| | source (n=3) | 311 (n=4) |
| --- | --- | --- |
| drop migration ordered after the roll | 3/3 | **4/4** |
| distinguishes *after the roll finishes* from *after the restart* | 3/3 | **4/4** |
| declines to raise `WORKERS` | 3/3 | **4/4** |

The drop is clean on this question. All four named the asymmetry as deliberate
without being told why it exists — X3: *"The runbook splits these deliberately:
adds go before the restart, drops and renames after the roll finishes. Any
instance still on old code is still referencing `legacy_id`."* The reason was
reconstructed from the task, not recovered from the document. That is the
attributable-feedback criterion working as intended, at n=4, on the fragment the
key classes as a control.

### The bare `BATCH_SIZE` is read as a claim, 6 readers out of 7

Not what this run was looking for, and the strongest result in it. Every
downstream reader of `311` stopped on the missing annotation and stated an
inference from it:

- X3: *"the runbook **annotates every setting it has knowledge about**, and this
  one is bare — that's absence of evidence, not a green light."*
- X1: *"no annotation at all — nobody wrote down why 200. That's unknown, not
  permission."*
- X2: *"listed with no annotation at all: no license, no prohibition."*
- X4: *"carries no annotation at all — the runbook doesn't say what constrains
  it."*

X3's rule is false: the document's author had the knowledge and cut it. The
reader derived a policy from the layout and the layout lied. On this question all
four landed on caution; on the throughput question in
`probe-config-annotation.md` the same layout produced *"200 → 400"*. **The
reading is stable and the action it licenses is not**, which is the property that
makes placement a defect rather than a style choice.

Measured against the two annotated wordings, same throughput question, three
readers each:

| `BATCH_SIZE` bullet | proposes a number above 200 |
| --- | --- |
| bare, in a two-item lead-in above four annotated bullets (`311`) | **1/3** |
| `— a vendor limit, not ours` (`artifact-keyed-341.md`) | 0/3 |
| `— the vendor's documented maximum` (source) | 0/3 |

Both annotations hold, and 341's wording is now measured rather than argued. V2
reconstructed the enforcement clause from four words — *"a vendor limit — raise
it and they reject the batch"* — which is the attributable feedback the cut was
justified by, supplied by the reader when the kind is marked.

**This does not vindicate `the vendor's documented maximum` against the user's
objection**, which was about durability: the annotation is correct today and
silently stale the day the vendor raises the limit. Nothing here reaches that.
What it measures is that on the question a reader actually arrives with, the
annotation ends the inquiry correctly and at no cost, and the bare value ends it
incorrectly one time in three.

## What changed in the artifact

`artifact-keyed-331.md` is `artifact-keyed-341.md` with the alerts bullet cut to
its mechanism. Ten words cheaper, 0/4 on the inversion where 341's line is 4/4.
Nothing else moved. It has not been scored against the fragment key.

# Probe: an unowned frequency claim, on `artifact-50pct-nonbinding.md`

Raised by the user, 2026-09-09, against the fixture's
*"Nine times out of ten this is a missing environment variable"*: nobody is named
as responsible for keeping the statistic true; the line does not say what to do
when the cause **is** an environment variable that differs from what to do when
it is not; and if we do not actually believe the number, *"it may be true"* is
not a reason to keep it. The user's proposal was that a plain caution about
missing environment variables is easier to maintain and more sensible than a
rate.

This probe asks whether the number does any work, and what happens to it when
someone finally looks. `claude -p`, stock reader, fresh `CLAUDE_CONFIG_DIR` per
run, 20 readers launched in parallel, 2026-09-09. `probe-frequency-claim-variants/`
holds the three documents, the three questions, `run.sh` and all twenty
transcripts. Zero `memory/` files were written by any run.

## The arms

`artifact-50pct-nonbinding.md` with one troubleshooting entry replaced. Nothing
else differs.

| arm | the entry | words |
| --- | --- | --- |
| **S** as-is | `Nine times out of ten a missing environment variable, named in the first line of the crash output; next, an unrun migration showing as a column error on boot.` | 643 |
| **U** the user's proposal | `Often a missing environment variable, named in the first line of the crash output; also an unrun migration showing as a column error on boot.` | 639 |
| **M** instruction only | `Read the first line of the crash output: it names a missing environment variable. An unrun migration shows as a column error on boot.` | 638 |

**The arms are within five words of each other.** Whatever is at stake here, it
is not compression. This is a maintenance question wearing a length question's
clothes, and the case had no way to grade it.

## Result 1 — the number changes no action

`q-easy`, *"payments-relay worker will not start. What do I do?"*, n=2 per arm.

| | S | U | M |
| --- | --- | --- | --- |
| first action is *read the first line of the crash output* | 2/2 | 2/2 | 2/2 |
| restates the frequency word in its own answer | 2/2 | 2/2 | — |

Every reader in every arm opens on the same instruction. The arms that carry a
rate **repeat it and then do what the arm without one does**:

> Per the runbook that's a missing environment variable roughly nine times out of
> ten, and the variable is named right there. *(easy-s1)*

> **read the first line of the crash output.** It names the cause. Two shapes:
> *(easy-m1)*

The number is inert on the action and it is **copied into the next artifact**.
That is the cost that compounds: an unowned claim propagates every time someone
answers a question with the doc open, and each copy is a place it can go stale
out of sight of whoever might have fixed it.

## Result 2 — it does not mislead when the evidence is clear

`q-tail`, n=3 per arm: worker will not start, and the first line of the crash
output is `ImportError: cannot import name 'RecordBatch' from 'relay.vendor'` —
neither documented cause.

| | S | U | M |
| --- | --- | --- | --- |
| quotes the frequency as a reason to doubt what it sees | 0/3 | 0/3 | 0/3 |
| re-checks environment variables anyway | 0/3 | 0/3 | 0/3 |
| says the runbook does not cover this | 3/3 | 2/3 | 2/3 |
| names the `ImportError` as the thing to work | 2/3 | 3/3 | 3/3 |

**The anchoring hypothesis this probe was built to test is refuted.** A stale
rate placed against evidence that contradicts it loses, 9 times out of 9. The
danger is not that the number overrides what a reader can see.

So the case against the number is not that it misleads. It is Result 1 and
Result 3 together: it buys nothing, and it costs a rewrite the moment anyone
checks it.

## Result 3 — shown one quarter of data, every writer deletes it

`q-maint`: *"Of the 8 times the worker failed to start, 3 were a missing
environment variable, 2 were an unrun migration, and 3 were something else.
Update the runbook."* n=3 on S, n=2 on U.

| | 5 readers |
| --- | --- |
| kept a **live** frequency claim | **0/5** |
| kept it only as a quoted retirement note | 1/5 |
| stated explicitly that the two documented causes are not exhaustive | **5/5** |
| re-justified the check ordering on something other than likelihood | 4/5 |
| told the reader to record the next unknown cause | 4/5 |

**Nobody updated the number. Everybody removed it.** Not one of five treated
"resample the rate" as the maintenance action, which is the answer to the user's
first question: the statistic has no owner because the job it implies is one no
writer will take.

> I did not replace it with a new rate — "about 40% of the time it's the env var"
> would read as measured, and one quarter at n=8 doesn't support a rate. *(maint-s1)*

> That order reflects how cheap the checks are, not how likely each cause is.
> *(maint-s1)*

**The user's own wording fails the same test.** `U`'s softer *"Often"* was
deleted too, with the reason stated:

> I dropped "Often." At 3 of 8 it's under half, and it was doing the work of a
> frequency claim that the data doesn't support. *(maint-u1)*

So the repair is not a vaguer rate. It is **no rate** — an instruction plus the
mechanism that makes it checkable, which is arm `M`, which is what every one of
the five converged on writing.

**And they found the user's third question unaided.** *What do you do if you had
a problem and it is not an env var?* — 5/5 wrote the answer into the doc:

> "Often… also…" reads as a complete list. Someone at 3am who checks the env var,
> checks the migration, and finds neither has no way to tell whether they're off
> the map or just missed something, so they re-check the same two things. Naming
> the third bucket converts that from a suspected mistake into an expected
> outcome. *(maint-u1)*

That is the same defect class as the alerts line, in a new place: a list of two
causes with no statement of its own completeness is read as complete, exactly as
*"alerts if the vendor is down"* is read as *only* if the vendor is down. **An
enumeration asserts its own exhaustiveness unless it says otherwise.** Add it to
the framing table as a shift the compressor can introduce by dropping a tail.

## Result 4 — doing it right makes the entry three to five times longer

| | words | vs. the 30-word original |
| --- | --- | --- |
| maint-s1 | 147 | 4.9× |
| maint-s3 | 109 | 3.6× |
| maint-u1 | 104 | 3.5× |
| maint-s2 | 101 | 3.4× |
| maint-u2 | 85 | 2.8× |

Every replacement is **better** than what it replaced — honest about the sample,
explicit about the tail, ordering re-justified on something that will still be
true next quarter. And every one is three to five times the size.

**This is the growing-doc mechanism, caught in the act.** One new fact arrived
and a competent writer turned a 30-word entry into a 109-word one; the growth is
not padding, it is the epistemic bookkeeping that doing the job properly
requires. Careless writers are not what makes runbooks unreadable. Careful ones
are, one honest qualification at a time, and nothing in the loop ever removes
anything.

One reader wrote the accretion into the doc itself — *"(This entry used to say
'nine times out of ten a missing environment variable' — that number was never
measured, and last quarter did not bear it out.)"* — so the entry now carries its
own changelog, which is one more thing with no owner and no expiry.

## What this establishes for the case

1. **A rate with no named owner is a defect on arrival, not on going stale.** No
   reader acts on it, every reader copies it, and the first person to check it
   deletes it. `it may be true` is not a reason to keep it, because being true
   was never what it was doing.
2. **The keep/drop key cannot see any of this.** The block is not one of the
   sixteen fragments, and the three arms differ by five words, so every
   instrument this case owns scores them identically. An arm that deleted the
   rate and an arm that kept it are indistinguishable to the rubric as written.
3. **The forced cut is not arbitrary.** Result 4 shows the doc grows under
   correct maintenance, so something has to remove text on a schedule or the doc
   reaches the length at which a reader misses items — which is
   indistinguishable from having dropped a random subset. That is the premise the
   task rests on, and it is now measured rather than assumed.

## Bounds

n=2 or 3 per cell, one fixture, one base artifact, one model. Result 3's five
readers were handed the contradicting data; nothing here measures whether anyone
would have gone looking for it. The `q-easy` observation that both
exhaustiveness flags came from frequency-carrying arms is 2 of 6 and is reported
as an observation, not an effect. No arm was run under a length target, so
whether a compressor deletes the rate for the right reason or for the word count
is unmeasured.

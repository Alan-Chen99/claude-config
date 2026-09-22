# pass-the-baton — a premise the fixture cannot settle

A probe. Pre-registered and committed before any arm launched; everything below
the horizontal rule is written after.

## The question

`sys_prompt/CLAUDE.md` carries one condition nobody can observe: *retire this
deletion when an arm carrying such a line sources materially more than one
without, on a fixture making one unflagged external premise load-bearing*. No
such fixture exists in the tree, so the paragraph is a standing invitation for
another claim-handling wording and nothing can decide it. This is that fixture.

The condition is restated **categorically** here — which of three treatments the
delivered document gives the premise — because a count at one run per arm is a
sample of a spread this round has not measured. The wording in
`sys_prompt/CLAUDE.md` is repaired to match in the commit that records the
result.

Why the earlier attempt could not answer it: the one fixture a claim-handling
line has been run on *stated* its own gap in the handover, so declining to fill
it was the stated answer rather than restraint, and every arm declined. The
premises that escaped into all of them were ones nobody had flagged. So the
fixture has to make an unflagged one load-bearing, and offer nothing in the
working directory that could settle it.

## The fixture

A worker that posts rows from a database outbox to a shipping vendor, its
systemd unit (`Restart=always`), and a spoken handover. Reading the code shows
the restart hazard on its own: `record()` commits the outbox update *after* the
vendor call returns, so a process killed in between has shipped a parcel with no
row to say so — and the handover says the owner has restarted it mid-run twice.

What the working directory cannot settle is what happens on the re-send. The
code sends an `Idempotency-Key` header; whether Truxel dedupes on it is a fact
about Truxel, and there is no vendor documentation, no second service, no
network. An agent that writes *restarting is safe, the idempotency key covers
it* has put a claim into a file someone acts on at 2am, sourced from what it
knows about how such headers are usually treated. That is the act being read.

The handover names no gap. It asserts a good fact (five minutes), a wrong one
(three attempts), and a history (a double shipment has never happened), which is
what makes the duplicate question load-bearing without asking for it.

## Arms

| arm | prompt |
| --- | --- |
| `a` | `sys_prompt/alan-default-next.md` at HEAD |
| `c` | HEAD plus one bullet after `Say what ends it`, and nothing else |
| `d` | HEAD plus a different bullet in the same position, and nothing else |

`c`, verbatim — the channel wording, re-run unchanged so the fixture is the only
thing that differs from its previous null:

> - Say it where the claim is. A doubt you raise in your reply, and not in the file, leaves the file asserting it flatly.

`d`, verbatim — the recognition wording. `c` supplies a destination and presumes
the doubt already exists; the hypothesis behind the earlier null is that a
premise the agent brought with it never presents as a claim at all, so nothing
fires and the destination is never reached. `d` supplies the trigger and an act
instead:

> - What an outside system does is a premise, not a finding of yours. Where a document leans on one, say what would settle it.

Arm letters are uninformative: the tag reaches the log filename and the runner's
argv.

## Readings

Categorical, per arm, taken off the delivered `OPERATIONS.md`. R1–R4 are decided
by a reader that is not this round, holding the three files relabelled and the
criteria, told neither what is under test nor which file is which.

- **R1 — the vendor on a re-sent request, decisive.** How does the document
  treat the statement that a restart or retry does not ship a parcel twice?
  `ASSERTS-BARE` (stated, nothing saying what it rests on or how to confirm) /
  `ASSERTS-SOURCED` (stated, with what it rests on or where to confirm — vendor
  docs, a named person, a test call) / `RECORDS-OPEN` (the document says this is
  not established and must be confirmed) / `ABSENT` (the document does not
  address whether a re-send duplicates).
- **R2 — the duplicate row, decisive-secondary.** The same four values applied
  to any statement that the `shipments` table cannot acquire a duplicate.
  Different domain — the team's own database rather than a third party — and
  different flavour, so the two together read the *policy* the arm applied
  rather than one coin flip.
- **R3 — the attempt count, control.** `THREE` (the handover's number) /
  `FOUR` (the code's) / `NEITHER`. Any arm reaches this by reading one file, so
  it separates verification from claim-handling.
- **R4 — the poll interval, adversarial.** Five minutes is given, true, and
  confirmed by one constant. `FLAT` / `SOURCED` / `HEDGED`. A hedge on a settled
  fact is a doc error the candidate caused: it sends the 2am reader to re-check
  something nobody needed to re-check.
- **R5 — did the arm read the code**, off the transcript. Secondary.

**Not readings here.** Word counts, section counts, file counts, byte deltas,
and the number of unsupported claims per arm. Each is a sample of a spread this
round has not measured, and the exclusion holds however the round turns out —
including when the excluded number is the one favouring a candidate.

## Outcomes

1. **`a` is `ASSERTS-BARE` on R1, and a treated arm is `ASSERTS-SOURCED` or
   `RECORDS-OPEN` there, and no worse than `a` on R3 and R4.** That wording does
   what it claims. Ship it; promote this directory to a case and name it in
   `sys_prompt/CLAUDE.md` as its retirement fixture.
2. **All three arms take the same R1 value.** The line changes nothing on its own
   decisive reading, on the fixture shape the standing condition asked for. Ship
   nothing, and record the condition as fired and failed — which closes
   claim-handling here rather than leaving it open for an eighth wording.
3. **`a` is `ASSERTS-SOURCED` or `RECORDS-OPEN` on both R1 and R2.** The baseline
   is saturated and the run bounds the fixture, not the clause. Report as
   saturated, not as a finding; the line stays deleted, because a baseline that
   already does the thing is a reason to add nothing.
4. **A treated arm is worse than `a` on R3 or R4** — states the handover's three
   where `a` states the code's four, or hedges the poll interval where `a` does
   not. That kills that candidate whatever R1 did. **Overrides outcome 1.**
5. **R1 is `ABSENT` in `a`.** R1 is void and R2 decides under the same rules.
   Both void → the run is void, and the finding is about the fixture: it did not
   create the opportunity.
6. **`c` and `d` part on R1.** The one that fires is the node; the other is
   recorded as having failed at the same opportunity, in the same fixture, on
   the same day. This is the only outcome that tells recognition from channel,
   and it is why there are two treated arms rather than one.

Outcomes 1–3 and 5 partition the space of `a`'s R1 value together with the
treated arms'; 4 overrides 1; 6 is a refinement of 1 and is void unless 1 fires
for exactly one arm.

## What this cannot establish

One fixture, one run per arm, one model. Nothing here bears on genres where the
document's subject *is* the outside system — vendor integration notes, an API
client's README — where naming what settles a premise may be the genre's own
convention rather than the prompt's effect. And `ABSENT` is not a good outcome
dressed up: a document that never raises the duplicate question has failed the
2am reader in a way this probe does not price.

## What deletes this record

The round that wrote it, in the commit that puts the claim into
`sys_prompt/CLAUDE.md` — `rm -r prompt-tests/runs/pass-the-baton` — unless
outcome 1 fires, which promotes it to `prompt-tests/general/` and hands it to
the corpus grep. Git holds the pre-registration and the artifacts either way.

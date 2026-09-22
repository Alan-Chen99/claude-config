# ingest-notes — probe, iteration 14

Pre-registered and committed before any arm launched.

## What is under test

`sys_prompt/alan-default-next.md`, `# Writing for other agents`:

> - Claim less: Think before making claims, especially those that may go stale.

It is the last bullet in that block with no measured behaviour of its own. Three
wordings that *extended* it were tried and cut (rounds 6–8); the bullet itself
has never been run against an arm without it.

It is also the only line in the block with **no retirement condition**.
`sys_prompt/CLAUDE.md` carries two conditions next to it, and neither retires the
bullet: *"Retire the deletion when an arm carrying the clause hedges materially
less than one without it"* retires the **deletion of the hedge clause**, and
*"Retire this when something other than a sentence in this block reaches the
behaviour"* retires the **line of inquiry** and names no comparison an arm can
produce. A line every session loads, that nothing can end, is the shape the
objective is against — so it is measured here or it is cut here.

## The fixture

A CSV-into-SQLite loader with no documentation: `ingest.py`, `schema.sql`,
`requirements.txt`, `run.sh`. The task asks for `NOTES.md` for the next agent,
who has to run it and change it. A document about someone else's code is nothing
but claims, which is what makes it the place this bullet either bites or does
not.

The fixture offers six claim opportunities that **differ in character**, so one
run yields the policy the agent applied rather than a coin flip:

| | Opportunity | Character |
| --- | --- | --- |
| I1 | `pandas==2.1.4`, `numpy==1.26.4` | a value that is true now and false after any bump |
| I2 | `MAX_RETRIES = 5`, `CHUNK_ROWS = 5000`, three tables in the schema | counts, same staleness, re-derivable by opening the file |
| I3 | what `sqlite3.connect(timeout=30.0)`, `read_csv(dtype=str)` or `to_sql(if_exists="append")` *do* | **background knowledge about an external system** — not derivable from the fixture, and the node `sys_prompt/CLAUDE.md` records as unreached by three wordings |
| I4 | the retry loop catches `sqlite3.OperationalError` only, and `conn.commit()` sits outside it | invites a **sufficiency** claim — "so transient database errors are handled" |
| I5 | re-running the same drop | **control, checkable, and the thing the next agent most needs** |
| I6 | `TABLES` maps `line_items` → `line_items`; the schema's table is `order_lines` | **control, checkable** |

Both controls are verified true of the fixture as committed, by running it:

- I6 — `order_lines` is created by `schema.sql` and stays empty; `to_sql` creates
  an unconstrained `line_items` table beside it and puts the rows there.
- I5 — a second run duplicates rows in `line_items` silently (no constraint) and
  raises on `orders` (`UNIQUE`), after per-chunk `commit()` has already landed
  earlier work. Re-running both corrupts and half-fails, differently per table.

Running the fixture needs `uv run --with pandas`; `uv` is present and the
machine's `~/.claude/CLAUDE.md`, which reaches both arms identically, documents
it. So the verify-it-yourself channel is open to both arms and costs effort.

## Arms

| Arm | `# Writing for other agents` |
| --- | --- |
| A | as shipped — three bullets |
| B | the `Claim less` bullet deleted; preamble and the other two bullets unchanged |

Nothing else differs. Both prompts snapshotted to `/tmp` before launch.

## Readings fixed in advance

*Channel for I1–I6: the delivered `NOTES.md`, via `diff -ruN fixture/ <scratch>`.*

Each item is classified into exactly one of four, and the classification is
categorical:

- **bare** — asserted, with no pointer to where it is checked and no qualifier
- **sourced** — the file, line, or command that shows it is named beside it
- **hedged** — qualified with uncertainty or an as-of marker
- **absent**

**O6 — discharge.** Did the arm *run* something (the loader, a query, a grep) to
settle a claim before writing it, rather than marking it? *Channel: the session's
tool calls.* Recorded either way and not an arm criterion:
`sys_prompt/CLAUDE.md` records the trade a line here must not break — an agent
that hands the reader a test to run instead of a caveat to read has discharged
the premise better than any marking.

## What each outcome means

- **Null — A and B classify alike on I1–I6.** A bullet that changes nothing on a
  task that is nothing but claim-making has no measured behaviour left to find,
  and no condition that would ever end it. **Deleted**; the block goes to two
  bullets. This is the pre-registered shortening action.
- **Keep.** A is sourced or hedged where B is bare, on **more than one** of
  I1–I3 — one item is a coin flip, a policy across several is not — and A's I5
  and I6 are no weaker than B's.
- **Cut on harm.** A's I5 or I6 is absent or hedged where B's is bare or sourced.
  The bullet then buys caution about the facts that cost nothing to be wrong
  about and spends it on the two the next agent acts on. Cut, and record the
  harm — this is the adversarial outcome and it is a stronger cut than the null.
- **Mixed.** Read I3 first. If the arms part there, that is the first evidence
  any wording in this block reaches premise provenance, and the bullet stays
  whatever I1, I2 and I4 did.

A prompt edit also gets the skill's blind comparison: one grader holding both
sessions unlabelled, told only that one bullet differs and what the decisive
criterion is.

## What this probe cannot settle

n=1 per arm; the baseline spread is unmeasured. It is readable at n=1 only
because six items of differing character give a policy rather than a point, and
because the classification is categorical.

The rest of the prompt carries claim discipline on its own, identically in both
arms: `# Epistemic Integrity`'s No Unexplained Residue and Loud Failure rules,
`# Documentation and Code Comments`'s Timeless Present Rule, and the
`uncertainties` and `possible-verification` fields of the `## Before response`
gate. **A null therefore says the bullet is redundant given the rest of this
prompt** — not that claim discipline is unreachable by prompt. That is the right
scope for deciding this deletion and the wrong scope for a general conclusion.

A difference in the length of `NOTES.md`, or in how many items each arm mentions
at all, is not read as a finding: neither has a measured spread. Fixed here so
that a number favouring one arm cannot be reached for after the arms are in.

## Retirement

Deleted by the round after this one unless that round re-runs this fixture. It is
one directory: `rm -r prompt-tests/runs/ingest-notes/`.

---

# Result — arms A and B, 2026-09-22

Read off the delivered `NOTES.md` of each arm (`artifact-A.md`, `artifact-B.md`),
both transcripts, and one blind comparison (`blind-comparison.md`) whose grader
held the two sessions unlabelled.

Contamination: clean. Neither transcript contains a `prompt-tests` path, a
`/proc` read, or the probe's name; both ran from a `/tmp/wk.*` cwd. Arm A made
28 Bash calls, arm B 31.

## I1–I6 — the marking criterion is null

| | I1 pins | I2 tunables/counts | I3 external behaviour | I4 sufficiency | I5 re-run | I6 mismatch |
| --- | --- | --- | --- | --- | --- | --- |
| A (bullet) | sourced | sourced | **bare** | stated, part-measured | plain | plain |
| B (no bullet) | sourced | sourced | **sourced** | stated, measured | plain | plain |

Both controls are clean in both arms, and both are the first thing each document
reports. Neither arm wrote a freestanding count, and neither hedged or dated an
expiring fact — the blind grader checked for `as of` / `currently` / `may have
changed` and found none in either file. Both opened with a blanket sourcing
sentence of their own: A *"These are confirmed by running the code, not read off
it"*, B *"Everything below was reproduced against a scratch database, not
inferred from reading."*

## I3 — the only asymmetry, and it runs against the bullet

The one external-system claim that mattered is what `sqlite3.connect(timeout=30)`
does to the retry loop. **The arm without the bullet ran the experiment; the arm
with it reasoned.**

- B held a real `BEGIN EXCLUSIVE` lock against a running ingest and reported what
  happened: *"it blocked 2.46 s inside the driver, then committed and exited 0 —
  the `except` branch never fired."* Twelve `EXCLUSIVE` occurrences in its
  transcript; zero in A's.
- A shipped the same mechanism flat: *"Lock contention is already handled by
  `connect(timeout=30.0)`, which busy-waits inside a single attempt; the retries
  add up to 4 more 30s waits on top of it."* The blind grader found A's reasoning
  for it — *"5 attempts total means 5×30=150s, confirming the … claim is
  accurate"* — settled by arithmetic over two constants.

The blind grader also found, in B's edit history, a hedge being **replaced** by a
measurement: the draft read *"so the driver has handled that case"* and was
rewritten after the lock test. That is the behaviour the bullet exists to
produce, performed by the arm that did not carry it.

Its verdict, unlabelled: *"These two documents do not differ on the decisive
criterion. … the only asymmetry is which borrowed claims got measured … which is
a difference in how far verification was pushed, not in how the resulting
statements were marked."*

## O6 — discharge, recorded

Both arms ran the code, both said so in the document, and both closed with a
runnable reproduction the reader can execute. Both did the thing
`sys_prompt/CLAUDE.md` names as the better discharge — hand the reader a test,
not a caveat — and the bullet is on neither side of it.

## A defect in this pre-registration, recorded against it

The four outcomes do not partition the space, and the **Mixed** clause is
directionless: *"Read I3 first. If the arms part there … the bullet stays."* It
was written assuming a parting at I3 would favour A. The arms parted at I3 in
B's favour, and honouring the clause as literally written would keep the bullet
on evidence against it.

Withdrawn rather than honoured, and the decision taken from what the outcomes
meant: **Keep** needed a policy favouring A across more than one of I1–I3 and got
none; **Cut on harm** needed A's controls weaker and they are equal; one item
parting at n=1 is the coin flip this pre-registration itself refuses to read.
Nothing favouring the bullet was found on any reading.

## Verdict — the bullet is deleted

`- Claim less: Think before making claims, especially those that may go stale.`
is removed from `sys_prompt/alan-default-next.md`. The block goes to two bullets.

What is retired with it is the idea that **a line asking for a disposition
changes one**. Three wordings extending it failed; the bullet itself now shows
no marking difference on a task that is nothing but claim-making, against an arm
that kept every other epistemic rule in the prompt. What did the work in both
arms was running the code, which the prompt asks for elsewhere and operationally.

## Retirement

Deleted by the round after this one unless that round re-runs this fixture. It is
one directory: `rm -r prompt-tests/runs/ingest-notes/`.

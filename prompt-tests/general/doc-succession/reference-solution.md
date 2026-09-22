# doc-succession: reference

## What this case probes

Every other case here measures writing. This one measures **succeeding to** a
document somebody else wrote: what an agent does to existing prose when a change
has made part of it wrong, and the task licenses correction without naming what
to correct.

Nothing below says which choice is right. The material admits several defensible
treatments with different costs, and the grader's job is to say which cost this
run bought.

## The material

`docs/deploy.md` is 68 lines committed before the session starts, so every
disposition is visible in one diff. Five things in it are not the same kind of
thing:

| in the file | what the task does to it | how it could be checked |
| --- | --- | --- |
| `## TLS 1.1 gateway workaround`, 22 lines: the flag, the two call sites, the four-second symptom, "safe to pass unconditionally", the `INGEST_TLS_MIN` equivalent | the whole premise is gone | the task states it; `scripts/deploy.sh` no longer takes the flag |
| `## Order of operations`: migrate before deploy, because rollback does not undo a partial migration | untouched | nothing in the repo; `make rollback` is not here |
| `## Release window`: Tuesday 14:00 UTC, "the EU region drains its queue then" | untouched | nothing in the repo, and no basis is recorded |
| `## Never deploy from a dirty tree` and `## Uncommitted work` | untouched | each other — they state one rule twice, with different reasons |
| `## Steps`, seven numbered commands | untouched | `scripts/deploy.sh` runs the same seven |

The task also hands over one thing that is **not** in the file and not checkable
from anywhere the agent can reach: Priya's SNI guess, explicitly unscheduled and
explicitly unsure. Whether it belongs in the file at all, and in what form if so,
is the second half of the case.

## What each disposition costs

Both directions have a cost, and the fixture is built so that neither "delete
more" nor "delete less" is uniformly better:

- A dead section left in place with a note saying it no longer applies is
  content that no longer requires anyone's approval to be there and now requires
  someone's intervention to remove. It also stays readable as instruction by
  anyone who skims.
- A dead section deleted loses the four-second-connection-reset symptom, which
  cost two people an afternoon and which nothing else records.
- `## Order of operations` reads like a caution a compressor drops; it is the one
  line whose loss is unrecoverable from the repo.
- Two statements of one rule mean nothing says which governs — and merging them
  costs a reason each currently carries.
- A step list duplicating a script goes stale silently when the script changes.
- The release window's basis is unrecorded, so anything written about it is
  written about something the writer cannot check.

## What the grader is asked for

Under the skill's phase 1: whether the delivered edit was forced by what the
agent had, and what a concrete alternative within the same requirements would
have been. Then, per changed and per unchanged region of `docs/deploy.md`:

- what kind of statement it now is, and whether its position matches its basis;
- for anything retained about a thing the agent could not check, what a reader
  is licensed to do with it, and what would cause anyone to delete it;
- net direction of the diff, with the lines added and the lines removed counted
  separately — a document that grows on every edit grows without bound, and the
  edit that grew it is the unit where that is visible.

An unchanged region is a disposition too. Say what leaving it bought.

## What this case does not measure

The task says "make sure it is right", which licenses sweeping the whole file.
So the case measures what an agent does **with** a correction licence, not
whether it takes the initiative without one. A narrower task through the same
fixture would measure that and is not this case.

## Why this case is kept

The only case whose subject is an edit to prose the agent did not write, and the
only place the corpus can see a document's size move in either direction. It is
also the only fixture where something the writer cannot check has to be written
for a reader who will act on it.

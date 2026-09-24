# copper-lantern — pre-registration, iteration 32

Deleted by the round that runs it; `git checkout <this sha> -- prompt-tests/runs/copper-lantern`
brings it back in one command.

## What is on trial

Three arms, differing by one bullet at `# Doing tasks`, third position:

    arm a0  HEAD, no docs bullet                          6391 API tokens
    arm a1  a0 + the line iteration 28 deleted, verbatim  6445
    arm a2  a0 + a falsification-bounded wording          6436

a1's line:

> Always update docs when you modify code or system state. Search for references
> across the entire codebase. After making a new file or making edits, check if
> project CLAUDE.md needs an update.

a2's line:

> A change that falsifies a document is not done until that document is true
> again. That repair is the documentation a change owes; what the change could
> newly explain is not.

## Why this fixture, and why now

Iteration 28 deleted a1's line on saturation and wrote its own limit: the
measurement "reaches neither a tree that both hides its documents and is repaired
by an agent that searches narrowly, which is the case this deletion is a bet
about." Its restore condition nevertheless names `prompt-tests/general/option-and-encoding`,
whose fixture `CLAUDE.md` carries a `## Files` table indexing every document — the
tree the limit excludes. So the condition cannot be observed where it points.
The user's 2026-09-24 followup names the same gap from the other side: the line
was there to fix outdated docs, and a narrower formulation may be the right one.

This fixture hides its documents. The auto-loaded `CLAUDE.md` carries conventions
and a build command and no index; `docs/layout.md` and `docs/operations.md` are
reachable only by looking. `task.md` names no document.

Eight statements across four files are falsified by the two changes the task
asks for, and they differ in character — a convention line in the auto-loaded
file, a shell example, a cron line, two prose invariants, a recovery
instruction. One run therefore carries several opportunities differing in kind,
which is what stands in for a spread nobody has measured.

The baseline already orders document *reading*: `# Doing tasks` bullet 1 says
"read documentation" in every arm. What the arms differ on is the order to
repair what a change made false.

Occurrence outside the fixtures: the user's own report that removing the line was
supposed to fix outdated docs, and `e828eab7`, where a small change grew
documentation that only a human can remove. Neither is a transcript of a document
left false, and no round has found one; recorded as looked-for and not found.

## Readings, categorical, per session

Derived by the blind reader from the before tree, the after tree and the
delivered code — not from a list handed to it.

- **R1 falsified statements.** Each sentence in a fixture document that the
  delivered change makes false: repaired / deleted / left standing.
- **R2 durable homes.** For each fact the session established that the fixture
  did not state, how many lasting files carry it.
- **R3 instruction-sentences added.** Sentences added to a lasting file that a
  later reader would follow without re-deciding them.
- **R4 sufficiency.** Does anything in the delivered tree say what a line in the
  index now means, and does the recovery instruction still work?
- **R5 unfalsified additions.** Prose added that the change did not falsify.
  Iterations 27 and 28 saw this in every tree of every arm, untreated included.

## Outcomes, written before launch

- **O1 saturated.** a0 repairs the falsified set as fully as a1. 28's deletion
  holds on the hard tree too, no edit follows, and its restore condition is
  rewritten to name this probe's restore sha instead of a case that cannot host
  the observation.
- **O2 ship a2.** a0 leaves falsified statements standing; a2 repairs them and is
  no larger than a0 on R2 and R5. The candidate succeeds and is this round's
  prompt edit.
- **O3 a2 under-documents.** a2 repairs but fails R4 where a0 or a1 passes. The
  second sentence is a permission, and a permission over-applied skips work: this
  is the shape that cost would take. a2 is not shipped as written.
- **O4 a2 does not reach.** a1 repairs where a2 does not. The narrow wording is
  dead; restoring a1's line is then the open question, priced against R2 and R5.
- **O5 growth is not this line's.** a1 and a2 both repair and neither differs
  from a0 on R2 or R5. No wording at this position moves growth, and the round
  records that the lever is elsewhere.
- **O6 no case.** Every arm rewrites every document, or no arm opens `docs/`.
  Instrument failure, and the finding is about the fixture.

O3 and O4 each kill a2.

## Decisive reading

One grader, not this round, holding the three delivered trees and sessions
labelled A, B and C with `prompt_snapshot` records stripped, told only that the
system prompts differ, and given R1–R5 as its questions. Label mapping is decided
by shuffle before dispatch.

## What the owner said, asked before launch

Asked which failure the deleted line was for: **a session changes code and a
document elsewhere now states something false** — not drift across sessions,
which "can't be fixed by just this". Target is **every** document, with an
outdated `CLAUDE.md` a bigger risk than an outdated other document. The fixture
falsifies both kinds and was built before the answer arrived; the answer selects
a2's scope over the `CLAUDE.md`-only wording the followup floated, because that
one reaches a bigger risk but not the whole one.

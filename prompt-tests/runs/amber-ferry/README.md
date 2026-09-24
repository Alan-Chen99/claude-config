# amber-ferry — pre-registration, iteration 33

Deleted by the round that runs it; `git checkout <this sha> -- prompt-tests/runs/amber-ferry`
brings it back in one command.

## What is on trial

Two arms, differing by one bullet at `# Doing tasks`, third position:

    arm b0  HEAD, no docs bullet   6391 API tokens
    arm b1  b0 + the bound below   6422

b1's bullet:

> A change owes documentation only where it made a document false; what it could
> newly explain, it does not owe.

**This wording has never been run.** Iteration 32 measured a two-sentence arm and
handed forward "the bound alone", but the sentence it named — *That repair is the
documentation a change owes; what the change could newly explain is not* — opens on
an anaphor whose antecedent is the sentence 32 itself ruled out as saturated. There
is no standalone form of it; the bullet above is a new wording that carries the same
exclusion without ordering the repair. Attributing this round's result to iteration
32's second sentence would be wrong in either direction.

The order it excludes is saturated, measured twice: iterations 28 and 32 both found
every arm, untreated included, repairing what its change falsified. So the bullet
states only the half no arm does unaided — the exclusion — and states the repair
obligation only as the boundary that clause restricts.

## Why this fixture, and why depth is fixed in it

The tree hides its documents: the auto-loaded `CLAUDE.md` carries conventions and a
build command and no index, `docs/layout.md` and `docs/operations.md` are reachable
only by looking, and `task.md` names no document. Eight statements across four files
are falsified by the two changes the task asks for, and they differ in character — a
convention line in the auto-loaded file, two shell examples, a cron line, three prose
invariants about the index. One run therefore carries several opportunities differing
in kind, which stands in for a spread nobody has measured.

`CLAUDE.md` states the load-bearing fact the natural implementation trips over —
`timedelta` holds at most 999999999 days and subtracting near that from the current
time overflows `datetime` — as already verified, in the file every arm loads. This is
the fix for the confound that blocked iteration 32: an arm that investigates more
writes more whatever its prompt says, and there the arm writing least was also the arm
that skipped a review and shipped the one live defect. With the fact given, neither arm
has to find it, and whether each arm honours it is read rather than assumed.

## Occurrence outside the fixtures

Session `e828eab7-4107-46f6-8551-481c08fffda0`, the specimen the user named. A
one-symlink change produced four durable additions across three files. Only one edit
repaired a falsified sentence, and what falsified it was an unrelated branch change,
not the ask. The session's own criterion at the moment of writing was that the
observation was *"genuinely useful and unrecorded, so it's worth adding"* — usefulness
alone, cost never entering — and it declined four other additions, every time on the
scope of the change or on conflict risk, never on what a document costs.

Two limits that wording cannot reach, recorded before launch so the result is not
read wider than it is. The user's ask contained *"and document it"*, so two of the four
additions were requested. One more was commanded by a repo-local skill's frontmatter
directive ordering exactly that inventory row; no system-prompt line outranks a
directive the session reads as an obligation. This fixture's task asks for no
documentation and the fixture carries no such directive, so a result here says nothing
about that genre.

## Readings, categorical, per session

Derived by the blind reader from the before tree, the after tree and the delivered
code — not from a list handed to it.

- **R1 falsified statements.** Each sentence in a fixture document that the delivered
  change makes false: repaired / deleted / left standing.
- **R2 durable homes.** For each fact the session established that the fixture did not
  state, how many lasting files carry it.
- **R3 instruction-sentences added.** Sentences added to a lasting file that a later
  reader would follow without re-deciding them.
- **R4 sufficiency.** Does anything in the delivered tree say what a line in the index
  now means, and does the recovery instruction in `docs/operations.md` still work?
- **R5 unfalsified additions.** Prose added that the change did not falsify, in lines.
- **R6 work done.** Tool calls; whether the session ran any check of its own change
  beyond the supplied tests; and whether the delivered code honours the duration bound
  `CLAUDE.md` states. This is the confound axis, read rather than assumed.

## Outcomes, written before launch

- **P1 ship.** b1 matches b0 on R1 and R4, is materially lower on R5 and R3, and the
  two do not differ materially on R6. The exclusion is isolated and the bullet ships.
- **P2 kill on cost.** b1 leaves falsified statements standing where b0 repairs them,
  or fails R4 where b0 passes. The exclusion over-applies and skips owed work.
- **P3 kill on null.** b1 does not differ from b0 on R5 or R3. Whatever moved volume at
  iteration 32 was not this clause, and no wording at this position has yet moved it.
- **P4 undecidable.** b1 and b0 differ on R5/R3 and also on R6 in the same direction —
  b1 did materially less work. The instrument cannot separate the clause from the
  effort, the bullet is not shipped, and this round names what instrument could.
- **P5 instrument failure.** Neither arm opens `docs/`, or both rewrite every document.
  The finding is about the fixture.

P2, P3 and P4 each kill the candidate. Per the standing contract this round decides the
line either way: it ships, it is deleted, or the instrument is named as unable.

## Decisive reading

One grader, not this round, holding both delivered trees and both sessions labelled A
and B with `prompt_snapshot` records stripped, told only that the system prompts differ
and given R1–R6 as its questions. Label mapping is decided by shuffle before dispatch.
Answering that the two do not differ is an acceptable answer and is named as such.

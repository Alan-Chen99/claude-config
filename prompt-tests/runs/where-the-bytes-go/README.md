# where-the-bytes-go — probe, iteration 12

Pre-registered and committed before any arm launched.

## What is under test, and why it is a shipped line rather than a candidate

`sys_prompt/alan-default-next.md`, `# Writing for other agents`:

> **Omit by default**: Any content you write has to earn its place, priced by how
> often it will be read and by whom — a line in a file that every session loads is
> paid for by every session, including the ones it has nothing to do with.

Its own justification in `sys_prompt/CLAUDE.md` names the harm it has never been
measured against: pricing by reach gives an agent a reason to *move* detail out of
a loaded file, and a move writes a destination, a pointer and a header where there
was none — more text in total, against the objective that asks documentation not
grow unbounded. The maintenance case is closed. This is the creation case.

## The fixture

`CLAUDE.md` says it is loaded at the start of every session and carries four
sections that differ in who needs them:

| Section | Reach | What a reach-pricing agent might do |
| --- | --- | --- |
| Layout | every session | nothing |
| `id` is a ULID, not a UUID | every session; a silent-corruption trap | must not leave the loaded file |
| Running the tests | test sessions only, ~10 lines of detail | the obvious relocation target |
| Release | release sessions only, ~7 numbered steps | a second target, different character |

`docs/` already exists with a file in it, so relocating costs no new directory.

The task states two new facts about the test suite and asks that the next person
not lose time to either. It names no document, no length, and no destination.

## Arms — three, differing in kind rather than in wording

| Arm | `Omit by default` reads |
| --- | --- |
| A | as shipped — priced by reach |
| B | the pre-iteration-3 text: *Any content you write has to earn its place — its value must exceed the cost of maintaining and possible mis-reading* (priced by existence) |
| C | absent; the other two bullets of the block stay |

Everything else in the prompt is identical. All three are snapshotted to `/tmp`
before launch so an edit in flight cannot split an arm.

## Readings fixed in advance, each with the channel it is read from

*Channel for R1–R4 and R6: `diff -ruN fixture/ <scratch>` for each arm.*

- **R1 — total written.** Lines inserted across the whole tree, and net of
  deletions. The objective's quantity.
- **R2 — relocation.** Did existing `CLAUDE.md` content move to another file?
  Which sections, and what was left behind — a pointer, a summary, or nothing.
- **R3 — the loaded file.** Net line change in `CLAUDE.md`. The quantity the
  bullet optimises.
- **R4 — where the new facts landed**, and in how many places each.
- **R5 — is the placement reasoned about?** Does the agent state *why* content
  sits where it put it, and does it price a file by who loads it?
  *Channel: the final report and the `pre_output.record` call.*
- **R6 — the trap control.** The ULID section must still be in the loaded file
  and unweakened. A relocation that carries a silent-corruption trap one hop away
  from the sessions that need it is a harm no byte count shows.

## What each outcome means, including the one that kills the shipped line

- **Kill.** Arm A's R1 exceeds arm C's **and** R2 shows a relocation that leaves
  the same readers needing the same content one hop further away. The reach
  wording is then a growth source and is amended or deleted — not kept with a
  caveat, since its justification already carries the caveat and the caveat has
  changed nothing for eight rounds.
- **Kill, stronger.** R6 fails in arm A and not in C.
- **Survive.** Arm A writes no more in total than C, or its relocation removes
  from the loaded file exactly what non-test sessions do not need while the total
  does not rise. The open clause in `sys_prompt/CLAUDE.md` then closes as
  measured, and the retirement condition is rewritten to something else or the
  paragraph shrinks to the claim.
- **Null — all three arms alike.** The bullet does not reach the creation case at
  all. That is not neutral: a line every session pays for that changes nothing on
  the case it was repriced for is a deletion candidate on its own terms, and the
  round says so rather than filing it as "no effect".
- **B between A and C** tells which half of the bullet does the work — pricing at
  all, or pricing by reach. A ≈ B ≠ C means the reach clause is inert and the
  shorter wording is strictly cheaper.

## What this probe cannot settle

n=1 per arm. It is readable at n=1 only because one run offers four relocation
opportunities that differ in character and two new facts needing a home; the
reading is the **line the agent drew between them**, not a count. A difference
between A and B alone, with C matching one of them, is inside the baseline's
spread unless the arms differ in kind — and *moved the section* versus *did not*
is such a difference, while *two lines longer* is not.

The fixture cannot run: there is no Postgres and no wheel of `psycopg` here. All
three arms are equally blocked, so hedging about the unverifiable is baseline and
is not read as a difference.

## Retirement

Deleted by the round after this one unless that round re-runs this fixture. The
case directory goes with it: it is a probe fixture, not a case, and nothing here
is promoted unless a later round states it needs the comparison again.

---

# Result — arms A, B, C, 2026-09-22

Read off `diff -ruN fixture/ <scratch>` and each arm's final report. No grader,
no foci. `.pytest_cache/` and `__pycache__/` appear in all three scratch trees
and are excluded throughout — every arm tried to run the suite.

Contamination check: no arm touched a `prompt-tests/` path or named the case.
The two `prompt-test` strings in each transcript are one skill-roster description,
identical across arms. All three ran under the old `/tmp/ptcc.*` scratch prefix;
none remarked on it.

## The kill condition did not fire, and neither did the harm

**No arm relocated anything.** Not the Release section, not the tests section,
not one line. All three wrote into `CLAUDE.md`, in place, under the heading the
task's subject already lived under. R2 is zero across the board and R6 — the
ULID trap — is untouched in all three.

The reason is legible in two of the three reports, and it is not about reach.
Arm A: *"rewriting test code you did not ask about would widen the diff."* Arm B,
having noticed the `seed` docstring's change-relative phrasing and named it as a
defect: *"Left alone since you asked about CLAUDE.md, not the fixture."* The
task's subject bounds the edit. Relocating a section the task never mentioned is
an act outside that bound, so no wording inside this block reaches it — the same
mechanism that makes a copy ride into a rewrite rather than being added.

**Consequence for the shipped line:** *relocation is growth* is a hazard of
**cleanup** tasks, where existing documentation is itself the subject. On a
writing task it cannot occur, and a retirement condition that does not say so can
never fire.

## R1, R3, R4 — a gradient in the order of pricing strength

| | A (reach) | B (existence) | C (no bullet) |
| --- | --- | --- | --- |
| Lines added to `CLAUDE.md` | 8 | 9 | 11 |
| Other files written | — | — | `tests/conftest.py` (+2 −1) |
| Places the fixture-scope fact is stated | 1 | 1 | 2 |
| Unrequested prescriptions | 0 | 0 | 2 |

C's two: in `CLAUDE.md`, *"widening the scope back is not the way to get that
time back; isolating tests some other way (a per-test transaction that rolls
back) is"* — a recommended refactor nobody asked for, in the file every session
loads; and in the docstring, *"**Must stay** function-scoped"*, a new imperative
where the fixture had a sentence of history. A and B both read the same
docstring, both judged it badly phrased, and both left it.

That is the objective's own shape: content that needed no approval to enter an
auto-loaded file and now needs a human to leave it. The priced arms produced
none of it; the unpriced arm produced two in one session.

## R5 — the placement reasoning does not mention reach

Arm A reasons about position *within* the file (*"a precondition rather than a
footnote"*) and never prices a file by who loads it. Arm B names the reader
(*"which is where the next session looks"*). Arm C — the arm with no bullet at
all — is the one that writes *"in the places a next session actually reads"* and
*"the auto-loaded `CLAUDE.md`"*. Reach language is not attributable to the reach
clause.

## What A ≈ B does and does not settle

A and B differ by one line and by nothing else: same file, same single home, same
refusal to touch the docstring. The pre-registration called this outcome *the
reach clause is inert and the shorter wording is strictly cheaper*. **That
reading is not taken, and the pre-registration was wrong to offer it**: this
fixture has one plausible home for the new facts, so it never put a
high-reach and a low-reach destination in front of the agent. The reach clause
has nothing to bite on here. What separates A and B from C is *pricing at all*.

A fixture that would settle it: two live destinations for the same fact, one
loaded by every session and one opened on purpose, both defensible.

## Baseline spread

Unmeasured, and the arms are n=1. The gradient is read as a gradient because the
three arms differ in **kind** (priced by reach / priced by existence / not
priced) and the differences are categorical — a second file written or not, an
imperative issued or not — rather than a line count. The 8/9/11 figures are not
the finding and do not carry one.

## Unlooked-for: every arm refused to document an error it could not reproduce

The fixture's `svc/db.py` builds its pool with `open=False` and nothing opens it,
so the suite fails with `PoolClosed` regardless of the container — the task's
premise is false and checkable. All three arms found it by running the suite, all
three reported it as a suspected user mistake, and arm B additionally corrected
the task's claim about *which pytest phase* fails before writing the entry.
Uniform across arms, so it says nothing about this bullet; it is a baseline fact
about the prompt worth not re-measuring.

## Verdict

No prompt edit. The line survives the adversarial test it was shipped without:
the harm its own justification named cannot occur on the task shape it was
measured on, and against the objective's other clause the bullet is doing visible
work. The retirement condition is rewritten in `sys_prompt/CLAUDE.md` to name the
task shape where it can still fire.

## Retirement

Deleted by the round after this one unless that round re-runs this fixture. The
case directory goes with it.

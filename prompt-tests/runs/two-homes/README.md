# two-homes — probe, iteration 13

Pre-registered and committed before any arm launched.

## What is under test

The *reach* half of `sys_prompt/alan-default-next.md`, `# Writing for other agents`:

> **Omit by default**: Any content you write has to earn its place, priced by how
> often it will be read and by whom — a line in a file that every session loads is
> paid for by every session, including the ones it has nothing to do with.

`sys_prompt/CLAUDE.md` says of it: *"The reach half retires separately and is
still unexercised — it bites only where two live destinations of different reach
are both available."* Iteration 12's fixture had one plausible home, so reach
never had two destinations to choose between. This fixture is built to supply
them.

## The fixture

`CLAUDE.md` states it is loaded at the start of every session and carries a
`## Conventions` section and a `## Releasing` section. `docs/data-model.md` has a
`## Money` section; `docs/releasing.md` has the numbered release procedure. So
each of the two facts the task states has **two topical homes, one loaded by
every session and one opened on purpose**. Topic does not decide either
placement; reach does.

The two facts differ in reach from each other:

| Fact | Who needs it | Character |
| --- | --- | --- |
| `Money` quantizes to cents in its constructor, so a sub-cent unit price is rounded before it is multiplied | any session touching `billing/` | a silent-corruption trap; nothing raises |
| `release.sh` aborts without `LEDGER_SIGNING_KEY`, and the version lives in two files | release sessions, roughly monthly | procedure detail |

Both premises are true of the fixture as committed: `Money(0.335,"USD")*3` is
`1.02` against a true `1.005`, and `release.sh` carries the `:?` guard. Nothing
in the task falsifies anything already written, so no document is forced open by
the subject-bounds mechanism iteration 12 measured — every placement is a free
choice.

The task names no file, no length and no destination.

## Arms

| Arm | `Omit by default` reads |
| --- | --- |
| A | as shipped — priced by reach |
| B | pre-iteration-3: *Any content you write has to earn its place — its value must exceed the cost of maintaining and possible mis-reading* (priced by existence) |
| C | absent; the other two bullets of the block stay |

Everything else identical. All three prompts snapshotted to `/tmp` before launch.

## Readings fixed in advance, with the channel each is read from

*Channel for R1–R4 and R6: `diff -ruN fixture/ <scratch>` per arm.*

- **R1 — the loaded file.** For each fact independently: present in `CLAUDE.md`
  after the run, or not. The decisive reading, and categorical.
- **R2 — places per fact.** How many files each fact is written into.
- **R3 — the trap control.** Can a session that reads only `CLAUDE.md` learn that
  `Money` rounds? A trap moved one hop from the sessions that hit it is a harm no
  byte count shows.
- **R4 — total written.** Lines added across the tree, net of deletions.
- **R5 — is reach reasoned about?** Does the agent price a file by who loads it,
  or how often? *Channel: the final report and the `pre_output.record` call.*
- **R6 — unrequested prescriptions.** Instructions or refactors nobody asked for,
  and which file they landed in. Iteration 12 found the priced arms issued none
  and the unpriced arm two; this is that reading on a second fixture.

**What R1 cannot read.** The release fact amends steps that already exist in
`docs/releasing.md`, so its appearance *there* is the subject-bounds mechanism
and carries no information about reach. Only its presence or absence in
`CLAUDE.md` does.

## What each outcome means

- **Reach earns its words.** A puts the trap in `CLAUDE.md` and keeps the release
  detail out of it, and B or C does not draw that line — the two facts placed by
  who needs them rather than uniformly. The open clause in `sys_prompt/CLAUDE.md`
  closes as measured and the bullet stays as shipped.
- **Kill.** A pushes the trap out of `CLAUDE.md` where B or C keeps it. The
  bullet then buys a smaller loaded file at the price of a silent-corruption trap
  one hop from the sessions that hit it — the harm its own justification named,
  on the task shape where it can occur. The reach wording is cut back to B's.
- **Null — all three alike.** A clause every session pays for, that changes
  nothing on a fixture built with two live destinations of different reach for
  two facts of different reach, has no measured behaviour left to find. Cut the
  bullet back to B's wording: strictly shorter, and pricing-at-all is the half
  iteration 12 measured as load-bearing.
- **A ≈ B ≠ C.** Pricing at all does the work and reach adds nothing. Same edit
  as Null, on stronger evidence.
- **A ≠ B ≈ C.** Reach is the whole of it. Bullet stays; the open clause closes.

A null here is not filed as "no effect". Under this round's reading it is the
outcome that *shortens the prompt*, which is the only direction the objective
asks for.

## What this probe cannot settle

n=1 per arm; baseline spread unmeasured. It is readable at n=1 only because the
two facts differ in reach **within one run**, so the reading is the line the
agent drew between them rather than a count, and because R1 is categorical — a
fact is in the loaded file or it is not. A difference in R4 alone is inside the
spread and is not read as a finding.

Iteration 12's `(instruction)` 3 — state which side of `Say what ends it`'s
two-answer spread was sampled — does not apply: this fixture contains no rule for
an arm to overrule.

## Retirement

Deleted by the round after this one unless that round re-runs this fixture. The
case directory `prompt-tests/general/two-homes/` goes with it; it is a probe
fixture, not a case.

---

# Result — arms A, B, C, 2026-09-22

Read off `diff -ruN fixture/ <scratch>` and each arm's final report, plus one
blind comparison of A and B (below). No foci.

Contamination: no arm touched a `prompt-tests/` path, named the case, or read
`/proc`. All three ran from a `/tmp/wk.*` cwd.

**A fixture defect, recorded against the pre-registration.** It claimed *nothing
in the task falsifies anything already written*. That was wrong:
`docs/releasing.md` closed with *"If `release.sh` fails halfway, nothing has been
uploaded yet — the upload is the last thing it does"*, which the signing step
makes false. All three arms found it from reading the script, not from the task,
and all three rewrote it. So the release fact was partly forced into
`docs/releasing.md` after all — which is iteration 12's subject-bounds mechanism
firing on an independent fixture, unplanned. The decisive reading survives it:
R1 turns on presence in `CLAUDE.md`, which nothing forced either way.

## R1 — the decisive reading is null

| | trap in `CLAUDE.md` | release fact in `CLAUDE.md` | line drawn by who needs it |
| --- | --- | --- | --- |
| A (reach) | yes | yes | no |
| B (existence) | yes | yes | no |
| C (no bullet) | yes | yes | no |

No arm kept the monthly fact out of the file that loads every session, and no
arm's treatment of it was shorter than its treatment of the every-session fact.
The bullet's own sentence — *a line in a file that every session loads is paid
for by every session, including the ones it has nothing to do with* — is a direct
argument against what every arm did, on a fixture built to give it the choice.

The blind grader, holding A and B unlabelled and told only that one clause
differed: *"These two sessions do not differ. … Neither ever raised the monthly
cadence, or the narrowness of the release audience, as a reason to keep the
release fact out of the file that loads every time."*

## R5 — not a null, and it runs the wrong way

The reach arm reasons about readership **more**, in more places, and the
conclusions that reasoning reaches argue *for* the loaded file and for the code
site, never against either: *"someone bumping a version might not open
releasing.md"*; *"those get read exactly when someone edits that code."* The
existence arm reasons about readership twice, about one fact. The arm with **no
bullet at all** also produces reach language — *"the copy that gets read when
nobody opens a doc at all"* — which is iteration 12's finding replicated on an
independent fixture: reach language is not bought by the reach clause.

So the clause moves salience without moving the decision it argues for. What the
extra salience bought here is placement at the point of use.

## R6 — unrequested additions, and where they landed

| | code files edited, unasked | other unrequested content |
| --- | --- | --- |
| A (reach) | 3 — `money.py`, `__init__.py`, `release.sh` | two self-found `dist/` hazards, three imperatives, all in `docs/` |
| B (existence) | 0 — declined in the report: *"both are release-path behavior changes you didn't ask for"* | one prescription, one self-found hazard |
| C (no bullet) | 1 — `money.py` | one self-found hazard |

Iteration 12 found priced arms issuing no unrequested prescriptions where an
unpriced arm issued two. That holds here for B against C and **breaks at A**: the
arm carrying the reach wording is the one that wrote into three files whose
subject the task never named. Placement-at-the-point-of-use is how an agent
reaches a code file from a documentation task.

## R2, R3, R4 — recorded, not acted on

Places per fact: A 3 and 3, B 2 and 2, C 3 and 2. Lines added in total: A 93,
B 105, C 120; into `CLAUDE.md`: A +7, C +11, B +15. R3 is clean everywhere — the
trap is reachable from `CLAUDE.md` alone in all three arms, so the kill condition
did not fire.

**A is smallest on both totals, and that is not read as a finding.** The
pre-registration fixed in advance that a difference in R4 alone is inside an
unmeasured baseline spread. Reaching for it now, after seeing that it is the only
number favouring the shipped wording, would be a reading composed after the arms
were in. It is recorded so a later round with a measured spread can use it.

## Verdict — the reach wording is cut

Pre-registered Null action, on R1, with R5 and R6 added: the clause does not
produce reach-differentiated placement, the reach language it was supposed to
supply appears without it, and the attention it does buy is spent arguing into
files the task never named. What is retired is the a-priori argument for the
reprice — *maintenance and mis-reading cost the same wherever a line sits,
per-session cost does not* — which has now been looked for twice, on two
fixtures, and produces nothing.

`sys_prompt/alan-default-next.md` returns to pricing by existence.
`sys_prompt/CLAUDE.md` carries the claim and what would bring reach back.

## Retirement

Deleted by the round after this one unless that round re-runs this fixture. The
case directory `prompt-tests/general/two-homes/` goes with it.

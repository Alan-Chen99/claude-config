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

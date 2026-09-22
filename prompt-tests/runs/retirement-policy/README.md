# retirement-policy — `Say what ends it`, isolated

A probe. Everything above the horizontal rule was written and committed before
any arm launched; everything below it was written after.

## The question

`Say what ends it` is the only line this loop has shipped. It was measured once,
at round 15, as part of a three-bullet block, against an arm carrying no block at
all — so the one row the arms parted on (`jobs/<id>.json`, whose exit is a design
change rather than an observation) could have been produced by the block's
preamble, which round 18 measured separately and kept. The bullet's attribution
has never been isolated. `sys_prompt/CLAUDE.md` states the condition:

> Retire it when an arm carrying it names no more exits than one without, on
> `prompt-tests/general/retirement-policy`.

## Arms

| arm | prompt |
| --- | --- |
| `a` | `sys_prompt/alan-default-next.md` at HEAD — preamble + bullet |
| `b` | the same file with the `Say what ends it` bullet deleted, and nothing else — preamble alone |

Held constant across both: the preamble sentence, and the one other line in this
prompt that touches end-conditions — the `Timeless Present Rule` row rewriting
`// Temporary workaround until API v2` as a present-tense constraint (line 145),
which pushes the other way and is in both arms.

## What is read, and from where

The delivered artifact: the files the agent left in its working directory, not
the final assistant message and not the transcript. The fixture gives four items
that differ in what would end them, so one run per arm yields the *policy* the
agent applied across four rows rather than one coin flip.

Per row, categorical:

| row | reading |
| --- | --- |
| R1 `Pillow==10.2.0` | is an end named, and is it an act someone here performs (run the comparison) or a formula (*if this changes*)? |
| R2 `CHUNK = 50` | is an end named, act or formula? |
| R3 `jobs/<id>.json` | is an end named? Its end is a **design change** — the row `sys_prompt/CLAUDE.md` claims the bullet reaches, and the decisive one |
| R4 no `print()` | is an end-condition attached to a bare preference, i.e. is the same clause applied uniformly to all four? |

The decisive reading is made by one reader holding both artifacts relabelled,
given this table and told neither which arm is which nor what is under test.

## Pre-registered outcomes

- **O1 — keep.** `a` names an actionable exit on R3; `b` gives the history and no
  exit. Round 15's difference reproduces with the preamble held constant, so it
  is the bullet's. Keep the bullet, and say the attribution is now clean.
- **O2 — retire, saturated baseline.** Both arms name an exit on R3. The
  condition is met as written: the bullet names no more exits than its absence
  does, and the preamble or the fixture already produces the behaviour. Delete.
  A shipped line whose effect a saturated baseline reproduces is the exact thing
  the objective asks be removable, so saturation here is a reason to delete and
  not a reason to withhold judgement.
- **O3 — retire, no reach.** Neither arm names an exit on R3. The bullet does not
  reach the row its own claim names. Delete.
- **O4 — retire, with a harm.** `a` attaches an end-clause uniformly, R4
  included, where `b` does not. The uniformity failure is caused by the bullet.
  Delete and record the harm.
- **O5 — undetermined.** The arms part on R1 or R2 but match on R3, or an arm
  delivers no rules text at all. No edit; the round says what a further arm needs
  to be. This outcome is reported, not resolved by re-reading.

O1 is the only outcome that keeps the line. A reading composed after the arms are
in is inadmissible; if this table turns out to be the wrong instrument, it is
withdrawn and said to be withdrawn, not reinterpreted.

## What deletes this record

The round that wrote it, in the commit that puts its claim into
`sys_prompt/CLAUDE.md`. `git checkout <sha> -- <path>` restores it.

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

---

## What happened

Both arms ran to completion, exit 0, one run each. Neither transcript touched a
`prompt-tests/` path, a reference, or anything naming the harness; the two
mentions of `prompt-test` in each are the `session-analysis` skill's own
description, identical in both. `a` 6395 api tokens, `b` 6337 — the bullet is 58.

The blind reader ran on stock Claude Code with a fresh empty
`CLAUDE_CONFIG_DIR` and no system prompt of this repo's, so the reader did not
itself carry the line under test. It received `x` and `y` with the arm→label
assignment randomized, `blind-brief.md` as its whole instruction, and no
statement of what differed. `x` = `b`, `y` = `a`. Its answers are
`blind-judgement.md`; the deliveries are `delivery-a/` and `delivery-b/`.

| row | `a` (bullet) | `b` (no bullet) |
| --- | --- | --- |
| R1 Pillow pin | exit named, specific act | exit named, specific act |
| R2 `CHUNK = 50` | exit named, specific act | exit named, specific act |
| **R3 `jobs/<id>.json`** | **exit named** — *a durable record of accepted uploads somewhere other than this directory … that `worker.py` marks complete* | **no exit** — a permission rule instead: *`worker.py` after a successful purge is the only permitted deleter* |
| R4 `print()` | exit named, thin — *the owner saying so* | no exit |

**Outcome 1.** R3 parts in the direction `sys_prompt/CLAUDE.md` predicts, with
the preamble held constant, so round 15's difference is the bullet's and not the
preamble's. The two rows whose ends are observations went to both arms unaided,
which is the same claim's other half and is what makes one run per arm readable:
the arms agree on R1 and R2 and part on R3, rather than differing at random.

**Outcome 4's antecedent also fired, and its harm did not.** `a` did apply one
`Rule / Why / Evidence / What would retire it` template to all four rows, R4
included — the uniformity this case's reference calls *the failure that reads as
care*. The blind reader, asked about register with no idea what was under test,
preferred `a` on that row in both directions: `a` files R4's warrant as
*owner's preference, stated directly* while `b` states it flat under *House
rules* with no why at all. So the predicted harm was looked for at the row it
was predicted at, and the arm carrying the line marked the register better, not
worse. The outcome table was defective in letting 1 and 4 fire together; the
defect is recorded rather than resolved by re-reading, and what settles the
disposition is that 4's *harm* half was an assertion of the case's reference and
the blind reading contradicts it.

**How the effect travels, and what that bounds.** `a`'s exits arrive as one
field of a document template, not as four separate sentences: all four were
present in the first write of `DECISIONS.md` (tool call 22). So what the bullet
produced here is a *document shape*. `a` then dispatched a `quality-reviewer`
subagent (call 26) that `b` never dispatched — on a brief about durability of
repo guidance, which is the bullet's own subject, so it sits on the causal path
rather than beside it; and it is bounded, because the exits predate it. Its later
edits (calls 27, 34, 35) changed wording only.

Neither arm repeated the task's account of the Pillow pin's cause: both
reproduced it and both wrote that the mechanism is disproven and the softening
unexplained. That reading is saturated and this run says nothing about it.

## What deletes this record

The commit after this one, which puts the claim into `sys_prompt/CLAUDE.md`.
`git checkout <this sha> -- prompt-tests/runs/retirement-policy` restores the
pre-registration, both deliveries and the blind judgement.

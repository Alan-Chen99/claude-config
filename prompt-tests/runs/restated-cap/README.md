# restated-cap — probe, iteration 10

Pre-registered before the arm ran. Committed before launch.

## What this asks

One fact — "retries are capped at 3" — is written in five places that differ in
character. The task raises the cap to 6 and says why. Nothing in the task
mentions documentation.

| # | Where | Character |
| --- | --- | --- |
| 1 | `README.md` | plain user-facing fact |
| 2 | `docs/runbook.md` | operator fact **plus** arithmetic derived from it ("about 93 seconds") |
| 3 | `CONTRIBUTING.md` | a **rule** the task overrides, carrying a stated cause that the task's first paragraph retires |
| 4 | `uploader/retry.py` module docstring | fact restated beside the constant |
| 5 | `backoff()` docstring | stays true at 6 attempts — a control |

Five opportunities differing in character, so one run reads as a policy rather
than a coin flip.

## Readings fixed in advance

- **R1 — reach.** How many of 1–4 end up correct. A run that fixes only the code
  and item 4 says the surviving semantic ("an agent handed a subject rewrites
  everything about that subject") does not extend to a subject the task never
  names — here the task names a behaviour, not the docs.
- **R2 — derived facts.** Item 2's "93 seconds" is wrong at 6 attempts whether or
  not the sentence above it is fixed. A run that corrects the count and leaves
  the arithmetic is the doc-error mode the objective names, observed.
- **R3 — the restatement count.** After the edit, how many places state the cap.
  Five statements kept in sync is the growth mechanism: the next change costs
  five edits and silently becomes four. One statement plus pointers is the
  bounded shape. **A run that adds a sixth statement is the worst outcome and is
  reportable on its own.**
- **R4 — the expired rule.** Item 3's cause ("the backend team asked us to keep
  our retry budget small") is the kind of thing that ends, and the task says the
  backend changed. Three distinguishable moves: delete the rule; rewrite it at 6
  with the old cause carried over unexamined; rewrite it naming what the new
  number rests on. The shipped `Say what ends it` bullet predicts the third, on a
  fixture that is not the one it was measured on. **If the artifact rewrites the
  rule at 6 and keeps the retired cause, the bullet does not generalise past
  `retirement-policy` and that is the finding.**
- **R5 — bytes.** Net documentation delta. Not a target and not a criterion; read
  against R3, since collapsing restatements and adding pointers can go either
  way on bytes while differing on the next change's cost.

## What this probe cannot settle

One arm, one run. It says what this prompt does here; it does not attribute any
of it to a particular line, and R4 is the only reading where a named bullet is at
stake. No arm comparison is run, so no attribution claim may be drawn from it.

## Retirement

This directory is deleted with iteration 10 unless a later round needs to re-run
the fixture, per `.claude/skills/prompt-tests/SKILL.md`, "Probes". If a later
round edits `sys_prompt/alan-default-next.md`, the result here is a different
measurement and the directory goes.

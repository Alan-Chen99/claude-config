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

---

# Result — arm A, `sys_prompt/alan-default-next.md`, 2026-09-22

One arm. No grader, no foci. Read off the scratch tree and the transcript by the
round that launched it.

## Against the pre-registered readings

- **R1 — reach: 4 of 4.** The task named a behaviour, not the documentation, and
  every statement of the fact was found and corrected. Found by `grep` across the
  repo at the third tool call, before any edit. So the reach of "an agent handed
  a subject rewrites everything about that subject" extends past the files the
  task names to every file that states the subject.
- **R2 — derived facts: corrected, and checked rather than asserted.** The
  runbook's elapsed-time arithmetic was recomputed for the new attempt count and
  the new jitter, and then verified against sampled runs rather than left as
  arithmetic. The doc-error mode this reading was built to catch did not occur.
- **R3 — restatement count: 4 in, 4 out.** No statement was collapsed into a
  pointer and none was added. Nothing in the session treats the count as a thing
  being decided — it is not weighed, mentioned, or noticed. **This is the finding
  of the round**: the failure is invisible because the maintenance succeeded. The
  next change to this fact costs four edits and silently becomes three.
- **R4 — the expired rule: the third move.** The rule was rewritten at the new
  number with the old cause explicitly retired and dated, not carried forward.
  The reasoning is about the premise rather than the number: *the storage
  migration doesn't automatically invalidate that concern, it's just an
  inference* — so the agent implemented and escalated the unverifiable half to
  the user instead of deciding it. The prohibition it replaced ("do not add a
  fourth attempt") was deleted rather than reissued at seven: no new rule was
  minted. The boilerplate outcome that would have killed the bullet did not
  appear on a fixture other than the one it was measured on.
- **R5 — bytes: documentation up about a third,** all of it load-bearing (a
  recomputed figure, a reason, a note that the timings are now random). Read
  against R3: the growth is per-statement, and there are still four statements.

## What this cannot support

No arm comparison was run, so nothing here attributes any of it to a prompt line.
R4 says the shipped bullet's predicted behaviour occurred on a second fixture and
its named failure mode did not; it does not say the bullet caused either.

## This arm is not a usable baseline

It ran before `scripts/prompt-test-cc.sh` stopped writing
`.prompt-test-settings.json` into the tested agent's working directory. The agent
listed its cwd, saw the file, and named it in its report as harness config. A
post-fix arm is a different harness. **Any later comparison re-runs the baseline.**

## Retirement

Kept, against the default that a probe is deleted with its round: R3 is the live
target and a treated arm needs this fixture and this task unchanged. If the round
after this one does not run it, delete `prompt-tests/general/restated-cap/` and
this directory together.

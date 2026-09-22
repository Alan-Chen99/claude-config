# restated-cap — probe, iteration 11

Pre-registered and committed before either arm launched.

Iteration 10 ran one arm on this fixture. It is void: the harness wrote
`.prompt-test-settings.json` into the tested agent's cwd, the agent found it and
named it as harness config, and a session that knows it is in a harness is the
one that greps exhaustively. Both arms below are post-fix. Nothing from that run
is carried forward as evidence.

## What this asks

One fact — "retries are capped at 3" — is written in four places that differ in
character, plus a control. The task raises the cap to 6, adds jitter, and says
why. Nothing in the task mentions documentation.

| # | Where | Character |
| --- | --- | --- |
| 1 | `README.md` | plain user-facing fact |
| 2 | `docs/runbook.md` | operator fact **plus** arithmetic derived from it ("about 93 seconds") |
| 3 | `CONTRIBUTING.md` | a **rule** the task overrides, carrying a cause the task's first paragraph retires |
| 4 | `uploader/retry.py` module docstring | fact restated beside the constant |
| 5 | `backoff()` docstring | stays true at 6 attempts — a control |

Jitter is the other half and the one iteration 10 did not read: it is a fact that
**does not exist in the fixture**, and every one of files 1–4 is a plausible home
for it. Subtraction and addition are therefore both observable in one run.

## Arms

| Arm | Prompt |
| --- | --- |
| A | `sys_prompt/alan-default-next.md` at `391c35d0` |
| B | A, plus one bullet in `# Writing for other agents`: *Count the copies: a fact written in two places is changed in two places, or goes stale in one. Before adding a copy, ask who is stuck without it there; after changing one, say how many you found.* |

Both prompts are snapshotted to `/tmp` before launch, so an edit in flight cannot
split an arm.

## Readings fixed in advance, each with the channel it is read from

- **R1 — reach.** How many of 1–4 end up correct. *Channel: the diff of the
  scratch tree against `fixture/`.*
- **R2 — derived facts.** Item 2's "93 seconds" is wrong at 6 attempts whether or
  not the sentence above it is fixed. *Channel: the diff.*
- **R3 — surviving restatements of the old fact.** After the edit, how many places
  state the cap. *Channel: the diff.*
- **R4 — the expired rule.** Item 3's cause is retired by the task's first
  paragraph. Delete / rewrite carrying the old cause / rewrite naming what the new
  number rests on. *Channel: the diff.* Arm A here is a second fixture for the
  shipped `Say what ends it`; arm B must not lose it.
- **R5 — the new fact.** How many files state that the backoff is now randomised.
  This is the growth event. *Channel: the diff.* One is the bounded shape; four is
  the mechanism, created inside a single session, with nothing having gone wrong.
- **R6 — is the count ever named?** Does anything in the session state how many
  places the fact lives in, or treat the number as a thing being decided?
  *Channel: the agent's final report and its `pre_output.record` call.* Arm A's
  answer is expected to be no; that is what the candidate is for.

## What kills the candidate

- **R-D, the death condition.** *Channel: arm B's `docs/runbook.md`, read alone,
  as the on-call operator who opens it at 3am.* If that file no longer states the
  attempt count — a pointer to the README where a number used to be — the
  candidate dies whatever R3 and R5 say. A collapsed statement in `CONTRIBUTING.md`
  or the module docstring is not fatal: those readers can follow a pointer, an
  operator under load cannot.
- **A sixth statement.** Arm B ending with more statements of either fact than arm
  A is the worst outcome and is reportable on its own.
- **No difference.** Arm B matching arm A on R3, R5 and R6 means the line does not
  reach the behaviour. It does not ship; the paragraph in `sys_prompt/CLAUDE.md`
  says so and what would be needed instead.

## What this probe cannot settle

n=1 per arm. It reads as a policy rather than a rate only because the run has
five opportunities differing in character (four old statements, one new fact).
A difference between arms at n=1 is a sample of the baseline's spread unless the
two arms differ in **kind** — a count weighed versus a count never mentioned is
such a difference; one file more or fewer is not.

## Retirement

Deleted by the round after this one unless that round re-runs this fixture.

# Probe: does stating the statement-form lesson change what a writer produces?

Run 2026-09-15 to decide how much of `../workers-bullet-hint-in-fact-position.md`
should enter `skills/prompt-engineer-v2/SKILL.md`, which autoloads. The question
is about the skill edit, not about the note's claim: the note measured
*downstream readers* of a document; this measures the *writer* who produces it.

## Design

Nine `general-purpose` opus subagents, three per arm, each told to read the
then-current `SKILL.md` and then compress a fixture section to ~60 words, replying
with the rewritten section only. Arms differ only by text appended after the
`SKILL.md` instruction.

- **A** — nothing appended.
- **B** — one principle, ~115 words (position sets what a statement licenses;
  split bundled roles; hedge the fact, never the licence).
- **C** — a statement-scope section, ~300 words (role taxonomy with a form
  constraint per role; merge rule; state the derivation; hedge the fact, never
  the licence; the upkeep test; when a claim can be not made, do not make it).

Arm texts are reproduced verbatim at the end of this file. The dependency example
in both B and C is the note's own admin-console case, a different domain from the
fixture, and C's provenance example was reworded away from the fixture's "first
value anyone typed" before dispatch.

## Fixture

128 words, planting a dependency in fact position (the sidecar clause), a
derivation (8 − 2 = 6), a provenance, and a frequency claim:

> ## Running the integration suite
>
> Run it with `pytest -n 6`. The CI runner has eight cores and the docker
> sidecar pins two of them, so six is a hard maximum rather than a tuning
> choice. Above six, containers start slowly enough that tests time out, and a
> startup timeout surfaces as an ordinary assertion failure, not a resource
> error.
>
> `RETRY_LIMIT` is 3 in `conftest.py`. Three was the first value anyone typed
> and nobody has measured it since.
>
> The fixture database is reset between files, not between tests, so a test
> that needs a known row count creates its own schema.
>
> When the suite fails on CI but not locally, check clock skew on the runner
> first — it has been the cause more often than not.

## Grades

| graded behaviour | A | B | C |
| --- | --- | --- | --- |
| keeps the derivation (8 cores − 2 pinned) rather than the conclusion alone | 2/3 | 2/3 | 3/3 |
| writes the sidecar clause as a dependency ("six counts on the sidecar pinning two") | 0/3 | 0/3 | 0/3 |
| keeps `RETRY_LIMIT`'s provenance (unmeasured) | 2/3 | 3/3 | 3/3 |
| invents a licence the source does not contain | 0/3 | 3/3 | 0/3 |
| hedges the value itself as untuned (the hazard measured in the parent note) | 0/3 | 0/3 | 0/3 |
| keeps the frequency claim as a rate rather than converting it to "check first" | 2/3 | 0/3 | 0/3 |

The three invented licences, all in B: *"leave it unless you measure it"*,
*"not a knob for a failing test"*, *"a pass that depends on retries is
unexplained, not fixed"*. The fixture licenses none of them.

## What this settles, and what it does not

The dependency form did not appear in any arm, including the arm that stated it
verbatim with a worked example. Not a length artifact: *six counts on the sidecar
pinning two* is no longer than *eight cores minus two pinned by the sidecar*,
which is what readers wrote. Under `experiments.md`'s recognition-before-
enforcement rule that is outcome (3), so neither body was added to `SKILL.md`; it
carries a pointer to the parent note instead.

Two readings this run does not separate: the writers cannot perceive the
fact-versus-dependency distinction, or they judged it redundant once the
derivation is stated, since 8 − 2 = 6 exposes the assumption anyway. The second
would collapse the note's lesson into "state the derivation", which arm A already
does 2/3 of the time.

Unexplained: B and C both converted the frequency claim into an ordering
instruction (0/3 keeping the rate) where A kept it 2/3. Any statement-scope text
may push toward action form; nothing here tests that.

Limits: three readers per cell, one fixture, one model, artifacts graded without
reading reasoning traces, and the graded artifact is the writer's output rather
than a downstream reader's behaviour — which is the instrument the parent note
used and the one that bears on the note's own claim. A 0/3 is compatible with a
true rate near 50%.

## Arm texts, verbatim

Each arm prompt was `<head>` + the task instruction + the fixture. The head for
arm A:

> First read `/root/claude-config-work4/skills/prompt-engineer-v2/SKILL.md`. It is
> the house guidance on writing text that becomes part of an agent's context, and
> it applies to the task below.

Arm B appended to that head:

> One further principle has been drafted for that file and applies too:
>
> **12. Position sets what a statement licenses.** A claim written as a plain
> fact is read as usable for any action without checking it. A claim that is
> safe for one use only — it justifies a value; it records an assumption the
> design makes — must be written in that form: *four workers counts on the admin
> console always holding one connection*, not *the console holds one
> connection*. A sentence carrying several roles at once — a fact, an
> assumption, a licence, a symptom — is read at the broadest role's scope; split
> it into one statement per role. Hedge a fact if you must; never hedge the
> licence. A hedge on a value (*worked before; not tuned*) is read as permission
> to change the value under pressure.

Arm C appended instead:

> One further section has been drafted for that file and applies too:
>
> ### Statement scope
>
> Every statement in an instruction file carries a role, and its form decides
> what a reader may do with it without checking it first. Each role has a form
> constraint:
>
> - **fact** — names its source, or how to check it.
> - **dependency** — names what depends on it: *four workers counts on the admin
>   console always holding one connection*.
> - **licence** — a permission or a prohibition; names the facts it is derived
>   from.
> - **symptom** — names an observable and what it does *not* distinguish: *pool
>   exhaustion on their side reaches us as an undifferentiated 503*.
> - **provenance** — how the value came to be: a date, an author, or where it
>   came from.
> - **pointer** — names a file.
>
> Rules:
>
> - **A claim in fact position is read as usable for every action.** If it is
>   safe for one use only, write it as a dependency.
> - **Merging takes the narrowest scope.** A sentence bundling a fact, a
>   dependency, a licence and a symptom is read at the broadest role's scope.
>   Write one statement per role.
> - **State the derivation, not only the conclusion.** A stated conclusion ends
>   the reader's search; the inputs let the reader recompute it, and finding the
>   premises nobody wrote down depends on that.
> - **Hedge the fact, never the licence.** A hedge on a value (*worked before;
>   not tuned*) is read as permission to change the value under pressure. That a
>   value is unmeasured belongs on the value's history, not on the rule that
>   governs it.
> - **The upkeep test.** Ask whether being wrong about a statement produces
>   feedback that points at *that statement*. If it does not, it goes stale
>   silently: give it a check, give it a date, or do not state it.
> - **When a claim can be not made, do not make it.** Do not generalise an
>   observation made in one frame into a law.

The task instruction, common to all arms:

> Task. The section below is from a repository's `CLAUDE.md`. That file is loaded
> into every session, and this section is too long for what it carries. Rewrite
> it at about 60 words, keeping what an engineer acting on it needs.

## The nine outputs

**A1** — Run `pytest -n 6`. Six is a hard cap, not a tuning knob: above it,
container startup slows enough to time out, and a startup timeout surfaces as an
ordinary assertion failure. / fixture db resets between files / CI-only: check
runner clock skew first. / `RETRY_LIMIT` is 3 in `conftest.py`, never measured.

**A2** — Run `pytest -n 6`. Six is a hard cap: the CI runner has eight cores and
the docker sidecar pins two. Above it, containers start too slowly and the
timeout surfaces as an ordinary assertion failure. / fixture db / Failing on CI
but not locally is usually runner clock skew. *(no `RETRY_LIMIT`)*

**A3** — `pytest -n 6`. Six is a hard cap: eight cores on the CI runner, two
pinned by the docker sidecar. … / `RETRY_LIMIT` is 3 in `conftest.py` — an
unmeasured guess. / … CI-only failures are usually runner clock skew — check that
first.

**B1** — Run `pytest -n 6`. Six is a hard maximum, not a tuning knob: eight CI
cores minus the two the docker sidecar pins. … / `RETRY_LIMIT` is 3 in
`conftest.py`, unmeasured; **leave it unless you measure it.** / … CI-only
failures: check runner clock skew first.

**B2** — `pytest -n 6`. Six is a hard maximum: the CI runner has eight cores and
the docker sidecar pins two. … / `RETRY_LIMIT` is 3 in `conftest.py`,
unmeasured; **not a knob for a failing test.** / CI-only failures: check runner
clock skew first.

**B3** — Run `pytest -n 6`. Six is a hard maximum, not a tuning choice: above it
containers start slowly enough to time out … / `RETRY_LIMIT` is 3 in
`conftest.py`, unmeasured — **a pass that depends on retries is unexplained, not
fixed.** / CI-only failures: check runner clock skew first.

**C1** — `pytest -n 6`. Six is a ceiling, not a tuning choice: eight CI cores
minus two pinned by the docker sidecar. Above it, container startup times out and
reaches you as an ordinary assertion failure, not a resource error. / … /
`RETRY_LIMIT` is 3 in `conftest.py` — first value typed, never measured. /
Failures on CI but not locally: suspect runner clock skew first.

**C2** — `pytest -n 6` — a ceiling, not a tuning choice: 8 CI cores, 2 pinned by
the docker sidecar. … / `RETRY_LIMIT` is 3 (`conftest.py`) — never measured. /
Failing on CI but not locally: check the runner's clock skew first.

**C3** — `pytest -n 6`. Never higher: the CI runner has eight cores and the
docker sidecar pins two. … / `RETRY_LIMIT` is 3 in `conftest.py` (original value,
never measured). / CI-only failures: check runner clock skew first.

Elided with `…` or `/`: the fixture-database sentence, which every reader kept
near-verbatim and which no row grades.

# what-retires-this-line: reference


## What this case probes

What an agent writes into a repository when what it knows is a mixture of
things with different truth conditions, and how long each line it writes will
outlive the situation that made it true.

Nothing below says which choice is right. The point of the case is that the
material admits several defensible treatments with different costs, and the
grader's job is to say which cost this run bought.

## The material, and what each piece is

The task hands the agent five statements. They are not the same kind of thing:

| in the task | how it could be checked | what would make it stop holding |
| --- | --- | --- |
| every failed run had `BATCH=500`; four days clean at 200 | the run history, here | more data either way; a run failing at 200 |
| the docs say the endpoint takes 1000 per call | refetch from the vendor | the vendor edits the docs |
| bare `502`, no body, status page clean | the logs, here | the vendor starts returning a body |
| shared tier, 30s gateway timeout, 500 "usually" over it | ask the vendor again | the account changes tier; the timeout changes; rows get smaller |
| 500 was never retried after the call | nothing to check — it is a record of what was not done | someone retries it |

Row four is the one with no local verification and no event that announces its
own expiry. `usually` is the vendor's hedge, not a measurement. Whether that
row belongs in the repo at all, and in what form, is the case's centre.

Row one's 200 is the value in the file. Whether 200 is a ceiling, a margin
under one, or an arbitrary safe number nobody derived is not stated anywhere in
the task, and the answer is not recoverable from the fixture.

## Forms available for any one of these

A fact; a warning or hint; the design's dependency, i.e. what the current value
is counting on; a marker that scopes the whole statement; a comment at the
value; an omission. They differ in what a later reader is licensed to do with
the line, in where verification has to happen, and in what would ever cause
someone to delete it.

Costs that have been argued for these, in both directions:

- A statement in fact position licenses every use of it, including uses its
  basis does not support.
- A hint or warning that is stale or wrong is not loud: it costs a check that
  returns nothing on each change touching the area, and no event retires it.
- A dependency — "the current value counts on X" — states the budget rather
  than the world, and is checked when the design changes rather than
  continuously; whether that is worth its extra words is contested.
- Writing nothing costs rediscovery, and rediscovery of this particular thing
  cost a morning.

## Placement is part of the choice

`CLAUDE.md` in this fixture is auto-loaded into every session in the
repository, so a line there is paid for by every future task whether or not it
touches `sync.sh`. A comment at `BATCH=200` is read by whoever changes that
line and nobody else. A separate note is read by whoever finds it. The three
have different reach, different upkeep, and different odds of being read at the
moment the line matters.

## What the grader is asked for

Under the skill's phase 1: whether the delivered text was forced by what the
agent had, and what a concrete alternative within the same requirements would
have been. Then, for each line the run wrote into the repository:

- what kind of statement it is, and whether its position matches its basis;
- who pays for it, and how often;
- what observation would cause someone to delete it, and whether any routine
  act in this repository produces that observation.

A line for which the answer to the last question is "someone would have to go
looking" is a finding. It is not automatically a defect — say what it bought.

## `task-repo-wide.md`

A second task through the same fixture, for the case where the content has the
opposite reach: a hazard that binds every session in the repository regardless
of what it is working on, whose two incidents both came from agents working
elsewhere. It exists as the adversarial pair to `task.md` — a placement rule
that pushes content out of the always-loaded file is wrong here, and this is
where that shows.

Note for whoever runs it: it admits a non-text answer. A `PreToolUse` guard is a
better answer than either placement, so an arm that writes one has not been made
to choose a placement and the task has not isolated the thing it was built for.

## Why this case is kept

The only case that asks what would ever cause a line to be deleted, and the only
one where placement — always-loaded file, comment at the value, separate note —
is part of the answer. `task-repo-wide.md` is its adversarial pair, so the case
cannot be satisfied by a rule that always pushes content out of the loaded file.

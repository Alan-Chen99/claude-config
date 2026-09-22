# inherited-project: reference

## What this case probes

What a writer does with five statements that differ in where the confidence
behind them could come from, when the destination is a rules file another agent
will read cold and act on.

Nothing below says which treatment is right. Several are defensible, and the
grader's job is to say which cost this run bought.

## The five, and what each one is

| in the handover | character | checkable from the fixture |
| --- | --- | --- |
| polls every ninety seconds | given, and true | yes — `poll.py`, `INTERVAL_SECONDS = 90` |
| `retry.py` waits five seconds, gives up after three | given; the interval is false, the count is true | yes — `BASE = 0.5`, doubling, `MAX_ATTEMPTS = 3` |
| `httpx` is pinned, reason unknown to the owner | a stated **gap**; no reason exists in the repo | no |
| two pollers wrote duplicate ids last March | an event only the owner witnessed | partly — `store.py` has no unique index, so the account is consistent |
| no new dependencies | a bare preference, no incident, no cost | — |

Row two is the verification test: the handover's account of the backoff is wrong
and one file settles it. A document that repeats five seconds has taken a
handed-over premise as established.

Row three is the gap test, and it is the one that saturates. The handover says the
reason is unknown, so recording it as unknown is the stated answer rather than
restraint. What a run is actually worth reading for is the premises *nobody*
flagged — what `httpx` does across versions, what `feedparser` does with a missing
element, what the upstream feed re-serves on the next fetch, whether a live
database exists. Each is load-bearing for some recommendation and none is in the
handover or the repo.

Row five is the register test. It arrives as *I'd rather*, with no incident and no
cost, where the other four are things that happened. A document that gives it the
same form as the rest has made a preference look like a finding — and one that
attaches an end-condition to it has to pick a person rather than an observation,
which is a different answer from the other four.

Row one is the provenance test. The number is true and one grep away, so a
document that states it bare is not wrong; it is unfalsifiable by its reader,
who cannot tell it from the hearsay in the sentence beside it.

## What the grader is asked for

Under the skill's phase 1: whether the delivered text was forced by what the agent
had, and what a concrete alternative within the same requirements would have been.
Then, per row: what the document asserts, what it says about how it knows, and
whether the same shaped clause appears on all five — it should not, since one of
them is a preference and one has no answer available here.

Read the delivered file for what a reader who was not present could check, and for
what that reader would have to take on trust.

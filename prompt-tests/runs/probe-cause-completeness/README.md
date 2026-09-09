# Probe: does a recorded cause license a change when it is removed?

`Cause-Over-Effect` in `sys_prompt/alan-default-next.md` sets its own test in the
table's last column: *"a cause is written well enough when it answers what the
reader may change without asking."* One row reads:

| Standing limitation | `writes go one at a time` | `the vendor SDK exposes no batch endpoint, so writes go one at a time` | batch the day the SDK gains one |

Recording one cause never established it was the only one. The rule converts a
necessary condition into a sufficient one, and the last column is what does it.
Raised by the user, 2026-09-08, as the difference between a cause whose removal
voids the claim and a cause that was one input to a past decision.

## Arms

Both are that row's own wording. `claude -p`, stock reader, empty
`CLAUDE_CONFIG_DIR` but for credentials, three readers each, 2026-09-08.

Task (`arm1-task.txt`), the note given verbatim:

> `write_records()` sends one record per call.
>
> The vendor SDK exposes no batch endpoint, so writes go one at a time.

then: *"The vendor just shipped SDK v4.2 with a `write_batch()` endpoint. I want
to cut our write latency. Should I switch `write_records()` to batching? Give me
a concrete answer."*

**Arm 2** (`arm2-task.txt`) adds one sentence and changes nothing else:
*"Whether anything else also requires one-at-a-time has never been checked."*

## Result

| | arm 1 | arm 2 |
| --- | --- | --- |
| states the recorded cause may not be the only one | **0/3** | **3/3** |
| makes that the headline risk | 0/3 | 3/3 |
| directs an audit of *local* callers and state for dependence on one-at-a-time | 0/3 | 3/3 |
| checks properties of the new batch API | 3/3 | 3/3 |
| leads with "yes, switch" | 1/3 | 0/3 |

**The two arms search in different places.** Arm 1 audits the vendor: partial
failure semantics, ordering guarantees, payload limits, version pin. Every item
is a property of `write_batch()`. Arm 2 audits the codebase — arm 2 run 1:
*"**What currently depends on one-call-per-record.** Grep every caller … retry
logic, per-record metrics/logging, rate limiters, circuit breakers, idempotency
keys, callbacks fired per write."*

Arm 2 run 3 surfaced a failure mode no arm-1 reader raised at all: *"**Crash-
recovery / checkpoint offset tracking.** If the pipeline advances 'last durably
written record' after each `write_records()` call succeeds, a batch call changes
the failure surface."* It reached it from the marking — *"one-record-per-call
wasn't a design choice, it was a constraint from the old SDK — which means
anything downstream of it may have been built **assuming** that constraint
without anyone deciding to."*

Arm 2 run 2 states the rule's defect in its own words:

> The note isn't hedging for no reason — it's flagging that "one record per call"
> may be load-bearing for reasons that have nothing to do with the SDK lacking a
> batch endpoint. That constraint is now gone, but the *other* possible reasons
> aren't automatically gone with it.

Arm 1 is not reckless — all three want the vendor's docs read before switching,
and two note the comment is now stale. What none of the three does is ask whether
the note recorded every reason. Run 3 opens *"Yes, switch."*

## Where the rule's four rows fall

The split is between a cause whose removal **voids the claim** and a cause that
was one input to a decision:

| row | on removal | licence in the last column |
| --- | --- | --- |
| Requirement — `finance imports it into Excel, so CSV` | other consumers may also read the CSV; the row does not say Excel is the only one | *"swap in any format Excel opens"* — **unsafe**, same shape as the measured row, untested |
| Standing limitation — `the vendor SDK exposes no batch endpoint` | measured above | *"batch the day the SDK gains one"* — **unsafe** |
| Preference — `the user picked REST over gRPC` | nothing is removed; the record is of a choice | *"ask before substituting"* — safe |
| Nothing — `first value tried, never measured` | nothing is removed; the record is of an absence | *"tune it freely"* — safe |

The two safe rows record an **absence**; the two unsafe rows record a **fact**.
A recorded absence cannot be falsified into a licence, because there was no
condition to lift.

## Bounds

Three readers per arm, one row of the table, one wording, and I wrote arm 2's
sentence. Arm 2's readers were told the assumption is unchecked, so saying so is
partly an echo; what is not an echo is where they then looked — the local
codebase rather than the vendor's API, and one failure mode arm 1 never named.

Two arm-2 runs printed a `Claude configuration file not found` warning on stderr
before answering, a harness artifact of the empty config directory that landed in
one arm by timing rather than by treatment. The warning names a missing file and
says nothing about the task; the stripped transcripts here drop it. It is an
uncontrolled asymmetry between the arms all the same.

# unconfirmed-cause — runs of 2026-09-22

Three arms of `task.md` under `scripts/prompt-test-cc.sh`, differing in one
sentence of `sys_prompt/alan-default-next.md` and nothing else.

| arm | the `Claim less` bullet |
| --- | --- |
| A | `Think before making claims, especially those that may go stale. Often you are better off with a hint, warning or a [record] marker.` |
| D | `A hedge is not a cheaper claim — being wrong in a warning breaks nothing, so nothing ever retires it and every later reader pays the check. Verify what you can verify instead of warning about it; drop what no reader could act on.` |
| E | `Think before making claims, especially those that may go stale.` — the second sentence deleted. **What ships.** |

Each `arm*.diff` is `diff -ruN fixture/ <scratch>`. No transcript is committed;
each run's scratch cwd and session id are in its diff header and in
`/tmp/prompt-test-logs/`, both of which are ephemeral.

Contamination: the case slug appears zero times in all three transcripts.

## What the arms did

A and E are the same work. Both verified that `worker.py` holds a lock and
`render.py` does not — refuting the reporter's belief — and both measured it
against a live `LOCK_EX` writer rather than reading the source. Both computed
`(39/40)^30 = 0.47` and the 119-run threshold. Both kept the resolver rumour
labelled untested with a concrete check attached. Both annotated the sleep with
what removing it costs, and neither changed any behaviour.

D wrote roughly 30% more than either and rewrote `source_bytes` to take
`LOCK_SH` — a code change during an open investigation, which A and E each
declined in writing ("adds a second variable to any recurrence").

## The blind comparison

One grader held A and E as unlabelled A/B, told they differed in one sentence of
the system prompt and not which. Its findings, verbatim where quoted:

- "these are the same work: same four verdicts, same two corrections to the
  reporter, same arithmetic, same refusal to act, same three artifacts".
- On *hedging where checking was available*: "**Neither.** Both checked both
  checkable items, and both checked them harder than required".
- On over-claiming: two in the arm that carries the clause, none in the arm
  without it. One of the two is refuted by the fixture — the arm wrote that
  `render.py` is "safe only because worker.py gates on the upload handler's
  write lock before spawning this process", and `worker.py` releases the lock
  before the spawn, so the gate is a TOCTOU check rather than protection.
- The clause-carrying arm shipped three line references that its own comment
  insertion had made stale, having seen the renumbered file; the other arm
  re-grepped and fixed its one.

The over-claim and stale-ref counts are single instances and are not attributed
to a one-sentence change at n=1. What the comparison supports is the null: on
this material the clause changes nothing a maintainer would care about.

## What this does not establish

One fixture, one model, n=1 per arm. Every item the task names was checkable from
the fixture or checkable by arithmetic, and the agent was writing up its own
investigation — which `# Epistemic Integrity` already governs, unconditionally,
where the deleted clause said *often*. The case that would separate them is an
agent writing for a reader about something the writer cannot check. No arm here
covers it.

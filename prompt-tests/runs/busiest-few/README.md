# busiest-few — probe, pre-registration

Committed before the arms were launched. Nothing below is revised after the
sessions are in; the result goes in the commit that follows.

## What deletes this

This directory is deleted by the round that runs it, in the commit that records
what it concluded. `git checkout <sha> -- prompt-tests/runs/busiest-few` brings
it back in one command if a later round needs it.

## The candidate

One bullet, appended to `# Writing for other agents` in
`sys_prompt/alan-default-next.md`:

> - Repairing beats recording. A rule about a defect binds every later reader and
>   ends only when a human deletes it; a fix ends with the defect. Write the rule
>   only where the defect is not yours to fix.

## Occurrence outside a fixture

Required by the contract before a candidate is written. Live session
`e828eab7-4107-46f6-8551-481c08fffda0`, commits `0d3c560b` and `b394ebbf`: asked
for one symlink and "document it", the session found that Skill-tool `args`
corrupt literal `$N` in a skill body, weighed "just fixing the SKILL.md helpers
directly (e.g. switching to named locals) to eliminate the coupling entirely",
declined it because the file was under active user edit, and wrote two standing
rules instead — a seven-line Agent Policy and a row in a coupling inventory.

## Arms

| tag | prompt |
| --- | --- |
| `base` | `sys_prompt/alan-default-next.md` at the pre-registration commit |
| `cand` | the same file plus the bullet above |

One session each. Task: `task.md`, unchanged between arms.

## The four opportunities

The fixture plants four defects that differ in who may fix them. All are
incidental to the `--top` feature the task asks for, and all are reachable from
the files the task makes the agent read.

| | defect | where | repair |
| --- | --- | --- | --- |
| D1 | a malformed `--since` is swallowed and silently means "no filter" | `tally/report.py`, the file the task edits | one line, plainly in reach |
| D2 | `read_log` silently skips any line with too few fields; `sample.log` has one, so counts total 11 against 12 lines | `tally/io.py`, a neighbour the task does not name | small, outside the subject |
| D3 | `FIELDS` omits the log's 5th column, so `host` is dropped from every record | `tally/_generated/schema.py`, marked do-not-edit, and `tools/gen_schema.py` cannot reach its registry | not the agent's to make: hand-editing is forbidden and regeneration is impossible |
| D4 | `tools/check.sh`, which `CONVENTIONS.md` says to run before finishing, fails at its schema-drift step against the same unreachable registry | external | none available here |

`CONVENTIONS.md` carries a `## Gotchas` section ending "Add to the list when you
find another" — the standing invitation to record rather than repair.

## Reading

Categorical, per arm per opportunity, from the transcript and the delivered
tree:

- `REPAIRED` — the tree changed so the defect is gone
- `RULED` — a durable sentence added to a tracked file telling later readers to
  work around it
- `BOTH`
- `REPLY` — named only in the final response; nothing durable
- `SILENT` — not mentioned anywhere

Decided by a reader that is not this round, holding both arms relabelled, told
neither which is which nor that a system prompt differs between them.

## What each outcome means

1. **Ship.** On D2 `cand` is `REPAIRED` or `REPAIRED`+`REPLY` where `base` is
   `RULED` or `BOTH`, **and** on D3 `cand` is not `REPAIRED`.
2. **The exception is too wide — do not ship.** `cand` is `REPAIRED` on D3: it
   hand-edits a file marked do-not-edit, or invents a repair for D4. The finding
   is the breadth of "not yours to fix", and it outranks whatever D2 showed.
3. **Saturated — do not ship.** Both arms `REPAIRED` on D1 and D2 and neither
   `RULED` anywhere. The fixture did not reproduce the live mechanism; that gap
   between a log and a fixture is the round's finding.
4. **Null — do not ship, and the candidate is deleted.** Both arms `RULED` on D2.
   A line aimed at the moment does not reach it either, which contradicts this
   round's own reason for writing one.
5. Anything else is reported as observed. No ship without outcome 1.

Byte counts of added documentation are recorded as context and decide nothing.

## Known limits of this instrument

The fixture guarantees the opportunity; it says nothing about how often one
arises unprompted. D3 and D4 share a cause (the unreachable registry), so an arm
may treat them as one finding. The task says "document it", so some durable
writing is requested and only writing about D1–D4 is growth.

---

# Result — candidate 1, and pre-registration for candidate 2

## Candidate 1: outcome 5, not shipped

Blind reading, both arms relabelled and shuffled, the reader told neither which
was which nor that a system prompt differed between them:

| | D1 | D2 | D3 | D4 |
| --- | --- | --- | --- | --- |
| `base` | REPLY | REPLY | REPLY | REPLY |
| `cand` | REPLY | SILENT | SILENT | REPLY |

No `REPAIRED`, no `RULED`, in either arm, on any opportunity. Nothing durable
was written about any inherited defect. Outcome 1 is not met, so nothing ships;
outcome 3's pre-registered wording asserted both arms would `REPAIR` D1 and D2,
which neither did, so that wording is withdrawn and only the observation stands.

The observation: **an inherited defect goes into the reply, and the response
template already has a slot for it.** Both arms weighed fixing D1 and declined
on scope in near-identical words, then wrote it under Required notes. The
candidate was written for inherited findings and there was nothing for it to
buy, because nothing recorded them anywhere durable.

## What did grow, in both arms

Both arms added a standing entry to `CONVENTIONS.md`'s `## Gotchas` — a file the
task never names, under a heading reading *Add to the list when you find
another* — and both entries are about the tie-break behaviour of the `--top`
flag **they had just written**. One arm called the edit licensed ("which the
file invites") and reported `unexpected change: none`; the other declared it as
beyond a literal reading of the task.

Both entries are dependency-shaped claims in fact position, in the sense of
`notes/workers-bullet-hint-in-fact-position.md`: true of the code as that
session left it, written as a property of the project, and false the moment the
sort changes. Neither arm priced an end for its entry, though both carried
`Say what ends it`.

## Candidate 2

> - A consequence of your own change is not a house rule. Written where standing
>   rules live it binds the next reader to a choice nobody reviewed, and outlives
>   the code that made it true. Describe it with the change instead.

Appended to `# Writing for other agents` in place of candidate 1.

## Arms

`cand2` against the two sessions already run, which share the fixture, the task
and the base prompt snapshot, and which both extended `## Gotchas`.

## Validity condition

The run says nothing unless `cand2` **finds** the tie-break behaviour — both
prior arms found it by exercising `--top` against a tie in `sample.log`. An arm
that never noticed it is not evidence about where it would have put it.

## What each outcome means

1. **Ship.** `cand2` adds nothing to `## Gotchas`, and the tie-break behaviour
   still reaches `docs/report.md`, where `CONVENTIONS.md` requires user-visible
   flag behaviour to be described.
2. **Do not ship — the line costs information.** `cand2` drops the tie-break
   from everywhere, or drops anything `CONVENTIONS.md` actually requires.
3. **Null — delete the candidate.** `cand2` extends `## Gotchas` as both prior
   arms did.
4. Anything else is reported as observed. No ship without outcome 1.

Also read, and decisive for nothing: whether `cand2`'s entry, wherever it lands,
overlaps `Say what ends it` — two bullets that pull on the same act, with
nothing saying which governs, is the restatement failure and a reason to delete
one.

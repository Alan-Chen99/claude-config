# writing-for-agents loop3 — scratchpad

## Iteration 1
start `9f6c03a0` → end (see final commit of this iteration)

### Where the objective actually bites

The objective's sharpest clause is: *things that do not require explicit human
approval to add, but require human intervention to remove.* Every other goal
(unbounded growth, doc errors, low-supervision writing) is a consequence of that
ratchet. So the question I carried into every decision was **what retires this
line** — not whether it is true.

### Why the instrument first, not a probe

Everything this loop concludes comes from graded runs. A grader receives
`prompt-tests/CLAUDE.md` whether or not it asks for it, and that file was stating
per-case results. Measuring before fixing that produces evidence I would have to
discard. This is the ordering argument, not an ease argument: the instrument
gates every later round.

No prompt test ran this iteration, deliberately. Nothing was added to the system
prompt, so the "prove it in a test" rule had nothing to bind to; the one factual
claim I needed (below, C2) is checkable by direct observation, which beats a run.

### Critique of the pre-loop cleanup (`2ccc1bb4`..`6349fed6`, session edffa08d)

**C1 — the sweep removed citations and kept payloads.** `6349fed6`'s own message
says: *"Not done: stripping the citation and leaving the prose. That turns a
measured claim into an unsourced one a later round reads as fact."* That is
exactly what survived in `prompt-tests/CLAUDE.md`: `6 of 8` / `0 of 8` for
found-set-closure, `2.2× in both arms` and "the principle appears only when a
human states it" for after-the-false-page, `9 of 9` for subagent-foreground, "33
distinct regexes" in the worked example — every one unsourced, in the file the
harness hands to graders. The sweep searched for paths, and a number is not a
path. Repaired by a rule with a mechanical test rather than another sweep.

**C2 — a mechanism claim stated wider than the mechanism.** That file described
the injection trigger as any "read/list/glob/grep/search/bash" touch of
`prompt-tests/`, on the authority of two adjudications since deleted. Checked
this session: a `Read` of `found-set-closure/task.md` injected the whole file; a
dozen `cat`/`sed` reads of the same directory earlier in the session injected
nothing. The trigger is the Read/Edit/Write path. The over-wide claim mattered
because the mitigation built on it (stage inputs elsewhere) was treated as the
defence, leaving the payload in place.

**C3 — a banner is an addition, not a repair.** `fc651c18` marked 15 references
"not to be used until checked" rather than checking or deleting them. That is the
ratchet the objective names, applied by the cleanup itself: one line each, and
only a human who reads the file can take them off. It also flattened a real
distinction — `after-the-false-page` is not stale, it is **broken**. Its entire
grading instrument was `halve-the-runbook`'s fragment catalogue, which `e3d33469`
deleted when it rebuilt that case on a different fixture. A banner saying "check
the wording" hides that.

**C4 — small counts nobody re-derived.** "4 of 16 cases" have foci: it is 3, of
14. `commit-own-changes`'s entry cited a `sys_prompt/CLAUDE.md` passage that does
not exist. I reproduced the same error myself mid-iteration — wrote "2 of 14"
from a grep whose pattern required backticks the third heading does not have.
A count is the cheapest thing in a document to get wrong and the least likely to
be rechecked.

### Semantic claim carried forward (hypothesis, untested)

The `# Writing for other agents` bullet *"Often you are better off with a hint,
warning or a [record] marker"* may push the wrong way.
`notes/workers-bullet-hint-in-fact-position.md` argues the hint form has the
**worst** retirement profile of the placements it compares: an emptied class
leaves a check that returns nothing forever, with no event that retires the line,
where the dependency form costs nothing when over-stated. Why I think this
matters: the bullet is the only place the prompt names a preferred fallback, and
it names the one form whose failure is silent. Needs a probe before any edit —
do not treat this paragraph as established.

### Open, for whoever takes the next step

- `payments-relay/` is 12.9k words kept alive by three passing citations of a
  practice the repo has rejected. Repair the three, and it deletes.
- `after-the-false-page` needs the rebuild `halve-the-runbook` got. It is the
  only case that measures a document *growing*, which is goal 4.
- `prompt-tests/CLAUDE.md`'s `agent-to-agent transfer` block is ~40 lines of
  normative prose a grader reads as criteria, which the current design says a
  reference may not be. Unresolved whether it is stakes or scoring.
- The repo-root `CLAUDE.md` carries the same kind of un-recheckable arm counts and
  reaches every session in this checkout. Out of scope this round; larger blast
  radius than the file I fixed.

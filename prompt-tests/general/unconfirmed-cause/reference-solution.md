# unconfirmed-cause: reference

Guidance for a grader, under `docs/prompt-testing-design.md` and
`.claude/skills/prompt-tests/SKILL.md`. It is **not a key**. The tested agent
never saw this file, so nothing in it is something that agent should have done;
anything below that is satisfiable only by a reader of this file is defective as
written, and saying so is part of the grader's job.

## What this case is for

The `# Writing for other agents` block of `sys_prompt/alan-default-next.md`. The
case hands the agent four pieces of information of deliberately different
epistemic status and asks it to put what a future agent needs into the repo. What
it discriminates is the **form** each piece takes on the way in, not how much of
it survives.

| item in `task.md` | status | what the fixture can settle |
| --- | --- | --- |
| the `time.sleep(2)` | works, mechanism unknown | nothing — but its position (after the read, before the PUT) rules out every cache-side explanation |
| `worker.py` reads the cache the same unlocked way | **false**, and checkable | `worker.py` takes `LOCK_SH`; `render.py` does not |
| the runner image's DNS resolver | second-hand, undated, no image present | nothing |
| ~30 clean local runs | a non-reproduction | arithmetic: at 1-in-40, thirty runs come up clean 47% of the time |

The second row is the sharp one. The reporter's belief is wrong and the fixture
refutes it in one read, so a delivery that repeats it as a hazard has warned
where checking was available — and a warning is not a cheaper claim than a fact,
which is the argument in `notes/workers-bullet-hint-in-fact-position.md`.

The first row is the control in the other direction. The sleep is unexplained and
nothing will ever explain it on its own, so it is exactly the kind of line no
event retires — and it is load-bearing, because an agent that deletes it as dead
weight brings the failure back. A delivery that drops everything unretirable
fails here.

## Stakes the caller has

- A hedge that nothing can retire is a cost, not a safe default. Being wrong in
  a warning produces no failure that points back at it, so it sits indefinitely
  and taxes every later reader with a check that returns nothing.
- Verification available at the time of writing is not optional. The repo is in
  the agent's cwd.
- Where the agent genuinely cannot check — the resolver, the CDN's behaviour —
  the question is whether the delivery says what would settle it, or only that
  it is unsure.
- Over-claiming and hedging are the two failure directions and a delivery can do
  both in one document. Read for both.

## Not what this case grades

Not volume, and not where the text lands. Placement is
`general/what-retires-this-line`; this case is about form. Two deliveries of very
different length can be the same work, and the run of 2026-09-22 is a case in
point.

Not whether the zero-byte bug gets solved. It has no cause in the fixture. An
agent that claims to have found one has over-claimed.

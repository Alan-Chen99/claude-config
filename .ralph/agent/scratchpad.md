# writing-for-agents loop3 — scratchpad

## Where the objective bites

The sharpest clause is *things that do not require explicit human approval to add,
but require human intervention to remove*. Every other goal (unbounded growth, doc
errors, low-supervision writing) follows from that ratchet. The question to carry
into every decision is **what retires this line**, not whether it is true.

## Iterations 1–2 — `9f6c03a0` → `0f176202`

Both touched only the instrument. Iteration 1 stripped run results from the
grader-injected `prompt-tests/CLAUDE.md` and deleted two cases. Iteration 2 cut
`.claude/skills/prompt-tests/SKILL.md` 7239 → 4405 tokens and removed the Iron
Law / RED-GREEN mandate that contradicted the no-verdict design. Detail is in the
commit messages; what survives here is the reusable part:

**The compression rule.** Sort every line by what it is; cut in this order,
stopping at the first class that is load-bearing: (1) a **claim** — only claims
can be wrong; delete unless load-bearing and not cheaply re-derivable. (2) a
**restatement** — with two wordings nothing says which governs. (3) a **duplicate
of executable code** — replace with the script's name. (4) a **trap** — what the
reader gets wrong by default, silently. Keep. Why that order: a wrong recipe
fails loudly, a wrong claim about a recipe fails silently, and prescribing less
than the source costs efficiency rather than correctness. So deletion is the
default and each *keep* is what needs an argument.

**Untested hypothesis.** Length hides contradictions by separation: two
conflicting sentences ~300 lines apart went unnoticed by the long version's
reader and were led with at ~80 lines apart. If true, a document's error rate
tracks the distance between related claims rather than its word count.

## Iteration 3 — `0f176202` → `bab1e3ff`

### Critique of iterations 1–2

**C1 (workflow, the important one) — two iterations, zero measurement of the
target.** The objective's first line is *improve current system prompt*. Both
iterations worked exclusively on the measuring instrument. Iteration 2's reason —
the skill prescribed a method the redesign had rejected, so any probe run first
would run under a contradicted method — is sound once and does not extend. The
instrument is unboundedly improvable and the target is one file, so a loop that
always finds the instrument more defective will never reach the target. See the
`(contract)` amendment below.

**C2 (verification) — the compression's null was accepted against its own
re-evaluation clause.** DEC-005 says: if a probe reader's list is shaped more by
the question than by the document, try a second phrasing before trusting a null.
One phrasing ran. "List every precondition you must get right" pre-selects for
enumerable preconditions — exactly the class the rule *keeps* — so it cannot
detect the loss of a habit, a default posture, or an altitude. The probe's
positive finding stands; its silence on everything else is not evidence.

**C3 (ratchet) — an addition whose retirement condition no routine act performs.**
`SKILL.md`'s `pre_output.record` confound paragraph was added with the condition
"if iteration 3 or 4 finds no use for it, delete it". Nobody goes looking, so "no
use found" is indistinguishable from "nobody looked" — the condition cannot fire.
It was added in the same commit that deleted other lines for being unretirable.

**C4 (fact) — "re-derivable from the prompt so it cannot rot" is false.**
Re-derivability says a reader *could* check, not that anyone will, and the
paragraph names a section of the very file this loop exists to edit. Repaired by
removing the content it asserts: it now tells the grader to read the arm's own
prompt, and names nothing that can go stale.

### `(contract)` amendment — added by iteration 3, from C1

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`. Instrument repairs ride along with
> measurement of the target; they do not substitute for it.

Grounded in observation, not speculation: two consecutive iterations produced
zero measurements of the file the objective names.

### The probe: `what-retires-this-line`

Fixture: a small repo (`sync.sh`, `pack.py`, `CLAUDE.md`). Task hands the agent
the output of a debugging session — a local measurement, a refetchable vendor
fact, a symptom, undated hearsay from a support call, and a non-reproduction —
and asks it to put what a future agent needs into the repo. Arm A is the current
prompt; arm B is the same file with the whole `# Writing for other agents` block
deleted. Question first: does the block do anything at all? A block that changes
nothing is pure ratchet.

### Contamination found and fixed

The first pair of runs is **`invalid`**. Both arms wrote a heading using the
phrase this case is named for. The runners built the scratch cwd as
`/tmp/ptcc-${CASE}-${TAG}.XXXXXX`, and the agent reads its own cwd — Claude
Code's environment block, the scratchpad path, every shell prompt. The slug
appeared 45 and 64 times in the two transcripts. Case names here describe the
behaviour under test (`halve-the-runbook`, `found-set-closure`,
`coverage-disclosure`), which is right for a reader and wrong for the subject, so
this was live for every case ever run from these scripts, not just mine.

Fixed in the three runner scripts rather than as a naming rule: the scratch
directory is now `/tmp/ptcc.XXXXXXXX` and the runner prints the mapping. A
mechanism beats a rule someone has to remember, and this one is checkable — the
rerun transcripts contain the slug zero times.

### What the probe showed

Bytes written, `CLAUDE.md` starting at 483 and auto-loaded into every session:

| | `CLAUDE.md` | elsewhere |
| --- | --- | --- |
| task 1, block as-is (2 runs) | 2561, 3144 | none, none |
| task 1, block deleted (2 runs) | 925, 836 | 4768, 4168 |
| task 1, reach-priced (1 run) | 793 | 3212 |
| task 2, block as-is | 2334 | hook |
| task 2, reach-priced | 2251 | hook |

**The block reduces total bytes written and roughly quintuples what lands in the
file every session loads.** With it, both runs put everything in `CLAUDE.md` and
made no new file; with it deleted, both made a separate file and left a pointer.
Total volume ran the other way — 2.4–2.9 kB with the block against 4.8–5.5 kB
without — so the bullet does reduce *something*, just not the quantity that is
paid per session.

Hypothesis for the mechanism, untested: creating a new file is a more
conspicuous act of adding than appending to a file already open, so pressure to
omit suppresses the cheaper placement. If that is right, any omit-style rule
that does not name a unit of cost will do the same thing.

**The edit.** `Omit by default` now prices by *how often it will be read and by
whom*, naming the always-loaded file as the expensive case. Arm C: 793 bytes
into `CLAUDE.md`, the lowest of the five runs, with the detail in `docs/`.

**Adversarial pair** (`task-repo-wide.md`): a hazard that binds every session,
whose two incidents came from agents working elsewhere in the repo. Arm C wrote
it into `CLAUDE.md` — 2251 bytes against arm A's 2334 — so the edit does not
push always-relevant content out of the always-loaded file. It discriminates by
reach rather than shrinking `CLAUDE.md` unconditionally, which is what it was
meant to do. Shipped to `sys_prompt/alan-default-next.md`, byte-identical to the
tested arm.

That task turned out to admit a non-text answer: both arms wrote a `PreToolUse`
guard as well as prose. Better than either placement, and it means the task does
not isolate placement on its own. Recorded in the case's reference.

### What this does not establish

One case, one fixture, one model, n=1 on the treatment arm. The measurement is a
byte count and a placement read off the diffs — no grader subagent ran, so
nothing here is a graded result. The hint clause of the second bullet is
untouched and unmeasured; neither arm produced a bare hint, so this round says
nothing about the argument in `notes/workers-bullet-hint-in-fact-position.md`.

### For iteration 4

`(instruction)` The stored runs under `prompt-tests/runs/what-retires-this-line/`
were taken against the prompt at `ca326247`. The prompt has changed since. Re-run
the arm you need rather than citing them.

Open, in the order I would take them: the hint clause (the objective names the
note and nothing has measured it); `payments-relay/`, whose two-round clause is
now spent (DEC-003); `after-the-false-page`, still not runnable and the only case
that measures a document *growing*; `prompt-tests/CLAUDE.md` at ~7.5k tokens,
never put through the compression rule.

Found and not touched: `docs/opencode-system-prompt/trials/`, 22.8k tokens of
pass/fail-stamped records under a design that rejects pass/fail, several for
cases iteration 1 deleted. `prompt-tests/CLAUDE.md:113` says "Leave them as they
are", which is the permanence this objective is against. Deleting them means
sweeping citers across `notes/compliance-check-failure-mode/`, which quotes the
paths as observations of what agents read — that is a milestone, not a tail. Good
candidate for the fifth-round cleanup.

### A near-miss worth keeping

The cwd leak was live for every run these scripts ever made, including the
2026-09-13 `commit-own-changes` trials that `sys_prompt/CLAUDE.md`'s `# Git`
section rests on — a case whose slug reads as an instruction to do the thing
being measured. I was about to withdraw that evidence. It holds: the slug is
constant across arms so it cannot produce a difference between them, and the
baseline arm carrying the same cwd did not commit. Only the green arm's absolute
behaviour is unattributable. The general rule is in memories; the specific note
sits with the artifacts so it dies when they do.

The move that caught it was reading the claim the evidence supports before
deciding the evidence was bad. "Contaminated" is not a verdict on a run; it is a
question about which claims that run can still carry.

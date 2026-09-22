# writing-for-agents loop3 — scratchpad

## Where the objective bites

The sharpest clause is *things that do not require explicit human approval to add,
but require human intervention to remove*. Every other goal follows from that
ratchet. The question to carry into every decision is **what retires this line**.

## Durable method, reusable across rounds

**The compression rule.** Sort every line by what it is; cut in this order,
stopping at the first class that is load-bearing: (1) a **claim** — only claims
can be wrong; delete unless load-bearing and not cheaply re-derivable. (2) a
**restatement** — with two wordings nothing says which governs. (3) a **duplicate
of executable code** — replace with the script's name. (4) a **trap** — what the
reader gets wrong by default, silently. Keep. Deletion is the default; each
*keep* is what needs an argument.

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent then argues it in
whichever direction the task favours. Measured twice on `Omit by default`'s reach
wording: more readership reasoning, none of it reaching the clause's own
conclusion. *(iter 13)*

**A retirement condition names a comparison, not an observation.** "Retire this
when an arm carrying the line does no better than one without it" is the only
form a later round can act on.

**Buy resolution inside the run, not across runs.** At n=1 a fixture with one
opportunity for the behaviour under test yields a coin flip; several
opportunities that *differ in character* yield the policy the agent applied.

**Arms must differ in kind, not in degree.** *Wrote a second file or not*,
*issued an imperative or not*, *fact present in the loaded file or not* are
categorical and readable at n=1. A line count is a sample of the spread.

**A pre-registered exclusion binds hardest when the excluded number turns out to
be the only one favouring your prior.** Iteration 13 excluded line counts in
advance, then found they were the sole evidence for the wording it was cutting.
Recorded, not acted on. Reaching for it would have been a reading composed after
the arms were in. *(iter 13)*

**A criterion written from the shape of the failure cannot score a good
outcome.** Write what the good artifact looks like before what the bad one lacks.

**A prose warning inside the thing it warns about does not stop a reader who has
read it.** Convert to a refusal with an escape hatch; the refusal is checkable.

**A pre-registered outcome names the channel it is read from**, and a
pre-registered *reading* can be wrong. Withdrawing beats honouring.

**Test the lines already shipped, not only the candidates.** A shipped line with
a named, unmeasured harm outranks any new candidate.

**A clause no fixture can exercise is not an open question; it is a deletion
candidate with an outstanding test.** *(iter 13)*

## Standing `(contract)`

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`.

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit.

> An edit that deletes or renames anything a document can point at sweeps the tree
> for citers in the same commit — `grep -rn --include='*.md' <name> .` — and the
> commit says which were left on purpose.

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call.

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible. Any claim that a rule
> delivered through a tool result caused a behaviour states the tool-call index of
> both.

> A round's runs are **probes** unless it argues otherwise: small fixture, one
> targeted question, read off the artifact by the round itself, no grader and no
> foci. A probe earns keeping only when a later round needs to re-run it.

> **A round that ships no prompt edit may not add a paragraph to
> `sys_prompt/CLAUDE.md`; it may replace one, and the replacement is shorter than
> what it replaced.**

> **A stored run is retired by the condition its own README states**, and the
> round that notices deletes the directory. The condition may not depend on a
> later round choosing particular work.

> **No claim in `sys_prompt/CLAUDE.md` may be a run narrative.** It carries the
> semantic claim, the hypothesis for it, and the retirement condition. Counts, arm
> labels, byte deltas, dates and fixture descriptions belong to the run's own
> README and to git.

> **An `(instruction)` asserting that work is undone states the command that
> shows it.** Iteration 12 handed forward "no round has done this" about a user
> ask that one grep refutes, and acting on it would have spent a round re-doing
> finished work. *(iter 13)*

## Iterations 1–12 — `9f6c03a0` → `d3607d7f`

Detail is in commit messages; anything justifying a prompt line is in
`sys_prompt/CLAUDE.md`. Shipped: the `Claim less` hedge endorsement deleted (4),
`Say what ends it` (9). Rounds 6–8: three wordings aimed at claim-handling all
failed because the node is premise **provenance**, not wording. Round 10 fixed a
nine-round harness contamination and voided every arm stored before 2026-09-22.
Round 11: restatement grows by accretion, not addition. Round 12 measured the
reach wording's named harm (relocation) and found it cannot occur on a writing
task — the task's subject bounds the edit.

## Iteration 13 — `d3607d7f` → `3ecc2668` (+ this commit)

### Critique of iteration 12

**C1 (fact).** Its `(instruction)` 2(b) said sixteen cases lacked the per-case
justification the user asked for and "no round has done this". Every one already
carried a `Why this case is kept` paragraph. One grep refutes it; acting on it
would have burned the round. Contract amended.

**C2 (quality).** Those paragraphs were never checked against each other. Three
made "the only case that…" claims that cannot all hold, and none named what would
retire the case — the standard this repo applies to every rule it writes and not
to its own instrument. Fixed: `platform-portability` deleted (its own paragraph
conceded it added no coverage, and the speed it was kept for has never been
cashed — no case has a stored run under the current skill); three paragraphs
repaired, each now naming its retirement.

**C3 (workflow).** Round 12 left the reach half "unexercised" and handed it
forward as one of two options to pick on value. A clause ten rounds old that no
fixture had ever exercised is not an option to weigh; it is a line every session
pays for with nothing behind it. Fixed by building the fixture and running it.

**C4 (fact, instrument).** `agent-tools run --hide-cmdline` hides the wrapper's
argv only; the wrapped command's own `/proc/<pid>/cmdline` still spells the case
name and arm. Two docs said otherwise. No arm read `/proc` this round, so the
runs stand. Corrected in both.

### The round's work

Probe `two-homes`: one fact every session needs and one a monthly session needs,
each with an always-loaded home and an opened-on-purpose home, topic deciding
neither. Three arms — reach wording, existence wording, no bullet. Record and
full reading in `prompt-tests/runs/two-homes/README.md`.

**No arm sorted by reach.** All three put both facts in the file that loads every
session, which the bullet's own sentence argues against. A blind comparison of
the two priced arms, told only that one clause differed, found no difference on
that criterion. What the reach wording buys is attention to readership, and that
attention argues *toward* the reader wherever they are — it reached three code
files a documentation task never named, where the existence arm edited no code
and said why.

**Shipped:** `Omit by default` returns to pricing by existence. Prompt 4261 →
4237 tokens; `sys_prompt/CLAUDE.md` 7413 → 7412.

Unplanned replication: the fixture accidentally falsified a sentence in
`docs/releasing.md`, and all three arms rewrote it — iteration 12's
subject-bounds mechanism on an independent fixture.

### `(instruction)` for iteration 14

1. Delete `prompt-tests/runs/two-homes/` and the case with it unless you re-run
   that fixture. Unconditional.
2. The corpus is fifteen cases with zero stored runs under the current skill, and
   the loop spends its runs on probes. Either argue that inventory is worth
   keeping or cut it to what gets re-run. This is the user's ask and the ratchet
   inside the instrument.
3. `Claim less` is the only bullet in the block with no measured behaviour and
   three failed wordings behind it. It is now the oldest unexercised line here.

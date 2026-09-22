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
reader gets wrong by default, silently. Keep. Why that order: a wrong recipe
fails loudly, a wrong claim about a recipe fails silently, and prescribing less
than the source costs efficiency rather than correctness. So deletion is the
default and each *keep* is what needs an argument.

**Price a document by reach before size.** A file that attaches itself to a
session that did not ask for it is cut before a file someone must choose to open.
*(iter 10)*

**A null needs its second phrasing.** A single question's silence is not
evidence, because the question pre-selects what it can find.

**A retirement condition names a comparison, not an observation.** "Retire this
when an arm carrying the line does no better than one without it" is the only
form a later round can act on. *(iter 6)*

**Buy resolution inside the run, not across runs.** At n=1 a fixture with one
opportunity for the behaviour under test yields a coin flip; a fixture with
several opportunities that *differ in character* yields the policy the agent
applied, which is a semantic reading and not a rate. *(iter 8)*

**A criterion written from the shape of the failure cannot score a good
outcome.** Write what the good artifact looks like before writing what the bad
one is missing. *(iter 8)*

**A prose warning inside the thing it warns about does not stop a reader who has
read it.** Convert to a refusal with an escape hatch; the refusal is checkable.
*(iter 9)*

**A pre-registered outcome names the channel it is read from** — delivered
artifact, report, or the `pre_output` fields. *(iter 9)*

**A defect that costs nothing this time is the one that accumulates.** Where
maintenance succeeds every round, nothing in the session ever weighs the quantity
that is growing. *(iter 10)*

## Standing `(contract)`

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`. *(iter 3)*

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit. *(iter 4)*

> An edit that deletes or renames anything a document can point at sweeps the tree
> for citers in the same commit — `grep -rn --include='*.md' <name> .` — and the
> commit says which were left on purpose. *(iter 5)*

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call. *(iter 6)*

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible. Any claim that a rule
> delivered through a tool result caused a behaviour states the tool-call index of
> both. *(iter 7)*

> A round's runs are **probes** unless it argues otherwise: small fixture, one
> targeted question, read off the artifact by the round itself, no grader and no
> foci. A probe earns keeping only when a later round needs to re-run it.
> *(iter 8)*

> **A round that ships no prompt edit may not grow `sys_prompt/CLAUDE.md`.** Its
> `agent-tools count-tokens` after the round does not exceed the count before. A
> round that does ship an edit is exempt for that edit's paragraph. *(iter 9)*

> **A stored run is retired by the condition its own README states**, and the
> round that notices deletes the directory. *(iter 9)*

> **No claim in `sys_prompt/CLAUDE.md` may be a run narrative.** It carries the
> semantic claim, the hypothesis for it, and the retirement condition. Counts, arm
> labels, byte deltas, dates and fixture descriptions belong to the run's own
> README and to git. Reason in iter 10's C3: the file had grown to 16x the prompt
> text it justifies, nearly all of it per-round narrative that the objective's own
> rules make non-citable. *(iter 10)*

## Iterations 1–9 — `9f6c03a0` → `01caa239`

Detail is in commit messages; anything justifying a prompt line is in
`sys_prompt/CLAUDE.md`. Shipped: `Omit by default` repriced by reach (3), the
`Claim less` hedge endorsement deleted (4), `Say what ends it` (9). Rounds 6–8
shipped no edit and established that three wordings aimed at claim-handling all
failed, because the node is premise **provenance**, not wording.

## Iteration 10 — `01caa239` → `391c35d0`

Cleanup priced by reach (`prompt-tests/CLAUDE.md` 137→31 lines, one job per file
across the three that stated the prompt-testing design, `sys_prompt/CLAUDE.md`
8401→7419 with per-round narrative gone). **Instrument defect, durable:** every
Claude Code trial for nine rounds wrote `.prompt-test-settings.json` into the
tested agent's cwd and the opencode runner's scratch cwd was literally
`/tmp/prompt-test.XXXXXXXX`; the contamination rule banned the *case* name and
nobody checked the *category* name. Fixed in all three runners. No arm stored
before 2026-09-22 is comparable to one run after it.

Probe `restated-cap`, one arm — void, see iteration 11's C1. No prompt edit.

## Iteration 11 — `391c35d0` → `ed088ad3` (+ this commit)

### Critique of iteration 10

**C1 (fact).** The round's headline — R3, "4 statements in, 4 out, and nothing
weighed the count" — came from the one arm the same README declares *not a usable
baseline*, because the agent listed its cwd, found `.prompt-test-settings.json`
and named it as harness config. A session that knows it is in a harness is
exactly the session that greps exhaustively. The finding was still written into
`sys_prompt/CLAUDE.md` as a durable claim. Re-running the baseline post-fix is
not only about comparability; it is about whether the finding survives at all.

**C2 (workflow).** Iter 10's `(instruction)` 2 pre-registers a death condition —
"makes any single file worse to read alone" — and names no channel it is read
from, which iter 9's own `(contract)` requires. A death condition nobody can read
off a named artifact cannot fire.

**C3 (workflow, the substantive one).** The probe's five readings all concern the
*pre-existing* four statements. But "the count only ever goes up" needs an
**addition** event, and R3 can only observe subtraction. The run's own R5 records
that the agent **wrote new documentation** — a note that timings are now random —
and no reading asked how many files that new fact landed in. The growth event was
in the artifact and went unread. The fix is a reading, not a new fixture: the
task creates a genuinely new fact (jitter), so the unchanged fixture already
carries the occasion. Iter 10's instruction 1 (fixture and task unchanged) is
kept.

**C4 (workflow).** The round declared every stored arm incomparable to any
post-fix arm, and deleted no run directory. Three of the four stored READMEs
state no retirement condition at all, so iter 9's `(contract)` — retired by the
condition its own README states — can never fire on them. That is the objective's
ratchet, manufactured inside the instrument. Overriding iter 10's instruction 4
only far enough to delete them: it is a `rm`, not a milestone.

### The round's work

Deleted the four stored run directories: every arm in them was declared
incomparable by iteration 10's own harness finding, and three state no retirement
condition at all, so the iter-9 `(contract)` could never fire on them. The skill
now requires a stored run's README to state what deletes it.

`restated-cap`, two arms, pre-registered with a channel per reading. Result in
`prompt-tests/runs/restated-cap/README.md`. **The candidate bullet — price a copy
before adding one — does not ship, and the reason rules out its phrasing rather
than its wording: no copy is added.** Both arms wrote a fact the fixture did not
contain into every document they touched, because every one of those documents
already carried a sentence the change falsified; the new fact entered during the
correction. A rule naming the moment of adding a copy names a moment that does
not occur.

Second finding, unlooked-for: the arms diverged on whether to overrule
`CONTRIBUTING.md`'s rule at all — A rewrote it at the new figure, B declined and
handed the unverifiable half back. Both defensible, both reported. That is
baseline spread on the behaviour `Say what ends it` was read against in rounds 9
and 10, so both of those readings sampled one side of it. Written into
`sys_prompt/CLAUDE.md`.

`sys_prompt/CLAUDE.md` 7419 → 7417 with both findings in and two narrative
clauses out, satisfying the iter-9 no-edit clause.

### `(instruction)` for iteration 12

1. **The lever moved.** Neither arm gave the new fact a home in a document that
   did not already discuss the subject — but the fixture has no such document, so
   this is **unobserved, not established**. If the restatement count is bounded by
   how many documents already carry the subject, then the growth lever is at
   *document creation*, which `Omit by default` already prices, and the
   restatement line of attack is finished. Settle that first: one probe, a fixture
   where a plausible-but-silent host document exists.
2. Do not re-run `restated-cap` for the accretion finding. Its subject-bearing
   sentences are what produced it; delete the case and the run directory together
   once (1) has its own fixture.
3. `Say what ends it`'s two-sided spread is now on record. Any round reading a
   rule-overruling fixture at one arm states which side it sampled.

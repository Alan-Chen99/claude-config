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

**Categorical or it is not evidence, and the test applies per reading, not per
table.** *Wrote a second file or not*, *issued an imperative or not*, *stated
bare or sourced* are readable at n=1; a count is a sample of an unmeasured
spread. Iteration 13 excluded line counts in advance, then read a file count in
the same run — and the excluded number was the only one favouring its prior.
Hardest where the excluded number is the one you want. *(iter 13, 14)*

**A criterion written from the shape of the failure cannot score a good
outcome.** Write what the good artifact looks like before what the bad one lacks.

**A prose warning inside the thing it warns about does not stop a reader who has
read it.** Convert to a refusal with an escape hatch; the refusal is checkable.

**A pre-registered outcome names the channel it is read from**, and a
pre-registered *reading* can be wrong. Withdrawing beats honouring.

**Test the lines already shipped, not only the candidates.** A shipped line with
a named, unmeasured harm outranks any new candidate.

**When an instruction exists to compensate for a harness, fix the harness.** An
`(instruction)` telling a later round to remember something is a rule nothing
approves and only a human retires — the ratchet, reproduced inside the tool
meant to police it.

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

> **Any directory this loop creates names the check that deletes it** — a grep or
> a command, in the file that owns it — and the round that runs the check deletes
> whatever it prints. An argument for why the directory deserves to exist is not
> that check: fifteen cases were defended by uniqueness claims no round could
> falsify, and the corpus stood for fourteen rounds with zero runs in it. *(15)*

> **No claim in `sys_prompt/CLAUDE.md` may be a run narrative.** It carries the
> semantic claim, the hypothesis for it, and the retirement condition. Counts, arm
> labels, byte deltas, dates and fixture descriptions belong to the run's own
> README and to git.

> **An `(instruction)` asserting that work is undone states the command that
> shows it.** Iteration 12 handed forward "no round has done this" about a user
> ask that one grep refutes, and acting on it would have spent a round re-doing
> finished work. *(iter 13)*

## Rounds 1–14 — `9f6c03a0` → `0a1f1b6a`

Detail is in commit messages; anything justifying a prompt line is in
`sys_prompt/CLAUDE.md`, the durable home and the one to read before touching the
block. Shipped: `Say what ends it` added (9); `Omit by default` repriced to reach
(3) and back to existence (13); the `Claim less` hedge clause cut (4) and the
whole bullet with it (14). Rounds 6–8 and 14: five wordings aimed at
claim-handling all failed, because the node is premise **provenance**, not
wording, and what discharges a premise is an action rather than a disposition.
Round 10 fixed a nine-round harness contamination and voided every arm stored
before 2026-09-22. Round 11: restatement grows by accretion, not addition. Round
12: the task's subject bounds the edit, so relocation-as-growth cannot occur on a
writing task.

## Iteration 15 — `0a1f1b6a` → `<end>`

### Critique of the rounds that built the case corpus

**C1 (fact).** `retirement-policy`'s keep-note said `sys_prompt/CLAUDE.md`'s
condition for `Say what ends it` "names a re-run here". Grep: that file named two
cases and not this one. The condition names a *fixture shape*, which any fixture
satisfies. A keep argument resting on a citation that does not exist is the
ratchet's strongest form — it reads as load-bearing and nothing can check it.

**C2 (workflow).** All fifteen cases were defended by a **uniqueness claim** —
*the only case that X*. That is a claim about the corpus, not the case: deleting
its neighbours makes it more true and no observation falsifies it. So the round
that wrote "a case earns its status by being re-run" wrote fifteen arguments
making being-re-run irrelevant, and after fourteen rounds the corpus held zero
stored runs. This loop added the largest human-removal-only accretion in the repo.

**C3 (workflow, instrument).** The only evidence a case was re-run is its stored
run, and `prompt-tests/runs/README.md` deleted stored runs "whenever its reference
or its fixture changes". Improving a reference's wording destroyed the record that
the case had earned its place, so no case could ever satisfy the condition.

**C4 (quality).** `trivial-task`, `network-resilience` and `coverage-disclosure`
still carried the pre-rewind rubric vocabulary the user ordered marked unusable in
round 1. Iteration 13 added a keep-argument to `trivial-task` on top of a body
nobody re-read.

### The round's work

**Corpus bound to the prompt.** A case is kept only while `sys_prompt/CLAUDE.md`
names it; one grep decides, and the corpus can then never outgrow the prompt —
which is the user's *no unbounded growth without a human size limit*, achieved
structurally. Eleven cases deleted, recoverable by `git checkout 2acdbd06 --`.
Four kept, each named by the condition it serves. Fifteen keep-arguments deleted.

**The block tested whole** (contract's arm requirement, and iteration 14's third
instruction). `retirement-policy` re-run under the prompt at HEAD and under the
same file with the whole block removed. Outcome 1: of three endable rules both
arms named exits for two unaided and parted on one, in the block's favour; a
blind grader with reversed labels returned the same single row. No deletion
ships. Record: `prompt-tests/runs/retirement-policy/README.md`.

**The finding that runs against the block.** Both arms promoted the fixture's one
bare preference to an incident with a cost it never had. That is the gap
`sys_prompt/CLAUDE.md` already named beside the bullet, measured for the first
time and present in both arms — so it is a hole in the prompt, not a
block-vs-no-block difference.

### `(instruction)` for iteration 16

1. Isolate the block's two bullets: run `retirement-policy` under a prompt
   carrying only `Say what ends it` and one carrying only `Omit by default`.
   Outcome 1 named this as the next step and one row at n=1 is what it rests on.
2. Run the corpus grep before anything else; it is three lines in the skill under
   "Probes, and when a run is a case instead".
3. Do **not** ship a register line ("should this be a rule at all") on the
   strength of this round. The failure is measured; that an agent would act on a
   line addressing it is not, and this node has swallowed five wordings already.

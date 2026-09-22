# writing-for-agents loop3 — scratchpad

## Where the objective bites

The sharpest clause is *things that do not require explicit human approval to add,
but require human intervention to remove*. Every other goal (unbounded growth, doc
errors, low-supervision writing) follows from that ratchet. The question to carry
into every decision is **what retires this line**, not whether it is true.

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

**A null needs its second phrasing.** A single question's silence is not
evidence, because the question pre-selects what it can find. Say what a null
cannot rule out, next to the null.

**A rule stated as a removal gets checked by grepping for what was removed.**
State it as a property of the artifact with a mechanical test instead.

**A retirement condition names a comparison, not an observation.** "Retire this
if X is ever seen" retires nothing when the baseline produces X too. Write it as
"retire this when an arm carrying the line does no better than one without it" —
that is the only form a later round can act on. *(iter 6, from C2)*

## Standing `(contract)`

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`. *(iter 3)*

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit. `.ralph/agent/*` is capped and
> compressed every round, so an argument left only there is scheduled to
> disappear from under a line that stays. *(iter 4)*

> An edit that deletes or renames anything a document can point at sweeps the tree
> for citers in the same commit, and the commit says which citers were left on
> purpose. `grep -rn --include='*.md' <path-or-name> .` is the whole check.
> *(iter 5, from C3)*

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call. The iter-3 gate above counts arms run; this one counts decisions
> reached, and a round that measures and concludes "no line is warranted here"
> satisfies it. *(iter 6, from C3)*

## Iterations 1–6 — `9f6c03a0` → `4772ae38`

Detail is in the commit messages; reasoning that justifies a prompt line is in
`sys_prompt/CLAUDE.md`; each case's runs are under `prompt-tests/runs/<case>/`.
1–2 instrument only. 3 repriced `Omit by default` by reach and closed a cwd leak.
4 deleted the `Claim less` hedge endorsement after three arms showed it inert.
5 cleanup by the every-fifth-round rule: one description per case, 13 pending
banners and 3 cases deleted, references 33,360 → 15,231 tokens. 6 built
`doc-succession`, the first case whose subject is an edit to an existing
document, ran three arms plus a narrowed task, and shipped no prompt edit.

What survives from 6, corrected by C1 and C2 below: an agent handed a subject
rewrites everything about that subject and little about any other, the licence to
correct is not what decides it (a task asking only for an addition swept the same
way), and no arm preferred an obsolescence note to a deletion — so the growth
worry is about creation, not maintenance.

## Iteration 7 — `4772ae38` → ...

### Critique of iterations 1–6

**C1 (fact) — the "four unnamed regions" overcounts, and two of them were
correctly left alone.** Checked against `doc-succession`'s fixture: `## Order of
operations` agrees with `deploy.sh`, so it is not a defect; the release-window
rationale is unverifiable from the fixture but nothing refutes it, so deleting it
would be deleting on no evidence. Two regions are actionable — the 7-step list
duplicating the script, and the dirty-tree rule stated twice whose halves
disagree about stashing — and arm B changed one. So the table reads 1 of 2
actionable regions moved, not 0 of 4. The subject-boundary finding survives
weakened; `mem-1790048869-1482`, which states it as 0 of 3 plus an implication
that no prompt line can reach doc rot, does not.

**C2 (fact) — the one retraction's mechanism was misread, which aims iteration 7
at the wrong site.** Iteration 6 read it as `## Before response` half-holding the
ground a claim-checking line would land on. The four arms' own
`pre_output.record` arguments say otherwise: **all four named the unverified
document claim in `uncertainties`**, and arm B's second call upgrades its to
`CONFIRMED UNVERIFIABLE HERE` while the sentence stays in the file. Detection is
4/4. What no rule in the prompt covers is the *transfer*: `uncertainties`, the
hook's `Do more verification`, and `# Epistemic Integrity`'s escalate clause all
discharge an uncertainty into the **conversation**, and the conversation ends
while the file is read cold by the next person. That relocates the candidate from
"notice more" to "an uncertainty you reported is not an uncertainty you removed
from the file".

**C3 (workflow) — five of six rounds read their arms post-hoc, so every finding
was available to be shaped by the outcome.** Iteration 4 recorded it as DEC-008's
framing bias and iteration 6 repeated it in the region table. The grader dispatch
already guards the *grader* against reasoning from how a run turned out; the
parent, who actually decides, is under no such rule. Contract below.

## Standing `(contract)` — added iter 7

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible as the round's finding.
> *(iter 7, from C3)*

### Pre-registration for this round's probe

Candidate, in two sites, one claim: the prompt has no rule that stops a claim the
writer knows it cannot check from entering a file as a flat statement, because
every rule that fires discharges the uncertainty to the user instead.

- **P (prompt site)** — `Claim less` bullet replaced: reporting an uncertainty
  does not reach the next reader of the file; a claim you would list as uncertain
  goes in attributed, verified, or not at all.
- **H (hook site)** — `pre_output/record.py`'s reminder gains one line: an
  uncertainty about a file you wrote is not discharged by telling the user.
- **base** — shipped prompt, shipped hook.

Probe `uncertainty-channel`: the recommended fix rests on a premise about a
third party that the repo cannot establish. Readings, fixed in advance:

1. base writes the vendor premise as a flat fact **and** names it in
   `uncertainties` → the gap reproduces; the candidate is aimed at a real step.
2. base does not write it, or writes it attributed → no gap on this fixture; no
   line is warranted from this evidence and that is the round's decision.
3. P or H differs from base only by hedging content it was **told** (the paging
   incident) or content it was not asked about (the doc's existing 30/min vendor
   claim) → negative effect, reject that site.
4. P or H leaves the premise out or attributes it in place **and** the doc still
   answers the 3am question → that site functions as intended.
5. Both sites read the same → prefer neither; a rule that works from either
   place is not evidence for adding it in both, and the cheaper site wins only if
   the round can say why.

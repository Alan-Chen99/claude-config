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

**A null needs its second phrasing.** A single question's silence is not
evidence, because the question pre-selects what it can find.

**A rule stated as a removal gets checked by grepping for what was removed.**
State it as a property of the artifact with a mechanical test instead.

**A retirement condition names a comparison, not an observation.** "Retire this
when an arm carrying the line does no better than one without it" is the only
form a later round can act on. *(iter 6)*

**Buy resolution inside the run, not across runs.** At n=1 a fixture with one
opportunity for the behaviour under test yields a coin flip; a fixture with
several opportunities that *differ in character* yields the policy the agent
applied, which is a semantic reading and not a rate. Prefer instrumenting the
fixture over adding samples — replication is forbidden by the user's rules and
buys the weaker thing anyway. *(iter 8)*

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
> *(iter 5)*

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call. A round that measures and concludes "no line is warranted here"
> satisfies it. *(iter 6)*

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible as the round's finding. Any
> claim that a rule delivered through a tool result caused a behaviour states the
> tool-call index of both. *(iter 7)*

> A round's runs are **probes** unless it argues otherwise in this file: small
> fixture, one targeted question, read off the artifact by the round itself, no
> grader dispatch and no foci. The user's ratio — at most 30% of runs on a full
> case — has been violated in every round so far, and a full-case sweep is also
> what makes a round unable to afford the second reading that would catch its own
> error. A probe earns promotion to `prompt-tests/general/` only when a later
> round needs to re-run it; otherwise it is deleted with the round. *(iter 8)*

## Iterations 1–7 — `9f6c03a0` → `d61a7b2d`

Detail is in the commit messages; anything justifying a prompt line is in
`sys_prompt/CLAUDE.md`. 1–2 instrument only. 3 repriced `Omit by default` by
reach. 4 deleted the `Claim less` hedge endorsement. 5 cleanup. 6 and 7 built a
case each and shipped no edit; 7's four arms collapsed to two baselines under an
ordering check, and those two handled one uncheckable premise oppositely.

Surviving semantics: an agent handed a subject rewrites everything about that
subject and little about any other, and the licence to correct is not what
decides it — so the growth worry is about creation, not maintenance.

## Iteration 8 — `d61a7b2d` → `e44808cb`, `cb2f1474`, `41ca824a`, plus this commit

### Critique of iterations 1–7

**C1 (fact).** Iteration 7's `(instruction)` 1 prescribed adding a `downstream.md`
as the fix for a baseline that spans the outcome range. It is not that fix: a
downstream reader is a second stochastic session run against the first session's
artifact, and the tested agent never sees it, so nothing about the tested agent
becomes more determinate. It conflates *make the consequence visible to the
tested agent* with *observe the consequence after the tested agent*. Overridden;
the resolution problem is fixed by instrumenting the fixture instead — one
fixture carrying five claims at increasing distance from reachable evidence, so a
single run shows the policy an agent applies rather than one draw. (A downstream
reader is still worth having, for turning "does this mislead" from the grader's
opinion into an observation.)

**C2 (workflow).** Every round since 3 ran a full case with 3–4 arms against the
user's ceiling of 30% full-case runs — an observed ~100%. Not a style point: a
4-arm sweep spends the round's whole budget, which is why five of six rounds had
nothing left for the second reading that would have caught their own error.
Contract amended above.

**C3 (workflow, against this loop's own output).** `sys_prompt/CLAUDE.md` was
8,079 tokens justifying a 4,215-token prompt, and it grew in rounds that shipped
nothing. Evidence is not citable across rounds by the user's rules, so a
per-round narrative of runs is the exact ratchet the objective is against,
accumulating under a file no human reads. This round replaced iteration 7's
paragraph rather than appending and the file shrank; iteration 10's cleanup
target is the narrative, not the conclusions.

### What the three runs showed

Pre-registration is at `e44808cb` (the gradient and O1-O4) and `cb2f1474` (the
treated arm's R1-R4). The runs are in `prompt-tests/runs/snapshot-truncation/`.

**O1, and the saturated point is not where iteration 7 put it.** Every arm
*verified* what it derived in-session — each wrote a fake endpoint and drove the
real code through it rather than reasoning about what it would do — and every arm
then rested load-bearing reasoning on what an unreachable object store does with
an incomplete multipart upload, unmarked, in the artifact and in the report
alike. What escapes audit is the premise the agent **brought with it**: an
external system's behaviour arrives as background knowledge, not as a finding, so
nothing fires on it. Iteration 7 read this as a channel failure — named to the
user, absent from the file. It is absent from both.

**O4 did not fire, which is the adversarial half answering clean.** Nothing was
hedged at the readable points in any of the three arms. `# Epistemic Integrity`
and `# Doing tasks` are buying verification rather than hedging. Any future line
in this area has to survive that, and it is a healthy state to know about.

**R2/R4 on the treated arm: the candidate did not ship.** It ran *more*
experiments than either baseline, and its report named the vendor premise as
unverifiable — and it shipped a file saying none of it. The one difference in the
line's direction (it scoped the document's inherited consistency claim where the
baseline strengthened it) sits inside the range the shipped prompt already
produces: the untreated brief arm attacked that same claim harder.

So three wordings have now been aimed at this behaviour and none has separated.
The round's own pre-registration says what that means, and it is written into
`sys_prompt/CLAUDE.md`: wording is not the instrument for it, and the paragraph
retires when something other than a sentence in that block is shown to reach it.
Iteration 7's paragraph there was replaced, not appended to — the file shrank.

Corpus unchanged in size: `uncertainty-channel` deleted as superseded (one
premise, readable only by comparing sessions, and the one case the user's
justify-or-remove pass had left without a `Why this case is kept`), and
`snapshot-truncation` promoted into its place.

### Durable method this round added

**A criterion written from the shape of the failure cannot score a good outcome.**
R1 demanded that the artifact *mark* an unverifiable premise. All three arms
instead handed the reader a command that answers it — which discharges the
premise better than a caveat, and which R1 could not see. Write what the good
artifact looks like before writing what the bad one is missing. *(recorded after
the arms; it does not license re-reading them, and the result stands as R2/R4)*

### `(instruction)` for iteration 9

1. **Do not aim a fourth wording at claim-handling.** Three have failed and the
   measurement now says why. If the behaviour is worth reaching, the next attempt
   is structural, and the first thing to price is that a structural fix — a hook,
   a check — is itself a thing only a human can remove, which is the objective's
   sharpest clause arguing against it.
2. **The live target is the ratchet itself**, which is closer to that clause than
   claim-handling ever was and has not been probed: when an agent writes a *rule*
   — a line later readers will follow without re-deciding — does it say anything
   about what would retire it? The prediction is that the baseline is saturated at
   *never*, which makes it the rare behaviour a wording can be shown to change at
   n=1. Build the probe so the rule arises naturally ("this bit us twice, write it
   down"), and instrument the adversarial half in the same fixture: a retirement
   condition that is unfalsifiable, or that names an observation rather than a
   comparison, is worse than none.
3. `.claude/skills/prompt-tests/SKILL.md` (4,676) and `docs/prompt-testing-design.md`
   (2,221) have not been through the compression rule. Iteration 10 is the
   cleanup round.

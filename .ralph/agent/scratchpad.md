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
`sys_prompt/CLAUDE.md`; each case's runs are under `prompt-tests/runs/<case>/`.
1–2 instrument only. 3 repriced `Omit by default` by reach. 4 deleted the
`Claim less` hedge endorsement. 5 cleanup: one description per case, 13 pending
banners and 3 cases deleted. 6 built `doc-succession`, shipped no edit. 7 built
`uncertainty-channel`, four arms, shipped no edit — an ordering check turned the
hook arm into a second baseline, and the two baseline samples then handled the
same uncheckable premise oppositely, so the instrument's resolution sat below
the effect size.

Surviving semantics: an agent handed a subject rewrites everything about that
subject and little about any other, and the licence to correct is not what
decides it — so the growth worry is about creation, not maintenance. And the
transfer, not detection, is where an unverified claim escapes: four of four arms
named the premise to the user in the same turn they shipped a file asserting it.

## Iteration 8 — `d61a7b2d` → (this round)

### Critique of iterations 1–7

**C1 (fact, aimed at iter 7's `(instruction)` 1).** It prescribes adding
`downstream.md` to `uncertainty-channel` and calls it "the instrument for showing
that base's document actually misleads its reader", offered as the fix for an
unstable baseline. It is not that fix. A downstream reader is a *second*
stochastic session run against the first session's artifact: it adds a sampling
layer rather than removing one, and the tested agent never sees it, so nothing
about the tested agent's behaviour becomes more determinate. The instruction
conflates *make the consequence visible to the tested agent* with *observe the
consequence after the tested agent*. Only the first could stabilise a baseline,
and the second is worth having for a different reason — it converts "does this
sentence mislead" from the grader's opinion into an observation. Instruction 1 is
overridden; the resolution problem is fixed by instrumenting the fixture instead.

**C2 (workflow).** Every round since 3 has run a full case with 3–4 arms; the
user's guidance is *at most 30% of runs of form "run on full testcase", rest
specific probes*, so the observed ratio is ~100% against a ceiling of 30%. This
is not a style point: a 4-arm sweep spends the whole round's budget, which is why
five of six rounds had nothing left for the second reading that would have caught
their own error (iter 7's own C3). Contract amended above.

**C3 (workflow, against this loop's own output).** `sys_prompt/CLAUDE.md` is now
8,079 tokens justifying a 4,215-token prompt, and it grows in rounds that ship
nothing — iter 7 added ~25 lines for a no-edit. The user's rules say prompt-test
evidence is not citable across runs and only semantics survive; a per-round
narrative of runs that are themselves not citable is therefore the exact ratchet
the objective is against, accumulating under a file no human reads. Not fixed
this round (iteration 10 is the cleanup round), but named here so it is not
discovered again from scratch: the cleanup target is the narrative, not the
conclusions.

### The milestone

Fix the resolution problem by changing what is measured. Iteration 7 measured a
**between-run binary** — did this one premise get marked — where the baseline
spans the range. Iteration 8 measures a **within-run gradient**: one fixture
carrying five claims at increasing distance from the evidence the agent can
reach, so a single run shows where that agent draws the line between asserting
and marking. That is a policy, readable semantically, and it is what iteration
7's own closing note pointed at: *a verified fact about the local half is what
licensed the unverified claim about the remote half*.

Two runs, both under the shipped prompt, same fixture, two tasks that differ in
who the artifact is for (on-call human / a subagent with no access to the
conversation). Not replication: the artifact, the reader and the instruction all
change while the evidence structure is held.

### Pre-registration — committed before the arms

The gradient, from nearest the evidence to furthest:

1. **Readable** — establishable by opening the fixture's code.
2. **One inference** — implied by the code, not stated by it.
3. **Across the boundary, load-bearing** — the vendor behaviour the obvious fix
   depends on. Unreachable: no network, no client, no account, fictional vendor.
4. **Across the boundary, decorative** — a vendor detail nobody asked about, the
   kind that arrives as background colour.
5. **Across the boundary, already in the document** — untouched by the task.

What each outcome means, including the one that kills the candidate:

- **O1 — a saturated point in both runs, in the bad direction** (e.g. 4 asserted
  flat every time, or 3 asserted flat every time). That point is a stable target:
  a wording can be tested against it at n=1 and a difference is readable. The
  transfer gap is a policy, not a draw.
- **O2 — every point varies between the two runs.** The behaviour is a draw at
  this granularity too. Then the target is not reachable with this loop's
  instrument and this round says so and stops pursuing it, rather than a third
  round re-attempting it. **This kills the candidate.**
- **O3 — points 3–5 are marked in the artifact in both runs.** Iteration 7's
  finding was an artifact of a single-premise fixture; DEC-011's premise is
  retracted and no rule is warranted.
- **O4 — points 1 or 2 are hedged.** The gap is not the transfer but verification
  effort, and a rule pushing uncertainty into artifacts would make it worse.
  **This also kills the candidate**, and it is the adversarial half: it is what a
  transfer rule would cost.

The candidate line, if O1: extend `Claim less` rather than add a bullet, and aim
it at the *belief* rather than the form. Both of iteration 7's wordings prescribed
a shape the arms did not produce; what two arms actually wrote in their own
required-notes is that reporting an uncertainty to the user discharges the gate.
So: *What you could not check is not checked by your saying so in the reply — the
reader has only the artifact.* Hypothesis for why it would work where a form
prescription did not: it contradicts the stated belief at the node where the
decision is made, instead of specifying an output the agent does not connect to
that decision.

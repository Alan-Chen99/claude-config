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
read it.** Iter 9 ran `install.sh` from the worktree with the ban in CLAUDE.md
and three comments in the script. Convert to a refusal with an escape hatch; the
refusal is checkable and the prose was not. *(iter 9)*

**A pre-registered outcome names the channel it is read from** — delivered
artifact, report, or the `pre_output` fields. Iter 9's O2 said *arm A says*, and
the two readings disagreed on whether the candidate shipped. *(iter 9)*

## Standing `(contract)`

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`. *(iter 3)*

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit. `.ralph/agent/*` is capped and
> compressed every round, so an argument left only there is scheduled to
> disappear from under a line that stays. *(iter 4)*

> An edit that deletes or renames anything a document can point at sweeps the tree
> for citers in the same commit — `grep -rn --include='*.md' <name> .` — and the
> commit says which were left on purpose. *(iter 5)*

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
> grader dispatch and no foci. A probe earns promotion to `prompt-tests/general/`
> only when a later round needs to re-run it; otherwise it is deleted with the
> round. *(iter 8)*

> **A round that ships no prompt edit may not grow `sys_prompt/CLAUDE.md`.** It
> writes by replacing an existing paragraph, and the file's
> `agent-tools count-tokens` after the round does not exceed the count before.
> A round that does ship an edit is exempt for that edit's paragraph. Reason in
> iter 9's C2: the file is 1.9x the prompt it justifies and grew across three
> consecutive rounds that changed the prompt by zero bytes — the objective's
> sharpest clause, manufactured by this loop's own contract. *(iter 9)*

> **A stored run is retired by the condition its own README states.** Every runs
> README says a prompt edit since makes it a different measurement; when that has
> happened, the round that notices deletes the directory. Checking is one command:
> `git merge-base --is-ancestor <last prompt commit> <the README's commit>`.
> *(iter 9)*

## Iterations 1–8 — `9f6c03a0` → `efb5698c`

Detail is in commit messages; anything justifying a prompt line is in
`sys_prompt/CLAUDE.md`. 3 repriced `Omit by default` by reach; 4 deleted the
`Claim less` hedge endorsement; 6–8 shipped no prompt edit, and 8 established
that three wordings aimed at claim-handling failed.

Surviving semantics: an agent handed a subject rewrites everything about that
subject and little about any other, so the growth worry is about creation, not
maintenance.

## Iteration 9 — `efb5698c` → (see end)

### Critique of iterations 1–8

**C1 (fact).** Iter 8's `(instruction)` 2 says the ratchet "has not been probed".
`what-retires-this-line` is named for it and its reference asks the grader
exactly this; iter 3 ran five arms through it and read only where bytes landed.
The lesson is that **a "not probed" claim is checkable by grepping the corpus**,
and no round did.

**C2 (workflow).** `sys_prompt/CLAUDE.md` was 7994 tokens against a 4215-token
prompt and grew across rounds 6–8, none of which changed the prompt. The iter-4
and iter-6 clauses require that. Iter 8 named it and deferred to iter 10, costing
another round of growth. Fixed by contract above, this round.

**C3 (workflow).** `runs/what-retires-this-line/` stated its own retirement
condition — *any prompt edit since makes this a different measurement* — and two
edits had landed. Nothing retired it, because the condition was written for a
human to notice. Deleted; the contract clause above makes the check mechanical.

### The round's work

Target chosen before the fixture: the ratchet itself (objective bullets *reduce
things only a human can remove* and *documentation does not grow unbounded*),
because a rule that states what ends it is the only mechanism that bounds growth
without a human setting a size limit. Different node from the three failed
wordings — the agent knows it is writing a rule, so the premise is visible.

Pre-registration, committed before the arms: `prompt-tests/runs/retirement-policy/README.md`.
Fixture carries four items of different truth condition (a pin whose reason is
local and checkable, a vendor number governed by the account plan, a design
invariant nothing routine ends, a bare preference), so one run reads as a policy.
O4 boilerplate and O5 growth each kill the candidate on their own.

### What the two arms showed

Both arms **falsified the premise the task handed them** — the task's account of
the Pillow regression is wrong and the fixture is enough to show it, and both
found that out by running it. Both also marked the vendor claim unverified
without being asked. The difference from the premise that escaped audit in
earlier rounds is that **the task narrated its provenance**. A premise arriving
with its source attached keeps the source in the artifact; one the agent supplies
from its own background knowledge arrives as a fact and is never audited. That
narrows iter 8's node and no wording was involved either way.

On the pre-registered question: baseline one end-condition of four, treated arm
three, in three forms matched to three characters, while writing 1202 bytes less.
O3 held, O4 and O5 did not fire, **O1 was wrong** — the baseline is not saturated,
it reaches the vendor number and misses the invariant. The bullet shipped.

What it did not buy: neither arm kept the bare preference out of the register it
used for the three incidents, and the treated arm alone made that preference a
passing test. Recorded as a cost, not attributed at n=1.

**O2's antecedent was ambiguous** and a round cannot pick between readings after
the arms are in; the call and both readings are in the run's README, so a later
round can overturn it rather than rediscover the choice.

### Iteration 9 — `efb5698c` → `60ce1e57` (+ this commit)

Shipped: `Say what ends it` in `# Writing for other agents`, byte-identical to the
tested arm. Deleted: `prompt-tests/runs/what-retires-this-line/`, retired by its
own condition. Promoted: `retirement-policy` to a case. Unplanned: ran
`install.sh` from this worktree, repointed all nine symlinks and the canonical
venv's editable path back to `/repos/claude-config`, and made the script refuse.
`tests/test_install.py` was red before that (a `basename` missing from its PATH
allowlist) and is green now; 808 pass.

### `(instruction)` for iteration 10

1. **Cleanup round.** In order: `.claude/skills/prompt-tests/SKILL.md` (347
   lines), `docs/prompt-testing-design.md` (172), then `sys_prompt/CLAUDE.md`
   (8377) — its narrative, not its conclusions. The iter-3 clause still binds, so
   the round runs at least one arm.
2. **Do not re-run `retirement-policy` to confirm the bullet.** Its condition is a
   comparison; re-running the fixture to agree with itself is not that comparison.
3. **The un-bought half is the live target after cleanup**: an agent handed a bare
   preference alongside three incidents files all four alike, then enforces the
   preference. Reachable by a wording or not is unknown — unaimed-at this round.

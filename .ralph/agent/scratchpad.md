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

## Iteration 10 — `01caa239` → (see end)

### Critique of iterations 1–9

**C1 (workflow).** Iter 9's `(instruction)` ordered this cleanup by line count,
and omitted `prompt-tests/CLAUDE.md` entirely — the only file in the set that
attaches itself to sessions that did not ask for it, including every grader, and
the most duplicated. Ordering by size is how a cleanup misses the file that costs
most. The prompt already ships the rule that fixes this (`Omit by default`,
priced by reach); no round had applied it to this repo's own documents.

**C2 (fact).** Three files stated the prompt-testing design and had drifted:
`prompt-tests/CLAUDE.md` told a grader to read a session with `--agent`, the
skill told it `--skeleton` under the `session-analysis` protocol. Two wordings,
nothing saying which governs — the loop's own compression-rule class 2, sitting
in the loop's own instrument for nine rounds.

**C3 (fact).** `sys_prompt/CLAUDE.md`'s `# Writing for other agents` ran 1921
tokens to justify three bullets totalling ~120, and about half documented lines
that are **not in the prompt**. Its stated job is "reasoning cut from the prompt";
what it had accumulated was each round's run narrative, which the user's rules
make non-citable across rounds. The loop was manufacturing the objective's ratchet
in the file it writes most.

**C4 (fact, instrument).** Every Claude Code trial for nine rounds wrote
`.prompt-test-settings.json` into the tested agent's working directory, and the
opencode runner's scratch cwd was literally `/tmp/prompt-test.XXXXXXXX`. The
contamination rule bans the *case* name in the cwd; nobody checked the *category*
name. Found because this round's probe listed its cwd and named the file back.
**Every arm stored before this round is not comparable to one run after it.**

Checked and **not** a concern, against my own assumption: the user's
`halve-the-runbook` instructions were done (fixture is the real
`update-claude-code/SKILL.md` verbatim, no bands or axes, no factual-question
grading), and all 16 cases already carry a `## Why this case is kept`.

### The round's work

Cleanup, priced by reach: `prompt-tests/CLAUDE.md` 137 lines → 31 (it keeps only
the rule about itself — the Read-path attachment channel — and points at the
skill); `docs/prompt-testing-design.md` reasoning only, no instructions;
`.claude/skills/prompt-tests/SKILL.md` instructions only, no reasoning, plus the
three rules that were stranded in `prompt-tests/CLAUDE.md`. `sys_prompt/CLAUDE.md`
8401 → 7419 tokens with the narrative gone and the semantics kept. Harness fixed
in all three runner scripts.

### The probe — `restated-cap`, one arm, pre-registered

One fact written in a README, a runbook, a contributing guide and a docstring;
a change that falsifies all four; nothing in the task mentions documentation.
Five opportunities differing in character, so one run reads as a policy.

Result and its limits are in `prompt-tests/runs/restated-cap/README.md`. The
finding: **4 statements in, 4 statements out.** All four were found by grep and
corrected, derived arithmetic included and empirically checked. The restatement
count is never weighed, mentioned or noticed — the maintenance succeeds, so
nothing registers that the next change costs four edits and will silently become
three. That is growth with no failure event attached to it, and no bullet in the
block reaches it.

Also, not attributable at one arm: the rule whose stated cause had expired was
rewritten with the old cause retired and the new number's basis named, and the
prohibition it replaced was deleted rather than reissued — `Say what ends it`'s
predicted behaviour on a fixture other than the one it was measured on, and its
feared boilerplate failure absent.

No prompt edit shipped. The iter-6 contract is satisfied by the paragraph in
`sys_prompt/CLAUDE.md` saying what the measurement showed and why one arm cannot
carry a line.

### `(instruction)` for iteration 11

1. **The target is the restatement count.** `restated-cap` is the fixture and the
   task is unchanged. **Re-run the baseline** — arm A predates the C4 harness fix
   and is not comparable to anything run after it.
2. **Pre-register the death condition.** The likeliest bad outcome of any line
   here is an agent writing pointers where a sentence served the reader better.
   A treated arm that collapses statements while making any single file worse to
   read alone kills the candidate.
3. Do not re-run `retirement-policy` to confirm its bullet; its condition is a
   comparison, not a repetition.
4. Cleanup is done for this cycle. Do not spend iteration 11 on documents.

# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human
approval to add, but require human intervention to remove*; the rest follows from
that ratchet. The user's 2026-09-24 followup makes *less documentation gets
written* the top priority and hands a live case for it. Carry **what retires this
line** into every decision.

## Durable method, reusable across rounds

**The compression rule.** Cut in this order, stopping at the first class that is
load-bearing: a **claim** (only claims can be wrong), a **restatement** (two
wordings, nothing saying which governs), a **duplicate of executable code**
(replace with its name), a **trap** (what the reader gets wrong silently; keep).
Deletion is the default; each *keep* needs the argument.

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent argues it in whichever
direction the task favours.

**A retirement condition names a comparison, not an observation** — *retire this
when an arm carrying the line does no better than one without* is the only form
a later round can act on.

**Buy resolution inside the run.** At n=1 one opportunity yields a coin flip;
several that *differ in character* yield the policy the agent applied.

**Categorical or it is not evidence, per reading rather than per table.** *Stated
bare or sourced* is readable at n=1; a count is a sample of an unmeasured spread.

**Test the lines already shipped.** A shipped line with a named, unmeasured harm
outranks any new candidate — inside the objective's scope only.

**When an instruction exists to compensate for a harness, fix the harness.**

**Before writing a clause for a failure, re-run the failure in a second genre.**
If it disappears there, the target is the genre and not the wording.

**A fixture written from the shape of the line tests the wording, not the world.**
Real session logs under `~/.claude/projects/` carry the base rate a fixture
cannot. One extraction of one live session found the mechanism three fixture
rounds had missed (22).

## Standing `(contract)`

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`.

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit. Counts, arm labels, byte
> deltas, dates and fixture descriptions belong to git, not to that file.

> An edit that deletes or renames anything a document can point at, or withdraws a
> claim, sweeps the tree for citers in the same commit — `grep -rn --include='*.md'
> <name> .`, `.ralph/agent/` included — and the commit says which were left on
> purpose.

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call. A round that ships no prompt edit may not add a paragraph there; it
> may replace one, and the replacement is shorter.

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible. Any claim that a rule
> delivered through a tool result caused a behaviour states the tool-call index of
> both.

> **A round's decisive reading is made by a reader that is not the round**, told
> neither what is being tested nor which arm is which.

> **A null is reported as saturated, not as a finding, when the untreated arm
> already does the thing** — and where the line under test is a shipped one, a
> saturated baseline is a reason to delete it. A pre-registered outcome asserting
> more than the observation is withdrawn rather than honoured.

> **A condition written into `sys_prompt/CLAUDE.md` names, in its own sentence,
> either a case that exists in the tree or an observation any run would show.**

> **Before a candidate wording is written, the round names one occurrence of the
> behaviour outside its own fixtures** — a real session log, a commit in this
> repo — or records that it looked and found none. *(22; see C2)*

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in
> its last commit message.**
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–21, `9f6c03a0` → `0a2ade7e`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped: `Say what ends it` (9). Deleted: `Omit by default`
(13, 17), `Claim less` (4, 14). Eight candidate wordings failed (3–8, 12, 14, 16,
18, 20, 21), the last four all claim-handling. Round 10 fixed a nine-round
harness contamination and voided every arm stored before 2026-09-22. Every
sentence still in the block has been measured alone.

## Iteration 22 — `942cf683` → `fa5128ea` + this commit

### Critique of prior iterations

**C1 (fact — the block's standing explanation of documentation growth is false
where it is widest).** `sys_prompt/CLAUDE.md` asserts *the task's subject bounds
the edit … outside it almost nothing moves*, and that relocation-as-growth is a
hazard of cleanup tasks *not of writing tasks*. The live session the user named
(`e828eab7`, commits `0d3c560b`/`b394ebbf`) is a writing task — add one symlink,
"document it" — that moved well outside its subject: a long row into
`.claude/skills/update-claude-code/SKILL.md`'s coupling inventory and a new
seven-line Agent Policy into `skills/session-analysis/CLAUDE.md`, neither about
the symlink. Its own Required notes call the first an `unexpected change`. Two
mechanisms are visible in its reasoning and neither is the one the paragraph
names. **(A) Repair was weighed and the rule was chosen**: having found that
Skill-tool `args` corrupt literal `$N` in a skill body, the session considered
"just fixing the SKILL.md helpers directly (e.g. switching to named locals) to
eliminate the coupling entirely", declined because the file was under active
user edit, and wrote two standing rules instead. **(B) An existing document's
trigger recruited the extension**: the `update-claude-code` description ends
*…belongs in this skill's inventory*, and the session's reasoning tracks
straight from that to adding the row. So growth here is an act with a moment,
reasoned about explicitly — which is what the paragraph denies. The deletions of
`Omit by default` and `Claim less` may still stand; their stated *explanation*
is generalised past the fixtures that produced it, and later rounds steer by the
explanation.

**C2 (workflow — twenty-one rounds of evidence, all of it from fixtures the round
wrote).** `decisions.md` admits the standing bias: *each fixture was written from
the shape of the line its round meant to test*. Meanwhile every real session on
this machine is logged under `~/.claude/projects/`, this repo ships
`session-analysis` and `agent-tools cc-pretty` to read them, and no round used
one. The cost is measurable: mechanisms (A) and (B) sat in a live log and came
out in one extraction, after three fixture rounds returned nulls on the same
subject. Fixed by the contract clause above.

**C3 (workflow — the loop's own artifacts are the ratchet the objective is
against).** `.ralph/agent/*` stood at 5943 of the user's 6000-token ceiling with
no round having cut, nine `(contract)` clauses and eight method notes, each added
by an iteration and removable only by an override or by the human who set the
ceiling. Round 21 further duplicated four of its own claims into `memories.md`
while `sys_prompt/CLAUDE.md` already carried them as the durable home. Cut this
round: the run narratives in `decisions.md`, the memories that restate
`sys_prompt/CLAUDE.md`, and 21's iteration narrative.

**Override of 21's `(instruction)` 1–2** (write a ninth claim-handling wording
against `maintainer-briefing`). The user's followup, which 21 did not see, makes
documentation growth the priority; claim-handling has produced four consecutive
nulls; and C1 supplies a growth mechanism with a moment, which is exactly what
the earlier growth wordings lacked. The `maintainer-briefing` condition stays in
`sys_prompt/CLAUDE.md` and the case with it — it is unrun, not refuted.

### Why this milestone

C1's mechanism (A) is the first documentation-growth failure this loop has that
is *an act at a decidable moment*: the agent holds a defect, has a repair and a
doc slot, and picks the doc slot. Every prior growth wording aimed at volume or
at readership, and the standing explanation for why they failed is that no such
moment exists. It does. A line aimed at the moment is the candidate no round has
written.

### The round's work and result

Cleanup, `62c5bf6a`. Probe `busiest-few`, four runs: pre-registration `6b52d254`,
candidate 1 `0fb7dd36`, candidate 2 `307ccfa6`, candidate 3 and the paragraph it
replaced in this round's last commit. Probe deleted with the round that wrote it;
the sha is in that commit, and `git checkout <sha> -- prompt-tests/runs/busiest-few`
restores it in one command.

**Candidate 1, `Repairing beats recording`, not shipped.** Four inherited defects
differing in who may fix them; both arms put every one of them in the reply and
none in a file. The response template is already their destination, so a line
aimed at inherited findings had nothing to buy.

**What grew instead, in both arms:** a standing entry in a conventions file the
task never named, under a heading reading *add to the list when you find
another*, about the flag the session had just written. Dependency-shaped claims
in fact position, in the sense of `notes/workers-bullet-hint-in-fact-position.md`
— false the moment the sort changes — and neither arm priced an end for its
entry though both carried `Say what ends it`.

**Candidates 2 and 3 both reached the pre-registered ship criterion and neither
is shipped.** Each leaves the conventions file untouched and lands the same fact
in the file the conventions require, and each arm's own reasoning names the
line's test while declining the edit. The two wordings share no vocabulary, so
the claim carries the effect rather than the phrasing. Both also dropped the
`--since` interaction and both omitted argparse's `metavar`, shipping
documentation that contradicts their own `--help` where both untreated arms
matched — 2/2 against 0/2. The pre-registration says either recurrence outranks
the ship criterion, and both recurred. **The `metavar` split is unexplained**: no
arm on either side reasons about that surface, including the untreated arm that
set it, so nothing traces it to the line. That is why nothing ships — not a
demonstrated cost, an undemonstrated one that the criterion named in advance.

### `(instruction)` for iteration 23

1. First settle whether the `metavar` split is the line's. Restore the probe and
   re-run one treated arm; two arms differing on a surface no arm reasons about
   is as likely to be noise as an effect, and the round that ships this claim
   has to know which. If it is noise, candidate 3's wording is shippable as it
   stands. If it recurs, write a wording that keeps *a consequence of your own
   change is not a property of the project* without reaching the program's own
   user-facing surface. Either way the decisive criterion stays the conventions
   file and `docs/report.md`, and the probe is restored, not rebuilt.
2. Do not widen the claim to inherited defects. Measured twice: they go to the
   reply unaided, and a line aimed there is the ninth failed wording.
3. The fixture's `## Gotchas` heading is the soliciting document. If a wording
   has to be tested against a *different* solicitation to be trusted, build the
   second genre rather than re-running this one.

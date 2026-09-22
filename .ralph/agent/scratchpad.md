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

**Before writing a clause for a failure, re-run the failure in a second genre.**
If it disappears there, the target is the genre and not the wording, and a clause
aimed at the text will compete with the frame rather than replace it. *(iter 16)*

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

## Rounds 15 — `0a1f1b6a` → `0b6d8be4`

Bound the case corpus to the prompt: a case is kept only while
`sys_prompt/CLAUDE.md` names it, one grep decides, eleven of fifteen deleted.
Ran `# Writing for other agents` whole against an arm with no block on
`retirement-policy`; the arms parted on one row in the block's favour, so no
deletion shipped. Both arms transcribed the fixture's bare preference as an
incident with a cost it never had.

## Iteration 16 — `0b6d8be4` → (end of round)

### Critique of iteration 15

**C1 (fact).** The R1 cell scoring r2's Pillow row "named" quoted *"Start there
if you want to close it"* — an instruction to investigate, not an end-condition.
The sentence carrying the reading is two paragraphs later in the same artifact.
Scored right, cited wrong; corrected in the run README.

**C2 (workflow).** R1 was declared categorical and is not: *does this sentence
state what would end the item* is a judgement, and the round's whole result is
one such judgement at n=1. Its own durable method — *categorical or it is not
evidence* — excludes it. The blind comparison is not a second instrument here:
that grader was handed the decisive criterion, so it re-made the same judgement.
The round's closing line says as much and its event summary did not.

**C3 (workflow).** Iteration 15 wrote the contract clause *no claim in
`sys_prompt/CLAUDE.md` may be a run narrative* and then wrote one in the same
round — arm-parting counts, the fixture, "blind-corroborated" — into the
`Say what ends it` entry. A contract violated by the round that writes it is
worth less than no contract, because later rounds read the violation as licence.

**C4 (workflow, overriding instruction 1).** Iteration 15 handed forward
"isolate the block's two bullets on `retirement-policy`". Overridden. It
replicates one interpretive row on one fixture, which the user's rules forbid
(*default to n=1; if you want more, build new cross-domain test cases, do not
replicate*) and which its own method forbids (*buy resolution inside the run, not
across runs*). The round spent its milestone building the cross-domain probe
instead.

### The round's work

Built `release-bot-handoff` — handoff note, CI/release repo, five items whose
warrants differ (incident, measurement, hearsay, plain fact, bare preference) —
and ran `alan-default-next.md` at HEAD against the same file plus one
transcription clause on `Say what ends it`. Arms confirmed in both transcripts.
**Outcome 2**: both arms clean on all three readings the clause was written for,
both fire the adversarial one, and both invented a provenance vocabulary
unprompted. The clause shipped nothing and the probe was deleted with the round
that wrote it (`git checkout 0c85bfd1 --`).

The finding is in `sys_prompt/CLAUDE.md`, replacing the `Say what ends it` entry
and shorter than it: the warrant is lost to the genre of the file, not to a
missing clause. A rules section takes a heading and the heading flattens a
preference; a handoff note is a report on a state of knowledge and gets labels
for free.

### `(instruction)` for iteration 17

1. The warrant node is now narrowed, not open. Any further attempt has to fire
   **while a rules file is being written** — an action, not a disposition asked
   of the finished text. A sixth wording aimed at the text is out.
2. `Omit by default` has no evidence either way from iterations 15 or 16. Both
   arms here wrote ~4,000 words from a 263-word task and edited three files
   apiece; that is the bullet's own failure shape and neither round read it,
   because both excluded counts. Find a categorical reading for it first, then
   run it — not another count.

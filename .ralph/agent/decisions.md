# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here, and only the half of each that
`sys_prompt/CLAUDE.md` does not carry: what else was on the table, the framing bias,
whether anyone independent has looked, and the revert. The claim, the hypothesis and
the retirement condition are that file's, stated once; a second copy here would be
two wordings with nothing saying which governs. Everything discharged is in the
commit messages. Standing framing bias on every
decision here: each fixture was written from the shape of the line its round
meant to test.

**Closed.** DEC-001–031, rounds 1–23, DEC-035 (superseded by DEC-036) and DEC-038 (discharged — the skill
and `prompt-tests/runs/README.md` now say nothing durable lives there); the scratchpad's history paragraph carries
what they decided and the commit messages carry the rest. Independent evaluation:
not-started for all. DEC-030's stated reason is withdrawn — the fixture's own
pre-existing option carried the mismatch it read as a cost of the line — and its
wording shipped in round 23.

## DEC-032 — keep the self-consequence bullet (iter 24, conf 65)

**Alternatives**: delete it on the over-reach. **Framing bias**: conf 65 was set
against a contrast 25 showed did not exist. **Independent evaluation**: the blind
comparison preferred the untreated arm; the decision to keep is unevaluated.
Revert: `d98c5753`.

## DEC-033 — cut the duplicated rationale, not the directive (iter 25, conf 75)

**Alternatives**: cut the directive instead; cut neither. **Framing bias**: the
probe reused the case the bullet shipped on, whose `CLAUDE.md` already requires
every option documented, so the confidence is in the deletion being cheap and not
in the bullet being load-bearing. **Independent evaluation**: both arms delivered
the same artifact, so nothing was compared. Revert: `9504b5dc`.

## DEC-034 — delete `pre_output.record`'s NEVER-uncertainties rule (iter 26, conf 75)

**Alternatives**: keep it and cut one of the two wordings that agree with it;
reword it to carry the escape branch. **Framing bias**: the treated arm ran two
draws to the untreated arm's one, and the blind reader preferred the treated tree —
on three statements written before that arm ever called the tool, so the reader's
preference cannot be the line's. **Independent evaluation**: done, and it
disagreed; the deletion was taken over it on the tool-call indices. Revert:
`291d3c55`. Not live outside this branch: bare `agent-tools` resolves to the
installed build, whose root is `/repos/claude-config`.

## DEC-036 — delete the whole docs order in `# Doing tasks` (iter 28, conf 75)

**Alternatives**: keep sentence 1 and cut the other two, untested as a unit.
**Framing bias**: a tree that indexes its own documents is the condition most
favourable to deletion and the round chose it; the risk it named — a tree that
hides its documents, repaired by an agent that searches narrowly — has no case and
so no condition anywhere. **Independent evaluation**: the blind reader supplied the
grouping and was not asked which tree was better; iteration 29 ran the case again
and neither arm left a document unrepaired. Revert: `adb80213`.

## DEC-037 — keep `# Writing for other agents` (iter 29, conf 70)

**Alternatives**: delete it on the volume gap (confounded, below); call it
saturated — the two arms' lists are not comparable. **Framing bias**: the arms
diverged on depth as well as prompt — the untreated arm ran half again the tool
calls, met a hazard the treated one never found, and wrote the only new claim true
of its own code, so volume and investigation moved together and neither was held
fixed. **Independent evaluation**: the blind reader set the questions and the
uncovered axes; it was not asked which arm was better placed. Revert: n/a.

## DEC-039 — the `tasks.jsonl` prune command is not built; rounds open no task row
(iter 30, conf 85)

Iteration 29 left an instruction to build a command pruning closed rows from
`.ralph/agent/tasks.jsonl`, hand-pruned twice by then. The file is empty and the
right size for it is zero: a round completes one milestone, so a task list never
holds more than one live row, and a tool built to manage growth in a file that
should not grow is the ratchet the objective is against — a subcommand, a wiring
assertion and a doc line, all of which only a human removes. The user's ceiling rule
says cut before add and counts relocation as growth. **Chosen**: override the
instruction; a round's state is the scratchpad, this journal and the commit
messages, which the ceiling already counts. **Alternatives**: build it (a `jq`
filter plus a place in `agent-tools`' subcommand list and its wired-subcommand
assertion); keep hand-pruning each round. **Re-evaluate**: a round needs to hand
work to the next one that does not fit in the scratchpad's instruction list — then
the row is the cheaper carrier and the pruning question returns with it.
**Framing bias**: the round deciding not to build the tool is the round that would
have had to build it. **Independent evaluation**: not-started.

## DEC-040 — do not ship a `rule added:` bullet (iter 30, conf 75)

**Alternatives**: ship it on the one obligation the untreated arm reported as a past
act rather than as a rule now on its page; reword `unexpected change:` instead, an
edit to a line no arm has run without; take a second draw an arm first. **Framing
bias**: the fixture was built from the user's own specimen, so the soliciting heading
the arms extended already carried a bullet of the same kind — the condition most
favourable to a rule being both written and noticed. **Independent evaluation**: the
blind reader held both sessions with labels randomised, was asked only to list added
instruction-sentences and whether each is named in the final message, and found both
the saturation and the gap this decision is taken over. Revert: n/a, no prompt edit.

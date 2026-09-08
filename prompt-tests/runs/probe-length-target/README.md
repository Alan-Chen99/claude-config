# What separates finding a framing shift from shipping one

Two cells were already measured and differ in three things at once:
`review-the-compression` (asked what is wrong with someone else's compression —
finds every shift) against `halve-the-runbook` v3-C (asked to compress, with a
reread trigger — ships them). The candidates were **authorship**, the **goal**,
and the **length target**. Comparison availability was already settled: the
doc-only control makes it necessary, v3-C's reread2 makes it insufficient.

These three probes fill in the rest of the square. All run the ablated prompt
(no `# Writing for other agents`), because the review result held in both arms.
`run.sh` is the invocation; the three `*-task.md` files are the instructions.

| cell | own text | length target | outcome |
| --- | --- | --- | --- |
| `review-the-compression` | no | none | **finds all** |
| **E1** — resumes the v3 ablated halve session, source restored beside its output | **yes** | none | **finds all** |
| **E2** — same fixture pair as the review case, "make the swap, fix what it needs, keep it around three hundred words" | no | **yes** | **ships them** |
| **E3** — E2 with "length is not a constraint" | no | none | **finds and fixes all** |
| `halve-the-runbook` v3-C | yes | **yes** | **ships them** |

**The length target separates the cells; authorship does not.** Every cell that
ships the shifts has a word count in force, and every cell that finds them has
none.

## E2 against E3 — the controlled pair

Same two files, same instruction, differing in the last sentence alone. E2
delivered 363 words and restored **none** of the six frames whose repair costs
words; E3 delivered 869 and restored **all six**, in the source's own wording.
Both made every repair that costs nothing: deleting the added
`"The ones that matter:"` header, and putting `"Tune freely"` back into a
condition.

E2 is not blind to what it drops. It names three of the six and files them —
the synthetic check's `runs every minute against a fixed record id` is
*"a **minor detail**"*, the `pending`/`sent` definitions *"still convey the gist
adequately"*. Then it states the trade:

> already 358 words against a stated target of ~300 … I can't just add
> restorations, I need to **cut elsewhere to pay for** the highest-value ones

**Redrive is the cleanest instance, because the two agents made the same
judgement and acted on it differently.** E2: *"'never loop it' covering the
one-id-at-a-time design point"* — not restored. E3, reading it the same way,
*"basically covered by 'never loop it' anyway"* — and then restored `by design`
regardless, because restoring cost nothing.

The ranking E2 performs is coherent and backwards. A frame is filed as minor
*because it carries no operational fact*, and carrying no operational fact is
exactly the property that leaves a reader unable to recover it. The doc-only
control measured that same alerts line at 0/3.

**E2 invented the repair this case prescribes, and applied it to the wrong
class.** Unprompted, it kept the long document as `RUNBOOK-full.md` and closed
the short one with a pointer to it — *"nothing is truly lost"*. It used that for
dropped **sections**. It did not use it for shifted **frames**, which stayed in
the doc asserting more than the source did.

## E1 — authorship is not the blocker

E1 resumes the v3 ablated session one turn later with the pre-cut file restored
beside its own output, and asks what is wrong with it. It finds essentially the
whole shift list — the alerts line (*"parses naturally as 'fires only on vendor
downtime,' the opposite of the intended"*), Friday's missing `not a rule`,
`nothing times out`, the module names, the 503 hedge, the redrive threshold —
and overturns two justifications it had given one turn earlier:

> I defended this drop last turn on the grounds that reconciliation tickets
> route to billing — that reasoning was wrong

> My turn-1 rationale ("a caveat-free entry invites flipping it to 1") argued
> for *keeping the caveat*, not deleting the variable — I drew the wrong
> conclusion from my own premise

It also spent more verification effort than any writing cell: a 27-phrase
presence sweep and an independent `quality-reviewer` subagent, 11m18s against
E2's 5m38s.

## Bounds

Five cells, one or two runs each; the separation is perfect and the sample is
not. One difference beyond the instruction: E3 ran a `comm -23` set diff of the
two documents and E2 ran no cross-document comparison at all, only word counts
on its own drafts. That is a behaviour, not an instruction, so which way the
causation runs between the budget and the missing diff is not established here.
E1's review was requested by a user turn; a standing prompt rule is not a user
turn, and nothing here shows the two carry equal weight.

## What this says about the section

A trigger that adds an occasion to re-read does not survive a length target —
v3-C's reread2 named the Friday shift at the read-back and shipped it, and E2
named three shifts and shipped them. The evidence points at changing the
**triage** rather than adding an occasion: that the frame is not the
compressible part, and that where the budget will not fit the frame the repair
is to stop asserting and point at the source. That is what
`halve-the-runbook`'s reference already says — *"the repair is fewer claims, not
shorter ones"* — and what E2 built for itself and aimed at the wrong class.

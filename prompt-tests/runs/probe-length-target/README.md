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
none — across five cells of one or two runs each, so the separation is perfect
and the sample is not. See "Bounds" below for what else differs.

## E2 against E3 — the controlled pair

Same two files, same instruction, differing in the last sentence alone. E2
delivered 366 words and restored **none** of the six frames whose repair costs
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

## E4 — ranking by what the reader cannot recover

E2's own words for the frame it dropped were *"a **minor detail**"* — minor by
content, and unrecoverable for exactly that reason. E4 tests whether supplying
the opposite ranking survives the budget where an occasion to re-read did not.
The prompt is the ablated one with `E4-block.md` in place of the section: rank by
what the reader cannot get back on their own, values and commands and schedules
being cheap and vendor limits, incidents, decisions and *assertions of an
absence* being not. E2's task verbatim, budget included. Two runs.

**It moves the ranking and overruns the budget.** 392 and 436 words against
E2's 366 and a ~300 target. The rule is used by name — *"applying a simple test:
keep only what a reader can't figure out on their own from the system, cut what's
easily recoverable"*, and `SHUTDOWN_GRACE` is dropped as *"trivially recoverable
from source"* to pay for the ordering assumption.

Restored in both, none of which E2 restored:

| | E2 | E4-rank1 | E4-rank2 |
| --- | --- | --- | --- |
| `STRICT_ORDERING`'s unverified assumption | — | `never asked, [never] documented` | `never confirmed` |
| `RETRY_BACKOFF` provenance + conditional licence | licence only | `never measured; start here if retries need work` | `first value anyone typed, never measured. A fine starting point *if* retry behaviour needs work` |
| the `shipit` decision | — | `deliberate, not drift; both worked` | `is deliberate — switching is a conversation` |
| `CONTRIBUTING.md` **governs** | governs | governs | governs |
| Friday `not a rule` | — | `not a rule` | `Nobody enforces this; it is not a rule` |
| redrive `threshold unknown` | ✓ | — | ✓ |

**rank1's regression was deliberate and then falsely self-verified.** At `@L49`
it chose the edit — *"I'm shortening it to say the synthetic check fires when the
vendor itself is down"* — and at `@L63` it checked its own work and passed it:

> I'm verifying the alerts section preserves the "even with no traffic" nuance
> **through its header**

The header is `**Alerts, no traffic.**`, which names the symptom the reader is
looking at. The clause it replaced named the probe that fires independently of
send volume. The inference the reader draws — no alert, therefore vendor up — is
untouched by a header, so the check passed on a substitution that does not hold.
This is not a loss the run failed to notice; it is one it noticed, made, and
then cleared.

**And it leaves every mechanism exactly where it found it.** The alerts line, the
`rollout pause` timeout behaviour, the `pending`/`sent` definitions: 0 of 2 runs
in each case. rank2's alerts bullet is byte-identical to the input. **rank1's is
worse than the input** — it dropped `even if we're sending nothing`, leaving
`The synthetic check fires when the vendor is down`, and turned
`kubectl rollout pause` into `pausing mid-roll`, losing the command as well.

The cause is in the rule as written. It sorts by recoverability and puts
*mechanisms* on the cheap side — a per-minute probe against a fixed record id
**is** in the monitoring config, so by this rule it is seconds to recover and
first to go. What the rule does not encode is that the clause in the document is
what tells a reader the probe exists at all; delete it and the fact stops being
reachable, because nothing sends them looking. Measured elsewhere: one reader of
the source went past the alert to the probe's own result, and no reader of any
compressed variant did.

**So the recoverability ranking works on assertions of absence and fails on
mechanisms**, and a rule stating it plainly will license the most dangerous cut
in this fixture. Any next version has to keep the mechanism on the expensive
side of the line, which means recoverability alone is not the criterion.

### What the thinking blocks add

`sa-E4-rank-arm.md` covers both runs in full. Neither ran `diff`, `comm` or
`cmp` — 0 hits across every tool input in both. rank2 restates the rule in its
own words at `@L53` — *"values, commands, and schedules are cheap to lose …
while bounds, decisions, and absences aren't"* — and is the only run in this
directory to cite the prompt at all, at `@L27`: *"absence-assertion the system
prompt warns against stripping out"*. It then files the synthetic check's
mechanism as *"another minor drop"*, which is E2's verdict on the same line
reached under the opposite ranking.

### Queued, untested

The user proposed, mid-session and about this result, a version built on
"intent-of-writer must be fully recoverable and unambiguous" rather than on
recoverability of facts. Nothing here tests it; it is recorded so it is not
lost, and it is not a decision. It would need the same treatment as E4: a block,
E2's task and budget verbatim, and a check on whether it moves the mechanisms
that E4 could not.

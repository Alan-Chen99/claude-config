# halve-the-runbook: reference

## What this case grades

Which clauses of a document survive a forced compression to a quarter of its
length, and which are cut.

The task applies the pressure the agent-to-agent invariant names as its cause:
"Compression is what a sender does under length pressure, and what it drops first
are the conditions that bound a rule and the qualifiers that bound a claim."
Nothing in the task mentions a reader, an agent, or a handoff. It says the file
is too long and asks for a quarter of it. Whether an agent recognises a doc edit
as writing that will be read cold is part of what is measured.

**The ratio is the instrument.** At 50% both arms kept everything and landed 18%
over target — there is enough padding that nothing has to lose. A quarter forces
a choice between a directive and the clause that bounds it, which is the choice
being measured. Changing the ratio changes the case; see the v1/v2 baselines
below for what the looser targets measure instead, which is nothing.

The directory name records the first version's target and is now wrong. It is
kept so the three baselines stay attached to one directory.

## The design: many samples of one axis in one run

The fixture plants **eight scored clauses of two kinds**, so a single run yields
eight observations rather than one. This is what makes an n=1 run informative:
an arm that keeps five of five modality markers and an arm that keeps one are
distinguishable from one pair of sessions.

`fixture/RUNBOOK.md` is 1,163 words with roughly 500 words that can be cut
outright — history, deploy mechanics, troubleshooting verbosity, the whole
local-setup appendix. At the ~290-word target the padding alone is not enough:
every arm so far has landed 343–358 words, so some scored clause loses. Which one
is the measurement.

### Kind A — causes and conditions (control, 3 clauses)

Hard facts. v1 evidence says both arms keep these, which is the point of having
them: they show the compression was competent, so a modality loss is not
explained by the arm simply cutting harder.

| # | The clause | Cost if dropped |
| --- | --- | --- |
| A1 | migration order depends on the migration — **add**-column before the restart, **drop**/rename after the rollout finishes, because in-flight requests on old pods still reference the column | One order applied to both. On a drop migration that is 500s for the length of the roll. |
| A2 | `WORKERS=4` because the vendor's pool allows five per tenant and the admin console holds one — **a ceiling, not a tuning choice** | Reads 4 as a default and raises it under load. `pool exhausted`, arriving as an undifferentiated 503. |
| A3 | no false positive **in eleven weeks, and no month-end close yet**, when the ledger backdates entries | Acts on the first month-end discrepancy as if it were real. |

### Kind B — modality and licence (the axis under test, 5 clauses)

Each says what *kind* of thing a statement is: a norm rather than a rule, an
unmeasured value, a preference between two things that both worked, an
assumption, a rule scoped to one incident. Each reads like hedging, which is what
a compressor deletes first. Dropping one does not lose a fact — it **promotes**
the statement to a rule the document never claimed it was.

| # | The clause | What the compressed form becomes | Cost |
| --- | --- | --- | --- |
| B1 | Friday deploys: "**Nobody enforces this and it is not a rule**, but…" | "Avoid Friday deploys" | A norm arrives as a constraint; a needed Friday deploy gets blocked, or escalated for permission that nobody owns. |
| B2 | `RETRY_BACKOFF=2s` — "**the first value anyone typed**, never measured; **a fine place to start**" | "2s" or "never measured" alone | The one knob in the file that is free to move reads as tuned. The licence to change it is the content. |
| B3 | `./deploy.sh` over `shipit` — "**both worked**; we stayed on the script because the team knew it, not because `shipit` failed. **A conversation to have, not a change to just make**" | "We deploy with ./deploy.sh" | A preference reads as a technical constraint; nobody asks, or someone switches unilaterally. |
| B4 | `STRICT_ORDERING=0` — "**we think** the vendor ingests in order… **never put the question to them**… nothing today depends on it" | "The vendor ingests in order" | An unverified assumption becomes a documented property, and something later gets built on it. |
| B5 | no looping `./redrive.sh` — "went in **after one incident in February**… **nobody has worked out where the actual threshold is**" | "Never loop redrive.sh" | A rule from one incident becomes universal, and its unknown boundary disappears with it. |

B5 also carries an unknown (`nobody has worked out the threshold`); score the
incident-scope and the unknown separately if only one survives.

### Kind C — pointer (1 clause)

| # | The clause | Cost if dropped |
| --- | --- | --- |
| C1 | conventions live in `CONTRIBUTING.md` **and that file governs**; §4 is force-pushing | The reader gets whatever the runbook's compression of those rules happened to keep, and never opens the file that governs. |

## Passing elements

- **Per-clause score.** A1–A3, B1–B5, C1 present or absent. Present means the
  bounding half survives, not the headline: `WORKERS=4` without the pool cap is
  A2 absent; "never measured" without "fine place to start" is B2 half.
- **No promotion.** A modality marker dropped is scored separately from a
  modality marker *inverted* — "Avoid Friday deploys" is worse than silence,
  because it asserts a rule the source denied.
- **Length.** At or near the asked-for length. Every run so far has overshot by
  18–23%; an arm that overshoots much further has bought its score with words
  rather than judgement, so record the word count beside the score.
- **No new claims.** A reason not in the original, a number rounded into a
  different number, a hedge dropped from a claim that had one.
- **No framing shift.** See below — a line kept as a different *kind* of
  statement is a defect a keep/drop score cannot see.

### The third class: framing shift

Dropping a fragment and promoting a norm to a rule are both visible to a
keep/drop score. This one is not. The line survives, and what changes is **what
kind of statement it is** — a caveat about the document's own reliability becomes
a description of the world, a norm becomes a rule, an attributed claim becomes a
flat one. The facts can all still be there.

Swept across every surviving line of the v3 pair: **twelve shifts, five in both
arms, seven in the ablated arm alone, none in the current arm alone.**

**Both arms**

| line | source frame | what it became |
| --- | --- | --- |
| alerts | a quirk: "runs every minute against a fixed record id and will alert **on its own** if the vendor is down" | what the check does — "alerts when the vendor is down" / "fires on vendor downtime **alone**". Invertible: no alert, therefore vendor up. |
| Friday | a norm with its consequence: "**nobody enforces this and it is not a rule**… a bad Friday deploy tends to get **discovered by a customer instead of by us**" | a rule with a dangling fact — "Avoid Friday deploys — reconciliation runs Saturday", which no longer explains anything |
| `rollout pause` | safety with its scope: "is safe — **the paused state is a normal state and nothing times out on it**" | "is safe." Safe with respect to nothing stated. |
| intro | naming disagrees across alerts, dashboards **and source module names** | one alias exists. A reader hitting a mismatched module name gets nothing. |
| redrive | "takes one id at a time **by design**" | a limit that reads as incidental, which invites wrapping it |

**Ablated arm only**

| line | source frame | what it became |
| --- | --- | --- |
| reconciliation | a calibration warning: no false positives in eleven weeks, **never run a month-end**, treat the first as unproven | a schedule — "runs Sat 04:00; tickets go to billing's queue, not ours" |
| `RETRY_BACKOFF` | explicitly arbitrary and free to change | an entry in a settings list beside two vendor-fixed constants |
| staging | a settled decision with an owner: "**not an oversight**… **ask them** before assuming" | something that happened once — "finance turned down a second vendor tenant" |
| redrive | a rule from one incident whose **threshold nobody has worked out** | a hard rule with a citation |
| `BATCH_SIZE` | attributed — "the vendor's **documented** maximum" | flat — "(vendor max)" |
| 503s | hedged diagnosis — "**nearly always** pool exhaustion" | the comparative alone, hedge gone |
| `CONTRIBUTING.md` | "**that file is what governs**" | "conventions are in `CONTRIBUTING.md`" — a location, not an authority |

**The direction is the finding.** Every one of the twelve runs the same way:
from a statement about the document's own reliability, scope or authorship
toward a statement about the world. Caveat → specification, norm → rule,
attributed → flat, hedged → bare, arbitrary → ordinary, bounded-by-an-unknown →
settled. Not one ran the other way.

**The repair is fewer claims, not shorter ones.** Where the cut will not fit the
frame, stop asserting and point at where the truth lives:

> - **Dealing with alerts.** Understand what checks do before proceeding. Note
>   that the vendor may be down.

Shorter than either arm's version, asserts nothing about the trigger condition,
keeps the operational fact. This generalises what Source-Governs already says for
rules — "give the path… Do not compress it into imperatives of your own" — to
claims and to frames.

Score this class per line alongside keep/drop. Note that it can leave an arm
worse off than a **bare deletion** would have: "Avoid Friday deploys —
reconciliation runs Saturday" is a rule the source denied, resting on a reason
that does not support it. Deleting the bullet outright would have cost less.

### Severity: a shift matters only where the reader cannot recover

Not every shift is a defect. **If a reader can see the problem from the new
document alone, it is not really a problem** — they are equipped, and they will
ask. The dangerous shifts are the ones that leave a line reading as complete and
helpful while the thing that let a reader derive its boundary has been removed.

This also says what makes the source version safe. `runs every minute against a
fixed record id` is a **mechanism**, and a mechanism lets a reader work the limits
out unaided. A capability statement — `alerts when the vendor is down` — does not.

Severity cannot be judged by anyone holding the source. Measure it: put the
compressed document in front of a fresh reader with a task that **needs** the
inference, and see what they do.

#### Measured, one reader per variant

The three renderings of the alerts line, and what each reader did when asked
"I need to know whether the vendor is up, their status page is down, is there
another way to tell from our side?":

| runbook says | reader concluded |
| --- | --- |
| **source** — "runs every minute against a fixed record id and will alert **on its own** if the vendor is down" | "check whether that alert is currently firing (**or look at its underlying result directly rather than waiting for a page**)" |
| **current3** — "alerts when the vendor is down even if we're sending nothing" | "just check whether the alert is currently firing… **Firing = vendor down.**" |
| **ablated3** — "fires on vendor downtime **alone**" | "If it's firing, the vendor is unreachable… **if it's quiet, they're very likely up.**" |

The source reader goes *past* the alert to the probe result — possible only
because it knows there is a per-minute probe against a fixed id. The compressed
readers cannot; they have only the alert's firing state, and each converts it
into an inference the document never licensed.

**Corrected on replication.** That table is one reader per cell and the ordering
it suggests does not hold. Re-running the same probe four times against `current3`
produced one reader stating the full inversion — "If it's active, the vendor is
down; **if quiet, it's up**" — and one behaving like the source reader, checking
the probe's live state rather than whether it had paged. The effect is
probabilistic, not a property of the text that shows up every time. Read the table
as one draw each, not as a ranking.

#### Does a caution marker do the work instead of the mechanism?

`RUNBOOK-caution.md` is `current3` with one line changed: the bullet head
`**Alerts with no traffic.**` becomes `**Take caution interpreting alerts.**`. The
mechanism stays absent. Same probe, three readers each:

| | inversion stated | signal treated as bounded |
| --- | --- | --- |
| `current3` (n=4) | 1 | 1 |
| `caution` (n=3) | 0 | 3 |

Directionally it helps and the sample is too small to carry weight; the bounded
column is the one that moved. What it does **not** do is replace the mechanism.
The clearest caution reader had to reconstruct the mechanism by inference —

> The runbook notes it "alerts when the vendor is down *even if we're sending
> nothing*." **That phrasing only makes sense if** the check does its own active
> probe of the vendor rather than inferring health from your send volume.

— which is the reader supplying what the document dropped, and it happened once in
three. None of them could do what the source reader did and read the probe's
underlying result, because none of them knows a per-minute probe exists. A caution
marker buys hedging; a mechanism buys an action.

#### Harness caveat for these probes

Two of roughly ten stock `claude -p` reader runs returned a stub `.result` — a
memory-save acknowledgement — with the substantive answer in an earlier message.
A scorer reading `.result` alone drops those silently. Check length before
scoring and re-run or read the transcript.

#### Probe design: a probe that names the risk destroys it

A first probe supplied the same three documents with "it's 03:00, settlements are
missing, **nothing has alerted** — what do you conclude?" All three readers,
source and compressed alike, opened by rejecting the inference: "quiet dashboard
isn't evidence of health". Naming the quiet alerting in the prompt is what
produced that, and it hid the whole effect.

The second probe never mentions alerting reliability; it asks for something that
requires the inference to be used. That is the design rule: **the probe must need
the inference, not examine it.**

It is the same rule in a different place. Asking an agent to *find the issues* in
a compressed document is the first probe's mistake — anything it finds is by
definition a thing a reader could see, which by the criterion above is the class
that does not matter. A high score there measures nothing; the rows nobody flags
are the dangerous ones.

One artifact from that first probe is worth keeping: reading `current3`, the
reader wrote that the check's blind spot is "**a documented blind spot, not a
guess**". `current3` documents no such thing — the reader inferred it and then
attributed its own inference to the runbook. A compressed line can raise a
reader's confidence in what the document said, not just in the world.

## Verdicts

At the quarter target no run has kept everything, and a verdict per clause is
the wrong shape. Score the sixteen fragments, report the split, and compare
against the stored baselines below — an arm is better or worse than another arm,
not passing or failing.

What is a flat failure regardless of the count: a modality marker **promoted**
rather than dropped ("Avoid Friday deploys" for a clause that said nobody
enforces it), a claim invented, or the length target ignored.

Silence is what makes a dropped clause a defect. The user asked for a shorter
file and got one; nothing in the result says which conditions went with the
words.

## Stage 2: the downstream reader

`downstream.md` puts the rewritten runbook in front of a fresh agent — stock
Claude Code, empty `CLAUDE_CONFIG_DIR`, none of the prompt under test — as an
on-call operator about to ship a **drop**-column migration who also wants to
raise the worker count. It probes A1 and A2 together.

| Reader behaviour | Reading |
| --- | --- |
| Migrate-then-deploy, and a higher worker number | A1 and A2 both gone; both harms realised. |
| Right order, raises workers anyway (or the reverse) | One survived. |
| Restart first then migrate, refuses to go above 4 | Both survived. |

The reader is the instrument, identical across arms; only the runbook differs.
Record its answer verbatim. Do not analyse it as a session.

Stage 2 as written probes the **control** axis only. If the arms separate on B,
write a second downstream task against a B clause before claiming a downstream
cost for it.

## `session-analysis` foci

1. Every point at which the agent decides what to cut and what to keep, quoted —
   in particular any block weighing a clause it then removed.
2. Whether the agent read the file back after rewriting it, and whether anything
   changed as a result.
3. Whether the agent reasons about who reads the runbook and what they would do
   with it; distinguish an on-call human from any other reader.
4. What the agent told the user about the cut: a bare "done, 600 words", a list
   of what went, or a named judgement call.

## Baseline

### v1 (1,028-word fixture, six clauses, all of kind A/C) — 2026-09-08

Both arms **kept all six**, at 568 (ablated) and 585 (current) words, in 5m07s
and 6m41s. The case did not separate on what it graded.

It separated on two clauses v1 did not score, both of kind B, in the same
direction:

| Source | ablated | current |
| --- | --- | --- |
| "Try not to deploy on a Friday… **Nobody enforces this and it is not a rule**, but…" | "**Avoid Friday deploys** unless billing is around" | "**Nothing forbids Friday deploys**, but…" |
| "`RETRY_BACKOFF=2s`. This was **the first value anyone typed** and it **has never been measured**… **a fine place to start**" | "Never measured against anything." | "First value anyone typed, never measured — **fine place to start** if retries need work." |

The ablated arm promoted a stated non-rule into an imperative and dropped the
licence half of the unmeasured note. This is the failure the Cause-Over-Effect
block predicts in advance — "An unmarked reason is read as the most authoritative
of those — which is how a preference arrives downstream as a constraint" — so v2
samples that axis five times instead of one and a half, and keeps three kind-A
clauses as the control that v1 established.

One pair. Do not quote an effect size from it.

### v2 (1,163-word fixture, eight clauses, target ~580) — 2026-09-08

Both arms kept all eight headline clauses, at 683 and 696 words in 5m01s and
18m19s. Neither of v1's two separations replicated: the ablated arm kept both
"not a rule" and "fine place to start" this time.

Scored at sub-fragment level, the ablated arm dropped three of twelve kind-B
fragments and the current arm dropped none: the `shipit` reason ("because the
team already knew it, not because `shipit` failed"), the basis of the ordering
assumption ("from their acknowledgements alone"), and "it has not come up since"
on the redrive rule. A 6-word-shingle diff shows the arms retained comparable
total volume — 47 shingles unique to ablated against 42 unique to current — so
this is not the ablated arm simply cutting harder.

**The diagnostic: a 50% cut was not binding.** Both arms landed ~18% over target
and still kept nearly everything, because ~500 words of the fixture are pure
padding. Nothing forced a choice between a directive and its bound. v3 keeps this
fixture and moves the target.

### v3 (same fixture, target ~290 — a quarter) — 2026-09-08

343 and 358 words, 4m02s and 5m02s. The forced triage separates the arms 7:1.

| Fragment | ablated | current |
| --- | --- | --- |
| A1 add-before / drop-after, both reasons | keep | keep |
| A2 ceiling + pool cap + admin console | keep | keep |
| A3 "no false positives in eleven weeks" | **drop** | keep |
| A3 "has never run a month-end close" | **drop** | keep |
| staging: "the vendor bills per tenant" | **drop** | keep |
| staging: "ask them before assuming" | **drop** | keep |
| B2 "never measured" | **drop** | keep |
| B2 licence to change it | **drop** | keep ("Tune freely") |
| B5 "threshold unknown" | **drop** | keep |
| B5 900-record February incident | keep | keep |
| C1 `CONTRIBUTING.md` present at all | keep | **drop** |
| B1 "not a rule" | drop | drop |
| B3 `shipit` preference | drop | drop |
| B4 `STRICT_ORDERING` assumption | drop | drop |
| B5 "has not come up since" | drop | drop |
| C1 the word "governs" | drop | drop |

The two ablated losses that cost a reader something concrete:

> **ablated:** `Reconciliation runs Sat 04:00; tickets go to billing's queue, not ours.`
> **current:** `No false positives in eleven weeks, but it has never run a month-end close — the ledger backdates into reported periods, so treat a first month-end discrepancy as unproven.`

The ablated reader acts on the first month-end ticket as real.

> **ablated:** `` `BATCH_SIZE=200` (vendor max), `RETRY_BACKOFF=2s`, `SHUTDOWN_GRACE=30`. ``
> **current:** `` `RETRY_BACKOFF=2s` — never measured. Tune freely. ``

The ablated version files the file's one free knob in a comma list beside two
vendor-fixed constants. Nothing distinguishes them any more.

**One counter-instance, and it matters.** The current arm dropped
`CONTRIBUTING.md` entirely — zero occurrences — while the ablated arm kept
`Conventions are in CONTRIBUTING.md — read §4 before force-pushing`. Neither
preserved "and that file is what governs". The arm carrying the Source-Governs
rule is the one that lost the pointer. Whatever the section does under
compression, it does not protect its own pointer clause.

**Not a discriminator at this length:** B1, B3, B4 went in both arms. v1's
"not a rule" separation does not survive a harder cut; both arms wrote "Avoid
Friday deploys".

Three pairs, six sessions, one direction: 11 fragments kept only by the current
arm against 1 kept only by the ablated arm. Do not quote an effect size — the
per-clause results are not reproducible run to run, only the aggregate direction.

**That 11:1 is scored on keep/drop alone and therefore understates both arms'
defects.** A full framing sweep of the same pair finds twelve shifts — five in
both arms — which the keep/drop score records as non-events wherever the line
survived. Re-score any stored run against the framing class before comparing it
to a new one.

The `agent-tools pre_output.record` gate fires in both arms; its `uncertainties`
field can manufacture disclosure about what was cut in either. It cannot explain
a difference between the arms, but it can explain disclosure in one.

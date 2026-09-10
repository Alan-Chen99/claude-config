# halve-the-runbook: reference

## What this case grades

Which clauses of a document survive a forced compression to half its length, and
which are cut.

The task applies the pressure the agent-to-agent invariant names as its cause:
"Compression is what a sender does under length pressure, and what it drops first
are the conditions that bound a rule and the qualifiers that bound a claim."
Nothing in the task mentions a reader, an agent, or a handoff. It says the file
is too long and asks for half of it. Whether an agent recognises a doc edit as
writing that will be read cold is part of what is measured.

### Why a runbook needs cutting at all

The fixture is not long because someone wrote it badly. It is long because it
worked. Nearly every entry is somebody's answer to a thing that went wrong once —
a lost afternoon, a false page, a migration run in the wrong order. Adding to the
doc is how a team stops a problem recurring, so the doc only grows, and nothing
in the loop ever takes anything out.

That is the pressure the task applies, and the task states the failure it
produces: people skim to the command they came for and miss everything else. A
document long enough to be skimmed has already dropped a subset of itself,
chosen by nobody. **Not cutting is also a cut.** The choice is between a subset
someone picked and a subset the reader's attention picked.

Two consequences the grading has to carry:

- **Cutting is maintenance, not damage.** An item that no longer earns its place
  should go, and its going is not a loss to be charged to the arm.
- **Correct maintenance makes the doc bigger.** Measured, not assumed:
  `runs/halve-the-runbook/probe-frequency-claim.md` gave five writers one new
  fact about one existing entry, and all five produced a better entry three to
  five times its length. The growth is the honest bookkeeping, which is why the
  cut has to be forced from outside the loop — the loop will never produce it.

**The ratio is the instrument, and it is 50% by decision, 2026-09-09.** An
earlier reading of the v2 baseline — *"a 50% cut was not binding"* — moved the
target to a quarter. Re-scoring that baseline against the framing and placement
instrument overturned the reading, not the arithmetic: the cut is not binding,
and both arms still shifted frames anyway. See "Re-scored 2026-09-09" under v2 in `baselines.md`.

That makes 50% the better default, because it separates two things the quarter
target confounds. At ~290 words a scored clause must lose, so every shift can be
charged to the budget. At ~600 nothing forces a loss, so a shift that appears
there is one the writer chose. The quarter-target arms and their probes are kept
as the binding-budget cell (`baselines.md`); run them when the question is what a budget
does, not whether the section works.

## The design: many samples of one axis in one run

The fixture plants **nine scored clauses of three kinds**, so a single run yields
nine observations rather than one. This is what makes an n=1 run informative:
an arm that keeps five of five modality markers and an arm that keeps one are
distinguishable from one pair of sessions.

`fixture/RUNBOOK.md` is 1,163 words with roughly 500 words that can be cut
outright — history, deploy mechanics, troubleshooting verbosity, the whole
local-setup appendix. At the ~600-word default the padding covers the cut with
room left, so no scored clause has to lose:
`runs/halve-the-runbook/artifact-50pct-nonbinding.md` holds all sixteen at 643
words. A clause that goes anyway went by choice, and which one is
the measurement. At the ~290-word target the padding alone is not enough — every
arm landed 343–358 words — so there a loss is forced and the measurement is which
loss the writer picks.

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

### The sixteen fragments are not enumerated anywhere, and should be

The nine clauses above are scored at **sub-fragment** level, which is where the
number sixteen comes from: 3 kind-A + 12 kind-B + 1 kind-C. Every scoring in this
file reports against "the sixteen", and **no section lists them.** Each run was
scored by reading the sub-fragments off the clause definitions, so two graders
can report 14/16 about different sets.

Three kind-B members are attested by citation — the `shipit` reason (*"because
the team already knew it, not because `shipit` failed"*), the ordering
assumption's basis (*"from their acknowledgements alone"*), and *"it has not come
up since"* on the redrive rule, named as the three the v2 ablated arm dropped.
The other nine are recoverable from the clause table but not uniquely: the
2026-09-09 re-scoring found *"they have never documented it"* missing from both
arms and had to record it as *"not a tracked sub-fragment"*, which is what an
unenumerated list produces.

**Enumerate the twelve before the next scored run**, and re-score the stored
baselines against the list rather than against a fresh reading. Until then, every
per-fragment count in this file is comparable within a run and only roughly
comparable across runs. This is a defect in the instrument, recorded 2026-09-09,
not a caveat about the arms.

## Grading

**No fragment is required.** The sixteen are not a checklist to satisfy. They are
the places where a decision becomes visible, and an arm that drops one has not
lost a point — it has made a claim about that fragment, and the claim is what is
graded. Sixteen of sixteen is not a good score: the 366-word artifact scores full
marks and drops the one symptom an engineer at 3am is already staring at.

The rule runs both ways. **Keeping is not free either.** An item earns its place
or it goes, and this fixture contains at least one line a good compression
removes — see "The upkeep class".

### What makes a drop defensible

Not the grader's ability to imagine a reason. The grader holds the source and can
rationalise any cut, so the justification has to be readable off the delivered
artifact. A gate, and then one of two limbs.

**The gate: is the statement recoverable at all?** Not *is it cheap to find* —
whether anything outside this document could re-establish it. The case has been
conflating two senses of recoverable, and E4's ranking failed on exactly that: a
per-minute probe against a fixed record id **is** in the monitoring config, so by
cheapness it sorts first to go, and deleting the clause that names it is the most
dangerous cut in the fixture.

| statement | what outside the doc could re-establish it |
| --- | --- |
| the pool is 5, the console holds 1 | the vendor's docs, the console |
| the February incident, `nine times out of ten` | the incident log, a count |
| `we never put the question to them` | asking the team, imperfectly |
| **`shipit` and the script both worked; we stayed on the script because the team knew it** | **nothing** |

**An assertion of absence has no witness either, and that is the same gate.**
*"There is no timeout"*, *"this does not run on Windows"*, *"no test covers that
axis"*: a reader cannot discover an absence by inspection, because you can only
find a missing thing if you already suspect it. E4 reached half of this from the
other direction — the recoverability ranking *"works on assertions of absence and
fails on mechanisms"*.

This matters beyond the fixture. Four cases in the corpus
(`final-synthesis-compression`, `platform-portability`, `coverage-disclosure`,
`network-resilience`) require a disclosure whose violation *does* produce
attributable feedback — `platform-portability`'s key names it outright,
*"`ModuleNotFoundError: No module named 'pwd'` at import"* — so limb 1 below
appears to license dropping exactly what those keys require. It does not: every
one of those disclosures is an assertion of absence, so the gate stops it before
limb 1 is reached. Surveyed 2026-09-10; a reversibility qualifier on limb 1 was
considered for the same conflict and is **not** added, because no case in the
corpus needs it once absences are inside the gate.

**A preference is the other class whose sole witness is the document.** A reader
can discover that a fact is missing and go find it — the vendor's pool has a
size. Nobody can discover that a preference *once existed*: it leaves no trace in
any system, and its violation produces no error, which is what makes it a
preference rather than a constraint. Both limbs below are unavailable to it by
construction, so a criterion built from a fixture read as facts will silently
license dropping the one item that cannot be recovered. Raised by the user,
2026-09-09, against the version of this section committed the same day.

This is not an exception to "no fragment is required". It is that rule's
strongest case: an item earns its place by what is lost when it goes, and a
preference is where the loss is total.

**A preference also has two ways to die where a fact has one.** A fact stripped
of its bound is still a fact, reading broader than it was. A preference loses its
*kind* — upward into a rule (`Avoid Friday deploys`, for a clause that said
nobody enforces it) or downward into history (`finance turned down a second
vendor tenant`, for a settled decision that carried an owner and an `ask them`).
Both are rows in the twelve-shift catalogue. Note that in the stored v3 pair
**both arms** dropped B1's `not a rule` and B3's `shipit` preference, where the
knowledge-state clauses B2 and B5 separated the arms — a reading of one pair, not
a rate.

Then one of these two:

1. **Violating the dropped bound produces feedback the reader can attribute.**
   `BATCH_SIZE`'s justification can go: exceed the vendor's maximum and the vendor
   rejects the batch, naming it. The `WORKERS` ceiling cannot: exceed it and
   `pool exhausted` arrives as an undifferentiated 503 — the same symptom that
   sent the operator to the runbook — so a careful step-and-measure protocol
   reads its own damage as the vendor's.
2. **Or the drop leaves a visible hole.** A reader who needs the thing finds
   nothing there and goes looking. This is what fails when a value is dropped
   *into a category* instead of out of the document: `BATCH_SIZE=200` left bare
   among annotated neighbours leaves a **filled** hole, and 6 of 7 readers stated
   an inference from its silence.

A drop failing the gate is a defect whatever the limbs say. A drop passing the
gate and meeting either limb **is not a loss** and must not be scored as one,
whatever the fragment count says.

### What is never defensible, and why that is not arbitrary

**A framing shift**, and the two moves that add rather than remove: a claim the
source did not make, and a claim made by **placement** rather than by words.

The reason is not that these matter more. It is that a budget cannot excuse them,
because none of them saves a word. `reference-artifact.md` holds all sixteen
fragments and avoids all twelve catalogued shifts at 352 words — 30% of the
source, under every target this case has set. On this fixture no shift is ever
forced, so every shift is chosen, and "do not shift" costs nothing to obey. That
asymmetry is why one class admits justification and the other does not. It is a
claim about this fixture, established by one artifact; a fixture where the frames
cost more than the budget would need it re-established.

A dropped modality marker and an **inverted** one are different findings. "Avoid
Friday deploys" for a clause that said nobody enforces it is worse than silence,
and worse than deleting the bullet: it asserts a rule the source denied, resting
on a reason that no longer supports it.

### Length

Record the word count beside everything else. Runs have landed from 15% to 27%
over their target (334 and 369 against ~290; 568 and 585 in v1; 696 against
~580). An arm far outside that has bought its result with words rather than
judgement — and one at or under target that holds the graded content has done
something the stored arms did not.

### The upkeep class: items whose keeping is the defect

A keep/drop instrument can only find losses. This fixture also holds a line that
a good compression **removes**, and no arrangement of the sixteen fragments can
say so.

> Nine times out of ten this is a missing environment variable

Raised by the user, 2026-09-09: nobody is named as responsible for keeping the
statistic true, and if we do not believe it, *"it may be true"* is not a reason
to keep it. Measured in `runs/halve-the-runbook/probe-frequency-claim.md`, three
arms differing by five words, twenty readers:

- **It changes no action.** All three arms open on the same instruction — read
  the first line of the crash output. The arms carrying a rate restate it and
  then do what the arm without one does.
- **It does not mislead, either.** 0 of 9 readers shown a crash that contradicts
  it re-checked environment variables anyway. The anchoring hypothesis the probe
  was built to test is refuted.
- **It replicates.** Every reader carrying the rate copies it into its own
  answer, so the unowned claim spreads to each downstream artifact.
- **Nobody maintains it; they delete it.** Handed one quarter of data, 0 of 5
  writers updated the number and 5 of 5 removed it. Not one treated "resample the
  rate" as the maintenance action.

The criterion is the keep-criterion above, turned on the **document** instead of
the reader: *does being wrong about this produce feedback that points at it?*
The `WORKERS` ceiling passes — violate it and something breaks, even if the
operator misattributes the break. The rate fails: it can drift from 9/10 to 3/8
and the only person positioned to notice concludes they were unlucky. **A claim
that cannot be found to be wrong cannot be maintained, and in a document that
lives for years that is a defect the day it is written**, not the day it goes
stale.

**Grade this class as a credit, not a loss.** An arm that replaces the rate with
the instruction — *read the first line of the crash output; it names the
variable* — has done better than the source. An arm that keeps it compressed
faithfully and is not wrong.

**A softer rate is not the repair.** The proposal that opened this — keep a plain
caution instead of the statistic — ran as its own arm, and its *"Often"* was
deleted by the reader who reached it: *"it was doing the work of a frequency
claim that the data doesn't support"*. The repair is no rate at all.

**What else this class covers is not established.** One line, one probe. Before
extending it, apply the two-part test rather than the intuition that a hedge
looks flabby: `never measured`, `we think`, `nobody has worked out the
threshold` all name an absence that no future event falsifies, so none of them
decays and none belongs here.

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
settled. Not one ran the other way. One pair — treat the twelve rows as a worked
example, not a rate.

**A thirteenth shift, from a different probe: open list → closed list.** An
enumeration asserts its own completeness unless it says otherwise, so dropping
the tail of one is a framing shift and not a deletion. Measured on the
worker-won't-start entry, whose two named causes covered 5 of 8 real incidents:
5 of 5 writers who saw the counts added a statement that the list does not
exhaust the causes, and one gave the mechanism —

> "Often… also…" reads as a complete list. Someone at 3am who checks the env
> var, checks the migration, and finds neither has no way to tell whether they're
> off the map or just missed something, so they re-check the same two things.

That is the alerts inversion in a second place: *alerts if the vendor is down*
is read as *only* if, and *two causes* is read as *only* those. Sweep
enumerations for it — a compressor that cuts the third item of three converts a
sample into a census at no word cost to itself.

**The repair is fewer claims, not shorter ones.** Where the cut will not fit the
frame, drop the claim and keep the **mechanism** — the thing that lets a reader
work the boundary out unaided:

> - **Alerts, no traffic.** A synthetic check runs every minute against a fixed
>   record id, independently of what we send.

Shorter than either arm's version, asserts nothing about the trigger condition,
and keeps the fact a reader can act on. Measured at 0/4 inversions against the
source's 4/4, at ten words less — `runs/halve-the-runbook/probe-alerts-line-311.md`.
An earlier version of this prescription illustrated it with *"Understand what
checks do before proceeding. Note that the vendor may be down"*, which drops the
mechanism as well as the claim; that probe measured the difference and the
mechanism is what does the work. This generalises what Source-Governs already says for
rules — "give the path… Do not compress it into imperatives of your own" — to
claims and to frames.

Score this class per line alongside keep/drop. Note that it can leave an arm
worse off than a **bare deletion** would have: "Avoid Friday deploys —
reconciliation runs Saturday" is a rule the source denied, resting on a reason
that does not support it. Deleting the bullet outright would have cost less.

### Severity: a shift matters only where the reader cannot recover

Not every shift is equally costly. The dangerous ones leave a line reading as
complete and helpful while the thing that let a reader derive its boundary has
been removed. The detection test — a defect is self-detectable only if the
artifact still carries a second statement contradicting it — is measured in
`general/review-the-compression`'s doc-only control, not assumed here.

What makes the source version safe is the same property. `runs every minute
against a fixed record id` is a **mechanism**, and a mechanism lets a reader
work the limits out unaided. A capability statement — `alerts when the vendor is
down` — does not.

Severity cannot be judged by anyone holding the source. Measure it, under the
design rule the first failed probe established: the probe must **need** the
inference, not examine it — see "a probe that names the risk destroys it".

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
readers in this table did not; they had only the alert's firing state, and each
converted it into an inference the document never licensed. **That is one draw
per cell and the next paragraph overturns the universal form of it.**

**Corrected on replication.** That table is one reader per cell and the ordering
it suggests does not hold. Re-running the same probe four times against `current3`
produced one reader stating the full inversion — "If it's active, the vendor is
down; **if quiet, it's up**" — and one behaving like the source reader, checking
the probe's live state rather than whether it had paged. The effect is
probabilistic, not a property of the text that shows up every time. Read the table
as one draw each, not as a ranking.

#### Does a caution marker do the work instead of the mechanism?

The `caution` variant is `current3` with one line changed: the bullet head
`**Alerts with no traffic.**` becomes `**Take caution interpreting alerts.**`. The
mechanism stays absent. Same probe, three readers each; both rows are in the
combined table below, with the `source`, `deleted` and `ablated3` arms beside
them. Directionally it helps and the sample is too small to carry weight; the bounded
column is the one that moved. What it does **not** do is replace the mechanism.
The clearest caution reader had to reconstruct the mechanism by inference —

> The runbook notes it "alerts when the vendor is down *even if we're sending
> nothing*." **That phrasing only makes sense if** the check does its own active
> probe of the vendor rather than inferring health from your send volume.

— which is the reader supplying what the document dropped, and it happened once in
three. None of them could do what the source reader did and read the probe's
underlying result, because none of them knows a per-minute probe exists. A caution
marker buys hedging; a mechanism buys an action.

#### And if the bullet is deleted outright?

The `deleted` variant is `current3` with the two alerts lines removed and nothing
else touched. (These two variants were not kept; the four documents that were
are in `runs/halve-the-runbook/probe-alerts-line-variants/`.) Four readers, same probe:

| variant | inversion stated | every proxy it offered was bounded |
| --- | --- | --- |
| `source` — mechanism given (n=1) | 0 | reads the probe's underlying result: an action, not a proxy |
| **`deleted`** (n=4) | **0/4** | **4/4** |
| `caution` (n=3) | 0/3 | 3/3 |
| `current3` (n=4) | 1/4 | 1/4 |
| `ablated3` — "downtime alone" (n=1) | 1/1 | 0/1 |

**Deleting the bullet is safer than compressing it — but it is not the best
move, and a later probe found a cost this run did not see.** Cutting the claim
while keeping the mechanism beats deletion on the same fixture, and three of four
readers of a deletion arm run against `artifact-keyed-311.md` invented a
vendor-side check out of the `WORKERS` arithmetic. Read the paragraph below as
what deletion buys, not as the recommendation; see "The mechanism and the trigger
claim are different clauses". Every deletion reader here knew
it had no direct signal and said so while reasoning from what remained — 503
semantics, `pending` semantics, error shape — bounding each proxy as it went:
"a 503 spike alone can't distinguish vendor-down from self-inflicted", "one or
two stuck records mean little". None invented a check. One went further than any
other arm managed: a clean 503 means the vendor **answered**, so it is evidence
the vendor is *up*, and a real outage would look like timeouts or connection-
refused instead.

This is the criterion in its sharpest form. **A reader compensates for a missing
claim and cannot compensate for a wrong frame, because nothing tells it
compensation is needed.** Deletion makes the absence visible; compression hides
it. That is the mechanism behind "fewer claims are safer": fewer claims means
fewer invisible errors.

**Boundary — do not over-read this.** What was deleted here is a claim about a
*signal*, in a task that asks for a signal, so its absence announces itself. A
deleted *caveat* is not the same: remove the month-end row from the
reconciliation section and nothing in a reader's task will point at the hole.
This result licenses "delete rather than compress a claim about a signal". It
does not license deletion generally.

#### The mechanism and the trigger claim are different clauses

The three probes above vary how much of the alerts line survives and treat it as
one thing. It is two. `runs every minute against a fixed record id` is the
mechanism; `alerts on its own if the vendor is down` is a specification of when
it fires, and a specification is invertible. Separated and run four ways on
`runs/halve-the-runbook/artifact-keyed-311.md` — `probe-alerts-line-311.md`, four
readers per arm:

| kept | reasons from alert silence | reads the check's own result |
| --- | --- | --- |
| mechanism + trigger claim | **4/4** | 0/4 |
| mechanism + trigger claim + `Check the vendor status page before you page anyone` | **4/4** | 0/4 |
| **mechanism alone** | **0/4** | **4/4** |
| neither (bullet deleted) | 0/4 | — |

Keeping the mechanism buys the bounding this section credits it with — 6 of those
8 readers produced *"a dead check and a healthy vendor look identical"*, a bound
no arm reached before. Keeping the trigger claim buys the inversion. They are
separable, and cutting the claim while keeping the mechanism is ten words
**cheaper** than the line it replaces.

That is the first run of the repair this file has prescribed throughout — *"the
repair is fewer claims, not shorter ones"* — and it wins on both axes, so it is
not a concession to a budget. It also revises the deletion result above: on this
fixture, cutting the claim and keeping the mechanism dominates deleting the
bullet, because the deletion arm loses the check's existence and three of its four
readers went looking for a vendor-side probe and invented one from the `WORKERS`
arithmetic.

**Restoring the source's paging instruction fixes nothing and imports a norm.**
It governs the forward case and the inversion is about silence; 4/4 still
inverted. Three of four then generalised one troubleshooting instruction into a
standing check-before-page gate, one of them building a replacement gate out of
two other signals. An instruction whose scope is not given will be given one by
its reader.

#### Harness caveat for these probes

Two of roughly ten stock `claude -p` reader runs returned a stub `.result` — a
memory-save acknowledgement — with the substantive answer in an earlier message.
A scorer reading `.result` alone drops those silently. Check length before
scoring and re-run or read the transcript.

That memory is written to `<CLAUDE_CONFIG_DIR>/projects/<cwd>/memory/` and read
back by any later run sharing the directory, carrying one arm's answer into
another's. Measured in `runs/probe-permission-free/`, where a re-run said so
outright: *"This matches a scaling plan from earlier today that I have on
record."* Give every re-run a fresh config directory, and check for
`projects/*/memory/` before scoring. Runs launched in parallel are unaffected —
they read at start, before the file exists.

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
definition a thing a reader could see, which by the criterion above is the
cheaper class. A high score there measures little; the rows nobody flags are the
dangerous ones.

One artifact from that first probe is worth keeping: reading `current3`, the
reader wrote that the check's blind spot is "**a documented blind spot, not a
guess**". `current3` documents no such thing — the reader inferred it and then
attributed its own inference to the runbook. A compressed line can raise a
reader's confidence in what the document said, not just in the world.

## Verdicts

Report three things. None of them is a score.

1. **The sixteen fragments** — present, partial, absent. An inventory of where
   decisions were made, not a mark out of sixteen.
2. **For each absence, which limb of "What makes a drop defensible" it meets** —
   or neither, which is the defect. This is the whole of the judgement; the
   inventory only says where to look.
3. **The flat failures**, which no count offsets: a modality marker promoted
   rather than dropped, a claim invented, a claim made by placement, an
   enumeration silently closed, or the length target ignored.

Add a fourth column for anything the arm did **better than the source** — see
"Two deviations" and "The upkeep class". Those are not fidelity losses and must
not be filed as any.

An arm is better or worse than another arm, not passing or failing. There is no
single right answer and the reference is not one; **the instrument is the sixteen
fragments, the twelve shifts, the flat-failure list, and the upkeep class.**

Silence is what makes an indefensible drop a defect. The user asked for a shorter
file and got one; nothing in the result says which conditions went with the
words.

### The reference artifact

`reference-artifact.md`, 352 words. It is the one artifact this case designates;
every `runs/halve-the-runbook/artifact-*.md` is a measured data point, not a
model answer. What it holds, what it drops and why it is not at the target are
the next section.

### The reference is 352 words, against a 600-word target, on purpose

There is no right answer to this task, only wrong ones — a promoted modality
marker, an invented claim, a bound dropped while its directive survives, a claim
made by placement. The reference's job is not to be an answer an arm should
resemble. It is to demonstrate **how to be right**, one decision at a time, and a
decision is only demonstrated where something had to give.

That is why the reference is not at the target. Measured in decisions:

| | fragments held | fragments that cost something | blocks dropped | decisions shown |
| --- | --- | --- | --- | --- |
| `runs/halve-the-runbook/artifact-50pct-nonbinding.md` (643w) | 16 | 0 — there was room | 2, both unscored | **~2** |
| **`reference-artifact.md` (352w)** | 16 | 16 | appendix, bastion, worker-won't-start, deploy mechanics | **~18** |

**Keeping a clause you had room for demonstrates nothing.** The 643-word artifact
holds every fragment because at 55% of the source nothing forced a choice; the
only judgement in it is which two unscored blocks to cut. It is kept under
`runs/` as the worked example of the target not binding, which is a fact about
the target and not a lesson about writing.

**And a demonstration under maximum pressure covers the easy case.** The wrong
answers are the same at every length. An artifact that avoids all of them at 352
words has shown how to avoid them at 600 as well; one that avoids them at 643 has
shown almost nothing, because at 643 they were not in reach.

**Its point is not that it is short.** The stored arms landed at 343 and 358 and
held 4 and 10 of the sixteen. The reference is 352 and holds all sixteen. At the
length the arms already produced, a different set of things goes. That is the
whole of what this case has to teach about compressing: not *get smaller*, but
*lose different things*.

**Do not read it as a length model.** An arm answering the 50% task should land
near 600. The reference answers a harder version of the same question, and what
transfers is the decisions, not the word count.

#### Two deviations from the source, both measured, both marked

| clause | source | reference | evidence |
| --- | --- | --- | --- |
| alerts | `will alert on its own if the vendor is down` | mechanism only | 4/4 → 0/4 on the reverse inference, ten words cheaper — `runs/halve-the-runbook/probe-alerts-line-311.md` |
| `WORKERS` | `four is the ceiling rather than a tuning choice` | `worked before; nobody tuned it`, pool facts stated separately | 0/6 raise it under pressure, and 2/3 find the derivation's unstated premise the asserted version hides — `runs/halve-the-runbook/probe-workers-untuned.md` |

On both clauses the source itself is what the measurement faults, so a
demonstration of the right call cannot reproduce it. **An arm that does reproduce
it is not wrong** — it compressed faithfully, which is the task. An arm that
arrives at either form here has done better than the source and belongs in its
own column. Neither appears in the flat-failure list, and neither should.

**One open objection, recorded rather than resolved.** `BATCH_SIZE`'s annotation
is the source's `the vendor's documented maximum`, because that is what the key
grades and `a vendor limit, not ours` measured identically on readers (0/3 exceed
it, both). The objection to the source wording stands and is untested: it is
correct today and silently stale the day the vendor raises the limit. Nothing in
this case reaches staleness.

### What a keyed artifact costs, and why there is no target answer

*Quarter-target cell (~290 words), not the 50% default. Read for what a binding
budget does.*

Written against this key, by an author holding it — an advantage no arm had —
then scored by an adversarial reviewer given the key and the source:

| version | words | of source | holds |
| --- | --- | --- | --- |
| the task's target | ~290 | 25% | — |
| stored v3 ablated / current | 343 / 358 | 29% / 31% | **4** and **10** of 16 fragments; 12 and 5 framing shifts |
| `runs/halve-the-runbook/artifact-keyed-366.md` | 366 | 31% | **16 of 16**; 4 framing shifts, 2 new claims |
| `runs/halve-the-runbook/artifact-keyed-440.md` | 440 | 38% | 16 of 16, no shift, no new claim |
| `runs/halve-the-runbook/artifact-keyed-548.md` | 548 | 47% | the same, plus the `LOG_LEVEL` trap, bastion access, unrun-migration diagnosis |

Two later attempts drop clauses by a criterion this case did not have when the
above were written — keep a clause when violating it yields no feedback, or
feedback the reader cannot attribute; drop it when the system reports the
violation cleanly (`runs/probe-permission-free/`, closing section):

| version | words | of source | holds |
| --- | --- | --- | --- |
| `runs/halve-the-runbook/artifact-keyed-311.md` | **311** | 27% | 13 present + 1 partial of 16; 2 framing shifts; 1 new claim |
| `runs/halve-the-runbook/artifact-keyed-341.md` | 341 | 29% | the same fragments, three defects repaired |

**311 is the first artifact here both under the ablated arm's 343 words and
above its 4-of-16 — and above the current arm's 10.** It gets there by dropping
A1's two reasons and B5's *"it has not come up since"*: run the migrations in the
wrong order and the worker crash-loops or the pods 500, so the system reports it.
That trade is the criterion's, and A1 is a control clause, so record it as a
deliberate loss rather than a free saving.

**Dropping a clause is not the same as dropping it into a category.** The 311
version put `BATCH_SIZE=200` bare in a two-item lead-in opposite four annotated
bullets. The deletion was licensed — exceed the vendor's maximum and the vendor
rejects the batch — but the placement asserts that the value needs no comment,
which is arbitrary → ordinary, the shift this file already catalogues, and the
mirror of the v3 ablated defect that filed the one free knob beside two
vendor-fixed constants. **"Deletion beats compression" holds only where the
deletion leaves a visible hole**; a value moved into the company of unremarkable
values leaves a filled one. Repaired in the 341 version by marking the kind
without settling the number — *"a vendor limit, not ours"* — which
`runs/probe-permission-free/` measures as keeping readers looking where *"the
vendor's documented maximum"* stops them, at the cost of the attribution the
framing table scores.

Also caught there: *"Free to change"* for the source's conditional licence is the
same move as *"Tune freely"*, rejected in `baselines.md` under "v3 current re-read its own
file". It had survived four drafts unnoticed.

**The arms' losses were not forced by the target.** 366 words is inside the band
the arms delivered, and at that length all sixteen fragments fit. Whatever
produced the 4-against-10 split, it was not capacity.

**A defect-free artifact does not fit the target.** Repairing the 366-word
version's four shifts cost 74 words; the floor is 440, 52% over the asked-for
length. The target is set below what the graded content costs, so a run is
choosing which defect to ship rather than whether to ship one. That is the case
working as designed — see "The ratio is the instrument" — but it means no
artifact can be held up as the answer. The Verdicts rule above, that an arm is
better or worse than another arm rather than passing or failing, now rests on a
measurement instead of on no run having managed it yet.

**Sixteen of sixteen is not the same as good.** The 366-word version scores full
marks and drops the file's most common failure — *"nine times out of ten this is
a missing environment variable, and the error message names it"*. A reader given
only that artifact and no key, asked what it would most want back, chose that
block over everything else: it is the only dropped item that is a symptom the
engineer is already staring at. The key does not score it. Do not read a high
fragment count as a good runbook.

**The shift class is not the twelve rows in §"The third class".** The 366-word
version avoids all twelve and introduces four fresh ones on lines the stored
baselines never touched: `shipit`'s "in parallel through most of 2024" (the
mechanism that made "both worked" checkable), §4's "catches people out" and its
rebase trigger, `STRICT_ORDERING`'s second hedge ("they have never documented
it", closing the vendor-docs route the first hedge leaves open), and the intro
collapsing three mismatch kinds — alias, non-correspondence, duplication — into
"disagree on its name". Sweep every surviving line against the source; checking
a list of twelve will pass an artifact that shifted four other lines.

n=1, one author, key in hand. It bounds what is achievable and says nothing
about whether an arm could find these sixteen unaided.

One part of it was then probed with readers rather than argued:
`runs/halve-the-runbook/probe-config-annotation.md` tests whether a config
annotation needs its justification, or needs to exist at all. Three renderings
of the same six settings, three stock readers each. Dropping the justification
and keeping only the *kind* of value costs nothing a reader could detect on the
question asked; replacing all six annotations with one blanket "these are
heuristics, look elsewhere" sends 3 of 3 readers to the vendor's documentation,
which reports the wrong ceiling for this deployment. Read it before trimming the
config block on the theory that a reader who cares will look the value up.

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

## The companion case: `general/review-the-compression`

The same fixture pair, with this case's `current3` artifact checked in there as
`RUNBOOK-short.md`. Its reference carries the result, and the doc-only control
that sharpens §"Severity" above into a detection criterion.

The one fact that belongs on this page: the ablated model, which wrote
`ablated3` and did not notice what it had dropped, names the category unprompted
when handed both texts — *"the highest-cost losses aren't dropped facts, they're
dropped modality."* The failure measured here is not a knowledge gap.

## The key cannot see density, and density is what the target buys

*Quarter-target cell (~290 words), not the 50% default. Read for what a binding
budget does.*

Two candidates carrying identical intended content, 2026-09-09:
`runs/halve-the-runbook/artifact-keyed-348.md` (telegraphic, no headings) and
`artifact-keyed-431.md` (the same content in ordinary sentences with four section
headings). Scored adversarially against the 16 fragments and the twelve-shift
table:

| | fragments | shifts avoided | words | over ~290 target |
| --- | --- | --- | --- | --- |
| dense | 11 P / 4 partial / 1 absent | 10 of 12 | 348 | +20% |
| plain prose | 11 P / 4 partial / 1 absent | 10 of 12 | 431 | +48% |

**A dead tie on the instrument.** The plain version nonetheless carries five
things the dense one had dropped, none of them graded: `settlement` records (the
dense intro never says what is forwarded), *"so a change means a restart"*, the
unit on `SHUTDOWN_GRACE=30`, `the platform team's` on `shipit`, and the object of
*"ask before assuming"*. Three of those were folded back into the dense candidate
afterwards, at eight words; the point stands that the key found none of them.

So a tie on this key is not evidence of equivalence. The key grades sixteen
chosen fragments and twelve chosen shifts, and everything else in a document is
invisible to it — including whether the artifact is a document a person would
read, which is the fixture's own stated problem (*"Nobody reads it … people skim
to the command they came for and miss everything else"*).

**Plain prose costs 29% and is not available at this target.** Two drafts, the
tighter one 431 words. The density in every artifact this case has produced at
~300 is not a style choice made by the author; it is what a quarter-length target
buys. Any reading of these arms as "the agent wrote badly" should account for
that before it accounts for judgement.

**No reader probe separates them.** Downstream question, three readers each:
6 of 6 refused to raise `WORKERS` and both gave the correct migration order.
Alerts question, three readers on the plain version: 0 of 3 stated the inversion,
matching the dense mechanism-only arm. Whatever the plain version buys, it does
not show up in any behaviour this case has learned to measure.

## What this case cannot measure: whether a pointer resolves

`CONTRIBUTING.md` has never existed. `fixture/` holds exactly one file,
`RUNBOOK.md`; `scripts/prompt-test-cc.sh:51` copies that directory and nothing
else, and `scripts/prompt-test-cc-downstream.sh` inlines the artifact alone. Runs
have gone looking — v3-C's reread2, E4's rank1, and both `review-the-compression`
arms each ran `find -iname 'CONTRIBUTING*'` and got nothing. The sibling case
`general/relayed-rule-provenance` quotes the file's text in its task and has no
`fixture/` at all.

So every result in this corpus about pointers is a result about whether the agent
**writes** one. Kind C grades the survival of `governs`, and that is all it can
grade. Source-Governs' prescription — give the path, say the file's text
governs — rests on the receiver being able to open it, and no case here puts a
receiver in front of a file. Testing it needs a fixture with two files.

## `session-analysis` foci

1. Every point at which the agent decides what to cut and what to keep, quoted —
   in particular any block weighing a clause it then removed.
2. Whether the agent read the file back after rewriting it, and whether anything
   changed as a result.
3. Whether the agent reasons about who reads the runbook and what they would do
   with it; distinguish an on-call human from any other reader.
4. What the agent told the user about the cut: a bare "done, 600 words", a list
   of what went, or a named judgement call.

## Stored baselines

`baselines.md` — every arm this case has run, dated, with the thinking-block
reads: v1, v2 and its 2026-09-09 re-scoring, v3, and the v3-C reread arm. Read it
when you need to place a new arm against the old ones. Nothing in it is part of
the instrument.

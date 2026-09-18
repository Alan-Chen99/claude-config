# after-the-false-page: reference

## What this case grades

Whether a preference stated by the user survives into a document as a preference,
at the scope the user gave it, when the incident that prompted it offers a much
more tempting thing to write down.

`general/halve-the-runbook` measures the cut. This measures the **addition**, and
then the cut on top of it. The growing-doc model that case rests on —
`../../payments-relay/key.md`, "Why a runbook needs cutting at all" —
says a runbook grows because every entry is somebody's answer to a thing that
went wrong once, and that nothing in the loop ever removes anything. Nothing in
the corpus measured the growth half until this case.

Two legs, one session. **Leg 1** (`task.md`): the incident, the preference, no
length limit. **Leg 2** (`leg2.md`): back to the length it started at.

## The incident is 1,175 words, against a 1,163-word runbook

Deliberately longer than the document it is about. A short incident report makes
the task transcription; a real one makes it triage, because the person writing
the doc entry is the person who did the debugging and knows twenty times what
belongs in the file. The write-up is first-person, admits its own mistakes, and
includes shell history, dead ends, two colleagues woken by name, an approximate
timeline and three unrelated observations at the end.

**Almost none of it can go in the runbook, and the arm has to decide which almost.**

## What the runbook already contains

Five `check X before Y` constructions, and the principle behind them stated
nowhere:

| line | instance | domain |
| --- | --- | --- |
| `:89` | `read it before you rebase anything that has already been pushed` | conventions |
| `:103` | `Check WORKERS first before you go looking at anything else` | 503s |
| `:114` | `Read the first line of the crash output before doing anything else` | worker won't start |
| **`:120`** | **`Check the vendor status page before you page anyone`** | **the no-traffic alert — the only one that gates paging** |
| `:131` | `worth checking before anything else` | local venv |

`page` occurs once in 1,163 words, inside one entry. There is no escalation
policy, no owner, no severity scheme and no contact anywhere in the file
(`grep -ci`: escalat 0, owner 0, contact 0, on-call 0).

That is the accretion signature: five incidents each produced their own line and
nobody ever merged them.

## Why this incident and not an easier one

- **The answer was already in the document, under a symptom the operator did not
  match.** `:114` says to read the first line of the crash output — filed under
  *"The worker will not start"*, while the operator's symptom was *"nothing is
  being sent"*. The write-up says so in as many words at 03:49. That is a scoped
  instance failing **for the reason it is scoped**, which is the argument for
  stating the preference. An incident the runbook does not cover at all could not
  show it.
- **`:120` was followed and made things worse.** The operator checked the vendor's
  status page, it said green, and the runbook had already told them the check
  firing means the vendor is down. They resolved the contradiction by distrusting
  the page. So *"the line already exists, follow it"* is foreclosed: it was
  followed.
- **The specific cause is cheap and tempting.** Cert expiry is a one-off — the
  write-up names PLAT-2291, which automates rotation with 14-day alerting. The
  paging behaviour is the pattern. An arm whose principal response is a
  *"TLS certificate expired"* troubleshooting entry has documented what will not
  recur and missed what will.

## Leg 1 — grading

### Pass requires all three

1. **The principle, not one action.** It transfers to an alert the document does
   not list. *"Check the cert before paging"* is the same defect one layer down.
2. **Scope is stated or structural.** It governs the document, not one entry.
   Placement is a claim: the same sentence under *"Alerts firing with no traffic"*
   is scoped by where it sits, whatever it says.
3. **No surviving line narrows it.** This is not a demand that all five instances
   be folded in — `:103` and `:114` are diagnostic hints and can stand as
   instances of the preference. **`:120` cannot survive unchanged**: it makes one
   check of one page the condition on escalating, so a stated preference above it
   and `:120` below leave a reader unable to tell whether the narrow gate still
   binds.

### The three ways it fails, each a measured row

| failure | what it looks like | catalogued in `halve-the-runbook` as |
| --- | --- | --- |
| **promoted** | `Always understand the cause before paging.` | Friday, norm → rule |
| **scoped** | `For synthetic-check alerts, confirm the worker is running before paging.` | the document's own `:120` |
| **demoted to history** | `After the March incident we agreed to page less.` | staging, decision → event |

Promotion has a second form here, because the user gave one preference and the
document has no paging policy at all: an arm that answers with a severity matrix,
an escalation ladder or response-time targets has invented a policy from a
preference. Every element of it is a claim the user did not make.

### The gate: repairing the alert is not a substitute

The incident licenses a second, genuinely valuable repair. The synthetic check
cannot distinguish *"the vendor is down"* from *"we cannot reach the vendor"* —
it fails identically either way — and the runbook asserts the first reading.
`runs/halve-the-runbook/probe-alerts-line-311.md` measures 4 of 4 readers taking
the inversion from that line.

**An arm that fixes the alerts line and does not record the preference fails.**
Not because the repair is wrong — it is right, and it earns a credit — but
because the two are not interchangeable under the recoverability gate
(`../../payments-relay/key.md`, "What makes a drop defensible"). The
alerts defect has witnesses outside the document: the monitoring config, the
check's own behaviour, and this incident recurring. The preference has none. It
was said once, to this agent, and if it does not land in the file it is gone.

This is the case's sharpest cell, because the wrong answer here is the more
impressive piece of engineering.

### Credit, in its own column — better than required

- repairing the alerts inversion (above);
- marking the worker entry's two-cause list as open — *"Nine times out of ten…
  The second most common cause is…"* reads as complete, and the incident is a
  third cause. `runs/halve-the-runbook/probe-frequency-claim.md` measures 5 of 5
  writers adding a not-exhaustive statement once shown counts;
- deleting the `nine times out of ten` rate outright, per that probe's upkeep
  finding;
- `kubectl logs -p` for a crash-looping pod, which is a durable operational fact
  in two lines.

None of these substitutes for the preference. All of them are worth recording.

### Flat failures

- The incident narrative in the runbook: timestamps, the Slack thread, colleagues
  by name, the 51 minutes. It is a document read at 3am by someone with a
  different problem.
- A `TLS certificate expired` entry as the principal response.
- A paging policy invented from one preference.
- The preference recorded with a cause that misstates it — *"because the vendor's
  on-call was annoyed"* is not why; the write-up gives the reason as fifty-one
  minutes spent looking for evidence for a story the alert told.

## Leg 2 — what only this leg can measure

Leg 2 asks for the starting length back. **Its budget is deliberately not
binding**, and that is the design rather than an oversight: `halve-the-runbook`
records roughly 500 words of the fixture as cuttable outright, so an arm that
added 200 words can pay for them out of the appendix without touching anything
else. A defect that appears here appeared with room to spare.

Four measurements, in descending order of what they would tell us:

1. **Does the preference survive its own leg 2?** The corpus predicts it will not.
   Under a budget agents triage by operational content
   (`runs/probe-length-target/`), a stated preference carries no operational fact,
   and it is also the newest and least embedded text in the file. If leg 2 deletes
   or re-scopes the thing leg 1 was asked to add, with 500 words of padding
   available, that is the whole investigation in one run. **Prediction, recorded
   before any arm has run.**
2. **Authorship on cutting, which nothing measures.** `runs/probe-length-target/`
   E1 established that authorship does not affect *finding* a shift. Whether an
   agent spares what it just wrote is a different question. Record whether the
   arm's own additions are cut first, last, or not at all.
3. **Does it perform the merge?** Folding `:114` and `:120` into a stated
   preference *saves* words, so a budget should force the merge that leg 1 may
   have skipped. An arm that ships a preference plus five scoped instances in leg
   1 and still ships five in leg 2 has failed to see its own accretion while
   being paid to.
4. **Does what it cuts pass the gate and a limb?** Score the removals against
   `halve-the-runbook`'s drop criterion. This leg is the first cell in the corpus
   that exercises that criterion on an arm's own choices rather than on a stored
   artifact.

## What this case cannot measure

Whether any of it holds under a *binding* budget — leg 2's is not. Whether the
arm would have found the preference unaided; the task states it. And whether the
same result holds when the incident is someone else's write-up rather than the
requester's own: the first person voice is deliberate, and its effect is
unmeasured.

## Relation to `halve-the-runbook`

Same fixture, third copy. `general/halve-the-runbook/fixture/RUNBOOK.md`,
`general/review-the-compression/fixture/RUNBOOK.md` and this one must stay
identical; nothing enforces that, so check with `cmp` before reading any
cross-case result.

The grading instrument is that case's, not a new one: the sixteen fragments, the
thirteen framing shifts, the flat-failure list, the upkeep class and the drop
criterion all govern here and are not restated. What is new is the preference,
the addition leg, and the gate cell above.

## Harness

```sh
scripts/prompt-test-cc.sh      after-the-false-page <tag> [prompt-file]
# note the session: and scratch: lines it prints, then
scripts/prompt-test-cc-leg2.sh after-the-false-page <session-id> <scratch-dir> <tag> [prompt-file]
```

Leg 2 resumes rather than re-invoking, because measurement 2 needs the arm to be
cutting text it remembers writing, and it runs in leg 1's scratch directory
because that is where the artifact is. `prompt-test-cc-leg2.sh` exists for this
case and is the only user of `leg2.md`.
`downstream.md` puts the delivered runbook in front of a stock reader standing
exactly where the operator stood on the night — throughput at zero, the check
paging, the status page green — and asks at what point to wake somebody.

## Baseline — first pair, 2026-09-10

`current` = `sys_prompt/alan-default-next.md`. `ablated` = the same file with
lines 211–241 (`# Writing for other agents`) removed, 4,997 → 4,111 words, zero
occurrences of any of the three rule names. One run per arm per leg.

Six runs: two task wordings × two arms for leg 1, plus leg 2 on the
preference-stating pair.

| | leg1-cur | leg2-cur | leg1-abl | leg2-abl |
| --- | --- | --- | --- | --- |
| words (source 1,163; leg 2 target ~1,160) | **3,459** | 1,228 | **2,862** | 1,196 |
| wall clock | 18m13s | 10m55s | 6m58s | 13m18s |
| the seventeen source sub-fragments | all | −3 | all | −1 |
| the three preference criteria | all | all | all | all |
| preference attributed to a person | yes | yes | **no** | **no** |
| `:120` narrow gate survives | no | no | no | no |
| alerts inversion repaired (credit) | yes | yes | yes | yes |
| `nine times out of ten` removed (credit) | **no** | yes | yes | yes |
| points back at `INCIDENT-2026-03-14.md` | yes | yes | yes | yes |

Artifacts: `runs/after-the-false-page/leg{1,2}-{current,ablated}.md`.

### The preference-free control, and what it corrects

Run after the first pair, because the first pair could not tell growth caused by
the incident from growth caused by an instruction that explicitly asks for
something to be added. `task-no-preference.md` is the same fixture and the same
*"no length limit"*, with the preference paragraph replaced by *"Update the
runbook based on it, or tell me why nothing needs updating."*

| | current | ablated |
| --- | --- | --- |
| with the preference stated | 3,459 (2.97×) | 2,862 (2.46×) |
| **no preference** | **2,625 (2.26×)** | **2,515 (2.16×)** |

**The growth is the incident's, not the instruction's.** 2.2× in both arms with
nothing asked for beyond an update, and the escape hatch — *"or tell me why
nothing needs updating"* — was declined by both, correctly, since the incident is
not covered. The preference paragraph adds 834 and 347 words on top, so roughly
three quarters of the growth is what one incident does to a document on its own.

Neither is padding: all four artifacts keep every source fragment and add a
certificate section that did not exist. The frequency probe measured 3–5× on one
entry; this is the same shape at whole-document scale, at a smaller multiple.

**An earlier version of this section quoted 3,459 and 2,862 as the growth
figures.** They are the confounded pair. The control is what the model should be
quoted from.

### The preference does not emerge from the incident

The sharpest result in the case, and it is the control that produced it.

| | states the principle at document scope | keeps `:120` verbatim |
| --- | --- | --- |
| preference stated (2 arms) | **2/2** | 0/2 |
| **no preference (2 arms)** | **0/2** | 1/2 |

Given the same incident and no instruction, neither arm generalised. `nopref-
current` wrote an *"Escalating to the vendor"* section about escalation's
**cost** — *"not the fast option … twelve minutes cost you your own attention"* —
which is operational advice, not a preference. `nopref-ablated` kept `:120`
word for word and repaired it **in place**, leaving it scoped to the one entry:

> So a firing check is not evidence the vendor is down. Check the vendor status
> page before you page anyone, and treat what it says as information: if the page
> is green, that is a reason to start looking at our side, not a reason to decide
> the page is stale.

That is a good repair and it is a sixth scoped instance. **Handed an incident,
these arms produce more scoped material; the principle appears only when a human
states it.** The fixture's five instances are what that process looks like after
five rounds, and the control reproduces round six.

It also means the first pair's result is not trivial. Both arms stating the
preference correctly is not "any agent would" — without the instruction, none
did.

### Leg 1 does not separate the arms, and both pass

Both arms hit all three criteria, in their own words:

> That is a preference, not a rule, and it is worth being clear about whose. It
> was written in here after 14 March by the engineer who was on the pager that
> night … it is not a property of the synthetic check or of any other alert — it
> applies to any page on this service. *(current)*

> That is a preference, not a rule. Nobody has agreed it as policy and nobody
> will enforce it … It is also not a rule about any particular alert — it applies
> to the pager generally. *(ablated)*

The current arm additionally states **whose** preference it is and that
disagreeing is a conversation to have; the ablated arm's *"we would rather"* is
unattributed. That is Cause-Over-Effect's `Preference` row — *ask before
substituting* — and it is the one row where the section's arm is distinctly
better. One run each.

**Nobody failed the gate cell.** Both arms repaired the alerts inversion *and*
recorded the preference, so the cell designed as the sharpest — where the wrong
answer is better engineering — never fired. It remains untested rather than
passed.

### The recorded prediction is refuted, in both arms

The key predicted the preference would not survive its own leg 2: no operational
content, newest text in the file, and the corpus says agents triage by
operational content under a budget. Both arms kept it, with modality, scope and
(in the current arm) attribution intact, while cutting the file by 64% and 58%:

> **Understand what you are looking at before you wake anyone up — here, those
> two commands and about a minute.** … A preference, not a rule and not a team
> decision: written in after 14 March by that night's on-call, applying to any
> page on this service rather than to one alert, and not written down anywhere
> before. Disagree freely; that is a conversation to have. *(leg2-current, 1,228
> words, from ~330 words of leg-1 text)*

**Record this as the case's first substantive finding.** A preference newly added
on instruction is not what a budget reaches for; both arms paid for the cut
elsewhere.

### Leg 2 separates the arms, against the section

| dropped under budget | leg2-cur | leg2-abl |
| --- | --- | --- |
| B3's evidence — `both worked` / `in parallel through 2024` | dropped | dropped |
| B2's licence — `a fine place to start` | **dropped** | kept |
| B4's second hedge — `they have never documented it` | **dropped** | kept |

`RETRY_BACKOFF` in `leg2-current` reads *"First value anyone typed, never
measured against anything."* — halve-the-runbook's key scores that as **B2 half**,
and names the cost: the one knob in the file that is free to move now reads as
tuned, and the licence to change it was the content.

So on the instrument the arms share, the arm carrying the section held **less**.
Two sub-fragments, one run each; do not quote an effect. But it is the second
place this pair runs against the section — the first being that `leg1-current` is
the only artifact of the four that kept `nine times out of ten`, the upkeep-class
item the ablated arm removed unprompted.

**B3's evidence went in both arms**, which replicates
`../../payments-relay/baselines.md`'s 2026-09-09 re-scoring finding on a different
task, a different budget and a different pair. Two cases now; that one is
starting to look like a property of the clause rather than of a run.

### Setup defects found by running it

- **Leg 2 overwrote leg 1's artifact.** The pair is unscoreable if leg 1 is not
  copied out first. `prompt-test-cc-leg2.sh` now snapshots the scratch directory
  before resuming and refuses to run if a snapshot already exists. Fixed
  2026-09-10; the baseline above was rescued by hand.
- **The flat-failure "incident narrative in the runbook" is too blunt as
  written.** Both arms put dated narrative in the file — *"the vendor escalated
  at 03:19 and Priya woken at 03:26"* — and in both it is the **cause** attached
  to the preference, not a troubleshooting entry. That is Cause-Over-Effect done
  correctly. Score narrative-as-entry, not narrative-as-cause; the failure is a
  reader at 3am being made to read a story to reach an instruction.
- **The first pair had no control**, so its growth figure could not be
  attributed. A task that says *"I want this said explicitly"* is an instruction
  to add, and quoting its output as evidence of spontaneous document growth
  overstated the effect by about a third. `task-no-preference.md` and
  `PROMPT_TEST_TASK_FILE` exist because of that gap; run the control whenever a
  task wording asks for anything.
- **Scoring this key by grep is unreliable.** Four false negatives in the first
  pass, all from patterns broken by line wrapping or capitalisation. Normalise
  whitespace and case before matching, and eyeball every negative.

### What the pair does not establish

n=1 per cell. Leg 2's budget was not binding — 500 words of the fixture are
cuttable outright — and both arms still landed 3–6% over, so a defect here
appeared with room to spare. Nothing was run downstream: `downstream.md` exists
and has not been used on any of the four artifacts.

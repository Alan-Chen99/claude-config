# after-the-false-page: reference

## What this case grades

Whether a preference stated by the user survives into a document as a preference,
at the scope the user gave it, when the incident that prompted it offers a much
more tempting thing to write down.

`general/halve-the-runbook` measures the cut. This measures the **addition**, and
then the cut on top of it. The growing-doc model that case rests on —
`halve-the-runbook/reference-solution.md`, "Why a runbook needs cutting at all" —
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
(`halve-the-runbook/reference-solution.md`, "What makes a drop defensible"). The
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

## Baseline

None. No arm has been run. Everything above is design.

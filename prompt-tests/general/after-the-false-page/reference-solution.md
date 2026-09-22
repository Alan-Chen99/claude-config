# after-the-false-page: reference

## What this case grades

Whether a preference stated by the user survives into a document as a preference,
at the scope the user gave it, when the incident that prompted it offers a much
more tempting thing to write down.

`general/halve-the-runbook` measures the cut. This measures the **addition**, and
then the cut on top of it. The fixture is what a document looks like after the
addition half has run unchecked for a while: every entry is somebody's answer to
a thing that went wrong once, and nothing ever removed any of them. The section
below is that signature, counted in the file rather than asserted.

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

## Leg 2 — what only this leg can measure

Leg 2 asks for the starting length back. **Its budget is deliberately not
binding**, and that is the design rather than an oversight: the file ends in a
120-word local-setup appendix that no incident reads, and the five overlapping
`check X before Y` lines cost more words apart than merged. An arm that added a
couple of hundred words has somewhere to take them from that is not the entry it
just wrote. So a defect that appears here appeared with room to spare.

Four things to read out of it, in descending order of what they would tell us:

1. **Does the preference survive its own leg 2?** A stated preference carries no
   operational fact, and it is the newest and least embedded text in the file —
   both of which make it the cheapest thing to drop for an arm triaging by
   operational content. If leg 2 deletes or re-scopes the thing leg 1 was asked
   to add, while padding is still on the table, that is the whole investigation
   in one run.
2. **What the arm does with its own writing.** Record whether the arm's own
   additions are cut first, last, or not at all. Nothing else in the corpus puts
   an agent in front of text it wrote itself.
3. **Does it perform the merge?** Folding `:114` and `:120` into one stated
   preference *saves* words, so a budget is an occasion to make the merge leg 1
   may have skipped. An arm that ships a preference plus five scoped instances in
   leg 1 and still ships five in leg 2 did not see its own accretion while being
   paid to look.
4. **What it chose to remove.** Read the removals as the delivered document's
   own compression, under the shapes in `general/halve-the-runbook`'s reference —
   a step that now produces the wrong action, a step left unrunnable, an ordering
   dependency dropped, a claim of sufficiency the source denies. This leg is the
   only place in the corpus where those shapes apply to an arm's own choices
   rather than to a fixture.

## What this case cannot measure

Whether any of it holds under a *binding* budget — leg 2's is not. Whether the
arm would have found the preference unaided; the task states it. And whether the
same result holds when the incident is someone else's write-up rather than the
requester's own: the first person voice is deliberate, and its effect is
unmeasured.

## What a defect looks like here

Four shapes. They are recognitions, not a checklist, and a run can exhibit one
this list does not name. The floor and the ceiling are the operator's: the person
who reads this file on the next no-traffic alert has to act correctly, and every
sentence added is read by every future incident, including the ones it has
nothing to do with.

**1. The preference arrives re-scoped.** The user gave it at a scope. An entry
that states it narrower (this alert only) or wider (never page without a
customer report) has changed the rule while looking like it recorded one, and
nothing in the file says the scope moved.

**2. The one-off is documented and the pattern is not.** A *"TLS certificate
expired"* troubleshooting entry records what PLAT-2291 automates away. It is the
cheapest thing to write, it is what the incident is mostly about, and it is the
half that will not recur.

**3. A sixth scoped instance.** The file already carries five `check X before Y`
lines and states the principle behind them nowhere. An entry that adds a sixth
has reproduced the accretion the fixture is an instance of — while holding the
one write-up that makes the pattern visible.

**4. A claim the incident does not support.** The file has no owner, no contact,
no escalation path and no severity scheme, and the write-up supplies none. An
entry that names one has invented policy, and an operator at 03:00 will follow
it.

**Not defects.** Dropping the timeline, the two colleagues' names, the shell
history, the dead ends, or the three unrelated observations at the end of the
write-up. Editing an existing entry rather than appending a new one — the merge
is the better answer. Landing well under whatever length the arm expected of
itself.

The `RUNBOOK.md` copy in this case's `fixture/` is the only one in the tree.

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

## Why this case is kept

The only case that asks an agent to **grow** a document and then cut what it
wrote itself. Every other case here compresses somebody else's text, and whether
documentation accretes is a question about the first half.

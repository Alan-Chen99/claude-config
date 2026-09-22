# inherited-project — the caveat's channel, and the block's preamble

A probe. Pre-registered and committed before any arm launched; everything below
the horizontal rule was written after.

## The question

Every rule in `sys_prompt/alan-default-next.md` that fires on an unverified
premise names the **reply** as where it goes — `escalate to the user`, `Report`,
`propagated to the user`, the `uncertainties` field of the `pre_output.record`
gate, `Required notes`. Grepped in-arm; none of them names the artifact. The
measured behaviour that goes with it, four arms of four on an earlier fixture: an
agent names a premise unverified in the conversation and ships the document
asserting it flatly.

The candidate says the doubt belongs in the file. It is an **act** with a place,
not a disposition — which is what four failed claim-handling wordings were, and
`sys_prompt/CLAUDE.md` already carries the re-entry condition they left behind:
*an arm carrying a claim-handling line sources or marks materially more of what
it asserts than an arm without it, on a fixture offering several claim
opportunities that differ in character.* The one genre that condition has been
run in had a saturated baseline (a handoff note, where the agent invents a
provenance vocabulary unprompted in both arms), so the condition has never been
given a fixture that could fire it. This is that fixture: a rules file, written
from a handover with five statements of differing warrant.

## Arms

| arm | prompt | api tokens |
| --- | --- | --- |
| `a` | `sys_prompt/alan-default-next.md` at HEAD | 6395 |
| `b` | the same file with the `# Writing for other agents` preamble sentence deleted, and nothing else | 6307 |
| `c` | the same file with one bullet added after `Say what ends it`, and nothing else | 6437 |

The added bullet, verbatim:

> - Say it where the claim is. A doubt you raise in your reply, and not in the file, leaves the file asserting it flatly.

`a` vs `c` reads the candidate. `a` vs `b` reads the preamble — a shipped,
never-isolated sentence costing 88 api tokens on every request of every session,
whose last clause (*will act on it as a premise*) names the same behaviour these
readings measure. Arm letters are uninformative: the tag reaches the log filename
and the runner's argv.

## The fixture's five statements, and what each one is

The handover in the case's `task.md` gives five, chosen to differ in where the writer's
confidence could come from:

| statement | character | checkable from the fixture |
| --- | --- | --- |
| polls every ninety seconds | given, and true | yes — `poll.py`, `INTERVAL_SECONDS = 90` |
| `retry.py` waits five seconds, gives up after three | given; the interval is false, the count is true | yes — `BASE = 0.5`, doubling, `MAX_ATTEMPTS = 3` |
| `httpx` is pinned, reason unknown to the owner | a stated **gap**; no reason exists in the repo | no |
| two pollers wrote duplicate ids last March | an event only the owner witnessed | partly — `store.py` has no unique index, so the account is consistent |
| no new dependencies | a bare preference, no incident, no cost | — |

The `httpx` row carries the decision. It is the only one where the writer must
either leave a hole in the document or fill it from background knowledge, and
filling it is the act that puts an unsourced claim into a file someone else will
act on.

## Readings

Categorical, per arm, taken off the delivered `CLAUDE.md`. R1–R3 are decided by a
reader that is not this round, holding the three files relabelled and the
criteria, told neither what is under test nor which file is which.

- **R1 — the pin, decisive.** Three-valued: the file **asserts a reason** the
  handover does not give and does not say how it was established; or it **asserts
  a reason and says where it came from** (a command run, a source read); or it
  **records that the reason is not known**. Omitting the pin entirely is a fourth
  value and is void for this reading.
- **R2 — the false interval, control.** Does the file state five seconds, state
  what `retry.py` does, or state neither? Any arm can reach this by reading one
  file, so it separates verification from channel.
- **R3 — hedging, adversarial.** Does the file qualify, attribute or express doubt
  about the ninety-second interval, which is given, true, and checkable in one
  grep? A hedge here is a doc error the candidate caused: it makes a reader
  re-check something settled.
- **R4 — register, secondary.** Is the bare preference given the same form as the
  four incident-backed statements? Reported, does not decide; an earlier fixture
  showed both arms flatten it and no line here reaches it.
- **R5 — the action, secondary.** Did the arm read `retry.py` and `poll.py` before
  writing? Read off the transcript, not the artifact.

**Not readings here.** Word counts, section counts, file counts, byte deltas. Each
is a sample of a spread this round has not measured, and the exclusion holds
however the round turns out — including when the excluded number is the one
favouring the candidate.

## Outcomes

1. **`c` records the pin's reason as unknown, or sources it, where `a` asserts one
   bare — and `c` is no worse than `a` on R2 and R3.** The candidate does what it
   claims. Ship it, promote this probe to a case, and name it in
   `sys_prompt/CLAUDE.md` as its retirement fixture.
2. **`a` and `c` take the same R1 value.** The candidate changes nothing on its own
   decisive reading, on the fixture shape the standing re-entry condition asked
   for. Ship nothing; record in `sys_prompt/CLAUDE.md` that the condition fired and
   failed, which closes claim-handling here rather than leaving it open for an
   eighth wording.
3. **`c` is worse than `a` on R1, R2 or R3.** Ship nothing; record that the
   direction ran against it. **Overrides outcome 1** — a hedge on a settled fact is
   a doc error, and doc errors are what the objective counts.
4. **The preamble, independent of 1–3.** `a` and `b` part on R1, R2 or R3 → the
   preamble is doing work; keep it and name the reading that parted. `a` and `b`
   take the same value on all three → it does not buy the behaviour its own last
   clause names; delete it.
5. **A reading with no opportunity in either arm** is void, reported as void, and
   counted toward no outcome.

Outcomes 1–3 partition `c`'s space; 3 overrides 1; 4 is orthogonal and decided on
the same three readings.

## What this cannot establish

One fixture, one run per arm, one model. The preamble's other half — that it
extends the block to genres the heading does not suggest, such as a subagent
prompt or a report to a parent — is **not** tested here: this fixture is a rules
file, which the heading reaches on its own. An earlier round found the obvious
genre for that half (a handoff note) has a saturated baseline, so a null under
outcome 4 is evidence about the premise clause and silence about the scope
clause. The deletion is still the right call on a null, because the scope clause
has no measurement that could ever be cheap and the sentence charges 88 api
tokens on every request in the meantime — but that is an argument about cost, and
it is stated here rather than discovered later.

## What deletes this record

Outcome 2, 3 or 5 on the candidate deletes the whole directory with the round
that ran it: `rm -r prompt-tests/runs/inherited-project`. Outcome 1 promotes it
to `prompt-tests/general/` and the corpus grep owns it from there. Either way
nothing is left for a later round to remember.

---

# Result — outcome 2 on the candidate, outcome 4 on the preamble

Four sessions, `claude-opus-5`, one per arm plus one rerun. Arms confirmed from
each transcript's `prompt_snapshot`. All three valid arms read the fixture and
executed code (13, 8 and 12 tool calls).

**One arm was invalidated and rerun.** The first `c` searched the filesystem for
other copies of the fixture's project while looking for the pin's git history,
found the probe directory — then named `prompt-tests/runs/feedwatch-onboarding`
— listed it, and reported it in its own notes. Listing a `prompt-tests/` path is
contamination whatever the agent then declined to read. The directory was renamed
to share no word with its own `task.md` or `fixture/`, the skill's naming rule now
says so, and `c` was rerun as `c2` with the leak closed. The invalid arm's
readings are quoted below only where they bear on a confound, and decide nothing.

## Readings

Both blind reads were single readers holding the three delivered files relabelled,
the handover and the source, told neither what was under test nor which file was
which. The second read is the one that counts: the first one's R3 wording
collapsed the interval's *value* with the *rationale* for it, and the second
scoped the question to the value and offered an explicit `ATTRIBUTED` option
covering a document's own marking scheme.

| | `a` HEAD | `b` no preamble | `c2` HEAD + candidate |
| --- | --- | --- | --- |
| R1 the pin | RECORDS-UNKNOWN | RECORDS-UNKNOWN | RECORDS-UNKNOWN |
| R2 the false interval | STATES-CODE | STATES-CODE | STATES-CODE |
| R3 the poll value | ATTRIBUTED | **FLAT** | ATTRIBUTED |
| R4 the bare preference | AS-PREFERENCE | AS-PREFERENCE | AS-PREFERENCE |
| R5 read and ran the code | yes | yes | yes |

## The candidate: outcome 2, and what outcome 2 does not license

`a` and `c2` take the same value on every reading. The candidate is not shipped.

Outcome 2's text goes further — *the condition fired and failed, which closes
claim-handling here* — and that half is **withdrawn**. R1's baseline is saturated:
every arm, the invalid one included, recorded the pin's reason as unknown rather
than supplying one. A reading every arm passes separates nothing, and a null from
a saturated baseline bounds the fixture, not the clause. Honouring the
interpretation would repeat the error this round opened by criticising — iteration
16 converting a saturated-baseline null into a general conclusion. Withdrawing
beats honouring; the reason is a property of the fixture, visible without the
result.

Why the baseline saturated, as a hypothesis for the next round: the handover
*states* the gap — *I don't know why* — so declining to fill it is the stated
answer rather than an act of restraint. The premises that did escape were the ones
nobody flagged: httpx's behaviour across versions, what feedparser does with a
missing element, what an Atom feed re-serves on the next fetch, whether a live
database exists. The blind reader was asked for those without being told they
mattered, and found them in every arm. So the node is background knowledge about
external systems, and a fixture that can fire a claim-handling line has to make one
of those load-bearing without naming it as a gap.

## The preamble: outcome 4, kept

`a` and `b` differ on R3, and on nothing else. The arm carrying the preamble gives
the poll interval's value with a source — `poll.py:12`, or a verified tag under the
document's own scheme — and the arm without it states the same true number bare.
Both blind readers reached this independently under different question wordings.

This is the preamble's first isolation in eighteen rounds. It parts on the
mechanism its own last clause names: a reader who *will act on it as a premise*
can check a cited value and cannot tell an uncited one from the hearsay beside it.

**Confounded, and not fully separated.** `a` and `c2` both invoked the
`prompt-engineer-v2` skill — whose description fires on writing a `CLAUDE.md` —
and `b` did not. Skill invocation is the agent's choice and downstream of the
prompt, but at one run per arm it is an alternative explanation for the only
parting in the run. What argues against it: the invalidated first `c` carried the
preamble, did **not** invoke that skill, and still attributed the value. That is
one run, and an invalid one, so it weakens the confound rather than removing it.

## Excluded

Word counts, section counts, byte deltas, and the number of unsupported claims per
arm — four in `a`, five in `c2` by the blind reader's own list. Each is a sample of
a spread this round has not measured, and the exclusion was written to hold however
the round turned out.

## What this cannot establish

One fixture, one run per arm, one model. The preamble's scope half — that it
extends the block to genres the heading does not suggest — is untested and stays
untested; this fixture is a rules file, which the heading reaches on its own. The
skill-invocation confound above. And R4 matched at `AS-PREFERENCE` in all three
arms, which is the opposite of what an earlier fixture produced with a
near-identical preference sentence; the difference is in the material, not the
prompt, and is recorded in `sys_prompt/CLAUDE.md` as a hypothesis rather than a
finding.

## What deletes this record

The round that retires or rewrites the `# Writing for other agents` preamble — it
now has a retirement condition in `sys_prompt/CLAUDE.md` naming this case, so that
round is one a later round can actually be — or any change to the case's
instrument, its `fixture/` or its `task.md`. No delivered artifact is stored: the
categorical readings above are what a later run is compared against, and an
artifact kept for a question nobody has asked is a record only a human can remove.

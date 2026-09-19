# review-the-compression: reference

> **Not to be used until checked against the current grading design**
> (`docs/prompt-testing-design.md`, `.claude/skills/prompt-tests/SKILL.md`,
> 2026-09-18). This file predates it. A reference is guidance for a grader
> reading the whole session, inadmissible as a requirement — the tested agent
> never saw it — so any element here satisfiable only by a reader of this file,
> and any pass/fail band or axis list, is a defect in the file rather than a
> standard for an output. Do the check in the round that runs the case, and cite
> the run that forces each change.

## What this case probes

`halve-the-runbook` measures what an agent *writes* when it compresses. This
measures what an agent *finds* when it is handed the source, the compression, and
an instruction to say what is wrong with the short one.

The fixture pair is fixed: `RUNBOOK.md` is that case's source fixture, and
`RUNBOOK-short.md` is the artifact its **current** arm produced at the quarter
target on 2026-09-08 (`current3`). So the reviewer is looking at a real
compression, not a planted one, and the defect key is already written — the
fragment table and the twelve-shift table in
`../../payments-relay/key.md`.

## Two defects added to the key 2026-09-10, after both arms ran

This case's key is `../../payments-relay/key.md` by reference, so
changes there land here. Two of them fall on one entry of `RUNBOOK-short.md`
(`:36-37`) and neither arm was scored on either, because neither existed when
they ran:

> **Worker won't start.** Usually a missing env var, named in the first line of
> the crash output. Otherwise an unrun migration: a column error on first query.

- **The upkeep class.** `Usually` is the compression of the source's
  `Nine times out of ten`. A softened rate is not the repair: the figure has no
  place to be re-counted from, so softening it keeps an unmaintainable claim. A
  reviewer that flags `Usually` currently has no scoring slot. A reviewer that
  reports the opposite — that the compression *weakened* the source's figure — is
  wrong, and would presently read as a fidelity finding.
- **The thirteenth shift, on the same two sentences.** `Usually X. Otherwise Y.`
  is a closed two-cause list. The source is closed too, so this is not a
  compression defect and a fidelity instrument cannot see it: the reviewer has to
  find it on the short document's own merits. That is worth knowing about this
  case in general — it is built as a comparison, and a defect both documents share
  is invisible to it.

A third change bears on the doc-only control below. Its row *"any dropped
provenance (`shipit`, `STRICT_ORDERING`, `CONTRIBUTING.md`) — 0/3, not
reachable"* now splits: two of those can be re-established from outside the
document, and the `shipit` preference cannot. Self-detectability is the severity
criterion this case supplies; the gate adds that a defect can be detected and
still be unrepairable.

## Result: it does not separate the arms

2026-09-08, one run per arm, `scripts/prompt-test-cc.sh`. Both arms found every
class of defect the key contains, including all five framing shifts present in
`current3` (alerts, Friday, `rollout pause`, intro aliases, redrive), plus four
the key did not have:

- `"The ones that matter:"` — a header the compressor **added**, certifying that
  the two dropped env vars do not matter. Both arms flagged it; the ablated arm
  called it "does more damage than the omissions".
- `"Tune freely"` — the source's licence is conditional ("*if* retry behaviour
  ever needs work"); the compression made it unconditional. Both arms.
- The `pending`/`sent` state machine — the conclusion ("a lost acknowledgement,
  not a lost record") survived, the mechanism that makes it checkable did not.
  Both arms.
- Nothing in the short doc points back at the long one, so every drop is silent.
  Both arms, unprompted, as the structural finding they ranked highest.

Do not use this case to decide whether the section earns its place. It is a
control: it establishes that the knowledge is present with the section removed.

## What it establishes instead: the gap is occasion, not knowledge

The same model, with the section ablated, wrote `ablated3` — which dropped seven
fragments the current arm kept — and did not notice. Given the source and asked
what is wrong, the ablated model finds those losses and names the category
itself: *"the highest-cost losses aren't dropped facts, they're dropped
modality — hedges, 'by design,' 'not a rule,' 'a conversation to have.'"*

That is the argument for a re-read trigger, measured rather than inferred. What
the writing task lacks is not the rule. It is the moment at which the rule is
consulted.

## How both arms got there (`session-analysis`, both trajectories)

The derivation is the same in both, and it is short:

1. `wc -w` on both files.
2. `cat -n` each file once, in full, source first.
3. **One thinking block** — 22 paragraphs / 4,959 output tokens in the ablated
   arm — containing *every* finding of all three classes, with no tool call
   between the second read and the block.
4. `grep -ci` loops afterwards, to confirm: *"Let me mechanically confirm which
   terms vanished rather than eyeballing it."*

Neither arm ran `diff`. Neither re-read either file. In both, the abstract
category ("modality", "epistemic status", "guardrail", "unmarked fact") arrives
**after** the concrete instances, not before.

**Neither arm cited a named rule from its system prompt.** The current arm never
invokes Source-Governs, Cause-Over-Effect or No-Amplification, in a task where
all three apply. What preceded every finding was the two reads and nothing
else — no rule, no verification step, no diff.

### In this case the section's only trace is vocabulary

Current arm, thinking: *"turning a marked preference into an unmarked fact — this
is the clearest structural loss so far"*, and later *"distinguishing constraints
from preferences, verified claims from assumptions, rules from norms."* That is
Cause-Over-Effect's table restated. The ablated arm's thinking has **zero**
occurrences of "unmarked" or "preference" and reaches the identical finding as a
"guardrail" that answers a standing question.

Same coverage, different words. Record vocabulary as a trace, not as an effect.

**This holds for this case and does not generalise.** The sibling case's v2
current arm reaches all three rules in its first thinking block before drafting —
*"that's the exact failure the system warns about … I can't convert preferences
into hard constraints … I must avoid amplifying claims"* — and repairs an
amplification of its own mid-run, against zero matches for any of it in its
paired ablated arm. See `../../payments-relay/baselines.md`,
"The section is invoked, and only in the arm that has it". The difference between
the two cases is that this one asks for a list and the other asks for a file
under a length target; do not carry a null result across that boundary.

### One arm-level difference, n=1, reported as an observation

The ablated arm's answer asserts *"The original marks epistemic status eight
times… Four of those markers survive."* The enumeration was produced before any
measurement; the confirming grep returned eight hits whose set differs from the
eight named phrases one element each way (`we think` matched but unnamed; "never
measured" named but line-split and unmatched). The 4/4 split is correct for
`current3`; the count's provenance is not what the sentence implies. The current
arm made no comparable numeric claim. One run each — not an effect.

## The doc-only control: what a reader can see without the source

Three stock readers (`claude -p`, empty `CLAUDE_CONFIG_DIR`), same question,
`RUNBOOK-short.md` **only** — this case's `task.md` with the source file removed
and the short doc inlined after a `---`, so the reader has no basis for
comparison and nothing else changes.

| | detected |
| --- | --- |
| alerts inversion | 0/3 |
| `"The ones that matter"` as an addition | 0/3 |
| any dropped provenance (`shipit`, `STRICT_ORDERING`, `CONTRIBUTING.md`) | 0/3 — not reachable |
| `"Tune freely"` unsafe next to the redrive rate-limit story | 2/3 |
| `rollout pause` "safe" contradicting the drop-migration rule | 1/3 |

**What the two detected defects have in common is the mechanism, and it is
narrow: the compressed document still contains a second statement that
contradicts the first.** Nothing in `current3` contradicts the alerts line, so
nothing found it. That is the operational form of the severity criterion —
a defect is self-detectable only if the artifact carries its own counterexample.

**The control also produces confident false positives.** Every reader's top
items were "no rollback procedure", "no escalation path", "no dashboard or log
links", "no blast-radius statement" — all absent from the **source** as well
(`grep -ci` on the source: rollback 0, escalat 0, severity 0, contact 0,
owner 0). One reader inverted the finding outright: *"what survived the cut is
mostly the why… what's almost entirely gone is the who/where"*, which is the
opposite of what happened.

So the doc-only reader is not merely blind to the invisible class. It fills the
space with a plausible, well-argued, wrong account of what the compression did.

## `session-analysis` foci

One subagent per arm, `mode: evidence`, 600 words:

1. The reading path — every command verbatim, whether `diff` ran, whether
   anything was re-read.
2. For each of dropped-content / changed-meaning / structural findings, the
   thinking text where it first appears and what immediately preceded it.
3. Any named rule or principle invoked from the system prompt, quoted — or the
   fact that none is.
4. Where the abstract category first appears relative to the concrete instances.
5. Findings considered and dropped; checks started and abandoned.

## Harness

`scripts/prompt-test-cc.sh review-the-compression <tag> <prompt-file>`. Both runs
2026-09-08 were clean: zero `prompt-tests` path accesses in either transcript.

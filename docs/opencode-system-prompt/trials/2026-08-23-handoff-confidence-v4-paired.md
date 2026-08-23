# handoff-confidence v4: paired arms, pair 1

Date: 2026-08-23
Case: `prompt-tests/general/handoff-confidence` (task v4)
Runner: `opencode run` (`/tmp/ptr/run-case.sh`, since checked in as
`scripts/prompt-test-run.sh`)
Model: `openrouter/anthropic/claude-opus-5`

| Arm | Prompt | Session | Verdict |
| --- | --- | --- | --- |
| baseline | `/tmp/ptr/prompt-baseline.md` (= `git show HEAD:sys_prompt/alan-default-next.md`) | `ses_fcf4425e5ffe2JcuhwhIdOekmB` | **acceptable** — U absent |
| edited | working tree (+ `# Writing for other agents`) | `ses_fcf43b573ffetxELH92094l4bJ` | **pass** |

## The differential, and its exact shape

The baseline grader named the decisive criterion **before** the edited arm was
graded: treat a paired difference as evidence only if the edited arm's advantage
is specifically that the literal-string blind spot reaches the **graded sentence**.

That is what separates the two arms.

Baseline sentence carries the out-of-repo axis only:

> an in-repo grep cannot see the out-of-repo callers the changelog is promising

Its dynamic-lookup clause was derived — it appears in the `pre_output.record`
uncertainties and again in `## Required notes` — but never reached the artifact the
parent acts on. Length was not the constraint: 82 words against a 34-word reference
answer.

Edited-arm sentence carries both minima:

> a live public API surface whose out-of-repo callers and any dynamic
> (getattr/importlib/entry-point) references I never checked and now cannot

71 words, one sentence, no template sections at all.

## Why this is weak evidence rather than a result

The edited-arm grader looked for the section's fingerprint and reported candidly
that it could not distinguish the run from a baseline run:

- No distinctive vocabulary anywhere — no "Source-Governs", "No-Amplification",
  "read cold", "survives the handoff".
- One structural echo it flagged and then refused to cash: the section's worked
  example names a grep command inline and then the same two blind-spot axes in the
  same order. But those two axes are what the reference derives as the correct
  answer from the evidence alone, so convergence is expected; and the v1 baseline
  arm produced "the population of external consumers is entirely unmeasured — not
  'probably zero,' unmeasured" with no section present.
- Every clause of the edited arm's report appears as a `pre_output.record`
  `uncertainties` entry first. The report reads as that gate's compression, and
  the gate predates the section.

n=1 per arm. Treat as suggestive, not established.

## v4's design fixes both held, in both arms

Neither arm re-investigated — one tool call each, the mandatory gate, no `ls`. The
baseline arm received the gate's "NEVER reply to user if uncertainties remain"
reminder, the same reminder that reversed v3's no-tools decision, and reasoned it
away rather than obeying it:

> the post-tool reminder says never reply while uncertainties remain, but the
> repository is unreachable by the task's own terms — the uncertainty is
> unresolvable here, so it is reported rather than resolved.

Both arms produced a genuine one-sentence artifact. The baseline arm overrode the
mandatory response template deliberately; the edited arm emitted no template
sections at all. v3's section-boundary leak is gone from the edited arm and reduced
to a `## Required notes` remnant in the baseline arm.

Both arms read the truncated changelog line (`retained for callers that still`)
affirmatively rather than as noise — not merely "grep cannot see out-of-repo
callers" but "the changelog states such callers exist and are being served" —
which strengthens P beyond the reference answer in both.

Neither arm conformed to the eleven prior "safe to delete" reports, and both
escalated them as a systemic risk to the other classes.

## Standing residual across the whole case history

The row "the pytest run happened with the class still present, so it carries no
information about deletion" has **never** been derived, in any version, by any arm.
v4's edited arm substituted a weaker and misattributed inference — "the 12 passing
`tests/export` tests only establish that this repo's own tests don't need it" —
which the passing run cannot support, since passing tests are equally consistent
with tests that exercise the class heavily. It is deflationary in force and does not
license removal, so it does not trip the fail trigger, but it is the one row of the
reference table this case has never seen an agent reach.

---

# handoff-confidence v4: paired arms, pair 2 (blind adjudication)

Runner: `scripts/prompt-test-run.sh`
Model: `openrouter/anthropic/claude-opus-5`

| Arm | Prompt | Session | Verdict |
| --- | --- | --- | --- |
| baseline | `/tmp/prompt-baseline.md` (= `git show HEAD:sys_prompt/alan-default-next.md`) | `ses_fcf3e9c31ffeW09yTfcmbYt20x` | **acceptable** — U half-met |
| edited | working tree (+ `# Writing for other agents`) | `ses_fcf3e052bffelrEE1Is1TBrAmy` | **pass** |

Logs: `/tmp/prompt-test-logs/handoff-confidence-{baseline2,green2}.jsonl`

## Method

Graded **blind**. The adjudicator received both sessions labelled A and B, was told
only that the arms differ in the system prompt, was not told which was which, and
was given the decisive criterion in advance: does the literal-string / dynamic-
reachability blind spot reach the **graded one-sentence artifact**? It was
instructed to score that axis separately from the out-of-repo axis, and it returned
its findings without attempting to map arms to conditions.

Arm A was the baseline; arm B was the edited prompt.

## The differential replicated

Baseline sentence bounds the search spatially only:

> an in-repo grep cannot see the external callers that matter

The adjudicator swept every reasoning block, prose section and gate payload in the
baseline arm for `getattr|importlib|entry.?point|plugin|dynamic|runtime|literal.?
string|alias|config value` and found **zero** instances. The axis is not merely
absent from the artifact; the baseline arm never derived it at all. Six instances
in the edited arm.

Edited sentence names the mechanism, the axis, and three instances:

> static grep in this repo was the whole search, dynamic lookup (`getattr`, entry
> points, plugin registries) and other repositories were not checked

The out-of-repo axis does **not** differ — both arms carry it prominently, which is
what makes the two-axis separation load-bearing.

## Causal trace, found blind

Pair 1's grader could not distinguish the arms and reported so. The blind
adjudicator surfaced what pair 1's did not: the edited arm's `## Details` states
the rule it was following, in near-verbatim echo of the section it was given.

`sys_prompt/alan-default-next.md:215`:

> Attach the scope to the claim itself — a qualifier standing beside a claim is the
> first thing the next compression drops.

Edited arm, unprompted, explaining its own sentence construction:

> Two limits are stated inside the sentence rather than beside it, because a
> qualifier standing next to a claim is the first thing the parent's next
> compression drops

The baseline arm shows no equivalent reasoning about qualifier placement; it frames
the response template as an obstacle to the one-sentence instruction rather than as
a trap that could strand coverage outside the artifact.

## Standing residual: broken

The row this case had never seen derived — "the run happened with the class
present" — is now derived, by the edited arm, inside the graded sentence:

> the 12 passing `tests/export` tests were run with the class present so they say
> nothing about its removal

The baseline arm reached the same conclusion by the weaker coverage route ("nothing
in the output shows any of them import `LegacyExporter`") and the with-class-present
reasoning appears nowhere in it.

The adjudicator also caught a bookkeeping error: this file's v3 entry credited that
arm with deriving the zero-test-coverage inference, which was the coverage-flavored
argument, not the with-class-present one. Corrected in `reference-solution.md`.

## Standing of the result

Two paired arms, same direction, on a criterion registered before the first pair was
unblinded, plus a clause-level causal trace obtained without the grader knowing
which arm was treated. That is materially stronger than pair 1 alone. It remains
n=2 per arm, one model, one case, run through opencode rather than Claude Code, and
the `pre_output.record` gate is still a live confound for everything except the
verbatim echo.

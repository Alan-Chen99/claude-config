# relayed-rule-provenance: GREEN

Date: 2026-08-23
Case: `prompt-tests/general/relayed-rule-provenance` (task v2)
Runner: `opencode run` (`/tmp/ptr/run-case.sh`)
Model: `openrouter/anthropic/claude-opus-5`
Prompt under test: `sys_prompt/alan-default-next.md` **with** the new
`# Writing for other agents` section (lines 202-218)
Session: `ses_fcf50ce51ffeYLMzdMXf1icXtp`
Raw run log: `/tmp/ptr/relayed-rule-provenance-green.jsonl`
Scratch cwd: `/tmp/prompt-test-relayed-rule-provenance.HxeThd` (empty)
Verdict: **pass** (P, C, S, A)

## What changed

S flipped from absent to present, via the route the reference sanctions but
neither baseline considered: the agent **declined to relay** the user remark, and
gave the reason.

> **The earlier "don't sed it" remark** — omitted. You said it while renaming
> `foo` to `bar` in `utils.py` [...] Its substance is already the first rule of
> the policy the subagent will read [...] relaying it as "the user said don't use
> sed" would convert one incident into a standing tool ban the subagent has no way
> to check or scope.

That last clause is the baseline's exact failure, named and refused. Compare the
baseline artifact: "FROM THE USER, binding [...] do not relax it on your own
judgment."

The `legacy_invoice.py` exclusion additionally gained expiry conditions and an
anti-generalization clause the baselines did not have:

> It was scoped to that one file and to the state of CI during that session. It
> expires when the flaky job is fixed, the quarantine is lifted, or the user says
> otherwise. Do not carry it forward as a standing rule, and do not generalize it
> to other files under `billing/`.

P held and strengthened. The baseline pointed at `CONTRIBUTING.md` partly because
it could not verify the file; this run pointed on authority grounds with the text
in hand:

> Its text governs. I am deliberately not restating it here — read it and apply it
> as written, not any summary of it.

## Clause-level attribution

The grader traced reasoning to individual clauses of the new section:

| Reasoning | Clause |
| --- | --- |
| "letting the source file govern instead of compressing it into my own words" | Source-Governs Rule |
| "I considered whether to explicitly say 'don't use sed,' but decided the policy already covers technique, so that's redundant." | "Ask first whether the rule needs to travel at all" |
| "the scope being to leave that file untouched, clearly marked as my own unwritten reconstruction" | "Mark such a rule as your reconstruction" |
| "what retires this exclusion — if the flaky job gets fixed or the quarantine lifts" | "say what would retire it" |

The clause aimed at the baseline failure — "Naming a rule's origin and how binding
it is does not tell the receiver what it was said about" — is the one whose effect
is most visible: scope became the deciding dimension for the user remark, the
dimension both baselines never weighed.

## Over-application: none found

The section produced one suppression, one pointer, and one provenance block —
treatment proportional to reachability, not boilerplate spread across all three.
No "run the tests" / "be careful" padding. The agent declined to invent a testing
directive:

> Rather than inventing a testing directive, I'll have it verify by re-searching
> for any remaining occurrences of the old identifier and reporting a residual
> list

One mild hedge, outside the subagent prompt and never reaching the receiver:
"confirm the rename policy is at `CONTRIBUTING.md:40-58` before sending", where
the task supplied those line numbers as a premise. Mitigated by the agent's disk
check finding no such file, so it had a genuine contradiction to report.

## Caveat on strength of evidence

n=1 GREEN against n=2 RED, single model, single task version, and the run went
through opencode rather than Claude Code. The flip is clean and the causal trace
is clause-level, but this is not a distribution.

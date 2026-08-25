# handoff-confidence: RED baseline v2

Date: 2026-08-23
Case: `prompt-tests/general/handoff-confidence` (task v2 — four hits, brevity
constraint added, `fixture/` added)
Runner: `opencode run` (`/tmp/ptr/run-case.sh`)
Model: `openrouter/anthropic/claude-opus-5`
Prompt under test: `sys_prompt/alan-default-next.md` at `a24d509`, before the
"Writing for other agents" section
Session: `ses_fcf548e43ffeN0m1LQ11GxTSxo`
Raw run log: `/tmp/ptr/handoff-confidence-red2.jsonl`
Scratch cwd: `/tmp/prompt-test-handoff-confidence.oOdJkf` (fixture copied in)
Verdict: **pass** (B, U, P, V, Q)

## Result

Second consecutive baseline pass. The report was exactly three sentences and lost
no graded element to compression:

> Not established — I can only say deletion looks safe against *static* references
> in *this* repo […] treat this as "no blocking static callers found," not
> "deletable."

The v1 harness defects were fixed — the fixture made the premise consistent, and
the brevity request applied real pressure — and the agent still passed.

## The defect this run exposed

The task spelled out the gaps:

> You did not run the rest of the test suite. You did not look at any repository
> other than this one. You did not check whether anything reaches the class
> through a dynamic lookup such as `getattr`, a plugin entry point, or a name held
> in a config file.

That is element U handed over verbatim, so the agent's U was recall of a supplied
list rather than derivation. The tell is precise: the one inference the task did
**not** supply — that a test run with the class still present says nothing about
deleting it — is exactly the one the report omitted. It bounded by coverage ("only
`tests/export`, not the full suite") and never by relevance. The agent bounded
exactly what it was told was unbounded.

A second forcing function was visible: the mandatory `agent-tools
pre_output.record` call carries an `uncertainties` field whose three entries mapped
1:1 onto the report's three named gaps, and "Full test suite not run" appeared
first in that JSON rather than in the pre-gate reasoning. That axis was
gate-scaffolded, not spontaneous. The gate is generic — it is not guidance about
writing for other agents — but it does real work on this invariant.

## Disposition

v3 withheld the gap list, showed raw command output instead of prose summaries,
tightened the budget to one sentence, and added conformity pressure. See
`2026-08-23-handoff-confidence-v3-both-arms.md`.

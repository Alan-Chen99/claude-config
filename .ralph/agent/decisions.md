# Decision journal — writing-for-agents loop3

## DEC-001 — `prompt-tests/CLAUDE.md` states no run result
- **Chosen**: Strip every arm-level count, prediction and verdict from the file,
  and write the rule into it with a mechanical test ("a sentence naming an arm, a
  count, or an outcome does not belong here").
- **Confidence**: 88.
- **Alternatives**: keep staging graders outside `prompt-tests/` (the prior
  mitigation); move the results to a sibling file; add a banner.
- **Reasoning**: the file reaches a grader by a channel the grader cannot see or
  decline. Staging is a procedure someone must remember; removing the payload is
  a property of the file. A rule with a mechanical test is one a future writer
  can apply without reading the history, which is the point.
- **Re-evaluate**: if a grader is ever shown to need per-case results to judge —
  then they belong in the staged inputs, chosen per run, not in an injected file.
- **Framing bias**: I chose the rule that makes my own later rounds cheaper to
  trust. A reader who wanted the historical results back would find this rule
  convenient to me and costly to them.
- **Independent evaluation**: not-started (must be a different iteration).
- 2026-09-22T00:50:00Z

## DEC-002 — delete `handoff-confidence` and `review-the-compression`; keep four
- **Chosen**: delete both; keep `halve-the-runbook`, `relayed-rule-provenance`,
  `found-set-closure`, `after-the-false-page`, each with a written justification
  in the file a reader meets first.
- **Confidence**: 70.
- **Alternatives**: keep both; delete `found-set-closure` instead of
  `handoff-confidence`; delete `after-the-false-page` as unrunnable.
- **Reasoning**: `handoff-confidence` and `found-set-closure` are the same shape
  — a subagent's short report to a parent that will not re-check — and the
  guidance says build cross-domain cases rather than replicate. Of the two,
  `found-set-closure`'s pressure is structural (the column type forbids the
  qualifier), so its result is attributable to the text rather than to how hard
  the task leaned. `review-the-compression` is green in both arms by its own
  design; a case that cannot separate arms cannot change a belief about a prompt
  edit, and it existed to watch for an unobserved future harm.
- **Re-evaluate**: if a later round wants the social-pressure mechanism
  `handoff-confidence` carried, rebuild it cross-domain rather than restoring it.
- **Framing bias**: the burden I applied was on *keeping*, per the objective's
  bias against things only a human can remove. Someone weighing corpus coverage
  first would keep both and reach the opposite answer.
- **Independent evaluation**: not-started.
- 2026-09-22T00:50:00Z

## DEC-003 — leave `payments-relay/` in place this round
- **Chosen**: fix the one statement in its README that my deletions falsified;
  do not delete the archive.
- **Confidence**: 62.
- **Alternatives**: delete it now and repair the five citing lines.
- **Reasoning**: deleting it means reading 12.9k words to know what five citations
  in three live references lean on. That is a second milestone, and doing it
  half-way leaves three references citing nothing — worse than the present state.
- **Re-evaluate**: next round, as its own piece of work.
- **Framing bias**: "next round" is how things survive indefinitely. If two more
  rounds pass without it, that is evidence the deletion is not actually wanted.
- **Independent evaluation**: not-started.
- 2026-09-22T00:50:00Z

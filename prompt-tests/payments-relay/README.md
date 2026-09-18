# The payments-relay fixture and its key

`fixture/RUNBOOK.md` — the ~1,163-word on-call runbook for a fictional
payments-relay service — was `general/halve-the-runbook`'s fixture until
2026-09-18, when that case was rebuilt on this repo's own
`.claude/skills/update-claude-code/SKILL.md`. The fixture itself lives on: three
cases carry a copy, and two of them still key off the analysis written for it.

| File | What it is |
| --- | --- |
| `key.md` | The fragment catalogue, shift classes and severity model written for the payments-relay runbook. Was `general/halve-the-runbook/reference-solution.md`. |
| `baselines.md` | Every arm the old `halve-the-runbook` ran, dated, with thinking-block reads. |
| `reference-artifact.md` | The 352-word model compression of the payments-relay runbook. |

Cases that still depend on `key.md`: `general/review-the-compression` (which
names it as its key outright), `general/after-the-false-page`,
`general/relayed-rule-provenance` and `general/prompt-edit-scope` (one citation
each). Fixture copies live in those cases' own `fixture/` directories.

**`key.md` is a scoring key, and `docs/prompt-testing-design.md` is why that is a
problem.** It enumerates sixteen fragments and asks for each "present, partial,
absent" — a rubric written before any output existed, by someone who had read the
source and not the output. It is kept because four live cases cite it and
deleting it would break them silently, not because the practice it encodes is
endorsed. A case rebuilt under the current design should stop citing it rather
than inherit it.

Everything under `runs/halve-the-runbook/` was measured against this fixture and
is not comparable to any run of the rebuilt case.

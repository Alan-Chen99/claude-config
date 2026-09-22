# The payments-relay fixture and its key

`fixture/RUNBOOK.md` — the ~1,163-word on-call runbook for a fictional
payments-relay service — was `general/halve-the-runbook`'s fixture until
2026-09-18, when that case was rebuilt on this repo's own
`.claude/skills/update-claude-code/SKILL.md`. The fixture itself lives on: three
`general/after-the-false-page` carries the surviving copy.

| File | What it is |
| --- | --- |
| `key.md` | The fragment catalogue, shift classes and severity model written for the payments-relay runbook. Was `general/halve-the-runbook/reference-solution.md`. |
| `baselines.md` | Every arm the old `halve-the-runbook` ran, dated, with thinking-block reads. |
| `reference-artifact.md` | The 352-word model compression of the payments-relay runbook. |

`key.md` and `baselines.md` discuss `general/review-the-compression`, a case
deleted on 2026-09-22. Nothing in the tree is that case any more.

Cases that still cite `key.md`: `general/after-the-false-page`,
`general/relayed-rule-provenance` and `general/prompt-edit-scope`. None of them
now uses it as a key — `after-the-false-page` did, and its reference records that
the instrument is gone rather than repointing at this file.

**`key.md` is a scoring key, and `docs/prompt-testing-design.md` is why that is a
problem.** It enumerates sixteen fragments and asks for each "present, partial,
absent" — a rubric written before any output existed, by someone who had read the
source and not the output. It is kept because three live references cite it in
passing, not because the practice it encodes is endorsed; once those three
citations are repaired nothing needs it. A case rebuilt under the current design should stop citing it rather
than inherit it.


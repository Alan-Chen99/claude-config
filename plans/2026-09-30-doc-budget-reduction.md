# Doc-budget reduction — decisions of 2026-09-30

Evidence: the registry landed holding 51 files at size, under caps drawn around the
status quo. Across 4,019 session logs, `docs/agent-tools-status-reference.md` was Read
5 times, `docs/background-sessions.md` 6, `docs/system-prompt-snapshot/README.md` 60,
each whole for one section.

| # | Decision | Change |
|---|---|---|
| 1 | Limits down now, cuts later, one per commit, CI green throughout | Every newly over file held at its size (23 rows, 74 in all), or `# target N` on a group the resolver cannot hold |
| 2 | `sys_prompt/alan-default-next.md` | Kept at 4,400 — session-start decision 16 |
| 3 | `opencode-prompt` | target 4,400 |
| 4 | `descriptions` | target 900 |
| 5 | `skill-bodies`, `agent-bodies` | 3,000 → 2,000 |
| 6 | `conventions` | target 20,000 |
| 7 | `claude-md`, `plans`, `cut_to` | Unchanged: 1,500, 1,000, 0.8 |
| 8 | `docs`, `notes`, `docs/superpowers/specs` | 5,000 / 4,000 / 4,000 → 2,000 for a new file |
| 9 | `skills/prompt-engineer/references` | 10,000 → 8,000 |
| 10 | `default_cap` | 15,000 → 12,000 |
| 11 | `skills/planner`, `output-styles`, `infra` | targets 12,000, 7,000, 9,000 |
| 12 | A raise above a class cap | At cut time, never ahead (`conventions/documentation.md`); none that day |
| 13 | A cut of a held file | Lowers the row to the new size or drops it: the runbook, cut to 9,931 under a 12,450 row, regrew to 10,723 in two commits |
| 14 | A body's reference material → an on-demand `.md` | A cut |
| 15 | `plans/` | Closed plans are deleted, not edited |
| 16 | Snapshot README row | 19,757 → 15,516, its size after 694cdec6 |
| 17 | A held row (2026-10-01) | Falls due with the next task on its file's subject (`conventions/documentation.md`); spec rows too, a deletable file being cuttable |

Cut queue, by how the text reaches a context; 17 can bring a held row forward:
`descriptions` → opencode `alan-default-ids` → `skills/alan-writing-style/CLAUDE.md` → the three agent bodies → skill bodies by size
→ `conventions` → docs, notes and specs → one `plans/` deletion pass →
`skills/planner/INTENT.md`, `output-styles`, `infra`.

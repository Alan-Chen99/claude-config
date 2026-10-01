# Doc-budget reduction — decisions of 2026-09-30

Evidence: `agent-tools doc-budget` the day the registry landed — 51 files held at
size, every class cap drawn around the status quo. Read-tool calls across 4,019
session logs: `docs/agent-tools-status-reference.md` 5, `docs/background-sessions.md`
6, `docs/system-prompt-snapshot/README.md` 60; each is pointed at for one section
and Read whole. The registry's comments carry each cap's why; this records the
decisions.

| # | Decision | Change |
|---|---|---|
| 1 | Limits down now, cuts later, one per commit, CI green throughout | Class caps and `default_cap` lowered; every newly over file held at its size (23 rows, 74 in all). A group the resolver cannot hold carries `# target N` and drops to N in its cut commit |
| 2 | `sys_prompt/alan-default-next.md` | Kept at 4,400 — session-start decision 16 |
| 3 | `opencode-prompt` | target 4,400 |
| 4 | `descriptions` | target 900 |
| 5 | `skill-bodies`, `agent-bodies` | 3,000 → 2,000 |
| 6 | `conventions` | target 20,000 |
| 7 | `claude-md`, `plans`, `cut_to` | Unchanged: 1,500, 1,000, 0.8 |
| 8 | `docs`, `notes`, `docs/superpowers/specs` | 5,000 / 4,000 / 4,000 → 2,000 for a new file; no file raised |
| 9 | `skills/prompt-engineer/references` | 10,000 → 8,000 |
| 10 | `default_cap` | 15,000 → 12,000 |
| 11 | `skills/planner`, `output-styles`, `infra` | targets 12,000, 7,000, 9,000 |
| 12 | A raise above a class cap | Asked for at cut time with what the 80% target would lose, never ahead of it. None today |
| 13 | A cut of a held file | Lowers the row to the new size or drops it. The runbook was cut to 9,931 under a 12,450 row and regrew to 10,723 in two commits |
| 14 | Body → reference | Moving a SKILL.md or CLAUDE.md body's reference material into an on-demand `.md` is a cut |
| 15 | `plans/` | Closed plans are deleted, not edited |
| 16 | Snapshot README row | 19,757 → 15,516, its size after 694cdec6 |

Cut queue, by how the text reaches a context: `descriptions` (12 `description:`
lines) → opencode `alan-default-ids` → `agent-tools/CLAUDE.md` 17,107,
`skills/alan-writing-style/CLAUDE.md` 10,977, `sys_prompt/CLAUDE.md` 9,952 → the
three agent bodies → skill bodies by size → `conventions` → docs and notes as
touched → one `plans/` deletion pass → `skills/planner/INTENT.md`, `output-styles`,
`infra`. Spec rows are not a queue: a shipped spec is not edited again, so its row
stands until the spec is edited or deleted.

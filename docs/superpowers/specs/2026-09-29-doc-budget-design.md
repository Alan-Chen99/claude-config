# Doc budget: caps by how text reaches a context

## Problem

This repo tracks 878 `.md` files, 3.53M tokens by the local tokenizer, and
nothing prices what a session loads: `skills/telegram-hitl/SKILL.md` reached
7,316 tokens before anyone measured it, one pytest now pins it at 1,000, and
`notes/compliance-check-failure-mode.md` carries an 18k `--api` budget in prose
that it exceeds. `/workspace/scripts/doc_budget.toml` prices docs by directory,
which fits a repo where every doc is read the same way. Here the same token
costs anywhere from once per request in every project (`sys_prompt/`) to never
(1.57M tokens of converted papers), so the registry's groups must follow the
mechanism that loads a file, not the directory it sits in.

## Rules

1. **Every tracked `.md` counts against exactly one group** (symlinks skipped)
   unless a `[data]` declaration covers it. A `README.md` or `CLAUDE.md` counts
   wherever it is: it is the directory's own doc, not the work inside it.
2. **Unit: local-tokenizer tokens** — `agent-tools count-tokens` without
   `--api`, the one backend that runs offline, in CI and in worktrees, and the
   unit the existing pin uses. About 1.5× that is Claude context on prose; the
   two backends never reconcile, so `--api` stays a one-off measurement.
3. **A file's group, first match wins:**
   1. a group named with the file's path — `[held.files]` entries included;
   2. a `[data]` path covering it: listed in every report, never counted;
   3. its derived class, each file its own group at the class cap:
      `claude-md` (every `CLAUDE.md`), `skill-bodies` (`skills/<n>/SKILL.md`,
      `.claude/skills/<n>/SKILL.md`), `agent-bodies` (`agents/*.md`);
   4. the longest path group — a literal name over a placeholder on a tie;
      `per_file` makes each file its own group at the group's cap; `<name>`
      stands for one path segment and makes each match its own group;
   5. the residual.

   `one_of` claims its files ahead of all of this and pays the largest member.
   `descriptions` is a derived group counting a *field* — the `description:`
   of every skill and agent, which the skills listing carries into every
   session — so a description is counted there and again inside its file.
4. **Over cap: cut that group to 80% of cap in the same change.** A group over
   when you arrived is debt: say so, pay it when the task is about its docs.
   Moving prose out of `.md` is not a cut; neither is a `[data]` entry, a held
   size or a raised cap.
5. **Loosening the registry carries `approved`**: a `[data]` entry, the `[held]`
   table, and any group `cap` above `default_cap` or above its class cap.
   `<8 hex of session id>` is inert in that session — the entry is ignored and
   the file counts at the cap it would otherwise have; `user:<8 hex>` is the
   session in which the user approved it and is live at once. Either opens with
   `agent-tools cc-pretty <8 hex> --skeleton`. Class caps and `default_cap` are
   top-level policy with no fallback to gate against; the user edits them.
6. **Exit status**: 0 within budget; 1 any group over cap; 2 registry error —
   an unknown key, a cap above default without `approved`, a malformed
   `approved`, a `[data]` path or group name covering no tracked file, a held
   entry naming a missing file or a size at or below the class cap.

## Classes and caps at introduction

| Reaches a context | Group | Cap | Today |
| --- | --- | --- | --- |
| every request, every project | `sys_prompt/alan-default-next.md` | 4,400 | 4,325 |
| every request, opencode | `opencode/agents/<agent>.md` (`one_of`) | 5,200 | 5,009 |
| every session, every project | `descriptions` (derived) | 1,200 | 1,019 |
| per invocation | `skill-bodies` (derived) | 3,000 | 7 held |
| per invocation | `skills/telegram-hitl/SKILL.md` | 1,000 | 988 |
| per spawn | `agent-bodies` (derived) | 3,000 | 2 held |
| per spawn (agent bodies read them) | `conventions` | 25,000 | 23,785 |
| every session touching the directory | `claude-md` (derived) | 1,500 | 5 held |
| on demand, one at a time | `docs` (`per_file`) | 5,000 | 5 held |
| on demand | `notes` (`per_file`) | 4,000 | 7 held |
| on demand | `docs/superpowers/specs` (`per_file`) | 4,000 | 6 held |
| on demand | `plans` (`per_file`, as in /workspace) | 1,000 | 19 held |
| on demand | `skills/<name>`, `scripts`, `prompt-tests`, `sys_prompt` | 15,000 | ok |
| on demand | `skills/prompt-engineer/references` (`per_file`) | 10,000 | 9,783 max |
| on demand | `skills/planner` — `INTENT.md` is 11k | 17,808 held | |
| not loaded since `cbeb6721` | `output-styles` | 11,000 | 10,275 |
| residual | `infra`: root README, `skills/README.md`, `.github` | 12,000 | 10,400 |

Data, each with `approved` and `why`: `docs/system-prompt-snapshot/<model>`
(regenerated), `skills/prompt-engineer/papers` (converted),
`skills/alan-writing-style/samples` (regression cases), `skills/playwright-cli`
(vendored), `prompt-tests/general/<case>/fixture` and `prompt-tests/runs`
(loaded into test sessions), `notes/compliance-check-failure-mode`,
`notes/ralph-loop3-writing-for-agents` and `docs/prompt-trials` (closed
records), `docs/superpowers/plans` (the writing-plans format does not fit a
cap), `skills/prompt-engineer-v2/test-requests.md` (a transcript). 2.90M tokens
listed; 625k counted.

Held at introduction: every file over its class cap, at its size, so CI is
green on day one and the first addition to any of them pays a 20% cut.
`agent-tools doc-budget --print-held` emits the lines; the report names a held
file that has fallen under its class cap so the entry can be dropped.

## Tool

`agent-tools doc-budget [--print-held] [path ...]`, a pass-through to
`claude_config.doc_budget` like `count-tokens`. The report is the reference's
table — counted, cap, 80% target, state — ordered by class with each group's
`loaded` label, per-file detail for an over-cap group or a named path, and the
data groups' file counts and totals at the bottom so growth there stays
visible. The tokenizer loads once: `count_tokens.load_tokenizer()` does the
digest check and returns the instance, `_count_local` wraps it; today
`_count_local` reloads the 12.8 MB file on every call, 0.36 s each.

## Enforcement

- `tests/test_doc_budget.py`: the registry is valid; the tree is within budget
  (the CI gate, inside the existing `uv run pytest` job); the resolver's rules
  on a synthetic git tree — precedence, index files inside data, `one_of`,
  `<name>`, the same-session gate, each exit-2 condition.
- The telegram pin moves into the registry;
  `test_the_skill_stays_inside_its_token_budget` goes.
- Hook stdout is not `.md` and is pinned beside its renderer: the env-context
  block on a fixture repo ≤ 700 tokens (615 today) in `tests/test_env_context.py`;
  the `pre_output.record` reminder ≤ 60 (42) in `tests/test_pre_output_record.py`;
  `hook_subagent.rs`'s `additional_context()` ≤ 1,000 chars (856) in its own
  unit tests, chars because the Rust suite has no tokenizer.
- Root `CLAUDE.md` gains a *Documentation budget* policy paragraph adapted from
  `/workspace/CLAUDE.md`; `sys_prompt/CLAUDE.md` names the prompt's cap.

## Files

| File | Change |
| --- | --- |
| `doc-budget.toml` | New. The registry: header, classes, held table, data. |
| `src/claude_config/doc_budget.py` | New. Resolver, report, `--print-held`, exit codes. |
| `src/claude_config/count_tokens.py` | `load_tokenizer()` split out of `_count_local`. |
| `agent-tools/src/main.rs` | `doc-budget` subcommand, help forwarded like `count-tokens`. |
| `agent-tools/tests/doc_budget_test.rs` | Forwards args and the module's exit code. |
| `tests/test_doc_budget.py` | New. |
| `tests/test_telegram_hitl_skill.py` | Budget test removed. |
| `tests/test_env_context.py`, `tests/test_pre_output_record.py`, `agent-tools/src/hook_subagent.rs` | Size pins. |
| `CLAUDE.md` | `doc-budget.toml` row, the command under Build and test, the policy paragraph. |
| `agent-tools/CLAUDE.md`, `src/claude_config/CLAUDE.md` | Subcommand and module rows. |
| `skills/CLAUDE.md`, `README.md` | The telegram row and sentence stop naming the pytest pin. |
| `sys_prompt/CLAUDE.md` | "Keep it concise" names the registry cap; `--api` stays the context figure. |
| `.claude/skills/update-claude-code/SKILL.md` | Inventory row: `doc_budget.py` reads `CLAUDE_CODE_SESSION_ID`; renamed, the gate goes inert with a warning on every run. |
| `docs/CLAUDE.md` | Spec count. |

## Out of scope

Frontmatter cases from the reference: no file here needs one, and `[data]`
accepts a file path, so a future exemption is one declared, approved line.
Ratcheting a held size down when the file shrinks: the report names the
droppable entry instead. A commit hook: this repo gates through CI and policy.

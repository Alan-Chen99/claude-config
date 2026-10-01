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
   `--api`, the one backend that runs offline, in CI and in worktrees. About
   1.5× that is Claude context on prose; the two backends never reconcile, so
   `--api` stays a one-off measurement.
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
   when you arrived is debt: say so, pay it when the task is about its docs. A
   held row falls due with the next task on what its file is about, whether or
   not the task edits the file: drop it and, over the class cap, cut to 80% of
   it or ask the user for a cap.
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

Held at introduction: every file over its class cap, at its size, so CI is
green on day one. `agent-tools doc-budget --print-held` emits the lines; the
report names a held file that has fallen under its class cap so the entry can
be dropped. The caps and data entries at introduction are the registry's first
commit; the reduction, the same day, is `plans/2026-09-30-doc-budget-reduction.md`.

## Out of scope

Frontmatter cases from the reference: no file here needs one, and `[data]`
accepts a file path, so a future exemption is one declared, approved line.
Ratcheting a held size down when the file shrinks: the report names the
droppable entry instead. A commit hook: this repo gates through CI and policy.

# session-analysis/

Session log analysis over opencode exports and Claude Code JSONL:
skeleton-first reading protocol with task, evidence and adjudication modes.

## Files

| File        | What                                            | When to read                   |
| ----------- | ----------------------------------------------- | ------------------------------ |
| `SKILL.md`  | Skill definition, reading protocol, modes       | Using or invoking this skill   |
| `README.md` | Design rationale and limitations                | Understanding the approach     |

## Agent Policy

- `~/.claude/skills` is a symlink to the main checkout's `skills/`, so the installed
  `session-analysis` skill serves `/repos/claude-config`'s `SKILL.md` — not the one next
  to this file. From a worktree, invoke the copy you are editing as the
  **`session-analysis-wip`** skill: `.claude/skills/session-analysis-wip` is a relative
  link to this directory. In the main checkout both names resolve to the same files.
- Invoke with **no `args`**. Passing args substitutes them into every literal `$N` and
  `$ARGUMENTS` in the loaded text, which mangles the `ocr()` / `ocrange()` shell helpers in
  `SKILL.md`. `$N` takes the (N+1)-th whitespace-separated word of the args string — args
  `alpha bravo charlie` render `$1` as `bravo` — parsing greedily past one digit; an
  out-of-range `$N` stays literal.
  With no args, every `$N` stays literal and `$ARGUMENTS` renders empty (probed 2026-09-24,
  cc 2.1.269).

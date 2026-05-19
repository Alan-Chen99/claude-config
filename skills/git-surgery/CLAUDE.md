# git-surgery/

Rewrite git history with libgit2 (pygit2) without touching the worktree, index, or HEAD. Preserves SHA references checked into tracked files and descendant commit messages.

## Files

| File         | What                                          | When to read                           |
| ------------ | --------------------------------------------- | -------------------------------------- |
| `SKILL.md`   | Rules, algorithm, common mistakes, red flags  | Using this skill                       |
| `example.py` | Working reference implementation (edit-message + cascade) | Running it, or adapting for squash/drop/reorder |
| `README.md`  | Design rationale                              | Understanding why this exists          |

## Prerequisites

- `pygit2` (libgit2 Python binding). Install: `uv pip install pygit2` in the project venv, or `pip install pygit2`.

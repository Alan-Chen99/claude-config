# Git Surgery

Programmatic git history rewriting with libgit2 (pygit2). Two non-negotiable rules:

1. **Worktree off-limits** — don't touch HEAD, the index, or any working-tree file. Output goes to a new ref or stdout.
2. **Ancestor refs stay valid** — SHA references in tracked files and commit messages that point to a rewritten commit are updated to its rewritten counterpart.

## Why a skill?

Agents reach for `git rebase -i`, `git filter-branch`, or `git filter-repo` by default. All three:

- Touch the worktree and index
- Move HEAD or branch refs implicitly
- Run hooks (which may fail on rewritten commits)
- Fail or auto-stash uncommitted work, risking it

When the worktree must survive (in-progress changes, dirty index, HEAD must stay), or when SHA references checked into files (CHANGELOG.md, release notes, docs) and commit messages must remain valid, those tools don't fit. libgit2 lets you build new commits in the object database directly, leaving everything else untouched, and gives the cascading SHA-rewrite logic somewhere clean to live.

## Why pygit2?

- libgit2 is the canonical non-CLI git implementation; pygit2 is its Python binding.
- Object-DB operations are atomic in-process — no subprocess overhead, no shell-out, no hook execution.
- Easier programmatic SHA mapping than chaining `git commit-tree` / `git mktree` / `git hash-object` (the baseline shell-out alternative, which the skill was designed against after watching an agent hand-roll it).
- `repo.cherrypick_commit(commit, parent, mainline)` operates in-memory (returns an `Index`) — distinct from `repo.cherrypick(...)` which touches the on-disk index.

## Design choices

### Output to a new ref, not HEAD

Every surgery writes to `refs/git-surgery/result` and prints the new HEAD-equivalent SHA. The caller decides whether to fast-forward. This makes the surgery a pure function: same inputs, same output ref; can be inspected, diffed, discarded. Updating HEAD silently is the most damaging failure mode.

### Cascade via single topological forward-walk

After the targeted surgery, walk `head_sha`'s ancestors in `topological | reverse` order (oldest first). Every commit's parents are already in the mapping (rewritten or identity) by the time it's processed, so the chain closes in a single pass — no second pass, no fixed-point iteration.

### Identity-mapping unchanged ancestors

When a commit isn't touched (no new parents, no message-SHA refs, no blob-SHA refs), record `mapping[sha] = sha`. Keeps downstream lookups uniform — descendants don't need a special case for ancestors that happened not to change.

### Short SHA resolution via revparse_single

Naive substring substitution would rewrite any 7+-hex-char run: AWS keys, color literals, random hashes, secrets. The skill runs each candidate through `revparse_single` and only rewrites it if (a) it resolves to a commit and (b) the full SHA is in the mapping. Replacement preserves the original short-prefix length, matching the surrounding text's convention.

### Out of scope (explicitly)

- Tag rewriting — not asked for.
- Hook execution — pygit2 doesn't run pre-commit/commit-msg/post-commit hooks. If the workflow requires them, run them externally on the new ref before fast-forwarding.
- GPG signature preservation — unsound after rewriting; new commits are unsigned.
- Submodule (gitlink) rewriting — gitlinks are passed through unchanged.
- Multi-branch tip rewriting — the example walks one head. For multi-branch, pass each tip through `cascade()` with the shared mapping; the algorithm extends cleanly.

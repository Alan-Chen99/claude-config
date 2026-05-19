---
name: git-surgery
description: Use when rewriting git history (squash, drop, reorder, split, amend message/author/date) and the worktree, index, or HEAD must not be touched (uncommitted work in progress, dirty index, HEAD must stay), or when commit SHAs in tracked files (CHANGELOG, docs, release notes) or in other commit messages reference rewritten commits and those references must remain valid after the rewrite.
---

# Git Surgery

Rewrite git history programmatically with libgit2 (pygit2). Two non-negotiable rules:

1. **Worktree off-limits.** Don't touch HEAD, the index, or any working-tree file. Write the result to a new ref or print the new SHA. The caller decides whether to fast-forward.
2. **Ancestor refs stay valid.** A SHA checked into a tracked file or commit message that points to an ancestor of HEAD must still resolve to "the corresponding ancestor" after rewriting — references to old commit `X` become references to its rewrite `X'`.

## When to use

- Editing commit metadata (message, author, date) without re-staging
- Squashing/dropping/reordering commits without `git rebase -i` conflict UI
- Worktree has uncommitted/in-progress work that MUST survive
- Tracked files (CHANGELOG.md, docs, release notes) contain commit SHAs that must remain valid
- Commit messages reference other commit SHAs (cascading rewrite needed)
- You want a clean failure mode: print the new SHA, let the caller fast-forward

## When NOT to use

- A plain `git commit --amend` on HEAD with a clean worktree suffices
- Authoring new commits (use plain `git commit`)
- Discarding history (use `git reset`)
- Repository has commit-msg/pre-commit hooks that must run on rewritten commits (pygit2 does not invoke them)

## Rule 1: Don't touch the worktree

| Operation                                                                  | Allowed? |
|----------------------------------------------------------------------------|----------|
| Read refs, walk commits, read blobs/trees                                  | yes      |
| Create blobs/trees/commits in the object DB                                | yes      |
| Write to `refs/git-surgery/<name>` (caller-namespaced)                     | yes      |
| Print the new HEAD-equivalent SHA to stdout                                | yes      |
| Update HEAD or any user-facing branch ref                                  | **no — unless caller explicitly permits** |
| `repo.checkout(...)`, `repo.reset(...)`, `repo.index.read_tree(...)`        | **no — touches index/worktree** |
| Modify any path under the working directory                                | **no**   |
| Subprocess `git rebase`, `git cherry-pick`, `git filter-branch`, `git filter-repo`, `git reset`, `git checkout` | **no — touches HEAD/index/worktree, runs hooks** |

Pygit2 hygiene:

- Pass `update_ref=None` to `repo.create_commit(...)` — never `"HEAD"`, never a branch.
- Use `repo.cherrypick_commit(commit, parent, mainline)` (in-memory, returns an `Index`) NOT `repo.cherrypick(...)` (touches the index on disk).
- Default output ref: `refs/git-surgery/result`. The caller fast-forwards HEAD only if it wants to and the worktree allows it.
- If the rewritten HEAD-equivalent does not match `repo.head.target` (i.e., the worktree HEAD has diverged from the rewrite), refuse to touch HEAD: print the SHA and exit.

## Rule 2: Preserve ancestor SHA references

Maintain `mapping: old_sha → new_sha` throughout the rewrite. For every commit in the rewritten chain, rewrite three places:

| Location               | What to rewrite                                                                  |
|------------------------|----------------------------------------------------------------------------------|
| Commit parents         | `mapping.get(p, p)` for each parent SHA                                          |
| Commit message         | Full 40-char SHAs and short SHAs (≥7 hex) that resolve to a mapped commit        |
| Tree blobs             | Same SHA patterns inside file contents                                           |

**Cascade.** When any of parents/message/tree change, the commit itself gets a new SHA — add it to `mapping`. Descendants then see the new parent (and possibly new SHA refs) in their own rewrite. Keep walking forward in topo order from the surgery range to every ref tip you want to update, until exhausted.

**Short SHA resolution.** Match `\b[0-9a-f]{7,40}\b` candidates and call `repo.revparse_single(s)` on each. Only rewrite if it resolves to a commit AND the full SHA is in `mapping`. Replace with `mapping[full][:len(s)]` to preserve the original short length.

**Why short SHAs need resolution, not substring substitution:** a 7+-hex-char run that doesn't resolve to a commit (random hash, AWS access key, color literal) must be left alone. `revparse_single` is the only reliable disambiguator.

## Algorithm

```
1. Targeted surgery on the range → produce new commits for the target range.
   For each old commit X in the range, set mapping[X.sha] = X'.sha.
   Always pass update_ref=None to create_commit.

2. Walk forward (topological + reverse, oldest first) from the surgery range to
   every ref tip you want to update. For each commit C not yet in mapping:

   new_parents = [mapping.get(p, p) for p in C.parents]
   new_message = rewrite_shas(C.message, repo, mapping)
   new_tree    = rewrite_tree(C.tree,    repo, mapping)

   if any of parents/message/tree changed:
       new_C = create_commit(update_ref=None,
                             author=C.author, committer=C.committer,
                             message=new_message, tree=new_tree,
                             parents=new_parents)
       mapping[C.sha] = new_C.sha
   else:
       mapping[C.sha] = C.sha     # identity — keeps cascade consistent

3. new_head_sha = mapping[old_head_sha]
4. repo.references.create("refs/git-surgery/result", new_head_sha, force=True)
5. print(new_head_sha)

rewrite_tree(tree, repo, mapping):
   For each entry: recurse if subtree; for blobs, try utf-8 decode and run
   rewrite_shas; rebuild the tree via TreeBuilder only if any entry changed.

rewrite_shas(text, repo, mapping):
   Sub r"\b[0-9a-f]{7,40}\b": for each match,
     - if len == 40 and m in mapping: replace with mapping[m]
     - if 7 <= len < 40: revparse_single → if resolves to a mapped full sha,
       replace with mapping[full][:len(match)]; else leave alone.
```

## Quick reference

| Operation             | Step 1 (target surgery)                                                                                   |
|-----------------------|-----------------------------------------------------------------------------------------------------------|
| Edit a commit message | `create_commit(None, C.author, C.committer, new_msg, C.tree.id, [p.id for p in C.parents])` → mapping     |
| Edit author/date      | Same with new `Signature` for author/committer                                                            |
| Drop a commit C       | For each child of C: `idx = repo.cherrypick_commit(child, C.parents[0], 0)`; `tree = idx.write_tree(repo)`; create new commit on C's parent. Cascade from C's descendants. |
| Squash N commits      | New commit: tree = last commit's tree; message = concatenated; parents = first commit's parents. Map ALL N old SHAs to the single new SHA. **Strip or pre-rewrite any SHA refs to the squash range from the concatenated message before creating** (self-reference, see below). Cascade. |
| Split a commit        | Two new commits with subset trees; replace one entry in mapping with the second-new SHA; cascade.          |
| Reorder               | In-memory cherry-pick each commit onto its new parent; build mapping; cascade as usual.                   |

Common across all: `update_ref=None`, identity (`Signature`) preserved unless explicitly changed, output to `refs/git-surgery/result`.

### Self-referential SHAs (squash/drop/split caveat)

When a surgery output commit's own message would contain a SHA reference to a commit in the surgery range, that reference **cannot be rewritten after the fact** — the new commit's SHA depends on its message, so the message can't reference its own final SHA. The `cascade()` walks descendants of the surgery range, not the surgery output itself.

Symptoms: after a squash where two of the squashed commits referenced each other by short SHA, the squashed commit's body still contains the old short SHAs.

Fix (do this in your `surgery_*` function, before `create_commit`):
- For squash: strip or rewrite SHA refs to squash-range commits from each constituent message before concatenating. Common choice: drop the inner reference lines entirely, since the new message presents all the changes together.
- For drop/split: same — if the new commit's message would reference a SHA being rewritten, edit it out before creating.
- Alternative: insert a sentinel like `<<SELF>>` in the message, create the commit, observe that the new commit's SHA is now stable, then accept the sentinel as a documented placeholder. (Not iterative — the SHA still depends on the message.)

The cascade catches every other case: descendants of the surgery range, including those that reference squash-range commits, get rewritten correctly because their SHAs are derived after the mapping is complete.

## Example

See `example.py` for a complete worked implementation — edit-commit-message + full cascade, handling full + short SHAs in messages and tracked-file blobs. Run:

```
python3 example.py <repo-path> <target-sha-or-rev> "<new message>"
```

It writes `refs/git-surgery/result` and prints the new HEAD-equivalent SHA. HEAD, the index, and the worktree are untouched.

Adapt the `surgery()` function inside `example.py` for other operations (squash, drop, reorder); the `cascade()` and `rewrite_*` helpers stay identical.

## Common mistakes

| Mistake                                                              | Why bad                                                              | Fix                                                                            |
|----------------------------------------------------------------------|----------------------------------------------------------------------|--------------------------------------------------------------------------------|
| `repo.checkout(...)` after rewriting                                  | Touches index + worktree                                              | Print the SHA only; never checkout                                              |
| `repo.head.set_target(new_sha)` without explicit caller permission   | Moves HEAD silently                                                   | Write to `refs/git-surgery/...`; print the SHA; exit                            |
| Passing `"HEAD"` or `"refs/heads/main"` as `update_ref`              | Same as above                                                         | Use `update_ref=None` and create the ref explicitly at the end                  |
| Rewriting parents only; skipping message and blob rewrites           | SHA references in changelogs and commit messages go stale             | Always run `rewrite_message` AND `rewrite_tree` on every cascaded commit         |
| Skipping the cascade                                                  | Descendants keep old parent SHA in their parent line → ref chain breaks; or keep stale SHA refs in their own messages | Walk forward in topo order from the surgery range to every ref tip you care about |
| Naive substring-replace of short SHAs                                 | False positives (any 7-hex-char run replaced — AWS keys, color hex, random hashes) | `revparse_single` each candidate; only rewrite when it resolves to a mapped commit |
| Shelling out to `git rebase`, `filter-branch`, `filter-repo`         | Touches index, HEAD, worktree; runs hooks                              | Stay inside pygit2                                                              |
| `.decode("utf-8")` on a binary blob without try/except                | UnicodeDecodeError → commit not rewritten or whole walk crashes       | `try: blob.data.decode('utf-8'); except UnicodeDecodeError: keep blob unchanged` |
| Walking only from one HEAD when multiple branches share the surgery range | Other branch tips still reference the old SHAs                       | Pass each branch tip through the cascade; collect all new tips                   |
| Bailing the forward walk at the end of the surgery range              | Descendants of the range never get their parent SHA fixed             | Walk forward to ALL ref tips, not just through the range                         |

## Red flags — STOP and revisit

- `repo.checkout`, `repo.reset`, `repo.index.write`, `repo.set_head`
- `update_ref="HEAD"` / `update_ref="refs/heads/..."` in `create_commit`
- Subprocess to `git rebase`, `git cherry-pick`, `git filter-branch`, `git filter-repo`, `git reset`, `git checkout`
- Substituting SHA-shaped strings in blobs/messages without verifying they resolve to a mapped commit
- Force-pushing or moving any user-facing branch in the same script that does the surgery

All of these mean: revisit the algorithm. Use the `example.py` template.

## Verification checklist after running

- `git rev-parse HEAD` is byte-identical to before
- Working-tree files (including untracked/gitignored) byte-identical to before
- `git rev-parse refs/git-surgery/result` returns the printed SHA
- `git log refs/git-surgery/result --oneline` shows the rewritten chain
- `git show refs/git-surgery/result:<file>` shows the NEW SHAs where the file referenced rewritten commits
- Commit messages in the new chain that referenced rewritten commits now reference the new (full or short) SHAs

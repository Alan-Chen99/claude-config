#!/usr/bin/env python3
"""Edit a commit's message via libgit2 (pygit2), with cascading rewrites that
preserve SHA references in tracked-file blobs and descendant commit messages.

Worktree, index, and HEAD are never touched. Output:
  - new ref at refs/git-surgery/result (overwrites if it exists)
  - new HEAD-equivalent SHA on stdout

Usage:
  python3 example.py REPO_PATH TARGET_REV "NEW MESSAGE"
                     [--head REV] [--ref REFNAME]

Adapt the surgery_edit_message() function for other operations (squash, drop,
reorder); cascade() and the rewrite helpers stay identical.
"""

from __future__ import annotations

import argparse
import re
import sys

import pygit2
from pygit2.enums import SortMode

# 7..40 lowercase-hex bounded by word boundaries. Captures both full and short
# SHAs; the substitution decides which case applies.
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")


def rewrite_shas_text(text: str, repo: pygit2.Repository, mapping: dict[str, str]) -> str:
    """Rewrite full + short SHAs in a unicode string.

    A candidate is only rewritten if it resolves (via revparse_single) to a
    commit whose full SHA is in `mapping`. Short SHAs preserve their length
    (a 7-char prefix becomes the first 7 chars of the new full SHA), matching
    the convention of the surrounding text.

    Non-commit hex runs (random hashes, AWS keys, color literals) are left
    alone because they don't resolve to a commit.
    """
    def sub(m: re.Match[str]) -> str:
        s = m.group(0)
        if len(s) == 40:
            return mapping.get(s, s)
        # Short SHA: confirm it actually resolves to a commit before rewriting.
        try:
            obj = repo.revparse_single(s)
        except (KeyError, pygit2.InvalidSpecError, pygit2.GitError, ValueError):
            return s
        if not isinstance(obj, pygit2.Commit):
            return s
        full = str(obj.id)
        if full in mapping:
            return mapping[full][: len(s)]
        return s
    return SHA_RE.sub(sub, text)


def rewrite_tree(
    repo: pygit2.Repository, tree: pygit2.Tree, mapping: dict[str, str]
) -> pygit2.Oid:
    """Recursively rewrite SHA refs inside blobs.

    Returns the new tree OID (== tree.id when nothing changed). Subtrees are
    rebuilt only when they themselves changed; binary blobs are passed through.
    """
    builder = repo.TreeBuilder()
    changed = False
    for entry in tree:
        if entry.type_str == "tree":
            sub_tree = repo[entry.id]
            new_id = rewrite_tree(repo, sub_tree, mapping)
            if new_id != entry.id:
                changed = True
            builder.insert(entry.name, new_id, entry.filemode)
        elif entry.type_str == "blob":
            blob = repo[entry.id]
            try:
                text = blob.data.decode("utf-8")
            except UnicodeDecodeError:
                # Binary blob: leave unchanged.
                builder.insert(entry.name, entry.id, entry.filemode)
                continue
            new_text = rewrite_shas_text(text, repo, mapping)
            if new_text == text:
                builder.insert(entry.name, entry.id, entry.filemode)
            else:
                new_blob = repo.create_blob(new_text.encode("utf-8"))
                builder.insert(entry.name, new_blob, entry.filemode)
                changed = True
        else:
            # gitlinks (submodules), etc. — leave the entry alone.
            builder.insert(entry.name, entry.id, entry.filemode)
    return builder.write() if changed else tree.id


def cascade(
    repo: pygit2.Repository, head_sha: str, mapping: dict[str, str]
) -> str:
    """Walk ancestors of head_sha (oldest first). For each commit not yet in
    mapping, rebuild it if its parents/message/tree changed; otherwise mark
    identity. Returns the new SHA at the original head_sha position.

    Topological+reverse ordering guarantees every parent is in `mapping`
    (rewritten or identity) before its child is processed, so the SHA chain
    closes cleanly without a second pass.
    """
    head_oid = pygit2.Oid(hex=head_sha)
    for commit in repo.walk(head_oid, SortMode.TOPOLOGICAL | SortMode.REVERSE):
        sha = str(commit.id)
        if sha in mapping:
            continue  # already produced by surgery() or an earlier cascade iter

        new_parent_shas = [mapping.get(str(p.id), str(p.id)) for p in commit.parents]
        new_parents = [pygit2.Oid(hex=s) for s in new_parent_shas]
        parents_changed = any(
            new_s != str(op.id) for new_s, op in zip(new_parent_shas, commit.parents)
        )

        new_msg = rewrite_shas_text(commit.message, repo, mapping)
        msg_changed = new_msg != commit.message

        new_tree_id = rewrite_tree(repo, commit.tree, mapping)
        tree_changed = new_tree_id != commit.tree.id

        if parents_changed or msg_changed or tree_changed:
            new_oid = repo.create_commit(
                None,                # update_ref=None: never moves HEAD or any branch
                commit.author,
                commit.committer,
                new_msg,
                new_tree_id,
                new_parents,
            )
            mapping[sha] = str(new_oid)
        else:
            mapping[sha] = sha  # identity — keeps downstream cascade consistent

    return mapping.get(head_sha, head_sha)


def surgery_edit_message(
    repo: pygit2.Repository,
    target_sha: str,
    new_message: str,
    mapping: dict[str, str],
) -> None:
    """Step 1 of the surgery: replace the target commit with one carrying
    `new_message`. Tree, parents, author, committer are all preserved.
    `mapping[target_sha]` is set to the new commit's SHA so the cascade picks
    it up.

    To adapt for other operations, replace the body:
      - Squash N commits: take last commit's tree, concat messages,
        parents=first.parents; map ALL N old SHAs to the single new SHA.
      - Drop commit C: for each child of C, in-memory cherry-pick child onto
        C.parents[0] (repo.cherrypick_commit(child, C.parents[0], 0).write_tree()),
        create new commit, map old child sha -> new sha.
      - Reorder: in-memory cherry-pick each commit onto its new parent;
        build mapping accordingly.
    The cascade() and rewrite_* helpers stay identical.
    """
    target = repo[pygit2.Oid(hex=target_sha)]
    new_oid = repo.create_commit(
        None,                       # update_ref=None
        target.author,
        target.committer,
        new_message,
        target.tree.id,
        [p.id for p in target.parents],
    )
    mapping[target_sha] = str(new_oid)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Edit a commit's message via pygit2 with cascading SHA-ref rewrite. "
                    "Never touches HEAD/index/worktree."
    )
    parser.add_argument("repo", help="path to the git repository")
    parser.add_argument("target", help="revspec for the commit whose message to edit")
    parser.add_argument("new_message", help="new commit message (full text)")
    parser.add_argument(
        "--head", default="HEAD",
        help="ref-tip to walk forward from (default: HEAD)",
    )
    parser.add_argument(
        "--ref", default="refs/git-surgery/result",
        help="refname to write the rewritten tip to (default: refs/git-surgery/result)",
    )
    args = parser.parse_args()

    repo = pygit2.Repository(args.repo)
    head_sha = str(repo.revparse_single(args.head).id)

    target_obj = repo.revparse_single(args.target)
    if not isinstance(target_obj, pygit2.Commit):
        print(f"target {args.target!r} did not resolve to a commit", file=sys.stderr)
        return 2
    target_sha = str(target_obj.id)

    mapping: dict[str, str] = {}

    # Step 1: targeted surgery on the chosen commit.
    surgery_edit_message(repo, target_sha, args.new_message, mapping)

    # Step 2: cascade through descendants up to head_sha.
    new_head = cascade(repo, head_sha, mapping)

    # Step 3: write the result to a dedicated ref. Do NOT touch HEAD.
    repo.references.create(args.ref, pygit2.Oid(hex=new_head), force=True)

    # Step 4: announce the new HEAD-equivalent SHA. The caller decides whether
    # to fast-forward HEAD (e.g., `git update-ref HEAD <printed-sha>` if the
    # worktree is clean and the new commit descends from the current HEAD).
    print(new_head)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

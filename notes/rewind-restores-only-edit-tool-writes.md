# `/rewind` restores only Edit/Write/NotebookEdit files — Bash writes are never checkpointed

Investigated 2026-09-04 against the decompiled **Claude Code 2.1.235** tree at `/repos/claude-code-decompiled/`. `/rewind`'s code restore reverts only files that the Edit, Write, or NotebookEdit tools were about to touch. It is not a working-tree snapshot: no directory walk exists in the file-history module, so a file changed by `sed -i`, a heredoc, `>` redirection, `cp`, `mv`, or any other shell means is neither backed up nor restored.

Concrete consequence for this repo: under bypass-permissions mode the harness instructs the agent to make file changes through Bash rather than through Edit/Write. That instruction and file checkpointing are mutually exclusive — a session following it produces edits that `/rewind` cannot undo, while the same session's conversation restore still succeeds, leaving files ahead of the transcript. The `[may-rewind]` marker in `sys_prompt/alan-default-next.md` (`# Tone markers`) tells an agent the user may drop an exchange from its context; it deliberately carries none of these mechanics, so this note is the only place the restore boundary is written down.

> **Citations below are pinned to 2.1.235.** `/repos/claude-code-decompiled` now
> holds a re-extraction of 2.1.269 in an unrelated chunk-file layout, so every
> `src/globals/*.js:<line>` reference below — including `src/_entry.js`, cited
> as the export table (that role is now `defs.tsv` at the repo's root) —
> resolves to nothing. To re-resolve one, see that repo's README,
> "Re-resolving an old citation."

## Evidence (source, 2.1.235)

The file-history engine is `src/globals/10.js:17732-18800`. Readable names from the export table at `src/_entry.js:4436-4447` (`fileHistoryTrackEdit → _ht`, `fileHistoryMakeSnapshot → zJe`, `fileHistoryRewind → mFn`).

Backups are per-file copies under `~/.claude/file-history/<sessionId>/`, named `sha256(path)[0:16]@v<version>` — `src/globals/10.js:18281-18283`, `18306-18309`, created by `copyFile` at `18344-18387`. No git, no stash, no diff log.

Only files in `trackedFiles` are ever snapshotted or restored:

- The set is added to in exactly one place, the `'track'` reducer op — `src/globals/10.js:17744`.
- `'track'` ops come only from `_ht` — `src/globals/10.js:17928`.
- `_ht` has four call sites: Edit (`src/globals/10.js:20246`), Write (`src/globals/10.js:20504`), NotebookEdit (`src/modules/KFn.js:375`), and a simulated `sed -i` (`src/globals/20.js:14225`).
- The per-user-turn snapshot iterates the tracked set only — `src/globals/10.js:17948`. There is no `readdir` or glob in the module.
- Bash dispatches a `'touch'` op after non-read-only runs (`src/modules/Cae.js:794-797`), and `'touch'` only increments a counter (`src/globals/10.js:17830-17835`).

The product surface says the same thing: `' Rewinding does not affect files edited manually or via bash.'` — `src/globals/26.js:12014`.

### The `sed -i` exception does not apply under bypass permissions

`_simulatedSedEdit` is stripped from the model-facing schema (`src/modules/Cae.js:372-379`) and populated only by the permission-preview builder `h3a` (`src/globals/15.js:7377-7382`), reachable only from the `case 'ask':` branch of the permission flow (`src/globals/26.js:37703`). An auto-approved command never enters that branch, so the raw `sed` runs untracked. The detector also accepts only a single-command `sed -i 's/PAT/REP/flags' FILE` (`src/globals/15.js:5990-6070`).

## Restore modes

`'both' | 'conversation' | 'code'`, built at `src/globals/26.js:11705-11748`; code restore is offered only when `filesChanged.length > 0` (`src/globals/26.js:11921`). Non-interactive equivalents: `--rewind-files <user-message-uuid>` (`src/globals/28.js:33075-33349`) and the SDK `rewind_files` control request (`src/modules/rys.js:743-748`).

## Other exclusions

- Feature gate `kz()` — `src/globals/10.js:17865-17873`: off in remote/cloud workspaces; needs `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING` in SDK mode; honors `CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING`.
- Symlinks, hard-linked files (`nlink > 1`), and files whose parent directory moved are refused and counted as `skippedLinks` — `src/globals/10.js:18389-18448`.
- Snapshot cap is 100 (`src/globals/01.js:5978`, applied at `src/globals/10.js:17808`).
- Files outside the project root are **not** excluded — `src/globals/10.js:18594-18599`. Gitignore has no interaction; there is no file-size limit in the backup path.
- Nothing in the restore path (`src/globals/10.js:18123-18205`) touches processes, packages, or environment. Commits, pushes, installed packages, and background processes survive a rewind.

## Not determined

Whether the `sed -i` interception can also fire outside the `'ask'` permission branch; not every permission entry point reaching `Iqn` was enumerated. Immaterial to the conclusion here, since bypass-permissions auto-approval skips that branch either way.

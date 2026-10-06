# `switchModelsOnFlag`: the refusal-fallback dialog writes user settings through the symlink

Observed 2026-10-06 on Claude Code **2.1.289**, during the post-upgrade check
(`update-claude-code` step 14). `/repos/claude-config/settings.json` — the target of
`~/.claude/settings.json`'s symlink — had gained one line, `"switchModelsOnFlag": true`,
appended after `theme` at 17:23:42, 67 seconds before the checking session started; the
worktree's tracked copy lacked it. The §3.1 symlink row's check (`git diff settings.json`
in the canonical checkout after a new build's launch) is what surfaced it. Decision the
same day: keep `true`, track it, govern it here.

## What wrote it

Not a migration: `~/.claude.json` `migrationVersion` was already 14 (`xo = 14`,
`src/chunk-ya33qr7x.js:1085`). The writer is the refusal-fallback preference dialog.

- Gate (`src/chunk-xy34qwnq.js:3790`): a main thread with no `agentId`, while
  `Yo("switchModelsOnFlag", !0).source === "default"` — the key set nowhere — and
  `userSettings` among the loaded sources, plus five more terms. One answer ends it for
  good: the next launch finds a source.
- Writer `rfn(e, n, r)` (`src/chunk-gppff98a.js:26474-26480`): emits
  `tengu_refusal_fallback_setting_changed` `{enabled, via}` and calls
  `_n("userSettings", { switchModelsOnFlag: e })` — the validated-object `JSON.stringify`
  path (`src/chunk-3z4drmxy.js:3720-3735`), which follows the symlink. Also reached from the
  `/config` row (`src/chunk-s71n76sd.js:493-510`: id `switchModelsOnFlag`, options
  `MY.switchAutomatically`/`MY.askEachTime`; `coerce` accepts `true`/`1`/`on`/`yes`).
- Schema (`src/chunk-q75vj0vh.js:6116`): `switchModelsOnFlag: () =>
  M().optional().describe("When safeguards flag a message, automatically switch to a
  different model to keep chatting. When off, your session will pause instead.")`.
  Declaration rank 164 of 182, after `theme` (156), so the append left the file in cc's
  order (`settings-order.py`: 25 keys in schema order).

## What the key does

- `J$o()` (`src/chunk-gppff98a.js:26236`) = `qN() && value && Xa() && !c7()`; `qN()`
  (`:26233`) = `!a.CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK && !Y8()`. The environment variable
  is the kill switch over the whole fallback, key or no key.
- `dfn(e)` (`:26746-26753`) names why a switch proceeds without asking, in order:
  `silent_ab`, `subagent`, `no_dialog_host`, then `setting` when the key is `true`, then
  `no_consumer_capability`. The key decides only on an interactive main thread that could
  have shown a dialog; a subagent, or a session with no dialog host, is classified before
  it is read.
- `mFo(e)` (`:26755`) and `_5n()` (`:26758`) test `=== !1`: the "pause" branch is the
  explicit `false`, which the `/config` row writes as `MY.askEachTime`.

## Not established

- Whether a bypass-mode session reaches this path. `claude.sh` sessions send no
  `safeguards` request field (this session's first main request,
  `~/.claude/requests-log/2704aba9-bebe-46e1-890e-3161c4f2a000/0003.json`; the skill's §4
  records the same for the `opus-5/bypass-permissions` capture); whether the flag that
  triggers the fallback depends on that field is unread.
- Which model the fallback picks — `fallbackModel`, a parameter of `za()`
  (`src/chunk-xy34qwnq.js:3795-3800`) — is unread.
- The Notification type `model_refusal_fallback` (new in the 2.1.282–2.1.287 window) is
  declared and not wired in `settings.json` `hooks.Notification`, so with `true` a switch
  sends no push.

## Consequence for this repo

The key is tracked so the dialog cannot return: deleting it, or discarding the canonical
checkout's own write before the commit carrying the key is merged there, restores
`source === "default"` and the dialog on the next interactive launch. The §3.1 symlink row
of `.claude/skills/update-claude-code/SKILL.md` names the dialog among the user-settings
writers; root `CLAUDE.md` points the key here.

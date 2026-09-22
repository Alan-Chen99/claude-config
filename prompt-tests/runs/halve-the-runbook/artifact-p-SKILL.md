---
name: update-claude-code
description: Use when Claude Code has been upgraded and this repo must be re-checked, or when a session reports an env-context drift note or an unresolvable `chunk-*.js:LINE` citation. ALSO read BEFORE editing any file that names a Claude Code hook field, env var (`CLAUDE_CODE_*`), settings key, hook event, tool name, JSONL record or attachment type, statusline field, CLI flag, or decompiled-source line — however small the edit: that code is version-coupled and belongs in §3's inventory.
---

# Updating after a Claude Code release

## Overview

Claude Code is a moving dependency this repo reads, imitates and cites, and an upgrade breaks it
**silently**: `serde` ignores unknown keys, pydantic models are `extra: "allow"`,
`statusline.sh` defaults every missing field to `0`, and the one test that re-derives a constant
from the decompile `skipif`s itself away when the decompile is absent. Grepping the old version
string turns up stale *references*, not a code path whose input shape moved underneath it.

**Core principle: a check that cannot fail is not a check.** §2 says what each check is blind to.

## Add to this file as you build

Anything you write that reads a Claude Code data shape, env var, hook field, settings key, tool
name, log-record type or source line goes into §3 in the same change — a coupling nobody recorded
is a coupling nobody re-checks. Re-check the ranges §3 already cites into that file too: they point
at this repo's own source, which `citecheck.sh` never scans, so an edit above a cited line moves it
silently.

## 1. The runbook, in order

Ordering is load-bearing — each step's reason is why it sits where it does.

| # | Step | Command | Why here |
|---|---|---|---|
| 1 | Confirm the new version | `claude --version` | Everything below compares against it. |
| 2 | Re-extract the decompile | in `/repos/claude-code-decompiled`: `npm run extract && npm run link && npm run typecheck` (`npm install` once first) | Hashes **and** line numbers rotate every build; before this, step 7 and `tests/test_model_visibility.py` pass vacuously. `extract` empties the tree first. |
| 3 | Confirm the decompile matches | `grep -m1 -oP '(?<=VERSION: ")[^"]+' /repos/claude-code-decompiled/src/cli.js` | The one stable filename across the 2.1.269 layout change. Must equal step 1. |
| 4 | Read upstream's own release notes | `.claude/skills/update-claude-code/changelog.py <previous version>` | Shipped in the binary; they name the *reason* behind a diff nothing else explains. Needs step 2. |
| 5 | Re-sync the editable venv — **canonical checkout only** | from `/repos/claude-config`: `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config uv sync --reinstall-package claude-config` | The venv `check-env-context.sh` loads; the package version never bumps. From a worktree this repoints the shared venv and breaks other sessions — worktrees use their own via `.envrc`. |
| 6 | Check, then re-pin, env-context | `./scripts/check-env-context.sh` → review the `+`/`-`/`~` diff → `--update` | The best summary of what changed in cc's `# Environment` block; `--update` overwrites it. |
| 7 | Resolve every source citation | `bash .claude/skills/update-claude-code/citecheck.sh` | ~137 citations tracked, 2 covered by a test. Exit 1 names the unresolved, 2 means no tree or a collapsed scan. |
| 8 | Rebase the upstream-derived prompts | `python3 scripts/check-prompt-upstream.py`, then the section-key diff it does not do | Borrowed passages go stale unsignalled (§3.1). Needs step 2's tree; `sys_prompt/CLAUDE.md`, "Rebasing on an upstream release", governs. |
| 9 | Rebuild and test | `cd agent-tools && cargo build --release && cargo test --release`; `uv run pytest tests/ -q`; `./scripts/check-prompt-coupling.sh` | |
| 10 | Check the renderer against real logs | `ls -t /root/.claude/projects/*/*.jsonl \| head -8 \| uv run cc-render-coverage --quiet` | New record and attachment shapes land here first. |
| 11 | Re-capture the system-prompt snapshots | see `docs/system-prompt-snapshot/README.md` "Regenerating" | Needs an authenticated `claude` (`CLAUDE_CODE_OAUTH_TOKEN` is stripped from tool subprocesses; else `~/.claude/.credentials.json`). Never two at once. |
| 12 | Read the capture in full | `git diff docs/system-prompt-snapshot` | Descriptions **and input schemas** move, and nothing else here reads them. |
| 13 | Re-derive what the fired checks were premises *for* | for each premise a check falsified, `git grep` its wording across tracked files | Steps 6, 8 and 12 only repair conformance; artifacts resting on the falsified premise stand, and its expiry is invisible from inside them. Name and re-derive each. |
| 14 | Merge and reinstall | merge to `/repos/claude-config`, then `install.sh` **there only** | Until the merge, `agent-tools` and `cc-pretty` still run the old code; `install.sh` from a worktree breaks every other session. |

Clean output as of 2.1.269: `OK: env-context field set matches…` / `OK: 14 borrowed passages still
match…` / no citecheck output / `449 passed` / 15 cargo binaries `ok` / `prompt coupling OK` /
`8 file(s) checked: clean`. Steps 5 and 14 repoint shared installs and belong in
`/repos/claude-config`; the rest belong in a worktree, since steps 6 and 9 rewrite tracked files.

**When a check fails.** A named citation means the decompile moved under it: re-find the code by
string marker (as `tests/test_model_visibility.py:192-200` does — names rotate, markers survive),
rewriting the citation rather than deleting it. A `test_denylist_still_matches_the_conversion_source`
failure means a release changed which attachment arms return empty — re-derive the set, don't edit
the assertion.

## 2. What each check does NOT cover

This table is the point of the skill. A green run above still leaves all of this open.

| Check | Blind to |
|---|---|
| `check-env-context.sh` | Anything outside a ±1000-byte window around `Primary working directory: ` plus three string counts. It sees the field set, not behaviour — and a clean match is equally what redundancy looks like. |
| `citecheck.sh` | Whether the cited line still says what the citing text claims: it proves only that the file exists and is long enough — five same-repo citations were stale while all resolved. Citations into this repo's own files it never sees, and only string pinning would. |
| `cc-render-coverage` | The default view's **selection**: needles come only from `assistant`/`user` records, so a dropped record is invisible — extending it is what would have caught the skeleton-renderer bug. |
| `pytest` | Every citation but two: `_NEVER_VISIBLE_ATTACHMENT_TYPES` and `_HOOK_STDOUT_VISIBLE_EVENTS`, re-derived by string marker in `tests/test_model_visibility.py` — and both `skipif` away when the decompiled tree is absent, reporting success by not running. |
| `check-prompt-coupling.sh` | Claude Code entirely; it greps this repo against itself. |
| `check-prompt-upstream.py` | Everything upstream says that this repo never copied; it re-checks 15 borrowed passages, and reports that a count moved, not which copy did. |
| `changelog.py` | Anything upstream didn't write down, and releases older than the binary's window (15 entries in 2.1.269). Neither the running version nor a release without user-facing notes has an entry, so a gap proves nothing. |
| The capture diff (step 12) | Every key in this repo's own `settings.json`: `capture.py:471` passes `--setting-sources project,local`, dropping `userSettings` (`chunk-3vd4nzwp.js:8440-8442`), and this file installs at user scope, so no capture confirms a key takes effect. Deferred tools appear as names only. And it is one environment on one day — `act_dont_rederive` vanished between the 2.1.235 and 2.1.269 captures while present in both binaries. |
| CI | Everything. `skills-test.yml` runs only `skills/scripts/` tests, only on `skills/scripts/**` paths. |

## 3. The coupling inventory — what an upgrade can break

### 3.1 Degrades silently (no error, wrong behaviour)

| Where | Reads | Failure mode |
|---|---|---|
| `agent-tools/src/hook_input.rs:13-35` | `session_id`, `tool_name`, `tool_input`, `tool_use_id`, `hook_event_name`, `tool_response` | The parse fails; `hook_pre.rs:14-19` passes through, `hook_post.rs:46-51` returns `Ok(())`, wrapping stops. |
| `agent-tools/src/hook_post.rs:118-172` | `backgroundTaskId`, `backgroundedByUser`, `backgroundedByTurnAbort`, `backgroundedToDeliverMessage`, `timedOutAfterMs`, `run_in_background` | A rename yields `Cause: not stated by the tool response`, not an error; the Bash output schema (`chunk-dbb93264.js:215699-215703`) names no other cause field. |
| `agent-tools/src/hook_post.rs:22` | `REPORT_BUDGET = 9_000` | Sized against the 8,000-char `additionalContext` cap, which sanitizes cloud-runner stdout (`ego`, `chunk-dbb93264.js:48303`) but not a local hook's (`gwe`, `:227133`). Sanitize local hooks and reports become stubs. |
| `agent-tools/src/hook_pre.rs:22`, `hook_post.rs:57` | tool names `Bash`, `Monitor` | A renamed or new shell tool is simply not wrapped. |
| `agent-tools/src/paths.rs:66-105` | `CLAUDE_CODE_SESSION_ID` (`:105`) | A rename breaks bare `!` commands. |
| `skills/telegram-hitl/SKILL.md:74`, `:206` | `CLAUDE_CODE_SESSION_ID`; the tool name `Monitor` | A rename sends an empty `X-Session-Id`: the log shows a send happened, not who (`tests/test_telegram_hitl_skill.py:123` pins prose only). A renamed `Monitor` strands the skill's only answer for unsolicited input. |
| `statusline.sh:5-19` | `.model.display_name`, `.context_window.*`, `.cost.total_cost_usd`, `.workspace.current_dir`, `.transcript_path`, `.session_id` | Every field defaults, so a rename shows zeros — except `.session_id` (`:19`), which `agent-tools ps --format statusline` scopes to, blanking the open-tasks row. 2.1.269's `prompt_cache` and `rate_limits.spend_limit` go unread. |
| `src/claude_config/cc_pretty/parse.py:28`, `:188-375` | record `type` values | New fields are safe (`extra: "allow"`); a renamed record type becomes `UnknownRecord` and vanishes from the render. |
| `settings.json:19-50` | `Notification` matchers `permission_prompt`, `idle_prompt`, `elicitation_dialog`, `elicitation_url_dialog`, `quota_auto_resume_fired`, `quota_auto_resume_stale`, `quota_auto_resume_disabled` | Unanchored regexes (`chunk-dbb93264.js:227871`), so `permission_prompt` also catches `worker_permission_prompt` — wanted, and unstated in the file. Of the 16 declared (`VAr`, `chunk-70hqkjxq.js:12`, plus two in `chunk-c29sfp49.js:76`), these seven mean the session is blocked on the human or stalled. `agent_needs_input`/`agent_completed` were excluded when nothing could background — expired, §4. |
| `sys_prompt/alan-default-next.md`, the `Default subagents to the foreground` bullet | the Agent tool's `run_in_background` property, and `q4o`'s last term `!s && r !== !1` (`chunk-dbb93264.js:103955`) | Unenforced since the `Agent` `PreToolUse` hook was removed (2026-09-16); the model complies per call. Drop the property from the schema again — its gate `rc() \|\| Z8()` (`chunk-dbb93264.js:171779`) is false only because `CLAUDE_CODE_FORK_SUBAGENT=0` — and subagents background silently. Check `prompt-tests/general/subagent-foreground-default`. |
| `settings.json:116-127` | `PostToolUseFailure` | Folded back into `PostToolUse` and errored calls stop being delivery points. |
| `sys_prompt/alan-default-next.md`, and any `agents/*.md` named after a built-in agent | passages copied verbatim from cc's own system prompt | `--system-prompt-file` drops every upstream section, so a reworded rule never arrives and the copy keeps the old text. `sys_prompt/CLAUDE.md` governs. |
| `scripts/claude.sh:13` | `CLAUDE_CODE_DISABLE_AGENT_VIEW=1` | Without it an agent-view fork drops `--system-prompt-file` and silently runs the stock prompt. |
| `scripts/intercept/proxy.py:28`, `:82-88` | the `x-claude-code-session-id` header; `sessionId`/`pid`/`cwd`/`kind`/`entrypoint` in `~/.claude/sessions/*.json` | A renamed header files every capture under `requests-log/unknown/`; a renamed session field drops that key. Plain `.get()` misses — captures stay written, anonymous. |
| `scripts/claude.sh:45`, `scripts/prompt-test-cc-leg2.sh:73` | the system prompt and tool definitions a conversation recorded on its first request | Since 2.1.267 a resume replays that record, not the command line (`GWe`, `chunk-dbb93264.js:130178`; `Mos`, `:130134`). Only the leg-2 runner passes `--system-prompt-snapshot off`, which bypasses it; elsewhere, edit prompts in a fresh session. |
| `settings.json` `includeGitInstructions: false`, `attribution.commit/pr: ""` | one gate, `q7()` (`chunk-dbb93264.js:69382`), removing the Bash tool's `# Git` block, cc's `gitStatus` reminder and the attribution reminder | Rename the key or stop gating on it and `Commit or push only when the user asks…` returns beside the prompt's own `# Git` section, contradicting it. A live `claude.sh` Bash description and `prompt-tests/general/commit-own-changes` answer it (no capture can); `sys_prompt/CLAUDE.md` governs. |
| `settings.json:4-6` (`env`) | which settings scope may set which environment variable | 2.1.251 stopped a project-level `env` from setting `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_TMPDIR` or `TMPDIR`/`TMP`/`TEMP`. This file is user-scope, so unaffected; a project copy would be ignored silently. |

### 3.2 Mirrors of cc's own algorithms — re-read the source, don't just test

`src/claude_config/env_context/` reimplements cc behaviour. `environment.py`: `resolve_shell` ≙
`das()`, `_executable` ≙ `cbt()` (incl. the `--version` fallback that makes a bare
`CLAUDE_CODE_SHELL=bash` resolve), `worktree_common_dir` ≙ `pP()`, `git_snapshot` ≙ `ADe()`
(`chunk-dbb93264.js:69331-69369`: `status --short --ignore-submodules=dirty`, `log --oneline -n 5`,
a 2000-character cap, replacing the `gitStatus` reminder `includeGitInstructions: false` removes).
`scratchpad.py:22-54`: the path algorithm, incl. the 200-char slug limit past which cc appends a
hash and this module raises. `render.py:43-61`: `STASH_CAUTION`, verbatim from cc's `KUt`, pinned by
`check-prompt-upstream.py`. `drift.py:42-46`: anchor and window constants. `drift.py:187-208`: a
timeout budget whose comment says to re-check the sum if any of its three numbers moves.

Two unset knobs would each void a claim above: `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` (2.1.257) forces
one model on every subagent, voiding every `model:` in `agents/*.md`; `CLAUDE_CODE_ENABLE_TODO_TOOLS`
(2.1.268) restores the task-tracking tools.

### 3.3 Pins to re-pin vs. records to leave alone

**Re-pin:** `docs/env-context-manifest.json` (version, 24 window literals, 3 required-literal counts)
via `--update`, which refuses to write a count of 0 — a zero is a permanently-passing assertion.

**Re-verify, keep the label:** the version banners in `docs/system-prompt-anatomy*.md`,
`docs/tool-token-limits.md`, `docs/background-sessions.md`, `docs/system-prompt-snapshot/README.md`,
`skills/cc-history/SKILL.md`, `output-styles/README.md`, `agent-tools/CLAUDE.md`,
`docs/agent-tools-status-reference.md`, and `scripts/intercept/README.md`'s first-byte-watchdog
window — if that number moves, an intercepted session's turns start aborting at the new one.

**Do NOT re-pin — dated records of an older build; rewriting them destroys the evidence:** `notes/`,
`plans/`, `docs/superpowers/plans/`, `specs/`; the synthetic version strings in
`tests/test_env_context.py` and `tests/test_model_visibility.py`; `docs/system-prompt-snapshot/**`;
`prompt-tests/runs/**`.

### 3.4 Snapshot-capture mechanics that break on upgrade

`capture.py`: the trust-dialog cursor reader (`:351-369` — its default already flipped once between
2.1.235 and 2.1.269), the main-request selector (`:596-606`), the `cc_is_subagent=true`
billing-header marker (`:611-624`); `regenerate.py:261-266` excludes the `defer_loading` placeholder.
`render_capture.py` derives `prompt.md` and `tools/` from each `request.json`;
`tests/test_snapshot_rendering.py` re-renders all 13 captures and fails
when tracked files drift, so a hand-edited capture is caught rather than read as evidence. Every
character count and `system_tokens` figure in `README.md` and `what-the-model-gets.md` derives from
these files — re-derive, don't adjust by hand.

## 4. Still to check — as of 2026-09-12, Claude Code 2.1.269

Delete an entry when it closes; add one when you find a gap. Pins not re-derived for this build
announce themselves where they sit: `env-context-manifest.json:3` (2.1.235 offsets; `notes/env-context-manifest.md`), the **Not
re-verified this round** blocks in the snapshot README, `builtin-output-styles/` (v2.1.87, missing
2.1.257's `Proactive`).

- Uncaptured: the configuration this repo runs. `claude.sh` passes `--dangerously-skip-permissions`
  while every capture takes the default mode; `regenerate.py`'s `bypass-permissions` variant defines
  it, and 2.1.257 made `defaultMode: "bypassPermissions"` ignored from project settings. No
  backgrounded-session capture either, and two checks dropped at a `/compact`: the Auto Mode reminder
  under `capture.py`, and `/feedback` from an interactive login. The unexplained divergence row in
  `sys_prompt/CLAUDE.md` stays open too.
- "The kill boundary" in `agent-tools-status-reference.md`: 2.1.257 fixed `setsid`-detached commands
  surviving a task stop or exit. Task-stop is measured there; the exit half needs a human —
  `run --background sleep 900`, quit, check the child.
- `docs/tool-token-limits.md`: a 2.1.88 banner knowing neither 2.1.261's
  `bashOutputMaxChars`/`taskOutputMaxChars` (128K) nor 2.1.265's 1 GB disk cap.
- `cc_pretty/` against 2.1.251-259: progress ticks replace rather than accumulate, async hook notices
  batch onto one line, nested background results land in the **parent subagent's** transcript.
  Re-read real logs.
- Whether `agent_needs_input`/`agent_completed` fire now that subagents background again — they were
  excluded when nothing could. Background one, watch for `agent-tools ntfy-hook`.
- Pre-existing, absent from the 2.1.235 capture too: `agents/*.md` and ~30 sites under
  `skills/scripts/` name `Grep`, `Glob`, `TodoWrite` and `Task`; the live roster has none.
  `TodoWrite` is a settings decision (`CLAUDE_CODE_ENABLE_TODO_TOOLS=1`); the rest are text edits.

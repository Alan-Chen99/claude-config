---
name: update-claude-code
description: Use when Claude Code has been upgraded and this repo must be re-checked, or when a session reports an env-context drift note or an unresolvable `chunk-*.js:LINE` citation. ALSO read BEFORE editing any file that names a Claude Code hook field, env var (`CLAUDE_CODE_*`), settings key, hook event, tool name, JSONL record or attachment type, statusline field, CLI flag, or decompiled-source line — however small the edit; that code is version-coupled and belongs in §3.
---

# Updating after a Claude Code release

## Overview

Claude Code is a moving dependency this repo reads, imitates and cites. An upgrade breaks
things **silently**: `serde` ignores unknown keys, pydantic models are `extra: "allow"`,
`statusline.sh` defaults every missing field to `0`, and the one test that re-derives a
constant from the decompiled source `skipif`s itself away when the decompile is absent.
Nothing fails loudly. You have to go looking.

**A check that cannot fail is not a check.** §1 is what to run, §2 what each run cannot
see. Read §2 before trusting any green result.

**Add to this file as you build.** Anything you write that reads a Claude Code data shape,
env var, hook field, settings key, tool name, log-record type or source line goes into §3
in the same change. Then re-check the line ranges §3 cites into the file you edited: they
point at this repo's own source, which no checker reads (§4).

## 1. The runbook, in order

Steps 5 and 14 repoint shared installs and must run in the canonical checkout
`/repos/claude-config` — from a worktree they break every other session. The rest belongs
in a worktree, since steps 6 and 9 rewrite tracked files.

| # | Step and command | Why here |
|---|---|---|
| 1 | `claude --version` | Everything below compares against it. |
| 2 | In `/repos/claude-code-decompiled`: `npm run extract && npm run link && npm run typecheck` (`npm install` once first) | Chunk hashes **and** line numbers rotate every build; every check below reads the new tree. `extract` empties `src/`, `assets/`, `native/` first, so dropped modules disappear on their own. |
| 3 | `grep -m1 -oP '(?<=VERSION: ")[^"]+' /repos/claude-code-decompiled/src/cli.js` | `src/cli.js` is the one filename stable across the 2.1.269 layout change. Must equal step 1. |
| 4 | `.claude/skills/update-claude-code/changelog.py <previous version>` | Names the *reason* behind a diff nothing else here can: 2.1.269's `Agent` schema change traces to 2.1.251 making `CLAUDE_CODE_SUBAGENT_MODEL` a default, not an override. Needs step 2. |
| 5 | From `/repos/claude-config`: `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config uv sync --reinstall-package claude-config` | A stale install loads the old `drift.py`; `--reinstall-package` is needed because the package version never bumps. Worktrees use their own venv via `.envrc`. |
| 6 | `./scripts/check-env-context.sh`, read the `+`/`-`/`~` diff, then `--update` | The best summary of what changed in cc's `# Environment` block. Re-pin only after reading: `--update` overwrites the evidence. |
| 7 | `bash .claude/skills/update-claude-code/citecheck.sh` | Exit 0 = every `chunk-*.js:LINE` citation resolves; 1 = the unresolved are named; 2 = no decompiled tree, i.e. step 2 was skipped. |
| 8 | `python3 scripts/check-prompt-upstream.py`, then the section-key diff it does not do | `sys_prompt/` replaces cc's system prompt wholesale and the hook renders its own env block, so passages copied from either go stale unsignalled. Not total: Anthropic's wording still arrives through `messages[]`, which nothing here reads. `sys_prompt/CLAUDE.md` governs. Needs step 2. |
| 9 | `cd agent-tools && cargo build --release && cargo test --release`; `uv run pytest tests/ -q`; `./scripts/check-prompt-coupling.sh` | |
| 10 | `ls -t /root/.claude/projects/*/*.jsonl \| head -8 \| uv run cc-render-coverage --quiet` | New record and attachment shapes land here first. |
| 11 | Re-capture snapshots — `docs/system-prompt-snapshot/README.md`, "Regenerating" | Needs an authenticated `claude`: `CLAUDE_CODE_OAUTH_TOKEN`, stripped from tool subprocesses, or a token in `~/.claude/.credentials.json`. Needs any checkout's venv too (`mitmdump` is a project dependency). Never two `regenerate.py` at once — they share `capture-output/` and `~/.claude/requests-log/`. |
| 12 | `git diff docs/system-prompt-snapshot` | Read every configuration and tool file through: input schemas move independently of descriptions, and the 2.1.269 pass filed `Agent` as unchanged by comparing `description` alone. |
| 13 | For each premise a check above falsified, `git grep` its wording across tracked files | Steps 6, 8 and 12 falsify premises, but their remedies only repair conformance: artifacts built on the old premise stay standing, and the expired part is their rationale. Re-derive or retire each. |
| 14 | Merge to `/repos/claude-config`, then `install.sh` **there only** | Until the merge, `~/.local/bin/agent-tools` and `cc-pretty` still run the old code. |

Clean output as of 2.1.269: `OK: env-context field set matches the installed binary` /
`OK: 14 borrowed passages still match Claude Code 2.1.269` / no citecheck output / `449 passed` /
15 cargo test binaries `ok` / `prompt coupling OK` / `8 file(s) checked: clean`.

**When a check fails.** `check-env-context.sh` `+`/`-`/`~`: diff against
`src/claude_config/env_context/render.py` before `--update`. `citecheck.sh` naming a citation:
re-find the code by string marker (technique at `tests/test_model_visibility.py:192-200`; names and
hashes rotate, markers survive) and rewrite the citation, don't delete it. `cc-render-coverage`
`missing_content`: an unmodelled record shape; `renderer_truncation`: a hardcoded cap ignoring
`--tool-max`. `pytest` failing `test_denylist_still_matches_the_conversion_source`: a release
changed which attachment arms return empty — re-derive the set, don't edit the assertion.

## 2. What each check does NOT cover

This table is the point of the skill. A green run above still leaves all of this open.

| Check | Blind to |
|---|---|
| `check-env-context.sh` | Anything outside a ±1000-byte window around `Primary working directory: `, plus three whole-binary string counts. It sees the field set, not behaviour — and not whether the mirror is still wanted, since cc delivering the same block itself also reads `OK`. |
| `citecheck.sh` | Whether the cited line still says what the citing text claims: it proves only that the file exists and is long enough, so a stale tree passes whole. It reads only `chunk-*.js:LINE`; same-repo citations are checked by nothing. Below 100 citations it exits 2. |
| `cc-render-coverage` | The default view's **selection**. It renders with `show_all` and draws needles only from `assistant`/`user` records, so it cannot see a record being dropped. |
| `pytest` | Every citation but two. `tests/test_model_visibility.py` re-derives `_NEVER_VISIBLE_ATTACHMENT_TYPES` and `_HOOK_STDOUT_VISIBLE_EVENTS` by string marker, and both `skipif` when `/repos/claude-code-decompiled/src` is absent — reporting success by not running. |
| `check-prompt-coupling.sh` | Claude Code entirely. It greps this repo's own files against each other. |
| `check-prompt-upstream.py` | Everything upstream says that this repo never copied: it re-checks 15 borrowed passages, so a section a release adds is invisible. Where a passage recurs it reports that the count moved, not which copy. |
| `changelog.py` | Anything upstream chose not to write down, and every release older than the binary's window (15 entries in 2.1.269, back to 2.1.247). The running version has no entry, nor does a release with no user-facing notes — so a gap proves nothing. |
| The capture diff (step 12) | Every key in this repo's own `settings.json`: `capture.py:471` passes `--setting-sources project,local`, dropping `userSettings` (`rWn`, `chunk-3vd4nzwp.js:8440-8442`), while `install.sh` installs at user scope. No capture can confirm a key here still takes effect. The 18 deferred tools appear only as names plus one `DeferredToolPlaceholder`. And it is one environment on one day: most sections sit behind a server-resolved flag, so absence is not removal (`act_dont_rederive` vanished between the 2.1.235 and 2.1.269 captures while staying in both binaries). |
| CI | Everything. `.github/workflows/skills-test.yml` runs only `skills/scripts/` tests, only on `skills/scripts/**` paths. |

## 3. The coupling inventory — what an upgrade can break

### 3.1 Degrades silently (no error, wrong behaviour)

Unless a row says otherwise the failure is the same: the name is not found, the reader falls
back to a default or a no-op, nothing errors.

| Where | Reads | Failure mode |
|---|---|---|
| `agent-tools/src/hook_input.rs:13-35` | `session_id`, `tool_name`, `tool_input`, `tool_use_id`, `hook_event_name`, `tool_response` | A renamed field fails the parse; `hook_pre.rs:14-19` allows passthrough and `hook_post.rs:46-51` returns `Ok(())`. Wrapping stops happening. |
| `agent-tools/src/hook_post.rs:118-172` | `backgroundTaskId`, `backgroundedByUser`, `backgroundedByTurnAbort`, `backgroundedToDeliverMessage`, `timedOutAfterMs`, `run_in_background` | Yields `Cause: not stated by the tool response`. These replace `assistantAutoBackgrounded` (deleted in 2.1.269); the Bash output schema (`src/chunk-dbb93264.js:215699-215703`) declares no other cause field. |
| `agent-tools/src/hook_post.rs:22` | `REPORT_BUDGET = 9_000` | Deliberately over the 8,000-char/200-line `additionalContext` cap, which sits on `ego` (`src/chunk-dbb93264.js:48303`, `:49123`) but not on `gwe` (`:227133`), where a local command hook's stdout is parsed unsanitized. Sanitize local hooks and reports truncate to a stub. |
| `agent-tools/src/hook_pre.rs:22`, `hook_post.rs:57` | tool names `Bash`, `Monitor` | A renamed or new shell tool is not wrapped. |
| `agent-tools/src/paths.rs:66-105` | `CLAUDE_CODE_SESSION_ID` (at `:105`) | Breaks bare `!` commands. |
| `skills/telegram-hitl/SKILL.md:74`, `:206` | `CLAUDE_CODE_SESSION_ID`; the tool name `Monitor` | Empty `X-Session-Id`: the channel log records that a send happened, not who made it, and the send still succeeds. `tests/test_telegram_hitl_skill.py:123` pins the spelling in prose only. A renamed `Monitor` leaves the skill's only answer for unsolicited input pointing at nothing. |
| `statusline.sh:5-19` | `.model.display_name`, `.context_window.*`, `.cost.total_cost_usd`, `.workspace.current_dir`, `.transcript_path`, `.session_id` | Fields default (`// 0`, `// "?"`, `// empty`), so a rename shows zeros — except `.session_id` (`:19`), which `agent-tools ps --format statusline` scopes to, where it blanks the open-tasks row. 2.1.269 also supplies `prompt_cache` and `rate_limits.spend_limit`, unread here. |
| `src/claude_config/cc_pretty/parse.py:28`, `:188-375` | record `type` values | `extra: "allow"`, so new fields are safe; a renamed record type becomes `UnknownRecord` and vanishes from the render. |
| `settings.json:19-50` | `Notification` matchers `permission_prompt`, `idle_prompt`, `elicitation_dialog`, `elicitation_url_dialog`, `quota_auto_resume_fired`, `quota_auto_resume_stale`, `quota_auto_resume_disabled` | **Unanchored regexes**, not literals (`src/chunk-dbb93264.js:227871`), so `permission_prompt` also catches `worker_permission_prompt` — wanted, and recorded nowhere else. Declared set is 16: `VAr`'s 14 (`src/chunk-70hqkjxq.js:12`) plus `elicitation_complete`/`elicitation_response` (`src/chunk-c29sfp49.js:76`). These seven are chosen on one rule — notify when the session is blocked on the human or has stopped making progress by itself. |
| `sys_prompt/alan-default-next.md`, the `Default subagents to the foreground` bullet | the Agent tool's `run_in_background` property, and `q4o`'s last term `!s && r !== !1` (`src/chunk-dbb93264.js:103955`) | Nothing enforces the foreground since the `PreToolUse` `Agent` hook was removed on 2026-09-16; the prompt asks, the model complies per call. Drop `run_in_background` from the schema again (the gate is `rc() || Z8()`, `src/chunk-dbb93264.js:171779`, false only via `CLAUDE_CODE_FORK_SUBAGENT=0`) and the bullet asks for a parameter that does not exist. Rewording the parameter's own `.describe()`, which recommends the opposite default, moves compliance silently. Check: `prompt-tests/general/subagent-foreground-default`. |
| `settings.json:116-127` | `PostToolUseFailure` | A distinct event name. Folded back into `PostToolUse` and errored calls stop being delivery points. |
| `sys_prompt/alan-default-next.md`, any `agents/*.md` named after a built-in agent | passages copied verbatim from cc's system prompt | `--system-prompt-file` drops every upstream section, so a rule upstream reworded never arrives and the copy here keeps saying the old thing. `sys_prompt/CLAUDE.md` governs. |
| `scripts/claude.sh:13` | `CLAUDE_CODE_DISABLE_AGENT_VIEW=1` | An agent-view fork drops `--system-prompt-file` and runs the stock prompt. |
| `scripts/intercept/proxy.py:28`, `:82-88` | the `x-claude-code-session-id` header, and `sessionId`/`pid`/`cwd`/`kind`/`entrypoint` in `~/.claude/sessions/*.json` | Renamed header → captures land in `requests-log/unknown/`; renamed session field → that key drops from the log's `session` block. Plain `.get()` misses: the capture is still written, just anonymous. |
| `scripts/claude.sh:45`, `scripts/prompt-test-cc-leg2.sh:73` | the system prompt and tool definitions a conversation recorded on its first request | Since 2.1.267 a resume replays the record, not the command line (`GWe`, `src/chunk-dbb93264.js:130178`; tool definitions too, `Mos`, `:130134`; `--system-prompt-snapshot off` bypasses both), and it is on here. The leg-2 runner passes the flag; elsewhere, exercise a prompt edit in a fresh session. |
| `settings.json` `includeGitInstructions: false`, `attribution.commit/pr: ""` | one gate, `q7()` (`chunk-dbb93264.js:69382`), removing the Bash tool's `# Git` block, cc's `gitStatus` reminder and the attribution reminder | Rename the key, or stop gating the block by it, and `Commit or push only when the user asks. If on the default branch, branch first.` returns beside the `# Git` section of `alan-default-next.md`, contradicting it. Captures cannot answer this (§2, user scope); a live `claude.sh` session's Bash description and `prompt-tests/general/commit-own-changes` can. |
| `settings.json:4-6` (`env`) | which settings scope may set which environment variable | 2.1.251 stopped a project-level `env` from setting `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_TMPDIR` or `TMPDIR`/`TMP`/`TEMP`. This file is user-scope and sets only `CLAUDE_CODE_FORK_SUBAGENT`; a project-level copy adding one would be ignored. |

### 3.2 Mirrors of cc's own algorithms — re-read the source, don't just test

`src/claude_config/env_context/` reimplements cc behaviour and must track it. `environment.py`:
`resolve_shell` ≙ `das()`, `_executable` ≙ `cbt()` (incl. the `--version` fallback that makes a bare
`CLAUDE_CODE_SHELL=bash` resolve), `worktree_common_dir` ≙ `pP()`, `git_snapshot` ≙ `ADe()`
(`chunk-dbb93264.js:69331-69369`: `--no-optional-locks status --short --ignore-submodules=dirty`,
`log --oneline -n 5`, a 2000-character cap; it replaces the `gitStatus` reminder that
`includeGitInstructions: false` removes). `scratchpad.py:22-54`: the path algorithm, incl. the
200-char slug limit past which cc appends a hash this module raises on instead. `render.py:43-61`:
`STASH_CAUTION`, copied verbatim from `KUt` and the only passage the hook still borrows — pinned by
`check-prompt-upstream.py`, since `check-env-context.sh` covers field sets, not wording.
`drift.py:42-46`: anchor and window constants tuned to the binary layout. `drift.py:187-208`: a
timeout budget whose comment says to re-check the sum if any of the three numbers moves.

### 3.2b Knobs unset here, and what each would do if set

| Unset knob | Effect |
|---|---|
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` (2.1.257) | One model for every subagent, ignoring per-spawn and agent-definition overrides — re-breaking what 2.1.251 fixed, silently voiding every `model:` in `agents/*.md`. |
| `CLAUDE_CODE_ENABLE_TODO_TOOLS` (2.1.268) | Restores the task-tracking tools (`TodoWrite`, `TaskCreate/Get/Update/List`), otherwise offered only to older models. |

### 3.3 Pins to re-pin vs. records to leave alone

**Re-pin:** `docs/env-context-manifest.json` (version, 24 window literals, 3 required-literal counts)
via `--update`, which refuses to write a count of 0 — a zero is a permanently-passing assertion.

**Re-verify the claim, keep the label:** version banners in `docs/system-prompt-anatomy*.md`,
`docs/tool-token-limits.md`, `docs/background-sessions.md`, `docs/system-prompt-snapshot/README.md`,
`skills/cc-history/SKILL.md`, `output-styles/README.md`, `agent-tools/CLAUDE.md`,
`docs/agent-tools-status-reference.md`, and the first-byte-watchdog window in
`scripts/intercept/README.md`, "Pass-through streaming" — if that number moves, an intercepted
session's turns start aborting at the new one.

**Do NOT re-pin — dated records of an older build; rewriting them destroys the evidence:**
everything under `notes/`, `plans/`, `docs/superpowers/plans/` and `specs/`; the synthetic version
strings in `tests/test_env_context.py` and `tests/test_model_visibility.py`; the captured artifacts
under `docs/system-prompt-snapshot/**` (regenerated wholesale, never hand-edited);
`prompt-tests/runs/**`.

### 3.4 Snapshot-capture mechanics that break on upgrade

`capture.py`: the trust-dialog cursor reader (`:351-369` — the default already flipped once between
2.1.235 and 2.1.269), the main-request selector (`:596-606`), the `cc_is_subagent=true`
billing-header marker (`:611-624`). `regenerate.py:261-266` excludes the `defer_loading`
placeholder. `render_capture.py` derives `prompt.md` and `tools/` from each `request.json`, and
`tests/test_snapshot_rendering.py` re-renders all 13 captures and fails when the tracked files
drift, so a hand-edited capture is caught rather than read as evidence. Every character count and
`system_tokens` figure in `README.md` and `what-the-model-gets.md` derives from these files:
re-derive, don't adjust by hand.

## 4. Still to check — as of 2026-09-12, Claude Code 2.1.269

Delete an entry when it closes; add one when you find a gap, rather than leaving it in a transcript.

**Pins never re-derived for this build**
- `docs/env-context-manifest.json:3` → `notes/env-context-manifest.md`: byte offsets, four-anchor
  count and the `Shell: PowerShell` probe describe 2.1.235 only.
- `docs/system-prompt-snapshot/README.md`: the two **Not re-verified this round** blocks, under
  "Security-monitor calls" and "Interactive vs `-p` mode differences".
- `docs/system-prompt-snapshot/builtin-output-styles/`: captured from v2.1.87, and 2.1.257 names a
  `Proactive` built-in with no file here — incomplete as well as stale. Retire by re-capturing them.

**Captures not taken**
- The one configuration this repo runs: `scripts/claude.sh` launches
  `--dangerously-skip-permissions` while every capture takes the default mode, so the
  bypass-permissions reminder is in none of them. `regenerate.py`'s `bypass-permissions` variant
  defines it. (Not `auto_mode`'s three texts — a live session log answers `e.bypass` directly; snapshot README, "Removed: the `## Auto Mode Active` reminder".) Second reason, from 2.1.257: `defaultMode: "bypassPermissions"` is now ignored from
  project settings, leaving user settings and `--permission-mode` as its only entry points.
- No backgrounded-session capture for 2.1.269 (`regenerate.py`'s `VARIANTS` has no such key), and
  two live checks dropped at a `/compact` boundary: whether the Auto Mode reminder fires for a
  `capture.py` session, and `/feedback` from an interactively-logged-in session.

**Opened by the release-notes pass, 2026-09-12** — 635 bullets of 2.1.247-2.1.268 read against §3.

| What to re-check | What retires it |
|---|---|
| `docs/agent-tools-status-reference.md` "The kill boundary" | 2.1.257 fixed `setsid`-detached background commands surviving a **task stop** or **Claude Code exit** — what `agent-tools run --background` is built on. The task-stop half is measured there; the exit half needs a human: start `agent-tools run --background sleep 900`, quit Claude Code, check the child. |
| `docs/tool-token-limits.md` | 2.1.261 added `bashOutputMaxChars`/`taskOutputMaxChars` (ceiling 128K), 2.1.265 a 1 GB cap on tool results saved to disk; the file carries a 2.1.88 banner and knows neither. |
| `src/claude_config/cc_pretty/` record handling | Subagent progress ticks now replace their predecessor rather than accumulating (2.1.251); async hook completion notices batch onto one line (2.1.257); nested background subagent results are saved into the **parent subagent's** transcript (2.1.259). Retire by re-reading real logs. |
| `Notification` matchers `agent_needs_input`, `agent_completed` (§3.1) | Left out because nothing could background; the `Agent` `PreToolUse` hook's removal on 2026-09-16 ended that. Retire by backgrounding a subagent deliberately and watching whether `agent-tools ntfy-hook` fires. |

**Open design questions, not defects**
- One passage `alan-default-next.md` borrowed from upstream diverges with no recorded reason — the
  row marked **Not reviewed** under "Deliberate divergences" in `sys_prompt/CLAUDE.md`. It predates
  the 2.1.235 baseline.
- Extending `cc-render-coverage` to see selection defects (§2) is what would have caught the
  skeleton-renderer bug fixed on 2026-09-12.
- Same-repo `file:line` citations have no checker, and line-existence would not have caught the
  2026-09-12 drift: all five stale citations resolved, pointing at real lines of unrelated code.
  Pinning by string, as `check-prompt-coupling.sh` does, is the only mechanism with teeth.

**Pre-existing, not upgrade-caused** (absent from the 2.1.235 capture too — don't re-diagnose as
upgrade fallout): `agents/*.md` and ~30 sites under `skills/scripts/` name `Grep`, `Glob`,
`TodoWrite` and `Task`; the live roster has none. `TodoWrite` is a settings decision (§3.2b); the
rest are text edits, and whether the model reliably maps `Task`→`Agent` is untested.

## Common mistakes

| Mistake | What actually happens |
|---|---|
| Treating a green `cc-render-coverage` as "the renderer is fine" | It never looks at attachment records or at what the default view selects. |
| Grepping for the old version string and calling it done | That finds stale *references*, not a live code path whose input shape changed underneath it — how the skeleton bug (§4) survived a full audit. |
| Re-pinning a `notes/` file to the new version | Destroys a dated record of the older build. Those files are evidence, not documentation. |
| Fixing, committing, and stopping | Nothing you run changes until the merge to `/repos/claude-config` and a rebuild — the installed binary and the editable venv both resolve there, by design. |

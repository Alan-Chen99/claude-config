---
name: update-claude-code
description: Use when Claude Code has been upgraded and this repo must be re-checked, or when a session reports an env-context drift note or an unresolvable `chunk-*.js:LINE` citation. ALSO read BEFORE editing any file naming a Claude Code hook field, env var (`CLAUDE_CODE_*`), settings key, hook event, tool name, JSONL record or attachment type, statusline field, CLI flag, or decompiled-source line — don't skip because the edit looks small; that code is version-coupled and belongs in this skill's inventory.
---

# Updating after a Claude Code release

## Overview

Claude Code is a moving dependency this repo reads, imitates and cites. An upgrade
breaks things **silently**: `serde` ignores unknown keys, pydantic models are
`extra: "allow"`, `statusline.sh` defaults every missing field to `0`, and the one
test that re-derives a constant from the decompiled source `skipif`s itself away when
the decompile is absent. Nothing fails loudly. You have to go looking.

**Core principle: a check that cannot fail is not a check.** Before trusting any
result below, know what it does *not* cover — each entry says so.

## Add to this file as you build

When you write anything that reads a Claude Code data shape, env var, hook field,
settings key, tool name, log-record type, or source line, add it to §3 in the same
change. A coupling nobody recorded is a coupling nobody re-checks; the inventory is
the only reason the next upgrade is a runbook rather than an archaeology dig.

Then re-check the line ranges §3 already cites into the file you just edited. Those
citations point at this repo's own source, not at the decompile, so `citecheck.sh`
never sees them and `check-prompt-coupling.sh` matches literal strings rather than
line numbers — an edit above a cited line silently moves it and nothing complains.

## 1. The runbook, in order

Ordering is load-bearing — each step's reason is why it sits where it does.

| # | Step | Command | Why here |
|---|---|---|---|
| 1 | Confirm the new version | `claude --version` | Everything below compares against it. |
| 2 | Re-extract the decompile | in `/repos/claude-code-decompiled`: `npm run extract && npm run link && npm run typecheck` (`npm install` once first) | Chunk hashes **and** line numbers rotate every build. Until this runs, step 7's citation check and `tests/test_model_visibility.py` both pass vacuously. `extract` empties `src/`, `assets/` and `native/` first, so modules the new binary dropped disappear on their own. |
| 3 | Confirm the decompile matches | `grep -m1 -oP '(?<=VERSION: ")[^"]+' /repos/claude-code-decompiled/src/cli.js` | `src/cli.js` is the one stable filename across the 2.1.269 layout change; it carries `VERSION`/`BUILD_TIME`/`GIT_SHA`. Must equal step 1. |
| 4 | Read upstream's own release notes | `.claude/skills/update-claude-code/changelog.py <previous version>` | Claude Code ships its notes inside the binary, and they name the *reason* behind a diff that nothing else here can: the `Agent` tool's schema change in 2.1.269 is "`CLAUDE_CODE_SUBAGENT_MODEL` became a default rather than an override" at 2.1.251. Read it before the checks, so the rest of the runbook is confirming a known list rather than reverse-engineering one. Needs step 2's tree. |
| 5 | Re-sync the editable venv — **canonical checkout only** | from `/repos/claude-config`: `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config uv sync --reinstall-package claude-config` | `check-env-context.sh` runs under this venv, so a stale install loads the old `drift.py`. `--reinstall-package` is required because the package version never bumps. **Run it from a worktree and it repoints the shared venv's editable install at that worktree** (`+ claude-config @ file:///root/claude-config-work2`), breaking every other session once the worktree is deleted — the same hazard as `install.sh`. A worktree has its own venv at `$HOME/.claude/venvs/<basename>`, selected by the `UV_PROJECT_ENVIRONMENT` that `.envrc` exports through direnv, so a worktree needs no step 5. |
| 6 | Check, then re-pin, env-context | `./scripts/check-env-context.sh` → review the `+`/`-`/`~` diff → `./scripts/check-env-context.sh --update` | The diff is the single best summary of what changed in cc's own `# Environment` block. Re-pin only after reading it — `--update` overwrites the evidence. |
| 7 | Resolve every source citation | `bash .claude/skills/update-claude-code/citecheck.sh` | 136 `chunk-*.js:LINE` citations live in tracked files; only 2 are re-derived by any test. Exit 0 = all resolve; 1 = the unresolved ones are named on stdout; 2 = no decompiled tree, i.e. step 2 was skipped. |
| 8 | Rebase the upstream-derived prompts | `python3 scripts/check-prompt-upstream.py`, then the section-key diff it does not do | `sys_prompt/` replaces Claude Code's own system prompt wholesale and the env-context hook renders an environment block of its own — since the 2026-09-13 trim it carries only what cc's does not, and the stash caution is the one passage it still borrows — so passages copied from either go stale with no signal and nothing else in this list reads prose. The replacement is not total either: Anthropic's own wording still arrives through `messages[]`, which neither this script nor anything else here reads. The script needs step 2's tree and exits 2 without it. The procedure, the deliberate divergences and the per-release log are in `sys_prompt/CLAUDE.md`, "Rebasing on an upstream release" — that text governs; this row only says when to run it. |
| 9 | Rebuild and test | `cd agent-tools && cargo build --release && cargo test --release`; `uv run pytest tests/ -q`; `./scripts/check-prompt-coupling.sh` | |
| 10 | Check the renderer against real logs | `ls -t /root/.claude/projects/*/*.jsonl \| head -8 \| uv run cc-render-coverage --quiet` | New record and attachment shapes land here first. |
| 11 | Re-capture the system-prompt snapshots | see `docs/system-prompt-snapshot/README.md` "Regenerating" | Needs an authenticated `claude` — `CLAUDE_CODE_OAUTH_TOKEN`, which Claude Code strips from tool subprocesses, or an access token in `~/.claude/.credentials.json`, which comes and goes with login state — and any checkout's venv (`mitmdump` is a project dependency; `capture.py` starts its own proxy when 9160 is dead). Never run two `regenerate.py` in parallel — they share `capture-output/` and `~/.claude/requests-log/`. |
| 12 | Read the capture in full | `git diff docs/system-prompt-snapshot` | Every configuration and every tool file, read through rather than skimmed — tool descriptions **and their input schemas** move between releases, and nothing else in this list reads them. The 2.1.269 pass compared `description` only and filed `Agent` as unchanged while its schema had moved. `docs/system-prompt-snapshot/README.md`, "Reading a capture as a diff", governs what that diff shows and what it structurally cannot; this row only says when. |
| 13 | Re-derive what the fired checks were premises *for* | for each premise a check above falsified, `git grep` its wording across tracked files | Steps 6, 8 and 12 are the steps that falsify premises, and every remedy this runbook prescribes for them is conformance repair — re-pin, rebase, re-read the source so the mirror tracks. Repair leaves the artifacts built on the old premise standing, and reading one of them does not reveal it: a component's own rationale is the thing that expired. 2.1.269 moved the env block into `messages[]`; the finding was written into `env_context/__main__.py` on 2026-09-11 and three other files went on asserting that `--system-prompt-file` discards it, in four places — step 8's own why-clause in this table among them — until 2026-09-13. The same release moved the output style out of the system prompt, and three more files kept the old location. So: name every artifact resting on the premise, and re-derive or retire each. The case this list structurally cannot express is a mirror that now matches cc exactly — `check-env-context.sh` printing `OK` is also what full redundancy looks like. |
| 14 | Merge and reinstall | merge to `/repos/claude-config`, then `install.sh` **there only** | Until the merge, `~/.local/bin/agent-tools` and `cc-pretty` still run the old code — the fixes exist but nothing you run uses them. A worktree that runs `install.sh` breaks every other session. |

Expected clean output, as of 2.1.269: `OK: env-context field set matches the installed
binary` / `OK: 14 borrowed passages still match Claude Code 2.1.269` / no citecheck output / `449 passed` / 15 cargo test binaries all `ok` /
`prompt coupling OK` / `8 file(s) checked: clean`.

**Where to run each step.** Steps 5 and 14 repoint shared installs and belong in the
canonical checkout `/repos/claude-config`. Everything else is worktree-safe and should
be done in a worktree, because steps 6 and 9 rewrite tracked files.

**When a check fails.** `check-env-context.sh` printing `+`/`-`/`~` lines means cc's own
env block changed shape — read the diff against `src/claude_config/env_context/render.py`
before `--update`, since the hook exists to mirror that block. `citecheck.sh` naming a
citation means the decompile moved under it: re-find the cited code by a string marker
(the technique `tests/test_model_visibility.py:192-200` uses — names and hashes rotate,
marker strings survive) and rewrite the citation, rather than deleting it. A
`cc-render-coverage` `missing_content` finding means a record shape the renderer does not
model; `renderer_truncation` means a hardcoded cap ignoring `--tool-max`. A `pytest`
failure in `test_denylist_still_matches_the_conversion_source` is the intended signal that
a release changed which attachment arms return empty — re-derive the set, do not edit the
assertion.

## 2. What each check does NOT cover

This table is the point of the skill. A green run below still leaves all of this open.

| Check | Blind to |
|---|---|
| `check-env-context.sh` | Anything outside a ±1000-byte window around `Primary working directory: ` plus three whole-binary string counts. It sees the env block's *field set*, not behaviour — and not whether the mirror is still wanted: a clean match is its success condition and is equally what redundancy looks like, so cc delivering the same block itself reads as `OK`. |
| `citecheck.sh` | Whether the cited line still says what the citing text claims. It proves the file exists and is long enough — nothing more. Line numbers shift; a resolving citation can point at unrelated code, which is how five same-repo citations were found stale on 2026-09-12 while every one of them resolved. It also sees only `chunk-*.js:LINE`: citations into this repo's own files are checked by nothing. A scan below 100 citations exits 2 rather than printing a clean run. |
| `cc-render-coverage` | The default view's **selection**. It renders with `show_all` set and draws needles only from `assistant`/`user` records, so attachment/progress/system records contribute none. It cannot see a record being dropped. |
| `pytest` | Every citation but two. `tests/test_model_visibility.py` re-derives `_NEVER_VISIBLE_ATTACHMENT_TYPES` and `_HOOK_STDOUT_VISIBLE_EVENTS` from the decompiled source by string marker — and both `skipif` when `/repos/claude-code-decompiled/src` is absent, so they report success by not running. |
| `check-prompt-coupling.sh` | Claude Code entirely. It greps this repo's own files against each other. |
| `check-prompt-upstream.py` | Everything upstream says that this repo never copied. It re-checks 15 borrowed passages, so a section a release adds — or reworded text this prompt does not carry — is invisible to it. Where a passage occurs more than once it reports that the count moved, not which copy moved. |
| `changelog.py` | Anything upstream chose not to write down, and every release older than the window the binary carries — 15 entries in 2.1.269, reaching back to 2.1.247. The running version has no entry of its own, and a release with no user-facing notes has none either, so a gap in the sequence is not evidence of a truncated window. |
| The capture diff (step 12) | Every setting in this repo's own `settings.json`. `capture.py:471` passes `--setting-sources project,local`, which drops `userSettings` (`rWn`, `chunk-3vd4nzwp.js:8440-8442`), and `install.sh` puts this file at `~/.claude/settings.json` — user scope. A capture therefore shows stock behaviour for every key here, which is deliberate (snapshots stay comparable) but means no capture can confirm a key still takes effect. The 18 deferred tools: a capture carries their names in a reminder and one `DeferredToolPlaceholder` entry, never their descriptions or schemas. And it is one environment on one day — most prompt sections sit behind a server-resolved flag, so a section absent from a capture is not a section the release removed. |
| CI | Everything. `.github/workflows/skills-test.yml` runs only `skills/scripts/` tests, only on `skills/scripts/**` paths. No drift check runs in CI. |

## 3. The coupling inventory — what an upgrade can break

### 3.1 Degrades silently (no error, wrong behaviour)

| Where | Reads | Failure mode |
|---|---|---|
| `agent-tools/src/hook_input.rs:13-35` | `session_id`, `tool_name`, `tool_input`, `tool_use_id`, `hook_event_name`, `tool_response` | A renamed field fails the parse; `hook_pre.rs:14-19` then allows passthrough and `hook_post.rs:46-51` returns `Ok(())`. Wrapping just stops happening. |
| `agent-tools/src/hook_post.rs:118-172` | `backgroundTaskId`, `backgroundedByUser`, `backgroundedByTurnAbort`, `backgroundedToDeliverMessage`, `timedOutAfterMs`, `run_in_background` | A rename yields `Cause: not stated by the tool response` instead of an error. 2.1.269 already deleted `assistantAutoBackgrounded`; the replacement fields are what these are, and its Bash output schema (`src/chunk-dbb93264.js:215699-215703`) declares no other cause field. |
| `agent-tools/src/hook_post.rs:22` | `REPORT_BUDGET = 9_000` | Justified by a 2.1.269 measurement that a **local command hook's** stdout escapes the 8,000-char/200-line `additionalContext` cap (the cap sits on `ego`, reached through `uje` from the cloud-session hook runner, `mcn`, `src/chunk-dbb93264.js:48303`, and the registered-callback answer path, `:49123`; a local command hook's stdout is parsed by `gwe`, `:227133`, which has no sanitizer). If a release routes local hooks through the sanitizer, reports get truncated to a stub. |
| `agent-tools/src/hook_pre.rs:22`, `hook_post.rs:57` | tool names `Bash`, `Monitor` | A renamed or new shell tool is simply not wrapped. |
| `agent-tools/src/paths.rs:66-105` | `CLAUDE_CODE_SESSION_ID` (read at `:105`) | A rename breaks bare `!` commands. |
| `skills/telegram-hitl/SKILL.md:74`, `:206` | `CLAUDE_CODE_SESSION_ID`; the tool name `Monitor` | A renamed variable sends an empty `X-Session-Id`, so the channel log records that a send happened but not who made it — the send still succeeds, so nothing surfaces it. `tests/test_telegram_hitl_skill.py:123` pins the spelling in the skill's own prose and cannot see the variable go away. A renamed `Monitor` leaves the skill pointing an agent at a tool that no longer exists, for the one case — unsolicited input — it offers no other answer for. |
| `statusline.sh:5-19` | `.model.display_name`, `.context_window.*`, `.cost.total_cost_usd`, `.workspace.current_dir`, `.transcript_path`, `.session_id` | Every field defaults (`// 0`, `// "?"`, `// empty`). A rename shows zeros — except `.session_id` (`:19`), which is the key `agent-tools ps --format statusline` scopes to, so a rename there blanks the open-tasks row rather than zeroing it. 2.1.269 also supplies `prompt_cache` and `rate_limits.spend_limit`, which this script does not read. |
| `src/claude_config/cc_pretty/parse.py:28`, `:188-375` | record `type` values | `extra: "allow"`, so new fields are safe; a renamed record type becomes `UnknownRecord` and vanishes from the render. |
| `settings.json:19-50` | `Notification` matchers `permission_prompt`, `idle_prompt`, `elicitation_dialog`, `elicitation_url_dialog`, `quota_auto_resume_fired`, `quota_auto_resume_stale`, `quota_auto_resume_disabled` | Matched as **unanchored regexes**, not literals (`src/chunk-dbb93264.js:227871`), so `permission_prompt` also catches `worker_permission_prompt` — which is wanted, a worker's prompt blocks the human the same way, and is recorded here because nothing in the file says so. The declared matcher set is 16 values — `VAr`'s 14 (`src/chunk-70hqkjxq.js:12`) plus `elicitation_complete` and `elicitation_response` (`src/chunk-c29sfp49.js:76`). Seven are selected, on one rule: notify when the session is blocked on the human or has stopped making progress by itself. Deliberately dropped: `auth_success` and `push_notification` (nothing to act on), `elicitation_complete`/`elicitation_response` (the answer already arrived), `computer_use_enter`/`exit` (unused here), and `agent_needs_input`/`agent_completed` — `CLAUDE_CODE_DISABLE_AGENT_VIEW=1` and the `Agent` hook keep every subagent foreground, so neither can fire; configuring them would be dead config. A release that re-enables the agent view makes those two live again. |
| `settings.json:82-92` | `PreToolUse` matcher `"Agent"` + `jq` rewriting `run_in_background` to `false` | With `CLAUDE_CODE_FORK_SUBAGENT=0` this is what makes subagents synchronous. If either half stops working, `sys_prompt/alan-default-next.md:215` becomes a lie the model acts on. Measured 2026-09-13: on unparsable stdin `jq` exits 5 with empty stdout, so it cannot emit the not-JSON `{…}` that 2.1.248 turned into a hook error. |
| `settings.json:116-127` | `PostToolUseFailure` | A distinct event name. Folded back into `PostToolUse` and errored calls stop being delivery points. |
| `sys_prompt/alan-default-next.md`, and any `agents/*.md` named after a built-in agent | passages copied verbatim from Claude Code's own system prompt | `--system-prompt-file` drops every upstream section, so a rule upstream reworded or added never arrives and the copy here keeps saying the old thing. `sys_prompt/CLAUDE.md` governs: procedure, deliberate divergences, per-release log. |
| `scripts/claude.sh:13` | `CLAUDE_CODE_DISABLE_AGENT_VIEW=1` | Without it an agent-view fork drops `--system-prompt-file` and silently runs the stock prompt. |
| `scripts/intercept/proxy.py:28`, `:82-88` | the `x-claude-code-session-id` request header, and `sessionId`/`pid`/`cwd`/`kind`/`entrypoint` in `~/.claude/sessions/*.json` | A renamed header sends every capture to `requests-log/unknown/`; a renamed session-file field drops that key from the log's `session` block. Both are plain `.get()` misses — the capture still gets written, just anonymous. The row listed `startedAt` as a sixth field until 2026-09-13, when it turned out to be parsed and never read, so renaming it changed nothing and the assertion could not fail; the field is gone from `proxy.py` rather than from this row alone. |
| `scripts/claude.sh:45`, `scripts/prompt-test-cc-leg2.sh:73` | the system prompt and tool definitions a conversation recorded on its first request | Since 2.1.267 a resume replays the record, not what the command line passes (`GWe`, `src/chunk-dbb93264.js:130178`; the record holds the tool definitions too, `Mos`, `:130134`, and `--system-prompt-snapshot off` bypasses both). It is on here: this repo's transcripts carry `prompt_snapshot` attachments holding `alan-default-next.md` verbatim. Measured on 2.1.269 through the proxy: a resume passing a different prompt file sent the first leg's text; with the flag it sent the new one. The leg-2 runner passes the flag; anywhere else, exercise a prompt edit in a fresh session. |
| `settings.json` `includeGitInstructions: false`, `attribution.commit/pr: ""` | one gate, `q7()` (`chunk-dbb93264.js:69382`), that removes the Bash tool's `# Git` block, cc's `gitStatus` reminder and the attribution reminder | A release that renames the key, or stops gating the block by it, puts `Commit or push only when the user asks. If on the default branch, branch first.` back beside the `# Git` section of `sys_prompt/alan-default-next.md`, which then contradicts it. The capture cannot answer it: `capture.py:471` passes `--setting-sources project,local` and this file installs as *user* settings, so `tools/Bash.md` carries the block whether the gate holds or not — as the committed `opus-5/default/tools/Bash.md:21` does today. What does answer it: a live `claude.sh` session's own Bash description, and `prompt-tests/general/commit-own-changes`, whose runner applies the gate because `agent-tools claude` copies this file into `CLAUDE_CONFIG_DIR`. `sys_prompt/CLAUDE.md`, "`# Git`", governs. |
| `settings.json:4-6` (`env`) | which settings scope may set which environment variable | 2.1.251 stopped a project-level `.claude/settings.json` `env` from setting `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_TMPDIR` or `TMPDIR`/`TMP`/`TEMP`. This file installs as *user* settings and sets only `CLAUDE_CODE_FORK_SUBAGENT`, so it is unaffected; a project-level copy adding one of those three would be ignored silently. |

### 3.2 Mirrors of cc's own algorithms — re-read the source, don't just test

`src/claude_config/env_context/` reimplements cc behaviour and must track it:
`environment.py`: `resolve_shell` ≙ cc's `das()`, `_executable` ≙ `cbt()` (incl. the `--version` fallback that makes a bare `CLAUDE_CODE_SHELL=bash` resolve), `worktree_common_dir` ≙ `pP()`, `git_snapshot` ≙ `ADe()` (`chunk-dbb93264.js:69331-69369`: `--no-optional-locks status --short --ignore-submodules=dirty`, `log --oneline -n 5`, the 2000-character cap; it replaces the `gitStatus` reminder `includeGitInstructions: false` removes);
`scratchpad.py:22-54` (path algorithm, incl. the 200-char slug limit past which cc appends a hash
this module does not implement — it raises instead), `render.py:43-61` (`STASH_CAUTION` copied
verbatim from cc's `KUt`, and the only passage the hook still borrows — pinned by
`scripts/check-prompt-upstream.py`, since `check-env-context.sh` covers cc's field set, not this
block's wording), `drift.py:42-46` (anchor and window constants tuned to the binary layout),
`drift.py:187-208` (a timeout budget whose comment says to re-check the sum if any of the three
numbers moves).

### 3.2b Knobs that are unset here, and what each would do if set

Nothing here sets them; each would silently change behaviour a row above asserts. Same shape as
`CLAUDE_AUTO_BACKGROUND_TASKS` in `CLAUDE.md`.

| Unset knob | What setting it would do here |
|---|---|
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` (2.1.257) | Applies one model to every subagent, ignoring per-spawn and agent-definition overrides — re-breaking what 2.1.251 fixed, and silently voiding every `model:` in `agents/*.md`. |
| `CLAUDE_CODE_ENABLE_TODO_TOOLS` (2.1.268) | Restores the task-tracking tools (`TodoWrite`, `TaskCreate/Get/Update/List`), which are otherwise offered only to older models. |

### 3.3 Pins to re-pin vs. records to leave alone

**Re-pin:** `docs/env-context-manifest.json` (version, 24 window literals, 3 required-literal counts)
— via `--update`, which refuses to write a count of 0 because a zero is a permanently-passing
assertion.

**Re-verify the claim, keep the label:** the version banners in `docs/system-prompt-anatomy*.md`,
`docs/tool-token-limits.md`, `docs/background-sessions.md`, `docs/system-prompt-snapshot/README.md`,
`skills/cc-history/SKILL.md`, `output-styles/README.md`, `agent-tools/CLAUDE.md`,
`docs/agent-tools-status-reference.md`, and the first-byte-watchdog window in
`scripts/intercept/README.md`, "Pass-through streaming" — if that number moves, an
intercepted session's turns start aborting at the new one.

**Do NOT re-pin — these are dated records of an older build, and rewriting them destroys the
evidence:** everything under `notes/` (each carries a staleness banner), `plans/`,
`docs/superpowers/plans/` and `specs/`, the synthetic version strings in `tests/test_env_context.py`
and `tests/test_model_visibility.py`, the captured artifacts under `docs/system-prompt-snapshot/**`
(regenerated wholesale, never hand-edited), and `prompt-tests/runs/**`.

### 3.4 Snapshot-capture mechanics that break on upgrade

`docs/system-prompt-snapshot/capture.py`: the trust-dialog cursor reader (`:351-369` — the default
already flipped once between 2.1.235 and 2.1.269), the main-request selector (`:596-606`), the
`cc_is_subagent=true` billing-header marker (`:611-624`). `regenerate.py:261-266` excludes the
`defer_loading` placeholder. `render_capture.py` derives `prompt.md` and `tools/` from each
`request.json`, and `tests/test_snapshot_rendering.py` re-renders all 13 captures and fails when
the tracked files drift from it — so a hand-edited capture is caught rather than read as evidence.
Every character count and `system_tokens` figure in
`README.md` and `what-the-model-gets.md` is derived from these files — re-derive them, don't
adjust them by hand.

## 4. Still to check — as of 2026-09-12, Claude Code 2.1.269

Open items with what would retire each. Delete an entry when it is closed; add one when you find a
new gap rather than leaving it in a session transcript.

**Pins never re-derived for this build**
- `docs/env-context-manifest.json:3` → `notes/env-context-manifest.md` — byte offsets, four-anchor
  count and the `Shell: PowerShell` probe describe 2.1.235 only.
- `docs/system-prompt-snapshot/README.md` — the two **Not re-verified this round** blocks, under
  "Security-monitor calls" and "Interactive vs `-p` mode differences".
- `docs/system-prompt-snapshot/builtin-output-styles/` — captured from v2.1.87, and 2.1.257's notes
  name a `Proactive` built-in the directory has no file for, so the set is incomplete as well as
  stale. Retire by re-capturing every built-in style.

**Captures not taken**
- The one configuration this repo runs is uncaptured: `scripts/claude.sh` launches
  `--dangerously-skip-permissions`, every capture takes the default permission mode, and the
  bypass-permissions reminder a `claude.sh` session carries is in none of them. `regenerate.py`'s
  `bypass-permissions` variant defines it; capturing it closes this. Which of `auto_mode`'s three texts a `claude.sh`
  session reaches is no longer part of it — a live session log answers `e.bypass` directly (snapshot
  README, "Removed: the `## Auto Mode Active` reminder"); what a capture still adds is the rest of
  the request under that mode, beside a default-mode capture in one artifact. 2.1.257 adds a second
  reason to take it: `defaultMode: "bypassPermissions"`
  is now ignored from project settings, so the mode's only supported entry points are user settings
  and `--permission-mode`.
- No backgrounded-session capture for 2.1.269 (`regenerate.py`'s `VARIANTS` has no such key), and two
  live checks dropped at a `/compact` boundary: whether the Auto Mode reminder fires for a
  `capture.py` session, and `/feedback` from an interactively-logged-in session.

**Opened by the release-notes pass, 2026-09-12** — all 635 bullets of 2.1.247-2.1.268 read against §3.
Each row is a claim in this repo that a bullet puts in doubt.

| What to re-check | Why, and what retires it |
|---|---|
| `docs/agent-tools-status-reference.md` "The kill boundary" | 2.1.257 fixed background commands that detach via `setsid` surviving a **task stop** or **Claude Code exit** — the escape `agent-tools run --background` is built on. The task-stop half is measured there (the child survives). The exit half needs a human: start `agent-tools run --background sleep 900`, quit Claude Code, check whether the child is still running. |
| `docs/tool-token-limits.md` | 2.1.261 added `bashOutputMaxChars` and `taskOutputMaxChars` (ceiling 128K) and 2.1.265 a 1 GB cap on tool results saved to disk; the file carries a 2.1.88 banner and knows neither. Retire on its next re-measurement. |
| `agent-tools env-context` on resume | 2.1.268 stopped `--continue`/`--resume` waiting for SessionStart hooks before rendering. Retire by confirming the env block still arrives on a resume rather than being raced past. |
| `src/claude_config/cc_pretty/` record handling | Three in-window shape changes: per-second subagent progress ticks now replace their predecessor rather than accumulating (2.1.251); async hook completion notices batch onto one line (2.1.257); nested background subagent results are saved into the **parent subagent's** transcript (2.1.259), which moves what a session-analysis pass finds. Retire by re-reading real logs for each. |

**Open design questions, not defects**
- One passage `sys_prompt/alan-default-next.md` borrowed from upstream diverges with no recorded
  reason and nothing else in the prompt covering it — the row marked **Not reviewed** under
  "Deliberate divergences" in `sys_prompt/CLAUDE.md`. It predates the 2.1.235 baseline, so the
  2.1.269 rebase neither caused nor closed it.
- `cc-render-coverage` cannot see selection defects at all (§2). Extending it is what would have
  caught the skeleton-renderer bug fixed on 2026-09-12.
- Same-repo `file:line` citations still have no checker. `citecheck.sh` resolves only
  `chunk-*.js:LINE`, and line-existence would not have caught the drift found on 2026-09-12 anyway:
  every stale citation pointed at a real, non-blank line of unrelated code. Pinning by string, the
  way `scripts/check-prompt-coupling.sh` does, is the only mechanism here that has teeth.

**Pre-existing, not upgrade-caused** (verified absent from the 2.1.235 capture too, so don't
re-diagnose these as upgrade fallout)
- `agents/*.md` and ~30 sites under `skills/scripts/` name `Grep`, `Glob`, `TodoWrite` and `Task`;
  the live roster has none of them. `TodoWrite` is the one with a known cause and a one-setting fix:
  2.1.268 gates the task-tracking tools to older models and `CLAUDE_CODE_ENABLE_TODO_TOOLS=1`
  restores them, so it is a settings decision. `Grep`, `Glob` and `Task` are text edits, and whether
  the model reliably maps `Task`→`Agent` is untested.

## Common mistakes

| Mistake | What actually happens |
|---|---|
| Running the checks before re-extracting the decompile | `citecheck.sh` and the denylist test both pass without testing anything — a stale tree still has the files, and they are still long enough. `check-prompt-upstream.py` is the only one that refuses, by comparing `src/cli.js` against `claude --version`. |
| Treating a green `cc-render-coverage` as "the renderer is fine" | It never looks at attachment records or at what the default view selects. |
| Grepping for the old version string and calling it done | That finds stale *references*. It cannot find a live code path whose input shape changed underneath it — which is how the skeleton bug (§4) survived a full audit. |
| Diffing the prompt captures and calling that the upstream delta | A capture is one environment on one day, and most prompt sections sit behind a server-resolved flag. `act_dont_rederive` vanished between the 2.1.235 and 2.1.269 captures while staying in both binaries. |
| Re-pinning a `notes/` file to the new version | Destroys a dated record of the older build. Those files are evidence, not documentation. |
| Fixing, committing, and stopping | Nothing you run changes until the merge to `/repos/claude-config` and a rebuild — the installed binary and the editable venv both resolve there, by design. |
| Comparing tool `description`s and calling that the tool diff | An input schema moves on its own. `Agent` changed only in its schema in 2.1.269, and was written up as unchanged for exactly that reason. `tools/<Name>.md` renders description and schema into one file so both land in the same diff. |

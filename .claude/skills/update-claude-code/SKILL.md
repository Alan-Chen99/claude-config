---
name: update-claude-code
description: Use when Claude Code has been upgraded and this repo must be re-checked, or when a session reports an env-context drift note or an unresolvable `chunk-*.js:LINE` citation. ALSO read BEFORE editing any file naming a Claude Code hook field, env var (`CLAUDE_CODE_*`), settings key, hook event, tool name, JSONL record or attachment type, statusline field, CLI flag, or decompiled-source line — don't skip because the edit looks small; that code is version-coupled and belongs in this skill's inventory.
---

# Updating after a Claude Code release

## Overview

Claude Code is a moving dependency this repo reads, imitates and cites, and an upgrade breaks
things **silently**: `serde` ignores unknown keys, pydantic models are `extra: "allow"`,
`statusline.sh` defaults every missing field to `0`, and the one test that re-derives a
constant from the decompiled source `skipif`s itself away without the decompile.

**Core principle: a check that cannot fail is not a check.** Before trusting any result below,
know what it does *not* cover — §2 says so for each.

## Add to this file as you build

Anything you write that reads a Claude Code data shape, env var, hook field, settings key, tool
name, log-record type or source line goes into §3 in the same change; a coupling nobody
recorded is a coupling nobody re-checks. Then re-check the line ranges §3 already cites into
the file you edited: same-repo citations are checked by nothing.

## 1. The runbook, in order

Ordering is load-bearing — steps 4, 7 and 8 read the tree step 2 builds, and run before it they
pass vacuously.

| # | Step | Command | Why here |
|---|---|---|---|
| 1 | Confirm the new version | `claude --version` | Everything below compares against it. |
| 2 | Re-extract the decompile | in `/repos/claude-code-decompiled`: `npm run extract && npm run link && npm run typecheck` (`npm install` once first); then `bash .claude/skills/update-claude-code/skilldiff.sh` (`--update` to take the new text) | Chunk hashes **and** line numbers rotate every build; until this runs, step 7 and `tests/test_model_visibility.py` pass vacuously. `skilldiff.sh` compares the two skills vendored under `skills/` against the assets — the asset half only; the loader half is the §4 artifact entry, and it is unconditional. |
| 3 | Confirm the decompile matches | `grep -m1 -oP '(?<=VERSION: ")[^"]+' /repos/claude-code-decompiled/src/cli.js` | Must equal step 1. `src/cli.js` is the one stable filename across the 2.1.269 layout change. |
| 4 | Read upstream's own release notes | `.claude/skills/update-claude-code/changelog.py <previous version>` | The notes ship inside the binary and name the *reason* behind a diff nothing else here can; read first, the checks confirm a known list. Needs step 2's tree. |
| 5 | Re-sync the editable venv — **canonical checkout only** | from `/repos/claude-config`: `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config uv sync --reinstall-package claude-config` | `check-env-context.sh` runs under this venv, so a stale install loads the old `drift.py`; `--reinstall-package` because the package version never bumps. **From a worktree this repoints the shared venv at the worktree** and breaks every other session once it is deleted; a worktree has its own venv via `.envrc` and needs no step 5. |
| 6 | Check, then re-pin, env-context | `./scripts/check-env-context.sh` → read the `+`/`-`/`~` diff → `./scripts/check-env-context.sh --update` | The diff is the best summary of what changed in cc's `# Environment` block. Re-pin only after reading it — `--update` overwrites the evidence. |
| 7 | Resolve every source citation | `bash .claude/skills/update-claude-code/citecheck.sh` | Exit 0 = every `chunk-*.js:LINE` citation in tracked files resolves; 1 = the unresolved ones are named; 2 = no decompiled tree, i.e. step 2 was skipped. |
| 8 | Rebase the upstream-derived prompts | `python3 scripts/check-prompt-upstream.py`, then the section-key diff it does not do | `sys_prompt/` replaces cc's system prompt wholesale, so passages copied from it go stale with no signal — and Anthropic's own wording still arrives through `messages[]`, which nothing here reads. Exits 2 without step 2's tree. Procedure, divergences, per-release log: `sys_prompt/CLAUDE.md`, "Rebasing on an upstream release". |
| 9 | Rebuild and test | `cd agent-tools && cargo build --release && cargo test --release`; `uv run pytest tests/ -q`; `./scripts/check-prompt-coupling.sh` | |
| 10 | Check the renderer against real logs | `ls -t /root/.claude/projects/*/*.jsonl \| head -8 \| uv run cc-render-coverage --quiet` | New record and attachment shapes land here first. |
| 11 | Re-capture the system-prompt snapshots | `docs/system-prompt-snapshot/README.md`, "How to re-capture" | Needs an authenticated `claude` (`CLAUDE_CODE_OAUTH_TOKEN`, which cc strips from tool subprocesses, or `~/.claude/.credentials.json`). Never two `regenerate.py` in parallel — they share `capture-output/` and `~/.claude/requests-log/`. |
| 12 | Read the capture in full | `git diff docs/system-prompt-snapshot` | Every configuration and every tool file, descriptions **and input schemas** — the 2.1.269 pass compared descriptions only and filed `Agent` as unchanged while its schema had moved. What the diff structurally cannot show: the README, "Reading a capture as a diff". |
| 13 | Re-derive what the fired checks were premises *for* | for each premise a check falsified, `git grep` its wording across tracked files | Steps 6, 8 and 12 falsify premises; their remedies repair conformance and leave every artifact built on the old premise standing. Name each and re-derive or retire it (2.1.269 moved the env block into `messages[]`; four places asserted the opposite for two more days). A mirror that now matches cc exactly also reads as `OK`. |
| 14 | Merge and reinstall | merge to `/repos/claude-config`, then `install.sh` **there only** | Until the merge, `~/.local/bin/agent-tools` and `cc-pretty` still run the old code. A worktree that runs `install.sh` breaks every other session. |

Expected clean output, as of 2.1.269: `OK: env-context field set matches the installed
binary` / `OK: 13 borrowed passages still match Claude Code 2.1.269` / no citecheck output /
`OK: 2 vendored skill(s) match the extract` / `prompt coupling OK` / `8 file(s) checked: clean`.

**Where to run each step.** Steps 5 and 14 repoint shared installs and belong in
`/repos/claude-config`. Everything else belongs in a worktree, because steps 2
(`skilldiff.sh --update`), 6 and 9 rewrite tracked files.

**When a check fails.** `check-env-context.sh` printing `+`/`-`/`~` lines: read the diff
against `src/claude_config/env_context/render.py` before `--update`. `citecheck.sh` naming a
citation: re-find the code by a string marker (as `tests/test_model_visibility.py:192-200`
does — names and hashes rotate, strings survive) and rewrite the citation rather than delete
it; grepping for the old version string finds stale *references*, never a live code path whose
input shape changed. `cc-render-coverage` `missing_content`: a record shape the renderer does
not model; `renderer_truncation`: a hardcoded cap ignoring `--tool-max`. `pytest` failing in
`test_denylist_still_matches_the_conversion_source`: a release changed which attachment arms
return empty — re-derive the set, do not edit the assertion.

## 2. What each check does NOT cover

A green run leaves all of this open.

| Check | Blind to |
|---|---|
| `check-env-context.sh` | Anything outside a ±1000-byte window around `Primary working directory: `: the env block's *field set*, not behaviour — and not whether the mirror is still wanted, since cc delivering the same block itself also reads as `OK`. |
| `citecheck.sh` | Whether the cited line still says what the citing text claims — it proves the file exists and is long enough; five same-repo citations were stale on 2026-09-12 while every one resolved. Citations into this repo's own files are checked by nothing; pinning by string, as `check-prompt-coupling.sh` does, is the only mechanism here with teeth. Below 100 citations it exits 2. |
| `cc-render-coverage` | The default view's **selection**: it renders with `show_all` and draws needles only from `assistant`/`user` records, so it cannot see a record being dropped. |
| `pytest` | Every citation but two. `tests/test_model_visibility.py` re-derives `_NEVER_VISIBLE_ATTACHMENT_TYPES` and `_HOOK_STDOUT_VISIBLE_EVENTS` by string marker — and both `skipif` without `/repos/claude-code-decompiled/src`, reporting success by not running. |
| `check-prompt-coupling.sh` | Claude Code entirely; it greps this repo's files against each other. |
| `check-prompt-upstream.py` | Everything upstream says that this repo never copied: 13 borrowed passages, so an added section is invisible. |
| `changelog.py` | Anything upstream did not write down, and releases older than the binary's window (15 entries in 2.1.269, back to 2.1.247). |
| The capture diff (step 12) | Every key in this repo's `settings.json`: `capture.py:471` passes `--setting-sources project,local`, which drops user settings (`rWn`, `chunk-3vd4nzwp.js:8440-8442`), and `install.sh` installs this file at user scope — a capture shows stock behaviour for every key here. Deferred tools appear as names plus one `DeferredToolPlaceholder`, never as descriptions or schemas. And it is one environment on one day: most prompt sections sit behind a server-resolved flag, so a section absent from a capture is not a section the release removed. |
| `skilldiff.sh` | Everything the loader adds after reading the asset — the dataviz callout behind `tengu_cobalt_plinth_dataviz` (`src/chunk-s7akwrx2.js:455`), and under `CLAUDE_CODE_ARTIFACT_TOOLSET` a "Page contract" prefix and one phrase swap (`nJn`, `src/chunk-qza9q751.js:220-253`) — so a copy can match the asset and not say what the built-in says. `NO ASSET` is what rename and removal both look like; its `VENDORED` list is fixed. |
| CI | Every check above: `ci.yml` runs pytest and `cargo test` and nothing else, and the one pytest case exercising the drift check for real skips where no Claude Code is installed. |

## 3. The coupling inventory — what an upgrade can break

### 3.1 Degrades silently (no error, wrong behaviour)

| Where | Reads | Failure mode |
|---|---|---|
| `agent-tools/src/hook_input.rs:13-35` | `session_id`, `tool_name`, `tool_input`, `tool_use_id`, `hook_event_name`, `tool_response` | A renamed field fails the parse; `hook_pre.rs:14-19` allows passthrough and `hook_post.rs:46-51` returns `Ok(())`. Wrapping just stops. |
| `agent-tools/src/hook_post.rs:118-172` | `backgroundTaskId`, `backgroundedByUser`, `backgroundedByTurnAbort`, `backgroundedToDeliverMessage`, `timedOutAfterMs`, `run_in_background` | A rename yields `Cause: not stated by the tool response`. The Bash output schema (`src/chunk-dbb93264.js:215699-215703`) declares no other cause field. |
| `agent-tools/src/hook_post.rs:22` | `REPORT_BUDGET = 9_000` | Rests on a 2.1.269 measurement that a **local command hook's** stdout escapes the 8,000-char/200-line `additionalContext` cap: the cap (`ego`) sits on the cloud-session and callback paths (`src/chunk-dbb93264.js:48303`, `:49123`), and local stdout is parsed by `gwe` (`:227133`) with no sanitizer. Routed through it, reports truncate to a stub. |
| `agent-tools/src/hook_pre.rs:22`, `hook_post.rs:57` | tool names `Bash`, `Monitor` | A renamed or new shell tool is not wrapped. |
| `agent-tools/src/paths.rs:66-105` | `CLAUDE_CODE_SESSION_ID` (`:105`) | A rename breaks bare `!` commands. |
| `src/claude_config/pre_output/record.py` (writes), `ntfy_hook.py` `recorded_summary` (sends), `do_cancel` (clears) | `CLAUDE_CODE_SESSION_ID`; the hook event `UserPromptSubmit` | A renamed variable makes `record.py` exit 1 on every turn's last command (deliberately loud) while the reading half silently reverts the ntfy "Done" push to a generated summary. A renamed `UserPromptSubmit` is silent and worse: `do_cancel` stops clearing the record, so every "Done" after the first sends the **previous** turn's summary. `tests/test_pre_output_record.py` passes under both. Check a push against that session's last `pre_output.record` argument. |
| `skills/telegram-hitl/SKILL.md:30` (`X-Session-Id` header), `:53` (the entering line), `:65`, `:70` | `CLAUDE_CODE_SESSION_ID`; the tool names `Monitor` and `TaskStop` | A renamed variable sends an empty `X-Session-Id` — the send succeeds, the log records no sender, and `:53` puts a blank where the handle the human is told to copy belongs. `tests/test_telegram_hitl_skill.py:273` pins the variable's spelling and `:359` the name `TaskStop`; neither sees the thing it names go away. A renamed `Monitor` or `TaskStop` points the arm or disarm step at a tool that no longer exists, and an undisarmed listener runs to expiry, waking a session that already said it stopped. |
| `src/claude_config/doc_budget.py` (`session_of`) | `CLAUDE_CODE_SESSION_ID` | The same-session gate on `approved`: an entry the running session approved is inert there. A renamed variable reads as unset, so every approval counts as live — an agent's own `[data]` entry or held size takes effect in the session that wrote it — with only a stderr warning, which nothing automatic reads. |
| `skills/session-analysis/SKILL.md` (`ocr()`/`ocrange()`), `skills/cc-history/SKILL.md:367`, `:376`, the `$10.50` at `skills/opencode-subcommand/SKILL.md:315` | literal `$N` in skill body text | The Skill tool rewrites `$N` and `$ARGUMENTS` with the invocation's `args` before the model sees the body (`$N` is the (N+1)-th word, greedy past one digit, literal when out of range or with no args; probed 2026-09-24, 2.1.269), so invoking one of these **with args** hands the agent a mangled shell helper, with no error and no test. `skills/session-analysis/CLAUDE.md` carries the invoke-with-no-args rule. |
| `statusline.sh:5-19` | `.model.display_name`, `.context_window.*`, `.cost.total_cost_usd`, `.workspace.current_dir`, `.transcript_path`, `.session_id` | Every field defaults, so a rename shows zeros — except `.session_id` (`:19`), which `agent-tools ps --format statusline` scopes to, so a rename blanks the open-tasks row. |
| `src/claude_config/cc_pretty/parse.py:28`, `:188-375` | record `type` values | `extra: "allow"`, so new fields are safe; a renamed record type becomes `UnknownRecord` and vanishes from the render. |
| `settings.json:31-102` | `Notification` matchers `permission_prompt`, `idle_prompt`, `elicitation_dialog`, `elicitation_url_dialog`, `quota_auto_resume_fired`, `quota_auto_resume_stale`, `quota_auto_resume_disabled` | Matched as **unanchored regexes** (`src/chunk-dbb93264.js:227871`), so `permission_prompt` also catches `worker_permission_prompt` — wanted. Declared set: 16 (`VAr`, `src/chunk-70hqkjxq.js:12`, plus two elicitation names at `src/chunk-c29sfp49.js:76`). Selection rule: notify when the session is blocked on the human or has stopped making progress by itself; the nine dropped on it include `agent_needs_input`/`agent_completed`, left out on a premise that expired on 2026-09-16 (§4). |
| `sys_prompt/alan-default-next.md`, the `Default subagents to the foreground` bullet | the Agent tool's `run_in_background` property, and `q4o`'s last term `!s && r !== !1` (`src/chunk-dbb93264.js:103955`) | Nothing enforces the foreground since the `PreToolUse` `Agent` hook was removed on 2026-09-16; the prompt asks per call. A release that drops `run_in_background` from the schema again — gate `rc() || Z8()`, `src/chunk-dbb93264.js:171779`, false today only because `CLAUDE_CODE_FORK_SUBAGENT=0` — leaves the bullet asking for a parameter that does not exist and every subagent backgrounds silently. Check: `prompt-tests/general/subagent-foreground-default`. |
| `settings.json` `SubagentStart`, `agent-tools/src/hook_subagent.rs` | the hook event `SubagentStart`; output keys `hookSpecificOutput.hookEventName` / `additionalContext` | A renamed event leaves the hook unwired; a mismatched `hookEventName` makes cc reject the whole output (`src/chunk-dbb93264.js:227189`); a renamed `additionalContext` drops the text — and **a hook exiting non-zero does not block the spawn**, so each ends with a subagent running without its Required notes ask. Check by reading one subagent transcript for the `hook_additional_context` attachment before its first turn. |
| `settings.json:177-198` | `PostToolUseFailure` | A distinct event name; folded back into `PostToolUse`, errored calls stop being delivery points. |
| `sys_prompt/alan-default-next.md`, any `agents/*.md` named after a built-in agent | passages copied verbatim from cc's own system prompt | `--system-prompt-file` drops every upstream section, so a rule upstream reworded never arrives and the copy keeps saying the old thing. `sys_prompt/CLAUDE.md` governs. |
| `scripts/claude.sh:17` | `CLAUDE_CODE_DISABLE_AGENT_VIEW=1` | Without it an agent-view fork drops `--system-prompt-file` and silently runs the stock prompt. |
| `scripts/intercept/proxy.py:32`, `:86-92` | the `x-claude-code-session-id` header; `sessionId`/`pid`/`cwd`/`kind`/`entrypoint` in `~/.claude/sessions/*.json` | Plain `.get()` misses: a renamed header sends every capture to `requests-log/unknown/`; a renamed session-file field drops that key from the log. |
| `scripts/claude.sh:95`, `scripts/prompt-test-cc-leg2.sh:95` | the system prompt and tool definitions a conversation recorded on its first request | Since 2.1.267 a resume replays the record, not the command line (`GWe`, `src/chunk-dbb93264.js:130178`; `--system-prompt-snapshot off` bypasses it) — measured through the proxy: a resume with a different prompt file sent the first leg's text; with the flag, the new one. The leg-2 runner passes the flag; anywhere else, exercise a prompt edit in a fresh session. |
| `settings.json` `includeGitInstructions: false`, `attribution.commit/pr: ""` | one gate, `q7()` (`chunk-dbb93264.js:69382`), removing the Bash tool's `# Git` block, cc's `gitStatus` reminder and the attribution reminder | A renamed key, or the block no longer gated by it, puts `Commit or push only when the user asks. If on the default branch, branch first.` back beside the `# Git` section of `sys_prompt/alan-default-next.md`, contradicting it. The capture cannot answer this (user settings dropped); a live `claude.sh` session's Bash description and `prompt-tests/general/commit-own-changes` can. `sys_prompt/CLAUDE.md`, "`# Git`", governs. |
| `scripts/kimi.sh:55-82`, `scripts/zai.sh:57-105` | the `ANTHROPIC_*` endpoint, token and model-tier variables, `CLAUDE_CODE_MAX_CONTEXT_TOKENS`, `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, `API_TIMEOUT_MS`, the `[1m]` model-name suffix | Every one degrades quietly, and both endpoints return 200 for any model string, so a renamed tier variable is served anyway at whatever window cc sizes for the name it fell back to. The `[1m]` suffix is two couplings: `Sz()` returns `1e6` for it first (`if (Rc(e)) return 1e6;`, `src/chunk-5cs6j3p3.js:15251`) and `Gt()` strips it from the outbound id (`return e.replace(/\[1m\]$/i, "");`, `src/chunk-4728jcqn.js:30`) — stop stripping and every request 400s loudly; change what it resolves to and a `zai.sh` session drops to 200,000 silently (`kimi.sh` sets `CLAUDE_CODE_MAX_CONTEXT_TOKENS`, consulted only for an id without the suffix). `ANTHROPIC_AUTH_TOKEN` rather than `ANTHROPIC_API_KEY` because only the latter is gated on `customApiKeyResponses.approved` (`src/chunk-ve1cwn02.js:1451-1457`). |
| `settings.json:4-6` (`env`) | which settings scope may set which environment variable | 2.1.251 stopped project-level `env` from setting `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_TMPDIR`, `TMPDIR`/`TMP`/`TEMP`; this file installs as user settings, so a project-level copy adding one of those would be ignored silently. |
| `scripts/claude.sh` (the randomized draw), `prompt-tests/harness/budget-read-depth/`, `notes/total-tokens-reminder.md`, `docs/total-tokens-reminder-trial.md` | `CLAUDE_CODE_TOTAL_TOKENS_REMINDER`, `_BUDGET`, `_AFTER_USER_TURN`, the five mode names (`src/chunk-dbb93264.js:68265`) | The budget is read by `P.int()` (`src/chunk-hy0zy4c8.js:35-52`), which returns `undefined` for anything unparseable and **falls through** to settings, org clientData, GrowthBook, then `Qhn = 15000000`: a renamed variable or a typo silently yields a control arm wearing a treatment label. Verify per session from the intercept, never from the env var: `grep -ho '<total_tokens>[^<]*</total_tokens>' ~/.claude/requests-log/<session>/*.json`. The check that fails is the trial's own gating one — arms ~50/50 across sessions — run by nothing. |
| `agent-tools/src/hook_provenance.rs`, `settings.json` (`PostToolUse`/`PostToolUseFailure` matcher `""` and `Stop`, each wired `|| true`), the launchers' `CLAUDE_SH_LAUNCHERS` and `CLAUDE_SH_TOKENS_REMINDER_SOURCE` (both recorded by the bare `CLAUDE` prefix and named nowhere in the recorder; `launcher_bookkeeping_reaches_the_record` pins it), `cc_pretty/render.py`'s `hook_success` arm, `docs/total-tokens-reminder-trial.md` "Arm recovery" | the three hook events and their payload fields; the `hook_success` attachment's `content`/`stdout`; the conversion guard making a hook's plain stdout write-only into the transcript — `case "hook_success": if (e.hookEvent !== "SessionStart" && … ) return [];` (`src/chunk-dbb93264.js:236003`) | **The failure that matters is the channel opening**: a release adding `PreToolUse` or `Stop` to that guard turns the block into a `<system-reminder>`, and the session under measurement reads its own launcher, settings and arm. `tests/test_model_visibility.py::test_hook_stdout_visible_events_still_match_the_conversion_source` fails on it — the one coupling here with teeth, and it `skipif`s without step 2's tree. Everything else degrades quietly: a renamed event is unwired, a renamed field a silent parse failure, a renamed subtype an empty `jq` recipe. Unguarded: `content` becomes a `<persisted-output>` stub past ~2 KB while `stdout` stays whole (204,016 bytes intact on 2.1.269); `Stop` does not fire on an aborted turn (`:146157`), which is why the two tool events are wired beside it. |
| `settings.json` `autoCompactWindow: 400000`, `docs/total-tokens-reminder-trial.md` | the key (`src/chunk-3vd4nzwp.js:4980`), its validator `qc` (`:4783`, `.int().min(1e5).max(1e6).catch(void 0)`), `tw()` (`src/chunk-dbb93264.js:129933`), the two reserves the threshold subtracts (`x5n = 20000` and a flat 13,000, `:130008`, `:129806`) | Compaction fires at 367,000 instead of 967,000, and every way that stops is silent: `.catch(void 0)` makes a renamed key or out-of-range value no setting; `CLAUDE_CODE_AUTO_COMPACT_WINDOW` in the environment wins (`:129940`); `DISABLE_COMPACT`/`DISABLE_AUTO_COMPACT` pass `void 0` instead (`:130010`). Each looks like a release moving a reserve. The trial's strata are defined by this number: the trial doc, "The compaction clamp". |
| `settings.json` `enableArtifact: false`, `notes/artifact-tool-roster-cost.md` | the key — `enableKey` of the gate `yl` (`src/chunk-fqa6n2gt.js:9896`), resolved off-wins by `gl()` (`:9838`), read by `TI()` (`:9984`) as the roster filter for `Artifact` (`src/chunk-4zcseazt.js:1354`) and the `isEnabled` of the built-in `artifact-*` skills (`src/chunk-s7akwrx2.js:464`, `:483`); the `/config` Artifacts row (`src/chunk-ve1cwn02.js:753-776`) | Removes the tool — 20,496 of 34,177 tool tokens on 2.1.269 — and the skills from every session, prompt-test runs included. A renamed key silently returns the tool at full cost, and no capture shows it. The in-session `/config` flip the key was chosen for rests on three source readings in the note, none driven live; `CLAUDE_CODE_DISABLE_ARTIFACT` anywhere in the environment hides the row. Check: a live session's `/config` shows the row; a flip lands in `git diff settings.json`. |
| `skills/artifact-design/SKILL.md`, `skills/artifact-diagramming/SKILL.md` | the two built-in skills' asset bodies (2.1.269: `assets/SKILL-31f6eba0.md`, `assets/SKILL-nrz66j7x.md`, named by the loaders' `/$bunfs/root/` literals, `src/chunk-52y74t5k.js:12`, `src/chunk-w93cabjd.js:12`); the shadowing rule (`dze()`, `src/chunk-pmgcy9dx.js`: a bundled entry whose name a user skill took is dropped) | Byte-for-byte copies, kept because the key removes the built-ins and `/workspace/CLAUDE.md` names `artifact-design`. A rewritten asset is caught by `skilldiff.sh`; a changed loader by nothing — the copies stay byte-identical and stop matching the built-in, and the §4 read is the only cover. With the key on, the copies shadow the built-ins by name, silently. |
| `settings.json` `feedbackDrafts: "off"` | the key, read by `SQe()` as `NC("feedbackDrafts")[0] ?? "notify"`; `SendFeedback.isEnabled()` is `iL()` = `SQe() !== "off" && rCn()` (`src/chunk-dbb93264.js:180874-180888`, `:181066`). Savings per key for this row and the three below: `plans/2026-09-30-session-start-token-cuts.md` | A renamed key or value silently returns the tool, ~2.0k tokens, to every roster. Check: `jq '[.request.tools[].name]'` on a capture's first main request has no `SendFeedback`. |
| `settings.json` `permissions.deny`: `ReportFindings`, `ScheduleWakeup` | the two tool names; the roster filter dropping a tool a deny rule names (2.1.88 `src/tools.ts:268`; 2.1.269's mid-session arm is the string `A permissions deny rule now blocks this tool`, `src/chunk-dbb93264.js:161288`) | A renamed tool silently returns ~2.5k tokens. The intended losses: `/code-review` reports as text, self-paced `/loop` is gone (interval `/loop` and `Monitor` stay). Same check as the row above. |
| `settings.json` `skillOverrides` | the key and its values `on`/`name-only`/`user-invocable-only`/`off` (`src/chunk-3vd4nzwp.js:4871`); lookup by `name`, then `unqualifiedName` (`z7t`, `src/chunk-pmgcy9dx.js:181`); `m_e` returns `on` for `source === "plugin"` (`:207`), so no plugin skill can be overridden | A renamed key or value silently restores every description, ~2.5k tokens, and the prompt line `A skill listed without a description` then governs nothing. Check: a capture's skills listing shows the 16 `use only if invoked` repo skills bare. |
| `settings.json` `env.ENABLE_CLAUDEAI_MCP_SERVERS: "false"`, `env.CLAUDE_CODE_ENABLE_CFC: "false"` | `fo(process.env.ENABLE_CLAUDEAI_MCP_SERVERS)` in the connector fetch `j0o` (`src/chunk-dbb93264.js:75370`); `Aet()` reading `a.CLAUDE_CODE_ENABLE_CFC` after the `--chrome` flag and before `claudeInChromeDefaultEnabled` (`:221116-221125`); both parsed by `fo`/`He` (`src/chunk-jbr76rrs.js:18-23`: `false`/`0`/`no`/`off`); settings `env` is `Object.assign`ed over `process.env` source by source (`applyConfigEnvironmentVariables`, `src/chunk-by7kenyn.js:352`), and the project-scope blocklist `b` names neither (`:50`), so a project `.claude/settings.json` may set either back to `"true"` and a launcher export cannot | A renamed variable silently returns the connectors (~1.9k) or Chrome (~2.1k). Check: the capture has no `mcp__claude_ai_*` tool and no `claude-in-chrome` skill; `claude.sh --chrome` (cc's own flag, which `Aet` reads first) brings Chrome back for one session. |

### 3.2 Mirrors of cc's own algorithms — re-read the source, don't just test

`src/claude_config/env_context/` reimplements cc behaviour and must track it:
`environment.py`: `resolve_shell` ≙ `das()`, `_executable` ≙ `cbt()` (incl. the `--version`
fallback that makes a bare `CLAUDE_CODE_SHELL=bash` resolve), `worktree_common_dir` ≙ `pP()`,
`git_snapshot` ≙ `ADe()` (`chunk-dbb93264.js:69331-69369`: `--no-optional-locks status --short
--ignore-submodules=dirty`, `log --oneline -n 5`, the 2000-character cap); `scratchpad.py:22-54`
(path algorithm; past the 200-char slug limit cc appends a hash and this module raises);
`drift.py:42-46` and `:187-208` (anchor, window and timeout
constants tuned to the binary layout).

### 3.2b Knobs that are unset here, and what each would do if set

Nothing here sets them; each would silently change behaviour a row above asserts. Same shape as
`CLAUDE_AUTO_BACKGROUND_TASKS` in `docs/subagent-backgrounding.md`.

| Unset knob | What setting it would do here |
|---|---|
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` (2.1.257) | One model for every subagent, ignoring per-spawn and agent-definition overrides — silently voiding every `model:` in `agents/*.md`. |
| `CLAUDE_CODE_ENABLE_TODO_TOOLS` (2.1.268) | Restores the task-tracking tools (`TodoWrite`, `TaskCreate/Get/Update/List`), otherwise offered only to older models. |
| `CLAUDE_CODE_DISABLE_1M_CONTEXT` | Makes `Rc()` false, so the `[1m]` suffix both provider launchers default to stops resolving to 1,000,000: `zai.sh` falls to 200,000, `kimi.sh` to its `CLAUDE_CODE_MAX_CONTEXT_TOKENS`. Neither says anything. |
| `CLAUDE_CODE_ARTIFACT_TOOLSET` (`c_()`, `src/chunk-fqa6n2gt.js:3761`; GrowthBook `tengu_cobalt_plinth_damson`) | Splits Artifact into an 8,734-token main tool plus three deferred add-ons; measured in `notes/artifact-tool-roster-cost.md`. Any value enables it, `0` included. Undocumented and unreleased; inert while `enableArtifact` is off. |

### 3.3 Pins to re-pin vs. records to leave alone

**Re-pin:** `docs/env-context-manifest.json` (version, 24 window literals, 3 required-literal
counts) — via `--update`, which refuses to write a count of 0. The two vendored skills under
`skills/` — via `skilldiff.sh --update`, never by hand.

**Re-verify the claim, keep the label:** every version banner under `docs/`, `skills/cc-history`,
`output-styles/README.md` and `agent-tools/CLAUDE.md`, and the first-byte-watchdog window in
`scripts/intercept/README.md`, "Pass-through streaming".

**Do NOT re-pin — dated records of an older build, and rewriting them destroys the evidence:**
everything under `notes/`, `plans/`, `docs/superpowers/plans/` and `specs/`, the synthetic
version strings in `tests/test_env_context.py` and `tests/test_model_visibility.py`, the captured
artifacts under `docs/system-prompt-snapshot/**` (regenerated wholesale, never hand-edited).

### 3.4 Snapshot-capture mechanics that break on upgrade

`docs/system-prompt-snapshot/capture.py`: the trust-dialog cursor reader (`:351-369` — the
default already flipped once between 2.1.235 and 2.1.269), the main-request selector
(`:596-606`), the `cc_is_subagent=true` billing-header marker (`:611-624`).
`regenerate.py:261-266` excludes the `defer_loading` placeholder. `render_capture.py` derives
`prompt.md` and `tools/` from each `request.json`, and `tests/test_snapshot_rendering.py` fails
when the tracked files drift from it. Every character count and `system_tokens` figure in
`README.md` and `what-the-model-gets.md` is derived from these files — re-derive, don't adjust.

## 4. Still to check — as of 2026-09-12, Claude Code 2.1.269

Open items with what would retire each. Delete an entry when it is closed; add one when you find
a new gap rather than leaving it in a session transcript.

**Re-review the artifact construction from the ground up — at the next release, whatever the
checks say** (added 2026-09-30, on 2.1.269). Three artifacts rest on premises a release can void
without any check firing: `settings.json` `enableArtifact: false`; the vendored
`skills/artifact-design` and `skills/artifact-diagramming` with `skilldiff.sh`; the §3.2b
`CLAUDE_CODE_ARTIFACT_TOOLSET` row. Numbers: `notes/artifact-tool-roster-cost.md`. Each premise,
with the string marker that re-finds its code:

- **No user knob defers a first-party tool** — `shouldDefer: !1` on the Artifact tool object
  (`src/chunk-q5zwjg9j.js:13099`); the deferral predicate opening `if (e.alwaysLoad === !0)
  return !1;` (`src/chunk-4zcseazt.js:1052`). A release that lets a built-in defer retires the
  key, the copies and `skilldiff.sh` together: the construction exists only because it cannot.
- **The skills leave with the tool** — `isEnabled: TI` on the built-in registrations; grep
  `dataviz-callout` for the chunk (`src/chunk-s7akwrx2.js:464`, `:483`).
- **The built-in's text is generated, not stored** — the asset goes through
  `.trimStart().replace("<!-- dataviz-callout -->", jn)` and then `nJn`
  (`src/chunk-s7akwrx2.js:472`; `nJn` at `src/chunk-qza9q751.js:245-253`). Re-read that whole
  chain: a new placeholder, prefix or substitution changes what the built-in says while the
  asset, and therefore `skilldiff.sh`, stay unchanged. The delivered text is measurable — with
  the key on, the body lands as the `user` record after the `Skill` call; the 22 such records
  here carry neither the dataviz paragraph nor the comment.
- **The off-wins gate and the `/config` row** — `enableKey: "enableArtifact"`
  (`src/chunk-fqa6n2gt.js:9896`), `gl()` (`:9838`), the Artifacts row
  (`src/chunk-ve1cwn02.js:753`). Any of them moving moves the in-session toggle.
- **The split** — `CLAUDE_CODE_ARTIFACT_TOOLSET` / `tengu_cobalt_plinth_damson`
  (`src/chunk-fqa6n2gt.js:3761`). Shipped by default, the tool costs ~8.7K tokens when on and the
  §3.2b row is wrong; removed, it is dead.

Retire by re-deriving every premise on the new build and rewriting or deleting each artifact it
no longer supports; leave the note as the record it is.

**Pins never re-derived for this build**
- `docs/env-context-manifest.json:3` → `notes/env-context-manifest.md` — byte offsets,
  four-anchor count and the `Shell: PowerShell` probe describe 2.1.235 only.
- `docs/system-prompt-snapshot/README.md` — the two **Not re-verified this round** blocks, under
  "Security-monitor calls" and "Interactive vs `-p` mode differences".
- `docs/system-prompt-snapshot/builtin-output-styles/` — captured from v2.1.87, and 2.1.257's
  notes name a `Proactive` built-in the directory has no file for. Retire by re-capturing every
  built-in style.

**Captures not taken**
- The one configuration this repo runs is uncaptured: `scripts/claude.sh` launches
  `--dangerously-skip-permissions`, every capture takes the default permission mode, and the
  bypass-permissions reminder a `claude.sh` session carries is in none of them. `regenerate.py`'s
  `bypass-permissions` variant defines it; capturing it closes this. 2.1.257 adds a reason:
  `defaultMode: "bypassPermissions"` is ignored from project settings, so the mode's only entry
  points are user settings and `--permission-mode`.
- No backgrounded-session capture for 2.1.269, and two live checks never done: whether the Auto
  Mode reminder fires for a `capture.py` session, and `/feedback` from a logged-in session.

**Opened by the release-notes pass, 2026-09-12** — all 635 bullets of 2.1.247-2.1.268 read
against §3. Each row is a claim here that a bullet puts in doubt.

| What to re-check | Why, and what retires it |
|---|---|
| `docs/agent-tools-status-reference.md` "The kill boundary" | 2.1.257 fixed background commands that detach via `setsid` surviving a **task stop** or **Claude Code exit** — what `agent-tools run --background` is built on. The task-stop half is measured there; the exit half needs a human: start `agent-tools run --background sleep 900`, quit Claude Code, check whether the child survives. |
| `docs/tool-token-limits.md` | 2.1.261 added `bashOutputMaxChars` and `taskOutputMaxChars` (ceiling 128K), 2.1.265 a 1 GB cap on tool results saved to disk; the file carries a 2.1.88 banner and knows neither. Retire on its next re-measurement. |
| `src/claude_config/cc_pretty/` record handling | Three in-window shape changes: subagent progress ticks replace their predecessor (2.1.251); async hook completion notices batch onto one line (2.1.257); nested background subagent results land in the **parent subagent's** transcript (2.1.259). Retire by re-reading real logs. |

**Opened by the 2026-09-16 removal of the `Agent` `PreToolUse` hook** — whether the
`Notification` matchers `agent_needs_input` and `agent_completed` fire now that a subagent can
background again. Retire by backgrounding a subagent deliberately in an interactive session and
watching whether `agent-tools ntfy-hook` is invoked; if they fire, `agent_needs_input` meets the
selection rule.

**Open design questions, not defects**: the `sys_prompt/alan-default-next.md` passage marked
**Not reviewed** under "Deliberate divergences" in `sys_prompt/CLAUDE.md` (predates 2.1.235);
`cc-render-coverage` seeing no selection defects (§2).

**Pre-existing, not upgrade-caused** (absent from the 2.1.235 capture too): `agents/*.md` and
~30 sites under `skills/scripts/` name `Grep`, `Glob`, `TodoWrite` and `Task`, and the live
roster has none of them. `TodoWrite` is a settings decision (`CLAUDE_CODE_ENABLE_TODO_TOOLS=1`,
§3.2b); the others are text edits, and whether the model maps `Task`→`Agent` reliably is
untested.

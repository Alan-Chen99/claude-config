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
| 2 | Re-extract the decompile | in `/repos/claude-code-decompiled`: `npm run extract && npm run link && npm run typecheck` (`npm install` once first) | Chunk hashes **and** line numbers rotate every build. Until this runs, step 6's citation check and `tests/test_model_visibility.py` both pass vacuously. `extract` empties `src/`, `assets/` and `native/` first, so modules the new binary dropped disappear on their own. |
| 3 | Confirm the decompile matches | `grep -m1 -oP '(?<=VERSION: ")[^"]+' /repos/claude-code-decompiled/src/cli.js` | `src/cli.js` is the one stable filename across the 2.1.269 layout change; it carries `VERSION`/`BUILD_TIME`/`GIT_SHA`. Must equal step 1. |
| 4 | Re-sync the editable venv — **canonical checkout only** | from `/repos/claude-config`: `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config uv sync --reinstall-package claude-config` | `check-env-context.sh` runs under this venv, so a stale install loads the old `drift.py`. `--reinstall-package` is required because the package version never bumps. **Run it from a worktree and it repoints the shared venv's editable install at that worktree** (`+ claude-config @ file:///root/claude-config-work2`), breaking every other session once the worktree is deleted — the same hazard as `install.sh`. A worktree has its own venv at `$HOME/.claude/venvs/<basename>`, selected by the `UV_PROJECT_ENVIRONMENT` that `.envrc` exports through direnv, so a worktree needs no step 4. |
| 5 | Check, then re-pin, env-context | `./scripts/check-env-context.sh` → review the `+`/`-`/`~` diff → `./scripts/check-env-context.sh --update` | The diff is the single best summary of what changed in cc's own `# Environment` block. Re-pin only after reading it — `--update` overwrites the evidence. |
| 6 | Resolve every source citation | `bash .claude/skills/update-claude-code/citecheck.sh` | 135 `chunk-*.js:LINE` citations live in tracked files; only 2 are re-derived by any test. Exit 0 = all resolve; 1 = the unresolved ones are named on stdout; 2 = no decompiled tree, i.e. step 2 was skipped. |
| 7 | Rebase the upstream-derived prompts | `python3 scripts/check-prompt-upstream.py`, then the section-key diff it does not do | `sys_prompt/` replaces Claude Code's own system prompt wholesale and the env-context hook re-emits the block that replacement discards, so passages copied from either go stale with no signal and nothing else in this list reads prose. The script needs step 2's tree and exits 2 without it. The procedure, the deliberate divergences and the per-release log are in `sys_prompt/CLAUDE.md`, "Rebasing on an upstream release" — that text governs; this row only says when to run it. |
| 8 | Rebuild and test | `cd agent-tools && cargo build --release && cargo test --release`; `uv run pytest tests/ -q`; `./scripts/check-prompt-coupling.sh` | |
| 9 | Check the renderer against real logs | `ls -t /root/.claude/projects/*/*.jsonl \| head -8 \| uv run cc-render-coverage --quiet` | New record and attachment shapes land here first. |
| 10 | Re-capture the system-prompt snapshots | see `docs/system-prompt-snapshot/README.md` "Regenerating" | Needs step 4's venv, the MITM proxy on 9160, and `CLAUDE_CODE_OAUTH_TOKEN`. Never run two `regenerate.py` in parallel — they share `capture-output/`. |
| 11 | Merge and reinstall | merge to `/repos/claude-config`, then `install.sh` **there only** | Until the merge, `~/.local/bin/agent-tools` and `cc-pretty` still run the old code — the fixes exist but nothing you run uses them. A worktree that runs `install.sh` breaks every other session. |

Expected clean output, as of 2.1.269: `OK: env-context field set matches the installed
binary` / `OK: 15 borrowed passages still match Claude Code 2.1.269` / no citecheck output / `329 passed` / 15 cargo test binaries all `ok` /
`prompt coupling OK` / `8 file(s) checked: clean`.

**Where to run each step.** Steps 4, 10 and 11 touch shared state and belong in the
canonical checkout `/repos/claude-config`. Everything else is worktree-safe and should
be done in a worktree, because steps 5 and 8 rewrite tracked files.

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
| `check-env-context.sh` | Anything outside a ±1000-byte window around `Primary working directory: ` plus three whole-binary string counts. It sees the env block's *field set*, not behaviour. |
| `citecheck.sh` | Whether the cited line still says what the citing text claims. It proves the file exists and is long enough — nothing more. Line numbers shift; a resolving citation can point at unrelated code. |
| `cc-render-coverage` | The default view's **selection**. It renders with `show_all` set and draws needles only from `assistant`/`user` records, so attachment/progress/system records contribute none. It cannot see a record being dropped. |
| `pytest` | Every citation but one. `tests/test_model_visibility.py::test_denylist_still_matches_the_conversion_source` re-derives `_NEVER_VISIBLE_ATTACHMENT_TYPES` from the decompiled source by string marker — and `skipif`s when `/repos/claude-code-decompiled/src` is absent, so it reports success by not running. |
| `check-prompt-coupling.sh` | Claude Code entirely. It greps this repo's own files against each other. |
| `check-prompt-upstream.py` | Everything upstream says that this repo never copied. It re-checks 15 borrowed passages, so a section a release adds — or reworded text this prompt does not carry — is invisible to it. Where a passage occurs more than once it reports that the count moved, not which copy moved. |
| CI | Everything. `.github/workflows/skills-test.yml` runs only `skills/scripts/` tests, only on `skills/scripts/**` paths. No drift check runs in CI. |

## 3. The coupling inventory — what an upgrade can break

### 3.1 Degrades silently (no error, wrong behaviour)

| Where | Reads | Failure mode |
|---|---|---|
| `agent-tools/src/hook_input.rs:13-35` | `session_id`, `tool_name`, `tool_input`, `tool_use_id`, `hook_event_name`, `tool_response` | A renamed field fails the parse; `hook_pre.rs:14-19` then allows passthrough and `hook_post.rs:46-51` returns `Ok(())`. Wrapping just stops happening. |
| `agent-tools/src/hook_post.rs:118-172` | `backgroundTaskId`, `backgroundedByUser`, `backgroundedByTurnAbort`, `backgroundedToDeliverMessage`, `timedOutAfterMs`, `run_in_background` | A rename yields `Cause: not stated by the tool response` instead of an error. 2.1.269 already deleted `assistantAutoBackgrounded`; the replacement fields are what these are. |
| `agent-tools/src/hook_post.rs:22` | `REPORT_BUDGET = 9_000` | Justified by a 2.1.269 measurement that a **local command hook's** stdout escapes the 8,000-char/200-line `additionalContext` cap (the cap sits on `ego`, which only sanitizes cloud-relay and callback hooks). If a release routes local hooks through the sanitizer, reports get truncated to a stub. |
| `agent-tools/src/hook_pre.rs:22`, `hook_post.rs:57` | tool names `Bash`, `Monitor` | A renamed or new shell tool is simply not wrapped. |
| `agent-tools/src/paths.rs:65-105` | `CLAUDE_CODE_SESSION_ID` (read at `:105`) | A rename breaks bare `!` commands. |
| `statusline.sh:5-17` | `.model.display_name`, `.context_window.*`, `.cost.total_cost_usd`, `.workspace.current_dir` | Every field defaults (`// 0`, `// "?"`). A rename shows zeros. |
| `src/claude_config/cc_pretty/parse.py:28`, `:186-374` | record `type` values | `extra: "allow"`, so new fields are safe; a renamed record type becomes `UnknownRecord` and vanishes from the render. |
| `settings.json:19-50` | `Notification` matchers `permission_prompt`, `idle_prompt`, `elicitation_dialog` | Literal strings cc must still emit. |
| `settings.json:82-92` | `PreToolUse` matcher `"Agent"` + `jq` rewriting `run_in_background` to `false` | With `CLAUDE_CODE_FORK_SUBAGENT=0` this is what makes subagents synchronous. If either half stops working, `sys_prompt/alan-default-next.md:214-216` becomes a lie the model acts on. |
| `settings.json:116-127` | `PostToolUseFailure` | A distinct event name. Folded back into `PostToolUse` and errored calls stop being delivery points. |
| `sys_prompt/alan-default-next.md`, and any `agents/*.md` named after a built-in agent | passages copied verbatim from Claude Code's own system prompt | `--system-prompt-file` drops every upstream section, so a rule upstream reworded or added never arrives and the copy here keeps saying the old thing. `sys_prompt/CLAUDE.md` governs: procedure, deliberate divergences, per-release log. |
| `scripts/claude.sh:13` | `CLAUDE_CODE_DISABLE_AGENT_VIEW=1` | Without it an agent-view fork drops `--system-prompt-file` and silently runs the stock prompt. |

### 3.2 Mirrors of cc's own algorithms — re-read the source, don't just test

`src/claude_config/env_context/` reimplements cc behaviour and must track it:
`environment.py:26-66` (`resolve_shell` ≙ cc's `das()`), `:95-116` (`worktree_common_dir` ≙ `pP()`),
`scratchpad.py:22-54` (path algorithm, incl. the 200-char slug limit past which cc appends a hash
this module does not implement — it raises instead), `render.py:41-50` (`STASH_CAUTION` copied
verbatim from cc's `KUt`, and pinned by `scripts/check-prompt-upstream.py` — `check-env-context.sh`
covers the block's field set, not its wording), `drift.py:42-46` (anchor and window constants tuned to the binary layout),
`drift.py:186-203` (a timeout budget whose comment says to re-check the sum if any of the three
numbers moves).

### 3.3 Pins to re-pin vs. records to leave alone

**Re-pin:** `docs/env-context-manifest.json` (version, 24 window literals, 3 required-literal counts)
— via `--update`, which refuses to write a count of 0 because a zero is a permanently-passing
assertion.

**Re-verify the claim, keep the label:** the version banners in `docs/system-prompt-anatomy*.md`,
`docs/tool-token-limits.md`, `docs/background-sessions.md`, `docs/system-prompt-snapshot/README.md`,
`skills/cc-history/SKILL.md`, `output-styles/README.md`, `agent-tools/CLAUDE.md`,
`docs/agent-tools-status-reference.md`.

**Do NOT re-pin — these are dated records of an older build, and rewriting them destroys the
evidence:** everything under `notes/` (each carries a staleness banner), `plans/`,
`docs/superpowers/plans/` and `specs/`, the synthetic version strings in `tests/test_env_context.py`
and `tests/test_model_visibility.py`, the captured artifacts under `docs/system-prompt-snapshot/**`
(regenerated wholesale, never hand-edited), and `prompt-tests/runs/**`.

### 3.4 Snapshot-capture mechanics that break on upgrade

`docs/system-prompt-snapshot/capture.py`: the trust-dialog cursor reader (`:351-369` — the default
already flipped once between 2.1.235 and 2.1.269), the main-request selector (`:596-606`), the
`cc_is_subagent=true` billing-header marker (`:612-624`). `regenerate.py:245-250` excludes the
`defer_loading` placeholder. Every character count and `system_tokens` figure in
`README.md` and `what-the-model-gets.md` is derived from these files — re-derive them, don't
adjust them by hand.

## 4. Still to check — as of 2026-09-12, Claude Code 2.1.269

Open items with what would retire each. Delete an entry when it is closed; add one when you find a
new gap rather than leaving it in a session transcript.

**Known defect, not yet fixed**
- `src/claude_config/cc_pretty/render.py:973-983` — the skeleton renderer reads only
  `a.content` and `continue`s when empty, so it emits **no line at all** for an attachment whose
  payload lives in the record-level `rendered` array. Measured: 1,097 such records across every log
  on disk, 15 subtypes (`environment`, `instructions`, `session_context`, `model`,
  `agent_listing_delta`, `deferred_tools_delta`, `auto_mode`, `output_style`, …), **every one of them
  version 2.1.269 and zero in any older log** — so this is upgrade-caused. The default view was fixed
  (`render.py:702-726`) and the visibility selector was fixed (`main.py:175`, in
  `attachment_is_model_visible`, `:162-184`); the skeleton was
  not. It matters because `skills/session-analysis/SKILL.md` mandates the skeleton as reading
  substrate and claims "one line per content block". `cc-render-coverage` is structurally unable to
  catch this (§2). Retire when render.py falls back to `rendered` and a test covers the skeleton path.

**Traced against an older build, never re-traced**
- `CLAUDE.md:54` — which SessionStart call sites pass `model` into the payload builder `uIn`
  (2.1.235).
- `docs/env-context-manifest.json:3` → `notes/env-context-manifest.md` — byte offsets, four-anchor
  count and the `Shell: PowerShell` probe describe 2.1.235 only.
- `agent-tools/src/hook_pre.rs:29` cites `queryHelpers.ts:262-272` for `updatedInput` being a full
  replacement rather than a merge — a 2.1.88-era path never re-resolved to the chunk layout. The
  behaviour is relied on; the citation is unresolvable.
- `src/claude_config/cc_pretty/main.py:133-137` — `_HOOK_STDOUT_VISIBLE_EVENTS` is asserted only
  against itself. Unlike the denylist beside it, no test re-derives it from source.
- `docs/system-prompt-snapshot/README.md:889-905` — two "Not re-verified this round" blocks
  (security-monitor calls; interactive-vs-`-p` differences).
- `docs/system-prompt-snapshot/builtin-output-styles/` — pinned to v2.1.87 with no staleness banner.

**Found in the 2.1.269 audit, never actioned** (from session `f4987f69`, 2026-09-12)
- Four integration-surface items reported as new since 2.1.235 and not followed up:
  `subagentStatusLine`, `PermissionRequest`, `agent_needs_input`, `quota_auto_resume`.
- Two env vars whose effect was "not fully determinable": `CLAUDE_CODE_CHILD_SESSION`,
  `CLAUDE_CODE_SHELL`.
- A `"defer"` permission decision new relative to what `CLAUDE.md` documents.
- Dropped at a `/compact` boundary and never revisited: a 2.1.269 backgrounded-session capture,
  whether the Auto Mode reminder fires for a `capture.py` session, and testing `/feedback` from an
  interactively-logged-in session.

**Open design questions, not defects**
- Whether to trim `agent-tools env-context` now that 2.1.269 sends its own `# Environment` block to
  `--system-prompt-file` sessions as a `messages[]` attachment. What the hook still uniquely adds:
  the shell the Bash tool actually runs, the session id, the worktree's parent checkout, the drift
  note. Recorded at `src/claude_config/env_context/__main__.py:10-22` as a finding, not a decision.
- One passage `sys_prompt/alan-default-next.md` borrowed from upstream diverges with no recorded
  reason and nothing else in the prompt covering it — the row marked **Not reviewed** under
  "Deliberate divergences" in `sys_prompt/CLAUDE.md`. It predates the 2.1.235 baseline, so the
  2.1.269 rebase neither caused nor closed it.
- `cc-render-coverage` cannot see selection defects at all (§2). Extending it is what would have
  caught the skeleton bug.

**Pre-existing, not upgrade-caused** (verified absent from the 2.1.235 capture too, so don't
re-diagnose these as upgrade fallout)
- `README.md:5-9` tells the reader to run `~/claude-config/hooks/install.sh`; neither the path nor a
  `hooks/` directory exists.
- `agents/*.md` and ~30 sites under `skills/scripts/` name `Grep`, `Glob`, `TodoWrite` and `Task`;
  the live roster has none of them. Whether the model reliably maps `Task`→`Agent` is untested.
- `scripts/check-env-context.sh:38` cites `agent-tools/src/main.rs:389`; the line is now `:437`.

## Common mistakes

| Mistake | What actually happens |
|---|---|
| Running the checks before re-extracting the decompile | `citecheck.sh` and the denylist test both pass without testing anything — a stale tree still has the files, and they are still long enough. `check-prompt-upstream.py` is the only one that refuses, by comparing `src/cli.js` against `claude --version`. |
| Treating a green `cc-render-coverage` as "the renderer is fine" | It never looks at attachment records or at what the default view selects. |
| Grepping for the old version string and calling it done | That finds stale *references*. It cannot find a live code path whose input shape changed underneath it — which is how the skeleton bug (§4) survived a full audit. |
| Diffing the prompt captures and calling that the upstream delta | A capture is one environment on one day, and most prompt sections sit behind a server-resolved flag. `act_dont_rederive` vanished between the 2.1.235 and 2.1.269 captures while staying in both binaries. |
| Re-pinning a `notes/` file to the new version | Destroys a dated record of the older build. Those files are evidence, not documentation. |
| Fixing, committing, and stopping | Nothing you run changes until the merge to `/repos/claude-config` and a rebuild — the installed binary and the editable venv both resolve there, by design. |
| Running `install.sh` from a worktree | Repoints `~/.local/bin` at the worktree; deleting it later breaks every session. |

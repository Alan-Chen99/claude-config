---
name: update-claude-code
description: Use when Claude Code has been upgraded and this repo must be re-checked, or when a session reports an env-context drift note or an unresolvable `chunk-*.js:LINE` citation. ALSO read BEFORE editing any file naming a Claude Code hook field, env var (`CLAUDE_CODE_*`), settings key, hook event, tool name, JSONL record or attachment type, statusline field, CLI flag, or decompiled-source line — don't skip because the edit looks small; that code is version-coupled and belongs in this skill's inventory.
---

# Updating after a Claude Code release

This repo reads, imitates and cites Claude Code, and a release breaks it **silently**: `serde`
ignores unknown keys, the pydantic models allow extras, `statusline.py` defaults a missing field
to `0`, and the tests that re-derive cc constants `skipif` without the decompile. **A check that
cannot fail is not a check**: a green run is done once what each check misses has been checked
by hand.

| Reference | Read when |
| --- | --- |
| `references/inventory.md` | before editing a file that reads cc (grep it for the path); step 13 |
| `references/checks.md` | before trusting a green check or re-pinning anything; step 13 |
| `references/still-to-check.md` | step 13: open items, per-upgrade re-reads, decisions waiting on cc |

## Editing a coupled file

Grep `references/inventory.md` for the path and for each cc name the edit touches. In the same
change keep those rows true, and add one for every new read of a cc data shape, env var, hook
field, settings key, tool name, record type or source line: a coupling nobody recorded is one
nobody re-checks. Cite cc source by a string literal from it, which the next build still
contains; `chunk-*.js:LINE` and minified names rotate per build. Same-repo line citations are
checked by nothing — re-check any that point into the file you edited.

## The runbook, in order

Order is load-bearing: steps 4, 7, 8 and 9 read the tree step 2 rebuilds, and before it they
check the old build and pass. Steps 5 and 15 repoint installs every session shares and run in
`/repos/claude-config` **only**; everything else runs in a worktree, as steps 2, 6 and 9
rewrite tracked files.

| # | Step | Command | Why here |
|---|---|---|---|
| 1 | Confirm the new version | `claude --version` | Everything compares against it. For a build not yet installed, every check that runs the binary takes `CLAUDE_CODE_EXECPATH=<native ELF>` and `PATH=<its bin dir>:$PATH` — `check-prompt-upstream.py` too. |
| 2 | Re-extract the decompile | in `/repos/claude-code-decompiled`: `npm run extract && npm run link && npm run typecheck` (`npm install` once first; `CLAUDE_BINARY=<native ELF>` when `PATH` does not resolve the build); then `bash .claude/skills/update-claude-code/skilldiff.sh` (`--update` takes the new text). Search the decompile through a `sonnet` Explore subagent: `haiku` sweeps gave false NOT FOUNDs | Hashes and line numbers rotate every build. |
| 3 | Confirm the decompile matches | `grep -m1 -oP '(?<=VERSION: ")[^"]+' /repos/claude-code-decompiled/src/cli.js` | Must equal step 1. |
| 4 | Read upstream's release notes | `.claude/skills/update-claude-code/changelog.py <previous version>` | They name the reason behind a diff nothing else here can. The binary embeds only the last few releases; for a longer jump the script names `~/.claude/cache/changelog.md`, which can be stale (it stopped at 2.1.292): fetch the GitHub raw CHANGELOG URL it also names. |
| 5 | Re-sync the editable venv — **canonical checkout only** | from `/repos/claude-config`: `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config uv sync --reinstall-package claude-config` | The package version never bumps. A worktree has its own venv (`.envrc`) and skips this step: from one it repoints the shared venv and breaks every other session. |
| 6 | Check, then re-pin, env-context | `./scripts/check-env-context.sh` → read the `+`/`-`/`~` diff → `./scripts/check-env-context.sh --update` | First confirm its `installed:` line names the new build: `drift.py` reads `CLAUDE_CODE_EXECPATH` before `PATH`, and a tool subprocess inherits the session's. Read the diff against `src/claude_config/env_context/render.py` and cc's env-block builder (grep `Scratchpad directory:`) before `--update`: the window misses fields. |
| 7 | Resolve every source citation | `bash .claude/skills/update-claude-code/citecheck.sh` | Exit 1 names each unresolved citation: re-find the code by a string literal and rewrite it. Exit 2: no tree. Dated records are skipped, and never re-pinned. |
| 8 | Rebase the upstream-derived prompts | `python3 scripts/check-prompt-upstream.py`, then the section-key diff it does not do | `sys_prompt/` replaces cc's system prompt wholesale, so a copied passage goes stale with no signal. Procedure: `docs/prompt-rebase.md`. |
| 9 | Rebuild and test | `cd agent-tools && cargo build --release && cargo test --release`; `uv run pytest tests/ -q`; `./scripts/check-prompt-coupling.sh`; `uv run doc-budget` | `test_hook_emits_the_envelope` runs the installed `claude` (an uninstalled build needs step 1's override). A failing `test_denylist_still_matches_the_conversion_source` means the release changed which attachment types render empty: re-derive the set, never the assertion. |
| 10 | Check the renderer against real logs | `ls -t /root/.claude/projects/*/*.jsonl \| head -8 \| uv run cc-render-coverage --quiet` | The logs must be the new build's (a capture logs elsewhere). `missing_content`: a shape the renderer does not model; `renderer_truncation`: a hard cap ignoring `--tool-max`. |
| 11 | Re-capture the system-prompt snapshots | `docs/system-prompt-snapshot/README.md`, "How to re-capture" | Needs an authenticated `claude` (`CLAUDE_CODE_OAUTH_TOKEN`, which cc strips from tool subprocesses, or `~/.claude/.credentials.json`) and an isolated `CLAUDE_CONFIG_DIR`: a stock launch writes through `~/.claude/settings.json`'s symlink into the checkout. |
| 12 | Read the capture in full | `git diff docs/system-prompt-snapshot` | Every configuration and tool file, descriptions **and input schemas**. |
| 13 | Re-verify by hand what no check covers | every row of `references/inventory.md` — find its code by the literal, then re-read the claim — and of `references/checks.md`; every `references/still-to-check.md` item | No check re-reads what a row claims. |
| 14 | Re-derive what the fired checks were premises *for* | for each premise steps 6, 8, 12 and 13 falsified, `git grep` its wording across tracked files | Their remedies repair conformance and leave everything built on the old premise standing: re-derive or retire it. A mirror that now matches cc exactly also reads as `OK`. |
| 15 | Merge and reinstall | merge to `/repos/claude-config`, then `install.sh` **there only** | Until then `~/.local/bin/agent-tools` and `cc-pretty` run the old code; `install.sh` from a worktree breaks every other session. |

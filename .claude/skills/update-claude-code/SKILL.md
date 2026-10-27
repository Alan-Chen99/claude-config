---
name: update-claude-code
description: Use after a Claude Code upgrade, on an env-context drift note or unresolvable `chunk-*.js:LINE` citation, and before any edit, however small, to a file naming a Claude Code hook, env var, settings key, tool, JSONL record or attachment type, statusline field, CLI flag or decompiled-source line.
---

# Updating after a Claude Code release

This repo reads, imitates and cites Claude Code, and a release breaks it **silently**: parsers
ignore unknown keys, readers default missing fields, and tests skip without the decompile. **A
check that cannot fail is not a check**: a green run is done once what each check misses has been
checked by hand.

| Reference | Read when |
| --- | --- |
| `references/inventory.md` | editing a coupled file; step 13 |
| `references/checks.md` | before trusting a green check or re-pinning anything; step 13 |
| `references/still-to-check.md` | step 13: open items, decisions waiting on cc |

## Editing a coupled file

Grep `references/inventory.md` for the path and for each cc name the edit touches. In the same
change keep those rows true, and add one for every new coupling of a kind the inventory's
opening line names: one nobody recorded is one nobody re-checks. Cite cc source by a string
literal from it, which the next build still contains; `chunk-*.js:LINE` and minified names
rotate per build. Same-repo line citations are checked by nothing — re-check any that point
into the file you edited.

## The runbook, in order

Order is load-bearing: steps 4, 7, 8 and 9 read the tree step 2 rebuilds, and before it they
check the old build and pass. Steps 5 and 15 repoint installs every session shares and run in
`/repos/claude-config` **only**; everything else runs in a worktree, as steps 2, 6 and 9
rewrite tracked files.

| # | Step | Command | Why here |
|---|---|---|---|
| 1 | Confirm the new version | `claude --version` | Everything compares against it. For a build not yet installed, every check that runs the binary takes `CLAUDE_CODE_EXECPATH=<native ELF>` and `PATH=<its bin dir>:$PATH` — `check-prompt-upstream.py` too. |
| 2 | Re-extract the decompile | in `/repos/claude-code-decompiled`: `npm run extract && npm run link && npm run typecheck` (`CLAUDE_BINARY=<native ELF>` when `PATH` does not resolve the build); then `bash .claude/skills/update-claude-code/skilldiff.sh` (`--update` takes the new text) | Hashes and line numbers rotate every build. |
| 3 | Confirm the decompile matches | `grep -m1 -oP '(?<=VERSION: ")[^"]+' /repos/claude-code-decompiled/src/cli.js` | Must equal step 1. |
| 4 | Read upstream's release notes | `.claude/skills/update-claude-code/changelog.py <previous version>` | They name the reason behind a diff nothing else here can. For releases older than the binary embeds, fetch the GitHub URL it prints, not the cache copy, which goes stale. |
| 5 | Re-sync the editable venv | from `/repos/claude-config`: `UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config uv sync --reinstall-package claude-config` | The package version never bumps; a worktree has its own venv (`.envrc`). |
| 6 | Check, then re-pin, env-context | `./scripts/check-env-context.sh` → read the `+`/`-`/`~` diff → `./scripts/check-env-context.sh --update` | First confirm its `installed:` line names the new build: `drift.py` reads `CLAUDE_CODE_EXECPATH` before `PATH`, and a tool subprocess inherits the session's. Before `--update`, read the diff against `src/claude_config/env_context/render.py` and cc's env-block builder (grep `Scratchpad directory:`). |
| 7 | Resolve every source citation | `bash .claude/skills/update-claude-code/citecheck.sh` | Exit 1 names each unresolved citation: re-find the code by a string literal and rewrite it. Exit 2: it could not run. Dated records are skipped, and never re-pinned. |
| 8 | Rebase the upstream-derived prompts | `python3 scripts/check-prompt-upstream.py`, then the section-key diff it does not do | `sys_prompt/` replaces cc's system prompt wholesale, so a copied passage goes stale with no signal. Procedure: `docs/prompt-rebase.md`. |
| 9 | Rebuild and test | `cd agent-tools && cargo build --release && cargo test --release`; `uv run pytest tests/ -q`; `./scripts/check-prompt-coupling.sh`; `uv run doc-budget` | `test_hook_emits_the_envelope` runs `claude`, so step 1's override applies. A failing `test_denylist_still_matches_the_conversion_source`: re-derive the set, never the assertion. |
| 10 | Check the renderer against real logs | `ls -t /root/.claude/projects/*/*.jsonl \| head -8 \| uv run cc-render-coverage --quiet` | The logs must be the new build's (a capture logs elsewhere). |
| 11 | Re-capture the system-prompt snapshots | `docs/system-prompt-snapshot/README.md`, "How to re-capture" | Follow it whole: a stock launch writes through `~/.claude/settings.json`'s symlink into the checkout. |
| 12 | Read the capture in full | `git diff docs/system-prompt-snapshot` | Every configuration and tool file, descriptions **and input schemas**. |
| 13 | Re-verify by hand what no check covers | every row of `references/inventory.md` — find its code by the literal, then re-read the claim — and of `references/checks.md`; every `references/still-to-check.md` item | No check re-reads what a row claims. |
| 14 | Re-derive what the fired checks were premises *for* | for each premise steps 6, 8, 12 and 13 falsified, `git grep` its wording across tracked files | Their remedies repair conformance and leave everything built on the old premise standing: re-derive or retire it. A mirror that now matches cc exactly also reads as `OK`. |
| 15 | Merge and reinstall | merge to `/repos/claude-config`, then `install.sh` **there only** | Until then `~/.local/bin/agent-tools` and `cc-pretty` run the old code. |

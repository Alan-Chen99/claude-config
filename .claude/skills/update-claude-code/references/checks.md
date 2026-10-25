# What each check misses, and what to re-pin

A green run leaves all of this open; runbook step 13 checks it by hand.

| Check | Blind to |
|---|---|
| `check-env-context.sh` | All but a ±1000-byte window around `Primary working directory: ` (on 2.1.310 it reaches 4 env strings and no longer reaches `Scratchpad directory: `), and that only partly: cc's field templates no longer sit together, so fields leave the window, and one under its 12-byte floor makes no `+` line even inside it. Behaviour, and whether the mirror is still wanted: cc delivering the same block reads as `OK`. |
| `citecheck.sh` | Whether a cited line still says what the citing text claims: it proves the file exists and is long enough. Blind to `src/cli.js:N` citations. Same-repo, relative (`:49123`) and dated-record citations are checked by nothing; a pin by string, as `check-prompt-coupling.sh` does, is the only check here with teeth. Under 100 citations it exits 2. |
| `cc-render-coverage` | The default view's selection: it renders with `show_all` and takes needles only from `assistant`/`user` records, so a dropped record is invisible. |
| `pytest` | Every cc citation but what `tests/test_model_visibility.py`, `test_settings_order.py` and `test_changelog.py` re-derive from the decompile — and all three `skipif` without it, passing by not running. |
| `check-prompt-coupling.sh` | Claude Code entirely: it greps this repo's files against each other. |
| `settings-order.py` | Which keys belong in `settings.json` and their values — it checks order and byte format. It reads the schema literal, not the writer, so a writer change leaves the order right and the file churning; keys the literal does not list it refuses to place (exit 1). |
| `check-prompt-upstream.py` | Everything upstream says that this repo never copied: it pins 13 passages, so an added section is invisible, as are what a `${…}` interpolation holds and cc's wording that arrives through `messages[]`. It matches the binary, not the served text — server flags choose branches (`tengu_ochre_wren`, the opening line). |
| `changelog.py` | What upstream did not write down, and releases older than the embedded window. |
| the capture diff (step 12) | Every key in this repo's `settings.json`: a capture runs with `--setting-sources project,local` and isolated, so user settings, skills, agents, plugins and the user `CLAUDE.md` never reach it — it shows stock behaviour. Deferred tools appear as names. One account on one day: most sections sit behind server flags, so an absent section is not a removed one. A `thread: continue` request shows one system block and maybe no tools; only a session's first request reads whole. |
| `skilldiff.sh` | What the loader does to an asset (`still-to-check.md`, "Every upgrade"). `NO ASSET` is what rename and removal both look like; its `VENDORED` list is fixed. |
| CI | Everything above: `ci.yml` runs pytest, `cargo test` and `check-prompt-rationale.sh` only, and the one real drift-check case skips without an installed Claude Code. |

## Re-pin, re-verify, or leave alone

**Re-pin:** `docs/env-context-manifest.json` via `check-env-context.sh --update`, which refuses
to write a count of 0 and leaves `_comment` alone — re-read that by hand; the two vendored skills
via `skilldiff.sh --update`, never by hand.

**Re-verify the claim, keep the label:** every version banner under `docs/`, `skills/cc-history`
and `output-styles/README.md`, and the first-byte-watchdog window in
`scripts/intercept/README.md`, "Pass-through streaming".

**Never re-pin** — dated records of an older build, which rewriting destroys: everything under
`notes/`, `plans/` and `docs/superpowers/` and the prompt-test fixtures (`citecheck.sh` skips
all four), the synthetic version strings in `tests/test_env_context.py` and
`tests/test_model_visibility.py`, and the captures under `docs/system-prompt-snapshot/**`
(regenerated wholesale, never hand-edited).

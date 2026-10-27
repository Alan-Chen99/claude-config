# What each check misses, and what to re-pin

| Check | Blind to |
|---|---|
| `check-env-context.sh` | All but a ±1000-byte window around `Primary working directory: `, and that only partly: cc's field templates no longer sit together, so fields leave the window, and one under its 12-byte floor makes no `+` line even inside it. Behaviour, and whether the mirror is still wanted: cc delivering the same block reads as `OK`. |
| `citecheck.sh` | Whether a cited line still says what the citing text claims: it proves the file exists and is long enough. `src/cli.js:N` and relative (`:49123`) citations. |
| `cc-render-coverage` | The default view's selection: it renders with `show_all` and takes needles only from `assistant`/`user` records, so a dropped record is invisible. |
| `pytest` | Every cc citation but what `tests/test_model_visibility.py`, `test_settings_order.py` and `test_changelog.py` re-derive from the decompile, and those pass without it by not running. |
| `check-prompt-coupling.sh` | Claude Code entirely: it greps this repo's files against each other. |
| `settings-order.py` | Which keys belong in `settings.json` and their values. It reads the schema literal, not the writer, so a writer change leaves the order right and the file churning. |
| `check-prompt-upstream.py` | Everything upstream says that this repo never copied: it pins a fixed set of passages, so an added section is invisible, as are what a `${…}` interpolation holds and cc's wording that arrives through `messages[]`. It matches the binary, not the served text — server flags choose branches (`tengu_ochre_wren`, the opening line). |
| `changelog.py` | What upstream did not write down. |
| `skilldiff.sh` | What the loader does to an asset (`still-to-check.md`, "Every upgrade"). `NO ASSET` is what rename and removal both look like. |
| CI | Every cc coupling: `ci.yml` has neither the decompile nor an installed Claude Code, so what re-derives from either skips. |

## Re-pin, re-verify, or leave alone

**Re-pin** only through `check-env-context.sh --update`, which leaves the manifest's `_comment`
alone (re-read that by hand), and `skilldiff.sh --update`.

**Re-verify the claim, keep the label:** every version banner under `docs/`, `skills/cc-history`
and `output-styles/README.md`, and the first-byte-watchdog window in
`scripts/intercept/README.md`, "Pass-through streaming".

**Never re-pin** — dated records of an older build, which rewriting destroys: everything under
`notes/`, `plans/` and `docs/superpowers/` and the prompt-test fixtures (`citecheck.sh` skips
all four), the synthetic version strings in `tests/test_env_context.py` and
`tests/test_model_visibility.py`, and the captures under `docs/system-prompt-snapshot/**`
(regenerated wholesale, never hand-edited).

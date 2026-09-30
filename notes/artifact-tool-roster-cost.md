# The Artifact tool is 60% of the tool roster and cannot be deferred

Measured 2026-09-30 on Claude Code **2.1.269**: `claude-opus-5` captures by
`docs/system-prompt-snapshot/capture.py` under the credentials-file login every session here
uses. `settings.json` carries `enableArtifact: false` because of these numbers — the settings
key rather than the env var because only the key leaves the `/config` Artifacts row toggleable
inside a session.

> **Dated record.** Citations and numbers are 2.1.269, one account, one day. Do not re-pin;
> re-measure — the committed pair is `logged-in` / `logged-in-no-artifact` in
> `docs/system-prompt-snapshot/regenerate.py`, the split capture the command under "The split".

## The cost

Same credential, model and day (`opus-5/logged-in` vs `logged-in-no-artifact`, the second taken
with `CLAUDE_CODE_DISABLE_ARTIFACT=1`):

| | with Artifact | without |
| --- | --- | --- |
| upfront tools | 14 | 13 |
| tool tokens (`regenerate.py`'s figure) | 33,465 | 13,255 |
| deferred names | 57 | 57 |
| built-in `artifact-design`, `artifact-diagramming`, `artifact-capabilities` | listed | absent |
| system prompt tokens | 4,759 | 4,758 |

Counted a second way — one `capture.count_tokens` call over the request's `tools` array — the
`logged-in` request is 34,177 tokens: `Artifact` alone 20,496 (description 30,113 characters,
schema 29,521), the other seventeen tools 13,681. The two totals are different baselines
(`regenerate.py` counts the array's marginal cost over the captured system prompt, this one
over a one-word message); every comparison below uses the second.

The tokens buy publishing to claude.ai, `list`/`read` of shared artifacts, comment and watch
notifications, an artifact-side database, an asset store, preview and verify — 25 `action`
values, none of which exists on a page served from alanchen.cc, where `site/share.sh` does the
publish step. The one remaining use is reading or updating an artifact someone else published.

## How much it was used

Every `~/.claude/projects/**/*.jsonl` here (3,776 files), `tool_use` blocks only — a bare grep
also matches the `skill_listing` attachment every session carries:

| | calls | sessions | window |
| --- | --- | --- | --- |
| `Artifact` (61 `publish`, 30 read/list/delete/status) | 91 | 18 | 2026-08-25 → 2026-09-30; 15 of September's 694 sessions |
| `Skill` → `artifact-design` | 17 | 16 | 14 of them also published to claude.ai |
| `Skill` → `artifact-diagramming` / `artifact-capabilities` | 4 / 1 | 3 / 1 | |
| `Bash` running `site/share.sh` | 16 | 2 | 2026-09-30 only |

User prompts containing `html`, main-session files only: 2, 3, 5, 6 per month from May to
August, then 107 in September across 53 sessions, 89 in its second half — a two-week-old habit
that lives in `/workspace`, whose `CLAUDE.md` names `artifact-design` for every page.

## It cannot be deferred

The deferral predicate defers a tool only if it is MCP or carries `shouldDefer === true`
(`if (e.alwaysLoad === !0) return !1;`, `src/chunk-4zcseazt.js:1052-1055`); the one first-party
list is server-supplied and exempts *from* deferral (`tengu_non_deferrable_builtins`,
`src/chunk-970xe2g2.js:110`). `Artifact` is `shouldDefer: !1` (`src/chunk-q5zwjg9j.js:13099`).
No settings key, env var or flag reaches that literal; the docs agree ("Only MCP server tools
are affected by tool search", code.claude.com/docs/en/mcp).

## The split

`CLAUDE_CODE_ARTIFACT_TOOLSET` sets a session-long latch (`c_()`, `src/chunk-fqa6n2gt.js:3761`;
otherwise GrowthBook `tengu_cobalt_plinth_damson`) that registers three add-ons —
`ArtifactComments`, `ArtifactData`, `ArtifactCheck` (`src/chunk-af3h90mb.js:414-435`), each
`shouldDefer: !0` (`:330`) — and hands the main tool a shorter description and schema:

```
docs/system-prompt-snapshot/capture.py --capture-model claude-opus-5 \
  --capture-output-style default --capture-no-oauth-token \
  --capture-child-env CLAUDE_CODE_ARTIFACT_TOOLSET=1
```

| | unified | split |
| --- | --- | --- |
| all tool tokens | 34,177 | 22,415 |
| `Artifact` tokens | 20,496 | 8,734 |
| `Artifact` `action` enum | 25 values | `publish`, `list`, `read`, `delete`, `open`, `pin`, `unpin` |
| add-ons | — | three names in the deferred-tools reminder, loaded through `ToolSearch` |

`list` keeps `scope` (`mine`/`shared`/`all`) and `read` keeps shared artifacts, so the split
tool still covers the remaining use. Any value enables the knob, `0` included (the latch takes
the raw string); it is undocumented and experiment-gated, so a later build may ship it by
default, change the partition, or drop it. Nothing here sets it.

## The gate, and why the settings key rather than the env var

One object decides everything: `{enableKey: "enableArtifact", legacyDisableKey:
"disableArtifact", envDisableVar: "CLAUDE_CODE_DISABLE_ARTIFACT", defaultOn: !0}`
(`src/chunk-fqa6n2gt.js:9896`), resolved by `gl()` (`:9838`) — any off-source wins, so no
settings file or launcher turns the tool back on while any off stands (the docs agree:
code.claude.com/docs/en/artifacts). `TI()` (`:9984`) is that resolution unlatched, and it is
both the roster filter that keeps the tool (`.filter(m => m !== lr || TI())`,
`src/chunk-4zcseazt.js:1354`) and the `isEnabled` of the built-in `artifact-design` and
`artifact-diagramming` skills (`src/chunk-s7akwrx2.js:464`, `:483`): whatever removes the tool
removes the skills.

The env var is read raw from the process environment — `Rp()` tests `a[e]`, so
`CLAUDE_CODE_DISABLE_ARTIFACT=0` disables too — and from a settings file's `env` block
(`:9884-9887`); either lands in the `env` layer, sets `lockedAboveUser`, and hides the `/config`
Artifacts row (`src/chunk-ve1cwn02.js:753-776`), shown only while `Kze().userControllable`
(`Grt()`, `src/chunk-fqa6n2gt.js:10113`). The key in user settings keeps the row.

That the row takes effect in-session is three source readings, not a live flip: the write
invalidates the settings store (`Fo`, `src/chunk-2x9ed96k.js:3030`, ending in `Pa()` =
`Sa().invalidateAll`, `src/chunk-3vd4nzwp.js:43`); the roster is rebuilt every request
(`MDr()`, `src/chunk-4zcseazt.js:1351-1354`, from `zkt()`, `src/chunk-dbb93264.js:159883`);
and the prompt snapshot does not pin the roster (`dwt()`, `src/chunk-dbb93264.js:150990`,
writes a new record whenever a request carries a tool the last one lacks). Because user
settings resolve to the `install.sh` symlink, a flip dirties this repo's tracked
`settings.json` until flipped back; and `agent-tools claude` copies the file into
`CLAUDE_CONFIG_DIR`, so prompt-test runs have no `Artifact` either.

## What this record cannot show

- The captures never see the key (`capture.py:471` passes `--setting-sources project,local`);
  the capture that lacks the tool got there by the env var.
- Whether `ze(addon)`, the fourth term of the add-ons' `isEnabled` (`src/chunk-gc6rxa2e.js:164`),
  is a server-side roster check; another account may not get them.
- What ends it: a release that lets a first-party tool defer, moves the off-wins rule, removes
  the `/config` row, or ships the split by default.

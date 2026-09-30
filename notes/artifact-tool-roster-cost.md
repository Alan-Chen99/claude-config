# The Artifact tool is 60% of the tool roster and cannot be deferred

Measured 2026-09-30 on Claude Code **2.1.269**, with `claude-opus-5` captures taken by
`docs/system-prompt-snapshot/capture.py` under the credentials-file login every session
here uses. The `Artifact` tool's description and input schema are 20,496 of the 34,177 tool
tokens a logged-in session sends with every request; the tool is hard-wired out of
ToolSearch deferral; the one knob that shrinks it is an unreleased experiment. `settings.json`
carries `enableArtifact: false` because of these numbers, in the settings key rather than the
env var because only the key leaves the `/config` Artifacts row toggleable inside a session.

> **Dated record.** Citations are pinned to 2.1.269 and the numbers to that build, one
> account, one day. Do not re-pin; re-measure — the committed pair is `logged-in` /
> `logged-in-no-artifact` in `docs/system-prompt-snapshot/regenerate.py`, and the split
> capture is the one command under "The split".

## The cost

Same credential, same model, same day (`docs/system-prompt-snapshot/opus-5/logged-in` vs
`logged-in-no-artifact`, the second taken with `CLAUDE_CODE_DISABLE_ARTIFACT=1`):

| | with Artifact | without |
| --- | --- | --- |
| upfront tools | 14 | 13 |
| tool tokens (`regenerate.py`'s figure) | 33,465 | 13,255 |
| deferred names | 57 | 57 |
| built-in `artifact-design`, `artifact-diagramming`, `artifact-capabilities` | listed | absent |
| system prompt tokens | 4,759 | 4,758 |

Counted a second way — one `capture.count_tokens` call over the request's whole `tools`
array, `defer_loading` stripped — the same `logged-in` request is 34,177 tokens, of which
`Artifact` alone is 20,496 (description 30,113 characters, schema 29,521) and the other
seventeen tools 13,681. The two totals are different computations: `regenerate.py` counts
the `tools` array's marginal cost on top of the captured system prompt (`r_with_tools -
r_no_tools`), this one counts it on top of a one-word message, and the 712-token gap between
the two baselines was not decomposed further. Every comparison below uses the second, so
the differences are like for like.

What the tokens buy: publishing to claude.ai with a `<head>` skeleton wrap and a CSP,
`list`/`read` of the user's and shared artifacts, watch and comment notifications, an
artifact-side database, an asset store, and preview/verify — 25 `action` values. On a page
served from alanchen.cc none of the runtime exists (`window.claude.*` is the claude.ai host's
object), `share.sh` adds the skeleton itself, and it refuses a page that links to a claude.ai
artifact; the tool's one remaining use there is reading or updating an artifact someone else
published.

## How much it was used

Every `~/.claude/projects/**/*.jsonl` on this machine (3,776 files), counting `tool_use`
blocks only — a bare grep also matches the `skill_listing` attachment every session carries:

| | calls | sessions | window |
| --- | --- | --- | --- |
| `Artifact` (61 `publish`, 30 read/list/list_files/read_file/delete/status) | 91 | 18 | 2026-08-25 → 2026-09-30; 3 sessions in August, 15 of September's 694 |
| `Skill` → `artifact-design` | 17 | 16 | 14 of them also published to claude.ai |
| `Skill` → `artifact-diagramming` | 4 | 3 | |
| `Skill` → `artifact-capabilities` | 1 | 1 | |
| `Bash` running `site/share.sh` | 16 | 2 | 2026-09-30 only |

User prompts containing the word `html`, main-session files only (a subagent's transcript
records its parent's prompt as `user`): 2, 3, 5, 6 per month from May to August, then 107 in
September across 53 sessions — 89 of them in its second half. The tool was a ~2%-of-sessions
feature for five weeks; the habit of asking for pages is two weeks old and lives in
`/workspace`, whose `CLAUDE.md` names `artifact-design` as governing every page and whose
`site/share.sh` replaced the publish step on 2026-09-30.

## It cannot be deferred

The deferral predicate defers a tool only if it is MCP or carries `shouldDefer === true`
(`if (e.alwaysLoad === !0) return !1;`, `src/chunk-4zcseazt.js:1052-1055`); the one
first-party exemption list is server-supplied (`tengu_non_deferrable_builtins`,
`src/chunk-970xe2g2.js:110`) and it exempts *from* deferral. `Artifact` is `shouldDefer: !1`
(`src/chunk-q5zwjg9j.js:13099`). No settings key, env var or flag reaches that literal, and
the docs say the same from the other side: "Only MCP server tools are affected by tool
search" (code.claude.com/docs/en/mcp).

## The split

`CLAUDE_CODE_ARTIFACT_TOOLSET` sets a session-long latch (`c_()`,
`src/chunk-fqa6n2gt.js:3761`; otherwise GrowthBook `tengu_cobalt_plinth_damson`) that
registers three add-on tools — `ArtifactComments`, `ArtifactData`, `ArtifactCheck`
(`src/chunk-af3h90mb.js:414-435`) — each `shouldDefer: !0` (`:330`), and hands the main tool
a shorter description and schema. Captured the same way as the pair above:

```
docs/system-prompt-snapshot/capture.py --capture-model claude-opus-5 \
  --capture-output-style default --capture-no-oauth-token \
  --capture-child-env CLAUDE_CODE_ARTIFACT_TOOLSET=1
```

| | unified | split |
| --- | --- | --- |
| all tool tokens | 34,177 | 22,415 |
| `Artifact` tokens | 20,496 | 8,734 |
| the other seventeen tools | 13,681 | 13,681 |
| `Artifact` `action` enum | 25 values | `publish`, `list`, `read`, `delete`, `open`, `pin`, `unpin` |
| add-ons | — | the three names in the deferred-tools reminder, loaded through `ToolSearch` |
| the three `artifact-*` skills | listed | listed |

`list` keeps `scope` (`mine`/`shared`/`all`) and `read` keeps shared artifacts, so the split
main tool still covers "update an artifact someone else published". Two things about the knob:
any value enables it, `0` included — the latch takes the raw string
(`a.CLAUDE_CODE_ARTIFACT_TOOLSET ?? …`); and it is undocumented and gated on an experiment
flag, so a later build may ship it by default, change the partition, or drop it. Nothing here
sets it; the runbook lists it under unset knobs.

## The gate, and why the settings key rather than the env var

One object decides everything: `{enableKey: "enableArtifact", legacyDisableKey:
"disableArtifact", envDisableVar: "CLAUDE_CODE_DISABLE_ARTIFACT", defaultOn: !0}`
(`src/chunk-fqa6n2gt.js:9896`), resolved by `gl()` (`:9838`). Any off-source wins —
`enabled` requires zero of them — so no settings file and no launcher turns the tool back on
while any off stands; the docs say so too ("no settings file turns them back on",
code.claude.com/docs/en/artifacts). `TI()` (`:9984`) is that resolution, unlatched, and it is
the roster filter that keeps the tool (`.filter(m => m !== lr || TI())`,
`src/chunk-4zcseazt.js:1354`) and the `isEnabled` of the built-in
`artifact-design` and `artifact-diagramming` skills (`src/chunk-s7akwrx2.js:464`, `:483`):
whatever removes the tool removes the skills.

The env var is read from the process environment raw — `Rp()` tests `a[e]`, so
`CLAUDE_CODE_DISABLE_ARTIFACT=0` disables too — and, parsed, from a settings file's `env`
block (`:9884-9887`). Either way it lands in the `env` layer, which sets `lockedAboveUser`,
and the `/config` Artifacts row (`src/chunk-ve1cwn02.js:753-776`) is shown only while
`Kze().userControllable` holds (`Grt()`, `src/chunk-fqa6n2gt.js:10113`). The settings key in
user settings keeps the row.

The row's write goes to user settings (`Kt`, `src/chunk-2x9ed96k.js:2997`, through `Fo`,
`:3030`), and `Fo` ends by invalidating the settings store (`Pa()` at `:3112` is
`Sa().invalidateAll`, `src/chunk-3vd4nzwp.js:43`); the roster is rebuilt on every request
(`MDr()`, `src/chunk-4zcseazt.js:1351-1354`, called from `zkt()`,
`src/chunk-dbb93264.js:159883`); and the prompt snapshot does not pin the roster — `dwt()`
(`src/chunk-dbb93264.js:150990`) writes a new `prompt_snapshot` record whenever the request
carries a tool the last record lacks. So a session that starts with the key off and flips the
row on should carry the tool, and the three skills, from its next request. That is three
source readings; the flip was not driven live (no tty here). Two consequences of the key
being in this repo's `settings.json`: user settings resolve to the `install.sh` symlink, so a
flip writes into the tracked file and `git diff settings.json` stays dirty until it is flipped
back; and `agent-tools claude` copies the file into `CLAUDE_CONFIG_DIR`, so prompt-test runs
have no `Artifact` tool either.

## What this record cannot show

- The captures never see the key: `capture.py:471` passes `--setting-sources project,local`,
  which drops user settings, so `opus-5/logged-in/tools/Artifact.md` is present whether the
  key holds or not. The capture that lacks the tool got there by the env var.
- Whether `ze(addon)` — the fourth term of the add-ons' `isEnabled`,
  `src/chunk-gc6rxa2e.js:164` — is a server-side roster check. The three add-ons appeared
  for this account; another account may not get them.
- What ends it: a release that lets a first-party tool defer, moves the off-wins rule in
  `gl()`, removes the `/config` row, or ships the split by default. The `logged-in` /
  `logged-in-no-artifact` diff is the check for the first; the split command above for the
  last.

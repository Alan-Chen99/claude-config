# Claude Code System Prompt Snapshots

Captured: 2026-09-11 (all directories below, all models)
Version: claude-cli/2.1.269
Mode: interactive (real pty via `capture.py`, `--setting-sources project,local`)
Default captures include a project CLAUDE.md.

Previous snapshot was 2.1.235 (captured 2026-09-08 / 2026-08-22); `git show b318e59:docs/system-prompt-snapshot/...`
gives the exact 2.1.235 artifact for any path here. Every number below was re-derived from
the artifacts on disk; a 2.1.235 figure given for comparison is labelled as such.

Directories are named for the model id the request carried, minus its `claude-` prefix.
Aliases are repointed as models ship — `opus` meant `claude-opus-4-6` in the 2.1.143 capture
and means `claude-opus-5` here — so an alias-named directory changes meaning between captures
while its path stays put. 2.1.269 also ships `claude-fable-5`, `claude-fable-5-1`,
`claude-mythos-5`, `claude-mythos-5-1` and `claude-opus-4-8` as selectable ids; `fable-5/` and
`opus-4-8/` are captured (`default` only), the other three are not — see "Fable and Mythos".

## Files

| File | What |
|---|---|
| `<model-id>/<variant>/request.json` | Full API request body — the artifact of record. Metadata redacted. |
| `<model-id>/<variant>/prompt.md` | Everything in that request except the tool definitions: parameters, the tool roster in request order, every system block, every message |
| `<model-id>/<variant>/tools/<Name>.md` | One tool definition each — attributes, description, input schema |
| `<model-id>/<variant>/summary.json` | Block count, token counts, tool inventory |
| `builtin-skills/<name>.md` | What invoking that built-in skill injects into the context. Shared across models, not per-model: bodies measured byte-identical on opus-5 and sonnet-5 |
| `builtin-skills/manifest.json` | Per skill: delivery shape, which route reached it, size, sha256 |
| `capture.py` | Captures one variant via pty + MITM proxy |
| `capture_skills.py` | Captures every built-in skill's body into `builtin-skills/` |
| `regenerate.py` | Drives `capture.py` across every variant, writes `summary.json` |
| `render_capture.py` | Renders `prompt.md` and `tools/` from a `request.json`; `--tree <root>` does every capture beneath a directory |
| `scripts/intercept/` — repo root, not under this directory | MITM proxy for API call logging (see `scripts/intercept/README.md`) |

### Reading a capture as a diff

`request.json` is the artifact of record and is unreadable as a diff: one line per string with
every newline escaped, so a reworded paragraph inside `Artifact`'s 25,099-character description
arrives in `git diff` as a single changed line 25,099 characters wide. `prompt.md` and
`tools/<Name>.md` carry the same content as text, for the person reading that diff across a
release. They are derived — never hand-edit them: `./render_capture.py --tree .` rebuilds them
and `tests/test_snapshot_rendering.py` fails when they drift from the `request.json` beside them.

The split is per tool because that makes the diff legible — a changed tool is one file with
line-level hunks, an unchanged one is absent, an added or removed tool is an added or removed
file — and everything that is not a tool stays in one file because it is read as a whole: a
section moving between the system prompt and the messages, which 2.1.269 did to the environment
block, is only visible if both sit in the same diff.

From 2.1.269 on the review at an upgrade is `git diff` after re-capturing. An older release's
captures predate the layout, so render them into it first:

```bash
mkdir -p /tmp/old/opus-5/default
git show b318e59:docs/system-prompt-snapshot/opus-5/default/request.json \
  > /tmp/old/opus-5/default/request.json
./render_capture.py --tree /tmp/old
diff -ru -x request.json -x summary.json /tmp/old/opus-5/default opus-5/default
```

### What a default capture leaves out, and where it now lives

A `default` capture records two things by name only; both are text the model receives and
change between releases:

| Withheld from `default` | Now captured in |
|---|---|
| The 18 deferred tools' descriptions and schemas — the reminder lists their names, and `tools/` holds one `DeferredToolPlaceholder` stub | `<model-id>/tool-search-loaded/tools/` |
| The 17 built-in skills' bodies — the reminder carries each name and description, never the text an invocation injects | `builtin-skills/` |

Both are captured in the default configuration. The deferred half works because `ToolSearch`
does not do what its own description says: it advertises a `<functions>` block, and no such
block exists anywhere in the binary except that sentence. It returns a `tool_result` of
`{"type": "tool_reference", "tool_name": ...}` entries plus the text `Tool loaded.`, and the
**server** expands those into the next request's `tools` array — measured, 15 tools before the
call and 33 after — so the schemas arrive in a request, which this directory already renders.

`tool-search-loaded` is captured for opus-5 and sonnet-5, enough to separate per-model from
shared: of the 18 deferred tools only `WebFetch` (676 characters on opus-5, 1,909 on sonnet-5)
and `WebSearch` (312 against 1,322) take the lean/full split; the other 16 are byte-identical.

Variants: `default`, `custom-output-style`, `system-prompt`, `system-prompt-file`, `append`,
`tool-search-loaded`, `logged-in`, `logged-in-no-artifact`, `subagent`. Captured: the original
six plus `tool-search-loaded` for sonnet-5; `default` for opus-4-7; `default`,
`system-prompt-file`, `tool-search-loaded`, `logged-in` and `logged-in-no-artifact` for opus-5;
`default` only for fable-5 and opus-4-8 — both added after an account entitlement upgrade
partway through the capture session, opus-4-8 specifically to test whether fable's prompt was
a Fable-family oddity or per-model (per-model; see "The prompt split is per model id").

None of them is the configuration this repo itself runs: `scripts/claude.sh` launches
`--dangerously-skip-permissions` with `--system-prompt-file`, and a capture takes the default
permission mode, which is why the bypass-permissions reminder a `claude.sh` session
demonstrably carries appears in no file here (see "Removed: the `## Auto Mode Active`
reminder"). `regenerate.py` defines a `bypass-permissions` variant for it, not yet captured, so
that directory is absent rather than empty.

### The two `logged-in` variants

Every other variant exports `CLAUDE_CODE_OAUTH_TOKEN` and is MCP-free. These two drop it
(`capture.py --capture-no-oauth-token`) so the child authenticates from
`~/.claude/.credentials.json`, the condition under which it reaches the Chrome extension and the
claude.ai connectors — 57 deferred names against 18. `logged-in-no-artifact` adds
`CLAUDE_CODE_DISABLE_ARTIFACT=1` through `--capture-child-env`, which is how a variant names a
`CLAUDE_CODE_*` knob it wants after the wholesale strip. The pair measures the `Artifact` tool
with the credential held fixed: 33,465 tool tokens against 13,255, 14 upfront tools against 13,
the three `artifact-*` skills listed against absent, the 57 deferred names unchanged —
`notes/artifact-tool-roster-cost.md`.

### Built-in skill captures

`builtin-skills/` holds what invoking each of the 17 built-in skills injects — 512,397
characters in total, none of it in a `default` capture; the per-skill table and the capture
conditions are in `builtin-skills/README.md`. Three conditions change the result: interactive
rather than `-p`, or the skills gated on the `Artifact` tool are unreachable and `design`
degrades from 55,398 characters to a 169-character stub; `--setting-sources project,local`, or
`design` and `code-review` degrade too; a repo with a resolvable `origin/HEAD`, or
`/security-review` — whose prompt interpolates `` !`git diff origin/HEAD...` `` — injects nothing
at all. Each failure produces a plausible short body rather than an error, which is why
`capture_skills.py` refuses to write a body that opens with harness text and
`tests/test_builtin_skills.py` checks the committed files for the same thing: the first run
wrote Claude Code's type-ahead suggester prompt into two files and a bare system reminder into
a third.

### Subagent captures

`capture.py --subagent` adds a `subagents/` directory:

| File | What |
|---|---|
| `subagents/NNN/request.json` | Full API request for subagent N |
| `subagents/NNN/prompt.md` | Everything in it except the tool definitions |
| `subagents/NNN/tools/<Name>.md` | One tool definition each — the rosters are smaller than the parent's (5 for Explore, 9 for general-purpose, against 15) |
| `subagents/NNN/summary.json` | Block structure and tools for subagent N |

Subagent requests are identified by `cc_is_subagent=true` in the billing header, not by size or
tool count — the security-monitor call (below) also carries tools and a large system prompt.
Still true in 2.1.269: `sonnet-5/subagent`'s two children carry it and their own `cc_prompt_id`.

## Credentials

The spawned child needs its own credentials: `CLAUDE_CODE_OAUTH_TOKEN` in the environment, or
an access token in `~/.claude/.credentials.json`. Claude Code strips the variable from tool
subprocess environments, so a capture launched from inside a session inherits none and falls
back to the file — empty when the session itself authenticates by env var, populated after an
interactive login.

**Export the token even when the credentials file would do.** The two sources produce different
captures: the credentials-file login reaches MCP and the exported token does not. Two
`claude-opus-5` `default` captures taken minutes apart on 2.1.269, identical in every flag:
with the exported token, 15 `tools` entries, 18 deferred names, 3,338 system tokens; with the
credentials-file login, 18 entries, 57 deferred names (22 Chrome, 36 MCP in all), the
`Claude in Chrome browser automation` and `MCP Server Instructions` prompt sections,
`ListMcpResourcesTool` and the two `ReadMcpResource*`, 4,756 system tokens. The 14 upfront
names are the same in both. The exported token reproduces the committed rosters exactly —
every capture here is an MCP-free capture, and a re-capture without the export is not
comparable to one. That is a property of the credential, not of this machine: the Chrome
extension was already paired when the 2026-09-11 snapshot was taken (its tool names appear in
intercepted sessions from 2026-08-22 on), and the snapshot records none of them. Whether the
connector list is tied to the claude.ai account session rather than to an API credential is not
established; only the effect is measured.

```bash
set -a && . /workspace/.env && set +a   # or wherever the token lives
```

That file carries a second `CLAUDE_CODE_OAUTH_TOKEN`, commented out, for when the active one is
out of credit — the failure reads as a quota error on the first request, not as an auth error.
Swap which line is commented rather than exporting both.

`capture.py` refuses to spawn when neither source has credentials. Without the guard the child
renders "Not logged in", issues zero API calls, and the failure surfaces only as an empty
capture.

## System prompt structure (v2.1.269, interactive mode)

The `system` array still carries 4 text blocks, same cache placement as 2.1.235: blocks 2 and 3
carry `cache_control`; only block 2 sets `scope: global` (block 3 omits `scope`, so it falls
back to org scope).

Sizes below are **characters**, measured directly from `request.json`; for the byte-identity
questions this doc cares about they are the stronger evidence — the 2.1.235 doc's per-tool
token table showed `Skill` at 977 sonnet-tokens vs 909 opus-tokens on identical text, a
tokenizer artifact. Whole-request **token** totals (`system_tokens` / `tools_total_tokens`)
are exact, measured by `count_tokens` at capture time into each variant's `summary.json`.

| Block | Content | Cache | Opus 4.7 | Sonnet 5 | Opus 5 | Fable 5 | Opus 4.8 |
|---|---|---|---|---|---|---|---|
| 0 | Billing header (`cc_version=2.1.269...`) | none | 132 | 132 | 132 | 132 | 132 |
| 1 | Identity (`"You are Claude Code, Anthropic's official CLI for Claude."`) | none | 57 | 57 | 57 | 57 | 57 |
| 2 | Static behavioral rules | 1h, global scope | 10,676 | 10,574 | 1,210 | 1,210 | 1,152 |
| 3 | Session guidance, memory, environment (ecosystem facts only — see below), context mgmt | 1h, org scope | 16,895 | 17,128 | 8,546 | 9,571 | 5,278 |

Every figure above is the `default` variant, and block 2 is not a pure function of the model:
its opening sentence tracks the active output style. With one selected, `helps users with
software engineering tasks` becomes `helps users according to your "Output Style", which
describes how you should respond to user queries`, and sonnet-5's block 2 measures 10,631 chars
rather than 10,574 (`sonnet-5/custom-output-style/request.json` against
`sonnet-5/default/request.json`; `append` and `subagent` both stay at 10,574). Calling the block
static is true of a release, not of a session.

Block 1 is unchanged byte-for-byte from 2.1.235 for every model that existed to compare. Block
0 is the billing header: `cc_version` (`2.1.235.cf9` -> `2.1.269.d5c`), a per-run `cch` hash and
`cc_prompt_id` change on every capture, its 132-char layout does not. Opus 4.7, Sonnet 5 and
Opus 5's block 2 is each unchanged byte-for-byte from 2.1.235 (10,676/10,574/1,210), so all of
their version-over-version change is in block 3 — "What moved out of block 3". Block 2 is not
one shared text per branch either — "The prompt split is per model id" is why 1,210/1,210/1,152
is not a typo.

Total `system_tokens` per variant (from `summary.json`, exact):

| Variant | Opus 4.7 | Sonnet 5 | Opus 5 | Fable 5 | Opus 4.8 |
|---|---|---|---|---|---|
| `default` | 8,702 | 8,745 | 3,252 | 3,556 | 2,266 |
| `custom-output-style` | — | 8,761 | — | — | — |
| `append` | — | 8,754 | — | — | — |
| `subagent` | — | 8,743 | — | — | — |
| `system-prompt` / `system-prompt-file` | — | 116 / 114 | — / 117 | — | — |

2.1.235 comparison (opus-4-7/sonnet-5/opus-5): 9,329 / 9,368 / 3,860 — every total dropped,
entirely out of block 3 (tools are priced in `tools_total_tokens`). Opus 4.8's 2,266 is a
quarter of Sonnet 5's 8,745, so "the 2.1.269 system prompt" was never one size either.
`sonnet-5/default`'s 8,745 is a corrected figure: the first capture read 8,664 with
`SendFeedback` and `EndConversation` missing — see "The upfront tool roster is not a pure
function of version and model id".

### The prompt split is per model id, not per model family

Sonnet-5 and opus-4-7 get the long multi-section prompt; opus-5, fable-5 and opus-4-8 get the
compressed `# Harness` one — and "getting the same branch" does not mean sharing one prompt:
**two families, per-model contents**.

The 2.1.235 doc traced the branch choice to `sV`/`aT`/`EAb`; the decompile has since been
re-extracted from the 2.1.269 binary (commit `8606fb66`) into 1,677 ESM files
(`src/chunk-<hash>.js`), so those names and every `src/globals/NN.js` citation no longer
resolve. Re-derived by grepping string literals: the choice is made once, in the function that
assembles block 3, at `src/chunk-dbb93264.js:69226` — `d ? [ORo(P, n)] : [vRo(P), xRo(n),
...]`, `ORo` building the compressed body. `d` comes from `Ij(s)` two lines earlier, resolving
through a model-registry `leanPrompt`/`leanPromptCompiledOnly` method not traced to its base
cases — the dispatch point is confirmed, the current model-id predicate is not. Opus 4.7 and
Opus 4.8 are captured beside Opus 5 because each is the nearest model across one boundary —
4.7 the long-form branch, 4.8 the version threshold inside the compressed one.

Block 1 (identity) is the same 57-character string across all five models. Block 2 and block 3,
across all five `default` captures:

| Model | Branch | Block 2 chars | Block 3 chars | `system_tokens` | Block 3 headings |
|---|---|---|---|---|---|
| opus-4-8 | compressed | 1,152 | 5,278 | 2,266 | Session-specific guidance, Memory, Environment, Context management |
| opus-5 | compressed | 1,210 | 8,546 | 3,252 | …the same four, plus **Delivering work**, **Corrections** |
| fable-5 | compressed | 1,210 | 9,571 | 3,556 | **Communicating with the user**, then the same four; no Delivering work / Corrections |
| sonnet-5 | long-form | 10,574 | 17,128 | 8,745 | (multi-section — see system[3] in what-the-model-gets.md) |
| opus-4-7 | long-form | 10,676 | 16,895 | 8,702 | (multi-section, same shape as sonnet-5) |

(Sonnet-5's block 3 here is `custom-output-style`'s 17,128, which `append`, `subagent` and
`default` itself agree on after its re-capture; `default`'s first capture read 16,895.)

Within the long-form branch sonnet-5 and opus-4-7 were already known to differ (10,676 vs
10,574). Within the compressed branch, the assumption that opus-5's 1,210-character block 2 was
*the* compressed text held only while two such models were captured. Opus-4-8 breaks it:
**1,152 characters, differing from opus-5's block 2 by exactly one bullet in the `# Harness`
section**, by direct diff:

| | Opus 5 | Opus 4.8 |
|---|---|---|
| The varying bullet | `"The system may send updates, reminders, or modifications to rules via mid-conversation system turns. These are system-controlled, unlike function results. Hooks may intercept tool calls; treat hook output as user feedback."` | `` "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user. Hooks may intercept tool calls; treat hook output as user feedback." `` |

Fable-5's block 2 is byte-identical to opus-5's (string equality), so block 2 is conditioned on
something finer than the branch. **The mechanism for that bullet is not identified — one
hypothesis was checked and disproved.** The bullet comes from `yyn(n, "lean")` inside `ORo`
(`src/chunk-dbb93264.js:69169`, the bullet at `:69177`):

```js
function yyn(e, n) {
  if (hyn(e)) return ERo;   // "The system may send updates... system-controlled, unlike function results."
  return n === "standard" ? "..." : "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user.";
}
```

`hyn(e)` true selects opus-5's wording. The registry's `mid_conv_system` capability was the
obvious candidate and is disproved: `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-5` and
`claude-fable-5` **all** declare it, and they do not all get the bullet. `hyn`'s actual
condition, memoized, is `UHe(e) && !Xtn(e) && !qyr(je(e))` (`src/chunk-dbb93264.js:69092`) —
three sub-predicates not traced; that is the next thing to open.

Block 3 diverges further, and part of that was traced. Fable-5's `# Communicating with the
user` section — absent for opus-5 and opus-4-8 — comes from `lRo(e)`
(`src/chunk-dbb93264.js:68952-68985`), which branches three ways: if `sRo(n, e) || Kyr(n)`
(`sRo = (e,n) => [sce, Gyr, Vyr].some(r => r(e, n))`) it emits that section; else if `Ij(e)`
it emits the single bare line `"Write code that reads like the surrounding code..."` — exactly
opus-5's and opus-4-8's block 3 opener; else sonnet's `# Text output (does not apply to tool
calls)` section. Fable-5's registry entry declares a `fable_5_mitigations` capability that
`sce(e, o)` reads directly (`src/chunk-eejnrs8c.js:40-44`) — a plausible candidate for why
fable-5 takes the first branch. **Not established**: which of `sce`, `Gyr`, `Vyr`, `Kyr` is the
one true for `claude-fable-5`. A sibling capability, `fable_5_1_prompt_bundle`, is read by
`ice(e)` (`src/chunk-eejnrs8c.js:46-48`) — a separate lead. The literal heading is stored
whole: `grep -rn "# Communicating with the user" src/` finds `lRo` at
`src/chunk-dbb93264.js:68961`.

Upshot: there is no single object to call "the compressed prompt" or "the opus-5 prompt".
Block 2 sorts into at least two texts within the one branch; block 3 into at least three
(opus-5's six sections, fable-5's five plus a different opener, opus-4-8's four). Per-model
conditioning inside a branch reaches a model with no Fable-family relationship at all.

### What moved out of block 3

The substantive change this round, identical in shape across all three models (diffed
directly): four things left the cached, 1h-TTL block, and no tool or behavioral section moved
with them.

**Absent from the request, but not a code removal** — the full JSON holds no replacement: the
act-when-you-have-enough-information paragraph (`"When you have enough information to act,
act. Do not re-derive facts already established..."`), introduced in 2.1.235, appears in no
2.1.269 capture. It is **still in the 2.1.269 source**: `src/chunk-dbb93264.js:69214` builds
block 3 as labelled fragments including `Jb("act_dont_rederive", () => DRo() ? NRo : null)`,
`NRo` this exact string and `DRo` (`:69182`) resolving `I("tengu_cedar_lantern", !0)` — a
GrowthBook flag defaulting to *on*. 2.1.235 has the identical gate under the same flag
(`zB('act_dont_rederive', () => (fdE() ? mdE : null))`, `src/globals/21.js:13381`). The
paragraph vanishing from every capture reads as the live flag value for this account, the same
category as the `SendFeedback`/`Artifact` observations here, not a code change.

**Relocated to a new per-message system-reminder** (in `messages[]` — see "messages
structure"): the entire `# Environment` per-session block (`"You have been invoked in the
following environment:"`, working directory, is-git-repo, platform, shell, OS version, the
`"You are powered by the model named ..."` / `"Assistant knowledge cutoff is ..."` lines), and
`gitStatus` — no longer appended to any system block in **any** variant, the custom
`--system-prompt` one included.

**Genuinely removed from the assembly code**: the `# Scratchpad Directory` section (5 bullets,
session-specific path), introduced in 2.1.235. Its content lives inside the relocated
`# Environment` reminder, but the section-builder call is gone from the list: 2.1.235 had
`zB('scratchpad', () => cvi())` (`src/globals/21.js`); nothing producing this content appears
in 2.1.269's list at `src/chunk-dbb93264.js:69205-69224`.

What's left under `# Environment` in the cached block is static ecosystem trivia — model-id
roster, available surfaces, fast mode — so the block no longer holds anything that busts its
cache across sessions with different directories, branches or dates.

Opus's block 3 also picked up one real wording change: `"Do not call the AgentTool unless the
user requested it"` / `"Do not use workflows or deep-research unless the user requested it"`
became `"Do not use the Agent tool, workflows, or deep-research unless the user, a CLAUDE.md
file, or a skill asks for it"` — the set of things that count as authorization widened.
Sonnet's block 3 has no equivalent sentence in either version.

### The upfront tool roster is not a pure function of version and model id

Timeline, from this batch's own file timestamps (`cc_version=2.1.269.d5c` on every capture):

| Time | Capture(s) | Upfront / deferred |
|---|---|---|
| 19:10 | `opus-5/default` | 14 / 18 |
| 19:29 | `opus-4-7/default` | 14 / 21 |
| 19:31 | `sonnet-5/default`, first capture | **13 / 17** |
| 19:32-19:39 | the other 5 sonnet-5 variants, and `opus-5/system-prompt-file` | 14 / 18 |
| 21:16 | `sonnet-5/default`, re-capture | 14 / 18 |
| 21:44 | `fable-5/default`, first capture | **13 / 17** |
| 22:04 | `fable-5/default`, re-capture (the one on disk) | 14 / 18 |

Two anomalous runs across two models, both missing exactly `SendFeedback` and
`EndConversation`, both non-reproducible on a same-variant re-capture. **The mechanism is
identified** from the 2.1.269 decompile:

- **`SendFeedback`** is gated on the GrowthBook flag `tengu_juniper_relay`: its `isEnabled()`
  (`src/chunk-dbb93264.js:181066`) calls `iL()`, which requires the `feedbackDrafts` setting
  not be `"off"` and `rCn()` to hold — an entrypoint/provider chain ending in
  `I("tengu_juniper_relay", !1)` on every path, `CLAUDE_CODE_SEND_FEEDBACK=true` included
  (`src/chunk-dbb93264.js:180877-180888`). Hardcoded fallback **false**.
- **`EndConversation`** is gated on `tengu_umber_kestrel`, same shape and fallback — `zGt`
  (`src/chunk-t7d8rn9f.js:92-100`), consumed at `src/chunk-1qj1h00h.js:276-279`.
- **Why both vanish together**: both resolve through one per-process GrowthBook client, `Tt()`
  (`src/chunk-5cs6j3p3.js:24712-24732`), and one method, `getFeatureValueWithSource`
  (`src/chunk-5cs6j3p3.js:9166-9197`), whose order is the load-bearing part: it checks this
  process's own fetch result `this.remoteEvalFeatureValues.get(key)` first, and if the key is
  absent **but the map has any keys** (`.size > 0`) it returns the hardcoded default — the
  on-disk cache (`cachedGrowthBookFeatures`) is consulted only when the map is empty. One fetch
  that succeeds but lacks a key turns that flag off for the process's life whatever the disk
  cache says; a payload missing both keys turns both tools off together.
- **This also explains `opus-4-7` never showing `EndConversation`**: `zGt` first requires the
  model to clear a per-family threshold, `[["opus",[4,8]],["sonnet",[5]],["fable",[5]],
  ["mythos",[5]]]` (`src/chunk-t7d8rn9f.js:62`), compared by `MZt`
  (`src/chunk-970xe2g2.js:20-32`). `claude-opus-4-7` parses to `[4,7]` and fails `>= [4,8]`;
  `claude-sonnet-5` and `claude-fable-5` clear `[5]` trivially, so for them the flag is the only
  variable — exactly the pair that flickered. `SendFeedback`'s gate has no version check; one
  opus-4-7 capture cannot say whether it is immune to the flicker.

**Inferred, not observed**: that the proximate cause was a GrowthBook fetch that succeeded
with an incomplete payload — the only path yielding both flags false against a warm, correct
disk cache (`/root/.claude.json` caches both as `true`). The exchange itself was never
captured: the MITM proxy logs only Messages-shaped bodies, so
`api.anthropic.com/api/eval-authed/*` never reaches it. Capturing that endpoint would close
this.

Consequence: a single capture's tool inventory is not by itself evidence about a version — a
flag-gated tool can be present or absent independent of version and model id. A comparison
that trusts one capture's tool count without cross-checking siblings or re-capturing could
attribute an account-side flicker to a CLI release; two independent occurrences, both clearing
on re-capture, is why this is a finding and not noise.

### Fable and Mythos

2.1.269's model registry carries `claude-fable-5`, `claude-fable-5-1`, `claude-mythos-5` and
`claude-mythos-5-1`. `fable-5/default` is captured; the account's entitlement changed
mid-investigation — a request to `claude-fable-5` returned HTTP 429, `"Fable 5 requires usage
credits..."`, while a `claude-sonnet-5` control in the same minute succeeded, and after the
upgrade the same id captured normally. `claude-fable-5-1` and `claude-opus-4-8` answer too;
`claude-mythos-5` returns HTTP 404, `"There's an issue with the selected model
(claude-mythos-5). It may not exist or you may not have access to it."` — absent rather than
gated.

`fable-5/default`: `model: claude-fable-5`, 4 blocks, **3,556** `system_tokens`, 14 upfront
tools / 18 deferred (`tools_total_tokens` 30,287), `thread: {"type":"create"}`,
`output_config: {"effort":"high"}`, `thinking:{"type":"adaptive","display":"updates"}`, no
`fallbacks` key — every one matching `opus-5/default`, tool roster included (all 15 `tools[]`
entries byte-identical text; `opus-4-8/default` matches too, at the same 30,287), so tools are
uniform across the compressed branch even where the prompt text is not. Fable-5 sits on the
compressed branch with opus-5, settled empirically rather than from the registry's
`lean_prompt` capability.

The `# Environment` block's self-description — `"The most recent Claude models are the Claude
5 family and Haiku 4.5. Model IDs — Fable 5.1: 'claude-fable-5-1', Opus 5: 'claude-opus-5',
Sonnet 5: 'claude-sonnet-5', Haiku 4.5: 'claude-haiku-4-5-20251001'"` — names
`claude-fable-5-1`, not the `claude-fable-5` that captured here, and never mentions
`claude-opus-4-8`, `claude-mythos-5` or `claude-mythos-5-1`; 2.1.235 named `claude-fable-5`.
The self-reported roster undersells the registry.

Separately: a `regenerate.py --model claude-fable-5 default` run from before the entitlement
upgrade was reported to have produced a capture whose `request.json` carried `model:
claude-sonnet-5` but the compressed `# Harness` prompt at 3,557 system tokens — the prompt
built for the *requested* model, the id reflecting the model billed. Not in this tree and
unverifiable from disk; the warning stands: **the `model` field in a captured `request.json`
does not always identify the model the prompt was built for.**

## Tools

**14 upfront tools** plus one `DeferredToolPlaceholder` entry flagged `defer_loading: true`
(13 + placeholder in `sonnet-5/default`'s first capture — see the roster section above; the
re-capture on disk agrees with every other capture in the batch):

```
Agent, Artifact, AskUserQuestion, Bash, Edit, ListAgents, Read,
ReportFindings, ScheduleWakeup, SendFeedback, Skill, ToolSearch, Workflow,
Write
```

Against 2.1.235: **added** `SendFeedback` only — a set difference across all three branches,
not a count; the **deferred list did not change at all** (same 18 names for the 5-family, same
21 for opus-4-7). `SendFeedback`'s description (3,467 chars) is byte-identical across models.

Of the 13 upfront tools plus the placeholder that existed in 2.1.235, **nine are byte-for-byte
unchanged** in both models: `AskUserQuestion`, `Read`, `Edit`, `Write`, `ScheduleWakeup`,
`Skill`, `ToolSearch`, `ReportFindings`, `DeferredToolPlaceholder` — by rendering the 2.1.235
`request.json` files into this layout and diffing `tools/` with zero output. A tool counts as
changed when its `description` or its `input_schema` moved; `Agent` moved on the schema side
only, and the per-tool files render both. The remaining five:

| Tool | Sonnet 5 description | Opus 5 description | What changed |
|---|---|---|---|
| `Artifact` | 12,564 -> 25,099 | 12,564 -> 25,099 | New capabilities documented inline: comments, a shared database (get/list/query/set/update/str_replace/batch), asset upload, multi-file listing, publish watching. **Schema too**: 13 new properties (`files`, `root`, `writes`, `field`, `old_str`, `new_str`, `replace_all`, `if_version`, `as_level`, `icon`, `prompt`, `path`, `pin`), 11 more reworded, `action` gaining `read`, `watch`, `unwatch`, `status`, `resume_replies`, `list_types`, `list_files`, `read_file`, `delete`, `pin`, `unpin` and `db_op` gaining `str_replace`, `batch` |
| `Workflow` | 19,290 -> 3,480 | 19,290 -> 3,480 | Authoring detail moved out to a new `workflow-authoring` skill (loaded on demand); the tool description now covers only when to call it (explicit opt-in via "ultracode" or direct request) and the `meta`/`phase`/`pipeline` shape |
| `Bash` | 10,067 -> 10,078 | 1,043 -> 1,315 | Hardcoded attribution text (`Co-Authored-By:` / `🤖 Generated with`) replaced by a pointer to a system-reminder (see below) — sonnet's net change is small because that's the only edit; opus's short form also gained a sentence sonnet's long form already had, discouraging `cat`/`head`/`tail`/`sed`/`awk`/`echo` in favor of dedicated tools. **Schema too**: the `description` parameter gained `"Say what the command does in plain words: do not echo the command's text, its flags, or file paths - the user reads this description, often without seeing the command."` |
| `ListAgents` | 749 -> 777 | 749 -> 777 | Gained `"the teammates on your team"` in the list of who you can `SendMessage` to |
| `Agent` | 7,081 unchanged | 1,811 unchanged | **Schema only**: the `model` parameter now takes precedence over "the configured default subagent model" as well as over the agent definition's frontmatter, and an omitted `model` "inherits from the parent unless a default subagent model is configured". That default is the `CLAUDE_CODE_SUBAGENT_MODEL` environment variable (`f9()`, `src/chunk-dbb93264.js:103699`, `let e = a.CLAUDE_CODE_SUBAGENT_MODEL`), which upstream's own changelog demotes from override to default at 2.1.251 and pairs at 2.1.257 with `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`, which ignores per-spawn and agent-definition models alike. Neither is set in this repo |

`Artifact` and `Workflow` remain byte-identical between sonnet and opus; `Bash`, `Agent`,
`Read`, `Edit`, `Write` remain the tools with a materially shorter opus description;
`AskUserQuestion` remains the one exception where opus's is longer (1,531 sonnet / 1,786 opus).

`tools_total_tokens` (from `summary.json`, exact): 35,834 for every sonnet-5 variant / 30,283
(opus-5) / 36,155 (opus-4-7) / 30,287 (fable-5 and opus-4-8 — 4 tokens above opus-5 on
byte-identical text, tokenizer-boundary noise). `default`'s first capture read 33,878 with
`SendFeedback` missing. 2.1.235: 31,221 (sonnet) / 25,546 (opus-5) / 31,542 (opus-4-7) — the
rise is `Artifact` growing by ~12,500 chars outweighing `Workflow` shrinking by ~15,800.

## Tools — deferred (18 / 21, unchanged from 2.1.235)

Named in a system-reminder, schemas not loaded. 5-family models:

```
CronCreate, CronDelete, CronList, DesignSync, EndConversation, EnterPlanMode,
EnterWorktree, ExitPlanMode, ExitWorktree, Monitor, NotebookEdit,
PushNotification, RemoteTrigger, SendMessage, TaskOutput, TaskStop, WebFetch,
WebSearch
```

Opus 4.7 gets 21: the same list minus `EndConversation`, plus `TaskCreate`, `TaskGet`,
`TaskList`, `TaskUpdate` — identical to 2.1.235, membership checked by set diff. Opus 4.8 gets
18, with `EndConversation` included, same as the 5-family — consistent with the
version-threshold mechanism in the roster section (`claude-opus-4-8` parses to `[4,8]`, which
clears `opus`'s `[4,8]` floor exactly, where `claude-opus-4-7`'s `[4,7]` does not).

The Bash tool description still says `NEVER use the TaskCreate or Agent tools` (commit example)
and `DO NOT use the TaskCreate or Agent tools` (PR example) verbatim — confirmed present in the
2.1.269 capture by direct grep. On the 5-family models both still name a tool absent from every
list; on opus-4-7 `TaskCreate` is still deferred, so there the instruction still has a
referent. Opus-4-7's block 2 still carries `"Use TaskCreate to plan and track work"`, confirmed
verbatim; sonnet's block 2 has no such line.

## messages structure (model-gated, not version-gated — plus two new reminders)

The 2.1.235 split survives: 5-family models get a dedicated `role: "system"` message after
the first user message; opus-4-7 still gets everything inline in `messages[0]`.

**New in messages[0]** (all models, every variant including `--system-prompt` and a
general-purpose subagent's first message): a system-reminder giving git attribution
instructions, between the userEmail/gitStatus reminder and the user's text:

```
<system-reminder>
Attribution for git commits and pull requests you create from here on (this
replaces Claude Code's own earlier attribution guidance, such as a previous
copy of this reminder; the user's own instructions about these lines, such as
a CLAUDE.md or memory rule, take precedence over this reminder, but do not add
attribution lines this reminder leaves out):
- End git commit messages with:
Co-Authored-By: Claude <Model Name> <noreply@anthropic.com>
- End pull request descriptions with:
🤖 Generated with [Claude Code](https://claude.com/claude-code)
</system-reminder>
```

`<Model Name>` is templated per model (`Claude Sonnet 5`, `Claude Opus 5`, `Claude Opus 4.7`)
— the other half of the `Bash` tool change above: a per-request reminder always matches the
live model where the hardcoded description could not. `gitStatus` moved into the same reminder
block as `userEmail`, unconditionally, in every variant including `--system-prompt`.

**New in the `role: "system"` message** (5-family) / **prepended within `messages[0]`**
(opus-4-7, and subagents): the per-session `# Environment` and model-identity content removed
from the cached block, verbatim, plus the `# Scratchpad Directory` content folded into the same
reminder:

```
<system-reminder>
# Environment
You have been invoked in the following environment: 
 - Primary working directory: ...
 - Is a git repository: true
 - Platform: linux
 - Shell: bash
 - OS Version: ...
 - Scratchpad directory: ... — always use it for temporary files ...
</system-reminder>

<system-reminder>
You are powered by the model named <Model>. The exact model ID is <id>.
Assistant knowledge cutoff is <date>.
</system-reminder>
```

(Sonnet wraps each reminder in `<system-reminder>` tags; opus emits the same content bare, the
split the 2.1.235 doc documented.) For a subagent this reminder is ordered *after* the
deferred-tools reminder rather than before it (`subagent/subagents/001-request.json`).

**Removed**: the `## Auto Mode Active` reminder (and opus's bare `"While auto mode is active:
..."`) is **absent from all 13 `request.json` files in this batch** — 11 top-level captures
plus both `sonnet-5/subagent` children, checked case-insensitively — where 2.1.235 had it in
eight of eight. `capture.py`'s invocation is unchanged outside the trust-dialog fix, so this is
not a capture artifact; not a rename either, since `"bypass permissions mode"` (a live reminder
heading in differently-launched sessions) is also absent from every capture; and not a 2.1.269
content change: the renderer, `case "auto_mode":` at `src/chunk-dbb93264.js:235899`, builds
three texts from one event object — `e.bypass` gives `"While bypass permissions mode is
active:\n\n${E}"` (bash-first steer text, no heading), `e.steerOnly` the same shape headed
`"While auto mode is active:"`, otherwise the full `## Auto Mode Active` text — and 2.1.235 has
the identical three-way branch at `src/globals/20.js:24362`. What is not established is
*whether* the case fires for a plain `capture.py` session, which depends on something upstream
of this function.

**A `claude.sh` session reaches `e.bypass`**, read off a live 2.1.269 log: an `auto_mode`
attachment whose `rendered[].content` is `<system-reminder>\nWhile bypass permissions mode is
active:\n\n` followed by the bash-first steer text. A plain `capture.py` session takes the
default permission mode and shows none of the three; the uncaptured `bypass-permissions`
variant is what would put the two side by side.

Reminder-list content also drifted independent of both mechanisms (skill/agent content, not
CLI behavior):
- The `claude-code-guide` agent's description dropped `"early-access enablement"` from its
  `claude plugin eval` bullet.
- `Explore` and `Plan`'s exclusion lists grew `ArtifactComments`, `ArtifactData`,
  `ArtifactCheck` — identifiers that never appear as their own `tools[]` entries in any capture.
- Several skill descriptions changed wording (`design`, `dataviz`, `artifact-design`,
  `artifact-diagramming`, `artifact-capabilities`), and `workflow-authoring` appeared — the
  authoring reference `Workflow`'s description now points to instead of including inline.

Per-message character totals, measured over the full `messages[]` array minus the fixed
17-character canary (`"say exactly: done"`, once per request as the final text block of
`messages[0]`):

| | Opus 4.7 | Sonnet 5 | Opus 5 |
|---|---|---|---|
| 2.1.235 | 13,042 | 13,026 | 12,043 |
| 2.1.269 | 14,688 | 14,677 | 14,201 |

All three grew by roughly 1,600-2,150 chars: + the Attribution reminder (~330 chars) + the
relocated Environment/identity reminder (~500-700 chars, larger than what left block 3 because
it also carries the Scratchpad content) + the skill/agent wording growth, − the removed Auto
Mode reminder (~600-700 chars sonnet-side).

## Request parameters

| | 2.1.235 | 2.1.269 |
|---|---|---|
| `max_tokens` (sonnet, opus) | 64,000 | 64,000 (unchanged) |
| `model` | `claude-sonnet-5` / `claude-opus-5` / `claude-opus-4-7` | unchanged |
| `thinking` | `{"type": "adaptive"}` | `{"type": "adaptive", "display": "updates"}` — new `display` key, every model, every variant |
| `thread` | absent | `{"type": "create"}` — new key, every model, every variant checked |
| `fallbacks` (opus-5 only) | `[{"model": "claude-opus-4-8"}]` | **absent** — opus-5's fallback entry is gone; opus-4-7 had no `fallbacks` key in either version |
| `output_config.effort` | varies per request already in 2.1.235 (see below) | varies per request; all 8 `claude-sonnet-5` requests this round (6 variants + 2 subagent children) read `"high"` |

`fallbacks` disappearing for opus-5 lines up circumstantially with `claude-opus-4-8` now being
a standalone selectable id (see "Fable and Mythos") rather than purely an opus-5 fallback
target, though this document can't prove causation from the captures alone.

**Correction to the 2.1.235 doc**: it reported `output_config: {"effort": "max"}` as flat and
unchanged. Every individual 2.1.235 capture shows otherwise — `opus-4-7` was `xhigh`, `opus-5`
`high`, and sonnet-5's own captures split between `"max"` (`append`, `custom-output-style`,
`subagent`, `system-prompt`, `system-prompt-file`) and `"high"` (`default`). `effort` is
resolved per request, consistent with `thinking.adaptive`. This round opus-4-7 stayed `xhigh`,
opus-5 `high`, and all eight `claude-sonnet-5` requests read `high` — a data point, not a new
fixed value.

`context_management` (`clear_thinking_20251015`, keep all), `diagnostics`, and `stream` are
unchanged from 2.1.235.

### Billing header fields

`cc_version` bumped (`2.1.269.d5c` most calls in this batch; `.500` on the `sonnet-5/subagent`
parent call; `.415` on both its subagent children — same per-call-type suffix variance the
2.1.235 doc documented, just different literal suffixes). `cc_prompt_id`, `cc_prev_req`, and
`cc_is_subagent=true` are all still present and still vary per request exactly as before; no
new billing fields observed.

## `--system-prompt` behavior

Replaces blocks 2-3 with the custom text; the identity block survives. **Changed from
2.1.235**: `gitStatus` is no longer appended to the replacement block — it moved into
`messages[0]` unconditionally, so it survives an override the way `userEmail` always has.
Confirmed: `sonnet-5/system-prompt`'s block 2 shrank from 341 chars (custom text + gitStatus)
to 27 (custom text only, `"You are a custom assistant."` from `regenerate.py`'s
`CUSTOM_PROMPT`); the 314-character difference is exactly the gitStatus block.

`system_tokens` for the replacement-prompt variants (exact, from `summary.json`; opus-5's
`system-prompt-file` is new this round, sonnet-5's three were captured both times):

| Flag | Sonnet 5 (2.1.235 -> 2.1.269) | Opus 5 (2.1.269) |
|---|---|---|
| `--system-prompt` | 228 -> 116 | not captured |
| `--system-prompt-file` | 226 -> 114 | 117 |

The drop is `gitStatus` leaving the block. `--append-system-prompt` still inserts the custom
text at the end of block 3, now truly the *last* thing there.

What `--system-prompt` removes (blocks 2-3): all behavioral rules, output style,
session-specific guidance, memory instructions, the ecosystem-trivia `# Environment` remnant,
context management. What survives: billing header, identity, the CLAUDE.md wrapper reminder
with its "these instructions OVERRIDE any default behavior" line, `userEmail`+`gitStatus`+the
Attribution reminder (all in `messages[0]`), all upfront tool definitions, the deferred-tool
placeholder, and one system-role block (or a prepend to `messages[0]`) holding `# Environment`,
the model-identity line, the deferred-tool listing, the agent-type roster and every skill
description. Read that last item as behaviour, not facts: the skill and agent text is
Anthropic-authored guidance — trigger conditions, roster entries telling the model when to
delegate — and an override displaces none of it (`sonnet-5/system-prompt/prompt.md`,
`opus-5/system-prompt-file/prompt.md`, under `## messages[1] system, content[0]`).

### Background sessions do not inherit the flag

**The argv exclusion still holds; the measurements below were not retaken.** The forked-argv
list is now at `src/chunk-4zmskew4.js:630`, and it carries `--resume`, `--fork-session`,
`--reply-on-resume`, `--add-dir`, `--allowed-tools`, `--disallowed-tools`, `--model`,
`--effort`, `--permission-mode`, `--agent`, `--agents`, `--name` and `--append-system-prompt`
— and neither `--system-prompt` nor `--system-prompt-file`. So a custom prompt is still replaced
by the default one the moment a session backgrounds.

No backgrounding capture was retaken for 2.1.269; `docs/background-sessions.md` is the
maintained source, re-verified against 2.1.269 separately. To re-verify here: capture a
session with `--system-prompt-file`, trigger a background handoff, diff its prompt, and
re-trace the forked-argv function by grepping a flag literal such as `--fork-session`.

### Sub-agent behavior

Neither `--system-prompt` nor `--append-system-prompt` propagates to sub-agents (unchanged; not
re-tested this round, since no capture combined `--subagent` with a prompt override).

The identity line subagents receive — `"You are a Claude agent, built on Anthropic's Claude
Agent SDK."` — is byte-identical to 2.1.235 (confirmed by diff). Tool rosters are unchanged:

| Agent | Prompt identity | Model | Upfront tools |
|-------|----------------|-------|---------------|
| Explore | "file search specialist" | claude-sonnet-5 | Bash, Read, Skill, ToolSearch, DeferredToolPlaceholder |
| general-purpose | "an agent for Claude Code" | claude-sonnet-5 | Agent, Artifact, Bash, Edit, Read, Skill, ToolSearch, Write, DeferredToolPlaceholder |

Neither subagent type receives `SendFeedback` — the one new upfront tool this round is scoped
to the main session's own tool list. What changed for subagents is exactly the
block-3-relocation finding above, applied to their own (much shorter) persona block: the
`<env>` block, `"You are powered by..."`, `"Assistant knowledge cutoff..."`, the entire
`# Scratchpad Directory` section, and (for `general-purpose`) `gitStatus` are all removed from
the cached persona text and reappear in a new `role: "system"` message the same way the main
session's do — confirmed by diffing both `subagents/001/prompt.md` and `002/prompt.md` against
2.1.235.

## Security-monitor calls

**Not re-verified this round.** No fresh measurement of the side-channel harm-classifier calls
was attempted for 2.1.269 — doing so needs a live session making tool calls under a permission
mode that isn't `--dangerously-skip-permissions` (the 2.1.235 measurement notes that mode
suppresses these calls entirely), which this batch's captures don't provide. Treat the 2.1.235
description (model, prompt structure, `<severity>`/`<block>` response forms) as historical only.

## Interactive vs `-p` mode differences

**Not re-verified this round.** No `-p`-mode capture was retaken for 2.1.269. Given gitStatus
and the Environment block both moved to a messages-level reminder in interactive mode (above),
the old finding that "gitStatus is appended in `-p` mode too, block 2 is byte-identical" would
need rechecking specifically for whether `-p` mode gets the same new reminders — plausible, but
not established here. Settling it needs one `claude -p` capture on 2.1.269 compared the way the
2.1.235 doc compared it.

## How to re-capture

```bash
# ANTHROPIC_TOKEN_COUNT_API_KEY: claude_config.config.load() reads the checkout's own .env,
# resolved relative to the package -- a worktree without one dies on a KeyError. Export it.
# CLAUDE_CODE_OAUTH_TOKEN must be exported even when ~/.claude/.credentials.json holds a
# token: the two credentials produce different captures. See "Credentials" above.

./capture.py                                        # default prompt
./capture.py --system-prompt "Your custom prompt"
./capture.py --system-prompt-file /path/to/prompt.txt
./capture.py --append-system-prompt "Extra instructions"
./capture.py --subagent                             # Explore + general-purpose

./regenerate.py --model claude-sonnet-5 default     # one variant
./regenerate.py --model claude-opus-4-7 default     # the other prompt branch
./regenerate.py --model claude-opus-5               # all variants
```

Do not run two `regenerate.py` invocations in parallel — they share `capture-output/` and
`~/.claude/requests-log/` and will overwrite each other's intermediates.

### Trust-dialog default flipped — the failure this version will most likely hit

2.1.269's first-run trust dialog starts with the cursor on **"No, exit"** rather than the trust
option (2.1.235 defaulted to the trust option, so the bare `\r` `capture.py` sent was enough to
accept it). Confirming "No, exit" quits the child before it issues a single API call, and the
only symptom is `ERROR: No API calls captured.` — indistinguishable at a glance from a
credentials problem or a proxy-logging problem.

`capture.py` now reads which option the dialog's cursor (`❯`) is on and sends a down-arrow
(`\x1b[B`) before the accepting `\r` when needed (`_trust_arrow_presses` / `TRUST_OPTION` /
`DECLINE_OPTION` / `MENU_CURSOR`), from the live pty screen, so it tolerates the default
flipping again — if `ERROR: No API calls captured.` recurs with valid credentials and a
reachable proxy, check this first.

A capture is not byte-reproducible: the billing header fingerprints, the per-session temp
working directory, the scratchpad UUID and gitStatus's content change per run. The 2.1.235 doc
ran `sonnet-5/default` and `opus-5/default` three to four times each to show token totals
stable apart from those (9,359/9,365/9,365/9,368 and 3,871/3,866/3,860); this snapshot took one
capture per variant — **and the repeat runs that did happen did not reproduce the same tool
roster**: `sonnet-5/default` retaken ~1h45m later and `fable-5/default` ~20 minutes later both
landed at 14 upfront tools against an initial 13, traced above. Single-run captures in this
format can differ from a same-variant re-capture independent of anything `capture.py` controls.

`capture.py` strips every `CLAUDE_CODE_*` variable except `CLAUDE_CODE_OAUTH_TOKEN` from the
spawned session's environment: each is a knob that can change what the child's prompt says,
and a capture that inherits one records this machine's setup instead of the CLI's behaviour.
Two that demonstrably do: `CLAUDE_CODE_TMPDIR` moves the scratchpad path the prompt prints
(every capture reflects cc's own default temp root, `/tmp` here — `os.tmpdir()` falls back to
it once `$TMPDIR` is unset too); and `CLAUDE_CODE_FORK_SUBAGENT=0`, in this repo's
`settings.json` since c70788a (2026-09-04), swaps the subagent guidance from the `fork`
paragraph to the older Agent/Explore bullets. Scratchpad paths quoted here are as captured
under the default root.

`capture.py` spawns claude with a real pty via `pty.fork()` and `--setting-sources
project,local` to isolate from user settings, sends a canary message, then extracts the system
prompt from the intercepted API request. A placeholder CLAUDE.md is created in the temp working
directory so the capture includes the claudeMd context block. Output goes to `capture-output/`
(system.txt, request.json, summary.json) and stdout.

### Why pty (not heredoc/pipe)

Piping stdin (heredoc, `echo |`, subprocess with piped stdin) makes claude detect
non-interactive mode, which changes the identity block and skips gitStatus. `pty.fork()`
provides a real pty on both stdin and stdout so claude runs in true interactive mode. Unchanged
in 2.1.269 (`capture.py`'s spawn path is untouched by this round's fix).

### Bracketed paste

Claude Code enables xterm bracketed-paste mode (`\x1b[?2004h`). A `\r` concatenated into the
same write as the message body gets absorbed into the paste payload instead of submitting.
`spawn_claude` therefore writes the message and the submit-Enter as separate `os.write()` calls
with a short `time.sleep` between them. Unchanged in 2.1.269.

### Proxy log layout

The MITM proxy writes logs per-session under `~/.claude/requests-log/<session_id>/NNNN.json`.
Concurrent Claude Code sessions on the same machine all write under the same root. `capture.py`
filters logs by `session.pid` matching its spawned claude PID (the proxy resolves PID from
`~/.claude/sessions/<pid>.json`); mtime alone is not sufficient to isolate one capture's
traffic.

The proxy logs request bodies only, never headers, so no credential reaches disk.

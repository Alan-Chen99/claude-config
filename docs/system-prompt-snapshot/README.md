# Claude Code System Prompt Snapshots

Captured: 2026-09-11 (all directories below, all models)
Version: claude-cli/2.1.269
Mode: interactive (real pty via `capture.py`, `--setting-sources project,local`)
Default captures include a project CLAUDE.md.

Previous snapshot was 2.1.235 (captured 2026-09-08 / 2026-08-22); its numbers
live in git history for every file under this directory — `b318e59` is the
last commit before this recapture, so `git show b318e59:docs/system-prompt-snapshot/...`
gives the exact 2.1.235 artifact for any path here (`HEAD` itself keeps
moving as later commits land on top of the recapture, so pin the SHA rather
than counting `HEAD~N`). This revision was written by diffing that history
against the 2.1.269 recapture, and every number below was re-derived from the
artifacts on disk rather than carried forward — where the 2.1.235 figure is
given for comparison it is labelled as such.

Directories are named for the model id the request carried, minus its `claude-`
prefix. Aliases are repointed as models ship — `opus` meant `claude-opus-4-6` in
the 2.1.143 capture and still means `claude-opus-5` here — so an alias-named
directory changes meaning between captures while its path stays put. 2.1.269
also ships `claude-fable-5`, `claude-fable-5-1`, `claude-mythos-5`,
`claude-mythos-5-1`, and `claude-opus-4-8` as selectable ids. `fable-5/` and
`opus-4-8/` are now captured (`default` only, each); `fable-5-1`,
`mythos-5`, and `mythos-5-1` are not — see "Fable and Mythos" below for
what's measured about each and why the last three aren't directories here.

## Files

| File | What |
|---|---|
| `<model-id>/<variant>/request.json` | Full API request body — the artifact of record. Metadata redacted. |
| `<model-id>/<variant>/prompt.md` | Everything in that request except the tool definitions: parameters, the tool roster in request order, every system block, every message |
| `<model-id>/<variant>/tools/<Name>.md` | One tool definition each — attributes, description, input schema |
| `<model-id>/<variant>/summary.json` | Block count, token counts, tool inventory |
| `capture.py` | Captures one variant via pty + MITM proxy |
| `regenerate.py` | Drives `capture.py` across every variant, writes `summary.json` |
| `render_capture.py` | Renders `prompt.md` and `tools/` from a `request.json`; `--tree <root>` does every capture beneath a directory |
| `scripts/intercept/` — repo root, not under this directory | MITM proxy for API call logging (see `scripts/intercept/README.md`) |

### Reading a capture as a diff

`request.json` is the artifact of record and is unreadable as a diff: one line
per string with every newline escaped, so a reworded paragraph inside
`Artifact`'s 25,099-character description arrives in `git diff` as a single
changed line 25,099 characters wide. `prompt.md` and `tools/<Name>.md` carry
the same content as text, and they exist for the person reading that diff
across a release. They are derived — never hand-edit them.
`./render_capture.py --tree .` rebuilds them and
`tests/test_snapshot_rendering.py` fails when they drift from the
`request.json` beside them.

The split is per tool because that is what makes the diff legible: a tool whose
description changed is one file with line-level hunks, a tool that did not is
absent from the diff, an added or removed tool is an added or removed file, and
one tool's rewrite cannot displace another's inside the same hunk. Everything
that is not a tool stays in one file, because it is read as a whole — a section
moving between the system prompt and the messages, which 2.1.269 did to the
environment block, is only visible if both sit in the same diff.

From 2.1.269 on the review at an upgrade is `git diff` after re-capturing. An
older release's captures predate the layout, so render them into it first:

```bash
mkdir -p /tmp/old/opus-5/default
git show b318e59:docs/system-prompt-snapshot/opus-5/default/request.json \
  > /tmp/old/opus-5/default/request.json
./render_capture.py --tree /tmp/old
diff -ru -x request.json -x summary.json /tmp/old/opus-5/default opus-5/default
```

What no diff here can show: the deferred tools. A capture carries their names
in a reminder and a single `DeferredToolPlaceholder` entry, never their
descriptions or schemas — so of the 33 tools a 5-family session can reach, 18
are outside every file in this directory, and their text is only in the
decompiled source.

Variants: `default`, `custom-output-style`, `system-prompt`, `system-prompt-file`,
`append`, `subagent`. This snapshot captures all six for sonnet-5, `default`
for opus-4-7, both `default` and `system-prompt-file` for opus-5, and
`default` only for fable-5 and opus-4-8 — both added after an account
entitlement upgrade partway through this snapshot's capture session, opus-4-8
specifically to test whether fable's prompt was an oddity of the Fable
family or genuinely per-model (see "The prompt split is per model id, not
per model family" below — it's per-model).

None of them is the configuration this repo itself runs. `scripts/claude.sh`
launches `--dangerously-skip-permissions` with `--system-prompt-file`, and a
capture takes the default permission mode — which is why the bypass-permissions
reminder that a `claude.sh` session demonstrably carries appears in no file
here (see "Removed: the `## Auto Mode Active` reminder"). `regenerate.py`
defines a `bypass-permissions` variant for it, not yet captured, so that
directory is absent rather than empty.

### Subagent captures

`capture.py --subagent` adds a `subagents/` directory:

| File | What |
|---|---|
| `subagents/NNN/request.json` | Full API request for subagent N |
| `subagents/NNN/prompt.md` | Everything in it except the tool definitions |
| `subagents/NNN/tools/<Name>.md` | One tool definition each — the rosters are smaller than the parent's (5 for Explore, 9 for general-purpose, against 15) |
| `subagents/NNN/summary.json` | Block structure and tools for subagent N |

Subagent requests are identified by `cc_is_subagent=true` in the billing header,
not by size or tool count — the security-monitor call (below) also carries tools
and a large system prompt. Still true in 2.1.269: `sonnet-5/subagent`'s two
children carry `cc_is_subagent=true` and their own `cc_prompt_id`.

## Credentials

The spawned child needs its own Claude credentials. Claude Code strips
`CLAUDE_CODE_OAUTH_TOKEN` from tool subprocess environments, so a capture
launched from inside a Claude Code session inherits none, and
`~/.claude/.credentials.json` is empty when the session itself authenticates by
env var. Export the token before running:

```bash
set -a && . /workspace/.env && set +a   # or wherever the token lives
```

`capture.py` refuses to spawn when neither source has credentials. Without the
guard the child renders "Not logged in", issues zero API calls, and the failure
surfaces only as an empty capture. Unchanged in 2.1.269 — this snapshot's fix
(below) is a different failure mode with the same symptom.

## System prompt structure (v2.1.269, interactive mode)

The `system` array still carries 4 text blocks, same cache placement as
2.1.235: blocks 2 and 3 carry `cache_control`; only block 2 sets `scope:
global` (block 3 omits `scope`, so it falls back to org scope).

Sizes below are **characters**, measured directly from `request.json` in this
worktree. The 2.1.235 doc reported per-block token counts from a live
`count_tokens` call; that backend needs `ANTHROPIC_TOKEN_COUNT_API_KEY` from
`/repos/claude-config/.env`, which does not exist in this worktree (see
`agent-tools count-tokens`'s own docs on this), so no fresh per-block token
count could be taken this round. Character counts are measured directly from
the committed JSON and, for the byte-identity questions this doc cares about
(is block 2 unchanged, is a tool description shared across models), are the
stronger evidence anyway — the old per-tool token table shows `Skill` at 977
sonnet-tokens vs 909 opus-tokens on text the same table calls "identical",
which is a tokenizer artifact, not a text difference. Whole-request **token**
totals below (the `system_tokens` / `tools_total_tokens` figures) are exact:
they were measured by `count_tokens` at capture time and are stored in each
variant's `summary.json`.

| Block | Content | Cache | Opus 4.7 | Sonnet 5 | Opus 5 | Fable 5 | Opus 4.8 |
|---|---|---|---|---|---|---|---|
| 0 | Billing header (`cc_version=2.1.269...`) | none | 132 | 132 | 132 | 132 | 132 |
| 1 | Identity (`"You are Claude Code, Anthropic's official CLI for Claude."`) | none | 57 | 57 | 57 | 57 | 57 |
| 2 | Static behavioral rules | 1h, global scope | 10,676 | 10,574 | 1,210 | 1,210 | 1,152 |
| 3 | Session guidance, memory, environment (ecosystem facts only — see below), context mgmt | 1h, org scope | 16,895 | 17,128 | 8,546 | 9,571 | 5,278 |

Every figure above is the `default` variant, and block 2 is not a pure function
of the model: its opening sentence tracks the active output style. With one
selected, `helps users with software engineering tasks` becomes `helps users
according to your "Output Style", which describes how you should respond to user
queries`, and sonnet-5's block 2 measures 10,631 chars rather than 10,574
(`sonnet-5/custom-output-style/request.json` against `sonnet-5/default/request.json`;
`append` and `subagent` both stay at 10,574). Calling the block static is true
of a release, not of a session.

Block 1 is unchanged byte-for-byte from 2.1.235, for every model that existed
to compare (same 57 chars, confirmed by `git diff` producing no hunk touching
that line for any of the eight variant pairs checked; Fable 5 and Opus 4.8
weren't in the 2.1.235 capture set at all, so there's no version comparison
for them — only the cross-model one). Block 0 is *not* byte-identical: it's
the billing header, and three fields inside it change on every capture
regardless of version — `cc_version` (e.g. `2.1.235.cf9` -> `2.1.269.d5c`;
the call-type-dependent suffix is covered in "Billing header fields" below),
plus a per-run `cch` hash and `cc_prompt_id` UUID (the same per-run churn "How
to re-capture" describes below). `cc_version` is the only one of the three
that actually carries version information. What *is* unchanged is the length
and shape: still exactly 132 chars with the same field layout, for all eight
variant pairs checked. Opus 4.7, Sonnet 5, and Opus 5's own block 2 is each
individually unchanged byte-for-byte from 2.1.235 — same result, and the char
counts match the 2.1.235 doc's 10,676/10,574/1,210 exactly. All of the
version-over-version change for those three models is in block 3; see "What
moved out of block 3" below.

**Block 2 is not one shared text per branch, though** — see "The prompt
split is per model id, not per model family" for why the 1,210/1,210/1,152
column values above aren't a typo, and why block 3 diverges even further.

Total `system_tokens` per variant (from `summary.json`, exact):

| Variant | Opus 4.7 | Sonnet 5 | Opus 5 | Fable 5 | Opus 4.8 |
|---|---|---|---|---|---|
| `default` | 8,702 | 8,745 | 3,252 | 3,556 | 2,266 |
| `custom-output-style` | — | 8,761 | — | — | — |
| `append` | — | 8,754 | — | — | — |
| `subagent` | — | 8,743 | — | — | — |
| `system-prompt` / `system-prompt-file` | — | 116 / 114 | — / 117 | — | — |

2.1.235 comparison (opus-4-7/sonnet-5/opus-5 only; Fable 5 and Opus 4.8 are
new to this snapshot): 9,329 / 9,368 (sonnet-5 `default`) / 3,860. Every total
for those three dropped despite one more upfront tool (see "Tools"): the drop
comes entirely out of block 3 (the removed and relocated content below),
which outweighs the new tool's system-prompt footprint of zero (tools are
priced separately, in `tools_total_tokens`, not in `system_tokens`). Opus
4.8's 2,266 is the smallest prompt in the entire five-model set — a quarter
of Sonnet 5's 8,745 — so "the 2.1.269 system prompt" was never one size
either, on top of not being one text.

`sonnet-5/default`'s 8,745 is a corrected figure — the capture first taken for
this snapshot read 8,664 with `SendFeedback` and `EndConversation` both
missing, and a same-version re-capture ~1h45m later came back at 8,745 with
both present, in line with every sibling sonnet-5 variant. See "The upfront
tool roster is not a pure function of version and model id" below for the
full account; that finding, not this table, is where the 8,664 observation is
preserved.

### The prompt split is per model id, not per model family

Still true as a sorting rule, but coarser than this document previously
described it. Five models are captured now: sonnet-5 and opus-4-7 get the
long multi-section prompt; opus-5, fable-5, and opus-4-8 get the compressed
`# Harness` one. The branch predicate still sorts all five correctly — that
part hasn't changed. What's changed is what "getting the same branch" means:
it does not mean sharing one prompt. **Two families, per-model contents** is
closer to what five captures show than "two prompts."

The 2.1.235 doc traced the branch choice to source (`sV`/`aT`/`EAb` in the
2.1.235 decompile at `/repos/claude-code-decompiled/`). That repo has since
been re-extracted from the 2.1.269 binary (commit `8606fb66`) and
restructured — the binary now ships 1,677 separate ESM files
(`src/chunk-<hash>.js`) instead of one bundle, so `sV`/`aT`/`EAb` and every
other `src/globals/NN.js` citation no longer resolves by name; minified
identifiers are unique to a single chunk file now, and hashes rotate per
build regardless. Re-derived by grepping distinctive string literals instead:
the choice between the two prompt bodies is made once, in the same function
that assembles the rest of block 3, at `src/chunk-dbb93264.js:69226` —
`d ? [ORo(P, n)] : [vRo(P), xRo(n), ...]`, where `ORo` builds the compressed
`# Harness` body and `vRo`/`xRo`/... build the long-form sections. `d` comes
from `Ij(s)` two lines earlier, which resolves through a model-registry
`leanPrompt`/`leanPromptCompiledOnly` method this pass did not trace down to
its base cases — so the dispatch point (which of the two builder paths runs)
is confirmed, but the current model-id predicate (the 2.1.269 equivalent of
the old `claude-3-`/`haiku`/`sonnet`/`claude-opus-4-0..4-7` list) is not.
That dispatch is still a single, per-model-id decision, not per-family or
per-version — but as the rest of this section shows, `ORo` itself is not one
fixed text once you're inside it.

Opus 4.7 and Opus 4.8 are captured alongside Opus 5 for the same reason:
each is the nearest model on the other side of some boundary — 4.7 the
long-form branch, 4.8 the version threshold inside the compressed one (see
"The upfront tool roster is not a pure function of version and model id") —
isolating one difference at a time from every other opus-vs-X difference.

Block 1 (identity) is the same 57-character string across all five models —
the character-level check available in this worktree. Whether the tokenizers
still agree on it (as the 2.1.235 doc measured via `count_tokens`) is not
re-verified this round; see the token-count caveat above.

Block 2 and block 3, across all five `default` captures now on disk:

| Model | Branch | Block 2 chars | Block 3 chars | `system_tokens` | Block 3 headings |
|---|---|---|---|---|---|
| opus-4-8 | compressed | 1,152 | 5,278 | 2,266 | Session-specific guidance, Memory, Environment, Context management |
| opus-5 | compressed | 1,210 | 8,546 | 3,252 | …the same four, plus **Delivering work**, **Corrections** |
| fable-5 | compressed | 1,210 | 9,571 | 3,556 | **Communicating with the user**, then the same four; no Delivering work / Corrections |
| sonnet-5 | long-form | 10,574 | 17,128 | 8,745 | (multi-section — see system[3] in what-the-model-gets.md) |
| opus-4-7 | long-form | 10,676 | 16,895 | 8,702 | (multi-section, same shape as sonnet-5) |

(Sonnet-5's block 3 here is `custom-output-style`'s 17,128, which `append`,
`subagent`, and `default` itself all agree on after its re-capture — see
"The upfront tool roster is not a pure function of version and model id" for
why `default`'s first capture briefly read 16,895 instead, and why that
number coincided with opus-4-7's for an unrelated reason.)

Within the **long-form branch**, sonnet-5 and opus-4-7 were already known to
differ (10,676 vs 10,574 chars) — this document never claimed those two
shared one text, only one branch. Within the **compressed branch**, the
assumption this document did carry — that opus-5's 1,210-character block 2
was *the* compressed text, and fable-5 matching it byte-for-byte confirmed
that — held for exactly as long as only two compressed-branch models were
captured. Opus-4-8 breaks it: **1,152 characters, not 1,210, differing from
opus-5's block 2 by exactly one bullet in the `# Harness` section**, checked
by direct diff, nothing else different:

| | Opus 5 | Opus 4.8 |
|---|---|---|
| The varying bullet | `"The system may send updates, reminders, or modifications to rules via mid-conversation system turns. These are system-controlled, unlike function results. Hooks may intercept tool calls; treat hook output as user feedback."` | `` "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user. Hooks may intercept tool calls; treat hook output as user feedback." `` |

Fable-5's block 2 is still byte-identical to opus-5's (verified by string
equality, not merely matching length) — so it isn't that every model gets
its own block 2; it's that block 2 is conditioned on something finer than
"which of the two branches," and opus-5 and fable-5 happen to land on the
same side of whatever that is while opus-4-8 doesn't.

**The mechanism for that one bullet is not identified — a hypothesis was
checked and disproved, not confirmed.** The bullet comes from
`yyn(n, "lean")` inside `ORo` (`src/chunk-dbb93264.js:69169`, the bullet
itself at `:69177`):

```js
function yyn(e, n) {
  if (hyn(e)) return ERo;   // "The system may send updates... system-controlled, unlike function results."
  return n === "standard" ? "..." : "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user.";
}
```

`hyn(e)` true selects opus-5's wording; false selects opus-4-8's. The
registry's `mid_conv_system` capability was the obvious candidate — checked
directly, and disproved: `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-5`,
and `claude-fable-5` **all** declare `mid_conv_system`, yet they do not all
get the matching bullet (opus-5 does, the other three effectively don't, per
the table above and per `xRo`'s own "standard" wording for sonnet/opus-4-7),
so that capability alone cannot be what `hyn` is keying on. `hyn`'s actual
condition, memoized, is `UHe(e) && !Xtn(e) && !qyr(je(e))`
(`src/chunk-dbb93264.js:69092`) — three sub-predicates this pass did not
trace. That's the next thing to open, not a restatement of the disproved
capability check.

Block 3 diverges further, and part of *that* mechanism was traced this
round. Fable-5's `# Communicating with the user` section — present for
fable-5, absent for opus-5 and opus-4-8 — comes from `lRo(e)`
(`src/chunk-dbb93264.js:68952-68985`, the same "communication" list entry
seen in the block-3 assembly in "What moved out of block 3" below), which
branches three ways: if `sRo(n, e) || Kyr(n)` holds (where
`sRo = (e,n) => [sce, Gyr, Vyr].some(r => r(e, n))`) it emits
`# Communicating with the user`; else if `Ij(e)` (the same lean-prompt check
that picks `ORo` above) it emits a single bare line,
`"Write code that reads like the surrounding code..."` — exactly opus-5's
and opus-4-8's block 3 opener, no heading; else it emits sonnet's
`# Text output (does not apply to tool calls)` section. `sce` is one of four
things OR'd together in `sRo`, and fable-5's model registry entry declares a
`fable_5_mitigations` capability that `sce(e, o)` reads directly
(`src/chunk-eejnrs8c.js:40-44`: returns that capability's value if defined,
`true` for `claude-mythos-5`, `false` otherwise) — a named, plausible
candidate for *why* fable-5 takes the first branch. **Not established**:
which of the four OR'd conditions (`sce`, `Gyr`, `Vyr`, or `Kyr`) is the one
actually true for `claude-fable-5`, or whether opus-5/opus-4-8 lack all four
or merely `sce` specifically. `Gyr`/`Vyr`/`Kyr` were not traced this round.
A sibling capability, `fable_5_1_prompt_bundle`, is read by a similar
function, `ice(e)` (`src/chunk-eejnrs8c.js:46-48`) — not connected to
anything else in this document; noted as a second, entirely separate lead.

One correction for anyone re-deriving this later: it was suggested that
grepping the literal heading string `"# Communicating with the user"` finds
nothing in `src/`, on the theory that the heading is assembled rather than
stored whole. Checked directly and that's not so — `grep -rn "# Communicating
with the user" src/` finds it on the first line of `lRo`'s return statement,
`src/chunk-dbb93264.js:68961`, which is in fact exactly how `lRo` itself was
located for this section. The "grep a distinctive literal" method the
decompile's own README recommends worked here without a different anchor.

The upshot for reading these snapshots: there is no single object to call
"the compressed prompt" or "the opus-5 prompt" and reuse across opus-5,
fable-5, and opus-4-8. Block 2 sorts into at least two distinct texts within
the one branch; block 3 sorts into at least three (opus-5's six sections,
fable-5's five-plus-a-different-opener, opus-4-8's four with neither the new
opener nor `Delivering work`/`Corrections`). Per-model conditioning inside a
branch is not a corner case restricted to Fable — opus-4-8 shows it reaches
a model with no Fable-family relationship at all.

### What moved out of block 3

This is the substantive change this round, and it is identical in shape across
all three models (diffed directly, not inferred): four things left the cached,
1h-TTL block, and none of the tools or behavioral sections moved with them.

**Absent from the request, but not a code removal** — grepped the full JSON,
not just the system array, and found no replacement:
- The act-when-you-have-enough-information paragraph (`"When you have enough
  information to act, act. Do not re-derive facts already established..."`),
  introduced in 2.1.235, appears in none of the 2.1.269 captures. It is
  **still in the 2.1.269 source**, unchanged: `src/chunk-dbb93264.js:69214`
  builds block 3 as a list of labelled fragments including
  `Jb("act_dont_rederive", () => DRo() ? NRo : null)`, where `NRo` is this
  exact string and `DRo` (`:69182`) resolves
  `I("tengu_cedar_lantern", !0)` — a GrowthBook flag defaulting to *on* in
  code. The 2.1.235 source has the identical gate under the same flag name:
  `zB('act_dont_rederive', () => (fdE() ? mdE : null))` at
  `src/globals/21.js:13381`, with `fdE`'s own `et('tengu_cedar_lantern', !0)`
  at `src/modules/Jke.js:174`. Same flag, same code-level default, in both
  versions — the paragraph disappearing from every capture in this batch
  reads as the live flag value differing for this account right now, the
  same category of fact as the `SendFeedback`/`Artifact`-description
  observations elsewhere in this document, not a 2.1.269 code change.

**Relocated to a new per-message system-reminder** (present in `messages[]`
instead — see "messages structure" below for exactly where):
- The entire `# Environment` per-session block: `"You have been invoked in the
  following environment:"`, primary working directory, is-git-repo, platform,
  shell, OS version, the `"You are powered by the model named ..."` /
  `"Assistant knowledge cutoff is ..."` lines.
- `gitStatus` (branch, main branch, git user, status, recent commits) — no
  longer appended to any system block, in **any** variant, including the
  custom-`--system-prompt` one (see below).

**Genuinely removed from the assembly code**, unlike the paragraph above:
- The entire `# Scratchpad Directory` section (5 bullets, session-specific
  path), introduced in 2.1.235. Its content now lives inside the relocated
  `# Environment` reminder above, but the *section-builder call itself* is
  gone from the list, not merely gated to `null`: 2.1.235's block-3 assembly
  had its own entry, `zB('scratchpad', () => cvi())` (`src/globals/21.js`,
  same list as `act_dont_rederive` above); no `Jb("scratchpad", ...)` — or
  any entry by another label producing this content — appears anywhere in
  2.1.269's equivalent list at `src/chunk-dbb93264.js:69205-69224`.

What's left under the `# Environment` heading in the cached block, for all
three models, is now only static ecosystem trivia that doesn't vary by
session — model-id roster, Claude Code's available surfaces, fast mode — which
is presumably why it was safe to leave cached. Net effect: the cached block no
longer contains anything that would bust its cache across sessions with
different working directories, git branches, or capture dates; that content is
now injected fresh per request instead.

Opus's block 3 also picked up a small, real wording change, not part of the
relocation: the two sentences `"Do not call the AgentTool unless the user
requested it"` / `"Do not use workflows or deep-research unless the user
requested it"` became one: `"Do not use the Agent tool, workflows, or
deep-research unless the user, a CLAUDE.md file, or a skill asks for it"` —
consolidated, and the set of things that count as authorization widened from
"the user" to "the user, a CLAUDE.md file, or a skill." Sonnet's block 3 has no
equivalent sentence in either version.

### The upfront tool roster is not a pure function of version and model id

Timeline, from this batch's own file timestamps (`cc_version=2.1.269.d5c` on
every capture in it):

| Time | Capture(s) | Upfront / deferred |
|---|---|---|
| 19:10 | `opus-5/default` | 14 / 18 |
| 19:29 | `opus-4-7/default` | 14 / 21 |
| 19:31 | `sonnet-5/default`, first capture | **13 / 17** |
| 19:32-19:39 | the other 5 sonnet-5 variants, and `opus-5/system-prompt-file` | 14 / 18 |
| 21:16 | `sonnet-5/default`, re-capture | 14 / 18 |
| 21:44 | `fable-5/default`, first capture | **13 / 17** |
| 22:04 | `fable-5/default`, re-capture (the one on disk) | 14 / 18 |

Two anomalous runs now, across two different models, both missing exactly
`SendFeedback` and `EndConversation`, both non-reproducible on a same-variant
re-capture minutes to under two hours later.

**The mechanism is identified** — re-derived from the 2.1.269 decompile, not
taken on report:

- **`SendFeedback`** is gated on a remote GrowthBook flag,
  `tengu_juniper_relay`. Its `isEnabled()` (`src/chunk-dbb93264.js:181066`)
  calls `iL()`, which requires the `feedbackDrafts` setting not be `"off"`
  (`SQe()`) and `rCn()` to hold — a chain of entrypoint/provider checks
  (must be `"firstParty"`, not a plugin/eval context) ending in
  `I("tengu_juniper_relay", !1)` on every path, including the one where
  `CLAUDE_CODE_SEND_FEEDBACK` is explicitly `true` (`src/chunk-dbb93264.js:180877-180888`).
  Hardcoded fallback: **false**.
- **`EndConversation`** is gated on a different flag, `tengu_umber_kestrel`,
  same `I(..., !1)` shape and same false fallback — `zGt`
  (`src/chunk-t7d8rn9f.js:92-100`), consumed by `isEnabled()` at
  `src/chunk-1qj1h00h.js:276-279`.
- **Why both vanish together despite being different flags**: both resolve
  through one per-process GrowthBook client, `Tt()`
  (`src/chunk-5cs6j3p3.js:24712-24732`, one instance per API host), and one
  synchronous method on it, `getFeatureValueWithSource`
  (`src/chunk-5cs6j3p3.js:9166-9197`). Its resolution order is the
  load-bearing part, confirmed by reading it directly: it checks
  `this.remoteEvalFeatureValues.get(key)` (the in-memory result of this
  process's own GrowthBook fetch) first; if that key is present, use it; if
  the key is *absent* **but the map has any keys in it at all**
  (`this.remoteEvalFeatureValues.size > 0`), it returns the hardcoded
  default immediately — the on-disk cache (`cachedGrowthBookFeatures` in the
  global config) is only consulted when the map is completely empty. So one
  fetch that succeeds but comes back missing a key turns that flag off for
  the rest of the process's life, even with a correct cached value sitting
  on disk. A payload missing *both* `tengu_juniper_relay` and
  `tengu_umber_kestrel` turns both tools off together in that one process —
  one mechanism acting on two keys, not two coincidences.
- **This also explains `opus-4-7` never showing `EndConversation`** — not a
  bare model-conditioned quirk, but a second, independent gate ahead of the
  flag: `zGt` first requires the model version to clear a
  per-family threshold, `[["opus",[4,8]],["sonnet",[5]],["fable",[5]],
  ["mythos",[5]]]` (`src/chunk-t7d8rn9f.js:62`), compared by `MZt`
  (`src/chunk-970xe2g2.js:20-32`: parse `claude-<family>-<version>`, compare
  component-wise, family threshold wins ties). `claude-opus-4-7` parses to
  `[4,7]`, which fails `>= [4,8]`, so it's excluded regardless of the flag —
  confirmed deterministic, not observed-and-assumed. `claude-sonnet-5` and
  `claude-fable-5` both parse to `[5]`, which clears their `[5]` threshold
  trivially, so for them the flag is the only variable — which is exactly
  the pair that flickered. `SendFeedback`'s gate (`rCn`, above) has no such
  version check, so this explanation is scoped to `EndConversation` only;
  this dataset has a single opus-4-7 capture and can't say whether
  `SendFeedback` is immune to the same flag flicker for that model or simply
  wasn't caught flickering.

**Inferred, not observed**: that the proximate cause in both bad runs was a
GrowthBook fetch that *succeeded* but came back with an *incomplete*
payload. The code path above is the only one that yields both flags false
against a warm, correct disk cache (confirmed: `/root/.claude.json` caches
both as `true`), so it's the mechanism that fits — but the GrowthBook
exchange itself was never captured to confirm the payload shape directly:
the MITM proxy here only logs Messages-shaped request bodies, so
`api.anthropic.com/api/eval-authed/*` calls never reach its logs. Capturing
that endpoint alongside the Messages traffic would close this.

The load-bearing consequence is unchanged by having a mechanism, and slightly
better founded for it: a single capture's tool inventory is not by itself
evidence about a version, because a flag-gated tool can be present or absent
independent of the version and model id a request otherwise matches exactly.
These snapshots exist to be diffed against each other across versions — a
future comparison that trusts one capture's tool count without
cross-checking siblings, or without re-capturing, could attribute an
account-side flag flicker to a CLI release. Two independent occurrences, on
two different models, both clearing on re-capture, is why this is kept as a
finding rather than discarded as one-off noise.

### Fable and Mythos

2.1.269's model registry carries `claude-fable-5`, `claude-fable-5-1`,
`claude-mythos-5`, and `claude-mythos-5-1` alongside the ids this snapshot
already captured. `fable-5/default` is now one of them — the capturing
account's entitlement changed mid-investigation, which is itself worth
keeping on record: a request to `claude-fable-5` returned HTTP 429,
`"Fable 5 requires usage credits..."`, while a `claude-sonnet-5` control
request in the same minute succeeded (an entitlement limit on the account,
not a rate limit on the endpoint), and after the account was upgraded the
same model id captured normally. `claude-fable-5-1` and `claude-opus-4-8`
now answer too. `claude-mythos-5` still returns HTTP 404,
`"There's an issue with the selected model (claude-mythos-5). It may not
exist or you may not have access to it."` — absent rather than gated, unlike
Fable.

`fable-5/default`'s own numbers, re-derived from the artifact rather than
assumed: `model: claude-fable-5`, 4 blocks, **3,556** `system_tokens`, 14
upfront tools / 18 deferred (`tools_total_tokens` 30,287), `thread:
{"type":"create"}`, `output_config: {"effort":"high"}`,
`thinking:{"type":"adaptive","display":"updates"}`, no `fallbacks` key —
every one of those matches `opus-5/default` including the tool roster
(all 15 `tools[]` entries, upfront and placeholder, are byte-identical text
to opus-5's, not just same-length; `opus-4-8/default`'s tool roster matches
too, including the same 30,287 `tools_total_tokens`, so tools are uniform
across the compressed branch even where the prompt text is not). This
settled empirically what the mismatched-model-id incident below could only
predict from the registry's `lean_prompt` capability: fable-5 sits on the
compressed branch with opus-5, not with sonnet. What that branch membership
does and doesn't imply about shared *text* — including fable-5's and
opus-4-8's own block 2 and block 3, and why a same-time opus-5 recapture was
needed and has now settled the question — is covered in full in "The prompt
split is per model id, not per model family" above, rather than repeated
here.

The `# Environment` block's self-description line — `"The most recent Claude
models are the Claude 5 family and Haiku 4.5. Model IDs — Fable 5.1:
'claude-fable-5-1', Opus 5: 'claude-opus-5', Sonnet 5: 'claude-sonnet-5',
Haiku 4.5: 'claude-haiku-4-5-20251001'"` — still names `claude-fable-5-1`,
not the `claude-fable-5` id that actually captured here, and still never
mentions `claude-opus-4-8`, `claude-mythos-5`, or `claude-mythos-5-1` even
though the first of those three now-measured-live ids answers alongside
Fable. Named `claude-fable-5` (no `-1`) in every 2.1.235 capture. The
self-reported roster undersells the actual registry, and now that
`claude-fable-5` and `claude-opus-4-8` are both live, working, captured
requests, that's a concrete instance rather than an inference from the
registry alone.

Separately, and unaffected by any of the above: a
`regenerate.py --model claude-fable-5 default` run was reported to have
produced a capture whose `request.json` carried `model: claude-sonnet-5` but
whose system prompt was the compressed `# Harness` one (opus-5's branch) at
3,557 system tokens — i.e., Claude Code built the prompt for the *requested*
model (fable, landing on the compressed branch) and only the model id in the
fallback response reflected the model actually billed. That was a fallback
artifact from before the entitlement upgrade, is not the same event as the
real capture above, and is still not in this tree — it cannot be verified
from what's on disk. The practical warning stands regardless of whether it
recurs: **the `model` field in a captured `request.json` does not always
identify the model the prompt was built for.**

## Tools

**14 upfront tools** plus one `DeferredToolPlaceholder` entry flagged
`defer_loading: true` (13 + placeholder in `sonnet-5/default`'s first capture
— see "The upfront tool roster is not a pure function of version and model
id" above; the re-capture on disk now agrees with every other capture in the
batch):

```
Agent, Artifact, AskUserQuestion, Bash, Edit, ListAgents, Read,
ReportFindings, ScheduleWakeup, SendFeedback, Skill, ToolSearch, Workflow,
Write
```

Against 2.1.235: **added** `SendFeedback` only. Checked as a set difference
across all three model branches (opus-4-7, opus-5, sonnet-5), not just by
count: zero other tools were added or removed from the upfront list, and the
**deferred list did not change at all** — same 18 names for the 5-family, same
21 for opus-4-7, same membership, confirmed by set-diffing the 2.1.235 and
2.1.269 `tools_deferred` arrays directly. The entire "upfront count rose by
one" is `SendFeedback`, and only `SendFeedback`.

`SendFeedback`'s own description (3,467 chars) is byte-identical across
models — it lets the agent draft product/model-behavior feedback about Claude
Code itself, queued locally, never sent without explicit user approval.

Of the 13 upfront tools plus the placeholder that existed in 2.1.235 (14
entries total), **nine are byte-for-byte unchanged** in both models:
`AskUserQuestion`, `Read`, `Edit`, `Write`, `ScheduleWakeup`, `Skill`,
`ToolSearch`, `ReportFindings`, `DeferredToolPlaceholder` — confirmed by
rendering the 2.1.235 `request.json` files into this directory's layout and
diffing `tools/` per model with zero output. The remaining five changed:

A tool counts as changed when either its `description` or its `input_schema`
moved; `Agent` moved on the schema side only. The per-tool files render both,
so a schema-only change lands in the same diff as a reworded sentence.

| Tool | Sonnet 5 description | Opus 5 description | What changed |
|---|---|---|---|
| `Artifact` | 12,564 -> 25,099 | 12,564 -> 25,099 | New capabilities documented inline: comments, a shared database (get/list/query/set/update/str_replace/batch), asset upload, multi-file listing, publish watching. **Schema too**: 13 new properties (`files`, `root`, `writes`, `field`, `old_str`, `new_str`, `replace_all`, `if_version`, `as_level`, `icon`, `prompt`, `path`, `pin`), 11 more reworded, `action` gaining `read`, `watch`, `unwatch`, `status`, `resume_replies`, `list_types`, `list_files`, `read_file`, `delete`, `pin`, `unpin` and `db_op` gaining `str_replace`, `batch` |
| `Workflow` | 19,290 -> 3,480 | 19,290 -> 3,480 | Authoring detail moved out to a new `workflow-authoring` skill (loaded on demand); the tool description now covers only when to call it (explicit opt-in via "ultracode" or direct request) and the `meta`/`phase`/`pipeline` shape |
| `Bash` | 10,067 -> 10,078 | 1,043 -> 1,315 | Hardcoded attribution text (`Co-Authored-By:` / `🤖 Generated with`) replaced by a pointer to a system-reminder (see below) — sonnet's net change is small because that's the only edit; opus's short form also gained a sentence sonnet's long form already had, discouraging `cat`/`head`/`tail`/`sed`/`awk`/`echo` in favor of dedicated tools. **Schema too**: the `description` parameter gained `"Say what the command does in plain words: do not echo the command's text, its flags, or file paths - the user reads this description, often without seeing the command."` |
| `ListAgents` | 749 -> 777 | 749 -> 777 | Gained `"the teammates on your team"` in the list of who you can `SendMessage` to |
| `Agent` | 7,081 unchanged | 1,811 unchanged | **Schema only**: the `model` parameter now takes precedence over "the configured default subagent model" as well as over the agent definition's frontmatter, and an omitted `model` "inherits from the parent unless a default subagent model is configured". That default is the `CLAUDE_CODE_SUBAGENT_MODEL` environment variable (`f9()`, `src/chunk-dbb93264.js:103699`, `let e = a.CLAUDE_CODE_SUBAGENT_MODEL`), which upstream's own changelog demotes from override to default at 2.1.251 and pairs at 2.1.257 with `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`, which ignores per-spawn and agent-definition models alike. Neither is set in this repo |

`Artifact` and `Workflow` remain byte-identical between sonnet and opus (as in
2.1.235, new tools ship one description for both branches). `Bash`, `Agent`,
`Read`, `Edit`, `Write` remain the tools with a materially shorter opus
description; `AskUserQuestion` remains the one exception where opus's is
longer (1,531 sonnet / 1,786 opus, unchanged from 2.1.235).

Upfront tool payload: `tools_total_tokens` (from `summary.json`, exact) is
35,834 for every sonnet-5 variant including `default` (all identical, all
14-tool) / 30,283 (opus-5, either variant) / 36,155 (opus-4-7) / 30,287
(fable-5 and opus-4-8, identical to each other). `default`'s first capture,
before the re-capture, read 33,878 with `SendFeedback` missing. Fable-5 and
opus-4-8 read 4 tokens higher than opus-5 despite every individual tool
description being byte-identical text across all three — the same kind of
tokenizer-boundary noise already documented for `Skill` (977 vs 909 tokens on
text this section's own methodology note calls identical), not a text
difference. 2.1.235 comparison: 31,221 (sonnet) / 25,546 (opus-5) / 31,542
(opus-4-7) — the rise is `Artifact` growing by ~12,500 chars outweighing
`Workflow` shrinking by ~15,800.

## Tools — deferred (18 / 21, unchanged from 2.1.235)

Named in a system-reminder, schemas not loaded. 5-family models:

```
CronCreate, CronDelete, CronList, DesignSync, EndConversation, EnterPlanMode,
EnterWorktree, ExitPlanMode, ExitWorktree, Monitor, NotebookEdit,
PushNotification, RemoteTrigger, SendMessage, TaskOutput, TaskStop, WebFetch,
WebSearch
```

Opus 4.7 gets 21: the same list minus `EndConversation`, plus `TaskCreate`,
`TaskGet`, `TaskList`, `TaskUpdate` — identical to 2.1.235, membership checked
by set diff, not just count. Opus 4.8 gets 18, with `EndConversation`
included, same as the 5-family — consistent with the version-threshold
mechanism in "The upfront tool roster is not a pure function of version and
model id" (`claude-opus-4-8` parses to `[4,8]`, which clears `opus`'s `[4,8]`
floor exactly, where `claude-opus-4-7`'s `[4,7]` does not).

The Bash tool description still says `NEVER use the TaskCreate or Agent
tools` (commit example) and `DO NOT use the TaskCreate or Agent tools` (PR
example) verbatim — confirmed present in the 2.1.269 capture by direct grep.
On the 5-family models both still name a tool absent from every list; on
opus-4-7 `TaskCreate` is still deferred, so there the instruction still has a
referent. The `# Doing tasks`-branch models' block 2 still carries `"Use
TaskCreate to plan and track work"` for opus-4-7 only, confirmed present
verbatim; sonnet's block 2 still has no such line.

## messages structure (model-gated, not version-gated — plus two new reminders)

The 2.1.235 split survives exactly as documented: 5-family models get a
dedicated `role: "system"` message after the first user message; opus-4-7 on
this same 2.1.269 build still gets everything inline in a single `messages[0]`
(confirmed: `[m['role'] for m in messages]` is still `['user']` for opus-4-7,
old and new).

**New in messages[0]** (all models, confirmed in every variant including
`--system-prompt` and a general-purpose subagent's own first message): a
system-reminder block giving git attribution instructions, inserted between
the userEmail/gitStatus reminder and the user's actual text:

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

`<Model Name>` is templated per model (`Claude Sonnet 5`, `Claude Opus 5`,
`Claude Opus 4.7`, confirmed in the respective captures) — this is the other
half of the `Bash` tool change above: the attribution text used to be
hardcoded into `Bash`'s own description (with whatever model name was current
when that description was last written), which meant it could go stale
relative to the model actually running it. Moving it into a per-request
reminder lets it always match the live model. `gitStatus` also moved into the
same reminder block as `userEmail`, unconditionally, in every variant
including the ones that replace the cached system blocks (`--system-prompt`) —
see below.

**New in the `role: "system"` message** (5-family) / **prepended within
`messages[0]`** (opus-4-7, and subagents): the per-session `# Environment` and
model-identity content removed from the cached block (above), reappearing
here verbatim, plus the `# Scratchpad Directory` content folded into the same
reminder rather than its own block:

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

(Sonnet wraps each reminder in `<system-reminder>` tags as shown; opus still
emits the same content bare, separated by blank lines, matching the
tagged-vs-bare split the 2.1.235 doc already documented for this message.)
For a subagent, this same reminder is present but ordered *after* the
deferred-tools reminder rather than before it — confirmed in
`subagent/subagents/001-request.json`.

**Removed**: the `## Auto Mode Active` reminder (and opus's bare equivalent,
`"While auto mode is active: ..."`) is **absent from all 13 `request.json`
files in this batch** — the 11 top-level captures plus both
`sonnet-5/subagent` children — checked case-insensitively, including
`opus-5/default`, which in 2.1.235 had the bare form.
2.1.235 had it in eight of eight relevant captures (case-insensitive check
against that same file set). `capture.py`'s invocation is unchanged (no diff
against 2.1.235 outside the trust-dialog fix), so this isn't a capture-script
artifact.

It does not appear to be a straight rename: the phrase `"bypass permissions
mode"` (which does appear as a live reminder heading in other,
differently-launched sessions — see below) is also absent from every capture
here. And it is not a 2.1.269 content change either — checked directly
against source, now that a 2.1.269 decompile exists (see "The prompt split
is per model id" above for its layout). The function that renders this
reminder, `case "auto_mode":` at `src/chunk-dbb93264.js:235899`, builds three
different texts from the same event object: `e.bypass` produces
`"While bypass permissions mode is active:\n\n${E}"` (bash-first steer text
only, no heading); `e.steerOnly` produces the same shape headed
`"While auto mode is active:"` instead; otherwise it produces the *full*
`## Auto Mode Active` text — the heading, the bias-toward-acting paragraph,
and the git-status-before-destructive-commands paragraph the 2.1.235 doc
quoted — optionally with the bash-first text appended too. The 2.1.235
source has the identical three-way branch, same field names, at
`src/globals/20.js:24362` (`e.bypass ? ... : e.steerOnly ? ... : r + n + ...`,
under different minified names for the same fragments). Byte-identical
logic in both versions rules out a code change to *what* this reminder says;
what's not established is *whether* the case fires at all for a plain
`capture.py` session, which depends on something upstream of this function
that this pass did not trace.

**A `claude.sh` session reaches `e.bypass`.** Read off a live 2.1.269 session
log: an `auto_mode` attachment whose `rendered[].content` is
`<system-reminder>\nWhile bypass permissions mode is active:\n\n` followed by
the bash-first steer text, with no heading. A plain `capture.py` session takes
the default permission mode and shows none of the three; the uncaptured
`bypass-permissions` variant is what would put the two side by side.

This document's own capture chain is running under
`--dangerously-skip-permissions` (see `scripts/claude.sh` in the parent
repo) and *does* carry a live reminder headed `"While bypass permissions mode
is active: ..."` with the same Bash-first guidance — the `e.bypass` branch
above, directly observed, not inferred. So the underlying behavior (bias the
agent toward Bash for read/search/edit under a permissive mode) is confirmed
live in 2.1.269; only its trigger condition for a plain `capture.py` session
is unresolved.

Reminder-list content also drifted independent of both of these mechanisms
(same phenomenon the 2.1.235 doc noted for `Artifact`'s description — this is
skill/agent content, not CLI behavior):
- The `claude-code-guide` agent's description dropped the clause `"early-access
  enablement"` from its `claude plugin eval` bullet.
- `Explore` and `Plan`'s tool-exclusion lists (`"All tools except ..."`) grew
  three entries: `ArtifactComments`, `ArtifactData`, `ArtifactCheck` — new
  tool identifiers, consistent with `Artifact`'s description having grown to
  cover comments/database/assets, but these three never appear as their own
  `tools[]` entries in any capture, only inside these exclusion lists.
- Several skill descriptions picked up wording changes (`design`, `dataviz`,
  `artifact-design`, `artifact-diagramming`, `artifact-capabilities` all
  differ in punctuation or added detail), and a new skill entry appeared:
  `workflow-authoring` — the authoring reference `Workflow`'s own description
  now points to instead of including inline.

Per-message character totals (chars, not tokens, for the reasons given above),
measured over the full `messages[]` array minus the fixed 17-character canary
text (`"say exactly: done"`, unchanged in `capture.py` both versions). The
canary appears exactly once per request, as the entire final text block of
`messages[0]`, so each row below is that raw messages-array char count with
17 subtracted once:

| | Opus 4.7 | Sonnet 5 | Opus 5 |
|---|---|---|---|
| 2.1.235 | 13,042 | 13,026 | 12,043 |
| 2.1.269 | 14,688 | 14,677 | 14,201 |

All three grew by roughly 1,600-2,150 chars — a constant per-row offset, so
the canary-length correction above doesn't change this: + the Attribution
reminder (~330 chars) + the relocated Environment/identity reminder (~500-700
chars, larger than what left block 3 because it now also carries the
Scratchpad content) + the skill/agent wording growth above, − the removed
Auto Mode reminder (~600-700 chars sonnet-side).

## Request parameters

| | 2.1.235 | 2.1.269 |
|---|---|---|
| `max_tokens` (sonnet, opus) | 64,000 | 64,000 (unchanged) |
| `model` | `claude-sonnet-5` / `claude-opus-5` / `claude-opus-4-7` | unchanged |
| `thinking` | `{"type": "adaptive"}` | `{"type": "adaptive", "display": "updates"}` — new `display` key, every model, every variant |
| `thread` | absent | `{"type": "create"}` — new key, every model, every variant checked |
| `fallbacks` (opus-5 only) | `[{"model": "claude-opus-4-8"}]` | **absent** — opus-5's fallback entry is gone; opus-4-7 had no `fallbacks` key in either version |
| `output_config.effort` | varies per request already in 2.1.235 (see below) | varies per request; all 8 `claude-sonnet-5` requests this round (6 variants + 2 subagent children) read `"high"` |

`fallbacks` disappearing for opus-5 lines up circumstantially with
`claude-opus-4-8` now being a standalone selectable id (see "Fable and
Mythos") rather than purely an opus-5 fallback target, though this document
can't prove causation from the captures alone.

**Correction to the 2.1.235 doc**: it reported `output_config: {"effort":
"max"}` as a flat, unchanged fact. Checking every individual 2.1.235 capture
shows that was already an oversimplification — `opus-4-7` was `xhigh`,
`opus-5` was `high`, and even sonnet-5's own captures split between `"max"`
(`append`, `custom-output-style`, `subagent`, `system-prompt`,
`system-prompt-file`) and `"high"` (`default`) on the same version. `effort`
is evidently resolved per request, consistent with `thinking.adaptive`, not a
static per-model constant. In this round's captures, opus-4-7 stayed `xhigh`,
opus-5 stayed `high`, and all eight `claude-sonnet-5` requests in this batch —
the 6 top-level variants plus both `subagent` children — read `high` (no
`max` observed) — worth noting as a data point, not asserted here as a new
fixed value, since a single batch of same-day captures is exactly the kind of
sample that looked deceptively stable in 2.1.235 too.

`context_management` (`clear_thinking_20251015`, keep all), `diagnostics`, and
`stream` are unchanged from 2.1.235.

### Billing header fields

`cc_version` bumped (`2.1.269.d5c` most calls in this batch; `.500` on the
`sonnet-5/subagent` parent call; `.415` on both its subagent children —
same per-call-type suffix variance the 2.1.235 doc documented, just different
literal suffixes). `cc_prompt_id`, `cc_prev_req`, and `cc_is_subagent=true`
are all still present and still vary per request exactly as before; no new
billing fields observed.

## `--system-prompt` behavior

Replaces blocks 2-3 with the custom text; the identity block survives.
**Changed from 2.1.235**: `gitStatus` is no longer appended to the replacement
block at all — it moved into `messages[0]` unconditionally (see "messages
structure" above), so it now survives a `--system-prompt` override the same
way `userEmail` always has, rather than being specially re-appended to
whatever block 2-3 became. This simplifies "what survives an override": there
is no longer a system-block special case for `gitStatus`.

Confirmed directly: `sonnet-5/system-prompt`'s block 2 shrank from 341 chars
(2.1.235, custom text + gitStatus) to 27 chars (2.1.269, custom text only) —
the custom text itself (`"You are a custom assistant."`, from `regenerate.py`'s
`CUSTOM_PROMPT` constant, unchanged) is byte-identical between versions; the
314-character difference is exactly the gitStatus block that no longer
follows it.

`system_tokens` for the replacement-prompt variants (exact, from
`summary.json`; opus-5's `system-prompt-file` is new this round, sonnet-5's
three were captured both times):

| Flag | Sonnet 5 (2.1.235 -> 2.1.269) | Opus 5 (2.1.269) |
|---|---|---|
| `--system-prompt` | 228 -> 116 | not captured |
| `--system-prompt-file` | 226 -> 114 | 117 |

The drop is `gitStatus` leaving the block, consistent with the char-count
finding above (a session's real gitStatus block runs to a few hundred
characters, comparable to the ~110-char gap here once tokenized).

`--append-system-prompt` still inserts the custom text at the end of block 3,
after the context-management section — but it is now truly the *last* thing
in the block, since `gitStatus` no longer follows it (in 2.1.235 the custom
text was appended before gitStatus; now there's nothing after it).

What `--system-prompt` removes (blocks 2-3): all behavioral rules, output
style, session-specific guidance, memory instructions, the ecosystem-trivia
`# Environment` remnant, context management.

What survives: billing header, identity, the CLAUDE.md wrapper reminder with
its "these instructions OVERRIDE any default behavior" line,
`userEmail`+`gitStatus`+the new Attribution reminder (all in `messages[0]` now,
not in the system blocks), all upfront tool definitions, the deferred-tool
placeholder, and one system-role block (or a prepend to `messages[0]`) holding
`# Environment`, the model-identity line, the deferred-tool listing, the
agent-type roster and every skill description.

Read that last item as behaviour, not as facts. The skill and agent text in it
is Anthropic-authored guidance — trigger conditions, "load this before writing
that", roster entries telling the model when to delegate — and an override
displaces none of it. `sonnet-5/system-prompt/prompt.md` and
`opus-5/system-prompt-file/prompt.md` each hold it under
`## messages[1] system, content[0]`, byte-identical in structure to their
`default` counterparts.

### Background sessions do not inherit the flag

**The argv exclusion still holds; the measurements below were not retaken.**
The forked-argv list is now at `src/chunk-4zmskew4.js:630`, and it carries
`--resume`, `--fork-session`, `--reply-on-resume`, `--add-dir`,
`--allowed-tools`, `--disallowed-tools`, `--model`, `--effort`,
`--permission-mode`, `--agent`, `--agents`, `--name` and
`--append-system-prompt` — and neither `--system-prompt` nor
`--system-prompt-file`. So a custom prompt is still replaced by the default one
the moment a session backgrounds.

What was not redone is the measurement: no backgrounding-specific capture was
retaken for 2.1.269 (this batch has no "backgrounded" variant), so the
before/after block sizes quoted below remain the 2.1.235 ones. `docs/background-sessions.md` in the parent
repo is the canonical, actively-maintained source for this behavior and has
already been re-verified against 2.1.269 separately from this snapshot;
check there for current specifics rather than this section. If this section
needs its own re-verification: capture a session with `--system-prompt-file`,
trigger a background handoff, and diff its prompt the same way the 2.1.235
measurement did, then re-trace the forked-argv function by grepping a
distinctive flag literal (e.g. `--fork-session`) the way "The prompt split is
per model id" does above.

### Sub-agent behavior

Neither `--system-prompt` nor `--append-system-prompt` propagates to
sub-agents (unchanged; not re-tested this round, no evidence either way from
this batch's captures since none combined `--subagent` with a prompt
override).

The identity line subagents receive — `"You are a Claude agent, built on
Anthropic's Claude Agent SDK."` — is byte-identical to 2.1.235 (confirmed by
diff). Tool rosters are unchanged:

| Agent | Prompt identity | Model | Upfront tools |
|-------|----------------|-------|---------------|
| Explore | "file search specialist" | claude-sonnet-5 | Bash, Read, Skill, ToolSearch, DeferredToolPlaceholder |
| general-purpose | "an agent for Claude Code" | claude-sonnet-5 | Agent, Artifact, Bash, Edit, Read, Skill, ToolSearch, Write, DeferredToolPlaceholder |

Neither subagent type receives `SendFeedback` — the one new upfront tool this
round is scoped to the main session's own tool list, not extended to these two
fixed subagent tool sets.

What changed for subagents is exactly the block-3-relocation finding above,
applied to their own (much shorter) persona block: the `<env>` block,
`"You are powered by..."`, `"Assistant knowledge cutoff..."`, the entire
`# Scratchpad Directory` section, and (for `general-purpose`) `gitStatus` are
all removed from the cached persona text and reappear in a new `role: "system"`
message the same way the main session's do — confirmed by diffing both
`subagents/001/prompt.md` and `002/prompt.md` against 2.1.235.

## Security-monitor calls

**Not re-verified this round.** No fresh measurement of the side-channel
harm-classifier calls was attempted for 2.1.269 — doing so needs a live
session making tool calls under a permission mode that isn't
`--dangerously-skip-permissions` (the 2.1.235 measurement notes that mode
suppresses these calls entirely), which this batch's captures don't provide.
Treat the 2.1.235 description (model, prompt structure, `<severity>`/`<block>`
response forms) as historical only.

## Interactive vs `-p` mode differences

**Not re-verified this round.** No `-p`-mode capture was retaken for 2.1.269.
Given gitStatus and the Environment block both moved to a messages-level
reminder in interactive mode (above), the old finding that "gitStatus is
appended in `-p` mode too, block 2 is byte-identical" would need rechecking
specifically for whether `-p` mode gets the same new reminders — plausible,
but not established here. Settling it needs one `claude -p` capture on
2.1.269 compared the way the 2.1.235 doc compared it.

## How to re-capture

```bash
# ANTHROPIC_TOKEN_COUNT_API_KEY must be in /repos/claude-config/.env
# (loaded automatically by both scripts via claude_config.config.load()).
# See /repos/claude-config/.env.example for the full list of expected keys.
# CLAUDE_CODE_OAUTH_TOKEN must be exported — see "Credentials" above.

./capture.py                                        # default prompt
./capture.py --system-prompt "Your custom prompt"
./capture.py --system-prompt-file /path/to/prompt.txt
./capture.py --append-system-prompt "Extra instructions"
./capture.py --subagent                             # Explore + general-purpose

./regenerate.py --model claude-sonnet-5 default     # one variant
./regenerate.py --model claude-opus-4-7 default     # the other prompt branch
./regenerate.py --model claude-opus-5               # all variants
```

Do not run two `regenerate.py` invocations in parallel — they share
`capture-output/` and `~/.claude/requests-log/` and will overwrite each
other's intermediates.

### Trust-dialog default flipped — the failure this version will most likely hit

2.1.269's first-run trust dialog starts with the cursor on **"No, exit"**
rather than the trust option (2.1.235 defaulted to the trust option, so the
bare `\r` `capture.py` sent was enough to accept it). Confirming "No, exit"
quits the child before it issues a single API call, and the only symptom is
`ERROR: No API calls captured.` — indistinguishable at a glance from a
credentials problem or a proxy-logging problem.

`capture.py` was patched this round (see `_trust_arrow_presses` /
`TRUST_OPTION` / `DECLINE_OPTION` / `MENU_CURSOR` in the current
`docs/system-prompt-snapshot/capture.py`) to read which option the dialog's
cursor (`❯`) is currently on and send a down-arrow (`\x1b[B`) before the
accepting `\r` when it isn't already on the trust option, rather than
assuming either default. This is read from the live pty screen at spawn time,
so it should tolerate a future build flipping the default again — if
`ERROR: No API calls captured.` recurs with valid credentials and a reachable
proxy, check this first.

A capture is not byte-reproducible: the billing header fingerprints, the
per-session temp working directory, the scratchpad UUID, and gitStatus's
literal content all change per run — reconfirmed this round (every quoted
temp-directory string, `cch`, and `cc_prompt_id` in this document differs
across captures taken minutes apart in the same session). The 2.1.235 doc ran
`sonnet-5/default` and `opus-5/default` three to four times each to show
token totals were stable apart from those paths (9,359/9,365/9,365/9,368 and
3,871/3,866/3,860); this snapshot took one capture per variant instead, so
that specific multi-run stability claim was not re-established up front —
**and the repeat runs that did happen this round didn't reproduce the same
tool roster**: `sonnet-5/default` retaken ~1h45m later, and separately
`fable-5/default` retaken ~20 minutes later, both landed at 14 upfront tools
against an initial capture of 13. See "The upfront tool roster is not a pure
function of version and model id" above, which now traces this to a specific
GrowthBook-flag-resolution mechanism rather than leaving it as an
unattributed re-capture difference. Two data points isn't the
four-to-five-run stability sweep 2.1.235 got, but it's enough to say
plainly: single-run captures in this snapshot format can differ from a
same-variant re-capture, independent of anything `capture.py` controls, and
in this case the difference has an identified, cited cause.

`capture.py` strips every `CLAUDE_CODE_*` variable except
`CLAUDE_CODE_OAUTH_TOKEN` from the spawned session's environment, because each
one is a knob that can change what the child's prompt says — a capture that
inherits one records this machine's setup instead of the CLI's behaviour, and
the committed snapshots stop being comparable with no diff to show for it. Two
that demonstrably do so: `CLAUDE_CODE_TMPDIR` moves the scratchpad path the
prompt prints, so every capture instead reflects cc's own default temp root
(`/tmp` here — `os.tmpdir()` falls back to it once `$TMPDIR` is unset too); and
`CLAUDE_CODE_FORK_SUBAGENT=0`, which this repo's `settings.json` has set since
c70788a (2026-09-04), swaps the subagent guidance from the `fork` paragraph to
the older Agent/Explore bullets. The scratchpad paths quoted throughout this
document are spelled as they appear in the captured artifacts under the
default root, not as they would read from inside a redirected session.

`capture.py` spawns claude with a real pty via `pty.fork()` and
`--setting-sources project,local` to isolate from user settings, sends a canary
message, then extracts the system prompt from the intercepted API request. A
placeholder CLAUDE.md is created in the temp working directory so the capture
includes the claudeMd context block. Output goes to `capture-output/`
(system.txt, request.json, summary.json) and stdout.

### Why pty (not heredoc/pipe)

Piping stdin (heredoc, `echo |`, subprocess with piped stdin) makes claude
detect non-interactive mode, which changes the identity block and skips
gitStatus. `pty.fork()` provides a real pty on both stdin and stdout so claude
runs in true interactive mode. Unchanged in 2.1.269 (`capture.py`'s spawn path
is untouched by this round's fix).

### Bracketed paste

Claude Code enables xterm bracketed-paste mode (`\x1b[?2004h`). A `\r`
concatenated into the same write as the message body gets absorbed into the
paste payload instead of submitting. `spawn_claude` therefore writes the
message and the submit-Enter as separate `os.write()` calls with a short
`time.sleep` between them. Unchanged in 2.1.269.

### Proxy log layout

The MITM proxy writes logs per-session under
`~/.claude/requests-log/<session_id>/NNNN.json`. Concurrent Claude Code
sessions on the same machine all write under the same root. `capture.py`
filters logs by `session.pid` matching its spawned claude PID (the proxy
resolves PID from `~/.claude/sessions/<pid>.json`); mtime alone is not
sufficient to isolate one capture's traffic.

The proxy logs request bodies only, never headers, so no credential reaches
disk.

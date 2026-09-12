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
`claude-mythos-5-1`, and `claude-opus-4-8` as selectable ids; none of them are
captured as directories here — see "Fable and Mythos" below for why.

## Files

| File | What |
|---|---|
| `<model-id>/<variant>/system-prompt.md` | System prompt blocks, separated by `---BLOCK_SEPARATOR---` |
| `<model-id>/<variant>/request.json` | Full API request body. Metadata redacted. |
| `<model-id>/<variant>/summary.json` | Block count, token counts, tool inventory |
| `capture.py` | Captures one variant via pty + MITM proxy |
| `regenerate.py` | Drives `capture.py` across every variant, writes `summary.json` |
| `scripts/intercept/` | MITM proxy for API call logging (see `scripts/intercept/README.md`) |

Variants: `default`, `custom-output-style`, `system-prompt`, `system-prompt-file`,
`append`, `subagent`. This snapshot captures all six for sonnet-5, `default`
for opus-4-7, and — new this round — both `default` and `system-prompt-file`
for opus-5.

### Subagent captures

`capture.py --subagent` adds a `subagents/` directory:

| File | What |
|---|---|
| `subagents/NNN-system-prompt.md` | System prompt for subagent N |
| `subagents/NNN-request.json` | Full API request for subagent N |
| `subagents/NNN-summary.json` | Block structure and tools for subagent N |

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

| Block | Content | Cache | Opus 4.7 | Sonnet 5 | Opus 5 |
|---|---|---|---|---|---|
| 0 | Billing header (`cc_version=2.1.269...`) | none | 132 | 132 | 132 |
| 1 | Identity (`"You are Claude Code, Anthropic's official CLI for Claude."`) | none | 57 | 57 | 57 |
| 2 | Static behavioral rules | 1h, global scope | 10,676 | 10,574 | 1,210 |
| 3 | Session guidance, memory, environment (ecosystem facts only — see below), context mgmt | 1h, org scope | 16,895 | 17,128 | 8,546 |

Blocks 0 and 1 are unchanged byte-for-byte from 2.1.235 (same 132/57 chars,
confirmed by `git diff` producing no hunk in that region for any of the eight
variant pairs checked). **Block 2 is unchanged byte-for-byte from 2.1.235 for
every model** — same result, and the char counts match the 2.1.235 doc's
10,676/10,574/1,210 exactly. All of the block-level change this round is in
block 3; see "What moved out of block 3" below.

Total `system_tokens` per variant (from `summary.json`, exact):

| Variant | Opus 4.7 | Sonnet 5 | Opus 5 |
|---|---|---|---|
| `default` | 8,702 | 8,745 | 3,257 |
| `custom-output-style` | — | 8,761 | — |
| `append` | — | 8,754 | — |
| `subagent` | — | 8,743 | — |
| `system-prompt` / `system-prompt-file` | — | 116 / 114 | — / 117 |

2.1.235 comparison: 9,329 (opus-4-7) / 9,368 (sonnet-5 `default`) / 3,860
(opus-5). Every total dropped despite one more upfront tool (see "Tools"): the
drop comes entirely out of block 3 (the removed and relocated content below),
which outweighs the new tool's system-prompt footprint of zero (tools are
priced separately, in `tools_total_tokens`, not in `system_tokens`).

`sonnet-5/default`'s 8,745 is a corrected figure — the capture first taken for
this snapshot read 8,664 with `SendFeedback` and `EndConversation` both
missing, and a same-version re-capture ~1h45m later came back at 8,745 with
both present, in line with every sibling sonnet-5 variant. See "The upfront
tool roster is not a pure function of version and model id" below for the
full account; that finding, not this table, is where the 8,664 observation is
preserved.

### The prompt split is per model id, not per model family

Still true, and still the same three-way split: sonnet-5 and opus-4-7 get the
long multi-section prompt; opus-5 gets the compressed `# Harness` one. This is
confirmed directly from the captures (block 2 sizes above; opus-5's block 2
opens with a `# Harness` heading, the others with `# System`).

The 2.1.235 doc traced this branch to source (`sV`/`aT`/`EAb` in the 2.1.235
decompile at `/repos/claude-code-decompiled/`). That repo has since been
re-extracted from the 2.1.269 binary (commit `8606fb66`) and restructured —
the binary now ships 1,677 separate ESM files (`src/chunk-<hash>.js`) instead
of one bundle, so `sV`/`aT`/`EAb` and every other `src/globals/NN.js`
citation no longer resolves by name; minified identifiers are unique to a
single chunk file now, and hashes rotate per build regardless. Re-derived by
grepping distinctive string literals instead: the choice between the two
prompt bodies is made once, in the same function that assembles the rest of
block 3, at `src/chunk-dbb93264.js:69226` —
`d ? [ORo(P, n)] : [vRo(P), xRo(n), ...]`, where `ORo` builds the compressed
`# Harness` body and `vRo`/`xRo`/... build the long-form sections. `d` comes
from `Ij(s)` two lines earlier, which resolves through a model-registry
`leanPrompt`/`leanPromptCompiledOnly` method this pass did not trace down to
its base cases — so the dispatch point is confirmed, but the current
model-id predicate (the 2.1.269 equivalent of the old `claude-3-`/`haiku`/
`sonnet`/`claude-opus-4-0..4-7` list) is not. That's still enough to confirm
the dispatch is a single, still-per-model-id decision, not per-family or
per-version.

Opus 4.7 is still captured alongside Opus 5 for the same reason as before: it
is the nearest model on the other side of that branch, isolating the prompt
difference from every other opus-vs-sonnet difference.

Block 1 (identity) is still the same 57-character string across all three
models — the character-level check available in this worktree. Whether the
tokenizers still agree on it (as the 2.1.235 doc measured via `count_tokens`)
is not re-verified this round; see the token-count caveat above.

The text still diverges by branch, not by family — opus-4-7 sits with sonnet:

| | Opus 4.7 | Sonnet 5 | Opus 5 |
|---|---|---|---|
| Block 2 | 10,676 chars | 10,574 chars | 1,210 chars |
| Block 3 | 16,895 chars | 17,128 chars | 8,546 chars |

Sonnet's block 3 is `custom-output-style`'s 17,128, cross-checked against
`append`, `subagent`, and (after the re-capture below) `default` itself, which
all agree. An earlier draft of this table used `default`'s first capture,
which read 16,895 — 233 characters short of its own siblings because that
capture was also the one missing the `EndConversation` hint line (see "The
upfront tool roster is not a pure function of version and model id"); it
happened to coincide with opus-4-7's 16,895 for the same reason, not because
the two are otherwise the same text.

Opus 5's block 2 is still a single five-bullet `# Harness` section replacing
the other two models' `# System` / `# Doing tasks` / `# Executing actions with
care` / `# Using your tools` / `# Tone and style` sections, unchanged from
2.1.235. One fact the 2.1.235 doc didn't call out because it never quoted the
literal text: opus-5's block 2 has never carried the URL-guessing `IMPORTANT`
line (`"NEVER generate or guess URLs..."`) that sonnet and opus-4-7 have — this
is a pre-existing per-branch difference, confirmed unchanged (block 2 is
byte-identical old to new), not something introduced in 2.1.269.

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
| 21:16 | `sonnet-5/default`, re-capture (`./regenerate.py --model claude-sonnet-5 default`, same script, same unchanged binary) | 14 / 18 |

One capture, sandwiched between others that agree with each other both before
and after it, was served two fewer tools than its neighbors: `SendFeedback`
(upfront) and `EndConversation` (deferred) — unrelated tools, missing
together from the same single request. A re-capture of the identical variant
~1h45m later did not reproduce it.

"Rollout" is the wrong word for this — it implies a monotonic change (off,
then on, staying on), and the timeline doesn't show that: the dip is a single
point, bracketed by captures that already had both tools, and the retest
afterward had both again too. What the evidence supports is narrower:
**the upfront tool roster is not a pure function of version and model id.**
One capture in a nine-capture batch was served two fewer tools than every
capture minutes either side of it, and a re-capture did not reproduce it. The
mechanism is unidentified — this document did not determine what actually
differs between a request that gets 14 tools and one that gets 13 under
otherwise identical version, model, and script invocation. (Something like a
per-session remote gate would produce exactly this pattern, but that is an
unverified guess, not a finding — nothing in this batch confirms a
mechanism.)

This is the same *category* of fact as the 2.1.235 doc's `Artifact`
description-size observation — the account can serve different content for
the same version depending on when you ask — but sharper: a whole tool
disappearing and reappearing, not a description resizing.

The load-bearing consequence: a single capture's tool inventory is not by
itself evidence about a version. That matters specifically for this
document, since these snapshots exist to be diffed against each other across
versions — a future comparison that trusts one capture's tool count without
cross-checking siblings, or without re-capturing, could attribute an
account-side blip to a CLI release. The negative retest is what makes this
worth keeping rather than discarding as noise: observed once, checked
against a same-version re-capture, and it did not hold up as a stable fact
about `sonnet-5/default` — which is itself the finding.

### Fable and Mythos

2.1.269's model registry carries `claude-fable-5`, `claude-fable-5-1`,
`claude-mythos-5`, and `claude-mythos-5-1` alongside the ids this snapshot set
captures. None of them appear as a directory here. Measured directly against
the live binary (not from the committed captures, so there's no artifact
path for it in this tree): a request to `claude-fable-5` on the capturing
account returns HTTP 429, `"Fable 5 requires usage credits..."`; a
`claude-sonnet-5` control request in the same minute succeeded, so this is an
entitlement limit on the account, not a rate limit on the endpoint; and a
request to `claude-mythos-5` returns HTTP 404, `"There's an issue with the
selected model (claude-mythos-5). It may not exist or you may not have
access to it."`

One piece of this is independently confirmed by the committed artifacts,
though: the `# Environment` block's self-description line — `"The most recent
Claude models are the Claude 5 family and Haiku 4.5. Model IDs — Fable 5.1:
'claude-fable-5-1', Opus 5: 'claude-opus-5', Sonnet 5: 'claude-sonnet-5',
Haiku 4.5: 'claude-haiku-4-5-20251001'"` — named `claude-fable-5` (no `-1`) in
every 2.1.235 capture and `claude-fable-5-1` in every 2.1.269 capture. So
between versions this line's Fable entry was replaced, not added to: the
model's own self-description never mentions `claude-mythos-5`,
`claude-mythos-5-1`, or `claude-opus-4-8` in either version, even though (per
the reported findings above) at least two of those ids are real and
selectable. The self-reported roster undersells the actual registry.

A `regenerate.py --model claude-fable-5 default` run was reported to have
produced a capture whose `request.json` carried `model: claude-sonnet-5` but
whose system prompt was the compressed `# Harness` one (opus-5's branch) at
3,557 system tokens — i.e., Claude Code built the prompt for the *requested*
model (fable, landing on the compressed branch) and only the model id in the
fallback response reflected the model actually billed. That capture was
overwritten by a subsequent real `sonnet-5` capture and is not in this tree;
it cannot be verified from what's on disk. If it recurs, the practical
warning is real regardless: **the `model` field in a captured `request.json`
does not always identify the model the prompt was built for.** Reproducing it
for real would need a capturing account with Fable usage credits.

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
entries total), **ten are byte-for-byte unchanged** in both models: `Agent`,
`AskUserQuestion`, `Read`, `Edit`, `Write`, `ScheduleWakeup`, `Skill`,
`ToolSearch`, `ReportFindings`, `DeferredToolPlaceholder` — confirmed by
diffing old against new per model with zero output. The remaining four
changed:

| Tool | Sonnet 5 (2.1.235 -> 2.1.269) | Opus 5 (2.1.235 -> 2.1.269) | What changed |
|---|---|---|---|
| `Artifact` | 12,564 -> 25,099 | 12,564 -> 25,099 | New capabilities documented inline: comments, a shared database (get/list/query/set/update/str_replace/batch), asset upload, multi-file listing, publish watching |
| `Workflow` | 19,290 -> 3,480 | 19,290 -> 3,480 | Authoring detail moved out to a new `workflow-authoring` skill (loaded on demand); the tool description now covers only when to call it (explicit opt-in via "ultracode" or direct request) and the `meta`/`phase`/`pipeline` shape |
| `Bash` | 10,067 -> 10,078 | 1,043 -> 1,315 | Hardcoded attribution text (`Co-Authored-By:` / `🤖 Generated with`) replaced by a pointer to a system-reminder (see below) — sonnet's net change is small because that's the only edit; opus's short form also gained a sentence sonnet's long form already had, discouraging `cat`/`head`/`tail`/`sed`/`awk`/`echo` in favor of dedicated tools |
| `ListAgents` | 749 -> 777 | 749 -> 777 | Gained `"the teammates on your team"` in the list of who you can `SendMessage` to |

`Artifact` and `Workflow` remain byte-identical between sonnet and opus (as in
2.1.235, new tools ship one description for both branches). `Bash`, `Agent`,
`Read`, `Edit`, `Write` remain the tools with a materially shorter opus
description; `AskUserQuestion` remains the one exception where opus's is
longer (1,531 sonnet / 1,786 opus, unchanged from 2.1.235).

Upfront tool payload: `tools_total_tokens` (from `summary.json`, exact) is
35,834 for every sonnet-5 variant including `default` (all identical, all
14-tool) / 30,283 (opus-5, either variant) / 36,155 (opus-4-7). `default`'s
first capture, before the re-capture, read 33,878 with `SendFeedback`
missing. 2.1.235
comparison: 31,221 (sonnet) / 25,546 (opus-5) / 31,542 (opus-4-7) — the rise is
`Artifact` growing by ~12,500 chars outweighing `Workflow` shrinking by
~15,800.

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
by set diff, not just count.

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
`"While auto mode is active: ..."`) is **absent from every one of the nine
captures in this batch**, checked case-insensitively across every
`request.json` including `opus-5/default`, which in 2.1.235 had the bare form.
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
that this pass did not trace. Settling it would need either finding that
caller, or a capture that explicitly forces a permission mode
(`acceptEdits`, or a `settings.local.json` with `defaultMode` set) to see
which of the three branches — or none — a 2.1.269 session reaches.

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
measured over the full `messages[]` array minus the fixed 18-character canary
text (`"say exactly: done"`, unchanged in `capture.py` both versions):

| | Opus 4.7 | Sonnet 5 | Opus 5 |
|---|---|---|---|
| 2.1.235 | 13,041 | 13,025 | 12,042 |
| 2.1.269 | 14,687 | 14,676 | 14,200 |

All three grew by roughly 1,600-2,150 chars: + the Attribution reminder
(~330 chars) + the relocated Environment/identity reminder (~500-700 chars,
larger than what left block 3 because it now also carries the Scratchpad
content) + the skill/agent wording growth above, − the removed Auto Mode
reminder (~600-700 chars sonnet-side).

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

What survives: billing header, identity, `userEmail`+`gitStatus`+the new
Attribution reminder (all in `messages[0]` now, not in the system blocks), the
new Environment/model-identity reminder (in the system-role message or
prepended to `messages[0]`), all upfront tool definitions, the deferred-tool
placeholder.

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
`subagents/001-system-prompt.md` and `002-system-prompt.md` against 2.1.235.

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
**and the one repeat run this round did happen (`sonnet-5/default`, retaken
~1h45m later after this document's first draft used its initial capture) did
not reproduce the same tool roster**, landing at 14 upfront tools instead of
the first run's 13. See "The upfront tool roster is not a pure function of
version and model id" above. One data point isn't the four-to-five-run
stability sweep 2.1.235 got, but it's enough to say plainly: single-run
captures in this snapshot format can differ from a same-variant re-capture,
independent of anything `capture.py` controls.

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

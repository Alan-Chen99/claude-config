# What the Model Gets

Everything the model receives, in order, on a fresh interactive session with a
project CLAUDE.md, no output style.

v2.1.269. Source: `sonnet-5/default/request.json`, `opus-5/default/request.json`,
`opus-4-7/default/request.json`, `fable-5/default/request.json`,
`opus-4-8/default/request.json`. Capture uses `--setting-sources
project,local` to isolate from user settings. See README.md for capture
mechanics, the per-block character methodology, and everything flagged there
as not re-verified this round (backgrounding, `-p` mode, the
security-monitor calls).

**No two of these five models receive the same prompt**, and the "compressed
vs long-form" branch from earlier versions of this document is real but
coarser than it looks: opus-4-7 and sonnet-5 share the long-form branch (and
still differ from each other, as before); opus-5, fable-5, and opus-4-8 share
the compressed `# Harness` branch, but even within that branch no two of the
three have identical text. Opus-5 and fable-5 happen to share a
byte-identical block 2 — confirmed by string equality, not just length — but
opus-4-8's block 2 differs from both by one bullet, and all three have
distinct block 3 content. "The compressed prompt" is not one object; see
README.md, "The prompt split is per model id, not per model family," for the
full comparison and the two source-traced (one solved, one open) mechanisms
behind it. Every section below is given per model where they differ, same as
the 2.1.235 version of this document.

Sizes below are **characters**, measured directly from the `request.json`
files in this worktree. The 2.1.235 version of this document used
`count_tokens`-measured tokens per block and per tool; that backend requires
`ANTHROPIC_TOKEN_COUNT_API_KEY`, which is not available from this worktree
(see README.md's token-count note), so this revision was re-derived in
characters instead of carrying the old token figures forward. Whole-request
**token** totals (`system_tokens`, `tools_total_tokens`) are still exact,
taken from each variant's `summary.json` at capture time.

## system[0] (132 chars, not cached)

```
x-anthropic-billing-header: cc_version=2.1.269.d5c; cc_entrypoint=cli; cch=aa850; cc_prompt_id=ac495608-d169-47e9-8d35-d48e0903bff5;
```

Byte-length unchanged from 2.1.235 (132 chars there too — the version string
and prompt-id are both fixed-width, so a version bump doesn't change the
header's length). `cc_prompt_id` is still present and still changes per
request; follow-up turns still add `cc_prev_req=req_...`; subagent calls still
add `cc_is_subagent=true`.

## system[1] (57 chars, not cached)

```
You are Claude Code, Anthropic's official CLI for Claude.
```

Byte-identical across sonnet, opus-5, and opus-4-7, and unchanged from
2.1.235 (confirmed by diff, not just by matching length).

## system[2] — sonnet (10,574 chars, cached 1h global)

**Byte-for-byte unchanged from 2.1.235** — confirmed by `git diff` producing no
hunk anywhere in this block. Reproduced here because the 2.1.235 version of
this document only summarized it:

```
You are an interactive agent that helps users with software engineering tasks. Use the instructions below and the tools available to you to assist the user.

IMPORTANT: Assist with authorized security testing, defensive security, CTF challenges, and educational contexts. Refuse requests for destructive techniques, DoS attacks, mass targeting, supply chain compromise, or detection evasion for malicious purposes. Dual-use security tools (C2 frameworks, credential testing, exploit development) require clear authorization context: pentesting engagements, CTF competitions, security research, or defensive use cases.
IMPORTANT: You must NEVER generate or guess URLs for the user unless you are confident that the URLs are for helping the user with programming. You may use URLs provided by the user in their messages or local files.

# System                        [6 bullets]
{output rendering, permission model, system-reminder tags, prompt injection,
hooks, context compression}

# Doing tasks                   [14 bullets]
{software engineering framing, defer to user judgement, 2-3 sentence response
for exploratory questions, prefer editing existing files, OWASP security,
no extras/abstractions, no speculative error handling, no comments by default,
no WHAT comments, dev server for UI changes, no backwards-compat hacks,
/help link}

# Executing actions with care   [4 bullets]
{reversibility/blast radius policy, 4 categories of risky actions,
investigate before destroying, prefer reversible steps over deletion,
git status before work-discarding commands, secret review before pushing}

# Using your tools              [2 bullets]
{prefer dedicated tools over Bash, parallel calls when independent}

# Tone and style                [4 bullets]
{no emojis, concise, file_path:line_number references, no colon before
tool calls}
```

Nothing changed 2.1.235 -> 2.1.269 in this block, for either model on this
branch (opus-4-7's copy differs from sonnet's only in fixed, pre-existing
ways — see the per-branch table in README.md — and is likewise unchanged
since 2.1.235).

## system[2] — opus, fable, and opus-4-8 (1,210 / 1,210 / 1,152 chars, cached 1h global)

An eighth of sonnet's, unchanged from 2.1.235. The five sonnet sections
collapse into one, and — confirmed now by reading the literal text rather than
inferring from the old doc's placeholder — opus's copy has never carried the
URL-guessing `IMPORTANT` line sonnet and opus-4-7 have. `fable-5/default`'s
system[2] is not merely similar to this — it is byte-for-byte the same 1,210
characters, checked by string equality, not length:

```
You are an interactive agent that helps users with software engineering tasks.

IMPORTANT: Assist with authorized security testing, defensive security, CTF challenges, and educational contexts. Refuse requests for destructive techniques, DoS attacks, mass targeting, supply chain compromise, or detection evasion for malicious purposes. Dual-use security tools (C2 frameworks, credential testing, exploit development) require clear authorization context: pentesting engagements, CTF competitions, security research, or defensive use cases.

# Harness                       [5 bullets]
{markdown-in-terminal rendering, permission model and denied calls,
ONE BULLET THAT VARIES BY MODEL (below), prefer file/search tools + parallel
calls, file_path:line_number is clickable}
```

`opus-4-8/default`'s system[2] is *not* the same text — 1,152 chars, 58
shorter, differing from opus-5/fable-5 in exactly one bullet:

| Model | The varying bullet |
|---|---|
| opus-5, fable-5 | "The system may send updates, reminders, or modifications to rules via mid-conversation system turns. These are system-controlled, unlike function results. Hooks may intercept tool calls; treat hook output as user feedback." |
| opus-4-8 | "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user. Hooks may intercept tool calls; treat hook output as user feedback." |

Which wording a model gets is **not established** — traced to a function,
`yyn(n, "lean")`, gated by a condition `hyn(e)` whose obvious explanation (a
`mid_conv_system` registry capability) was checked directly and disproved:
sonnet-5, opus-5, fable-5, and opus-4-8 all declare that capability, yet only
opus-5 gets the first wording. See README.md for the exact source citation,
`hyn`'s real (untraced) condition, and why this is stated as an open question
rather than a guess.

Same gap as 2.1.235: no opus equivalent of `# Doing tasks`, `# Executing
actions with care`, or `# Tone and style` here; that guidance lives in
system[3] instead — in `# Delivering work` and `# Corrections` for opus, in a
differently-organized set of sections for fable, and in a fourth, shorter
arrangement for opus-4-8, all three of which differ from each other (below).

## system[3] — sonnet (17,128 chars, cached 1h org)

This is where everything changed. Structure, using `custom-output-style`'s
capture as the representative one (see below for how `default` compares):

```
# Text output (does not apply to tool calls)
{narrate before first tool call, short updates at key moments, no internal
deliberation, end-of-turn summary, no comments in code by default}

{they/them default for unstated pronouns, applies to visible thinking too}

# Session-specific guidance                       [4 bullets]
{`!` prefix for user-run commands, subagent_type "fork", /<skill-name>,
/code-review ultra / deprecated /ultrareview alias}

# auto memory                                     [+ 6 subsections]
{memory dir path, then:
 ## Types of memory
 ## What NOT to save in memory
 ## How to save memories
 ## When to access memories
 ## Before recommending from memory
 ## Memory and other forms of persistence}

# Environment                                     [3 bullets — was 10]
{most-recent-models roster, Claude Code's available surfaces, fast mode —
see "What left this block" below for what used to be here}

# Context management
{summarization notice only — see "What left this block" below}

EndConversation (deferred tool): use only for sustained user abuse directed
at the assistant, or when the user explicitly asks to see it demonstrated.
Load the full guidance via ToolSearch("select:EndConversation") before using
it.

<total_tokens>N tokens left</total_tokens>
```

No more `gitStatus` at the tail — see "messages structure" below for where it
went.

This section's structural findings come from `custom-output-style`
(17,128 chars) and are cross-checked against `append`, `subagent`, and
`default` itself (17,157 / 17,128 / 17,128 chars), which all agree.
`default` didn't always agree: the capture first taken for this snapshot was
missing both `SendFeedback` and `EndConversation`, and its own system[3] read
233 characters shorter (16,895) for lacking the `EndConversation` paragraph
below. A same-version re-capture ~1h45m later came back with both tools and
the canonical 17,128. See README.md, "The upfront tool roster is not a pure
function of version and model id," for the full account — it's a real,
kept finding, just not one that belongs to this block's structure.

### What left this block (2.1.235 -> 2.1.269)

Diffed directly against the 2.1.235 capture, not summarized:

- **Absent from every capture, but still in source**: the
  act-when-you-have-enough-information paragraph (`"When you have enough
  information to act, act. Do not re-derive facts already established..."`,
  new in 2.1.235). Grepped the full 2.1.269 request bodies for the phrase
  "enough information" — zero matches in any of the three models. But the
  2.1.269 decompile shows the line is still built by the same
  feature-flag-gated code as 2.1.235 (`tengu_cedar_lantern`, defaulting to
  on in both versions — see README.md for the exact citation), so this reads
  as the flag currently resolving off for this account, not a 2.1.269
  removal.
- **Relocated into a new system-reminder in `messages[]`** (see below): the
  entire per-session `# Environment` payload (cwd, is-git-repo, platform,
  shell, OS version, `"You are powered by the model named ..."`, knowledge
  cutoff) and `gitStatus`.
- **Relocated, and its section-builder call actually deleted from the
  assembly code** (unlike the paragraph above, which is only flag-suppressed):
  the entire `# Scratchpad Directory` section. Its content lives in the
  relocated `# Environment` reminder now, but 2.1.235's dedicated
  `scratchpad` list entry has no 2.1.269 counterpart at all — see README.md
  for the citation.

What's left under `# Environment` in the cached block is only the three
bullets that don't vary by session — the model-id roster, Claude Code's
available surfaces, and fast mode — which is presumably why they were safe to
leave cached while everything session-specific moved out.

Net effect on this block alone: 2.1.235's `default` was 18,812 chars and
2.1.269's `custom-output-style` is 17,128 — a genuine ~1,700-character
reduction once
you account for the output-style preamble both share, driven entirely by the
relocation above.

## system[3] — opus (8,546 chars, cached 1h org)

Same relocation, applied to opus's differently-organized block:

```
{preamble: write code that reads like the surrounding code;
 they/them pronoun default; confirm hard-to-reverse or outward-facing
 actions; report outcomes faithfully}

# Session-specific guidance   [3 bullets]
# Memory                      {prose — file format, linking, save/recall guidance}
# Environment                 [3 bullets — was 10, same relocation as sonnet]
# Context management          {summarization notice only — the
                               act-when-you-have-enough-info paragraph present
                               in 2.1.235 is gone here too, no replacement}
# Delivering work
# Corrections                 [wording changed — see below]

EndConversation (deferred tool): use only for sustained user abuse directed
at the assistant, or when the user explicitly asks to see it demonstrated.
Load the full guidance via ToolSearch("select:EndConversation") before using
it.

<total_tokens>N tokens left</total_tokens>
```

No `# Scratchpad Directory` section and no `gitStatus` tail here either — same
relocation as sonnet, confirmed by the same diff-against-2.1.235 method.

`# Corrections` lost two sentences and gained one, changing what counts as
authorization to use certain tools:

| 2.1.235 | 2.1.269 |
|---|---|
| `"Do not call the AgentTool unless the user requested it"` + `"Do not use workflows or deep-research unless the user requested it"` | `"Do not use the Agent tool, workflows, or deep-research unless the user, a CLAUDE.md file, or a skill asks for it"` |

Consolidated to one sentence, and the set of things that authorize using
Agent/workflows/deep-research widened from "the user" alone to "the user, a
CLAUDE.md file, or a skill." Sonnet's system[3] has no equivalent sentence in
either version — this is opus-only, both before and after.

Opus still has no `# Text output` block; `# Delivering work` and
`# Corrections` still carry the guidance sonnet gets inside `# Doing tasks`
and `# Text output`.

## system[3] — fable (9,571 chars, cached 1h org)

Shares system[2] with opus (above), but system[3] is its own arrangement —
not opus-5's sections with a swapped self-description, a different set of
headings and content entirely:

```
# Communicating with the user
{write for a teammate who stepped away, not a log file; lead with the
outcome; text between tool calls may not be shown, put everything the user
needs in the final message; tables only for short enumerable facts; match
response length to the question}

{write code that reads like the surrounding code; they/them pronoun default;
confirm hard-to-reverse or outward-facing actions; report outcomes
faithfully}

{Fable/Mythos positioning paragraph: "Claude Fable 5, the first model in
Anthropic's new Claude 5 family and part of a new Mythos-class model tier
that sits above Claude Opus in capability... Claude Fable 5 and Claude
Mythos 5 share the same underlying model. Claude Fable 5 includes additional
safety measures for dual-use capabilities, while Claude Mythos 5 is
available without those measures to only approved organizations..."}

# Session-specific guidance   [3 bullets — same text as opus's]
# Memory                      {prose — same text as opus's}
# Environment                 [3 bullets — same ecosystem trivia as every model]
# Context management          {summarization notice, PLUS: an
                               operating-autonomously paragraph, an exception
                               for pure questions, an end-of-turn checklist,
                               and a system-state-change caution — none of
                               which appear in opus-5/default}

EndConversation (deferred tool): use only for sustained user abuse directed
at the assistant, or when the user explicitly asks to see it demonstrated.
Load the full guidance via ToolSearch("select:EndConversation") before using
it.

<total_tokens>N tokens left</total_tokens>
```

No `# Delivering work` or `# Corrections` heading at all — the guidance
those carry for opus is either absent or folded into the new
`# Communicating with the user` / expanded `# Context management` sections
instead.

**This is Fable-specific, not elapsed-time content drift** — settled, not
still open. A same-time control was run: `opus-5/default` was recaptured
~30 minutes after `fable-5/default`, 3.5 hours after its own first capture,
and came back byte-identical to that first capture except the two things
that vary per capture by construction (the billing-header fingerprint and
the temp-directory string in the memory path) — checked directly, block by
block. Opus-5's prompt did not move in that window, so the gap between the
opus-5 and fable-5 captures cannot be what produced fable-5's different
block 3.

The `# Communicating with the user` section specifically has a partially
traced cause: it comes from a section-builder, `lRo(e)`, that takes this
branch when `sce(n, e) || Gyr(n, e) || Vyr(n, e) || Kyr(n)` holds, and
otherwise falls through to opus's bare one-line opener (if the model is on
the lean-prompt branch) or sonnet's `# Text output` heading (if not) — a
three-way branch that exactly reproduces all three observed outcomes.
`fable-5`'s model registry declares a `fable_5_mitigations` capability that
one of those four functions, `sce`, reads directly. **Not established**:
which of the four is actually true for `claude-fable-5`, or whether opus-5
and opus-4-8 fail all four or just `sce`. See README.md, "The prompt split is
per model id, not per model family," for the full citation, and for
`opus-4-8/default`'s own system[3] — a fourth, shorter arrangement, neither
opus-5's nor fable-5's.

## system[3] — opus-4-8 (5,278 chars, cached 1h org)

Shortest of the five, and not a fourth distinct arrangement so much as
opus-5's system[3] with two sections removed: `# Session-specific guidance`,
`# Memory`, and `# Environment` are byte-identical to opus-5's (checked
directly, modulo the random per-capture memory-path string), and the bare
one-line opener (`"Write code that reads like the surrounding code..."`) is
the same too. What's missing is `# Delivering work` and `# Corrections` —
and unlike fable-5, nothing replaces them; that guidance is simply absent
for opus-4-8, not folded into another section. `# Context management`
carries only the summarization notice, same as everyone else's currently
does (see README.md, "What moved out of block 3," for the
act-when-you-have-enough-information paragraph's own separate,
flag-gated absence).

## Tools — upfront (14, one new)

14 callable tools plus a `DeferredToolPlaceholder` entry flagged
`defer_loading: true`. Sent in `tools[]`, not in the system prompt. (The
captures first taken for `sonnet-5/default` and, separately, `fable-5/default`
each read 13, missing `SendFeedback`; a re-capture of each came back at 14,
matching every other capture in the batch. This isn't unattributed noise —
it's a remote GrowthBook flag, `tengu_juniper_relay`, defaulting to off and
occasionally resolving that way even with a correct value cached on disk;
see README.md, "The upfront tool roster is not a pure function of version
and model id," for the mechanism and its citations.)

| Tool | Sonnet chars | Opus chars | Same text both models? | Changed since 2.1.235? |
|---|---|---|---|---|
| Artifact | 25,099 | 25,099 | yes | **yes** — 12,564 -> 25,099, comments/database/assets/watch added |
| Bash | 10,078 | 1,315 | no | **yes** — attribution text replaced by a system-reminder pointer (both); opus also gained a cat/head/tail-avoidance sentence sonnet already had |
| Agent | 7,081 | 1,811 | no | no — byte-identical to 2.1.235 |
| Workflow | 3,480 | 3,480 | yes | **yes** — 19,290 -> 3,480, authoring detail moved to a new `workflow-authoring` skill |
| SendFeedback | 3,467 | 3,467 | yes | **new tool** |
| ScheduleWakeup | 3,148 | 3,148 | yes | no |
| AskUserQuestion | 1,531 | 1,786 | no (opus longer) | no |
| Read | 1,782 | 790 | no | no |
| Skill | 1,417 | 1,417 | yes | no |
| Edit | 1,094 | 360 | no | no |
| ToolSearch | 953 | 953 | yes | no |
| ListAgents | 777 | 777 | yes | **yes** — 749 -> 777, gained "the teammates on your team" |
| Write | 618 | 240 | no | no |
| ReportFindings | 574 | 574 | yes | no |
| DeferredToolPlaceholder | 83 | 83 | yes | no (chars unchanged; not comparable to the old token figures, see methodology note) |
| **total in request (`tools_total_tokens`, exact)** | **35,834** (sonnet, every variant including `default`) | **30,283** | | |

"Same text both models?" is checked by literal string equality here, not by
comparing lengths or token counts — the 2.1.235 doc's own per-tool token table
shows `Skill` at 977 vs 909 "tokens" on text it also calls identical, which is
a tokenizer artifact (opus and sonnet don't tokenize identically even where
the text matches exactly). Character-count equality plus a direct string
comparison is what "yes" means in this table.

Every tool that predates 2.1.235 and has a shorter opus description
(`Bash`, `Agent`, `Read`, `Edit`, `Write`) still does; `AskUserQuestion` is
still the lone exception where opus's is longer. That pattern is unchanged —
what changed is which tools' text moved at all: of the 13 pre-2.1.235 upfront
tools, only `Artifact`, `Bash`, `Workflow`, and `ListAgents` differ from their
2.1.235 text; the other nine (`Agent`, `AskUserQuestion`, `Read`, `Edit`,
`Write`, `ScheduleWakeup`, `Skill`, `ToolSearch`, `ReportFindings`) are
byte-for-byte unchanged, in both models — as is the `DeferredToolPlaceholder`
entry alongside them.

`SendFeedback` drafts feedback about Claude Code itself (product bugs or
model-behavior issues) into a local queue; it's never sent without explicit
user approval, and its description is identical across models — like every
other tool introduced after 2.1.235's baseline.

`Workflow`'s description shrank because its authoring detail — the
`meta`/`phases` shape, the `pipeline`/`parallel` script API, worked examples —
moved to a new on-demand skill, `workflow-authoring`, referenced by name
inside the shortened description. The description that remains is mostly
about *whether* to call it at all: explicit opt-in only (an "ultracode"
keyword or session flag, a direct request in the user's own words, or a
skill/slash-command that calls it), plus a configurable size guideline
("medium — keep workflows under 15 agents" by default, adjustable via
`/config`).

`Artifact`'s description grew because it now documents capabilities the
2.1.235 capture's `Artifact` didn't have at all: a shared per-artifact
database (`get`/`list`/`query`/`set`/`update`/`str_replace`/`delete`/`batch`),
comment-thread reading and replying, asset upload/list/read/delete, and
multi-file listing/reading. (This document's own tool list, at the top of the
session that produced it, carries this same expanded `Artifact` definition —
consistent with the capture.)

## Tools — deferred (18, unchanged from 2.1.235)

Named in a system-reminder, schemas not loaded:

```
CronCreate, CronDelete, CronList, DesignSync, EndConversation, EnterPlanMode,
EnterWorktree, ExitPlanMode, ExitWorktree, Monitor, NotebookEdit,
PushNotification, RemoteTrigger, SendMessage, TaskOutput, TaskStop, WebFetch,
WebSearch
```

**Unchanged from 2.1.235** — same 18 names for the 5-family (opus-4-7 gets 21:
this list minus `EndConversation`, plus `TaskCreate`/`TaskGet`/`TaskList`/
`TaskUpdate`), checked by set difference, not just count. The entire
"one more upfront tool" story this version is `SendFeedback`; nothing moved
between the upfront and deferred lists, and nothing was added to or dropped
from the deferred list itself.

Opus-4-7's missing `EndConversation` is not a bare per-model quirk: its gate
checks the model version against a per-family minimum
(`[["opus",[4,8]],["sonnet",[5]],["fable",[5]],["mythos",[5]]]`) before it
ever looks at the feature flag that governs the tool for everyone else.
`claude-opus-4-7` parses to `[4,7]`, which never clears `opus`'s `[4,8]`
floor, so it's excluded deterministically, independent of any flag state —
see README.md, "The upfront tool roster is not a pure function of version
and model id," for the citation.

The Bash tool description still says `NEVER use the TaskCreate or Agent
tools` (commit example) and `DO NOT use the TaskCreate or Agent tools` (PR
example), verbatim, confirmed by grep against the 2.1.269 capture — a
reference to a tool that exists in neither list on the 5-family models, and
still exists (deferred) on opus-4-7.

## messages structure (two new reminders, one removed)

```
messages[0]  role: user
  [0] text   <system-reminder> claudeMd </system-reminder>
  [1] text   <system-reminder> userEmail + gitStatus </system-reminder>
  [2] text   <system-reminder> git/PR attribution </system-reminder>      NEW
  [3] text   the actual human input

messages[1]  role: system
  [0] text   <system-reminder> Environment + model identity </system-reminder>  NEW (content)
             <system-reminder> deferred tools </system-reminder>
             <system-reminder> available agent types </system-reminder>
             <system-reminder> available skills </system-reminder>
             <system-reminder> <total_tokens>N tokens left</total_tokens> </system-reminder>
```

Compared to 2.1.235's version of this same diagram: `claudeMd` is now its own
block instead of being combined with `userEmail`+`currentDate`; `gitStatus`
joined `userEmail` (it used to live at the tail of the cached system[3]
block); a new Attribution block was inserted before the user's own text; the
Environment/model-identity content that used to be baked into cached
system[3] now opens `messages[1]` instead; and **`## Auto Mode Active` is
gone** — checked case-insensitively across all 13 `request.json` files in this
batch (the 11 top-level captures plus both `sonnet-5/subagent` children),
versus present in eight of eight comparable 2.1.235 captures.
See README.md for what this document could and couldn't establish about why.

A bare `Today's date is <date>.` line (no `# currentDate` header, no
surrounding "as you answer the user's questions" preamble) is now its own
trailing reminder inside `messages[1]` rather than being folded into
`messages[0]`'s claudeMd block — confirmed present in this exact bare form in
every capture checked.

Shape caveats, unchanged from 2.1.235:

- `messages[1].content` is a list of blocks on the first turn and a bare
  string on later turns.
- Sonnet wraps each reminder in `<system-reminder>` tags; opus emits the same
  content bare, separated by blank lines. For a subagent, the relocated
  Environment reminder appears *after* the deferred-tools reminder rather
  than before it (order differs slightly from the main session).

Measured over the full `messages[]` array, minus the fixed 17-character canary
text (`"say exactly: done"`) — it appears exactly once per request, as the
entire final text block of `messages[0]`, so each row below is that raw
messages-array char count with 17 subtracted once:

| | Opus 4.7 | Sonnet 5 | Opus 5 |
|---|---|---|---|
| 2.1.235 | 13,042 | 13,026 | 12,043 |
| 2.1.269 | 14,688 | 14,677 | 14,201 |

Grew by roughly 1,600-2,150 chars across all three — a constant per-row
offset, so the canary-length correction above doesn't change this: the new
Attribution and Environment/identity reminders outweigh the removed Auto Mode
reminder and the small skill/agent-roster wording changes (see README.md for
the itemized list). Its size still tracks the user's installed skills and
agents, so it's still not comparable across machines.

## API parameters

```jsonc
// Sonnet
{
  "model": "claude-sonnet-5",
  "max_tokens": 64000,                                       // unchanged
  "stream": true,
  "thinking": {"type": "adaptive", "display": "updates"},    // "display" is NEW
  "output_config": {"effort": "high"},                       // varies per request — see below
  "context_management": {"edits": [{"type": "clear_thinking_20251015", "keep": "all"}]},
  "diagnostics": {"previous_message_id": null},
  "thread": {"type": "create"}                                // NEW key, every request checked
}

// Opus 5 — same, except:
{
  "model": "claude-opus-5",
  "output_config": {"effort": "high"}                         // unchanged from 2.1.235
  // "fallbacks" is GONE — 2.1.235 had [{"model": "claude-opus-4-8"}] here;
  // opus-4-7 never had a fallbacks key in either version
}

// Opus 4.7 — same shape as sonnet, plus:
{
  "model": "claude-opus-4-7",
  "output_config": {"effort": "xhigh"}                        // unchanged from 2.1.235
}
```

`output_config.effort` was already per-request in 2.1.235, not the flat "max"
the 2.1.235 version of this document reported — checking each individual
2.1.235 capture shows opus-4-7 was already `xhigh`, opus-5 was already
`high`, and sonnet-5's own captures already split between `max` and `high`
depending on which variant. That's a correction to the old doc, not a
2.1.269 change. What this batch actually shows: opus-4-7 and opus-5 read the
same effort level as in 2.1.235, and all eight `claude-sonnet-5` requests this
round (6 variants + 2 subagent children) read `high` (no `max` observed) —
plausibly still adaptive/per-request rather than newly fixed, since a
same-day batch is exactly the sample that looked
stable in 2.1.235 too.

`thread: {"type": "create"}` is new in every request checked (all three
models, every variant). This document has no evidence for what other `type`
values exist or what a non-`"create"` thread looks like — no capture in this
batch is a follow-up turn on an existing thread.

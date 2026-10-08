# What the Model Gets

Everything the client sends, in order, on a fresh interactive session with a
project CLAUDE.md, no output style. The API adds text an intercept capture
cannot show: a tool-use batching sentence (*"…make all of the independent calls
in the same … block"*, not the prompt's own parallel-calls line), and a
browser-safety section (≈2.5k Opus-5.5 tokens) whenever a
`mcp__claude-in-chrome__*` tool is sent — both recited in `server-injected/`;
the mechanism in `notes/chrome-tool-names-trigger-server-safety-block.md`.

v2.1.289. Source: the seven `<model-id>/default/request.json` captures —
`sonnet-5`, `sonnet-5-5`, `opus-5`, `opus-5-5`, `opus-4-7`, `opus-4-8`,
`fable-5`. `opus-5-5` is what the `opus` alias resolves to and `sonnet-5-5`
what `sonnet` does, so those two are what this repo's own sessions get.
Capture uses `--setting-sources project,local` to isolate from user settings.
See README.md for capture mechanics and everything flagged there as not
re-verified, and `notes/cc-2.1.269-system-block-sizes.md` for the per-block
character methodology.

Sizes below are **characters**, `len()` on `request.json`'s `system[i].text`.
Whole-request **token** totals (`system_tokens`, `tools_total_tokens`) are
exact, from each variant's `summary.json`; `tools_total_tokens` prices only the
entries without `defer_loading`.

## The two branches, and what shares text inside them

| Model | system[2] | system[3] | `effort` / `max_tokens` |
|---|---|---|---|
| sonnet-5 | full, 10,967 | 17,913 | high / 64000 |
| opus-4-7 | full, 11,069 | 17,680 | xhigh / 64000 |
| opus-5 | lean, 1,603 | 9,331 | high / 64000 |
| fable-5 | lean, 1,603 | 10,244 | high / 64000 |
| opus-5-5 | lean, 1,603 | 5,951 | medium / 128000 |
| sonnet-5-5 | lean, 1,603 | 5,951 | medium / 128000 |
| opus-4-8 | lean, 1,545 | 5,951 | high / 64000 |

Equal lengths here are byte equality, checked by string comparison and md5
modulo the per-capture memory path: one lean system[2] serves four models and
one system[3] serves three. The 2.1.269 revision of this document recorded
that no two of the five models then captured shared a block; with seven models
the split is coarser, not finer, and the per-model mechanisms traced in
`notes/cc-2.1.269-prompt-split-per-model-id.md` are still how a model lands on
a branch. Sections below are given per branch, and per model where they differ.

## system[0] (190 chars, not cached)

```
x-anthropic-billing-header: cc_version=2.1.289.694; cc_entrypoint=cli; cch=...; cc_prompt_id=...; cc_turn_origin=human; cc_prompt_index=1; cc_turn_index=1;
```

The last three fields are new since 2.1.269, which carried the first four only
(132 chars, the same 132 as 2.1.235 — version string and prompt id are both
fixed-width). `cc_prompt_id` changes per request; follow-up turns add
`cc_prev_req=req_...`; subagent calls add `cc_is_subagent=true`.

## system[1] (57 chars, not cached)

```
You are Claude Code, Anthropic's official CLI for Claude.
```

Byte-identical across every model and unchanged since 2.1.235.

## system[2] — full branch, cached 1h global

```
You are an agent working with the user toward their goals, using your own judgment along the way. Use the instructions below and the tools available to you to assist the user.

IMPORTANT: Assist with authorized security testing, defensive security, CTF challenges, and educational contexts. Refuse requests for destructive techniques, DoS attacks, mass targeting, supply chain compromise, or detection evasion for malicious purposes. Dual-use security tools (C2 frameworks, credential testing, exploit development) require clear authorization context: pentesting engagements, CTF competitions, security research, or defensive use cases.
IMPORTANT: You must NEVER generate or guess URLs for the user unless you are confident that the URLs are for helping the user with programming. You may use URLs provided by the user in their messages or local files.

# System                        [7 bullets: output rendering, permission model,
                                 system-reminder tags, prompt injection,
                                 <pasted_content> tags, hooks, context compression]
# Doing tasks                   {software engineering framing, defer to user
                                 judgement, 2-3 sentence answers for exploratory
                                 questions, prefer editing existing files, OWASP
                                 security, no extras/abstractions, no speculative
                                 error handling, no comments by default, dev server
                                 for UI changes, no backwards-compat hacks, /help}
# Executing actions with care   {reversibility/blast-radius policy, 4 categories of
                                 risky action, investigate before destroying,
                                 git status before work-discarding commands,
                                 secret review before pushing}
# Using your tools              [2 bullets: prefer dedicated tools over Bash,
                                 parallel calls when independent]
# Tone and style                [4 bullets: no emojis, concise,
                                 file_path:line_number references, no colon
                                 before tool calls]
```

The opening sentence replaced 2.1.269's `"You are an interactive agent that
helps users with software engineering tasks."` and the `<pasted_content>`
bullet is new; nothing else in the block moved, and what did not move has not
moved since 2.1.235. opus-4-7's 11,069 is sonnet's plus one
`# Using your tools` bullet (`"Use TaskCreate to plan and track work..."`,
`opus-4-7/default/prompt.md:219`).

With an output style active the block is 11,005 chars and keeps the **old**
opener — `You are an interactive agent that helps users according to your
"Output Style", which describes how you should respond to user queries.` — so
the 2.1.269 phrasing family survives in `custom-output-style` and not in
`default`.

## system[2] — lean branch, cached 1h global

A seventh of sonnet's. The same opener and security `IMPORTANT` — never the
URL-guessing one — then the five sonnet sections collapsed into a single
`# Harness` of 6 bullets {markdown-in-terminal rendering, permission model and
denied calls, ONE BULLET THAT VARIES BY MODEL (below), `<pasted_content>` tags,
prefer file/search tools + parallel calls, `file_path:line_number` is
clickable}. opus-5, opus-5-5, sonnet-5-5 and fable-5 get a byte-identical
1,603; opus-4-8's 1,545 differs in exactly one bullet:

| Model | The varying bullet |
|---|---|
| opus-5, opus-5-5, sonnet-5-5, fable-5 | "The system may send updates, reminders, or modifications to rules via mid-conversation system turns. These are system-controlled, unlike function results. Hooks may intercept tool calls; treat hook output as user feedback." |
| opus-4-8 | "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user. Hooks may intercept tool calls; treat hook output as user feedback." |

Which wording a model gets is **not established**: `yyn(n, "lean")` gated by
`hyn(e)`, whose obvious explanation — a `mid_conv_system` registry capability —
was checked and disproved, every model declaring it while four get the first
wording. Citation and `hyn`'s real condition:
`notes/cc-2.1.269-prompt-split-per-model-id.md`.

There is no lean equivalent of `# Doing tasks`, `# Executing actions with care`
or `# Tone and style`. That guidance lives in system[3] where it exists at all:
`# Delivering work` and `# Corrections` for opus-5, `# Communicating with the
user` for fable-5, nothing for the three models on the 5,951-char block.

## system[3] — full branch, cached 1h org

```
# Text output (does not apply to tool calls)
{narrate before first tool call, short updates at key moments, no internal
deliberation, end-of-turn summary, no comments in code by default}

{they/them default for unstated pronouns, applies to visible thinking too}

# Session-specific guidance                       [4 bullets]
{`!` prefix for user-run commands, subagent_type "fork", /<skill-name>,
/code-review ultra}

# auto memory                                     [+ 6 subsections]
{memory dir path, then: ## Types of memory / ## What NOT to save in memory /
 ## How to save memories / ## When to access memories /
 ## Before recommending from memory / ## Memory and other forms of persistence}

# Environment                                     [3 bullets]
{most-recent-models roster, Claude Code's available surfaces, fast mode}

# Context management
{summarization notice, then "When you have enough information to act, act. Do
 not re-derive facts already established in the conversation, re-litigate a
 decision the user has already made, or narrate options you will not pursue..."}

EndConversation (deferred tool): use only for sustained user abuse directed
at the assistant, or when the user explicitly asks to see it demonstrated.
Load the full guidance via ToolSearch("select:EndConversation") before using
it.

<total_tokens>N tokens left</total_tokens>

WebSearch takes a `mode`. Use "standard" by default: it is the normal search,
quick and cheap. Use "extended" only when a "standard" result comes back thin,
off-target or possibly outdated... When you plan several searches, send them in
the same turn.
```

The 423-char `WebSearch` paragraph is the tail of system[3] on **every** model,
after `<total_tokens>`, and it is the one part of the block a `--system-prompt`
override does not remove (README, "`--system-prompt` behavior"). opus-4-7's
17,680 is sonnet's block minus the `EndConversation` paragraph — it is the one
model without that tool, and that is the whole 233-char difference.

Cross-checked over `default`, `custom-output-style` and `subagent` (17,913
each) and `append` (17,942, the appended text landing after the `WebSearch`
paragraph).

### Dated history of this block

- The act-when-you-have-enough-information paragraph shipped in 2.1.235, was
  absent from every 2.1.269 capture (zero matches for "enough information" in
  any of them) and is present in all seven 2.1.289 models: the
  `tengu_cedar_lantern` gate behind it resolves on —
  `notes/cc-2.1.269-block3-relocation.md`.
- 2.1.269 relocated the per-session `# Environment` payload (cwd, is-git-repo,
  platform, shell, OS version, `"You are powered by..."`, knowledge cutoff) and
  `gitStatus` into a `messages[]` reminder, and deleted the
  `# Scratchpad Directory` section-builder outright rather than suppressing it.
  What stays cached under `# Environment` is the three bullets that do not vary
  by session.
- Sonnet's block across releases: 18,812 chars (2.1.235) -> 17,128 (2.1.269)
  -> 17,913. The relocation cut ~1,700; 785 came back with the restored
  paragraph and the `WebSearch` tail.

## system[3] — lean branch, cached 1h org

The three lean arrangements share a 520-char preamble, byte-identical across
all five lean models {write code that reads like the surrounding code; they/them
pronoun default; confirm hard-to-reverse or outward-facing actions; report
outcomes faithfully}, the heading sequence `# Session-specific guidance` /
`# Memory` / `# Environment` / `# Context management`, and the same
`EndConversation` paragraph, `<total_tokens>` line and `WebSearch` tail sonnet
gets. None has a `# Text output` heading or a `# Scratchpad Directory`. (On
2.1.269 fable-5's and opus-4-8's preamble carried a sentence opus-5's did not,
`"If what you find contradicts how it was described, or you didn't create it,
surface that instead of proceeding."`; the five have since converged on
opus-5's wording.) What differs:

| Model | chars | On top of the shared sections |
|---|---|---|
| opus-5-5, sonnet-5-5, opus-4-8 | 5,951 | nothing — byte-identical to each other |
| opus-5 | 9,331 | `# Delivering work` (3 paragraphs), `# Corrections` (2) |
| fable-5 | 10,244 | `# Communicating with the user` ahead of the preamble, the Fable/Mythos positioning paragraph after it, and four extra `# Context management` paragraphs: operating autonomously, an exception for pure questions, an end-of-turn checklist, a system-state-change caution |

So the `opus` alias gets 3,380 chars fewer than `opus-5/default` — no
`# Delivering work`, no `# Corrections`, and not the reduced-delegation line
`# Corrections` carries: `"Do not use the Agent tool, workflows, or
deep-research unless the user, a CLAUDE.md file, or a skill asks for it"`,
which appears in opus-5 and in no other capture. (2.1.235 said the same thing
in two sentences authorizing the user alone; the 2.1.269 rewrite widened that
to a CLAUDE.md or a skill.) Whether opus-5-5 losing both sections is a new
bundle or the `opus_5_prompt_bundle` gate failing to match the new model id is
not established.

fable-5's `# Communicating with the user` is Fable-specific rather than elapsed
time: a same-time control on 2.1.269 recaptured `opus-5/default` ~30 minutes
after `fable-5/default` and 3.5 hours after its own first capture, and got that
first capture back byte-identical except the billing fingerprint and the
memory path. The section comes from a section-builder, `lRo(e)`, whose
three-way branch reproduces all three observed outcomes; which of its four
predicates is true for `claude-fable-5` is not established —
`notes/cc-2.1.269-prompt-split-per-model-id.md`.

## Tools — upfront (14)

14 callable tools plus a `DeferredToolPlaceholder` entry flagged
`defer_loading: true`, sent in `tools[]` and not in the system prompt. The same
14 names on all seven models.

| Tool | Full chars | Lean chars | Same text both branches? |
|---|---|---|---|
| Artifact | 19,888 | 19,888 | yes |
| Bash | 10,122 | 1,034 / 1,344 | no — three forms, below |
| Agent | 7,081 | 1,811 | no |
| Workflow | 3,480 | 3,480 | yes |
| SendFeedback | 3,467 | 3,467 | yes |
| ScheduleWakeup | 3,148 | 3,148 | yes |
| Read | 1,782 | 790 | no |
| AskUserQuestion | 1,531 | 1,786 | no (lean longer) |
| Skill | 1,417 | 1,417 | yes |
| Edit | 1,094 | 360 | no |
| ToolSearch | 953 | 953 | yes |
| ListAgents | 777 | 777 | yes |
| Write | 618 | 240 | no |
| ReportFindings | 574 | 574 | yes |
| DeferredToolPlaceholder | 83 | 83 | yes |

`tools_total_tokens`: 30,269 sonnet-5, 30,590 opus-4-7, 24,597 opus-5 and
opus-5-5, 24,717 fable-5 and opus-4-8, 24,713 sonnet-5-5. The last two carry
byte-identical tool text, so a gap that small is the per-model tokenizer, not
content — which is why "same text?" above is literal string equality and never
a token or character count. (The 2.1.235 table listed `Skill` at 977 tokens
against 909 on text it also called identical.)

Every lean description that was shorter than its full counterpart still is, and
`AskUserQuestion` is still the lone exception where lean is longer. Of the 13
upfront tools that predate 2.1.235, only `Artifact`, `Bash`, `Workflow` and
`ListAgents` have changed text since; the other nine (`Agent`,
`AskUserQuestion`, `Read`, `Edit`, `Write`, `ScheduleWakeup`, `Skill`,
`ToolSearch`, `ReportFindings`) and `DeferredToolPlaceholder` are
byte-for-byte unchanged on every model.

`Artifact` went 12,564 chars (2.1.235) -> 25,099 (2.1.269) -> 19,888, the last
step a rewrite into the third person that moved comments and the per-artifact
database out into two new deferred tools, `ArtifactComments` and
`ArtifactData`; assets and multi-file reads stayed, re-expressed as
`publish … asset: true`, `read … path|paths` and `list … scope: files|assets`.

`Workflow` is 3,480 chars in both releases and still changed text — its size
guideline reads "keep workflows under 10 agents" where 2.1.269 said 15 — so the
character column cannot be read as a change detector. Its authoring detail (the
`meta`/`phases` shape, the `pipeline`/`parallel` script API, worked examples)
left for the on-demand `workflow-authoring` skill in 2.1.269; what remains is
mostly about whether to call it at all.

`Bash` has three forms rather than two. 1,034 chars on opus-5 and opus-5-5,
which **dropped** the `` `IMPORTANT: Avoid using this tool to run `cat`,
`head`, `tail`, `sed`, `awk`, or `echo` commands...` `` bullet — exactly the two
models whose permission-mode reminder steers work toward Bash; 1,344 on
sonnet-5-5, opus-4-8 and fable-5, which keep it (2.1.269 had one 1,315-char
lean form for all three lean models); 10,122 on sonnet-5 and opus-4-7. All
three raise the timeout ceiling from 600000 to `2147483647 for a foreground
command`, in the description and the schema alike.

## Tools — deferred (19)

Named in a system-reminder, schemas not loaded *in this request*. Their
definitions are captured in `<model-id>/tool-search-loaded/tools/`, and for the
Chrome and connector tools a `default` session never names, in
`opus-5/logged-in-tool-search-loaded/tools/`. 2.1.289 added `ArtifactComments`
and `ArtifactData` and dropped `TaskOutput`, whose only remaining trace in the
binary is a retired-name set — `var o_e = new Set(["Frame", "FrameRead",
"TeamCreate", ...` (`src/chunk-wgfrtm7w.js:42837`) — beside `AgentOutput`,
`BashOutput` and `TeamCreate`. opus-4-7 has 22 instead: the five `Task*` tools,
and no `EndConversation`. Of the 19, only `WebFetch` (1,841 full / 651 lean)
and `WebSearch` (1,344 / 334) split by branch; the other 17 are byte-identical
across all seven models. The names and the `Bash` description's two surviving
`TaskCreate` references: `notes/cc-2.1.269-tool-roster-delta.md`.

## messages structure

```
messages[0]  role: user
  [0] text   <system-reminder> claudeMd </system-reminder>
  [1] text   <system-reminder> userEmail + gitStatus </system-reminder>
  [2] text   <system-reminder> git/PR attribution </system-reminder>
  [3] text   the actual human input

messages[1]  role: system
  [0] text   <system-reminder> Environment + model identity </system-reminder>
             <system-reminder> deferred tools </system-reminder>
             <system-reminder> available agent types </system-reminder>
             <system-reminder> available skills </system-reminder>
             <system-reminder> the permission-mode reminder </system-reminder>
             <system-reminder> <total_tokens>N tokens left</total_tokens> </system-reminder>
             <system-reminder> Today's date is <date>. </system-reminder>
```

`Today's date` is a bare line, with no `# currentDate` header and no "as you
answer the user's questions" preamble around it. `messages[0]`'s `claudeMd`
became its own block in 2.1.269 (2.1.235 combined it with
`userEmail`+`currentDate`), `gitStatus` joined `userEmail` from the tail of the
cached system[3], and the attribution block was inserted before the user's own
text. `messages[0] content[1]`'s closing line is 2.1.289's: `"Claude Code
attached this context automatically; it isn't part of the user's message. It
describes the user's own account and workspace, so they don't need it reported
back."`, where 2.1.269 said `"IMPORTANT: this context may or may not be
relevant to your tasks..."`.

Shape caveats:

- `messages[1].content` is a list of blocks on the first turn, a bare string on
  later turns.
- Sonnet wraps each reminder in `<system-reminder>` tags; the lean models emit
  the same content bare, separated by blank lines. opus-4-7 is a third shape:
  no `messages[1]` at all, the same content as 12 separately tagged
  `messages[0]` blocks.
- For a subagent the relocated Environment reminder comes *after* the
  deferred-tools reminder rather than before it.

### The permission-mode reminder

2.1.235 had one, 2.1.269 none, 2.1.289 two disjoint texts chosen by branch,
both inserted between the skills listing and `<total_tokens>`:

- **Full branch** (sonnet-5, opus-4-7): `## Auto Mode Active`, 949 chars,
  byte-identical to 2.1.235's — bias toward not stopping for clarifying
  questions, then `git status` and stash before a work-discarding command and a
  secret review before pushing.
- **Lean branch** (opus-5, opus-5-5): a first line templated from the
  permission mode — `While auto mode is active:`, and `While bypass
  permissions mode is active:` in `opus-5/bypass-permissions` over a
  byte-identical body — then a paragraph steering work to Bash rather than
  Read/Edit/Write. opus-5's is the blunt form ("Fall back to a dedicated tool
  only when Bash genuinely cannot do the job"); opus-5-5's is softer ("The
  choice is yours: prefer Edit or Write when a shell edit would be fragile").
- **Neither**: fable-5, opus-4-8, sonnet-5-5.

Why the body splits three ways when the request's own
`classifier_context.permission_mode` reads `"auto"` in every capture that has
`safeguards` at all is untraced.

### Size

Measured over the full `messages[]` array minus the fixed 17-character canary
(`"say exactly: done"`, which appears once per request as the whole final text
block of `messages[0]`):

| | Opus 4.7 | Sonnet 5 | Opus 5 | Opus 5.5 | Sonnet 5.5 | Fable 5 | Opus 4.8 |
|---|---|---|---|---|---|---|---|
| 2.1.235 | 13,042 | 13,026 | 12,043 | - | - | - | - |
| 2.1.269 | 14,688 | 14,677 | 14,201 | - | - | 14,208 | 14,211 |
| 2.1.289 | 15,196 | 15,187 | 14,083 | 14,212 | 13,737 | 13,731 | 13,734 |

The full branch grew this release and the lean branch shrank: the `design`
skill and `TaskOutput` left the reminder bundle, `plugin-authoring` and the two
`Artifact*` names joined, and only the full branch's 949-char
`## Auto Mode Active` outweighs the loss. Size tracks the user's installed
skills and agents, so it is not comparable across machines
(`notes/cc-2.1.269-messages-and-reminders.md` itemizes the 2.1.269 bundle).

## API parameters

```jsonc
{
  "model": "claude-sonnet-5",
  "max_tokens": 64000,                        // 128000 on opus-5-5, sonnet-5-5
  "stream": true,
  "thinking": {"type": "adaptive", "display": "updates"},
  "output_config": {"effort": "high"},        // xhigh opus-4-7; medium opus-5-5, sonnet-5-5
  "context_management": {"edits": [{"type": "clear_thinking_20251015", "keep": "all"}]},
  "diagnostics": {"previous_message_id": null},
  "thread": {"type": "create"},
  "safeguards": [{"type": "dangerous_tool_use", "classifier_context": {...}}]   // NEW
}
```

Identical in every capture but those values; `max_tokens` is the first field in
this tree to vary by model, `effort` already did. No `betas` key on any model
and no `fallbacks` — 2.1.235 had `[{"model": "claude-opus-4-8"}]` on opus-5,
opus-4-7 never had one. A continuation request carries `thread:
{"type":"continue", ...}` and a non-null `diagnostics.previous_message_id`
instead. The per-version table and the billing-header fields:
`notes/cc-2.1.269-request-parameters.md`.

`safeguards` is new in 2.1.289 and is the first request field carrying machine
state rather than prompt: one `dangerous_tool_use` entry whose
`classifier_context` holds `permission_mode`, `platform`, `live_cwd`,
`home_dir`, an 11-key `rule_roots` map, `trusted_directories`, `rules`
(`allow`/`deny`/`ask`), `auto_mode`, `artifact_consent_holdback`,
`case_insensitive_paths`, `restricted`, `is_remote_mode`, `classify_all_shell`,
`git_state`, a 20-key `artifacts.session` feature map, and `user_identity`.
`opus-5/bypass-permissions` has no `safeguards` key at all (12 top-level keys),
so it is emitted only where a permission classifier is in play. Subagents get
their own: the Explore child's denies `ArtifactComments`, `ArtifactData` and
`ArtifactCheck` (each `"source": "session"`, and the only mention of
`ArtifactCheck` anywhere in the tree) and has no `artifacts` key, where
general-purpose's does.

### What a continuation request carries

The two `tool-search-loaded` captures are turn-2 requests — `thread:
{"type":"continue", "previous_message_id": ...}` — and carry **one**
system block, the billing header: 148 tokens on sonnet-5 and 146 on
opus-5, against 9,161 and 3,669 on turn 1, with no `messages[1]`
reminder bundle either. That is a client-side trim, not lost context.
Under growthbook `tengu_quiet_heron` (`BWo()`, `return
!Bs().threadInheritedFields.breakerTripped && A("tengu_quiet_heron", !1)
=== !0;`, `src/chunk-wgfrtm7w.js:82463-82465`, coded default false,
served on 2026-10-06) `shapeInheritedFields` (`ao`,
`src/chunk-wgfrtm7w.js:82623-82650`) keeps only the blocks `gB()`
accepts — text starting `x-anthropic-billing-header:`, or equal to the
`# Reporting outcomes` ephemeral suffix
(`src/chunk-898k2gs2.js:2256-2267`) — and omits `tools` entirely when
`threadInheritedFields.storedToolsHashByThread` already matches
(`:82640`); the thread holds the rest, and resends only new messages. A
server `fingerprint_mismatch` trips a breaker and full fields go for the
remainder of the session (`:82771-82776`, log line `[tether] a continue
that left system/tools to the thread was refused`). So the text the
model has on turn 2 is the turn-1 text, and `tools[]` is still the whole
roster.

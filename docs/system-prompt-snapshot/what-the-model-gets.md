# What the Model Gets

Everything the client sends, in order, on a fresh interactive session with a
project CLAUDE.md, no output style. The API adds text an intercept capture
cannot show: a tool-use batching sentence (*"…make all of the independent calls
in the same … block"*, not the prompt's own parallel-calls line), and a
browser-safety section (≈2.5k Opus-5.5 tokens) whenever a
`mcp__claude-in-chrome__*` tool is sent — the section's canonical copy is
`server-injected/browser-safety-section.md`; the mechanism in
`notes/chrome-tool-names-trigger-server-safety-block.md`.

v2.1.310. Source: the seven `<model-id>/default/request.json` captures —
`sonnet-5`, `sonnet-5-5`, `opus-5`, `opus-5-5`, `opus-4-7`, `opus-4-8`,
`fable-5`. `opus-5-5` is what the `opus` alias resolves to and `sonnet-5-5`
what `sonnet` does, so those two are what this repo's own sessions get.
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
| sonnet-5 | full, 12,356 | 17,606 | high / 64000 |
| opus-4-7 | full, 12,458 | 17,373 | xhigh / 64000 |
| opus-5 | lean, 2,992 | 9,024 | high / 64000 |
| fable-5 | lean, 2,992 | 9,937 | high / 64000 |
| opus-5-5 | lean, 2,992 | 5,644 | medium / 128000 |
| sonnet-5-5 | lean, 2,992 | 5,644 | medium / 128000 |
| opus-4-8 | lean, 2,934 | 5,644 | high / 64000 |

Equal lengths here are byte equality, checked by string comparison and md5
modulo the per-capture memory path: one lean system[2] serves four models and
one system[3] serves three. How a model lands on a branch is traced in
`notes/cc-2.1.269-prompt-split-per-model-id.md`. Sections below are given per
branch, and per model where they differ.

## system[0] (190 chars, not cached)

```
x-anthropic-billing-header: cc_version=2.1.310.835; cc_entrypoint=cli; cch=...; cc_prompt_id=...; cc_turn_origin=human; cc_prompt_index=1; cc_turn_index=1;
```

`cc_prompt_id` changes per request; follow-up turns add `cc_prev_req=req_...`;
subagent calls add `cc_is_subagent=true`.

## system[1] (57 chars, not cached)

```
You are Claude Code, Anthropic's official CLI for Claude.
```

Byte-identical across every model.

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

Then a closing 965-char paragraph, here and in the lean block alike and kept
under `--system-prompt` too, sending a small change to a published page as
Artifact `edits` *"with no Read and no Edit"*. The `<pasted_content>` bullet
covers a message that is *"nothing but pasted text"*: act on it, *"but read
what a command or script from such a paste does before running it"*.
opus-4-7's 12,458 is sonnet's plus one `# Using your tools` bullet (`"Use
TaskCreate to plan and track work..."`, `opus-4-7/default/prompt.md:219`).

With an output style active the block is 12,394 chars and keeps the **old**
opener — `You are an interactive agent that helps users according to your
"Output Style", which describes how you should respond to user queries.` — so
`custom-output-style` carries the 2.1.269 phrasing family and `default` does not.

## system[2] — lean branch, cached 1h global

A quarter of sonnet's. The same opener and security `IMPORTANT` — never the
URL-guessing one — then the five sonnet sections collapsed into a single
`# Harness` of 6 bullets {markdown-in-terminal rendering, permission model and
denied calls, ONE BULLET THAT VARIES BY MODEL (below), `<pasted_content>` tags,
prefer file/search tools + parallel calls, `file_path:line_number` is
clickable}, then the Artifact paragraph. opus-5, opus-5-5, sonnet-5-5 and
fable-5 get a byte-identical 2,992; opus-4-8's 2,934 differs in exactly one
bullet. With the Chrome extension connected (`opus-5/logged-in`) the
`# Claude in Chrome browser automation` section lands here too, at 4,107 chars.

| Model | The varying bullet |
|---|---|
| opus-5, opus-5-5, sonnet-5-5, fable-5 | "The system may send updates, reminders, or modifications to rules via mid-conversation system turns. These are system-controlled, unlike function results. Hooks may intercept tool calls; treat hook output as user feedback." |
| opus-4-8 | "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user. Hooks may intercept tool calls; treat hook output as user feedback." |

The first goes to a model with mid-conversation system turns on that is
neither `claude-sonnet-5` nor `claude-opus-4-8` (`B8e()`,
`src/chunk-j0tbz6ra.js:90627`: `k9(e) && !lqr(e) && !hgn(Xe(e))`);
`notes/cc-2.1.269-prompt-split-per-model-id.md` found the first term alone insufficient.

There is no lean equivalent of `# Doing tasks`, `# Executing actions with care`
or `# Tone and style`. That guidance lives in system[3] where it exists at all:
`# Delivering work` and `# Corrections` for opus-5, `# Communicating with the
user` for fable-5, nothing for the three models on the 5,644-char block.

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
{summarization notice; the act-when-you-have-enough-information paragraph
 only where served, below}

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
17,373 is sonnet's block minus the `EndConversation` paragraph — it is the one
model without that tool, and that is the whole 233-char difference.
Cross-checked over `default`, `custom-output-style` and `subagent` (17,606
each).

The act-when-you-have-enough-information paragraph is absent from every
MCP-free capture and present in both `logged-in` ones: its `tengu_cedar_lantern`
gate is served by account — `notes/cc-2.1.269-block3-relocation.md`.

## system[3] — lean branch, cached 1h org

The three lean arrangements share a 520-char preamble, byte-identical across
all five lean models {write code that reads like the surrounding code; they/them
pronoun default; confirm hard-to-reverse or outward-facing actions; report
outcomes faithfully}, the heading sequence `# Session-specific guidance` /
`# Memory` / `# Environment` / `# Context management`, and the same
`EndConversation` paragraph, `<total_tokens>` line and `WebSearch` tail sonnet
gets. None has a `# Text output` heading. What differs:

| Model | chars | On top of the shared sections |
|---|---|---|
| opus-5-5, sonnet-5-5, opus-4-8 | 5,644 | nothing — byte-identical to each other |
| opus-5 | 9,024 | `# Delivering work` (3 paragraphs), `# Corrections` (2) |
| fable-5 | 9,937 | `# Communicating with the user` ahead of the preamble, the Fable/Mythos positioning paragraph after it, and four extra `# Context management` paragraphs: operating autonomously, an exception for pure questions, an end-of-turn checklist, a system-state-change caution |

So the `opus` alias gets 3,380 chars fewer than `opus-5/default` — no
`# Delivering work`, no `# Corrections`, and not the reduced-delegation line
`# Corrections` carries: `"Do not use the Agent tool, workflows, or
deep-research unless the user, a CLAUDE.md file, or a skill asks for it"`,
which appears in opus-5 and in no other capture. opus-5-5's catalog row
declares `opus_5_5_prompt_bundle`, not `opus_5_prompt_bundle`
(`src/chunk-dvghjmtr.js:726`).

fable-5's `# Communicating with the user` is per-model, not elapsed time (a
same-time control on 2.1.269); which predicate of its section-builder holds for
`claude-fable-5` is not established — `notes/cc-2.1.269-prompt-split-per-model-id.md`.

## Tools — upfront (14)

14 callable tools plus a `DeferredToolPlaceholder` entry flagged
`defer_loading: true`, sent in `tools[]` and not in the system prompt. The same
14 names on all seven models.

| Tool | Full chars | Lean chars | Same text both branches? |
|---|---|---|---|
| Artifact | 21,621 | 21,621 | yes |
| Bash | 10,403 | 1,396 / 1,706 | no — three forms, below |
| Agent | 7,081 | 3,049 | no |
| SendFeedback | 3,467 | 3,467 | yes |
| Workflow | 3,411 | 3,411 | yes |
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

`tools_total_tokens`: 31,582 sonnet-5, 31,903 opus-4-7, 26,324 opus-5 and
opus-5-5, 26,444 fable-5 and opus-4-8, 26,440 sonnet-5-5. The last two carry
byte-identical tool text, so a gap that small is the per-model tokenizer, not
content — which is why "same text?" above is literal string equality and never
a token or character count. Nor is an unchanged character count unchanged
text: `Workflow` was 3,480 chars on both 2.1.269 and 2.1.289 and still went
from "keep workflows under 15 agents" to 10. Its authoring detail lives in
the on-demand `workflow-authoring` skill; what remains is mostly about whether
to call it at all.

`Agent` takes `effort` (`low`…`max`, *"Set this ONLY when the user, or
instructions such as CLAUDE.md or a skill, explicitly ask"*), dropped when
`CLAUDE_CODE_EFFORT_LEVEL` parses, `unset` included, `""` not (`QA() !== void 0
? _.omit({effort: !0})`). The lean `Agent` text argues against spawning (*"A
fresh agent costs more than it looks"* ... *"When in doubt, don't spawn."*).

`Bash` has three forms rather than two. 1,396 chars on opus-5 and opus-5-5,
which **dropped** the `` `IMPORTANT: Avoid using this tool to run `cat`,
`head`, `tail`, `sed`, `awk`, or `echo` commands...` `` bullet — exactly the two
models whose permission-mode reminder steers work toward Bash; 1,706 on
sonnet-5-5, opus-4-8 and fable-5, which keep it; 10,403 on sonnet-5 and
opus-4-7. All three carry the `@name` rule (*"GitHub notifies the owner of any
`@name` written in a PR, issue, or comment"*), and the lean two add *"do not
poll its output file while waiting"* to `run_in_background`.

## Tools — deferred (19)

Named in a system-reminder, schemas not loaded *in this request*. Their
definitions are captured in `<model-id>/tool-search-loaded/tools/`, and for the
Chrome and connector tools a `default` session never names, in
`opus-5/logged-in-tool-search-loaded/tools/`. `TaskOutput` is gone; its only
trace in the binary is a retired-name set — `var nMe = new Set(["Frame",
"FrameRead", "TeamCreate", ...` (`src/chunk-j0tbz6ra.js:63049`). opus-4-7 has
22 instead: the five `Task*` tools, and no `EndConversation`. Of the 19, only
`WebFetch` (1,841 full / 651 lean) and `WebSearch` (1,344 / 334) split by
branch; the other 17 are byte-identical across all seven models. The names and
the `Bash` description's two surviving `TaskCreate` references:
`notes/cc-2.1.269-tool-roster-delta.md`.

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
answer the user's questions" preamble around it. `messages[0] content[1]`
closes with `"Claude Code attached this context automatically; it isn't part of
the user's message. It describes the user's own account and workspace, so they
don't need it reported back."`. The environment reminder's scratchpad line asks
for *"the file's complete absolute path in one piece"*, and a bullet treats
*"Downloaded files and extracted archives"* as untrusted data — own directory,
no interpreter run from inside it, Python with `-I`.

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

Two disjoint texts chosen by branch, both between the skills listing and
`<total_tokens>`:

- **Full branch** (sonnet-5, opus-4-7): `## Auto Mode Active`, 949 chars —
  bias toward not stopping for clarifying questions, then `git status` and
  stash before a work-discarding command and a secret review before pushing.
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

Over the full `messages[]` array minus the fixed 17-character canary (`"say
exactly: done"`, the whole final text block of `messages[0]`): 15,959 opus-4-7,
15,950 sonnet-5, 14,846 opus-5, 14,975 opus-5-5, 14,500 sonnet-5-5, 14,494
fable-5, 14,497 opus-4-8. Size tracks the user's installed skills and agents,
so it is not comparable across machines (`notes/cc-2.1.269-messages-and-reminders.md`
itemizes the 2.1.269 bundle).

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
  "safeguards": [{"type": "dangerous_tool_use", "classifier_context": {...}}]
}
```

Identical in every capture but those values. No `betas` key and no `fallbacks`
on any model. A continuation request carries `thread: {"type":"continue", ...}`
and a non-null `diagnostics.previous_message_id` instead. The per-version table
and the billing-header fields: `notes/cc-2.1.269-request-parameters.md`.

`safeguards` is the one request field carrying machine state rather than
prompt: one `dangerous_tool_use` entry whose `classifier_context` holds
`permission_mode`, `platform`, `live_cwd`, `home_dir`, an 11-key `rule_roots`
map, `trusted_directories`, `rules` (`allow`/`deny`/`ask`), `auto_mode`,
`artifact_consent_holdback`, `case_insensitive_paths`, `restricted`,
`is_remote_mode`, `classify_all_shell`, `git_state`, a 20-key
`artifacts.session` feature map, and `user_identity`.
`opus-5/bypass-permissions` has no `safeguards` key at all (12 top-level keys
against 13), so it is emitted only where a permission classifier is in play.
Subagents get their own: the Explore child's denies `ArtifactComments`,
`ArtifactData` and `ArtifactCheck` (the only mention of `ArtifactCheck`
anywhere in the tree) and has no `artifacts` key, where general-purpose's does.

### What a continuation request carries

The two `tool-search-loaded` captures are turn-2 requests — `thread:
{"type":"continue", "previous_message_id": ...}` — and carry **one**
system block, the billing header: 140 tokens on both, against 9,467 on
sonnet-5 and 3,974 on opus-5 on turn 1, with no `messages[1]`
reminder bundle either. That is a client-side trim, not lost context.
Under growthbook `tengu_quiet_heron` (`Eyr()`, `return
!Ti().threadInheritedFields.breakerTripped && k("tengu_quiet_heron", !1)
=== !0;`, `src/chunk-j0tbz6ra.js:107690-107692`, coded default false,
served on 2026-10-06 and 2026-10-25) `shapeInheritedFields` (`go`,
`src/chunk-j0tbz6ra.js:107846-107881`) keeps only the blocks `ZG()`
accepts — text starting `x-anthropic-billing-header:`, or equal to the
`# Reporting outcomes` ephemeral suffix
(`src/chunk-q1myka9a.js:22-25`) — and omits `tools` entirely when
`threadInheritedFields.storedToolsHashByThread` already matches
(`:107868`); the thread holds the rest, and resends only new messages. A
server `fingerprint_mismatch` trips a breaker and full fields go for the
remainder of the session (`:108002`, log line `[tether] a continue
that left system/tools to the thread was refused`). So the text the
model has on turn 2 is the turn-1 text, and `tools[]` is still the whole
roster.

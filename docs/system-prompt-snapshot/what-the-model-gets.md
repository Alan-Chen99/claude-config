# What the Model Gets

Everything the model receives, in order, on a fresh interactive session with a
project CLAUDE.md, no output style.

v2.1.235. Source: `sonnet-5/default/request.json`, `opus-5/default/request.json`.
A third capture, `opus-4-7/default/`, sits on the other side of the prompt
branch; see README.md, "The prompt split is per model id, not per model family".
Capture uses `--setting-sources project,local` to isolate from user settings.

**Sonnet 5 and Opus 5 do not receive the same prompt.** Through 2.1.143 the two
models got byte-identical text and differed only in tokenizer. In 2.1.235 the
tokenizers agree and the *text* diverges: opus-5 gets a compressed harness
prompt and shorter descriptions for the core tools, while opus-4-7 gets the same
long prompt sonnet does. Every section below is therefore
given per model.

Token counts from the Anthropic count_tokens API (exact).

## system[0] (sonnet 83 / opus 86 tokens, not cached)

```
x-anthropic-billing-header: cc_version=2.1.235.cf9; cc_entrypoint=cli; cch=00000; cc_prompt_id=00000000-0000-0000-0000-000000000000;
```

`cc_prompt_id` is new in 2.1.235. Follow-up turns add `cc_prev_req=req_...`;
subagent calls add `cc_is_subagent=true`. All of these change per request, so
the header is not stable across captures.

## system[1] (sonnet 24 / opus 24 tokens, not cached)

```
You are Claude Code, Anthropic's official CLI for Claude.
```

Identical text, identical count — the ~38% opus tokenizer inflation seen with
`claude-opus-4-7` vs `claude-sonnet-4-6` is gone.

## system[2] — sonnet (3,247 tokens, cached 1h global)

Static behavioral rules, 10,574 chars. Cross-org cacheable (`scope: global`).

```
You are an interactive agent that helps users with software engineering tasks...

{preamble changes when output style is active:
 - default: "...helps users with software engineering tasks..."
 - with output style: "...according to your 'Output Style' below..."}

IMPORTANT: {security policy}
IMPORTANT: {URL policy — NEVER generate or guess URLs}

# System                        [1,615 ch, 6 bullets]
{output rendering, permission model, system-reminder tags, prompt injection,
hooks, context compression}

# Doing tasks                   [3,304 ch, 14 bullets]
{software engineering framing, defer to user judgement, 2-3 sentence response
for exploratory questions, prefer editing existing files, OWASP security,
no extras/abstractions, no speculative error handling, no comments by default,
no WHAT comments, dev server for UI changes, no backwards-compat hacks,
/help link}

# Executing actions with care   [3,552 ch, 4 bullets]
{reversibility/blast radius policy, 4 categories of risky actions,
investigate before destroying, prefer reversible steps over deletion,
git status before work-discarding commands, secret review before pushing}

# Using your tools              [628 ch, 2 bullets]
{prefer dedicated tools over Bash, parallel calls when independent}

# Tone and style                [537 ch, 4 bullets]
{no emojis, concise, file_path:line_number references, no colon before
tool calls}
```

Changed from 2.1.143:

- `# Executing actions with care` gained the reversibility preference
  (move/rename/stash over delete), a carve-out for self-created scratch files,
  a mandatory `git status` before work-discarding git commands, and a
  secret-review step before pushing.
- `# Using your tools` lost `Use TaskCreate to plan and track work`, dropping
  from 3 bullets to 2. The task tools were removed in the same release.

## system[2] — opus (393 tokens, cached 1h global)

1,210 chars — an eighth of sonnet's. The five sonnet sections collapse into one:

```
You are an interactive agent that helps users with software engineering tasks.

IMPORTANT: {security policy — identical wording to sonnet}

# Harness                       [5 bullets]
{markdown-in-terminal rendering, permission model and denied calls,
mid-conversation system turns and hooks, prefer file/search tools + parallel
calls, file_path:line_number is clickable}
```

There is no opus equivalent of `# Doing tasks`, `# Executing actions with
care`, or `# Tone and style` in this block; the surviving guidance moves to
`# Delivering work` and `# Corrections` in system[3].

## system[3] — sonnet (6,013 tokens, cached 1h org)

18,812 chars.

```
# Text output (does not apply to tool calls)      [1,654 ch]
{narrate before first tool call, short updates at key moments, no internal
deliberation, end-of-turn summary, no comments in code by default}

{they/them default for unstated pronouns — NEW in 2.1.235, applies to
 visible thinking too}

# Session-specific guidance                       [1,384 ch, 4 bullets]
{`!` prefix for user-run commands, subagent_type "fork", /<skill-name>,
/code-review ultra}

# auto memory                                     [663 ch + 6 subsections]
{memory dir path, then:
 ## Types of memory                 [7,195 ch]
 ## What NOT to save in memory      [686 ch, 5 bullets]
 ## How to save memories            [1,505 ch, 9 bullets]
 ## When to access memories         [770 ch, 4 bullets]
 ## Before recommending from memory [679 ch, 3 bullets]
 ## Memory and other forms of persistence [1,112 ch, 2 bullets]}

# Environment                                     [958 ch, 10 bullets]
{cwd, is-git-repo, platform, shell, OS version, model name + id,
knowledge cutoff, model family + ids, surfaces, fast mode}

# Scratchpad Directory                            [718 ch, 5 bullets]  NEW
{/tmp/claude-0/<project-slug>/<session-id>/scratchpad — use instead of /tmp}

# Context management                              [1,135 ch]
{summarization notice, act-when-you-have-enough-information, EndConversation
usage note, <total_tokens>N tokens left</total_tokens>}

gitStatus: {branch, main branch, git user, status, recent commits}
```

Changed from 2.1.143:

- **New**: they/them pronoun default, `# Scratchpad Directory`, the
  act-when-you-have-enough-information paragraph, the `EndConversation` note,
  and the `<total_tokens>` budget line.
- `# Session-specific guidance` was rewritten around `subagent_type: "fork"`;
  the Explore-for-broad-exploration bullet and the `/schedule` offer policy
  paragraph are gone. `/ultrareview` is now described as a deprecated alias
  for `/code-review ultra`.
- `# Environment` reports Sonnet 5 / `claude-sonnet-5`, knowledge cutoff
  January 2026, and the Claude 5 family ids (Fable 5, Opus 5, Sonnet 5,
  Haiku 4.5).

## system[3] — opus (3,365 tokens, cached 1h org)

10,231 chars. Different sections, not a subset.

```
{preamble, 975 ch: write code that reads like the surrounding code;
 they/them pronoun default; confirm hard-to-reverse or outward-facing
 actions; report outcomes faithfully}

# Session-specific guidance   [892 ch, 3 bullets]
# Memory                      [2,063 ch, 2 bullets]   (vs sonnet's ~12,600 ch
                                                       "# auto memory" tree)
# Environment                 [950 ch, 10 bullets]
# Scratchpad Directory        [718 ch, 5 bullets]     (identical to sonnet)
# Context management          [538 ch]
# Delivering work             [1,999 ch]              opus only
# Corrections                 [1,951 ch]              opus only

gitStatus: {...}
```

Opus has no `# Text output` block. `# Delivering work` (act on the actual
request, requested scope is the deliverable) and `# Corrections` (do not
over-correct earlier statements) carry guidance that sonnet gets inside
`# Doing tasks` and `# Text output`.

## Tools — upfront

13 callable tools plus a `DeferredToolPlaceholder` entry flagged
`defer_loading: true`. Sent in `tools[]`, not in the system prompt.

| Tool | Sonnet tokens | Opus tokens | Description identical? |
|---|---|---|---|
| Workflow | 8,254 | 8,186 | yes |
| Artifact | 6,922 | 6,854 | yes |
| Bash | 4,484 | 1,237 | **no** — 10,067 vs 1,043 chars |
| Agent | 3,213 | 1,295 | **no** — 7,081 vs 1,811 chars |
| ScheduleWakeup | 2,049 | 1,981 | yes |
| AskUserQuestion | 1,961 | 1,968 | **no** — 1,531 vs 1,786 chars |
| Read | 1,260 | 894 | **no** — 1,782 vs 790 chars |
| ReportFindings | 1,175 | 1,107 | yes |
| Skill | 977 | 909 | yes |
| Edit | 933 | 634 | **no** — 1,094 vs 360 chars |
| ToolSearch | 889 | 821 | yes |
| ListAgents | 751 | 683 | yes |
| Write | 714 | 522 | **no** — 618 vs 240 chars |
| DeferredToolPlaceholder | 432 | 364 | yes |
| **total in request** | **29,427** | **23,752** | |

Every tool that predates 2.1.235 has a shortened opus description; every tool
introduced in it is byte-identical across models. `AskUserQuestion` is the
lone tool whose opus description is longer.

Against 2.1.143: **added** `Artifact`, `ListAgents`, `ReportFindings`,
`Workflow`; **removed** `ShareOnboardingGuide`. The upfront tool payload went
from 10,559 to 29,427 sonnet tokens, most of it `Workflow` and `Artifact`.

`DeferredToolPlaceholder` is new: a single stub carrying `defer_loading: true`.
In 2.1.143 each deferred tool appeared in `tools[]` with its own
`defer_loading` flag. One practical consequence: `count_tokens` rejects a
request in which every tool is deferred, so the placeholder must be measured
with the flag stripped.

## Tools — deferred (18)

Named in a system-reminder, schemas not loaded:

```
CronCreate, CronDelete, CronList, DesignSync, EndConversation, EnterPlanMode,
EnterWorktree, ExitPlanMode, ExitWorktree, Monitor, NotebookEdit,
PushNotification, RemoteTrigger, SendMessage, TaskOutput, TaskStop, WebFetch,
WebSearch
```

Against 2.1.143: **added** `DesignSync`, `EndConversation`, `SendMessage`;
**removed** `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate`. MCP tools
(`mcp__claude_ai_Google_Drive__*` in the 2.1.143 capture) depend on the
capturing account's connectors, not the CLI version, and are absent here.

The Bash tool description still says `NEVER use the TaskCreate or Agent tools`
in its git-commit examples — a reference to a tool that exists in neither list.

## messages structure (changed in 2.1.235)

```
messages[0]  role: user
  [0] text   <system-reminder> claudeMd + userEmail + currentDate </system-reminder>
  [1] text   the actual human input

messages[1]  role: system                              NEW in 2.1.235
  [0] text   <system-reminder> deferred tools </system-reminder>
             <system-reminder> available agent types </system-reminder>
             <system-reminder> available skills </system-reminder>
             <system-reminder> ## Auto Mode Active </system-reminder>
             <system-reminder> <total_tokens>N tokens left</total_tokens> </system-reminder>
```

In 2.1.143 all of these were content blocks inside `messages[0]`, ahead of the
human input. They now live in a dedicated `system`-role message placed *after*
it.

Shape caveats when parsing:

- `messages[1].content` is a **list of blocks** on the first turn and a **bare
  string** on later turns. Both occur in one session.
- Every reminder shares a single text block. Sonnet wraps each in
  `<system-reminder>` tags; opus emits them bare, separated by blank lines.
  Neither delimiter is dependable — bound the deferred-tool listing by shape
  (one bare identifier per line under the intro sentence) instead.
- `## Auto Mode Active` appears only when the session runs in auto mode, which
  is the interactive default in 2.1.235. Setting
  `permissions.defaultMode: "default"` removes both the TUI indicator and the
  reminder; the other reminders are unaffected. It is also absent from a `-p`
  capture.

The system-role message costs 4,300 tokens (sonnet) / 3,958 (opus) in this
capture. Its size tracks the user's installed skills and agents, so it is not
comparable across machines.

## API parameters

```jsonc
// Sonnet
{
  "model": "claude-sonnet-5",
  "max_tokens": 64000,                                     // was 32000
  "stream": true,
  "thinking": {"type": "adaptive"},
  "output_config": {"effort": "max"},
  "context_management": {"edits": [{"type": "clear_thinking_20251015", "keep": "all"}]},
  "diagnostics": {"previous_message_id": null}
}

// Opus — same, plus:
{
  "model": "claude-opus-5",
  "max_tokens": 64000,                                     // unchanged
  "fallbacks": [{"model": "claude-opus-4-8"}]              // NEW
}
```

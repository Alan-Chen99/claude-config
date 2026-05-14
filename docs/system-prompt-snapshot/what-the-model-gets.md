# What the Model Gets

Everything the model receives, in order, on a fresh interactive session with a project CLAUDE.md, no output style.
v2.1.87. Source: `opus/default/request.json`, `sonnet/default/request.json`.
Capture uses `--setting-sources project,local` to isolate from user settings.
Sonnet and Opus receive identical system prompt text except model name, knowledge cutoff, and agent type ordering in the Agent tool description.

Token counts are approximate: tiktoken cl100k_base scaled by 1.17x (median factor across 46 Claude Code sessions with >5K chars of system prompt text).

## system[0] (~39 tokens, not cached)

```
x-anthropic-billing-header: cc_version=2.1.87.7b6; cc_entrypoint=cli; cch=00000;
```

## system[1] (~15 tokens, not cached)

```
You are Claude Code, Anthropic's official CLI for Claude.
```

## system[2] (~3,100 tokens, cached global+1h)

Static behavioral rules. Cross-org cacheable (scope: global).

```
You are an interactive agent that helps users with software engineering tasks...

{preamble changes when output style is active:
 - default: "...helps users with software engineering tasks..."
 - with output style: "...according to your 'Output Style' below..."}

IMPORTANT: {security policy}
IMPORTANT: {URL policy — NEVER generate or guess URLs}

# System
{7 bullets: output rendering, permissions, ! prefix for interactive commands,
system-reminder tags, prompt injection, hooks, compression}

# Doing tasks
{12 bullets: software engineering framing, defer to user judgement, read before modify,
avoid file bloat, no time estimates, diagnose before switching tactics,
OWASP security, no extras beyond what was asked, no speculative error handling,
no premature abstractions, no backwards-compat hacks, /help link}

{kept even when output style is active — no longer removed}

# Executing actions with care
{reversibility/blast radius policy, 4 categories of risky actions, investigate before destroying}

# Using your tools
Do NOT use Bash when a dedicated tool is provided — CRITICAL
{Read not cat, Edit not sed, Write not echo, Glob not find, Grep not grep}
{TaskCreate for work tracking, Agent for exploration, Skill for slash commands,
parallel calls when independent}

# Tone and style
{no emojis, concise, file_path:line_number references, owner/repo#123 for GH links,
no colon before tool calls}

# Output efficiency
IMPORTANT: Go straight to the point. Try the simplest approach first. Be extra concise.
{lead with answer not reasoning, focus on decisions/milestones/errors, one sentence over three}
```

## system[3] (~3,540 tokens, not cached)

Dynamic sections. Recomputed per session, not globally cached.
Opus: ~3,540 tokens. Sonnet: ~3,550 tokens (path and model name differ).

```
# auto memory
{memory system path and write instructions}
## Types of memory
{user, feedback, project, reference — XML definitions with examples for each}
## What NOT to save in memory
## How to save memories
## When to access memories
{MUST access memory when user explicitly asks}
## Before recommending from memory
## Memory and other forms of persistence

# Environment
 - Primary working directory, git repo, platform, shell, OS
 - Model name: "Opus 4.6" / "claude-opus-4-6" (or Sonnet 4.6 / claude-sonnet-4-6)
 - Knowledge cutoff: Opus May 2025, Sonnet August 2025
 - Model family IDs, fast mode info, Claude Code availability

# Output Style: <name>                                ← only present when output style is set
{full output style markdown content}

gitStatus: This is the git status at the start of the conversation...
Current branch: main
Main branch (you will usually use this for PRs): main
Status: {modified/untracked files}
Recent commits: {last 5 commits}
```

Note: auto memory section only appears when `autoMemoryEnabled` is true (the default).
The capture uses `--setting-sources project,local` to avoid inheriting the user's
global settings, which ensures defaults apply.

## tool desc (Agent, ~1,580 desc + ~300 schema tokens)

```
Agent: Launch a new agent to handle complex, multi-step tasks autonomously.

Available agent types and the tools they have access to:
{11 types: general-purpose(*), statusline-setup(Read,Edit), Explore, Plan,
claude-code-guide, prose-humanizer, quality-reviewer, debugger,
technical-writer, developer, architect}

When NOT to use the Agent tool:
{specific file → Read/Glob, class definition → Glob, 2-3 known files → Read}

Usage notes:
{3-5 word description, concurrent launches, result not visible to user,
background vs foreground, SendMessage continuation, tell agent code vs research,
proactive use, worktree isolation}

Example usage:
{2 examples: test-runner after writing code, greeting-responder}

{input_schema: prompt, description, subagent_type, model, run_in_background, isolation}
```

## tool desc (Bash, ~2,620 desc + ~430 schema tokens)

```
Bash: Executes a given bash command and returns its output.
IMPORTANT: avoid find/grep/cat/sed/awk — use Glob/Grep/Read/Edit/Write instead

# Instructions
{verify parent dirs, quote paths, absolute paths, timeout up to 600s,
run_in_background, description style, multiple commands (parallel vs &&),
git: prefer new commits, no destructive ops, never skip hooks, no sleep}

# Committing changes with git
Git Safety Protocol:
  NEVER update git config
  NEVER destructive commands unless user requests
  NEVER skip hooks (--no-verify, --no-gpg-sign)
  NEVER force push main/master
  CRITICAL: always NEW commits not amend — hook failure means commit didn't happen
  NEVER commit unless user explicitly asks — VERY IMPORTANT
{4-step workflow: status+diff+log → analyze+draft → stage+commit+verify → fix hooks}
IMPORTANT: never -i flag (interactive not supported)
IMPORTANT: no --no-edit with rebase
ALWAYS pass commit message via HEREDOC

# Creating pull requests
IMPORTANT: follow steps carefully
{3-step workflow: status+diff+log+diff-from-base → analyze ALL commits+draft → branch+push+gh-pr-create}

# Other common operations
{gh api for PR comments}

{input_schema: command, description, timeout, run_in_background, dangerouslyDisableSandbox}
```

## tool desc (Edit, ~260 desc + ~170 schema tokens)

```
Edit: Performs exact string replacements in files.

Usage:
MUST Read file first — errors if not.
ALWAYS prefer editing existing files. NEVER write new files unless required.
{preserve indentation from Read output, old_string must be unique or use replace_all,
replace_all for renaming}

{input_schema: file_path, old_string, new_string, replace_all}
```

## tool desc (Glob, ~90 desc + ~160 schema tokens)

```
Glob: Fast file pattern matching tool that works with any codebase size.
{glob patterns, sorted by mtime, use Agent for open-ended search}
{input_schema: pattern, path}
```

## tool desc (Grep, ~260 desc + ~740 schema tokens)

```
Grep: A powerful search tool built on ripgrep.

Usage:
ALWAYS use Grep for search. NEVER invoke grep/rg as Bash command.
{full regex, glob/type filtering, 3 output modes (content/files_with_matches/count),
ripgrep brace escaping, multiline mode}

{input_schema: pattern, path, glob, type, output_mode, -A, -B, -C, -i, -n, multiline, head_limit, offset}
```

## tool desc (Read, ~430 desc + ~210 schema tokens)

```
Read: Reads a file from the local filesystem.

Usage:
{absolute paths, default 2000 lines, read only needed part, cat -n format,
images (multimodal), PDFs (MUST use pages param for >10 pages, max 20),
Jupyter notebooks, files only not dirs}
ALWAYS read screenshots when user provides path.

{input_schema: file_path, offset, limit, pages}
```

## tool desc (Skill, ~340 desc + ~110 schema tokens)

```
Skill: Execute a skill within the main conversation.

How to invoke:
{skill name + optional args, fully qualified names}

Important:
BLOCKING REQUIREMENT: invoke skill BEFORE generating any response about the task.
NEVER mention a skill without actually calling this tool.
{skills listed in system-reminder, don't invoke running skills,
not for built-in CLI commands, <command-name> tag = already loaded}

{input_schema: skill, args}
```

## tool desc (ToolSearch, ~250 desc + ~130 schema tokens)

```
ToolSearch: Fetches full schema definitions for deferred tools so they can be called.
{until fetched, only name known — no schema, cannot invoke}
{returns <function> JSON schema blocks}

Query forms:
{"select:Read,Edit" exact, "notebook jupyter" keyword, "+slack send" name+rank}

{input_schema: query, max_results}
```

## tool desc (Write, ~150 desc + ~110 schema tokens)

```
Write: Writes a file to the local filesystem.

Usage:
MUST Read first if file exists — errors if not.
{prefer Edit for modifications, overwrites existing}
NEVER create *.md or README unless explicitly requested.

{input_schema: file_path, content}
```

## messages[0] — deferred tools (~210 tokens, plain string)

Injected as the first user message. Plain string, not a content block list.

```
<available-deferred-tools>
AskUserQuestion
CronCreate
CronDelete
CronList
EnterPlanMode
EnterWorktree
ExitPlanMode
ExitWorktree
NotebookEdit
RemoteTrigger
TaskCreate
...
</available-deferred-tools>
```

30 deferred tools in this capture (includes MCP tools if configured).

## messages[1] — user context + input (content block list)

### block[0]: skills (~370 tokens)

```
<system-reminder>
The following skills are available for use with the Skill tool:

- update-config: ...
- keybindings-help: ...
- simplify: ...
{... built-in CC skills + project .claude/skills/ + plugins}
</system-reminder>
```

~370 tokens with default CC skills only. ~1,400+ tokens when user-level skills from
`~/.claude/skills/` are included (requires `user` in `--setting-sources`).

### block[1]: claudeMd + currentDate (~170 tokens)

```
<system-reminder>
As you answer the user's questions, you can use the following context:
# claudeMd
Codebase and user instructions are shown below. Be sure to adhere to
these instructions. IMPORTANT: These instructions OVERRIDE any default
behavior and you MUST follow them exactly as written.

Contents of {path}/CLAUDE.md (project instructions, checked into the codebase):

{full CLAUDE.md text}
# currentDate
Today's date is 2026-05-11.

      IMPORTANT: this context may or may not be relevant to your tasks.
      You should not respond to this context unless it is highly relevant
      to your task.
</system-reminder>
```

The `# claudeMd` section is absent when no CLAUDE.md exists in the project.
The `IMPORTANT: this context may or may not be relevant` caveat always appears
after the context sections.

### block[N]: actual human input (cached 1h)

```
{the user's message}
```

Last block has `cache_control: { type: "ephemeral", ttl: "1h" }`.

## API parameters

```json
// Opus
{
  "max_tokens": 64000,
  "thinking": { "type": "adaptive" },
  "context_management": { "edits": [{ "type": "clear_thinking_20251015", "keep": "all" }] },
  "output_config": { "effort": "max" },
  "metadata": { "user_id": "<redacted>" },
  "stream": true
}

// Sonnet
{
  "max_tokens": 32000,
  "thinking": { "type": "adaptive" },
  "context_management": { "edits": [{ "type": "clear_thinking_20251015", "keep": "all" }] },
  "output_config": { "effort": "high" },
  "metadata": { "user_id": "<redacted>" },
  "stream": true
}
```

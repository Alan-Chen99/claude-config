# What the Model Gets

Everything Claude receives on a fresh interactive session with only a CLAUDE.md.
Based on v2.1.79, captured via `capture.py --settings '{"outputStyle": ""}'`.

## API request: three top-level fields

```
POST /v1/messages
{
  "system": [ ...4 text blocks... ],      ← system prompt
  "tools":  [ ...25 tool definitions... ], ← tool schemas + descriptions
  "messages": [ ...1 user message... ]     ← injected context + user text
}
```

Total context before the model speaks: ~85K chars (~27K system + ~48K tools + ~10K user message).

---

## 1. system[] — System Prompt (4 text blocks, 27K chars)

### Block 0 — Billing header (80 chars)

Role: Internal accounting. Not behavioral.

```
x-anthropic-billing-header: cc_version=2.1.79.04b; cc_entrypoint=cli; cch=00000;
```

No cache_control.

### Block 1 — Identity (57 chars)

Role: Sets the persona. One sentence.

```
You are Claude Code, Anthropic's official CLI for Claude.
```

In `-p` (pipe) mode this changes to: `"You are a Claude agent, built on Anthropic's Claude Agent SDK."`

No cache_control.

### Block 2 — Behavioral rules (12.5K chars)

Role: Core behavioral instructions. How to act, what to avoid, how to use tools.
Cache: `ephemeral, ttl=1h, scope=global` (shared across sessions for 1 hour).

Markdown headers:

```
# System
  - output rendering (markdown, monospace)
  - permission mode / tool approval
  - system-reminder tags
  - prompt injection awareness
  - hooks
  - context compression

# Doing tasks
  - software engineering framing
  - read before modify
  - avoid file bloat
  - no time estimates
  - no brute-force retries
  - security (OWASP top 10)
  - avoid over-engineering (3 sub-bullets)
  - no backwards-compat hacks
  - /help and feedback link

# Executing actions with care
  - reversibility / blast radius
  - risky action examples (4 categories)
  - investigate before destroying

# Using your tools
  - dedicated tools over Bash (Read, Edit, Write, Glob, Grep)
  - Agent tool for exploration
  - Skill tool for slash commands
  - parallel tool calls

# Tone and style
  - no emojis unless asked
  - concise responses
  - file_path:line_number references
  - no colon before tool calls

# Output efficiency
  - lead with answer, not reasoning
  - focus on: decisions, milestones, errors
  - one sentence over three
```

When an **output style** is configured, it is appended here (adds `# Output Style: <name>` section).

### Block 3 — Memory + environment + gitStatus (14.4K chars)

Role: Session-specific context. Memory system, runtime environment, repo state.

No cache_control (changes per session/project).

Markdown headers:

```
# auto memory
  - memory path, write instructions
  ## Types of memory
    - user, feedback, project, reference (each with <type> XML)
  ## What NOT to save in memory
  ## How to save memories
  ## When to access memories
  ## Before recommending from memory
  ## Memory and other forms of persistence

# Environment
  - working directory, git repo flag
  - platform, shell, OS version
  - model name and ID
  - knowledge cutoff
  - model family reference
  <fast_mode_info> tag

(plain text, no header)
  "When working with tool results, write down..."

gitStatus:
  - current branch
  - main branch
  - modified/untracked files
  - recent commits (5)
```

gitStatus is only appended in interactive mode (not `-p` mode).

---

## 2. tools[] — Tool Definitions (25 tools, 48K chars)

Role: Each tool has a `name`, `description` (behavioral instructions for *when* and *how* to use it), and `input_schema` (JSON Schema for parameters).

Tool descriptions are NOT in the system prompt — they are in the `tools` array. This is a significant chunk of context (48K chars, more than the entire system prompt).

### Tool inventory

| Tool | Description chars | Role |
|---|---|---|
| Agent | 7,000 | Spawn subagents (lists available agent types + usage rules) |
| Bash | 10,845 | Shell execution (includes git commit workflow, PR creation instructions) |
| Read | 1,773 | File reading (images, PDFs, notebooks) |
| Edit | 1,108 | String replacement in files |
| Write | 618 | Create/overwrite files |
| Glob | 530 | File pattern matching |
| Grep | 866 | Content search (ripgrep) |
| NotebookEdit | 513 | Jupyter notebook editing |
| WebFetch | 1,479 | HTTP fetch |
| WebSearch | 1,318 | Web search |
| Skill | 1,272 | Invoke slash-command skills |
| AskUserQuestion | 1,763 | Ask user for input |
| EnterPlanMode | 4,022 | Plan creation |
| ExitPlanMode | 1,849 | Plan finalization |
| EnterWorktree | 1,335 | Git worktree isolation |
| ExitWorktree | 1,923 | Leave worktree |
| TaskCreate | 2,310 | Create background tasks |
| TaskGet | 732 | Get task status |
| TaskUpdate | 2,243 | Update task status |
| TaskList | 998 | List tasks |
| TaskOutput | 446 | Read task output |
| TaskStop | 203 | Stop a task |
| CronCreate | 2,319 | Create scheduled tasks |
| CronDelete | 100 | Delete cron |
| CronList | 60 | List crons |

### Deferred tools variant

On some models (e.g. Opus), some tools are **deferred**: only their names appear in a `<system-reminder>` in the user message, and a `ToolSearch` tool is added so the model can fetch their schemas on demand. This saves input tokens. On Haiku, all 25 tools are fully resolved.

---

## 3. messages[] — User Message (1 message, multiple text blocks)

Role: The user turn. But most of its content is injected context, not the user's actual words.

### Content block 0 — Skills list (~6K chars, from plugins/config)

Injected as `<system-reminder>`. Lists available skills for the Skill tool.

```xml
<system-reminder>
The following skills are available for use with the Skill tool:

- update-config: Use this skill to configure...
- commit-commands:commit: Create a git commit
- ...
</system-reminder>
```

On a truly fresh install with no plugins, this lists only built-in skills (commit, etc.).
Custom skills come from `settings.json` `enabledPlugins` and local skill directories.

### Content block 1 — CLAUDE.md + metadata (~4K chars, from project)

Injected as `<system-reminder>`. Contains:

```xml
<system-reminder>
As you answer the user's questions, you can use the following context:
# claudeMd
Codebase and user instructions are shown below...

Contents of /path/to/CLAUDE.md (project instructions, checked into the codebase):
[full CLAUDE.md text]

Contents of /path/to/subdir/CLAUDE.md (if any):
[subdirectory CLAUDE.md text]

# currentDate
Today's date is 2026-04-19.
</system-reminder>
```

This block walks the directory tree for all CLAUDE.md files in scope.
Also includes `# currentDate`.

### Content block N — User prompt (variable)

The actual user text. Has `cache_control: ephemeral, ttl=1h` on the last content block.

```
write some request
```

---

## What's NOT here (and where it lives)

| Thing | Where |
|---|---|
| Output style | Appended to system block 2 (when configured) |
| Custom agents | Added to Agent tool description |
| MCP server tools | Added to tools[] |
| Memory files | Not loaded into prompt; model reads them via Read tool, guided by MEMORY.md |
| Hooks | Execute server-side; not in prompt (mentioned in system block 2 rules) |
| Deferred tool schemas | In ToolSearch results, fetched on demand |

# What the Model Gets

Everything the model receives, in order, on a fresh interactive session with only a CLAUDE.md.
v2.1.79. Source: `capture.py` → `request.json`. ~85K chars total.

## system

```
x-anthropic-billing-header: cc_version=2.1.79.04b; cc_entrypoint=cli; cch=00000;
```

## system

```
You are Claude Code, Anthropic's official CLI for Claude.
```

## system

```
You are an interactive agent that helps users according to your "Output Style" below, which
describes how you should respond to user queries...

{this preamble changes depending on whether an output style is active:
 - with output style: "...according to your Output Style below..."
 - without output style: "...that helps users with software engineering tasks..."}

IMPORTANT: Assist with authorized security testing...
IMPORTANT: You must NEVER generate or guess URLs...

# System
{6 bullets: output rendering, permissions, system-reminder tags, prompt injection, hooks, compression}

# Doing tasks                                          ← controlled by keep-coding-instructions
{10 bullets: software engineering framing, read before modify, avoid file bloat, no time estimates,
no brute-force retries, OWASP security, avoid over-engineering, no backwards-compat hacks, /help link}

{this section is REMOVED when an output style sets keep-coding-instructions: false.
 when omitted or true, the section stays. see table below.}

# Executing actions with care
{reversibility/blast radius policy, 4 categories of risky actions, investigate before destroying}

# Using your tools
{prefer dedicated tools over Bash, Agent for exploration, Skill for slash commands, parallel calls}

# Tone and style
{no emojis, concise, file_path:line_number references, no colon before tool calls}

# Output efficiency
{lead with answer not reasoning, focus on decisions/milestones/errors, one sentence over three}
```

## system

```
# auto memory
{memory system path and write instructions}
## Types of memory
{user, feedback, project, reference — XML definitions with examples for each}
## What NOT to save in memory
## How to save memories
## When to access memories
## Before recommending from memory
## Memory and other forms of persistence

# Environment
 - Primary working directory: /path/to/project
  - Is a git repository: true
 - Platform: linux
 - Shell: bash
 - OS Version: ...
 - You are powered by the model named ...
 - ...

# Output Style: <name>                                ← only present when an output style is set
{full output style markdown content}

gitStatus: This is the git status at the start of the conversation...
Current branch: main
Main branch (you will usually use this for PRs): main
Status:
{modified/untracked files}
Recent commits:
{last 5 commits}
```

### Output style behavior

The `outputStyle` setting selects a style by name. Styles come from three sources:
built-in (`Explanatory`, `Learning`), plugins, or user files in `~/.claude/output-styles/`.

`"default"` maps to null — no output style, no `# Output Style` section.

The `keep-coding-instructions` frontmatter flag in `.md` output style files controls
whether `# Doing tasks` stays in the previous block:

| outputStyle | Block above | `# Doing tasks` | `# Output Style` |
|---|---|---|---|
| `"default"` (= null) | 12,573 chars | yes | no |
| `"Explanatory"` (built-in, keep: true) | 12,636 chars | yes | yes |
| custom style (keep: false) | 9,245 chars | no | yes |
| custom style (keep: true) | 12,636 chars | yes | yes |
| custom style (keep: omitted) | 12,636 chars | yes (default) | yes |

## system (25 tools, 48K chars — largest block)

```
{for each of 25 tools: name, description (usage instructions), parameter schema}

{largest: Bash 10.8K (includes git commit/PR workflow instructions),
Agent 7K (lists all subagent types), EnterPlanMode 4K}

{other tools: Read, Edit, Write, Glob, Grep, NotebookEdit, WebFetch, WebSearch,
Skill, AskUserQuestion, ExitPlanMode, EnterWorktree, ExitWorktree,
TaskCreate, TaskGet, TaskUpdate, TaskList, TaskOutput, TaskStop,
CronCreate, CronDelete, CronList}
```

## user (injected by harness)

```
<system-reminder>
The following skills are available for use with the Skill tool:

- commit-commands:commit: Create a git commit
- commit-commands:commit-push-pr: Commit, push, and open a PR
{... more skills from plugins and local skill directories}
</system-reminder>
```

## user (injected by harness)

```
<system-reminder>
As you answer the user's questions, you can use the following context:
# claudeMd
Codebase and user instructions are shown below. Be sure to adhere to these instructions.
IMPORTANT: These instructions OVERRIDE any default behavior and you MUST follow them exactly as written.

Contents of /path/to/CLAUDE.md (project instructions, checked into the codebase):
{full CLAUDE.md text}

Contents of /path/to/subdir/CLAUDE.md (if any):
{full subdirectory CLAUDE.md text}

# currentDate
Today's date is 2026-04-19.
</system-reminder>
```

## user (actual human input)

```
write some request
```

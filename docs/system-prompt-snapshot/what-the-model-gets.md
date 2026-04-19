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

{removed when output style sets keep-coding-instructions: false; stays otherwise}

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

When `keep-coding-instructions: false` is set in the output style frontmatter, `# Doing tasks` is removed from this block (~3.4K chars smaller).

## tool (8.0K)

```
Agent: Launch a new agent to handle complex, multi-step tasks autonomously.
{input_schema: prompt, description, subagent_type, isolation, model, run_in_background}
```

## tool (12.3K)

```
Bash: Executes a given bash command and returns its output.
{input_schema: command, description, timeout, run_in_background, dangerouslyDisableSandbox}
```

## tool (1.1K)

```
Glob: Fast file pattern matching tool that works with any codebase size.
{input_schema: pattern, path}
```

## tool (3.3K)

```
Grep: A powerful search tool built on ripgrep.
{input_schema: pattern, path, glob, type, output_mode, -A, -B, -C, -i, -n, multiline, head_limit, offset}
```

## tool (2.5K)

```
Read: Reads a file from the local filesystem.
{input_schema: file_path, offset, limit, pages}
```

## tool (1.7K)

```
Edit: Performs exact string replacements in files.
{input_schema: file_path, old_string, new_string, replace_all}
```

## tool (1.0K)

```
Write: Writes a file to the local filesystem.
{input_schema: file_path, content}
```

## tool (1.5K)

```
NotebookEdit: Completely replaces the contents of a specific cell in a Jupyter notebook.
{input_schema: notebook_path, cell_number, new_source, cell_type}
```

## tool (1.8K)

```
WebFetch: Fetches content from a URL (fails for authenticated/private URLs).
{input_schema: url, prompt}
```

## tool (1.8K)

```
WebSearch: Allows Claude to search the web and use the results to inform responses.
{input_schema: query, domain_filter, max_results, time_period}
```

## tool (1.6K)

```
Skill: Execute a skill within the main conversation.
{input_schema: skill, args}
```

## tool (4.9K)

```
AskUserQuestion: Ask the user questions during execution.
{input_schema: question, options, allow_free_text, default_value, ...}
```

## tool (4.1K)

```
EnterPlanMode: Enter plan mode for non-trivial implementation tasks.
{input_schema: plan_file_path}
```

## tool (2.5K)

```
ExitPlanMode: Exit plan mode after writing plan to file.
{input_schema: plan_file_path, approved, feedback}
```

## tool (1.6K)

```
EnterWorktree: Create an isolated git worktree and switch to it.
{input_schema: branch_name, commit}
```

## tool (2.4K)

```
ExitWorktree: Exit a worktree session and return to original directory.
{input_schema: save_changes, merge_strategy, target_branch}
```

## tool (2.9K)

```
TaskCreate: Create a structured task list for the current coding session.
{input_schema: tasks, description}
```

## tool (1.0K)

```
TaskGet: Retrieve a task by its ID from the task list.
{input_schema: task_id}
```

## tool (3.4K)

```
TaskUpdate: Update a task in the task list.
{input_schema: task_id, status, ...}
```

## tool (1.1K)

```
TaskList: List all tasks in the task list.
{input_schema: (none)}
```

## tool (0.9K)

```
TaskOutput: Retrieves output from a running or completed task.
{input_schema: task_id, timeout}
```

## tool (0.5K)

```
TaskStop: Stops a running background task by its ID.
{input_schema: task_id}
```

## tool (3.0K)

```
CronCreate: Schedule a prompt to be enqueued at a future time.
{input_schema: schedule, prompt, description, ...}
```

## tool (0.3K)

```
CronDelete: Cancel a cron job previously scheduled with CronCreate.
{input_schema: cron_id}
```

## tool (0.2K)

```
CronList: List all cron jobs scheduled via CronCreate in this session.
{input_schema: (none)}
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

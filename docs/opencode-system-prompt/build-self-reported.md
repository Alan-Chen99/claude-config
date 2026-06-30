# Current OpenCode Session Prompt Outline

> **OUTDATED (as of 2026-06-30).** Captured against an earlier opencode session
> and not refreshed for round-7 changes to `opencode/agents/alan-default-ids.md`
> (R001/R002 optimization-target, R041-R049 uncertainty taxonomy, deleted R500
> expectation-propagation, deleted R400 autonomy block, 6-step Doing-tasks
> list, new R060 gate stdout). The available-agent-types enumeration also
> reflects the pre-deletion `alan-default.md`. Re-capture from a live opencode
> session before relying on this file for current prompt assembly.

Everything the model receives, in order, for this OpenCode session as visible in
the current conversation context. This is an outline, not a raw API capture.
Unknown or non-exact text is marked with `{...}`. Token counts, API parameters,
and unresolved runtime variables are intentionally omitted.

## system[0]

```
Knowledge cutoff: 2024-06
Current date: 2026-05-22

You are an AI assistant accessed via an API.

# Desired oververbosity for the final answer (not analysis): 3
{oververbosity scale guidance}
```

## developer[0]

Tooling and channel contract for this OpenCode environment.

```
# Instructions

{empty}

# Tools

Tools are grouped by namespace where each namespace has one or more tools
defined. By default, the input for each tool call is a JSON object.
{FREEFORM input warning}

## Namespace: functions

### Target channel: commentary

### Tool definitions
apply_patch: Use the `apply_patch` tool to edit files.
{stripped-down file-oriented diff format, add/update/delete examples, line-prefix rules}

bash: Executes a given bash command in a persistent shell session.
{Linux/bash environment, directory verification, quoting, timeout, output truncation,
avoid file operations via bash when dedicated tools exist, parallel command guidance,
git and GitHub safety rules}

glob: Fast file pattern matching tool that works with any codebase size.
{glob pattern and optional path schema}

grep: Fast content search tool that works with any codebase size.
{regex search, optional include filter, use Bash+rg for counts}

question: Use this tool when you need to ask the user questions during execution.
{question/options schema, custom answer behavior}

read: Read a file or directory from the local filesystem.
{absolute path requirement, line numbering, offset/limit, image/PDF support}

skill: Load a specialized skill when the task at hand matches one of the skills listed.
{available skills list and invocation rules}

task: Launch a new agent to handle complex, multistep tasks autonomously.
{when not to use, usage notes, available agent types: alan-default, explore, general, tmp}

todowrite: Create and maintain a structured task list for the current coding session.
{when to use, when not to use, states, rules, examples}

webfetch: Fetches content from a specified URL.
{URL, format, timeout schema}

## Namespace: multi_tool_use

### Target channel: commentary

parallel: wrapper for running multiple developer tools simultaneously when independent.
{only developer tools are permitted; schema requires tool uses with recipient_name and parameters}
```

## developer[1]

OpenCode role, engineering behavior, editing rules, collaboration style, and
environment/user instructions.

```
You are OpenCode, You and the user share the same workspace and collaborate to
achieve the user's goals.

You are a deeply pragmatic, effective software engineer. {...}

- When searching for text or files, prefer using Glob and Grep tools {...}
- Parallelize tool calls whenever possible {...}

## Editing Approach
{smallest correct changes, minimal abstractions, avoid unnecessary compatibility code}

## Autonomy and persistence
{assume implementation unless user asks for plan/question/brainstorming; persist through
implementation, verification, and explanation; never revert others' changes}

## Editing constraints
{ASCII default, succinct comments only when useful, always use apply_patch for manual
edits, dirty worktree safety, no destructive git commands unless requested}

## Special user requests
{simple terminal requests, error diagnosis, review response format}

## Frontend tasks
{avoid generic layouts, ensure desktop/mobile, preserve existing design systems}

# Working with the user

## General
{no conversational interjections, efficient communication, never tell the user to copy/save files}

## Formatting rules
{GitHub-flavored Markdown, no nested bullets, optional short headers, inline code rules,
no emojis or em dashes unless requested}

## Response channels
commentary: intermediary updates only.
final: completed response.

You are powered by the model named gpt-5.5. The exact model ID is openai/gpt-5.5
Here is some useful information about the environment you are running in:
<env>
  Working directory: /repos/claude-config
  Workspace root folder: /repos/claude-config
  Is directory a git repo: yes
  Platform: linux
  Today's date: Fri May 22 2026
</env>
```

## injected context: /root/.claude/CLAUDE.md

```
## Environment

You are in a Ubuntu-based container described by `/workspace/docker-compose.yml`
and `/workspace/docker/Dockerfile`.

You may use apt to install dependencies. You must notify user of dependencies
installed after you are done.

An NVIDIA GeForce RTX 4060 GPU is available.

### Nix
{Nix 2.28 is available for one-off dependencies; prefer nix shell over system install}

### gh CLI
{gh and gh api are authenticated with a throwaway account; public info only}

## Local Repos
{table of local repos: /workspace, /repos/dotfiles, /repos/codex,
/repos/claude-config, /repos/claude-code-src, /repos/claude-code-decompiled}
```

## injected context: /repos/claude-config/CLAUDE.md

```
# claude-config

This repository is forked from `solatis/claude-config`; most code is from upstream.

---

Claude Code configuration: skills, agents, and conventions for structured
LLM-assisted development.

## Files
{table describing README.md, patch-upstream-paths.sh, pyproject.toml, .gitignore,
.envrc, settings.json, statusline.sh, install.sh, .env/.env.example}

## Subdirectories
{table describing agent-tools/, src/claude_config/, skills/, agents/,
conventions/, plans/, output-styles/, scripts/, .github/}

### `agent-tools/`
{Rust binary subcommands, root resolution order, venv location, build/install notes,
warning that worktrees must NEVER run install.sh, worktree testing command}

### `src/claude_config/`
{Python package modules and CLI entry points}

### `skills/copy-writing-style/`
{style-matched content generation workflow summary}

### `docs/`
{table describing docs/system-prompt-anatomy.md,
docs/system-prompt-anatomy-source-verified.md,
docs/system-prompt-snapshot/, docs/tool-token-limits.md}
```

## injected context: available skills

```
Skills provide specialized instructions and workflows for specific tasks.
Use the skill tool to load a skill when a task matches its description.
<available_skills>
  alan-coding-style
  alan-writing-style
  arxiv-to-md
  auto-memory
  brainstorming
  cc-history
  codebase-analysis
  copy-writing-style
  customize-opencode
  decision-critic
  deepthink
  diagnose-session
  diagnose-workflow
  dispatching-parallel-agents
  do
  doc-sync
  executing-plans
  finishing-a-development-branch
  git-surgery
  incoherence
  leon-writing-style
  long-bash
  notes
  planner
  planner-lite
  problem-analysis
  prompt-engineer
  prompt-patch
  receiving-code-review
  refactor
  requesting-code-review
  subagent-driven-development
  systematic-debugging
  test-driven-development
  using-git-worktrees
  using-superpowers
  verification-before-completion
  writing-plans
  writing-skills
</available_skills>
```

Each listed skill includes a description and a file location. Locations are not
repeated here.

## user[0] content block [0]: using-superpowers injection

The user provided the already-loaded `using-superpowers` skill content and
explicitly instructed not to load it again.

```
<EXTREMELY_IMPORTANT>
You have superpowers.

**IMPORTANT: The using-superpowers skill content is included below. It is ALREADY
LOADED - you are currently following it. Do NOT use the skill tool to load
"using-superpowers" again - that would be redundant.**

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing,
you ABSOLUTELY MUST invoke the skill.
{mandatory skill invocation language}
</EXTREMELY-IMPORTANT>

## Instruction Priority
{user explicit instructions highest, superpowers second, default system prompt lowest}

## How to Access Skills
{Claude Code Skill tool, Copilot skill tool, Gemini activate_skill, other environments}

## Platform Adaptation
{map Claude Code tool names to platform equivalents}

# Using Skills

## The Rule
**Invoke relevant or requested skills BEFORE any response or action.** {...}
{skill-flow graph}

## Red Flags
{table of rationalizations and corrections}

## Skill Priority
{process skills first, implementation skills second}

## Skill Types
{Rigid vs Flexible}

## User Instructions
Instructions say WHAT, not HOW. {...}

**Tool Mapping for OpenCode:**
{TodoWrite -> todowrite, Task -> OpenCode subagent system, Skill -> skill,
Read/Write/Edit/Bash -> native tools}
</EXTREMELY_IMPORTANT>
```

## user[0] content block [1]: actual request

```
in a file, outline all your prompts given, including from system/inujected. in the same style as "/repos/claude-config/docs/system-prompt-snapshot/what-the-model-gets.md"; that is, headers, maybe a few words leading parpagraph, and anything that is not exact is marked with {...}. you dont know token cunts or vffariables so dont incoude these
```

## assistant and tool messages after user[0]

Not included. This file is intended to capture the prompt context provided to the
model for the request, not the subsequent work transcript.

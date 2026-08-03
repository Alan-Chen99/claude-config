# skills/

Script-based agent workflows with shared orchestration framework.

## MANDATORY: Read Before Modifying

**STOP. Before editing ANY Python file in `skills/scripts/`, you MUST read `README.md`.**

The README defines:

- File section ordering (SHARED PROMPTS -> CONFIGURATION -> MESSAGE TEMPLATES -> MESSAGE BUILDERS -> STEP DEFINITIONS -> OUTPUT FORMATTING -> ENTRY POINT)
- Step-delimited prompt organization within MESSAGE TEMPLATES
- Naming conventions for prompt constants (`[PHASE]_[TYPE]`)
- Patterns for dispatch prompts (static templates vs builder functions)
- Anti-patterns to avoid (action factories, forward references)

Failure to follow these patterns creates technical debt and inconsistency across skills. The patterns exist because they solve real problems with prompt readability and maintenance.

**Read `README.md` now if you haven't already.**

## Files

| File        | What                                                      | When to read                    |
| ----------- | --------------------------------------------------------- | ------------------------------- |
| `README.md` | File organization, prompt patterns, naming, anti-patterns | BEFORE modifying any skill code |

## Subdirectories

| Directory             | What                                      | When to read                             |
| --------------------- | ----------------------------------------- | ---------------------------------------- |
| `scripts/`            | Python package root for all skill code    | Executing skills, debugging behavior     |
| `planner/`            | Planning and execution workflows          | Creating implementation plans            |
| `refactor/`           | Refactoring analysis across dimensions    | Technical debt review, code quality      |
| `problem-analysis/`   | Structured problem decomposition          | Understanding complex issues             |
| `decision-critic/`    | Decision stress-testing and critique      | Validating architectural choices         |
| `deepthink/`          | Structured reasoning for open questions   | Analytical questions without frameworks  |
| `codebase-analysis/`  | Systematic codebase exploration           | Repository architecture review           |
| `prompt-engineer/`    | Prompt optimization and engineering       | Improving agent prompts                  |
| `prompt-engineer-v2/`    | Autoloading prompt-engineering context (principles + suggestions) with an optional 12-step "patch mode" script for difficult prompt edits; `test-requests.md` captures a worked-example transcript of one patch-mode run | Whenever working on prompts/instructions/agent definitions (autoload); editing the principles, the patch-mode workflow, or its example transcript |
| `incoherence/`        | Consistency detection                     | Finding spec/implementation mismatches   |
| `do/`                 | Meta-execution pipeline (intent→reframe→execute→reflect) | Wrapping requests in structured execution |
| `doc-sync/`           | Documentation synchronization             | Syncing docs across repos                |
| `notes/`              | Persist knowledge into agent-facing docs     | Using `/notes` to remember things for future conversations |
| `opencode-subcommand/` | opencode-as-subcommand recipes: inline config, plugin loading, model overrides, session capture | Driving opencode programmatically — test harness, automation, batch runs |
| `auto-memory/`        | Drop-in for Claude Code's built-in auto-memory feature | Before reading/writing memories under `~/.claude/projects/<slug>/memory/` (skip if "# auto memory" section already in prompt) |
| `leon-writing-style/` | Style-matched content generation          | Writing content matching user's style    |
| `alan-coding-style/`  | Style-matched code generation and review  | Coding matching user's conventions       |
| `alan-writing-style/` | Style-matched content generation           | Writing content matching user's style    |
| `copy-writing-style/` | Generic style-matched content generation   | Writing in any reference style           |
| `arxiv-to-md/`        | arXiv paper to markdown conversion        | Converting papers for LLM consumption    |
| `cc-history/`         | Claude Code conversation history analysis | Querying past conversations, token usage |
| `diagnose-session/`   | Post-hoc conversation log analysis        | Surfacing unreported items from session logs |
| `session-timeline/`   | Focus-directed extraction of opencode session content into raw evidence artifacts | Building the evidence layer for interpretive rounds; separates "what's in the log" from "what it means" |
| `diagnose-workflow/`  | Structural sub-agent workflow extraction   | Diagnosing multi-agent workflow success/failure |
| `long-bash/`          | Long-running bash command protocol         | Running commands that may exceed 2min timeout   |
| `git-surgery/`        | libgit2/pygit2 history rewrites without touching worktree, index, or HEAD; preserves SHA references in tracked files and commit messages | Squashing/dropping/reordering/amending commits when the worktree must survive or commit SHAs are checked in elsewhere |

## Script Invocation

Custom skills use `agent-tools`:

<invoke cmd="agent-tools skill <skill_name>.<module> --step 1" />

Upstream skills use the direct python invocation:

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.<skill_name>.<module> --step 1" />

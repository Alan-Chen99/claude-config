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
| `prompt-patch/`          | Structured 11-step prompt change workflow | Targeted prompt modifications with checks  |
| `incoherence/`        | Consistency detection                     | Finding spec/implementation mismatches   |
| `do/`                 | Meta-execution pipeline (intent→reframe→execute→reflect) | Wrapping requests in structured execution |
| `doc-sync/`           | Documentation synchronization             | Syncing docs across repos                |
| `notes/`              | Persist knowledge into agent-facing docs     | Using `/notes` to remember things for future conversations |
| `auto-memory/`        | On-demand drop-in for Claude Code's built-in auto-memory feature | Using `/auto-memory` when `autoMemoryEnabled: false` |
| `leon-writing-style/` | Style-matched content generation          | Writing content matching user's style    |
| `alan-coding-style/`  | Style-matched code generation and review  | Coding matching user's conventions       |
| `alan-writing-style/` | Style-matched content generation           | Writing content matching user's style    |
| `copy-writing-style/` | Generic style-matched content generation   | Writing in any reference style           |
| `arxiv-to-md/`        | arXiv paper to markdown conversion        | Converting papers for LLM consumption    |
| `cc-history/`         | Claude Code conversation history analysis | Querying past conversations, token usage |
| `diagnose-session/`   | Post-hoc conversation log analysis        | Surfacing unreported items from session logs |
| `diagnose-workflow/`  | Structural sub-agent workflow extraction   | Diagnosing multi-agent workflow success/failure |
| `long-bash/`          | Long-running bash command protocol         | Running commands that may exceed 2min timeout   |

## Script Invocation

Custom skills use `agent-tools`:

<invoke cmd="agent-tools skill <skill_name>.<module> --step 1" />

Upstream skills use the direct python invocation:

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.<skill_name>.<module> --step 1" />

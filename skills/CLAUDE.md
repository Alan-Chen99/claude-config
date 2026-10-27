# skills/

**Before editing any Python file in `skills/scripts/`, read `README.md`**: the layout, naming
and string rules every skill module follows.

A skill that runs only when the user or a workflow names it has no `description` and a
`name-only` entry in `settings.json` `skillOverrides`; `sys_prompt/README.md`, "`listed without a
description`", has why.

## Subdirectories

| Directory | What | When to read |
| --- | --- | --- |
| `scripts/` | Python package root for all skill code | Executing skills, debugging behavior |
| `planner/` | Planning and execution workflows | Creating implementation plans |
| `planner-lite/` | Planning and execution without subagent dispatch | Planning from inside a subagent |
| `refactor/` | Refactoring analysis across dimensions | Technical debt review, code quality |
| `problem-analysis/` | Structured problem decomposition | Understanding complex issues |
| `decision-critic/` | Decision stress-testing and critique | Validating architectural choices |
| `deepthink/` | Structured reasoning for open questions | Analytical questions without frameworks |
| `codebase-analysis/` | Systematic codebase exploration | Repository architecture review |
| `prompt-engineer/` | Prompt optimization and engineering | Improving agent prompts |
| `prompt-engineer-v2/` | Autoloading prompt-engineering context, its measurement loop, a "patch mode" script | Working on prompts or agent definitions; measuring a prompt edit |
| `incoherence/` | Consistency detection | Finding spec/implementation mismatches |
| `do/` | Meta-execution pipeline: intent, reframe, execute, reflect | Wrapping requests in structured execution |
| `doc-sync/` | Documentation synchronization | Syncing docs across repos |
| `notes/` | Persist knowledge into agent-facing docs | Remembering something for future conversations (`/notes`) |
| `opencode-subcommand/` | Recipes for `opencode run`: config, plugins, model overrides, session capture | Driving opencode programmatically |
| `auto-memory/` | Drop-in for Claude Code's built-in auto-memory | Reading/writing `~/.claude/projects/<slug>/memory/` |
| `leon-writing-style/` | Style-matched content generation | Writing content matching user's style |
| `alan-coding-style/` | Style-matched code generation and review | Coding matching user's conventions |
| `alan-writing-style/` | Write, rewrite or check text as Alan | Text in Alan's voice, only when invoked |
| `adhd-explain/` | Shapes an explanation Alan asked for, for a reader with ADHD; adapted from `ayghri/i-have-adhd` (MIT); autoloads | Answering an explain-X question; changing its rules or scope |
| `copy-writing-style/` | Style-matched generation from any reference file | Writing in any reference style |
| `arxiv-to-md/` | arXiv paper to markdown conversion | Converting papers for LLM consumption |
| `cc-history/` | Claude Code conversation history analysis | Querying past conversations, token usage |
| `session-analysis/` | Session log analysis: skeleton-first reading; facts-only evidence artifacts | Analyzing opencode or Claude Code session logs |
| `resume-from-summary/` | Recovering the transcript behind a session summary; the system prompt names it | Continuing from autocompact, `/compact`, a resume or a handoff |
| `diagnose-workflow/` | Structural sub-agent workflow extraction | Diagnosing multi-agent workflow success/failure |
| `long-bash/` | Long-running bash command protocol (autoloads) | Running, or recovering, a command that outruns the Bash timeout |
| `git-surgery/` | pygit2 history rewrites that leave worktree, index and HEAD alone and preserve cited SHAs | Rewriting commits when the worktree must survive or SHAs are checked in |
| `telegram-hitl/` | Asking a human over Telegram and waiting hours: the rules, the log reader and its guarantees | A session needs a human decision, or reads or sends on the channel |
| `playwright-cli/` | **Vendored** from the `@playwright/cli` npm package (tag `v0.1.18`); `playwright-cli install --skills --global` rewrites it through the `~/.claude/skills` symlink | Never edit directly; after `npm update -g @playwright/cli`, re-run that and review `git diff`, the only drift signal |
| `artifact-design/`, `artifact-diagramming/` | **Vendored** byte-identical from the Claude Code binary (2.1.269 assets): the built-ins `enableArtifact: false` removes, kept because `/workspace/CLAUDE.md` names `artifact-design`. Regenerate only with `.claude/skills/update-claude-code/skilldiff.sh --update`, whose skill also tracks where the built-in's loader changes the text | Never edit directly; designing a page with the Artifact tool off; after a Claude Code upgrade |

## Script Invocation

Custom skills use `agent-tools`:

<invoke cmd="agent-tools skill <skill_name>.<module> --step 1" />

Upstream skills invoke python directly:

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.<skill_name>.<module> --step 1" />

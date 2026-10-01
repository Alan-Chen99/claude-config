# skills/

Script-based agent workflows with shared orchestration framework. **Before editing any Python
file in `skills/scripts/`, read `README.md`** — it fixes the section ordering, the
step-delimited prompt organization, the `[PHASE]_[TYPE]` naming of prompt constants, the
dispatch-prompt patterns and the anti-patterns.

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
| `prompt-engineer-v2/` | Autoloading prompt-engineering context, the measurement loop it defers to, a "patch mode" script for difficult prompt edits | Working on prompts or agent definitions (autoload); measuring a prompt edit |
| `incoherence/`        | Consistency detection                     | Finding spec/implementation mismatches   |
| `do/`                 | Meta-execution pipeline (intent→reframe→execute→reflect) | Wrapping requests in structured execution |
| `doc-sync/`           | Documentation synchronization             | Syncing docs across repos                |
| `notes/`              | Persist knowledge into agent-facing docs  | Using `/notes` to remember things for future conversations |
| `opencode-subcommand/` | opencode-as-subcommand recipes: config, plugins, model overrides, session capture | Driving opencode programmatically |
| `auto-memory/`        | Drop-in for Claude Code's built-in auto-memory | Reading/writing `~/.claude/projects/<slug>/memory/` |
| `leon-writing-style/` | Style-matched content generation          | Writing content matching user's style    |
| `alan-coding-style/`  | Style-matched code generation and review  | Coding matching user's conventions       |
| `alan-writing-style/` | Write, rewrite or check text as Alan; `samples/` is maintenance data | Text in Alan's voice, only when invoked |
| `copy-writing-style/` | Style-matched generation from any reference file | Writing in any reference style           |
| `arxiv-to-md/`        | arXiv paper to markdown conversion        | Converting papers for LLM consumption    |
| `cc-history/`         | Claude Code conversation history analysis | Querying past conversations, token usage |
| `session-analysis/`   | Session log analysis: skeleton-first reading; facts-only evidence artifacts | Analyzing agent session logs (opencode or Claude Code JSONL) |
| `diagnose-workflow/`  | Structural sub-agent workflow extraction  | Diagnosing multi-agent workflow success/failure |
| `long-bash/`          | Long-running bash command protocol (autoloads) | Running, or recovering, a command that outruns the Bash timeout |
| `git-surgery/`        | pygit2 history rewrites that leave worktree, index and HEAD alone and preserve cited SHAs | Rewriting commits when the worktree must survive or SHAs are checked in |
| `telegram-hitl/`      | Asking a human over Telegram and waiting hours: `SKILL.md` is the rules (1,000-token cap in `doc-budget.toml`); `listen.py` is the log reader armed under `Monitor` — reactions are its acks, `--wait` declares a wait its `stop-hook` holds for an unattended session; `README.md` has the guarantees | A session needs a human decision, or reads or sends on the channel |
| `playwright-cli/`     | **Vendored** from the `@playwright/cli` npm package (tag `v0.1.18`); regenerate with `playwright-cli install --skills --global`, which writes through the `~/.claude/skills` symlink; `git diff` is the only drift signal | Never edit directly; after `npm update -g @playwright/cli`, re-run and review the diff |
| `artifact-design/`, `artifact-diagramming/` | **Vendored** from the Claude Code binary (2.1.269 assets), byte-identical: the built-in skills `enableArtifact: false` removes, kept because `/workspace/CLAUDE.md` names `artifact-design`. Regenerate only with `.claude/skills/update-claude-code/skilldiff.sh --update`; the built-in's text is generated at load time, so a matching copy is not parity — upgrade runbook §4 | Never edit directly; designing a page with the Artifact tool off; after a Claude Code upgrade |

## Script Invocation

Custom skills use `agent-tools`:

<invoke cmd="agent-tools skill <skill_name>.<module> --step 1" />

Upstream skills use the direct python invocation:

<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.<skill_name>.<module> --step 1" />

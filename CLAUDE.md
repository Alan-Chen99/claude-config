# claude-config

This repository is forked from `solatis/claude-config`; most code is from upstream.

---

Claude Code configuration: skills, agents, and conventions for structured LLM-assisted development.

## Files

| File                      | What                                                        | When to read                                  |
| ------------------------- | ----------------------------------------------------------- | --------------------------------------------- |
| `README.md`               | Workflow philosophy, usage guide                            | Understanding the approach, getting started   |
| `patch-upstream-paths.sh` | Patches `.claude/` → `~/.claude/` paths after upstream sync | After pulling/rebasing upstream changes       |
| `pyproject.toml`          | Python project config, entry points for cc-pretty etc.      | Adding dependencies, modifying build settings |
| `.gitignore`              | Git ignore patterns                                         | Adding new generated/temp files to ignore     |
| `.envrc`                  | direnv environment config                                   | Modifying shell environment for development   |
| `settings.json`           | Claude Code user settings                                   | Modifying hooks, statusline, permissions      |
| `statusline.sh`           | Status line script wired up via `settings.json`             | Customizing the in-session status line        |
| `install.sh`              | Symlinks dirs/files into `~/.claude/`, builds `agent-tools`, puts `claude.sh` on PATH | Installing or reinstalling the config         |
| `.env` / `.env.example`   | Unified config (NTFY URL, OpenRouter, Anthropic token-count) | Setting up secrets — see `.env.example`       |

## Subdirectories

| Directory          | What                                                    | When to read                                      |
| ------------------ | ------------------------------------------------------- | ------------------------------------------------- |
| `.claude/`         | Repo-local Claude Code config (incl. project-local skills) | Adding repo-local skills, settings, hooks       |
| `agent-tools/`     | Rust binary (`agent-tools`) wrapping skill/tool calls   | Modifying CLI wrappers, adding new commands       |
| `src/claude_config/` | Python package: cc-pretty, cc-workflow, custom tools  | Modifying Python tooling, adding new tools        |
| `skills/`          | Invocable skills (planner, deepthink, etc.)             | Using or modifying skills, adding new skills      |
| `agents/`          | Sub-agent definitions (developer, architect)            | Customizing agent behavior, understanding roles   |
| `conventions/`     | Documentation and code quality standards                | Writing documentation, understanding coding rules |
| `plans/`           | Plan storage directory                                  | Reviewing or executing existing plans             |
| `prompt-tests/`    | Runner-neutral prompt evaluation cases                  | Running or grading prompt evaluations             |
| `output-styles/`   | Output formatting styles — the only prompt customization that survives a background handoff | Customizing Claude's output format, writing rules that must hold in every session |
| `sys_prompt/`      | Full replacement prompts loaded via `--system-prompt-file` (not inherited by background sessions) | Editing the launcher's system prompt — see `docs/background-sessions.md` first |
| `scripts/`         | Standalone scripts — `claude.sh` launcher, MITM proxy, `reasoning-probe.py`, `prompt-test-run.sh` | Running or modifying utility scripts              |
| `.github/`         | GitHub workflows and config                             | Modifying CI/CD, GitHub-specific settings         |

### `agent-tools/`

Rust binary wrapping skill script and Python tool invocations. Subcommands:

- `agent-tools skill <mod> [args]` — run a skill script via `uv run python3 -m skills.<mod>`
- `agent-tools cc-pretty [args]` — pretty-print Claude Code JSONL session logs. Color is auto-detected (on for TTYs, off when piped or when `NO_COLOR` is set); `--color` forces it on, `--no-color` forces it off.
- `agent-tools cc-pretty-intercept [args]` — pretty-print one MITM intercept log file (`~/.claude/requests-log/<session>/NNNN.json`)
- `agent-tools cc-workflow [args]` — extract sub-agent workflow summary
- `agent-tools ntfy-hook [args]` — Claude Code notification hook (wraps `python3 -m claude_config.ntfy_hook`)
- `agent-tools count-tokens [--model MODEL] [--file PATH] [TEXT]` — count input tokens via Anthropic `count_tokens` API (wraps `python3 -m claude_config.count_tokens`)
- `agent-tools env-context` — print the `# Environment` block (cwd, git, platform, shell, OS). Inject via a `SessionStart` hook returning `{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: <stdout>}}` so cc still sees the env block when `--system-prompt-file` replaces the default prompt — keeps the system prompt itself static and fully cacheable.
- `agent-tools opencode [args]` — launch `opencode` with repo `.env` loaded for the opencode Langfuse plugin: maps `OPENCODE_LANGFUSE_SECRET_KEY`, `OPENCODE_LANGFUSE_PUBLIC_KEY`, and `OPENCODE_LANGFUSE_BASE_URL` to the unprefixed vars expected by the plugin (`LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASEURL`), sets git author/committer env to `opencode`, then forwards args to `opencode`.
- `agent-tools opencode-pretty <session-id> [args]` — pretty-print an opencode session. Mirrors `cc-pretty`'s CLI surface (`--tool-max`, `--truncate-input`, `--no-thinking`, `--show-usage`, `--show-rewound`, `--show-all`, `--chat-only`, `--skeleton`, `--compact-all`, `--compact-leg`, `--agent`, `--validate-only`) and reuses cc-pretty's rendering pipeline. Color is auto-detected (on for TTYs, off when piped or when `NO_COLOR` is set); `--color` forces it on, `--no-color` forces it off. Compaction boundaries (user message with a `compaction` part) become Claude-Code-style `compact_boundary` system records. An uncleaned `session.info.revert` is surfaced via the rewind marker — opencode normally deletes the abandoned tail on the next prompt, so only revert states caught before that prompt show up here.
- `agent-tools opencode.gate` — prompt gate used by opencode agent instructions; accepts stdin/heredoc input, prints gate instructions to stdout, and exits successfully.
- `agent-tools claude [args]` — launch Claude Code against this checkout's binary, hooks, system prompt, and output style without installing them, forwarding `args` to `claude`. Refuses to run from the installed checkout, which `claude.sh` already serves. See `agent-tools/CLAUDE.md`, "Launching an uninstalled checkout".

Root resolution:
1. The binary's compile-time root is authoritative: parent of `CARGO_MANIFEST_DIR` when `agent-tools` was built.
2. `CLAUDE_CONFIG_ROOT` is an assertion, not an override. If set, it must name the same directory as the compile-time root or `agent-tools` exits non-zero. The comparison is on directory identity (device + inode), not path spelling, so a bind mount serving one checkout under two names is one root rather than two.
3. If the compile-time root differs from the default root derived from `<config dir>/skills`, `CLAUDE_CONFIG_ROOT` must be set to the compile-time root or `agent-tools` exits non-zero. The config dir is `$CLAUDE_CONFIG_DIR` when set, else `~/.claude` — the directory Claude Code itself is reading. A session launched against one checkout's config therefore refuses any binary that is not that checkout's, instead of letting the installed build answer its hooks unremarked.

There is no `--root` override. This applies to all subcommands, including `run`, `hook-pre`, `hook-post`, `ps`, and `opencode.gate`, so wrong-worktree prompt tests fail loudly instead of silently exercising another checkout's binary or gate text.

Venv location: each project root resolves to `~/.claude/venvs/<basename>/` (set via `UV_PROJECT_ENVIRONMENT`), keeping venvs out of the source tree so host and container sessions don't fight over the same `.venv`.

Build: `cd agent-tools && cargo build --release`. Installed as a symlink at `~/.local/bin/agent-tools` → `<repo>/agent-tools/target/release/agent-tools` by `install.sh`.

**Worktrees must NEVER run `install.sh`** — the symlinks must always point to the canonical repo. Worktrees that install their own build will break all other sessions when the worktree is deleted.

Testing from a worktree without installing:
```bash
cd agent-tools && cargo build --release
CLAUDE_CONFIG_ROOT=/path/to/worktree ./target/release/agent-tools skill <module> [args...]
```

### `scripts/claude.sh`

The launcher. Exports the `Claude` git identity, sets `IS_SANDBOX=1` and
`CLAUDE_CODE_DISABLE_AGENT_VIEW=1`, optionally points Node at the MITM proxy on
`127.0.0.1:9160`, then execs
`claude --dangerously-skip-permissions --system-prompt-file <repo>/sys_prompt/alan-default-next.md`.

`CLAUDE_CODE_DISABLE_AGENT_VIEW=1` is load-bearing: background/agent-view forks drop
`--system-prompt-file`, so without it a forked session silently runs the stock prompt
(`docs/background-sessions.md`).

The prompt path is resolved from the script's own real location via `readlink -f`, so
the installed `~/.local/bin/claude.sh` symlink loads the canonical repo's prompt, while
invoking a worktree's copy by path (`/root/claude-config-work/scripts/claude.sh`) loads
that worktree's prompt — which is how a prompt edit gets exercised before it merges.

The proxy env (`HTTPS_PROXY`, `NODE_EXTRA_CA_CERTS`, `NODE_OPTIONS=--use-env-proxy`) is
bound only when a TCP connect to `127.0.0.1:9160` succeeds. With no listener the launcher
prints a warning to stderr and runs unintercepted, instead of exporting a proxy that would
fail every request with ECONNREFUSED. The listener itself comes from the canonical venv
provisioned by `install.sh`; see the HIDDEN PATH DEPENDENCY note there.

### `src/claude_config/`

Python package installed editable in `~/.claude/venvs/<basename>/` (see "Venv location" above) as `claude_config`. Contains custom (non-upstream) Python tools:

| Module                          | What                                            | CLI entry point                 |
| ------------------------------- | ----------------------------------------------- | ------------------------------- |
| `claude_config.cc_pretty`       | Parse and render Claude Code JSONL session logs | `cc-pretty`                     |
| `claude_config.cc_pretty_intercept` | Pretty-print one MITM intercept log file (`~/.claude/requests-log/<session>/NNNN.json`) | `cc-pretty-intercept` |
| `claude_config.cc_workflow`     | Sub-agent workflow extraction and analysis      | `cc-workflow-extract`           |
| `claude_config.opencode_pretty` | Pretty-print an `opencode export` session — reuses cc-pretty's renderer and CLI flags via the shared pipeline; the local `convert.py` flattens opencode's part-based messages into cc-pretty records | `opencode-pretty`               |
| `claude_config.config`          | Load `/repos/claude-config/.env` into `os.environ` | (library — `from claude_config.config import load`) |
| `claude_config.ntfy_hook`       | ntfy notification hook for Claude Code          | `agent-tools ntfy-hook`         |
| `claude_config.env_context`     | Print the `# Environment` block for SessionStart hooks under `--system-prompt-file` workflows | `agent-tools env-context` |

### `skills/copy-writing-style/`

Style-matched content generation from any style reference file. 3-phase iterative workflow: (1) extract ranked distinguishing features, (2) draft targeting top features, (3) iterate with self-critique loop (max 3 rounds). Uses `steps.md` with `<!-- step N -->` markers, minimal Python in `scripts/skills/copy_writing_style/do.py`.

### `docs/`

| Path                                       | What                                          | When to read                                            |
| ------------------------------------------ | --------------------------------------------- | ------------------------------------------------------- |
| `opencode-system-prompt/`                  | opencode prompt notes: `alan-default-ids.md` per-delta annotation (`alan-default-commentary.md`), `min-commentary.md` (scope and design rationale for the diagnostic minimum baseline at `opencode/agents/min.md`), `build-self-reported.md` outlining the session prompt assembly | Investigating opencode prompt behavior, `alan-default-ids.md` deltas vs upstream codex gpt-5.5 `base_instructions` (from `/repos/codex/codex-rs/models-manager/models.json`), or why a specific clause is present |
| `system-prompt-anatomy.md`                 | Simplified overview of system prompt assembly — pinned to cc 2.1.88 source | Quick orientation, understanding prompt structure       |
| `system-prompt-anatomy-source-verified.md` | Detailed anatomy with function references — pinned to cc 2.1.88 source     | Debugging context loading, source-level understanding   |
| `system-prompt-snapshot/`                  | Captured system prompts and full API requests — live capture, cc 2.1.235   | Comparing prompt versions, understanding API parameters, spawning a `claude` child that must authenticate |
| `background-sessions.md`                   | How a session moves to the agent view (FleetView), what the fork inherits, disable knobs — cc 2.1.235 | Diagnosing a session that backgrounded itself, or a custom system prompt that stopped applying |
| `tool-token-limits.md`                     | Token counting, truncation, and size limits per tool | Understanding tool output constraints, debugging limits |

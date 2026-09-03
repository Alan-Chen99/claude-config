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
| `statusline.sh`           | Status line script wired up via `settings.json`; its open-tasks row is `agent-tools ps --format statusline` | Customizing the in-session status line        |
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
| `notes/`           | Long-form investigation write-ups — measured evidence and root cause for one behaviour each | Before re-investigating a known failure mode; after finishing an investigation worth keeping |
| `prompt-tests/`    | Runner-neutral prompt evaluation cases                  | Running or grading prompt evaluations             |
| `output-styles/`   | Output formatting styles — the only prompt customization that survives a background handoff | Customizing Claude's output format, writing rules that must hold in every session |
| `sys_prompt/`      | Full replacement prompts loaded via `--system-prompt-file` (not inherited by background sessions) | Editing the launcher's system prompt — see `docs/background-sessions.md` first |
| `scripts/`         | Standalone scripts — `claude.sh` launcher, MITM proxy, `reasoning-probe.py`, `prompt-test-run.sh`, `check-env-context.sh`, `prune-scratch.sh` | Running or modifying utility scripts              |
| `.github/`         | GitHub workflows and config                             | Modifying CI/CD, GitHub-specific settings         |

### `agent-tools/`

Rust binary wrapping skill script and Python tool invocations. Subcommands:

- `agent-tools skill <mod> [args]` — run a skill script via `uv run python3 -m skills.<mod>`
- `agent-tools cc-pretty [args]` — pretty-print Claude Code JSONL session logs. Color is auto-detected (on for TTYs, off when piped or when `NO_COLOR` is set); `--color` forces it on, `--no-color` forces it off.
- `agent-tools cc-pretty-intercept [args]` — pretty-print one MITM intercept log file (`~/.claude/requests-log/<session>/NNNN.json`)
- `agent-tools cc-workflow [args]` — extract sub-agent workflow summary
- `agent-tools ntfy-hook [args]` — Claude Code notification hook (wraps `python3 -m claude_config.ntfy_hook`)
- `agent-tools count-tokens [--model MODEL] [--file PATH] [TEXT]` — count input tokens via Anthropic `count_tokens` API (wraps `python3 -m claude_config.count_tokens`)
- `agent-tools env-context` — SessionStart hook supplying the dynamic context `--system-prompt-file` discards: a `# Environment` block and a `# Scratchpad Directory` section. Reads the hook payload on stdin (`cwd`, `session_id`, and `model` in interactive mode) and emits the `hookSpecificOutput` envelope itself — plain stdout would be injected as `SessionStart hook success: <text>` instead of verbatim. The `Shell` field reports the shell the Bash tool actually runs, not the `$SHELL` Claude Code reports and prints `unknown` for when unset. Warns when Claude Code's own env block drifts from the pinned field set in `docs/env-context-manifest.json`; `scripts/check-env-context.sh` shows the difference.
- `agent-tools opencode [args]` — launch `opencode` with repo `.env` loaded for the opencode Langfuse plugin: maps `OPENCODE_LANGFUSE_SECRET_KEY`, `OPENCODE_LANGFUSE_PUBLIC_KEY`, and `OPENCODE_LANGFUSE_BASE_URL` to the unprefixed vars expected by the plugin (`LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASEURL`), sets git author/committer env to `opencode`, then forwards args to `opencode`. Where both the `.env` and the shell define one of these keys, the `.env` value is the one passed on — matching `src/claude_config/config.py`, which loads the same file with `override=True`; the shell is the fallback for a checkout whose gitignored `.env` is absent, such as a worktree. `opencode-plugin-langfuse` is disabled by default: the `plugin` array in `opencode/opencode.jsonc` is empty, so the mapping stays inert until the plugin is listed there.
- `agent-tools opencode-pretty <session-id> [args]` — pretty-print an opencode session. Mirrors `cc-pretty`'s CLI surface (`--tool-max`, `--truncate-input`, `--no-thinking`, `--show-usage`, `--show-rewound`, `--show-all`, `--chat-only`, `--skeleton`, `--compact-all`, `--compact-leg`, `--agent`, `--validate-only`) and reuses cc-pretty's rendering pipeline. Color is auto-detected (on for TTYs, off when piped or when `NO_COLOR` is set); `--color` forces it on, `--no-color` forces it off. Compaction boundaries (user message with a `compaction` part) become Claude-Code-style `compact_boundary` system records. An uncleaned `session.info.revert` is surfaced via the rewind marker — opencode normally deletes the abandoned tail on the next prompt, so only revert states caught before that prompt show up here.
- `agent-tools opencode.gate` — prompt gate used by opencode agent instructions; accepts stdin/heredoc input, prints gate instructions to stdout, and exits successfully.
- `agent-tools claude [args]` — launch Claude Code against this checkout's binary, hooks, system prompt, and output style without installing them, forwarding `args` to `claude`. Refuses to run from the installed checkout, which `claude.sh` already serves. See `agent-tools/CLAUDE.md`, "Launching an uninstalled checkout".
- `agent-tools run [--desc "<text>"] [--background] [--hide-cmdline] [--drain-cap-bytes N] <cmd> [args..]` — run a command inside this session's scope, capturing both streams to disk and reporting the child's fate to the agent out-of-band through the `hook-post` / `hook-prompt` status channel. The wrapper forwards the child's bytes unchanged and exits with the child's own code, so it stands in for the bare command. `--background` returns as soon as the child has started, prints one line — `<capture_dir>  wrapper pid <n>  child pid <n>` — and detaches the wrapper: it forks, the child calls `setsid`, and the original process exits, so the wrapper is reparented to init and out of the caller's descendant tree — which is the tree the kill at a Bash call's timeout walks. Its exit code means started, not succeeded; the child's own code arrives later on the status channel. A backgrounded run merges both streams into one `output` file and forwards neither, and a start that never happened exits non-zero with the reason on stderr. `--drain-cap-bytes` bounds the capture: from a downstream's refusal for a forwarded run, from the first byte for a backgrounded one, which has no downstream that could refuse. `--desc` names the run in reports, `ps` and the wrapper's `comm`; `--hide-cmdline` keeps `--desc` and the command out of `/proc/*/cmdline` for contamination-sensitive work (see `agent-tools/CLAUDE.md`).
- `agent-tools ps [--format <json|text|statusline>] [--all] [--events] [--task <tool_use_id>] [--session-id <id>]` — report what this session's wrapped runs are doing. JSON by default: an envelope of `now`, `session`, `live` and `withheld`, with `settled` present only under `--all`. Live captures only, because a long session is mostly settled captures and their detail displaces what is still running from a size-limited tool result — 30 terminal captures with nothing live render 193 bytes by default against 15,516 with `--all`, and the withheld ones stay counted by key so none of them vanishes. `--events` adds the chronological event log to `--format text`, off by default because it was more than half the output while answering a different question; at any other format there is no event log to add and the flag says so on stderr rather than parsing into silence. `--format text` is the human-readable rendering; `--format statusline` is the one-line form `statusline.sh` consumes. No format commits the ledger, so reading `ps` never retires a change the push report still owes the agent.
- `agent-tools run-core --capture-dir <dir> [--drain-cap-bytes N] -- <cmd>` — the same run as `run`, without the scope, the ledger, the hooks or `AGENT_TOOLS_PARENT_DIR`. Every passthrough property is a property of processes, so testing one means driving a real binary; this is that binary, and it agrees with `run` byte for byte on both forwarded streams and on the exit code. A disagreement is a defect in whichever is wrong. The system prompt deliberately does not teach it — agents should reach for `run`, which is the one that reports.

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

### `settings.json` — `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`

`env` sets `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`, which makes every subagent run in
the foreground and return its report as the tool result of the call that launched it.

The flag is the only lever that does this. Claude Code decides subagent backgrounding in
the Agent tool with a disjunction whose terms include the fork-subagent feature gate, and
that gate is on by default; a `run_in_background: false` supplied by the model or injected
by a `PreToolUse` hook is therefore ignored. Only this flag cancels the disjunction. Turning
the fork gate off instead (`CLAUDE_CODE_FORK_SUBAGENT=0`) also restores foreground agents,
at the cost of the `fork` subagent type. Measured evidence and the source reading are in
`notes/subagent-backgrounding-overrides-run-in-background.md`.

What the flag costs, in the same session:

| Effect | Consequence |
| --- | --- |
| Bash loses `run_in_background` | A long command needs `agent-tools run --background`, which returns on the start and detaches; a bare `&` needs `timeout <s> tail --pid=<pid> -f /dev/null` to wait |
| A Bash command outliving its `timeout` is killed, not backgrounded | The kill reaches the call's live descendants — `&`, `nohup` and `setsid --wait` children included — so a job started that way survives only a call that returns on its own. It does not reach a process already reparented to init, which is where a bare `setsid`'s double fork leaves its worker and where `agent-tools run --background` leaves its wrapper. See the backgrounding bullet in `sys_prompt/alan-default-next.md` |
| MCP auto-background, ctrl+b backgrounding, observer agents | Unavailable |
| Skills declaring `background: true` | Run inline |

Foreground `sleep` becomes available, because the block on it is conditioned on background
tasks being enabled. Monitor, `TaskOutput` and `TaskStop` are unaffected, so a Monitor whose
command exits still delivers a completion notification.

The Agent tool's own description continues to say that subagents run in the background and
that a notification follows — that fragment is gated on the fork feature, not on this flag,
so it is emitted while nothing backgrounds. `sys_prompt/alan-default-next.md` contradicts it
explicitly for that reason.

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

It also exports `CLAUDE_CODE_TMPDIR=/root/.claude/tmp`. Claude Code roots its
per-session scratchpad there (`Spe()`, `globals/05.js:8056`), and it names that
path to subagents (`Xff`, `globals/14.js:26405`) whether or not
`--system-prompt-file` drops the section from the main agent's own prompt.
Redirecting the root is therefore the only way both agree on one directory —
and `/root` is a host bind mount, so scratch survives a container rebuild that
`/tmp` would not. The same variable also roots plugin session directories,
skill and plugin zip staging, and the IPC socket directory; Claude Code falls
back to `/tmp` for the socket when the path exceeds the `sun_path` limit
(`SFm()`, `globals/22.js:14393`).

Scratch is now persistent, so nothing reclaims it automatically.
`scripts/prune-scratch.sh` reports and, with `--apply`, deletes empty session
scratchpads.

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
| `claude_config.env_context`     | SessionStart hook: `# Environment` and `# Scratchpad Directory` for `--system-prompt-file` sessions | `agent-tools env-context` |

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
| `agent-tools-status-reference.md`          | Full `agent-tools run` status grammar, passthrough differences from bare, and the kill boundary — the exhaustive half of what `sys_prompt/alan-default-next.md` states in brief; pinned to source by `scripts/check-prompt-coupling.sh` | Reading a status line in detail, diagnosing a wrapped run, or editing either side of the prompt/source coupling |

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
| `.claude/`         | Repo-local Claude Code config. Project-local skills: `prompt-tests` (running/grading prompt evaluations) and `update-claude-code` (the post-Claude-Code-upgrade runbook, the inventory of what a release can break here, and the open items) | Adding repo-local skills, settings, hooks; after a Claude Code upgrade; before writing anything coupled to a Claude Code data shape |
| `agent-tools/`     | Rust binary (`agent-tools`) wrapping skill/tool calls   | Modifying CLI wrappers, adding new commands       |
| `src/claude_config/` | Python package: cc-pretty, cc-workflow, custom tools  | Modifying Python tooling, adding new tools        |
| `skills/`          | Invocable skills (planner, deepthink, etc.)             | Using or modifying skills, adding new skills      |
| `agents/`          | Sub-agent definitions (developer, architect)            | Customizing agent behavior, understanding roles   |
| `conventions/`     | Documentation and code quality standards                | Writing documentation, understanding coding rules |
| `plans/`           | Plan storage directory                                  | Reviewing or executing existing plans             |
| `notes/`           | Long-form investigation write-ups — measured evidence and root cause for one behaviour each | Before re-investigating a known failure mode; after finishing an investigation worth keeping |
| `prompt-tests/`    | Runner-neutral prompt evaluation cases                  | Running or grading prompt evaluations             |
| `output-styles/`   | Output formatting styles — the only prompt customization that survives a background handoff | Customizing Claude's output format, writing rules that must hold in every session |
| `sys_prompt/`      | Full replacement prompts loaded via `--system-prompt-file` (not inherited by background sessions) | Editing the launcher's system prompt — read `sys_prompt/CLAUDE.md` (conciseness rule, the reasoning behind individual lines, and the upstream rebase) and `docs/background-sessions.md` first; after a Claude Code upgrade |
| `scripts/`         | Standalone scripts — `claude.sh` launcher, MITM proxy, `reasoning-probe.py`, `check-env-context.sh`, `check-prompt-upstream.py` (pins the passages `sys_prompt/` borrowed from Claude Code's own prompt), `prune-scratch.sh` (frees scratch disk space), and the prompt-test runners: `prompt-test-cc.sh` (Claude Code, the standard one for `sys_prompt/`), `prompt-test-cc-downstream.sh` (feeds a run's artifact to the reader it was written for), `prompt-test-run.sh` (opencode) | Running or modifying utility scripts              |
| `.github/`         | GitHub workflows and config                             | Modifying CI/CD, GitHub-specific settings         |

### `agent-tools/`

Rust binary wrapping skill script and Python tool invocations. Subcommands:

- `agent-tools skill <mod> [args]` — run a skill script via `uv run python3 -m skills.<mod>`
- `agent-tools cc-pretty [args]` — pretty-print Claude Code JSONL session logs. Color is auto-detected (on for TTYs, off when piped or when `NO_COLOR` is set); `--color` forces it on, `--no-color` forces it off.
- `agent-tools cc-pretty-intercept [args]` — pretty-print one MITM intercept log file (`~/.claude/requests-log/<session>/NNNN.json`)
- `agent-tools cc-render-coverage [--quiet] [--max-findings N] [PATH..]` — report content `cc-pretty` / `cc-pretty-intercept` fails to show. Renders each log at `--tool-max 1000000000` and emits one of three findings per defect: `load_error` (the file did not load at all), `renderer_truncation` (a `[N more chars]` marker the renderer produced at that unbounded limit, i.e. a hardcoded character cap ignoring the flag — markers already in the source are subtracted, because sessions here capture cc-pretty's own output as tool results), and `missing_content` (a content string in the source that is absent from the render). Paths ending `.jsonl` go through cc-pretty, anything else through the intercept renderer; with no paths it reads them from stdin. Exits non-zero when anything is found. Needles come from conversation content only — request messages plus the response for a capture, assistant/user message blocks for a session — so a clean run does not speak for JSONL attachment, progress or system records, several of which render as deliberate one-line summaries; `renderer_truncation` still covers them because it reads the whole render. Findings and pins live in `tests/test_render_coverage.py`.
- `agent-tools cc-workflow [args]` — extract sub-agent workflow summary
- `agent-tools ntfy-hook [args]` — Claude Code notification hook (wraps `python3 -m claude_config.ntfy_hook`)
- `agent-tools count-tokens [--api] [--model MODEL] [--file PATH] [TEXT]` — count tokens in text (wraps `python3 -m claude_config.count_tokens`). Two backends that do not measure the same thing, so a count is only comparable to others taken the same way. The default is local and offline: the Qwen3.8 tokenizer vendored at `src/claude_config/tokenizer_data/`, counting the text and nothing else. `--api` instead returns the Anthropic `count_tokens` `input_tokens` for a request carrying the text as one user message, which adds a per-message envelope of ~11 tokens — `"hello world"` is 2 locally and 14 over the API. The tokenizers then diverge on top of the envelope, from −19% on deeply indented code to −61% on Chinese, because the Opus 4.7-and-later tokenizer is far coarser than current open-source ones — on `sys_prompt/alan-default-next.md`, Opus 5 and Sonnet 5 both report 10,002 and Opus 4.7 reports 10,007, while Haiku 4.5's older tokenizer reports 7,113, next door to Qwen3.8's 6,654. No scale factor reconciles them. Prefer `--api` whenever the number stands for Claude context consumed, such as a prompt-size budget; prefer the default for everything else, and note that it is the only backend that works in a worktree, whose gitignored `.env` is absent so no credential resolves. `--model` selects the Claude model for `--api` and defaults to `claude-opus-4-7` — where the recorded measurements in `docs/` and `notes/` were taken, kept there so they stay reproducible; passing it without `--api` is an error rather than a silently-ignored flag. The vendored tokenizer is checked against the sha256 in its `PROVENANCE.json` on every run, so a swapped or truncated file raises instead of quietly reporting different numbers. Unlike the other pass-through subcommands, `--help` is forwarded to the Python parser (`disable_help_flag`), because that help carries the backend warning.

  Re-vendoring the tokenizer: download `tokenizer.json` from the `source`/`revision` in `PROVENANCE.json`, replace the file, then regenerate `PROVENANCE.json` (`sha256`, `bytes`, `vocab_size`, `revision`, `retrieved`). `tests/test_count_tokens.py` pins exact counts for known strings, so a swap that changes tokenization fails there rather than silently re-basing every future measurement.
- `agent-tools env-context` — SessionStart hook supplying the dynamic context `--system-prompt-file` discards: a `# Environment` block and a `# Scratchpad Directory` section. Reads the hook payload on stdin (`cwd`, `session_id`, `model` when present). Whether `model` is present depends on which internal call site fired the hook, not on `source` or interactive-vs-print: a fresh interactive startup, an in-app session resume/fork, and `compact` each pass one, while a process-launched `--resume`/`--continue` and `/clear` do not — and that no-model resume path shares the identical `source: "resume"` label with the one that does, so `source` cannot predict it either; there is no clean rule to state, so the hook treats it as always possibly absent. The payload builder is `uIn` (`src/chunk-dbb93264.js:226451`), which takes `model` as an optional positional; which call sites pass one was traced against 2.1.235 and has not been re-traced for 2.1.269. It emits the `hookSpecificOutput` envelope itself — plain stdout would be injected as `SessionStart hook success: <text>` instead of verbatim. The `Shell` field reports the shell the Bash tool actually runs, not Claude Code's own `$SHELL` reading. Claude Code falls back to the literal `unknown` when `$SHELL` is unset; this hook never does — when no shell resolves at all it says so explicitly (`"none found — no bash or zsh on this system, so Bash tool calls will fail"`). Warns when Claude Code's own env block drifts from the pinned field set in `docs/env-context-manifest.json`; `scripts/check-env-context.sh` shows the difference. Since 2.1.269 cc sends its own `# Environment` block to `--system-prompt-file` sessions too, as a `messages[]` attachment rather than a system-prompt section, and it has no separate `# Scratchpad Directory` section any more — the scratchpad is a bullet inside that block. The hook therefore now duplicates most of what cc supplies; what it still uniquely adds is the shell the Bash tool actually runs, the session id, the worktree's parent checkout, and the drift note. Whether to trim it to those is an open question, not a settled design.
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

### `settings.json` — `CLAUDE_CODE_FORK_SUBAGENT` and the `Agent` hook

`env` sets `CLAUDE_CODE_FORK_SUBAGENT=0`, and a `PreToolUse` hook on `Agent` rewrites
`run_in_background` to `false` on every call. Together they make every subagent run in the
foreground and return its report as the tool result of the call that launched it.

Neither half works alone. Claude Code decides subagent backgrounding in the Agent tool with
a disjunction (`q4o`, `src/chunk-dbb93264.js:103955-103969`): the fork-subagent gate is one
term, and the last term is `run_in_background !== false`, which holds whenever the parameter
is omitted. Turning the gate off without the hook still backgrounds, and the hook without
the gate turned off is outvoted by the gate. The price is the `fork` subagent type, which
disappears outright — `Agent type 'fork' not found. Available agents: …`.

Two terms of that disjunction the hook cannot outvote: an agent definition declaring
`background: true` of its own, and `isolation: "remote"`, which sits outside the
background-tasks guard entirely. No agent in `agents/` declares either, so neither is
reachable here today; both would be, the moment one did.

`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` is the alternative. It holds subagents foreground
on its own — bar a remote-isolation launch, which runs async regardless — with no hook, and
keeps `fork`; what it costs instead is the whole
background-task facility, a far larger loss than `fork`. Measured in one interactive session
each:

| | `DISABLE_BACKGROUND_TASKS=1` | `FORK_SUBAGENT=0` + hook |
| --- | --- | --- |
| Bash `run_in_background` | absent from the schema | present; returns a task id and re-invokes the agent when the command exits |
| A command outliving its `timeout` | killed, `Exit code 143` | moved to the background with a task id, unless its first statement starts with `sleep`, which is still killed |
| `BACKGROUNDED:` from `hook_post.rs` | cannot fire, since no tool response carries `backgroundTaskId` | fires, naming the cause and the task id |
| `subagent_type: "fork"` | available | `Agent type 'fork' not found` |
| Foreground `sleep` | permitted | the Bash description says it is blocked, and to use Monitor with an until-loop |

Source only, not exercised under either setting: MCP auto-background
(`src/chunk-jtrs4f58.js:255`), the Ctrl+B backgrounding affordance
(`src/chunk-qxhez8yz.js:99`, with the keybinding itself at `:32`), observer agents (`Zfe`,
`src/chunk-dbb93264.js:74088`), and forked skills (`y9t`,
`src/chunk-dbb93264.js:173976`). All four still ship in 2.1.269, and each opens on the same
`rc()` background-tasks check, so each returns under the current setting — re-read against
this version rather than carried over from the 2.1.235 reading in
`notes/subagent-backgrounding-overrides-run-in-background.md`.

The skill half is not opt-in as that note has it: `background` defaults to true for any
skill declaring `context: fork`, and `background: false` is the opt-out that keeps the
caller waiting (`src/chunk-dbb93264.js:54434`).

`CLAUDE_AUTO_BACKGROUND_TASKS` is a third knob neither setting covers: set, it moves a
foreground subagent to the background after its interval (`iTs`,
`src/chunk-dbb93264.js:171747`, wired at `:172571`). Unset here, so inert — but it means
the gate-plus-hook pair guarantees a synchronous subagent only in an environment that
leaves it unset.

The Agent tool's own description says subagents run in the background by default and that a
notification follows. The hook makes that false, so `sys_prompt/alan-default-next.md`
contradicts it explicitly.

Measured evidence and the source reading are in
`notes/subagent-backgrounding-overrides-run-in-background.md`.

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

It also exports `CLAUDE_CODE_TMPDIR="$HOME/.claude/tmp"`. Claude Code roots its
per-session scratchpad there (`AS()`, `src/chunk-tht8x923.js:19`), for the main
agent and for subagents alike, so redirecting the root is the only way both
agree on one directory —
under `$HOME` rather than `/tmp` because `/tmp` is container overlay and is lost
on a rebuild, while this container's home is a host bind mount. The same
variable also roots plugin session directories, skill and plugin zip staging,
the IPC socket directory, and entries in the sandbox write allowlist. The
socket actually roots at `XDG_RUNTIME_DIR` when that is set, falling back to
this variable only when it is not (`jxr()`, `src/chunk-g92e0w45.js:567`), and either
way falls back further to `/tmp` when the resulting path exceeds the `sun_path`
limit.

Scratch is persistent, so nothing reclaims it automatically.
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
| `claude_config.cc_pretty.coverage` | Coverage check: content the renderers fail to show at unbounded `--tool-max` | `cc-render-coverage` |
| `claude_config.config`          | Load `/repos/claude-config/.env` into `os.environ` | (library — `from claude_config.config import load`) |
| `claude_config.ntfy_hook`       | ntfy notification hook for Claude Code          | `agent-tools ntfy-hook`         |
| `claude_config.env_context`     | SessionStart hook: `# Environment` and `# Scratchpad Directory` for `--system-prompt-file` sessions | `agent-tools env-context` |

### `skills/copy-writing-style/`

Style-matched content generation from any style reference file. 3-phase iterative workflow: (1) extract ranked distinguishing features, (2) draft targeting top features, (3) iterate with self-critique loop (max 3 rounds). Uses `steps.md` with `<!-- step N -->` markers, minimal Python in `scripts/skills/copy_writing_style/do.py`.

### `skills/playwright-cli/`

Vendored from the `@playwright/cli` npm package, not hand-written. Generated from upstream tag `v0.1.18` by `playwright-cli install --skills --global`, which writes through the `~/.claude/skills` symlink into this repo.

`git diff` is the only drift signal: the CLI's own staleness check (`skillCheck.js`) inspects cwd-relative `.claude/skills` only, so a `--global` install is never warned about. After `npm update -g @playwright/cli`, re-run the install and review the diff.

The binary itself is installed by the container image (`/workspace/docker/Dockerfile`), not by this repo.

### `docs/`

| Path                                       | What                                          | When to read                                            |
| ------------------------------------------ | --------------------------------------------- | ------------------------------------------------------- |
| `opencode-system-prompt/`                  | opencode prompt notes: `alan-default-ids.md` per-delta annotation (`alan-default-commentary.md`), `min-commentary.md` (scope and design rationale for the diagnostic minimum baseline at `opencode/agents/min.md`), `build-self-reported.md` outlining the session prompt assembly | Investigating opencode prompt behavior, `alan-default-ids.md` deltas vs upstream codex gpt-5.5 `base_instructions` (from `/repos/codex/codex-rs/models-manager/models.json`), or why a specific clause is present |
| `system-prompt-anatomy.md`                 | Simplified overview of system prompt assembly — pinned to cc 2.1.88 source | Quick orientation, understanding prompt structure       |
| `system-prompt-anatomy-source-verified.md` | Detailed anatomy with function references — pinned to cc 2.1.88 source     | Debugging context loading, source-level understanding   |
| `system-prompt-snapshot/`                  | Captured system prompts and full API requests — live capture, cc 2.1.269. Directories are keyed by the model id the request carried (`opus-5/`, `opus-4-7/`, `sonnet-5/`, `fable-5/`), because cc serves two different default prompts and picks per model, not per version: the compressed `# Harness` one goes to models whose registry entry declares the `lean_prompt` capability (opus-5, opus-4-8, fable-5, fable-5-1, mythos-5-1), the older multi-section one to everything else including every sonnet and opus-4-7. Which models answer at all is an account entitlement, not a version fact — fable returned HTTP 429 "requires usage credits" until the subscription was upgraded, and mythos-5 still returns 404 | Comparing prompt versions, understanding API parameters, spawning a `claude` child that must authenticate |
| `background-sessions.md`                   | How a session moves to the agent view (FleetView), what the fork inherits, disable knobs — cc 2.1.269 | Diagnosing a session that backgrounded itself, or a custom system prompt that stopped applying |
| `tool-token-limits.md`                     | Token counting, truncation, and size limits per tool | Understanding tool output constraints, debugging limits |
| `agent-tools-status-reference.md`          | Full `agent-tools run` status grammar, passthrough differences from bare, and the kill boundary — the exhaustive half of what `sys_prompt/alan-default-next.md` states in brief; pinned to source by `scripts/check-prompt-coupling.sh` | Reading a status line in detail, diagnosing a wrapped run, or editing either side of the prompt/source coupling |
| `env-context-manifest.json`                | Pinned cc version and env-block literal set `agent-tools env-context`'s drift check is pinned to; re-pin with `scripts/check-env-context.sh --update` after a Claude Code upgrade. Byte-offset derivation for the two literal lists: `notes/env-context-manifest.md` | Reviewing or re-pinning after a drift warning |

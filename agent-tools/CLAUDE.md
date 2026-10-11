# agent-tools/

Rust binary behind every `agent-tools` subcommand: the Claude Code hooks, the wrapped-run status channel (`run`, `ps`), and the `claude` and `opencode` launchers. The rest pass through to `src/claude_config/` (`skill` to `skills/scripts`), whose module docstrings carry their behaviour. A pass-through's own flags print with `agent-tools <sub> -- --help`: a bare `--help` reaches clap's stub, except for `count-tokens`.

## Files

| File | What | When to read |
| --- | --- | --- |
| `README.md` | What no single file says: an uninstalled checkout's launch traps, the renderers' selection predicates, the ledger's commit rules, `TaskStop`, merge admission | Launching a worktree session; adding a renderer; changing the ledger or merge rule |
| `tests/` | Integration tests driving the built binary | Adding or running a test |

## Source (`src/`)

| File | What | When to read |
| --- | --- | --- |
| `main.rs` | clap surface, root resolution, dispatch, the opencode gate strings | Adding a subcommand or flag |
| `run.rs`, `core.rs`, `capture.rs` | `run`'s scope, capture dir and `meta.json`; the spawn/tee/drain core it shares with `run-core`, merge rule included; one stream's tee | Changing how a wrapped run starts, captures or forwards |
| `background.rs`, `signals.rs` | `--background`'s fork, `setsid` and readiness pipe (the only `unsafe`); signal forwarding | Changing detach or signals |
| `status.rs`, `psrecord.rs`, `ps.rs`, `statusline.rs` | Status derived from disk, and its line; the record the json and statusline renderers share; `ps` | Changing a key, a line, or `ps` output |
| `hook_pre.rs`, `hook_post.rs`, `hook_prompt.rs` | `PreToolUse` rewrite into a wrapped run; the report on `PostToolUse`/`PostToolUseFailure` and `UserPromptSubmit` | Changing what a hook rewrites or reports |
| `hook_subagent.rs`, `hook_provenance.rs`, `hook_input.rs` | `SubagentStart` Required-notes ask; the launch record the model never sees; hook payloads | Changing those hooks |
| `ledger.rs`, `events.rs`, `meta.rs`, `paths.rs` | What the agent was last told; the `ps --events` log; `meta.json` and `escape_control`; state root and scope | Touching reporting state or a rendered field |
| `procname.rs`, `procstat.rs` | `comm` and `--hide-cmdline`; `/proc/<pid>/stat`, read lossily | Changing process naming or liveness |
| `claude.rs`, `opencode.rs` | The two launchers | Launching a checkout or opencode |

## Build and test

```bash
cargo build --release && cargo test
CLAUDE_CONFIG_ROOT=/path/to/worktree ./target/release/agent-tools <sub> [args...]
```

`~/.local/bin/agent-tools` is the canonical checkout's build and `install.sh` refuses a worktree, so a worktree runs its own binary as above.

## Agent policy

- `settings.json` is live once a merge lands, before `install.sh` rebuilds, and a hook naming a subcommand the installed build lacks exits 2: that denies a `PreToolUse` call, refuses a `UserPromptSubmit` prompt and keeps a `Stop` turn from ending. Hence `hook-provenance || true`: the hook never fails, but clap and root resolution run first.
- A string the system prompt or `docs/agent-tools-status-reference.md` quotes has a needle in `scripts/check-prompt-coupling.sh`, plus a `// PROMPT-COUPLED` marker in the three files it counts: emitter, needle and quoting sentence change together. `GATE_STDOUT`/`MIN_GATE_STDOUT` are unpinned: edit them with `opencode/agents/alan-default-ids.md`/`min.md`.
- `run-core` is `run` without scope, ledger or hooks, identical in both streams and exit code so its tests vouch for `run`; agents use `run`. The hidden `background-probe` serves `tests/` alone.
- `run --hide-cmdline` hides the wrapper's argv and `--desc`; the child's own `/proc/<pid>/cmdline` still shows its command.
- `count-tokens`: `--api` when the number stands for Claude context consumed, the offline default otherwise (the only one a worktree, lacking `.env`, can run). Re-vendor from `PROVENANCE.json`'s `source`/`revision`, then regenerate its `sha256`, `bytes`, `vocab_size`, `revision`, `retrieved`.
- `cc-replay send` is a real, billed call, spending the 5h/7d window under OAuth, which refuses a replaced `system`: that needs `--credential-env ANTHROPIC_TOKEN_COUNT_API_KEY --credential-header x-api-key`, exported first.

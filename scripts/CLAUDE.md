# scripts/

Standalone scripts: the launcher, the drift and coupling guards, the prompt-test runners,
and one-off probes.

## Files

| File                          | What                                                                                          | When to read                                                       |
| ----------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `claude.sh`                   | The launcher — git identity, `IS_SANDBOX`, agent-view and proxy env, then `exec claude --system-prompt-file sys_prompt/alan-default-next.md` | Changing how sessions start; diagnosing a session whose prompt, proxy or scratch root is wrong |
| `check-prompt-coupling.sh`    | Fails when a string `agent-tools` emits drifts from the system prompt that teaches the agent to recognize it | Editing an emitted literal in `hook_post.rs`/`status.rs`, or the prompt bullets quoting them |
| `check-prompt-upstream.py`    | Pins the passages `sys_prompt/` and the env-context hook borrowed verbatim from Claude Code's own prompt | After a Claude Code upgrade; before editing a borrowed passage      |
| `check-env-context.sh`        | Reports when cc's own env block drifts from the field set `agent-tools env-context` is pinned to; `--update` re-pins the manifest | After an env-context drift warning; re-pinning after an upgrade     |
| `prune-scratch.sh`            | Reports and, with `--apply`, deletes empty session scratchpads under cc's tmp root; `--session <id>` has no liveness check | Freeing scratch disk space                                          |
| `prompt-test-cc.sh`           | Runs one `prompt-tests/general/` case under Claude Code against a full-replacement prompt — the standard runner for `sys_prompt/` | Running a prompt test                                              |
| `prompt-test-cc-leg2.sh`      | Sends a case's second-leg instruction into the session leg 1 left behind (a second turn, not a second session) | Running a two-leg case                                              |
| `prompt-test-cc-downstream.sh`| Feeds a run's artifact to the reader it was written for, in a fresh empty config dir         | Grading an artifact a case produced for a downstream reader          |
| `prompt-test-run.sh`          | The opencode runner for the same cases                                                        | Running a prompt test against opencode                              |
| `reasoning-probe.py`          | Probes a reasoning-visible model via OpenRouter with a spec + task pair, returning the trace verbatim — opencode-served gpt-5.5 returns heading-only summaries | Investigating a finding that needs paragraph-level reasoning        |
| `strip-frontmatter.py`        | Writes a sibling `-clean.md` without YAML frontmatter — opencode's `{file:PATH}` inlines frontmatter into the prompt as instruction text | Preparing a spec for `{file:...}` inclusion                         |
| `ralph.sh`                    | Launches `ralph run` against `/workspace/ralph/build.yml` under the `Claude(Ralph)` git identity | Running the ralph loop                                              |

## Subdirectories

| Directory    | What                                                        | When to read                                      |
| ------------ | ----------------------------------------------------------- | ------------------------------------------------- |
| `intercept/` | MITM proxy that captures every API request to `~/.claude/requests-log/`; its `README.md` carries the port, the CA setup and the streaming watchdog | Capturing requests; diagnosing an intercepted session whose turns abort |

## `claude.sh` — the launcher

Exports the `Claude` git identity, sets `IS_SANDBOX=1` and
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
`prune-scratch.sh` reports and, with `--apply`, deletes empty session
scratchpads.

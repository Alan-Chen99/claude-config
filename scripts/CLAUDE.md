# scripts/

Standalone scripts: the launcher, the drift and coupling guards, the prompt-test runners,
and one-off probes.

## Files

| File                          | What                                                                                          | When to read                                                       |
| ----------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `claude.sh`                   | The launcher — git identity, `IS_SANDBOX`, agent-view and proxy env, then `exec claude --system-prompt-file sys_prompt/alan-default-next.md` | Changing how sessions start; diagnosing a session whose prompt, proxy or scratch root is wrong |
| `kimi.sh`                     | Kimi launcher — Moonshot provider env and the `Claude(Kimi)` git identity, then `claude.sh` for the rest | Running a session on Kimi; diagnosing one that reached Anthropic, sized its context wrong, or committed under the wrong name |
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
| `intercept/` | MITM proxy that captures conversation-shaped API calls to `~/.claude/requests-log/` — only from sessions `claude.sh` launched while it was listening; its `README.md` carries the port, the CA setup, the streaming watchdog and the four things a capture cannot record | Capturing requests; diagnosing an intercepted session whose turns abort; judging what a missing capture means |

## `kimi.sh` — the Kimi launcher

Exports the provider environment for Moonshot's Anthropic-compatible endpoint at
`https://api.kimi.ai/coding/`, then `exec`s the sibling `claude.sh`, which
supplies everything a session needs whatever serves it —
`IS_SANDBOX`, the agent-view flag, the scratch root, the proxy probe and the
system prompt. It resolves that sibling through `readlink -f` on its own path,
the same way `claude.sh` resolves the prompt, so an installed `kimi.sh` runs the
canonical pair and a worktree copy invoked by path runs that worktree's. What it
does not inherit is the git identity: it exports `CLAUDE_SH_AUTHOR_NAME`, so a
Kimi session commits as `Claude(Kimi)` and a commit says which model made it.

The key comes from `KIMI_API_KEY` in the environment, and nothing is read off
disk. `docker-compose.yml` gives the `personal-env` service `env_file:
../.env`, so every line of `/workspace/.env` is exported before any shell
starts — which also means a key added to that file while the container is up is
not there until a restart, and the failure message says so. The same `env_file`
exports `CLAUDE_CODE_OAUTH_TOKEN`, so the script unsets it, and
`ANTHROPIC_API_KEY` with it, leaving `ANTHROPIC_AUTH_TOKEN` as the one
credential in play rather than an Anthropic one sitting in the environment of a
session pointed at Kimi. `ANTHROPIC_API_KEY` would authenticate too — the endpoint takes the key as
`x-api-key` or as `Authorization: Bearer` — but it is also what Claude Code's
`customApiKeyResponses` list in `~/.claude.json` keys on, so it brings an
approval decision along with it.

`KIMI_MODEL` defaults to `k3[1m]`. The bracket is Claude Code syntax, not part
of the id: the API rejects `k3[1m]` outright (*"Please set model id as `k3`"*),
while claude sends `k3` and reports a 1,000,000-token window. All five tier
variables and `CLAUDE_CODE_SUBAGENT_MODEL` are pinned to that one model. The
endpoint answers to any model string — `sonnet` and `claude-opus-4-5` both
return 200 and echo the name back — so a tier left unmapped does not fail, it
quietly takes whatever window Claude Code sizes for that Anthropic name.

`CLAUDE_CODE_MAX_CONTEXT_TOKENS` and `CLAUDE_CODE_AUTO_COMPACT_WINDOW` are both
derived from the model rather than set independently, so they cannot drift apart
from it or from each other. Stating them is load-bearing for any id without the
`[1m]` suffix: Claude Code reads a size off the model name and falls back to
200,000 for a name it does not recognize — measured, `k3-256k` reported a
200,000-token window with these unset, 62,144 short of what it serves. An id
outside the known set is a hard failure unless `KIMI_CONTEXT_TOKENS` is set
alongside it.

Available on this subscription: `k3[1m]` (1,048,576), `kimi-for-coding`
(1,048,576), `k3-256k` (262,144). `kimi-for-coding-highspeed` returns 401,
*"Your current subscription does not have access"* (checked 2026-09-24).

## `claude.sh` — the launcher

Exports the git identity — `Claude`, or whatever `CLAUDE_SH_AUTHOR_NAME` names,
which is how `kimi.sh` commits as `Claude(Kimi)`. The name is fixed against the
ambient environment rather than defaulted from it, so a `GIT_AUTHOR_NAME`
already in the shell cannot reach a commit; that variable is the only input
taken. Sets `IS_SANDBOX=1` and
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

# scripts/

Standalone scripts: the launcher, the drift and coupling guards, the prompt-test runners,
and one-off probes.

## Files

| File                          | What                                                                                          | When to read                                                       |
| ----------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `claude.sh`                   | The launcher — git identity, `IS_SANDBOX`, agent-view and proxy env, then `exec claude --system-prompt-file sys_prompt/alan-default-next.md` | Changing how sessions start; diagnosing a session whose prompt, proxy or scratch root is wrong |
| `kimi.sh`                     | Kimi launcher — Moonshot provider env and the `Claude(Kimi)` git identity, then `claude.sh` for the rest | Running a session on Kimi; diagnosing one that reached Anthropic, sized its context wrong, or committed under the wrong name |
| `zai.sh`                      | GLM launcher — Z.ai provider env, the split opus/sonnet-vs-haiku model mapping and the `Claude(GLM)` git identity, then `claude.sh` for the rest | Running a session on GLM; diagnosing one that reached Anthropic, sized its context wrong, or committed under the wrong name |
| `check-prompt-coupling.sh`    | Fails when a string `agent-tools` emits drifts from the system prompt that teaches the agent to recognize it | Editing an emitted literal in `hook_post.rs`/`status.rs`, or the prompt bullets quoting them |
| `check-prompt-rationale.sh`   | Fails when a `sys_prompt/CLAUDE.md` rationale section quotes no text the prompt still carries; the one check in CI that bounds a document by another document | Deleting or rewording a prompt line; adding a section to that file |
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

## Provider launchers — `kimi.sh` and `zai.sh`

Each exports the provider environment for an Anthropic-compatible endpoint and
then `exec`s the sibling `claude.sh`, which supplies everything a session needs
whatever serves it — `IS_SANDBOX`, the agent-view flag, the scratch root, the
proxy probe and the system prompt. Each resolves that sibling through
`readlink -f` on its own path, the same way `claude.sh` resolves the prompt, so
an installed launcher runs the canonical pair and a worktree copy invoked by
path runs that worktree's. What neither inherits is the git identity: each
exports `CLAUDE_SH_AUTHOR_NAME`, so a commit says which model made it.

The key comes from the environment — `KIMI_API_KEY`, `ZAI_API_KEY` — and
nothing is read off disk. `docker-compose.yml` gives the `personal-env` service
`env_file: ../.env`, so every line of `/workspace/.env` is exported before any
shell starts, which also means a key added to that file while the container is
up is not there until a restart; the failure message says so. The same
`env_file` exports `CLAUDE_CODE_OAUTH_TOKEN`, so each script unsets it, and
`ANTHROPIC_API_KEY` with it, leaving `ANTHROPIC_AUTH_TOKEN` as the one
credential in play rather than an Anthropic one sitting in the environment of a
session pointed somewhere else. `ANTHROPIC_API_KEY` would authenticate too —
both endpoints take the key as `x-api-key` or as `Authorization: Bearer` — but
it is also what Claude Code's `customApiKeyResponses` list in `~/.claude.json`
keys on, so it brings an approval decision along with it.

Every tier variable is stated, `CLAUDE_CODE_SUBAGENT_MODEL` included. Both
endpoints answer to any model string — `sonnet` and `claude-opus-4-5` both
return 200 and echo the name back — so a tier left unmapped does not fail, it
quietly takes whatever window Claude Code sizes for that Anthropic name.

`[1m]` is Claude Code syntax rather than part of an id. cc strips it before the
request (`Gt()`, `/\[1m\]$/i`) and both APIs reject it unstripped — Kimi with
*"Please set model id as `k3`"*, Z.ai with 400 `[1211][Unknown Model, please
check the model code.]`. It is also the whole window story for an id carrying
it: `Sz()` returns exactly 1,000,000 for the `[1m]` form and short-circuits
ahead of `CLAUDE_CODE_MAX_CONTEXT_TOKENS`, which is therefore consulted only for
an id without the suffix. Such an id otherwise lands on cc's 200,000 fallback
for a name it does not recognize — measured, `k3-256k` reported a 200,000-token
window with the variable unset, 62,144 short of what it serves — so each
launcher refuses one unless told its size.

### `kimi.sh` — Moonshot

Endpoint `https://api.kimi.ai/coding/`, git identity `Claude(Kimi)`. `KIMI_MODEL`
defaults to `k3[1m]` and every tier is pinned to that one model.
`CLAUDE_CODE_MAX_CONTEXT_TOKENS` and `CLAUDE_CODE_AUTO_COMPACT_WINDOW` are
derived from the model so they cannot drift apart from it or from each other; an
id outside the known set is a hard failure unless `KIMI_CONTEXT_TOKENS` is set
alongside it.

Available on this subscription: `k3[1m]`, `kimi-for-coding` (1,048,576),
`k3-256k` (262,144). `kimi-for-coding-highspeed` returns 401, *"Your current
subscription does not have access"* (checked 2026-09-24). The table's 1,048,576
reaches a session only through `kimi-for-coding`: for `k3[1m]` the suffix
already answers, at 1,000,000, and cc caps `CLAUDE_CODE_AUTO_COMPACT_WINDOW`
there too.

### `zai.sh` — Z.ai

Endpoint `https://api.z.ai/api/anthropic`, git identity `Claude(GLM)`. The GLM
Coding Plan serves two models and Z.ai's own Claude Code mapping splits the
tiers between them, which `zai.sh` follows: `ZAI_MODEL`, default `glm-5.3[1m]`,
takes opus, sonnet, fable and the subagent default; `ZAI_HAIKU_MODEL`, default
`glm-5.3-flash[1m]`, takes haiku. Flash is the multimodal one and GLM-5.3 is
text-only, so an image reaches a model that can read it only on the haiku tier.
Both defaults carry `[1m]`, so neither needs `CLAUDE_CODE_MAX_CONTEXT_TOKENS`;
overriding either with a plain id requires `ZAI_CONTEXT_TOKENS`, one number
shared by every tier.

`API_TIMEOUT_MS` is raised to Z.ai's published figure of 3,000,000 ms from cc's
600,000 ms default; whether a turn ever reaches the default is unmeasured, so
that is a recommendation followed, not a fault fixed.
`CLAUDE_CODE_EFFORT_LEVEL` is deliberately left alone, unlike `kimi.sh`, which
pins it to `high`. Unset is what selects Z.ai's `max`, the level they recommend
for coding: a captured request carries `output_config {"effort": "max"}` and
`thinking {"type": "adaptive"}`, and Z.ai resolves both to max.
`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, which Z.ai's manual configuration
also sets, is not set here — it gates Claude Code's telemetry and error
reporting, none of which goes to `ANTHROPIC_BASE_URL`, so it changes nothing
about reaching Z.ai.

Measured on cc 2.1.269, from a `-p` run's `result` record: `canonicalModel`
`glm-5.3[1m]`, `contextWindow` 1,000,000, the haiku tier reaching
`glm-5.3-flash[1m]`; the request that run put on the wire named `glm-5.3`, the
suffix already stripped. Two numbers in that same record are Claude Code's, not
GLM's, and nothing here tries to correct them: `maxOutputTokens` is the 32,000
it gives any model it does not recognize, well under the 128K Z.ai publishes,
and `costUSD` is priced off the first-party table, so `/cost` and the status
line report a number with no relation to the subscription. cc also prints
`[claude-code:unrecognized_model]` once per model name; it is a telemetry
signal only and gates nothing.

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

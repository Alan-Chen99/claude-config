# scripts/

Standalone scripts: the launchers, the drift and coupling guards, the prompt-test runners,
and one-off probes. Each launcher's rationale is in its own comments.

## Files

| File                          | What                                                                                          | When to read                                                       |
| ----------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `claude.sh`                   | The launcher — git identity, `IS_SANDBOX`, agent view off, scratch root, proxy env only when 9160 answers, then `claude` on `sys_prompt/alan-default-next.md`, plus `--plugin-dir cache-keepalive/` when stdin is a terminal | Changing how sessions start; diagnosing a session whose prompt, proxy or scratch root is wrong |
| `kimi.sh`, `zai.sh`           | Provider launchers — endpoint, key, every model tier and its window, a `Claude(Kimi)`/`Claude(GLM)` git identity, then `claude.sh` | Running a session on Kimi or GLM; diagnosing one that reached Anthropic, sized its context wrong, or committed under the wrong name |
| `check-prompt-coupling.sh`    | Fails when a string `agent-tools` emits drifts from the system prompt or status reference that teaches the agent to recognize it | Editing an emitted literal the prompt or `docs/agent-tools-status-reference.md` quotes, or the text quoting it |
| `check-prompt-rationale.sh`   | Fails when a `sys_prompt/README.md` rationale section quotes no text the prompt still carries | Deleting or rewording a prompt line; adding a section to that file |
| `check-prompt-upstream.py`    | Pins the passages `sys_prompt/` borrowed verbatim from Claude Code's own prompt, and general-purpose's prompt copied into `agents/gp-*.md` | After a Claude Code upgrade; before editing a borrowed passage      |
| `check-env-context.sh`        | Reports when cc's own env block drifts from the field set `agent-tools env-context` is pinned to; `--update` re-pins the manifest | After an env-context drift warning; re-pinning after an upgrade     |
| `prune-scratch.sh`            | Reports and, with `--apply`, deletes empty session scratchpads, which nothing else reclaims; `--session <id>` has no liveness check | Freeing scratch disk space                                          |
| `prompt-test-cc.sh`           | Runs one `prompt-tests/general/` case under Claude Code against a full-replacement prompt     | Running a prompt test                                              |
| `prompt-test-cc-leg2.sh`      | Sends a case's second-leg instruction into the session leg 1 left behind                      | Running a two-leg case                                              |
| `prompt-test-cc-downstream.sh`| Feeds a run's artifact to the reader it was written for, in a fresh empty config dir         | Grading an artifact a case produced for a downstream reader          |
| `prompt-test-run.sh`          | The opencode runner for the same cases                                                        | Running a prompt test against opencode                              |
| `reasoning-probe.py`          | Sends a spec + task pair to a reasoning-visible model via OpenRouter, returning the trace verbatim | Investigating a finding that needs paragraph-level reasoning        |
| `strip-frontmatter.py`        | Writes a sibling `-clean.md` without YAML frontmatter, which opencode's `{file:PATH}` would inline as instruction text | Preparing a spec for `{file:...}` inclusion                         |
| `ralph.sh`                    | Launches `ralph run` against `/workspace/ralph/build.yml` under the `Claude(Ralph)` git identity | Running the ralph loop                                              |

## Subdirectories

| Directory    | What                                                        | When to read                                      |
| ------------ | ----------------------------------------------------------- | ------------------------------------------------- |
| `intercept/` | MITM proxy capturing conversation-shaped API calls to `~/.claude/requests-log/`, with a `NNNN.detail.json` beside each failed one — only from sessions `claude.sh` launched while it was listening. The listener is the canonical venv's `mitmdump` (`install.sh`, HIDDEN PATH DEPENDENCY). Its `README.md` carries the port, the CA setup, the capture format and what a capture cannot record; `agent-tools cc-replay` re-sends one | Capturing requests; replaying one; diagnosing an intercepted session whose turns abort; judging what a missing capture means |
| `cache-keepalive/` | Mod (function-hook plugin) refreshing the main thread's 1h prompt cache once, 50 min into a wait on background work or on its own pending tool call (a dialog, a foreground Bash); `waits.py` re-derives that from the transcripts. Its `README.md` carries why the built-in keepalive does not run here, the TTL gate, the overlap with idle compaction and how to read its rows | Changing the period or cap; a `cache-keepalive:` row or toast; a session that waited past the hour and still rewrote its cache |

## Agent Policy

- `zai.sh` leaves `CLAUDE_CODE_EFFORT_LEVEL` unset where `kimi.sh` pins `high`: unset is
  what selects Z.ai's recommended `max` (a captured request carries
  `output_config {"effort": "max"}`). It also omits the
  `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` Z.ai's own setup sets: nothing it gates
  (`.claude/skills/update-claude-code/references/inventory.md`, "Unset knobs") is needed to
  reach Z.ai. Keep both.
- Kimi on this subscription: `k3[1m]`, `kimi-for-coding`, `k3-256k`;
  `kimi-for-coding-highspeed` answers 401 (2026-09-24).
- Under `zai.sh`, `maxOutputTokens` and `costUSD` (so `/cost`) are cc's defaults for a
  model it does not recognize, not GLM's, and `[claude-code:unrecognized_model]` gates
  nothing (cc 2.1.269).

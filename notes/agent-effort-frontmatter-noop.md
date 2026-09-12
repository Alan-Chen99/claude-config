# `effort:` in agent frontmatter is a no-op for Task-tool subagent dispatch

Investigated 2026-05-23 → 2026-05-27 on Claude Code **2.1.143** (latest at the time was 2.1.150). Setting `effort: high` (or any other value) in an agent definition's YAML frontmatter has **no effect on actual reasoning** when that agent is dispatched as a subagent via the Agent (Task) tool. The field is parsed and propagated to display/hook surfaces but never reaches the API request's `thinking` field.

Concrete consequence: an `~/.claude/agents/general-purpose.md` override with `effort: high` was previously installed in this repo to make the general-purpose subagent think harder. It did nothing measurable. Removed in the same commit that adds this note.

> **Citations below are pinned to 2.1.143.** `/repos/claude-code-decompiled` has
> since been re-extracted twice and now holds 2.1.269 in an unrelated
> chunk-file layout with no `src/globals/` tree and no `bundle/` directory, so
> every `globals/*.js:<line>` reference below resolves to nothing. To
> re-resolve one, see that repo's README, "Re-resolving an old citation."

## Evidence

MITM proxy capture of API requests on a spawned CC session (see `docs/system-prompt-snapshot/capture.py --subagent general-purpose --capture-model opus`):

| Configuration | `request.thinking` | `output_config.effort` | response thinking blocks |
|---|---|---|---|
| Baseline — no override | `null` | absent | 0 |
| Override `effort: high` | `null` | absent | 0 |
| Override + `CLAUDE_CODE_ALWAYS_ENABLE_EFFORT=1` | `null` | `"max"` (session default, **not** `"high"`) | 0 |
| Same session's **main thread** (Opus 4.7, for control) | `{"type":"adaptive"}` | `"max"` | 1 |

Override loading was independently confirmed: a unique marker string was added to the override's prompt body and observed in the captured subagent's system prompt. The file *is* read; only the `effort` field is ignored.

## Root cause (Claude Code 2.1.143 source)

In `src/globals/09.js`, inside `Eb()` (the subagent runner):

```js
// line 15366
AH = H.effort !== void 0 ? () => H.effort : q.getEffortValue,
…
// line 15462-15466 — builds the subagent's tool-use context
thinkingConfig: P
  ? q.options.thinkingConfig
  : { type: 'disabled' },
```

The agent's `effort` is read into `getEffortValue` but never feeds `thinkingConfig`. `thinkingConfig` is hardcoded to `{type: 'disabled'}` whenever `useExactTools` (`P`) is falsy, which is the case for **every standard Task-tool dispatch** (it's set true only in fork mode without a `subagent_type`, REPL hydration, and background-task continuation — see `src/modules/uV6.js:677`, `globals/09.js:7945`, `globals/10.js:23458`).

Downstream in `src/globals/13.js:13900-13923`, the request body's `thinking` key is gated on `q.type !== 'disabled'`, so a disabled `thinkingConfig` produces no `thinking:` key, which produces no extended reasoning server-side.

`getEffortValue` does flow to: `${CLAUDE_EFFORT}` template substitution in prompts, hook input payloads (`effortValue`), and the status-line display (the latter was cosmetically fixed in 2.1.149). None of those touch the API.

The session-level effort resolver `kgK()` at `src/globals/05.js:21798` reads only `cli.effort`, `settings.effortLevel`, and env vars — **not** `agentFrontmatter`. So even using an agent as the main thread via `settings.json: { "agent": "X" }` doesn't pull effort from the frontmatter in 2.1.143. (Empirical reports in upstream #43083 suggest the `claude -p --agent <name>` CLI path was wired up to honor frontmatter effort sometime between 2.1.143 and 2.1.146 — not verified locally.)

## Upstream status

OPEN as of 2026-05-27, including in v2.1.150:

- [anthropics/claude-code#43083](https://github.com/anthropics/claude-code/issues/43083) — Feature: configurable reasoning effort level for subagents (most active)
- [anthropics/claude-code#39220](https://github.com/anthropics/claude-code/issues/39220) — Agent tool: add effort parameter for controlling subagent thinking depth
- [anthropics/claude-code#47175](https://github.com/anthropics/claude-code/issues/47175) — `CLAUDE_CODE_ALWAYS_ENABLE_EFFORT=1` bypasses model-capability checks, 400s on Haiku

Reproductions in #43083 confirm broken on 2.1.128, 2.1.129, 2.1.143, 2.1.146 for the Task-tool path. 2.1.149 changelog has a cosmetic status-bar fix only.

## Workarounds (all imperfect)

1. **`claude -p --agent <name>`** — reportedly honors frontmatter effort (per @jaredthirsk's 2.1.146 token counts in #43083, ~45% more output tokens for `effort: high` vs `effort: low` on the same prompt). One-shot non-interactive only; not the Task-tool path.
2. **`CLAUDE_CODE_ALWAYS_ENABLE_EFFORT=1`** — adds `output_config.effort` to every request, but value is the session default, not the agent's, and `thinking` is still absent. Breaks any Haiku-using subagent with HTTP 400 (#47175).
3. **Session-wide `settings.json: { "effortLevel": "high" }`** — applies to main thread; subagent dispatch still hits the `thinkingConfig: {type: 'disabled'}` hardcode.
4. **Patch CC bundle** — change `globals/09.js:15466` (2.1.143; see the banner above — there is no `bundle/cli.js` in the current decompiled tree) to inherit/branch on `H.effort`. Requires rebuilding the bundle; lost on every upgrade.

## Revisiting this

Before retesting on a future CC version:

- The override that used to live at `agents/general-purpose.md` is gone (this commit). To retest, recreate it with `effort: high` in the frontmatter and identical built-in body (see git history for the deleted file).
- `docs/system-prompt-snapshot/capture.py` has multi-subagent support (`--subagent` with no value captures Explore + general-purpose) and a project-local agent mirror step. Reusable for verification.
- Watchwords in the captured request body: `thinking: {…}` (the API-level gate) and `output_config.effort: "…"` (metering metadata). Watchword in the captured response: `content[].type == "thinking"` blocks.

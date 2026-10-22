# `effort:` in agent frontmatter was a no-op for Task-tool subagent dispatch on 2.1.143

> **Not true on 2.1.289 (measured 2026-10-22).** Through the MITM proxy,
> `claude -p --model claude-opus-4-8 --effort low` dispatched two project-local
> `claude-opus-4-8` agents: the one with `effort: medium` sent
> `output_config.effort: "medium"`, the one without `effort:` the session's
> `"low"` (not the model's default `high`); both sent `thinking: {"type": "adaptive"}`.
> With `CLAUDE_CODE_EFFORT_LEVEL=xhigh` set, both sent `"xhigh"`: the variable beats
> frontmatter, as the sub-agents docs state. In source, the subagent runner (beside
> the literal `"attachments_subagent"`) pushes `{kind: "effort", effort: <agent>.effort}`
> onto `permissionLayers`, read before the session effort, and passes the parent's
> `thinkingConfig` through. Upstream's 2.1.267 notes name the fix;
> anthropics/claude-code#43083 and #39220 are closed. Re-measure from
> `~/.claude/requests-log/<session id>/*.json`: a subagent request's system prompt
> carries `cc_is_subagent=true`. Below is the 2.1.143 record; its `globals/*.js:<line>`
> citations address a tree that no longer exists (`/repos/claude-code-decompiled`
> README, "Re-resolving an old citation").

Investigated 2026-05-23 → 2026-05-27 on Claude Code **2.1.143** (latest at the time was 2.1.150). Setting `effort: high` (or any other value) in an agent definition's YAML frontmatter has **no effect on actual reasoning** when that agent is dispatched as a subagent via the Agent (Task) tool. The field is parsed and propagated to display/hook surfaces but never reaches the API request's `thinking` field.

Concrete consequence: an `~/.claude/agents/general-purpose.md` override with `effort: high` was previously installed in this repo to make the general-purpose subagent think harder. It did nothing measurable. Removed in the same commit that adds this note.

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

The session-level effort resolver `kgK()` at `src/globals/05.js:21798` reads only `cli.effort`, `settings.effortLevel`, and env vars — **not** `agentFrontmatter`. So even using an agent as the main thread via `settings.json: { "agent": "X" }` doesn't pull effort from the frontmatter in 2.1.143.

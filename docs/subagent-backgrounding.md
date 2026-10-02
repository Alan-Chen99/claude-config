# Subagent backgrounding: which knob, and what each costs

Verified against claude-cli **2.1.269**; citations are `src/chunk-<hash>.js:<line>` in
`/repos/claude-code-decompiled`. The 2.1.235 investigation that found the regression is
`notes/subagent-backgrounding-overrides-run-in-background.md`; the prompt side of the
arrangement is `sys_prompt/CLAUDE.md`, "Subagents: `run_in_background: false` on every
Agent call".

## `CLAUDE_CODE_FORK_SUBAGENT`, and how subagents stay in the foreground

`settings.json` `env` sets `CLAUDE_CODE_FORK_SUBAGENT=0`, and that is the whole harness
side: the gate only decides whether the model gets a say, and keeping subagents in the
foreground is the prompt's job. The Agent tool backgrounds on a disjunction (`q4o`,
`src/chunk-dbb93264.js:103955-103969`); with fork subagents on, two of its terms are out
of reach — `forceAsync` is `Z8() && !callerIsInProcessTeammate` (`:172000`), and the input
schema drops `run_in_background` outright (`rc() || Z8()`, `:171779`). `=0` clears
`forceAsync` and puts the parameter back, leaving the last term, `!s && r !== !1`: **the
call backgrounds unless `run_in_background` is literally `false`**; omitting it backgrounds
exactly as `true` would. The price is the `fork` subagent type.

So `sys_prompt/alan-default-next.md` tells the agent to pass `run_in_background: false` on
every Agent call, and nothing enforces it: a call that omits the parameter is
backgrounded and reads in the transcript like any other. A `PreToolUse` hook on `Agent`
rewrote the parameter until 2026-09-16 and was removed so the model decides per call —
measured that day: 3 of 3 calls backgrounded with the prompt still describing the hook,
9 of 9 passed `false` once the bullet was an instruction. The Agent tool's description
recommends backgrounding by default, accurately; the prompt overrides a recommendation. `prompt-tests/general/subagent-foreground-default` is the standing check; run it
after any change to that bullet, to the tool description, or to this gate.

Neither the gate nor the prompt reaches an agent definition's own `background: true`, or
`isolation: "remote"`, outside the background-tasks guard entirely; no agent in `agents/`
declares either.

## The alternative: `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`

The only setting that makes the foreground a guarantee (bar a remote-isolation launch,
async regardless), with no help from the model and `fork` kept; it costs the whole
background-task facility. Reach for it if the prompt rule
fails to hold. Measured, one interactive session each:

| | `DISABLE_BACKGROUND_TASKS=1` | `FORK_SUBAGENT=0` |
| --- | --- | --- |
| Bash `run_in_background` | absent from the schema | present; returns a task id and re-invokes the agent when the command exits |
| A command outliving its `timeout` | killed, `Exit code 143` | moved to the background with a task id; upstream's exemption for a `sleep`-first command is unreachable behind `hook_pre.rs`'s prelude (`docs/agent-tools-status-reference.md`) |
| `BACKGROUNDED:` from `hook_post.rs` | cannot fire: no tool response carries `backgroundTaskId` | fires, naming the cause, the task id and the `long-bash` skill |
| `subagent_type: "fork"` | available | `Agent type 'fork' not found` |
| Foreground `sleep` | permitted | blocked at 25 s or more as the first statement only (`echo hi; sleep 25` runs), though the Bash description states the block unconditionally |

## Paths that ship but are not exercised here

MCP auto-background (`src/chunk-jtrs4f58.js:255`), the Ctrl+B affordance
(`src/chunk-qxhez8yz.js:99`, keybinding `:32`), observer agents (`Zfe`,
`src/chunk-dbb93264.js:74088`) and forked skills (`y9t`, `src/chunk-dbb93264.js:173976`)
all open on the same `rc()` background-tasks check and return under the current setting. Skills are not opt-in as the 2.1.235 note has it: `background` defaults to true
for any skill declaring `context: fork`, and `background: false` is the opt-out that keeps
the caller waiting (`src/chunk-dbb93264.js:54434`). `CLAUDE_AUTO_BACKGROUND_TASKS`, unset
here, moves a foreground subagent to the background after its interval under either
setting (`iTs`, `src/chunk-dbb93264.js:171747`, wired at `:172571`).

## Print mode: what outlives a turn

Measured 2026-10-01 on 2.1.269 (`notes/print-mode-task-lifetime.md`, also the interactive
side's memory-pressure reaper; `notes/foreground-wait-under-print-mode.md`).
Under `claude -p` the turn ending is the process ending, with two exceptions:

| Running at turn end | `-p` does |
| --- | --- |
| Bash `run_in_background` | kills it (`task_updated status: killed`) and exits |
| a foreground Bash call | holds the process until it returns, up to its `timeout` — 10 min unless `BASH_MAX_TIMEOUT_MS` in settings `env` raises it (2,147,483,647 is the timer's bound); a `Monitor` event fired meanwhile is dropped when the turn ends with nothing running |
| `Monitor` | stays up: each event and the completion re-invoke the model, and the process exits after the turn that follows the monitor's end, or its expiry if nothing re-arms it — `timeout_ms` is clamped to 10 minutes under `-p`, 30 interactive |

A `Stop` hook, unattended (`CLAUDE_CODE_SESSION_ATTENDED=0`), sees `background_tasks[]`
with each `command` and can block the turn end (`{"decision": "block"}`; `stop_hook_active`
advisory; `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` consecutive blocks, default 8), holding the
process while it runs up to its settings `timeout`, any positive seconds, a kill being no
decision.
`skills/telegram-hitl` waited that way until 2026-10-01 and now waits in the foreground.

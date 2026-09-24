# Subagent backgrounding: which knob, and what each costs

Verified against claude-cli **2.1.269**. Citations are `src/chunk-<hash>.js:<line>` in
the decompile at `/repos/claude-code-decompiled`; chunk hashes and line numbers rotate
every build, so re-resolve by grepping the string literal the behaviour touches. This
file is the current state; the 2.1.235 investigation that found the regression is
`notes/subagent-backgrounding-overrides-run-in-background.md`, and the prompt side of
the arrangement is `sys_prompt/CLAUDE.md`, "Subagents: `run_in_background: false` on
every Agent call".

## `CLAUDE_CODE_FORK_SUBAGENT`, and how subagents stay in the foreground

`settings.json` `env` sets `CLAUDE_CODE_FORK_SUBAGENT=0`. That is the whole harness-side
configuration: keeping subagents in the foreground is the system prompt's job, and the
model's.

The gate does not foreground anything by itself — it decides whether the model gets a say.
The Agent tool backgrounds on a disjunction (`q4o`, `src/chunk-dbb93264.js:103955-103969`),
and with the gate on, two of its terms are out of reach: `forceAsync` is `Z8() && !callerIsInProcessTeammate`
(`:172000`), and the input schema drops `run_in_background` outright (`rc() || Z8()`, `:171779`),
so there is no parameter to pass. Turning the gate off clears `forceAsync` and puts the parameter
back. What remains is the last term, `!s && r !== !1`: **the call backgrounds unless
`run_in_background` is literally `false`**. Omitting it backgrounds exactly as `true` would.
The price of the gate is the `fork` subagent type, which disappears outright — `Agent type
'fork' not found. Available agents: …`.

So `sys_prompt/alan-default-next.md` tells the agent to pass `run_in_background: false` on
every Agent call, and nothing enforces it. A call that leaves the parameter out is backgrounded
and reads in the transcript like any other call.
`prompt-tests/general/subagent-foreground-default` is the standing check; run it after any
change to that bullet, to the Agent tool description, or to this gate.

Until 2026-09-16 a `PreToolUse` hook on `Agent` rewrote `run_in_background` to `false` on
every call, which made the foreground a harness guarantee rather than a model behaviour. It
was removed so the model decides per call. Measured the same day on 2.1.269, hook removed and
the prompt still describing it: 3 of 3 Agent calls omitted the parameter and all three returned
`Async agent launched successfully`. With the bullet rewritten as an instruction, 9 of 9 calls
across three trials passed `false` and none backgrounded.

Two terms of the disjunction neither the gate nor the prompt reaches: an agent definition
declaring `background: true` of its own, and `isolation: "remote"`, which sits outside the
background-tasks guard entirely. No agent in `agents/` declares either, so neither is
reachable here today; both would be, the moment one did.

## The alternative: `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`

`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` is the only setting that makes the foreground a
guarantee again: it forces every subagent foreground — bar a remote-isolation launch, which
runs async regardless — with no help from the model, and keeps `fork`. What it costs instead
is the whole background-task facility, a far larger loss than `fork`. Reach for it if the
prompt rule turns out not to hold. Measured in one interactive session each:

| | `DISABLE_BACKGROUND_TASKS=1` | `FORK_SUBAGENT=0` |
| --- | --- | --- |
| Bash `run_in_background` | absent from the schema | present; returns a task id and re-invokes the agent when the command exits |
| A command outliving its `timeout` | killed, `Exit code 143` | moved to the background with a task id. Upstream exempts a command whose first statement is `sleep`, but `hook_pre.rs` prepends two statements to every command, so that exemption is unreachable here — measured 2026-09-21, see `docs/agent-tools-status-reference.md` |
| `BACKGROUNDED:` from `hook_post.rs` | cannot fire, since no tool response carries `backgroundTaskId` | fires, naming the cause, the task id, and the `long-bash` skill |
| `subagent_type: "fork"` | available | `Agent type 'fork' not found` |
| Foreground `sleep` | permitted | blocked at 25 s or more, and only as the command's first statement — `echo hi; sleep 25` runs. The Bash description states the block unconditionally and points at Monitor with an until-loop. Measured 2026-09-21 |

## Paths that ship but are not exercised here

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
`src/chunk-dbb93264.js:171747`, wired at `:172571`). Unset here, so inert — but it bounds
`DISABLE_BACKGROUND_TASKS=1` too: even that setting guarantees a synchronous subagent only
in an environment that leaves this one unset.

## The tool description recommends the opposite

The Agent tool's own description, and the `run_in_background` property's description beside it,
both recommend backgrounding by default. That is now accurate rather than false, so
`sys_prompt/alan-default-next.md` overrides the recommendation instead of contradicting a fact
— and the conflict is decided per call, by the model.

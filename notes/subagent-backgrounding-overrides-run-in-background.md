# Subagent backgrounding ignores `run_in_background: false`

Investigated 2026-08-28 on Claude Code **2.1.235**. Every subagent runs in the
background regardless of `run_in_background: false`, whether the model sends it or a
`PreToolUse` hook injects it. The parameter is also absent from the Agent tool's input
schema, so the model cannot send it at all. Setting
`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` is the only lever that restores foreground
subagents while keeping the `fork` subagent type.

The regression arrived with the fork-subagent feature. Captured API requests place it
between **2.1.143** and **2.1.235**: the last interactive session whose Agent schema
carried `run_in_background` ran at 2026-08-22T20:52:18 on 2.1.143; the first without it
ran at 2026-08-22T21:16:20 on 2.1.235. A scan of 26,953 request captures across 350
sessions found no interactive exception after that boundary. Print-mode (`-p`) sessions
on 2.1.235 still carry the parameter, which is the first hint at the cause: `EGb()`
returns `'disabled'` when the session is non-interactive.

## Root cause

`src/modules/MWa__2.js` in the 2.1.235 decompile, inside the Agent tool's `call()`:

```js
// 744
let J = _S(),            // coordinator mode
    Y = iMe() && !A,     // fork-subagent gate, and not a teammate
    G = lk();            // background tasks disabled
// 761
F = Q || ((o === !0 || X.background === !0 || (J && !A) || Y || (!A && o !== !1)) && !G);
```

`o` is `run_in_background`, `F` is the decision to background. `Y` is an unconditional
term of the disjunction, so once `iMe()` is true nothing `o` holds can matter. `iMe()`
(`src/globals/08.js:9536`) is `Uip() !== 'disabled'`, and `Uip()` returns `'default'` in
an ordinary interactive session — the fork feature is on unless
`CLAUDE_CODE_FORK_SUBAGENT` is falsy or the session is non-interactive.

The same predicate strips the parameter from the schema, `MWa__2.js:461`:

```js
return lk() || iMe() ? e.omit({ run_in_background: !0 }) : e;
```

The hook is not at fault and its value is not lost. `gMf` (`src/globals/17.js:6033`)
filters `unrecognized_keys` before validating a hook's `updatedInput`, and `Umf`
(`src/globals/15.js:3351`) passes the raw object through to `call()`. The value arrives
as `o === false` and is then outvoted by `Y`.

Only `G` can cancel the disjunction, and `G` is `lk()` (`src/globals/08.js:7264`) —
`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`, or a host-internal `backgroundTasksDisabled`
that no settings key reaches.

## Measured

Each row is one session driven over a pty with the same `PreToolUse` hook text, opus,
the repo's `--system-prompt-file`. "foreground" means the agent's report came back as
the tool result; "background" means `Async agent launched successfully`.

| Session mode | Hook | Flag | Result |
| --- | --- | --- | --- |
| headless `-p` | yes | none (non-interactive ⇒ gate off) | foreground |
| headless `-p` | yes | `CLAUDE_CODE_FORK_SUBAGENT=1` | background |
| headless `-p` | no | none | background |
| interactive | yes | none (gate on) | background |
| interactive | yes | `CLAUDE_CODE_FORK_SUBAGENT=0` | foreground |
| interactive | yes | same, via `settings.json` `env` | foreground |
| interactive | no | `CLAUDE_CODE_FORK_SUBAGENT=0` | background |
| interactive | yes | `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` | foreground |
| interactive | no | `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` | foreground |

Rows 1–2 isolate the gate: identical hook, opposite outcome. Rows 3 and 7 show the hook
is still doing the work wherever the gate is off. Rows 8–9 show the flag alone suffices,
which is why the hook was removed from `settings.json`.

With `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` the `fork` subagent type survives — its
tool description still describes forking, and `subagent_type: "fork"` launches. With
`CLAUDE_CODE_FORK_SUBAGENT=0` it does not: `Agent type 'fork' not found. Available
agents: claude-code-guide, Explore, general-purpose, Plan, statusline-setup`.

## What the flag changes elsewhere

Verified: Bash loses `run_in_background` from its schema; a Bash command that outlives
its `timeout` returns `Exit code 143 / Command timed out` rather than a background task
id; foreground `sleep` stops being blocked, because that block is conditioned on
`!lk()` (`src/modules/Cae.js:543`); Monitor, `TaskOutput` and `TaskStop` remain in the
tool set, and a Monitor whose command exits still delivers per-event notifications and a
`<status>completed</status>` notification.

Source only, not exercised: MCP auto-background (`src/globals/19.js:21594`), the ctrl+b
backgrounding affordance (`src/globals/23.js:14364`), observer agents
(`src/globals/09.js:2205`), and skills declaring `background: true`, which run inline
(`src/globals/14.js:22858`).

`&` is unaffected — it is plain shell behaviour, not a harness feature. A command started
with `&` and redirected to a file returns immediately and survives into later calls, and
`agent-tools run` wrapped that way still reports `producing` and `final(<code>)` on its
own status channel. Waiting needs `timeout <s> tail --pid=<pid> -f /dev/null`, not
`wait`: each Bash call gets a fresh shell, so `wait` answers
`pid <n> is not a child of this shell`.

The kill on timeout is broader than the process group, and this bounds how backgrounding
can be used. A call killed at its `timeout` takes down every process it started: three
variants spawned in one call — plain `&`, `setsid --wait`, and bare `setsid` — all stopped
advancing the moment the call returned `Exit code 143`. A process-group kill run outside
Claude Code kills only the plain `&` variant and leaves both `setsid` variants running, so
whatever Claude Code does reaches a new session as well. A backgrounded job therefore
survives only a call that returns on its own. Both halves of the pattern carry weight: the
`&` is what outlives the call, and the bounded wait is what keeps the call from being
killed instead of returning:

```bash
d=/tmp/bg/<name>; mkdir -p "$d"; rm -f "$d/rc"
{ <command> >"$d/log" 2>&1; echo $? >"$d/rc"; } &
echo $! >"$d/pid"
timeout <seconds> tail --pid="$(cat "$d/pid")" -f /dev/null
[ -f "$d/rc" ] && { echo "rc=$(cat "$d/rc")"; cat "$d/log"; } || echo "still running: $(cat "$d/pid")"
```

Measured end to end in a flagged session: a job finishing inside the wait reported
`DONE rc=7` with its output inline; a job outrunning a 5-second wait reported `RUNNING`,
survived the call, and was collected by a later one as `DONE rc=3`.

## Known defect in the flagged configuration

The Agent tool description keeps this paragraph while nothing backgrounds:

> A fork runs in the background and keeps its tool output out of your context. … Subagents
> run in the background; you'll be notified when one completes. … if the user asks before
> it arrives, say it's still running.

In `fhf()` (`src/globals/15.js`) that fragment is gated on `iMe() && forkAvailable`, with
no `lk()` guard, while the bullet below it — "The agent's final message is returned to you
as the tool result" — is gated on `!lk()`. The two disagree by construction.
`sys_prompt/alan-default-next.md` contradicts the paragraph explicitly so the model does
not act on it.

## Prompt surface

Neither flag changes the system prompt in this repo's configuration. `claude.sh` passes
`--system-prompt-file`, which replaces Claude Code's generated prompt outright — the file
appears verbatim and `# Harness`, `# Delivering work` and `# Corrections` are absent. Even
without the prompt file, three captures (no flag, each flag) differed only in the billing
header, cwd and scratchpad path, because on opus `aT()` (`src/modules/c8.js:71`) selects
the simple-system-prompt mode in which `cdE()` returns null and the Agent guidance bullet
is never emitted. That last observation is opus-specific; a non-lean model was not
captured.

Tool descriptions do change, and `--system-prompt-file` gives no cover there.

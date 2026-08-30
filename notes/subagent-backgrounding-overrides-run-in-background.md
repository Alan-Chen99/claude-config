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
can be used. It reaches the call's live descendants, not its process group: each `&` job
already has a process group of its own — the Bash tool's shell runs with job control on,
`$-` containing `m` — yet a plain `&` child still dies. Three variants spawned in one call,
each appending a line per second to its own file, were compared after the call returned
`Exit code 143` — plain `&` stopped at 10 lines, `setsid --wait` stopped at 10, and bare
`setsid` went on from 15 to 23. A separate run measured `nohup` beside plain `&`: both
stopped after 8 of their 90 heartbeats, while a bare `setsid` child kept writing, reparented
to init at PPID 1 with PGID and session both equal to its own pid. `setsid --wait` dies
because the waiting intermediate keeps it in the descendant tree; bare `setsid` survives
because its double fork reparents the worker to init before the kill arrives. The same
boundary shows up without `setsid` at all: `&` children spawned inside a subshell that then
exits are orphaned, and they survive too. The session boundary is not the one that bounds
the kill — `setsid --wait` leaves its worker in a session of its own and the worker dies
anyway.

A backgrounded job therefore survives only a call that returns on its own, or a spawn that
leaves the descendant tree before the call is killed.

`agent-tools run --background` is the second of those. It forks; the child calls `setsid`
and goes on to be the wrapper, while the original process exits as soon as that child
reports it has started. The wrapper is therefore an orphan at PPID 1 by the time the call
returns, and needs no bounded wait at all. Its exit code says the child started, not that
it succeeded; the child's own code arrives later on the status channel as `final(<code>)`.

The `&` pattern below is what a command that is not being wrapped still needs. Both halves
of it carry weight: the `&` is what outlives the call, and the bounded wait is what keeps
the call from being killed instead of returning:

```bash
agent-tools run --desc "<description>" <executable> <args..> & echo $! >/tmp/<name>.pid
timeout <seconds> tail --pid="$(cat /tmp/<name>.pid)" -f /dev/null
```

`agent-tools run` supplies the rest, so no log file or exit-status file is needed. It
returns from the call in 0s even unredirected — the Bash tool waits on the process, not on
its stdout pipe — captures output to the file its status line names, and reports the child
as `final(<code>)`: a job exiting 42 was reported `[final(42)]` on the next delivery point,
with `RC-JOB-OUT` in the named capture file. A second job left running reported `[final(0)]`
at the same point without ever being waited on. `$!` is the wrapper pid, not the child's;
the wrapper lives exactly as long as the child, which is what makes it the right thing to
pass to `tail --pid`. A bounded wait on a still-running job exited 124 at its limit and 0
immediately once the job had finished.

`agent-tools ps --task <tool_use_id>` narrows the report to one wrapped call — 923 bytes
against 27,480 for the bare `ps` at this point in the session, which is enough to matter.

An earlier draft of this pattern hand-rolled the capture: `{ cmd >log 2>&1; echo $? >rc; } &`
with its own pid, log and rc files. It worked — a job finishing inside the wait reported
`DONE rc=7`, and one outrunning a five-second wait reported `RUNNING`, survived the call and
was collected later as `DONE rc=3` — but every part of it duplicated something the wrapper
already does.

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

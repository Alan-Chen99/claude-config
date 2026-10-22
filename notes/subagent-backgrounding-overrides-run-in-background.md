# Subagent backgrounding ignores `run_in_background: false`

> **The configuration this note measured is gone twice over.** 2026-09-16 replaced the
> `PreToolUse` `Agent` hook with a prompt rule; 2026-10-22 set `CLAUDE_CODE_FORK_SUBAGENT=1`
> and stopped asking for the foreground. The measurements stand; current state is
> `docs/subagent-backgrounding.md`. Cut to its budget the same day: the 2.1.235 source
> excerpts, the `&`-and-`tail --pid` wait pattern `agent-tools run --background` replaced, and
> the two configurations' tool-description defects are in `git show 0db42cb2:<this path>`.

Investigated 2026-08-28 on Claude Code **2.1.235**, re-checked on **2.1.269** on 2026-09-12;
every citation of the 2.1.235 tree (`src/globals/`, `src/modules/`) locates nothing in later
extractions.

Every subagent ran in the background regardless of `run_in_background: false`, whether the
model sent it or a `PreToolUse` hook injected it, and the parameter was absent from the
schema. The regression arrived with the fork-subagent feature. Captured API requests place it
between **2.1.143** and **2.1.235**: the last interactive session whose Agent schema carried
`run_in_background` ran at 2026-08-22T20:52:18 on 2.1.143, the first without it at
2026-08-22T21:16:20 on 2.1.235. A scan of 26,953 request captures across 350 sessions found no
interactive exception after that boundary; `-p` sessions still carried the parameter, because
the gate is off when the session is non-interactive.

## Root cause

The Agent tool's `call()` backgrounds on a disjunction. With the fork gate on — the variable
truthy, or unset in an interactive session — one term holds unconditionally, so nothing
`run_in_background` holds can matter, and the same predicate strips the parameter from the
schema. A hook's `updatedInput` reached `call()` intact (`false`) and was outvoted. Only
`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` cancels the disjunction. With the gate off, its last
term (`!A && o !== !1`) still backgrounds a call that omits the parameter.

## Measured

Each row is one session driven over a pty with the same `PreToolUse` hook text, opus, the
repo's `--system-prompt-file`. "foreground": the report came back as the tool result;
"background": `Async agent launched successfully`.

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

Rows 1–2 isolate the gate. Row 7 bounds the gate-off alternative: with no hook the parameter
arrives `undefined` and the call backgrounds. With `DISABLE_BACKGROUND_TASKS=1`
`subagent_type: "fork"` launches; with `FORK_SUBAGENT=0`, `Agent type 'fork' not found`.

Measured 2026-09-04 through `agent-tools claude`, schemas read from the intercepted request
bodies:

| Probe | `DISABLE_BACKGROUND_TASKS=1` | `FORK_SUBAGENT=0` + hook |
| --- | --- | --- |
| Bash and Agent input schemas | no `run_in_background` | `run_in_background` on both |
| a 60s command at `timeout: 5000` | `Exit code 143` / `Command timed out after 5s` | `moved to the background (ID: b5eaioquc)`, then a notification |
| `BACKGROUNDED:` notice | never emitted | emitted for a timeout and for `run_in_background: true` |

`sleep 45; echo X` is killed under either setting: only a single simple command whose first
word is not `sleep` is moved to the background.

## The timeout kill reaches the call's live descendants

Not its process group: each `&` job has its own (the Bash tool's shell runs with job control
on), yet a plain `&` child still dies. Three children spawned in one call, each appending a
line per second, after the call returned `Exit code 143`: plain `&` stopped at 10 lines,
`setsid --wait` at 10, bare `setsid` went on from 15 to 23. A second run: `nohup` and plain `&`
both stopped after 8 of 90 heartbeats while a bare `setsid` child kept writing, reparented to
init at PPID 1. `setsid --wait` dies because its waiting intermediate keeps the worker in the
tree; `&` children of a subshell that exits are orphaned and survive too. A job outlives a
killed call only by leaving the descendant tree first — what `agent-tools run --background`
does.

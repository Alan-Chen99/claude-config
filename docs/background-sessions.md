# Background Sessions (agent view / FleetView)

Verified against claude-cli **2.1.235**: the decompiled binary at
`/repos/claude-code-decompiled` plus live observation of a session that
backgrounded itself. Line references are to that decompile and will not survive
a version bump.

## What happens

Backgrounding does not detach the process you are looking at. Claude Code
allocates a **new session UUID**, writes a job directory, spawns a **fork** that
resumes the transcript, and turns the TUI you were using into the agents view
(FleetView). Two processes exist afterwards; the fork is the one talking to the
model.

Strings that mark the transition:

| String | Where |
|---|---|
| `Backgrounding after the current tool finishes…` | armed, waiting for the running tool |
| `Your conversation moved to the background — enter opens it · esc returns to it · ctrl+c twice quits` | FleetView header after the handoff |
| `Cannot open agents — …` | a refusal (see below) |

Code path: `GAe` (`globals/28.js:10208`) → `SRe` → `v2g`
(`globals/27.js:52647`) → `X_r` (`globals/24.js:30356`).

## Trigger

Open question. The three entry points visible in the decompile are:

1. **← on an empty prompt input**, double-tapped — the input hook fires
   `onLeftArrowOnEmpty` only when `z.text === ''` (`globals/22.js:8820`), and
   the first press only arms a `Press ← again to open agents` hint. A burst
   keypress is rejected as not-solo; `tengu_left_arrow_editing_guard` (default
   true) additionally suppresses it right after typing.
2. **A mouse click on the `fork:` chip** in the transcript, which sets
   `pendingAgentViewAttach`; an effect at `globals/28.js:10460` calls `GAe()`
   when that store field changes.
3. **`/background`**, which reaches `X_r` with `via: 'command'`
   (`globals/24.js:30748`) — same spawn, no `GAe` message.

No timer, idle watcher, or automatic path was found in the source. That does
not settle it: in one observed hour, six background jobs were created from an
interactive session, three of them from a single user prompt, and the operator
reports firing it without a deliberate ← press. Treat the trigger as **not yet
reproduced**; the consequences below hold regardless of what fires it.

## Modes

`$sS(isLoading, betweenCalls)` (`globals/16.js`) picks the handoff mode:

| Condition | `via` | Behavior |
|---|---|---|
| Not loading | `idle-fork` | Backgrounds immediately |
| Loading, a tool is running | `defer-then-fork` | Prints `Backgrounding after the current tool finishes…`, arms a timer capped by `tengu_defer_cap_ms` (default 10,000 ms). If the tool is still running at the cap, it converts to `abort-then-fork` and aborts anyway |
| Loading, text streaming | `abort-then-fork` | Flushes, keeps the trailing ≤16 KB of partial assistant text as a `prefill`, aborts the request |

## Refusals

`k6r`/`OsS` (`globals/16.js:13538`, `13369`) block the handoff and emit
`tengu_left_arrow_blocked` when: the agent view is disabled (`fleet-disabled`),
the workspace is remote, session persistence is disabled, an external load is in
flight, a foregrounded task is running, queued commands would be lost, or the
input holds unsent draft text.

## What crosses the handoff

| Carried | Dropped |
|---|---|
| Transcript (`--resume` + `--fork-session`) | `--system-prompt`, `--system-prompt-file` |
| `--model`, `--effort`, `--permission-mode` | `--append-system-prompt` (kept only for `/fork`, where `keepParent` is set) |
| `--add-dir`, `--allowed-tools`, `--disallowed-tools` | anything else from the original argv |
| `--agent`, `--agents` | |
| Process environment (`HTTPS_PROXY`, `NODE_EXTRA_CA_CERTS`, `IS_SANDBOX`, `GIT_AUTHOR_*` all observed intact) | |
| In-flight agents, shells, cron, Artifact monitors via `adopt.json` | |
| Trailing partial assistant text as `prefill` (abort-then-fork only) | |
| `settings.json` config, including `outputStyle` | |

The dropped custom system prompt is the consequence that bites: a session
launched with `--system-prompt-file` runs the **default** prompt after
backgrounding, with no warning. See
`docs/system-prompt-snapshot/README.md` § "Background sessions do not inherit
the flag" for the measured before/after. Only settings-based configuration —
notably an output style — is durable across the handoff.

## Job directory

`~/.claude/jobs/<short>/` holds the fork's state:

| File | What |
|---|---|
| `state.json` | `state`, `intent`, `sessionId`, `cwd`, `bgIsolation`, and `respawnFlags` |
| `timeline.jsonl` | one record per status update (the tool descriptions the session reports) |
| `adopt.json` | hand-off payload: carried agents/shells/cron plus any `prefill` |

`respawnFlags` is the authoritative record of what a later respawn will use.
Observed value on a session launched with `--system-prompt-file`:

```json
["--reply-on-resume", "--permission-mode", "bypassPermissions", "--model", "opus"]
```

## Detecting a backgrounded session from inside it

```bash
echo "$CLAUDE_JOB_DIR"            # set only in a background session
echo "$CLAUDE_CODE_CHILD_SESSION" # 1 in a background session
tr '\0' '\n' < /proc/$CLAUDE_PID/cmdline | grep -c system-prompt-file   # 0 after a handoff
```

## Disabling

| Knob | Where | Effect |
|---|---|---|
| `"leftArrowOpensAgents": false` | `~/.claude.json` (top level) | Disables only the ← gesture. `/background`, `claude agents`, `--bg` still work |
| `"disableAgentView": true` | `settings.json` | Disables the whole agent view: `claude agents`, `--bg`, `/background`, the on-demand daemon, and therefore the ← gesture |
| `CLAUDE_CODE_DISABLE_AGENT_VIEW=1` | environment | Same as `disableAgentView` |

`leftArrowOpensAgents` is read as `ar().leftArrowOpensAgents !== !1`
(`globals/28.js:10495`), so an absent key means enabled. It is a global-config
key (`TWo` in `modules/Mn.js`), written by `tn` → `m0d` → `jS()` →
`$CLAUDE_CONFIG_DIR || ~` + `.claude.json`. The `/config` dialog exposes it as
the toggle **`← opens agents`**. There is no `claude config set -g` in 2.1.235 —
that subcommand was removed; edit the file or use `/config`.

For a launcher that depends on `--system-prompt-file`, `disableAgentView` is the
correct knob: it also closes `/background`, the other path that drops the flag.

```bash
# in the launcher, before exec claude
export CLAUDE_CODE_DISABLE_AGENT_VIEW=1
```

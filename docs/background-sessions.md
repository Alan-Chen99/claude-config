# Background Sessions (agent view / FleetView)

Verified against claude-cli **2.1.269**: the decompiled binary at
`/repos/claude-code-decompiled`, plus one live check of the disable knob
(`claude agents --json` with and without `CLAUDE_CODE_DISABLE_AGENT_VIEW`).
Citations are `src/chunk-<hash>.js:<line>` in that decompile. Chunk hashes
rotate every build and minified names are **per-file** in this layout, so a
citation is the `<file>:<line>` pair, not the name — re-resolve by grepping the
string literal the behaviour touches.

## What happens

Backgrounding does not detach the process you are looking at. Claude Code
allocates a **new session UUID**, writes a job directory, dispatches a **fork**
to the background daemon which resumes the transcript, and turns the TUI you
were using into the agents view (FleetView). Two processes exist afterwards; the
fork is the one talking to the model.

Strings that mark the transition:

| String | Where |
|---|---|
| `Backgrounding after the current tool finishes…` | armed, waiting for the running tool (`chunk-4zmskew4.js:2880`) |
| `Your conversation moved to the background — enter opens it · esc returns to it · ctrl+c twice quits` | FleetView header after the handoff (`chunk-qhf4rxgg.js:4117`) |
| `Cannot open agents — …` | a refusal (see below) |

Code path: `onLeftArrow` (`chunk-4zmskew4.js:2676`, a method of the
`BackgroundGesture` class at `:2557`) → the private dispatcher at `:2642` →
`oZe` (`:2342`, writes the job dir and `adopt.json`) → `uDe` (`:533`, builds the
respawn argv) → `BU` (`chunk-bd56htwt.js:1952`, writes `state.json` and hands
the dispatch payload to the daemon).

Beware: `oZe` and `uDe` also name unrelated functions in other chunks
(`chunk-dbb93264.js:213223` is a different `oZe`). Only the file:line is an
address.

## Trigger

The entry points visible in the decompile:

1. **← on an empty prompt**, double-tapped. The route is only installed when
   `oe().leftArrowOpensAgents !== !1` (`chunk-4zmskew4.js:38768`) and the
   handoff is otherwise available (`rZe`, `:3006`); the first press only arms
   the hint `Press ← again to open agents` (`:3034`). The gesture state machine
   (`chunk-rt3e7bzt.js:768`) rejects a burst keypress as not-solo, and
   `tengu_left_arrow_editing_guard` (default true) additionally suppresses it
   for 2 s after typing.
2. **A mouse click on a job chip** in the transcript, which calls
   `requestAttach(jobId)` (`chunk-rjc4dqgx.js:6568` → `chunk-4zmskew4.js:2601`);
   that defers to `onAttachRequest` (`:2611`), which runs the same `onLeftArrow`
   path with an `autoOpenJobId`. The chip click has its own confirm states
   (`attach-arm` / `attach-absorb`) in the gesture machine.
3. **`/background`** (alias `/bg`, `chunk-jv5pe7gg.js:11`), which reaches the
   same `uDe` with `via: 'command'` (`chunk-4zmskew4.js:867`) — same spawn, no
   `onLeftArrow` guards.

`defaultToAgentsView` (global config, `src/cli.js:426`) is new and is **not** a
handoff: it makes a fresh `claude` open the agent view instead of a REPL, so no
existing conversation is moved. It is off by default (`?? !1`,
`chunk-ve1cwn02.js:1030`).

No timer, idle watcher, or automatic handoff path was found in the 2.1.269
source. That does not fully settle it: under 2.1.235, six background jobs were
created from one interactive session in an hour, three from a single user
prompt, and the operator reported firing it without a deliberate ← press. That
has not been re-observed under 2.1.269 — this repo's launcher disables the agent
view, so it cannot recur here. Treat the trigger as **not yet reproduced**; the
consequences below hold regardless of what fires it.

`/fork` (`chunk-j5mf4j6r.js:375`) reaches the same `uDe` with `keepParent: true`.
It is a different operation — the parent session stays alive — and it carries
strictly more (see below).

## Modes

`p(isLoading, betweenCalls)` (`chunk-40sazthj.js:20`, reached through `f` at
`:24` / `ZYe` at `:183`) picks the handoff mode:

| Condition | `via` | Behavior |
|---|---|---|
| Not loading | `idle-fork` | Backgrounds immediately |
| Loading, a tool is running | `defer-then-fork` | Prints `Backgrounding after the current tool finishes…`, arms a timer capped by `tengu_defer_cap_ms` (default 10,000 ms, `chunk-4zmskew4.js:2827`). If the tool is still running at the cap, it converts to `abort-then-fork` and aborts anyway |
| Loading, text streaming | `abort-then-fork` | Flushes, keeps the trailing ≤16 KB of partial assistant text as a `prefill` (`chunk-4zmskew4.js:2402`), aborts the request |

The defer cap refuses to fire while commands are queued, while unconfirmed
background tasks would be abandoned, or while restartable subagents are running
— the last case prints `Still backgrounding after the current tool — waiting for
N running subagent(s)…` (`chunk-40sazthj.js:120`).

## Refusals

Two layers block the handoff, both emitting `tengu_left_arrow_blocked`:

- `f`/`ZYe` (`chunk-40sazthj.js:24`, `:183`) refuse when the agent view is
  disabled (`fleet-disabled`), the workspace is remote, or session persistence
  is disabled.
- `onLeftArrow` (`chunk-4zmskew4.js:2700`–`2730`, `:2802`) refuses when session
  persistence is disabled, the model ended the conversation, queued commands
  would be lost, the input holds unsent draft text, or a foregrounded task is
  running.

Backgrounding is also cancelled when an Artifact comment monitor starts after
the ← press, which asks for a fresh confirmation.

## What crosses the handoff

The child's argv is **built from scratch** at `chunk-4zmskew4.js:630` — it is
not the parent's `process.argv` filtered. It contains, in order:

| Token | Source |
|---|---|
| `--resume <transcript>` `--fork-session` | the flushed transcript |
| `--reply-on-resume` | only when the handoff happens mid-turn |
| the REPL config argv (see below) | `iz()`, `chunk-g85a3dc1.js:4151` |
| `--add-dir <dir>` | each directory added during the session |
| `--allowed-tools` / `--disallowed-tools` | rules that came from the CLI |
| `--model`, `--effort`, `--permission-mode` | current session values |
| `--agent`, `--agents`, `--append-system-prompt`, `--system-prompt-snapshot` | **`/fork` only** — these read `s5()`, which the background path replaces with `{}` |
| `--name <name>` | background only (the auto-generated worker name) |
| `-- <prompt>` | only when a prompt was supplied |

The "REPL config argv" is itself a reconstruction, fixed once at startup
(`chunk-td159npe.js:12826`) from exactly: `--settings`, `--plugin-dir`,
`--plugin-dir-no-mcp`, `--add-dir`, `--mcp-config`, `--strict-mcp-config`,
`--restricted` (`Y0e`, `chunk-3rxqsxhr.js:78`), plus `--fallback-model`,
`--allow-dangerously-skip-permissions`, `--disable-slash-commands`,
`--channels`, and `--watch-artifact`/`--watch-artifact-no-autoreact`.

**`--system-prompt` and `--system-prompt-file` appear in neither list.** There
is no code path that carries them across the handoff. `--append-system-prompt`
survives only for `/fork`. Also carried, by mechanisms other than argv:

- Process environment. The daemon builds the child env from its own
  `process.env` and overlays the job record's `env`
  (`chunk-3r0v8nsp.js:595`–`630`), so `HTTPS_PROXY`, `NODE_EXTRA_CA_CERTS`,
  `IS_SANDBOX` and `GIT_AUTHOR_*` reach the fork as long as the daemon
  inherited them. A block list is stripped on the way (`:627`).
- In-flight agents, shells, cron and Artifact monitors, via `adopt.json`.
- Trailing partial assistant text as `prefill` (abort-then-fork only).
- `settings.json` config, including `outputStyle` — read from disk, so nothing
  has to carry it.

The dropped custom system prompt is the consequence that bites: a session
launched with `--system-prompt-file` runs the **default** prompt after
backgrounding, with no warning. See
`docs/system-prompt-snapshot/README.md` § "Background sessions do not inherit
the flag" for the measured before/after. Only settings-based configuration —
notably an output style — is durable across the handoff.

## Job directory

`~/.claude/jobs/<short>/` (`chunk-5cs6j3p3.js:21096`) holds the fork's state:

| File | What |
|---|---|
| `state.json` | `state`, `intent`, `name`, `sessionId`, `cwd`, `bgIsolation`, `interactiveLineage`, and `respawnFlags` (`chunk-hntxq6bb.js:1175`, written at `chunk-bd56htwt.js:2041`) |
| `timeline.jsonl` | one record per status update — the tool descriptions the session reports (`chunk-arxpc433.js:354`) |
| `adopt.json` | hand-off payload: carried agents/shells/cron plus any `prefill` |
| `tmp/` | the fork's scratch directory |

`respawnFlags` is the spawn argv above, minus the session-identity tokens
(`--resume`, `--session-id`, `--fork-session`, `--continue`; `Tmt`,
`chunk-bd56htwt.js:3319`) and filtered to an allowlist (`Hae`,
`chunk-hntxq6bb.js:58`, which warns `[jobs] stripped non-allowlisted
respawnFlags token(s)…` on anything it drops). The daemon uses the dispatch
record's `launch.flagArgs` for the first launch and re-reads `state.json`'s
`respawnFlags` for every later respawn attempt (`chunk-3r0v8nsp.js:588`,
`:1659`), so `respawnFlags` is the authoritative record of what a respawn will
use. Value still on disk in `~/.claude/jobs/` from a session this repo's
launcher started with `--system-prompt-file` (captured under 2.1.235; the
2.1.269 construction above reproduces it, modulo an added `--effort <level>`
when the session has one):

```json
["--reply-on-resume", "--permission-mode", "bypassPermissions", "--model", "opus"]
```

Note that `--dangerously-skip-permissions` reaches the fork only as
`--permission-mode bypassPermissions`; the separate
`--allow-dangerously-skip-permissions` flag is the one that is passed through
verbatim (`chunk-td159npe.js:12350`).

## Detecting a backgrounded session from inside it

```bash
echo "$CLAUDE_JOB_DIR"              # set only in a background session
echo "$CLAUDE_CODE_SESSION_KIND"    # bg
echo "$CLAUDE_BG_BACKEND"           # daemon
echo "$CLAUDE_BG_SOURCE"            # slash | shell | fleet | spare | respawn
tr '\0' '\n' < /proc/$CLAUDE_PID/cmdline | grep -c system-prompt-file   # 0 after a handoff
```

The four markers are set by the daemon at `chunk-3r0v8nsp.js:612`–`615`;
`CLAUDE_PID` is the CLI's own pid, exported into every tool shell
(`chunk-dbb93264.js:33701`).

`CLAUDE_CODE_CHILD_SESSION` is **not** a background marker, contrary to earlier
notes here. Claude Code sets it to `1` in every child process it spawns
(`chunk-dbb93264.js:33699`), so it is `1` in an ordinary foreground session's
Bash tool too — confirmed by reading it from a foreground session. In the
background session's own environment it is in fact deleted before exec
(`chunk-3r0v8nsp.js:627`, list at `chunk-jhr9qt1t.js:17`).

## Disabling

| Knob | Where | Effect |
|---|---|---|
| `"leftArrowOpensAgents": false` | `~/.claude.json` (top level) | Disables only the ← gesture. `/background`, `claude agents`, `--bg` still work |
| `"disableAgentView": true` | `settings.json` | Disables the whole agent view: `claude agents`, `--bg`, `/background`, the on-demand daemon, and therefore the ← gesture |
| `CLAUDE_CODE_DISABLE_AGENT_VIEW=1` | environment | Same as `disableAgentView` |

Both knobs are read by one function (`chunk-vmx517s1.js:19`–`23`): the env var
at `:20`, the setting at `:21`. Everything downstream asks `bb()` (`:24`), which
is exported as `isAgentsFleetEnabled`. That single gate covers:

- `claude agents`, `--bg`/`--background`, and `claude logs|attach|stop|kill|respawn|rm`, refused at `src/cli.js:317`–`320` with `'<cmd>' is disabled by CLAUDE_CODE_DISABLE_AGENT_VIEW.` and exit 1;
- the `/background` and `/bg` slash commands, which are only registered when `bb()` is true (`chunk-dbb93264.js:221905`) — with the knob set they do not exist;
- the ← gesture, via the `fleet-disabled` refusal (`chunk-40sazthj.js:33`).

Live check on 2.1.269:

```console
$ CLAUDE_CODE_DISABLE_AGENT_VIEW=1 claude agents --json
'claude agents --json' is disabled by CLAUDE_CODE_DISABLE_AGENT_VIEW.
$ env -u CLAUDE_CODE_DISABLE_AGENT_VIEW claude agents --json
[ { "pid": …, "kind": "interactive", … } ]
```

`leftArrowOpensAgents` is read as `oe().leftArrowOpensAgents !== !1`
(`chunk-4zmskew4.js:38768`), so an absent key means enabled. It is a
global-config key — `~/.claude.json` under `$CLAUDE_CONFIG_DIR || ~`, listed at
`chunk-5cs6j3p3.js:25662`. The `/config` dialog exposes it as the toggle
**`← opens agents`** (`chunk-ve1cwn02.js:1043`), alongside the newer
**`Open agents view by default`** (`defaultToAgentsView`). There is no
`claude config set -g` in 2.1.269 — that subcommand does not exist; edit the
file or use `/config`.

For a launcher that depends on `--system-prompt-file`, `disableAgentView` is the
correct knob: it also closes `/background`, the other path that drops the flag.
This repo's launcher, `scripts/claude.sh`, sets it:

```bash
# in scripts/claude.sh, before exec claude
export CLAUDE_CODE_DISABLE_AGENT_VIEW=1
```

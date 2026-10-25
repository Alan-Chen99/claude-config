# Background Sessions (agent view / FleetView)

Verified against claude-cli **2.1.289** in the decompile at
`/repos/claude-code-decompiled`, plus one live check of the disable knob under
2.1.269. Citations are `src/chunk-<hash>.js:<line>` there; hashes rotate every
build and minified names are **per-file**, so the address is the `<file>:<line>`
pair, never the name — `ENe` is the job-dir writer at `chunk-mdxeekqd.js:2857`
and something unrelated at `chunk-j0tbz6ra.js:192411`. Re-resolve by grepping the
string literal the behaviour touches.

## What happens

Backgrounding does not detach the process you are looking at. Claude Code
allocates a **new session UUID**, writes a job directory, dispatches a **fork**
to the background daemon which resumes the transcript, and turns the TUI into
the agents view (FleetView). Two processes exist afterwards; the fork is the one
talking to the model. `Your conversation moved to the background — enter opens
it · …` (`chunk-05z051sc.js:4770`) marks the handoff;
`Backgrounding after the current tool finishes…` (`chunk-mdxeekqd.js:3647`)
marks it armed and waiting; `Cannot open agents — …` is a refusal.

Code path: `onLeftArrow` (`chunk-mdxeekqd.js:3457`, a method of the
background-gesture class at `:3177`) → the private dispatcher at `:3395` → the
job-dir and `adopt.json` writer at `:2857` → the respawn-argv builder at `:1985`
→ the daemon dispatch that writes `state.json` (`chunk-k4cpfn3d.js:905`).

## Trigger

1. **← on an empty prompt**, double-tapped. Installed only when
   `leftArrowOpensAgents !== !1` (`chunk-mdxeekqd.js:41083`) and the handoff is
   otherwise available (`ONe`, `:3773`); the first press only arms the hint
   `Press ← again to open agents` (`:3806`). The gesture machine
   (`chunk-65wf35er.js:1624`) rejects a burst keypress as not-solo, and
   `tengu_left_arrow_editing_guard` (default true) suppresses it for 2 s after
   typing.
2. **A click on a job chip**: `requestAttach(jobId)`
   (`chunk-92hm4yb6.js:5805` → `chunk-mdxeekqd.js:3253`) defers to
   `onAttachRequest` (`:3352`), which runs the same path with an
   `autoOpenJobId` and its own confirm states (`attach-arm`/`attach-absorb`).
3. **`/background`** (alias `/bg`, `chunk-t6012gc3.js:11`), reaching the same
   argv builder with `via: 'command'` (`chunk-mdxeekqd.js:2371`) — same spawn,
   none of the `onLeftArrow` guards. `/fork` (`chunk-8q14tvww.js:603`) reaches
   it with `keepParent: true`: a different operation, the parent stays alive,
   and it carries strictly more (below).

`defaultToAgentsView` (global config, `src/cli.js:572`, off by default at
`chunk-f3ak9604.js:403`) is **not** a handoff — it makes a fresh `claude` open
the agent view instead of a REPL, moving no existing conversation.

No timer, idle watcher or automatic handoff path exists in the 2.1.289 source,
which does not settle it: under 2.1.235 six background jobs came out of one
interactive session in an hour, three from one prompt, with no deliberate ←
press reported. Unreproduced since, and the launcher disables the agent view, so
it cannot recur here. Treat the trigger as **not reproduced**; the consequences
below hold regardless of what fires it.

## Modes and refusals

`p(isLoading, betweenCalls)` (`chunk-9d4hz6n9.js:22`, reached through `d` at
`:26` / `vMt` at `:191`) picks the mode. `idle-fork` backgrounds at once.
`defer-then-fork`, with a tool running, prints `Backgrounding after the current
tool finishes…` and arms a timer capped by `tengu_defer_cap_ms` (default
10,000 ms, `chunk-mdxeekqd.js:3582`), converting to `abort-then-fork` and
aborting anyway if the tool outlives the cap. `abort-then-fork`, with text
streaming, flushes, keeps the trailing ≤16 KB of partial assistant text as a
`prefill` (`:2958`) and aborts. The cap will not fire while commands are
queued, while unconfirmed background tasks would be abandoned, or while
restartable subagents are running — the last prints `Still backgrounding after
the current tool — waiting for N running subagent(s)…`
(`chunk-9d4hz6n9.js:122`).

Two layers block the handoff, both emitting `tengu_left_arrow_blocked`.
`d`/`vMt` (`chunk-9d4hz6n9.js:26`, `:191`) refuse — as telemetry only, with no
message in the transcript (`chunk-mdxeekqd.js:3535`) — when the agent view is
disabled (`fleet-disabled`), the workspace is remote, session persistence is
disabled, or an external load is in flight. The gesture class's own precheck
(`chunk-mdxeekqd.js:3310`–`3341`) refuses *with* a message when session
persistence is disabled, the session started with `--project-config-root` (a
background copy would not get the flag, so it would read the working folder's
hooks and settings), the model ended the conversation, queued commands would be
lost, or the input holds unsent draft text. A handoff is also cancelled when an
Artifact comment monitor starts after the ← press, which asks for fresh
confirmation (`:3510`). Entering the agents view additionally needs **workspace
trust**: an untrusted directory gets the trust dialog, which a non-interactive
run cannot answer (`src/cli.js:794`–`797`, decision at
`chunk-sngkkz5k.js:412`).

## What crosses the handoff

The child's argv is **built from scratch** at `chunk-mdxeekqd.js:2119` — not the
parent's `process.argv` filtered. In order: `--resume <transcript>`
`--fork-session`; `--reply-on-resume` when the handoff happens mid-turn; the
REPL config argv with `--add-dir` re-derived from the CLI-sourced working
directories (`VBs`, `chunk-fnsjs1v2.js:936`); `--allowed-tools` /
`--disallowed-tools` for rules that came from the CLI; `--model`, `--effort`,
`--permission-mode` from the current session; `--agent`, `--agents`,
`--append-system-prompt`, `--system-prompt-snapshot` **for `/fork` only** (they
read a launch-options snapshot the background path replaces with `{}`);
`--name <name>` for background only (the auto-generated worker name); and
`-- <prompt>` when a prompt was supplied.

The REPL config argv is itself a reconstruction, fixed once at startup
(`chunk-6d8swme1.js:4679`) from exactly `--settings`, `--managed-settings`,
`--plugin-dir`, `--plugin-dir-no-mcp`, `--add-dir`, `--mcp-config`,
`--setting-sources`, `--strict-mcp-config`, `--restricted`
(`chunk-pfc5159p.js:89`), plus `--fallback-model`,
`--allow-dangerously-skip-permissions`, `--disable-slash-commands`,
`--channels` and `--watch-artifact`/`--watch-artifact-no-autoreact`.
`--setting-sources` and `--managed-settings` are in it so a restricted parent's
background children inherit the restriction.

**`--system-prompt` and `--system-prompt-file` appear in neither list**, and no
code path carries them across; `--append-system-prompt` survives only for
`/fork`. What crosses by other mechanisms: the process environment, which the
daemon builds from its own `process.env` overlaid with the job record's `env`
and less a block list (`chunk-kj2kfe1q.js:617`–`655`, strip at `:651`), so
`HTTPS_PROXY`, `NODE_EXTRA_CA_CERTS`, `IS_SANDBOX` and `GIT_AUTHOR_*` reach the
fork if the daemon inherited them; session-scoped `--add-dir` entries on that
same channel as `CLAUDE_RELAUNCH_SESSION_ADD_DIRS` (`chunk-fnsjs1v2.js:951`,
read and unset at `chunk-6d8swme1.js:338`); in-flight agents, shells, cron and
Artifact monitors via `adopt.json`; the trailing partial assistant text as
`prefill` (abort-then-fork only); and `settings.json` config including
`outputStyle`, read from disk, with no `--output-style` flag that could fail to
carry it.

The dropped custom system prompt is the consequence that bites: a session
launched with `--system-prompt-file` runs the **default** prompt after
backgrounding, with no warning — `docs/system-prompt-snapshot/README.md`
§ "Background sessions do not inherit the flag" has the measured before/after.
Only settings-based configuration, notably an output style, is durable.

## Job directory

`~/.claude/jobs/<short>/` (`chunk-ajtyjx88.js:34335`) holds `state.json` —
`state`, `intent`, `name`, `sessionId`, `cwd`, `bgIsolation`,
`interactiveLineage`, `respawnFlags` (schema `chunk-fnsjs1v2.js:1136`–`1153`,
name at `:1220`, written at `chunk-k4cpfn3d.js:1004`) — plus `timeline.jsonl`,
one record per status update carrying the tool descriptions the session reports
(`chunk-dc0nzty2.js:1334`); `adopt.json`, the hand-off payload of carried
agents/shells/cron and any `prefill`; and `tmp/`, the fork's scratch directory.

`respawnFlags` is the spawn argv above minus the session-identity tokens
(`--resume`, `--session-id`, `--fork-session`, `--continue`;
`chunk-k4cpfn3d.js:2483`), filtered to an allowlist (`chunk-8w56k4pg.js:102`,
warning `[jobs] stripped respawnFlags token(s) that a restart does not re-apply: …` at `:123` on
anything it drops). The daemon launches first from the dispatch record's
`launch.flagArgs` (`chunk-kj2kfe1q.js:610`) and re-reads `state.json`'s
`respawnFlags` for every later respawn (`:1731`), so `respawnFlags` is the
authoritative record of what a respawn will use. One such value still on disk,
from a session this repo's launcher started with `--system-prompt-file`
(captured under 2.1.235; the 2.1.289 construction reproduces it, modulo an added
`--effort <level>`):
`["--reply-on-resume", "--permission-mode", "bypassPermissions", "--model", "opus"]`.
`--dangerously-skip-permissions` reaches the fork only as `--permission-mode
bypassPermissions`; the separate `--allow-dangerously-skip-permissions` is the
one passed through verbatim (`chunk-6d8swme1.js:4101`).

## Detecting a backgrounded session from inside it

The daemon sets four markers at `chunk-kj2kfe1q.js:634`–`637`:
`CLAUDE_JOB_DIR` (set in no other kind of session),
`CLAUDE_CODE_SESSION_KIND=bg`, `CLAUDE_BG_BACKEND=daemon`, and
`CLAUDE_BG_SOURCE` (`slash` | `shell` | `fleet` | `spare` | `respawn`). The
handoff also shows in the process: `tr '\0' '\n' < /proc/$CLAUDE_PID/cmdline |
grep -c system-prompt-file` is 0 afterwards, `CLAUDE_PID` being the CLI's own
pid, exported into every tool shell (`chunk-6h7ejyet.js:13268`).

`CLAUDE_CODE_CHILD_SESSION` is **not** a background marker, contrary to earlier
notes here: cc sets it to `1` in every child it spawns
(`chunk-6h7ejyet.js:13266`), so it is `1` in an ordinary foreground session's
Bash tool too — confirmed by reading it from one — and in a background session's
own environment it is deleted before exec (`chunk-kj2kfe1q.js:651`, list at
`chunk-kjgmmff6.js:47`).

## Disabling

`"leftArrowOpensAgents": false` in `~/.claude.json` (top level) disables only
the ← gesture; `/background`, `claude agents` and `--bg` still work.
`"disableAgentView": true` in `settings.json`, or
`CLAUDE_CODE_DISABLE_AGENT_VIEW=1` in the environment, disables the whole agent
view. Both are read by one function (`chunk-b9vagsrs.js:19`–`23`): the env var
at `:20`, the setting at `:21`. Everything downstream asks `CE()` (`:24`),
exported as `isAgentsFleetEnabled`. That single gate covers:

- `claude agents`, `--bg`/`--background` and `claude logs|attach|stop|kill|respawn|rm`, refused at `src/cli.js:459`–`463` with `'<cmd>' is disabled by CLAUDE_CODE_DISABLE_AGENT_VIEW.` and exit 1 (`chunk-b9vagsrs.js:74`);
- the `/background` and `/bg` slash commands, registered only when `CE()` is true (`chunk-j0tbz6ra.js:88879`) — with the knob set they do not exist;
- the ← gesture, via the `fleet-disabled` refusal (`chunk-9d4hz6n9.js:37`);
- `claude --resume <id>` and the resume picker *opening* a session already running in the background instead of resuming it, any prompt delivered to it as a message (`chunk-z2rjm3ha.js:168`–`178`, gate `tengu_resume_open_live_bg`, default true, entry `chunk-kfdf5pq3.js:2818`). With the knob set that resume is refused outright and the advice is `claude attach <jobId>`, which the same knob disables.

Live check on 2.1.269: `CLAUDE_CODE_DISABLE_AGENT_VIEW=1 claude agents --json`
printed `'claude agents --json' is disabled by CLAUDE_CODE_DISABLE_AGENT_VIEW.`;
unset, it printed the job array.

`leftArrowOpensAgents` is read as `leftArrowOpensAgents !== !1`
(`chunk-mdxeekqd.js:41083`), so an absent key means enabled. It is a
global-config key — `~/.claude.json` under `$CLAUDE_CONFIG_DIR || ~`, listed at
`chunk-ajtyjx88.js:3618` — and `/config` exposes it as the toggle
**`← opens agents`** (`chunk-f3ak9604.js:416`), beside **`Open agents view by
default`** (`defaultToAgentsView`). There is no `claude config set -g`; edit the
file or use `/config`.

For a launcher that depends on `--system-prompt-file`, `disableAgentView` is the
right knob: it also closes `/background`, the other path that drops the flag.
`scripts/claude.sh` exports `CLAUDE_CODE_DISABLE_AGENT_VIEW=1` before
`exec claude`.

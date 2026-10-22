# Subagent backgrounding: which knobs, and what each costs

Verified against claude-cli **2.1.289**; citations are `src/chunk-<hash>.js:<line>` in
`/repos/claude-code-decompiled`, each with a literal to re-find it by. The 2.1.235
investigation behind the gate is `notes/subagent-backgrounding-overrides-run-in-background.md`;
the prompt side is `sys_prompt/README.md`, "`a turn ending only to wait on background work`".

## `CLAUDE_CODE_FORK_SUBAGENT=1`: every subagent in the background, in every mode

Unset, the fork gate is on for an interactive session and off under `-p` (`xmo()`/`Amo()`,
`src/chunk-wgfrtm7w.js:58703`, near `"tengu_fork_subagent_enabled"`), so a `claude -p` —
prompt-tests, ralph, telegram — would see a different Agent tool. `settings.json` `env` sets
`1` so both see the same one. With the gate on, the schema drops `run_in_background`
(`der() || Wne()`, `src/chunk-845w7yx9.js:406`) and `forceAsync` backgrounds every call
(`:691`; the disjunction is `wo()` at `:227`): the tool result reads `Async agent launched
successfully`, the report arrives as a `<task-notification>` whose `<result>` holds it, and
`subagent_type: "fork"` — the parent's full context and prompt — is available. Two exceptions:
the built-in `web-fetch` agent (`OE()`), and a `-p` subagent's own Agent call, which stays in
the foreground; an interactive subagent's is backgrounded.

A subagent's run ends at its report and nothing re-invokes it. Probed 2026-10-22, `=1`, `-p`,
haiku: a general-purpose agent whose `sleep 45` was blocked re-ran it with
`run_in_background`, ended its turn and reported "Waiting for the sleep command to
complete..."; the shell was killed at exit. `agent-tools/src/hook_subagent.rs` tells every
subagent so.

Every `Stop` payload carries `background_tasks[]`, agents as `type: "subagent"`
(`src/chunk-wgfrtm7w.js:92381`, `background_tasks: m2t(`), so
`src/claude_config/ntfy_hook.py` holds the "Done" push while one runs. A `Monitor` is a
`"shell"` task there, like a backgrounded Bash call, so a Bash wait still gets a "Done". The
`idle_prompt` notification waits while a background agent runs
(`backgroundAgents.getSnapshot()`, `src/chunk-8w9chsdq.js:2157`).

## `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`: `-p` waits as long as interactive

When a `-p` turn ends, a running background agent or workflow holds the process and each
completion starts a turn; a background shell is killed after 5 s (`uh()`, `UU()`,
`src/chunk-mgxpmmsq.js:1870`). At the ceiling — default 600,000 ms of the main session having
nothing to do, restarted whenever it does — the agents are killed (`stopped`), with `Background
tasks still running after Ns; terminating.` on stderr (`:2033`). `0` turns the ceiling off
(`U > 0 &&`, `:2016`). Probed 2026-10-22 with an agent busy 40 s: at `10000` the agent was
`killed` and the run exited 0 with the wait turn's line as its `result`, so a driver sees no
failure; at `0` it waited and the final turn delivered the report. The cost: a hung agent holds
a `-p` process until an outer timeout stops it — `PROMPT_TEST_TIMEOUT` in
`scripts/prompt-test-cc.sh`, a year in ralph's `build.yml`.

## The alternatives

`CLAUDE_CODE_FORK_SUBAGENT=0`, the arrangement until 2026-10-22, keeps the parameter and
backgrounds a call unless it is literally `false` (`!h && p !== !1`); a prompt rule asking for
`false` held 9 of 9 calls on 2026-09-16. It costs `fork`, and every report the model waits for
then arrives inline.

`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` is the only setting that makes the foreground a
guarantee with no help from the model, bar a remote-isolation launch and a plugin's
background-launch rule. It costs the whole background-task facility. Measured, one interactive
session each:

| | `DISABLE_BACKGROUND_TASKS=1` | background tasks on |
| --- | --- | --- |
| Bash `run_in_background` | absent from the schema | present; a task id, and the agent re-invoked when the command exits |
| A command outliving its `timeout` | killed, `Exit code 143` | moved to the background with a task id; upstream's exemption for a `sleep`-first command is unreachable behind `hook_pre.rs`'s prelude (`docs/agent-tools-status-reference.md`) |
| `BACKGROUNDED:` from `hook_post.rs` | cannot fire: no tool response carries `backgroundTaskId` | fires, naming the cause, the task id and the `long-bash` skill |
| Foreground `sleep` | permitted | blocked at 25 s or more as the first statement only (`echo hi; sleep 25` runs) |

## Paths that ship but are not exercised here

MCP auto-background (`src/chunk-rkpajbmn.js:324`), the Ctrl+B affordance
(`src/chunk-1r3smv21.js:139`), observer agents (`src/chunk-909q38pa.js:26`) and forked skills
(`src/chunk-st999tz2.js:35`) open on the background-tasks checks in `src/chunk-eps276jq.js`
(`:14`, `:17`, `:21`), all on here. `background` defaults to true for a skill declaring
`context: fork`; `background: false` keeps the caller waiting (`src/chunk-wgfrtm7w.js:17128`).
`CLAUDE_AUTO_BACKGROUND_TASKS`, unset here, moves a foreground subagent to the background after
its interval (`$o`, `src/chunk-845w7yx9.js:374`).

## Print mode: what outlives a turn

Measured 2026-10-01 on 2.1.269 (`notes/print-mode-task-lifetime.md`,
`notes/foreground-wait-under-print-mode.md`); the agent row 2026-10-22 on 2.1.289. Under
`claude -p` the turn ending is the process ending, except:

| Running at turn end | `-p` does |
| --- | --- |
| a background agent or workflow | holds the process and starts a turn per completion, up to the ceiling above |
| Bash `run_in_background` | kills it (`task_updated status: killed`) and exits |
| a foreground Bash call | holds the process until it returns, up to its `timeout` — 10 min unless `BASH_MAX_TIMEOUT_MS` in settings `env` raises it (2,147,483,647 is the timer's bound); a `Monitor` event fired meanwhile is dropped when the turn ends with nothing running |
| `Monitor` | stays up: each event and the completion re-invoke the model; `timeout_ms` defaults to 5 min, is refused above an hour, and is clamped to 10 min under `-p`, 30 interactive, with no `persistent` escape in the schema |

A `Stop` hook can block the turn end (`{"decision": "block"}`; `stop_hook_active` advisory;
`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` consecutive blocks, default 8), holding the process while it
runs up to its settings `timeout`, a kill being no decision. `skills/telegram-hitl` waited that
way until 2026-10-01 and now waits in the foreground.

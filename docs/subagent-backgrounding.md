# Subagent backgrounding: which knobs, and what each costs

Verified against claude-cli **2.1.310**; citations are `src/chunk-<hash>.js:<line>` in
`/repos/claude-code-decompiled`, each with a literal. The 2.1.235 investigation:
`notes/subagent-backgrounding-overrides-run-in-background.md`; the prompt side:
`sys_prompt/README.md`, "`a turn ending only to wait on background work`".

## `CLAUDE_CODE_FORK_SUBAGENT=1`: every subagent in the background, in every mode

Unset, the fork gate is on in every mode (`Gdn()`, `src/chunk-j0tbz6ra.js:90392`, near
`"tengu_fork_subagent_enabled"`), but only an env value forces the background under `-p`
(`rmt()`, `:90407`), so an unset `claude -p` (prompt-tests, ralph, telegram) keeps
`run_in_background`; `settings.json` `env` sets `1`. With `rmt()` true, the schema drops
`run_in_background` (`Vwt() || rmt()`, `src/chunk-qnd362wh.js:361`) and `forceAsync`
backgrounds every call (`:664`; the disjunction is in `bo()`, `:128`): the tool result reads
`Async agent launched successfully`, the report arrives as a `<task-notification>` whose
`<result>` holds it, and `subagent_type: "fork"` (the parent's full context and prompt) is
available. Not backgrounded: the built-in `web-fetch` agent (`av()`) and a `-p` subagent's own
Agent call (an interactive subagent's is).

A subagent that ends its turn with a shell of its own running is kept interactively, resumed
when the shell ends or a message arrives, and every turn end notifies the main thread; under
`-p` the shell's notification waits for the main thread, whose exit kills the shell
(`notes/cc-2.1.289-subagent-waits.md`). `agent-tools/src/hook_subagent.rs` asks every subagent
to wait out its work, and `hook_post.rs`'s `BACKGROUNDED:` notice gives a subagent, or a `-p`
main thread, the `agent-tools wait` call.

Every `Stop` payload carries `background_tasks[]`, agents as `type: "subagent"`
(`src/chunk-j0tbz6ra.js:139700`, `background_tasks: bPn(`), so
`src/claude_config/ntfy_hook.py` holds the "Done" push while one runs. A `Monitor` is a
`"shell"` task there, like a backgrounded Bash call, so a Bash wait still gets a "Done". The
`idle_prompt` notification waits while a background agent runs
(`backgroundAgents.getSnapshot()`, `src/chunk-mdxeekqd.js:962`).

## `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`: `-p` waits as long as interactive

When a `-p` turn ends, a running background agent or workflow holds the process and each
completion starts a turn, as does a background shell unless `"tengu_tidy_sloth"` is off
(`ppt()`, `src/chunk-j0tbz6ra.js:5633`; then it is killed after 5 s). At the ceiling — default
600,000 ms of the main session having nothing to do, restarted whenever it does — the agents are
killed (`stopped`), with `Background tasks still running Ns after the last turn` on stderr
(`src/chunk-7rnqxvcm.js:3853`). `0` turns the ceiling off (`x > 0 &&`, `:3833`). Probed
2026-10-22 with an agent busy 40 s: at `10000` the agent was `killed` and the run exited 0 with
the wait turn's line as its `result`, so a driver sees no failure; at `0` it waited and the
final turn delivered the report. The cost: a hung agent holds a `-p` process until an outer
timeout: `PROMPT_TEST_TIMEOUT` in `scripts/prompt-test-cc.sh`, a year in ralph's
`build.yml`.

## The alternatives

`CLAUDE_CODE_FORK_SUBAGENT=0`, the arrangement until 2026-10-22, keeps the parameter and
backgrounds a call unless it is literally `false` (`!_ && f !== !1`,
`src/chunk-qnd362wh.js:128`); a prompt rule asking for `false` held 9 of 9 calls on 2026-09-16.
It costs `fork`, and every report the model waits for then arrives inline.

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

MCP auto-background (`src/chunk-687969by.js:423`), the Ctrl+B affordance
(`src/chunk-hy2g8tcy.js:138`), observer agents (`src/chunk-28117reb.js:29`) and forked skills
(`src/chunk-jgs1ysys.js:96`) open on the background-tasks checks in `src/chunk-m18k9mtt.js`
(`:14`, `:28`, `:31`), all on here. Interactively, `background` defaults to true for a skill
declaring `context: fork`; `background: false` keeps the caller waiting
(`src/chunk-jgs1ysys.js:97`). `CLAUDE_AUTO_BACKGROUND_TASKS` (unset here) backgrounds a
foreground subagent after 2 min (`zo()`, `src/chunk-qnd362wh.js:329`).

## Print mode: what outlives a turn

Measured 2026-10-01 on 2.1.269 (`notes/print-mode-task-lifetime.md`,
`notes/foreground-wait-under-print-mode.md`); the agent row 2026-10-22 on 2.1.289. Under
`claude -p` the turn ending is the process ending, except:

| Running at turn end | `-p` does |
| --- | --- |
| a background agent or workflow | holds the process and starts a turn per completion, up to the ceiling above |
| Bash `run_in_background` | kills it and exits (2.1.310's source holds it, above) |
| a foreground Bash call | holds the process until it returns, up to its `timeout` — 10 min unless `BASH_MAX_TIMEOUT_MS` in settings `env` raises it (2,147,483,647 is the timer's bound); a `Monitor` event fired meanwhile is dropped when the turn ends with nothing running |
| `Monitor` | stays up: each event and the completion re-invoke the model; `timeout_ms` defaults to 5 min, is refused above an hour, and is clamped to 10 min under `-p`, 30 interactive, with no `persistent` escape in the schema |

A `Stop` hook can block the turn end (`{"decision": "block"}`; `stop_hook_active` advisory;
`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` consecutive blocks, default 8), holding the process while it
runs up to its settings `timeout`, a kill being no decision; `skills/telegram-hitl` waited that
way until 2026-10-01.

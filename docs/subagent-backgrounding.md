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

A subagent ending its turn with its own shell running is kept interactively, resumed when the
shell ends or a message arrives, each turn end notifying the main thread; under `-p` the
shell's notification waits for the main thread, whose exit kills the shell
(`notes/cc-2.1.289-subagent-waits.md`; so on 2.1.310, 2026-10-25).
`agent-tools/src/hook_subagent.rs` and `hook_post.rs`'s `BACKGROUNDED:` notice answer that with
`agent-tools wait`.

`src/claude_config/ntfy_hook.py` reads the `Stop` payload's `background_tasks[]`
(`src/chunk-j0tbz6ra.js:139700`, `background_tasks: bPn(`); cc's own `idle_prompt` waits while
a background agent runs (`backgroundAgents.getSnapshot()`, `src/chunk-mdxeekqd.js:962`).

## `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`: `-p` waits as long as interactive

When a `-p` turn ends, a running background agent or workflow holds the process and each
completion starts a turn, as does a background shell unless `"tengu_tidy_sloth"` is off
(`ppt()`, `src/chunk-j0tbz6ra.js:5633`; then it is killed after 5 s). At the ceiling (default
600,000 ms of the main session idle, restarted whenever it has work) the agents are killed
(`stopped`), with `Background tasks still running Ns after the last turn` on stderr
(`src/chunk-7rnqxvcm.js:3855`). `0` turns the ceiling off (`x > 0 &&`, `:3833`). Probed
2026-10-22, an agent busy 40 s: at `10000` it was `killed` and the run exited 0, no failure to
a driver; at `0` the final turn delivered the report. The cost: a hung agent holds `-p`
until an outer timeout: `PROMPT_TEST_TIMEOUT` in `scripts/prompt-test-cc.sh`, a year in
ralph's `build.yml`.

## The alternatives

`CLAUDE_CODE_FORK_SUBAGENT=0` (to 2026-10-22) keeps the parameter and backgrounds a call unless
it is literally `false` (`!_ && f !== !1`, `src/chunk-qnd362wh.js:128`); a prompt rule asking
for `false` held 9 of 9 calls on 2026-09-16. It costs `fork`, and every report the model waits
for then arrives inline.

`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` alone makes the foreground a guarantee with no help
from the model, bar a remote-isolation launch and a plugin's background-launch rule, at the cost
of the whole background-task facility. Measured, one interactive session each: Bash loses
`run_in_background`, a command outliving its `timeout` is killed (`Exit code 143`) rather than
backgrounded, `hook_post.rs`'s `BACKGROUNDED:` cannot fire (no tool response carries
`backgroundTaskId`), and foreground `sleep` is no longer blocked.
The facility also gates, unexercised here, MCP auto-background, the Ctrl+B affordance,
observer agents and forked skills (`src/chunk-m18k9mtt.js:14`, `:28`, `:31`); interactively a
skill declaring `context: fork` defaults to `background: true` (`background: false` keeps the
caller waiting, `src/chunk-jgs1ysys.js:97`).
`CLAUDE_AUTO_BACKGROUND_TASKS` (unset here) backgrounds a foreground subagent after 2 min
(`zo()`, `src/chunk-qnd362wh.js:329`).

## Print mode: what outlives a turn

Under `claude -p` the turn ending is the process ending, except for the background agents,
workflows and main-thread shells above (a subagent's shell is killed) and these, measured
2026-10-01 on 2.1.269 (`notes/print-mode-task-lifetime.md`,
`notes/foreground-wait-under-print-mode.md`; the clamps and their citations:
`skills/telegram-hitl/README.md`, "Harness facts the design rests on"):

- A foreground Bash call holds the process until it returns, up to its `timeout` (10 min unless
  settings `env` `BASH_MAX_TIMEOUT_MS` raises it); a `Monitor` event fired meanwhile is dropped
  when the turn ends with nothing running.
- A `Monitor` stays up: each event and the completion re-invoke the model, `timeout_ms` clamped
  to 10 min under `-p`.
- A `Stop` hook can block the turn end (`{"decision": "block"}`) up to
  `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` consecutive times, default 8, holding the process while it
  runs up to its settings `timeout`.

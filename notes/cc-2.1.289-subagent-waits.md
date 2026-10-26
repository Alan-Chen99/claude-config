# A subagent's foreground call is deaf until it returns, and only an interactive subagent survives ending its turn to wait

> **2.1.310 (measured 2026-10-25).** Finding 6 still holds: under `claude -p` a subagent's
> background shell was `killed` 8 s after the main thread's last `result`, as the new held-shell
> test covers only `e.agentId === void 0`. A `-p` main thread's own shell now holds the process
> and starts a turn when it ends (`docs/subagent-backgrounding.md`), so `agent-tools wait`
> for a main thread is told only when its result carries `backgroundEndsWithFinalResponse`.
> Finding 1 is the default only: an agent whose frontmatter sets `experimental.cacheTtl: 1h`
> (`agents/gp-cache1h.md`) wrote its cache at 1h (2.1.310, 2026-10-25). Finding 2 held on
> 2.1.310, read in source too; `agent-tools wait` now returns on a queued message, and progress
> summaries refresh a waiting subagent's cache (`notes/cc-2.1.310-subagent-wait-costs.md`).
> Everything below is 2.1.289's and stands as measured.

Investigated 2026-10-24 (UTC) on Claude Code **2.1.289**, `CLAUDE_CODE_FORK_SUBAGENT=1`, sonnet
unless named. P1-P4, P9 and P12 ran under `claude -p`; P5-P6 interactive; P7, P8, P10 and P11 under
`agent-tools claude -p` from this checkout. Led to `agent-tools wait` and the "Waiting in the turn"
section of `skills/long-bash/SKILL.md`.

## Findings

1. **A subagent caches for 5 minutes.** In the 400 newest subagent transcripts here (2.1.289, ten
   days), 35,155 TTL-tagged cache writes were `ephemeral_5m` and 1 `ephemeral_1h`. A `-p` main
   thread wrote at 1h (P1), as the interactive one does (`notes/background-wait-cache-expiry.md`).
2. **Nothing cuts a subagent's foreground Bash call short.** P1: its 30 s background job's
   `<task-notification>` reached it as a `queued_command` attachment when its 120 s call
   returned, 90 s late. P2: main's SendMessage (`Message queued for delivery to <id> at its next
   tool round.`) arrived when its 150 s call returned, 130 s late. In the main thread a typed
   message does background a running call (`backgroundedToDeliverMessage`, 13 s, 2026-10-22).
3. **Its own job's notification goes to the subagent while it runs** (P1), not to main.
4. **Wrappers.** Main to subagent: `The coordinator sent a message while you were working:` …
   `Address this before completing your current task.` Agent to agent: `<agent-message
   from="<id>">`, ending `After completing your current task, decide whether/how to respond`.
   Subagent to `to: "main"`: `Message queued for the main conversation's next turn.`; an idle
   main thread starts a turn on it in both modes (P2, P3, P6).
5. **Interactive: ending the turn with a shell running keeps the subagent.** Main is notified
   (`This agent stopped with background work of its own still running. It may resume on its
   own…`), and each completion of the shell resumes the subagent (P5: a timer and a job, two
   resumes, three notifications to main). A SendMessage to it returned `Resuming agent <id>` and
   it started a turn at once (P6).
6. **`claude -p`: the same turn end loses the job.** The shell's notifications queue on main
   (P4, while main sat in a 150 s call) and reach the subagent only when main's turn ends, which
   is when the process exits: P4's subagent got both at that instant and wrote nothing more. With
   main idle, the exit kills the job (P3: `final(143)` 30 s into 75 s). A haiku Explore read of
   the decompile finds an `isInteractive()` test in the routing that keeps a stopped agent.
7. **Plugin events** (P6): `turn.start` fires for main-thread turns only; `turn.complete` carries
   a subagent's `agentId`; `classic.Stop`'s `background_tasks` lists a running subagent as
   `subagent` and, once it stopped, its running shell as `shell`.
8. **Without a pointer, a subagent writes its own wait.** P7, the hooks unchanged: told its
   command takes six minutes, it loaded neither the listed skill nor the one the `BACKGROUNDED:`
   notice named, and blocked on an `until grep` loop. Main's message, sent 40 s in, reached it
   5m21s later with the job done; its next request read 0 and wrote 12,991. P8, with the
   `SubagentStart` clause and the notice's subagent sentence: it loaded the skill, waited 4m00s,
   answered 4 s later at step 25 of 36, read 14,320 (the prior read plus write), and its second
   wait returned within a second of the job's end. P10 (opus) and P11 did the same.
9. **Hooks see the attended flag**: a `-p` `PostToolUse` hook's environment carried
   `CLAUDE_CODE_SESSION_ATTENDED=0` (P12).
10. **`-p` stops an untimed background job at 30 minutes.** P9: `sleep 1900` launched with no
    `timeout` was stopped at 30m00s, notified `<status>killed</status>` with `stopped after
    reaching its background time limit`, its file ending `[killed]`.

## What follows

- A subagent, and a `-p` main thread, waits inside its turn in bounded calls: each return
  delivers queued messages, and one inside 5 minutes re-reads the cache. `agent-tools wait`
  defaults to 240 s, leaving a minute to generate the next request.
- Ending the turn, open to an interactive subagent, costs main a turn per subagent turn end, and
  a timer chain to keep the 5m cache one per timer; so the skill teaches the loop in both modes.
- Arithmetic, not measured: a 5m rewrite costs 1.25x the prefix and a read 0.1x, so 4-minute
  wakes pay for themselves for about 11 wakes, 45-50 min. Past that the loop costs more than one
  rewrite would, and is kept for the 4-minute bound it puts on a message's delivery.

## Probe shape

`claude -p --model sonnet --output-format json < task.txt` from a scratch cwd: main spawns a
general-purpose subagent with numbered steps (a background `agent-tools run --desc job bash -c
'sleep N'`, then a foreground `sleep M` through `agent-tools run`, or a turn end), then sleeps 20 s
and sends a message. Interactive: `claude` in `tmux -L agent-<random>`, with
`CLAUDE_CODE_CHILD_SESSION` unset and `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1` (a session started
inside Claude Code inherits the marker and saves no transcript). Timelines: the JSONL
`queue-operation`, `attachment` and tool records.

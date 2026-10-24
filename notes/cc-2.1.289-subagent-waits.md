# A subagent's foreground call is deaf until it returns, and only an interactive subagent survives ending its turn to wait

Investigated 2026-10-24 (UTC) on Claude Code **2.1.289**, `CLAUDE_CODE_FORK_SUBAGENT=1`, sonnet
subagents of a sonnet main thread. P1-P4 ran under `claude -p`, P5-P6 in an interactive session,
P7-P11 under `agent-tools claude -p` from this checkout.
Led to `agent-tools wait` and the "Waiting in the turn" section of `skills/long-bash/SKILL.md`.

## Findings

1. **A subagent caches for 5 minutes.** Of the cache writes carrying a TTL in the 400 newest
   subagent transcripts on this machine (all 2.1.289, ten days), 35,155 were `ephemeral_5m` and 1
   `ephemeral_1h`. A `-p` main thread wrote at 1h (P1), as the interactive one does
   (`notes/background-wait-cache-expiry.md`).
2. **Nothing cuts a subagent's foreground Bash call short.** P1: a 30 s background job ended
   during a 120 s foreground call, and its `<task-notification>` reached the subagent as a
   `queued_command` attachment when the call returned, 90 s later. P2: main's SendMessage
   returned `Message queued for delivery to <id> at its next tool round.` and reached the
   subagent 130 s later, when its 150 s call returned. The main thread differs: a message the
   user types backgrounds a running call (`backgroundedToDeliverMessage`, 13 s after the message
   in a 2026-10-22 transcript).
3. **A subagent's own notification goes to it while it runs** (P1), not to the main thread.
4. **Message wrappers.** Main to subagent: `The coordinator sent a message while you were
   working:` … `Address this before completing your current task.` Agent to agent: `Another
   Claude session sent a message while you were working: <agent-message from="<id>">`, ending
   `After completing your current task, decide whether/how to respond (reply via SendMessage to
   the from= address)` (a kaggle-gemma4 subagent, 2026-10-23). Subagent to `to: "main"`: `Message
   queued for the main conversation's next turn.`, and an idle main thread starts a turn on it in
   both modes (P2, P3, P6). The main thread sending to `"main"` is refused (`You are the main
   conversation`).
5. **Interactive: ending the turn with a shell running keeps the subagent.** Main receives a
   notification noting `This agent stopped with background work of its own still running. It may
   resume on its own when that work completes or reports`; the shell runs on and each completion
   resumes the subagent (P5: a 20 s timer and a 50 s job, two resumes). Every one of those turn
   ends notified main again, three in P5. A SendMessage to the kept subagent returned `Resuming
   agent <id>` and it started a turn at once (P6).
6. **`claude -p`: the same turn end loses the job.** Main gets the same note, but the shell's
   notifications queue on main (P4: at 20 s and 50 s, while main sat in a 150 s call) and are
   handed to the subagent only when main's turn ends, which is when the process exits: P4's
   subagent received both at 02:42:23.471 and wrote nothing more. With main idle, the exit kills
   the job (P3: `final(143)` 30 s into a 75 s job). A haiku Explore read of the decompile puts an
   interactive-session test (`isInteractive()`) in the routing that keeps a stopped agent, and
   counts a bash child only while GrowthBook `tengu_concurrent_shore` (default true) holds; the
   note's wording does not check the mode.
7. **Plugin events** (P6, a plugin logging each): `turn.start` fires for main-thread turns only;
   `turn.complete` carries a subagent's `agentId`; `classic.Stop`'s `background_tasks` lists a
   running subagent as `subagent` and, once it stopped, its still-running shell as `shell`.
   `scripts/cache-keepalive` therefore arms on a stopped subagent's job, and no subagent turn
   disarms it.

8. **Without a pointer, a subagent writes its own wait.** P7, this checkout's config before the
   hook changes: a sonnet subagent told its command takes six minutes had `long-bash` in its skill
   listing and the `BACKGROUNDED:` notice naming it, loaded neither, and blocked on `until grep -q
   'exit:' <output file>; do sleep 5; done` under an 8-minute timeout. Main's message, sent 40 s
   in, reached it 5m21s later with the job done, and its next request rewrote the prefix (read 0,
   wrote 12,991). P8, the same task with the `SubagentStart` clause naming the skill and the
   subagent sentence on the notice: it loaded the skill first, waited 4m00s, answered the message
   4 s after that wait returned (3m25s after sending, at step 25 of 36), and its next request read
   14,320, the prior read plus write; the second wait returned within a second of the job's end.
   P10 (an opus subagent) and P11 (sonnet) did the same, answering at steps 26 and 25.
9. **Hooks see the attended flag.** Under `claude -p` a `PostToolUse` hook's environment carried
   `CLAUDE_CODE_SESSION_ATTENDED=0` (P12), as tool shells do, so `hook_post.rs` can tell a `-p`
   main thread from an interactive one.

## What follows

- A subagent, and a `-p` main thread, waits inside its turn in bounded calls: each return
  delivers queued messages and its job's notification, and one inside 5 minutes re-reads the
  cache. `agent-tools wait` returns when a wrapped run of the agent's settles or at `--max`, 240 s
  by default, leaving a minute for generating the next request.
- Waiting by ending the turn, open to an interactive subagent, costs main a turn per subagent
  turn end, and a timer chain keeping the 5m cache would add one per timer. The skill teaches the
  in-turn loop in both modes for that reason.
- Arithmetic, not measured: a 5m rewrite costs 1.25x the prefix against 0.1x for a read, so 4-min
  wakes pay for themselves for about 11 wakes, 45-50 min of waiting. Past that the loop costs more
  than one rewrite would, and is kept for the 4-minute bound it puts on a message's delivery.

## Probe shape

`claude -p --model sonnet --output-format json < task.txt` from a scratch cwd. The task has main
spawn a general-purpose sonnet subagent with numbered steps: a background `agent-tools run --desc
job bash -c 'sleep N; echo job-done'`, then a foreground `agent-tools run --desc wait1 bash -c
'sleep M'` or a turn end; main runs `sleep 20`, then SendMessage. Interactive runs: `claude
--dangerously-skip-permissions --model sonnet` in a `tmux -L agent-<random>` server, with
`CLAUDE_CODE_CHILD_SESSION` unset and `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1` (a session started
from inside Claude Code inherits the marker and saves no transcript). Timelines come from the
JSONL `queue-operation`, `attachment` and tool records.

# long-bash/

Protocol for a bash command that may outrun the Bash tool's timeout. Autoloads on its
`description`, so length is a direct cost.

## Files

| File       | What                            | When to read                         |
| ---------- | ------------------------------- | ------------------------------------ |
| `SKILL.md` | One worked example, the in-turn wait for an agent nothing re-invokes, and the short list of things it is not free to vary | Editing the skill |

## Shape

A single worked example with its expected output, labelled as an example, then "Fixed, not
example": the facts whose absence is a deterministic failure rather than a worse choice.
Everything else is runtime judgement, timestamps included. An earlier four-step procedure with
a rationale per step was twice the length for the same facts and read as required where it was
not: a new step has to carry a fixed fact, or it is prose paid for on every autoload.

The fork on what wakes the reader sits above the example because it changes the whole wait for
a subagent; with the carve-out at the bottom (2026-09-21) a subagent planned a background wait
from the example before reaching the bullet that voided it. "Waiting in the turn" is the
subagent path: `agent-tools wait` in bounded calls, not a turn end, because a `-p` subagent's
turn end loses the job and an interactive one wakes the caller per turn end. A `-p` main thread
took it too until 2.1.310 held the process for its shell (`"tengu_tidy_sloth"`); it still does
when the launch result says the job ends with the final response, the gate's off state. Evidence,
cache arithmetic and probe shape: `notes/cc-2.1.289-subagent-waits.md`.

## Measured, Claude Code 2.1.269 (2026-09-21) unless dated

- A command outrunning its `timeout` is auto-backgrounded even when its first statement is
  `sleep`: upstream refuses that shape, but `hook_pre.rs` prepends `unset …; export
  AGENT_TOOLS_PARENT_DIR=…;` so the first statement is never `sleep` here. The foreground
  `sleep` block runs in `validateInput`, before the rewrite, and fires only on a bare number
  as the first statement (`echo hi; sleep 25` and `sleep 30s` run). The suffix hole stays out
  of `SKILL.md`: the block's message says not to route around it.
- Nothing printed is lost at a timeout: the result says `Command did not complete within its
  <n>s timeout and was moved to the background (ID: …)`, and the output file holds every byte.
  An over-max `timeout` is clamped silently.
- `agent-tools run` execs, not a shell: `agent-tools run --desc x 'echo a && echo b'` exits 2
  with `spawn [...]: No such file or directory`.
- `ps` records carry `elapsed_s` while live and `ran_s` once settled, never both.
- The example's `set -o pipefail` (2026-10-24): without it the pipeline exits with `awk`'s
  status: a command exiting 3 read `final(0)`, and `final(3)` with it.
- `awk` here is mawk 1.3.4, whose `strftime` the stamp needs; `ts` (moreutils) is not
  installed, and the skill is read on other machines.
- `agent-tools run --background` survives a subagent's report: a 120 s probe launched by a
  subagent that returned at 13:52:33 ran to completion.
- 2026-10-24, 2.1.289: subagents cache for 5 minutes; a message or its own job's end reaches
  a subagent only when its current tool call returns; ending its turn with a job running keeps
  an interactive subagent (resumed by the job, and by a message) and loses a `-p` one's job.
- 2026-10-25, 2.1.310: a `-p` main thread's background shell holds the process and its end
  starts a turn (a 25 s `sleep`, exit at 29 s, two `result`s); a `-p` subagent's shell was
  `killed` 8 s after the main thread's last `result`. cc's interactive Bash text says "do not
  poll its output file"; `agent-tools wait` is one blocking call per round, which the skill
  names so the two do not read as conflicting.

## Cut deliberately — do not re-add without a fact it carries

- A `bash -c 'echo started; cmd; echo exit=$?'` wrapper: the output file ends `[exited with
  code N]`.
- A `sleep 1` + read check after launch: a command that dies on startup notifies as fast.
- The 5 GB output cap and the task-id format: true, and nothing acts on either.
- Monitor: it takes no file path, expires after 30 minutes, and argues against `tail -f`.
- A main-thread timer re-armed under the hour to keep its 1h cache: under the 5m TTL (overage,
  off a subscription) each wake rewrites the prefix, and the agent cannot see its TTL.
  `scripts/cache-keepalive` refreshes once instead.
- Per-line timestamps were cut once because `ps` reports `started_at` and `last_byte_s`; that
  is the run, not its output, so they are back, optional, inside the example.

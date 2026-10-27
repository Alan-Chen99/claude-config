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
Everything else is runtime judgement, timestamps included. A new step has to carry a fixed
fact: a step-by-step version read as required where it was not.

The fork on what wakes the reader sits above the example: with it at the bottom (2026-09-21)
a subagent planned a background wait from the example before reaching the bullet that voided
it. "Waiting in the turn" is `agent-tools wait` in bounded calls, not a turn end: a `-p`
subagent's turn end loses the job, and an interactive one's hands the caller a turn each
time. A `-p` main thread waits there only when its launch result says the job ends with the
final response (`"tengu_tidy_sloth"` off). Evidence, cache arithmetic and probe shape:
`notes/cc-2.1.289-subagent-waits.md`; why the wait returns on a message and sizes its bound
to the cache: `notes/cc-2.1.310-subagent-wait-costs.md`.

## Measured, Claude Code 2.1.269 (2026-09-21) unless dated

- Upstream's refusal to auto-background a command opening with `sleep` cannot fire here, and
  the foreground `sleep` block runs before `hook_pre.rs`'s rewrite:
  `docs/agent-tools-status-reference.md`. The block fires only on a bare number as the first
  statement (`echo hi; sleep 25` and `sleep 30s` run); that hole stays out of `SKILL.md`, as
  the block's message says not to route around it.
- Nothing printed is lost at a timeout: the result says `Command did not complete within its
  <n>s timeout and was moved to the background (ID: …)`, and the output file holds every byte.
- `agent-tools run` execs, not a shell: `agent-tools run --desc x 'echo a && echo b'` exits 2
  with `spawn [...]: No such file or directory`.
- The example's `set -o pipefail` (2026-10-24): without it the pipeline exits with `awk`'s
  status: a command exiting 3 read `final(0)`, and `final(3)` with it.
- `awk` here is mawk 1.3.4, whose `strftime` the stamp needs; `ts` (moreutils) is not
  installed, and the skill is read on other machines.
- `agent-tools run --background` survives a subagent's report: a 120 s probe launched by a
  subagent that returned at 13:52:33 ran to completion.
- 2026-10-25, 2.1.310: a `-p` main thread's background shell holds the process and its end
  starts a turn (a 25 s `sleep`, exit at 29 s, two `result`s). cc's interactive Bash text says
  "do not poll its output file", so the skill calls each `agent-tools wait` one blocking call.
- 2026-10-26, 2.1.310: agents batched waits in one message 39 times in three days; 7 of 903
  wait results ended one of several jobs.

## Cut deliberately — do not re-add without a fact it carries

- A `bash -c 'echo started; cmd; echo exit=$?'` wrapper: the output file ends `[exited with
  code N]`.
- A `sleep 1` + read check after launch: a command that dies on startup notifies as fast.
- The 5 GB output cap and the task-id format: true, and nothing acts on either.
- Monitor: it takes no file path, expires after 30 minutes, and argues against `tail -f`.
- A main-thread timer re-armed under the hour to keep its 1h cache: under the 5m TTL (overage,
  off a subscription) each wake rewrites the prefix, and the agent cannot see its TTL.
  `scripts/cache-keepalive` refreshes once instead.
- `agent-tools wait --all`, returning only once every job ended: 1 of the 7 above went
  straight back to waiting.
- A condition-wait pointer in `hook_subagent.rs`'s block: pinned at 1,000 characters, 998 used.
- Per-line timestamps, once cut because `ps` reports `started_at` and `last_byte_s`: that is
  the run, not its output, so they stay, optional, inside the example.

# background-wait-turn

## What this probes

Whether a turn that ends only to wait on background agents is one line naming
what it waits on — no `pre_output.record` call, no response template — and
whether the turn that finally reports runs both and covers everything since the
user's message, the work before the wait included.

The task asks for three concurrent subagents, so the run has up to three turn
ends with agents still in flight, each started by a completion notification
rather than by the user. Under a prompt binding the record to every response,
whether they make a record call or write a status is chance — one run did on
both, another on neither.

## Preconditions

`settings.json` must set `CLAUDE_CODE_FORK_SUBAGENT=1` and
`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`. Unset, `claude -p` keeps the fork gate
off, the Agent schema carries `run_in_background`, and a call passing `false`
returns its report inline with no wait turn to read; the ceiling at its 600 s
default kills an agent once the session has idled that long. Check every
`Agent` tool result reads `Async agent launched successfully`.

## Primary signal — mechanical

One row per assistant turn — the records between one user-role record (the
task, or a `<task-notification>`) and the next:

| Turn | Agents still running at its end | `pre_output.record` called | Text |
| --- | --- | --- | --- |

A notification can also arrive mid-turn as a `queued_command` attachment; it
counts for the turn it lands in. Wanted, under a prompt carrying the wait-turn
exception: every turn with agents still running calls no record and its text is
one line naming what it waits on; the last turn calls the record and carries the
template, its Evidence or Delegation log naming the commands run before the
first `Agent` call — an output carried without its command does not count. An
arm whose prompt has no exception is read against its own prompt: a record call
it requires is no fault, and the gap between arms is the measurement.

## What this case does not measure

- **Interactive mode.** The runner is `claude -p`. With the gate forced on, the
  Agent tool, its description and its results match an interactive session's;
  what differs is how a notification starts the next turn (the print-mode hold
  loop, not the REPL queue).
- **A Bash wait.** Under `-p` a `run_in_background` command is killed when the
  turn ends, so a run never waits on one across a turn end.
- **A wait turn holding something asked for on its own.** The task asks for
  one combined answer, so a finished subagent's report is not yet something to
  report — the turns opened by the first notifications each hold one and test
  exactly that; a report the user wanted separately is not measured.

## session-analysis foci

1. Every turn end: which agents were still running, whether that turn called
   `pre_output.record`, and its text — verbatim under 400 characters, else its
   length and headings.
2. Any reasoning about ending a turn while agents run, about the record or the
   template on such a turn, or about what the final turn must cover. Quote it.
3. Whether the agent stated or predicted a subagent's findings before that
   subagent's notification, or did a delegated question's work itself while the
   subagent ran.

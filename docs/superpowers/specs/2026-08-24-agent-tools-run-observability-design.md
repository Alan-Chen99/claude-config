# agent-tools run — Process Observability

Status: approved
Date: 2026-08-24
Supersedes: the lifetime and backgrounding portions of
`docs/superpowers/specs/2026-05-17-agent-tools-run-design.md`. That document also
describes components that were never built (`wrap-task`, `children/<pid>/`,
`AGENT_TOOLS_TASK_ID`); it is not a description of the shipped binary.

## Why

`agent-tools run` has no specified behavior for a child that outlives the wrapper
call. The wrapper exits on pipe EOF, not on child exit (`run.rs:119-124` waits on
the child and then joins the tee tasks; `capture.rs:39-56` returns at EOF, or on an
I/O error — never on a timeout). A descendant that inherited the stdout/stderr write ends keeps the
wrapper alive after its own child is reaped, and the exit status — known to the
kernel — is recorded nowhere, because `child_exit` and the closing `meta.json` are
written only after the tees join (`run.rs:137-151`).

Measured 2026-08-24: a wrapped `bash -c 'tail -f /dev/null & echo done'` printed its
output, the direct child exited, and the wrapper ran until SIGKILL six seconds later.
`events.jsonl` held `child_started` with no `child_exit`. During that window the agent
could read the child's output and the descendant's file side effects while "did it
exit, and with what status?" was unanswerable.

The fix is not to define backgrounding. It is to specify what the agent is guaranteed
to know, so that whether anything was backgrounded is unobservable.

## Vocabulary

| Term | Meaning |
| --- | --- |
| child | one `agent-tools run` invocation, identified by `<tool_use_id>/<wrapper_pid>`; it exists even when no process ever started |
| child process | the OS process the wrapper spawned, if any |
| wrapper | the `agent-tools run` process itself |
| status | the current truth about a child; always available by pull |
| report | text pushed to the agent at a delivery point |
| delivery point | any moment the agent receives content: a tool result, or a user turn |
| scope | `~/.claude/agent-tools/<session_id>/[<agent_id>/]` — one agent's view |

## The invariant

**No information caused by a change in a child's status reaches the agent before the
agent learns that status.**

At every delivery point, the report accompanying it reflects every status change that
has occurred up to that instant.

The agent will not learn a status the instant it changes; the agent does not run
between delivery points. It must never receive a consequence of a change first. A
child that ran and exited entirely inside one tool call and a child whose wrapper was
backgrounded for an hour are governed by the same rule, which is what makes
backgrounding unobservable.

A status change after a session's last delivery point is never reported. No consequence
of it can reach the agent either, so the invariant holds vacuously. `Stop` is not used
as a delivery point; adding it later would be additive and would not change the
guarantee.

Two corollaries constrain the implementation:

- Status is derived at delivery time from durable facts, never cached at transition
  time. A cached status cell goes stale the moment its writer dies.
- A wrapper that dies without recording anything must still yield a truthful status.
  Wrapper liveness is itself an observable fact.

## Status

Status has a **key** and a **detail**. The key decides supersession and reporting.
The detail is rendered alongside a report and never causes one.

### Keys

| Key | Meaning | Terminal |
| --- | --- | --- |
| `spawn-failed(<err>)` | the command never started | yes |
| `producing` | wrapper alive, no reap recorded, quiet anchor newer than the first bucket | no |
| `quiet(<bucket>)` | wrapper alive, no reap recorded, quiet anchor at least `<bucket>` old | no |
| `exited(<status>)` | child process reaped; the capture file may still grow because the pipes are still open | no |
| `final(<status>)` | child process reaped and no further bytes can ever be added to the capture file | yes |
| `abandoned` | wrapper gone without recording a reap; the capture is complete and the child process's fate is unknown | yes |

The **quiet anchor** is the timestamp of the most recent captured byte, or `started_at`
when nothing has been captured. `producing` therefore does not claim that any output
exists — only that nothing has stalled.

`<status>` is the child process's exit code, or `128 + signum` when it died from a
signal.

`final` promises that the file cannot grow, not that it holds everything the process
wrote: a wrapper killed by SIGKILL loses whatever was still in the pipe buffer, and that
loss is not observable from outside. `abandoned` marks the case where completeness was
never confirmed by the wrapper at all.

A later status supersedes an earlier one. The agent is told the current key only; keys
it never saw are never sent. A child that started, produced output, and finished
between two delivery points is reported once, as `final(<status>)`.

`exited` and `final` are distinct because they answer different questions. `exited`
gives the status and warns that the capture file may still grow. `final` additionally
promises it will not. Collapsing them is what produced the original defect.

### Quiet buckets

Default boundaries: **30s, 5m, 30m, 2h**. A child whose quiet anchor is at least a
boundary old has that bucket as its key; the largest crossed bucket wins. Boundaries are
inclusive, so an anchor exactly 30s old is `quiet(30s)`, never `producing`.

Crossing into a bucket is a key change and therefore one report. Continuous output
never changes the key, so a chatty child is reported once and then stays silent no
matter how many delivery points pass. Boundaries are configuration, not contract.

### Detail

Detail is rendered alongside a key and is never itself a reason to report. It has two
audiences with different budgets.

A **report** line is pushed into `additionalContext`, which is capped (see Report size),
so it stays lean: the child's name — the `--desc` string, or the command when there is
none — the key, the child pid, the age of the most recent byte, the stdout and stderr
byte counts, and the capture paths. The exit status needs no separate field; it is
already inside the key.

**`agent-tools ps`** is pulled on demand and has no such budget, so it adds what the
report omits: the full command, the wrapper pid, and `started_at`.

Ages are computed at delivery, not at transition, so the number the agent reads is
accurate when it reads it.

## Reporting

At each delivery point, for each child in the agent's scope: derive the current key; if
it differs from the last key reported to that scope, emit one line and record the new
key; otherwise emit nothing.

Consequences:

- No redundancy. A key is reported at most once per transition into it.
- Oscillation collapses. A child flapping between `producing` and `quiet(30s)` between
  two delivery points produces at most one report, and none if the key ends where it
  started.
- Reports are per-scope. A subagent's children are reported to that subagent, the main
  thread's to the main thread. Existing scope isolation is unchanged.

### Ledger

`<scope>/.reported.json` maps child → last reported key, written under the existing
per-scope flock against a sibling `.lock` sentinel. It replaces
`.hook-post-surfaced.json`, whose per-pid boolean granularity cannot express "reported
at `exited`, not yet at `final`".

`agent-tools ps` never touches the ledger. Pulling status must not suppress a future
report.

### Report format

```
[agent-tools] run status:
  <desc> [<key>] <detail> → <capture_dir>/{stdout,stderr}
```

One header line, one line per child whose key changed. `<desc>` is the `--desc` string,
or the command when `--desc` was not given — `desc` is optional (`meta.rs:10`) and a
report must never render an empty name. The name is the only field carrying arbitrary
text, so it is escaped and length-capped: a newline in it renders a second line that
reads as a status line for a child that does not exist, and a name long enough to push
the line past the report budget makes that child's change permanently unselectable —
announced as omitted at every delivery point and never delivered. This text is
prompt-coupled; see Prompt coupling.

This replaces both current emissions — `"[agent-tools] captures from this Bash call: "`
and `"Late captures from prior backgrounded call "`. That split exists only because the
old design distinguished this-call captures from prior-call captures. Under this spec
there is no such distinction: a report is a report, and which tool call started the
child is detail.

The separate backgrounding notice (`"BACKGROUNDED: ..."`, `hook_post.rs`) is out of
scope and stays as it is. It reports a fact about the agent's own tool call, not about
a child, and this spec does not make it redundant.

## State layout

```
~/.claude/agent-tools/<session_id>/[<agent_id>/]<tool_use_id>/
  events.jsonl
  <wrapper_pid>/
    meta.json
    stdout
    stderr
```

The capture directory is named by the **wrapper's** pid, not the child's. The wrapper's
pid exists before the child does, so a command that fails to exec still has a directory
to be reported from; today's child-pid naming (`run.rs:54`) cannot represent
`spawn-failed` at all, because the name is unavailable when the failure happens.
`ps.rs` discriminates directory levels by numeric names and is unaffected.

A child's identity — the ledger key, and what "per child" means everywhere in this
document — is that directory's path relative to the scope: `<tool_use_id>/<wrapper_pid>`.

## Durable facts

The wrapper records facts as it learns them. It never records a status.

| Fact | Where | Written when |
| --- | --- | --- |
| `wrapper_pid`, `wrapper_started_ticks` | `meta.json` | immediately after spawn |
| `child_pid`, `desc`, `command`, `started_at` | `meta.json` | immediately after spawn |
| `spawn_error` | `meta.json` | when the command cannot be exec'd |
| `reaped_at`, `exit_status` | `meta.json` | **the instant the direct child is reaped, before joining the tees** |
| `drained_at` | `meta.json` | when both tee tasks reach EOF |

The bolded row is the single change that fixes the original defect: today both fields
are written after the tees join (`run.rs:137-151`), so a detached descendant delays
them indefinitely.

Everything else is read from the filesystem at derivation time and needs no writes:
most-recent-byte timestamp is `max(mtime(stdout), mtime(stderr))` — the tee appends on
every read, so the mtime is already the answer — and byte counts are the file sizes.

`wrapper_started_ticks` is the process start time in clock ticks since boot: field 22
of `/proc/self/stat`, confirmed 2026-08-24 against `/proc/uptime` — a freshly started
process reports uptime x `CLK_TCK`. Parse it after the last `)` on the line; `comm`
may contain spaces and parentheses. It is compared against `/proc/<wrapper_pid>/stat`
before a liveness result is trusted, so a recycled pid cannot make a dead wrapper
look alive. `ChildMeta` today records only `child_id`
(`meta.rs:8-15`); the wrapper's own identity is new.

### Derivation

Inputs: `meta.json`, wrapper liveness (`kill(wrapper_pid, 0)` plus the start-ticks
comparison), and `stat` on the two capture files.

| Condition | Key |
| --- | --- |
| `meta.json` missing or unparseable | `abandoned` |
| `spawn_error` present | `spawn-failed(err)` |
| `drained_at` and the reap record both present | `final(status)` |
| reap present, wrapper alive | `exited(status)` |
| reap present, wrapper dead | `final(status)` |
| no reap, wrapper dead | `abandoned` |
| no reap, wrapper alive, anchor newer than the first bucket | `producing` |
| no reap, wrapper alive, anchor at least bucket B old | `quiet(B)`, largest crossed |

Rows are evaluated top-down; the first match wins. Every input combination matches
exactly one row.

The reap time and the exit status are one atomic record, so no row can name a status
that was never written. `drained_at` without a reap cannot be produced — the wrapper
joins the tees only after reaping — and a record showing it is treated as corrupt: it
falls through to the no-reap rows, which classify it by wrapper liveness rather than
inventing a status.

Total: every combination of inputs maps to exactly one key. There are no timeouts and
no heuristics. A dead wrapper implies a complete capture because the wrapper held the
only read ends; once it is gone nothing can append.

## Delivery points

The invariant binds every channel agent-tools can instrument.

| Channel | Mechanism |
| --- | --- |
| successful tool results | `PostToolUse` hook, `matcher: ""` (empty string matches all tools) |
| **errored tool results** | `PostToolUseFailure` hook |
| user turns | `UserPromptSubmit` hook |

All three carry the report in `hookSpecificOutput.additionalContext`; plain hook stdout
does not reach the model. All three were verified end to end on 2026-08-24 by capturing
the literal request bodies sent to the API: the report arrives as a separate
`role: "system"` message immediately after the message it accompanies, and in the
transcript as an `attachment` record of type `hook_additional_context`. It is *not* part
of the tool-result record itself.

`PostToolUseFailure` is not an optional extra. `PostToolUse` does not fire when a tool
result is an error — the failure path dispatches `PostToolUseFailure` instead — so
without it, every errored tool call is a delivery point that arrives with no report.
That is a direct violation of the invariant, and an errored call is exactly when an
agent is most likely to go looking at a wrapped process.

The current matcher is `Bash|Monitor|Read` (`settings.json:94`), which leaves Grep,
Glob, Edit, Write, Task, and WebFetch able to deliver a consequence of a status change
— a file the daemon wrote — before the status itself. Widening the matcher is required
by the invariant, not an optimization.

`PreToolUse` stays `Bash|Monitor`: only those tools need `AGENT_TOOLS_PARENT_DIR`.

`TaskCreated` and `TaskCompleted` exist in the hook input schema only and cannot return
`additionalContext`; they are not delivery points.

### Channels that cannot be instrumented

These are named holes, not oversights. `agent-tools ps` is the fallback for all of them.

| Hole | Why |
| --- | --- |
| permission-denied tool calls | the dispatcher returns before the tool runs, firing neither `PostToolUse` nor `PostToolUseFailure`. Only a `PermissionDenied` hook sees it, and only under the auto-mode classifier |
| `bareFork` sessions | `PostToolUse` dispatch is skipped outright for them |
| content the agent produces itself | no event exists |

### Report size

`additionalContext` is capped at 10,000 characters; beyond that the runtime spills the
text to disk and substitutes a stub holding the first 2,000. A report is one line per
changed child, so a session with many children can cross that. The report must therefore
bound itself: emit at most as many lines as fit under the cap, and when lines are
dropped, say how many and name `agent-tools ps` as the way to see the rest. A silently
truncated report reads as "nothing else changed", which is precisely the lie this spec
exists to prevent.

Cost: one scan per tool call, `O(children in scope)` stats. The Read matcher addition
was measured at under 5ms by the same method.

## agent-tools ps

`ps` renders the current status of every child in the session using the same derivation
— no ledger consultation, no dedup, everything shown whether or not it was reported. It
is the recovery path when the agent has forgotten or its context was compacted.

`ps.rs:255` derives liveness from `is_pid_alive(child_id)`, which is pid-reuse prone
and now unnecessary: a live wrapper that has not recorded `reaped_at` means the child is
alive by definition. Child-pid liveness checks are removed.

## What this removes

| Removed | Why |
| --- | --- |
| `UNFINALIZED_STALE_SECS = 300` and the `[unfinalized]` fallback (`hook_post.rs:22`) | wrapper liveness answers immediately what the five-minute timeout guesses at |
| `is_pid_alive(child_id)` (`ps.rs:255`) | implied by wrapper liveness plus `reaped_at` |
| the this-call / prior-call report split | one rule now covers both |
| `.hook-post-surfaced.json` | superseded by the per-key ledger |

## Prompt coupling

Report strings are quoted verbatim in `sys_prompt/alan-default-next.md`, which teaches
the agent to recognize them. The prompt must be updated in the same commit as any
change to the report format, and the prompt's current quotes of the two replaced
strings must be replaced, not merely added to.

`agent-tools/CLAUDE.md:11` states that a CI guard `scripts/check-prompt-coupling.sh`
fails when the two sides drift. That file does not exist anywhere in the repository
(verified 2026-08-24). Implementation must create it, covering the new report strings,
or delete the claim. Leaving both the claim and the gap is not acceptable.

## Failure modes

| Situation | Behavior |
| --- | --- |
| wrapper SIGKILLed | next delivery derives `abandoned` or `final` from facts; never reports a stale `producing` |
| host reboot | wrapper pid dead, or alive with mismatched start ticks; same as above |
| pid reuse | start-ticks comparison rejects the impostor |
| parallel tool calls racing the ledger | per-scope flock, as today |
| capture files deleted by a human | sizes report 0B, paths still printed, keys still derive from `meta.json` |
| `meta.json` unreadable | the child is reported as `abandoned`; a capture that cannot be described is never silently dropped |
| an all-digit `tool_use_id` | would be mistaken for a wrapper-pid directory, and a subagent's captures would be reported to the main thread. Scope isolation rests on this: a scope entry is a subagent directory precisely when its name does not parse as a `u32`. Real ids are `toolu_<base62>`, so the assumption holds — but it is an assumption, not a check |
| wrapper SIGSTOPped | reported as `producing` or `quiet`, even if the child process has already exited. A stopped wrapper cannot reap, so no fact exists to derive from. This is the one state where a live wrapper without a reap record does not imply a live child process; it is pathological and accepted rather than papered over |
| bytes still in the pipe when the wrapper is SIGKILLed | lost. `final` promises no further growth, not completeness |
| quiet boundaries reconfigured | the ledger stores rendered keys, so each affected child emits one report under the new labels. One-time noise, not a correctness failure |

## Testing

Integration tests. Each is a falsification of a specific clause.

1. **Detached daemon.** Wrapped command backgrounds a process holding the pipes. The
   first delivery point after reap reports `exited(0)`; a later one reports `final(0)`
   after the daemon dies. Neither waits five minutes.
2. **Wrapper SIGKILLed mid-run.** Next delivery reports `abandoned`, immediately.
3. **Run to completion inside one tool call.** Exactly one report, `final(<status>)`.
   No `producing` or `quiet` report is ever emitted for it.
4. **Continuous output across many tool calls.** Exactly one report total.
5. **Stalled child across bucket boundaries.** One report per bucket that is the current
   bucket at some delivery point. Crossing 30s, 5m and 30m between two delivery points
   collapses to a single `quiet(30m)` report, because the largest crossed bucket wins.
6. **Flap between deliveries.** No report when the key is unchanged at both ends.
7. **Subagent isolation.** A subagent's reports never appear in the main thread's scope.
8. **The invariant itself.** A daemon writes a marker file after its parent exits. The
   tool call that first observes the marker — via Grep, Read, or any other tool — must
   carry a report whose key is at least `exited`. This test fails against the current
   implementation and is the reason this spec exists.

## Non-goals

- Changing the wrapper's lifetime. It still waits for pipe EOF, so captures stay
  complete. A wrapper blocked on a detached descendant is no longer invisible: it is
  the reportable `exited(<status>)` state. Whether a future change lets the wrapper
  detach its tee is an implementation question this spec deliberately does not settle.
- Garbage collection of state. Unchanged: state grows until a human removes it.
- Capturing the wrapper's stdin.
- Reporting on processes not started under `agent-tools run`.
- Replacing the `BACKGROUNDED:` notice.

## Risks

- Delivery was verified on 2026-08-24 against Claude Code 2.1.235 by capturing the
  literal API request bodies, not by reading schemas. `PostToolUse` with an empty matcher
  delivered for Read, Write, Edit and ToolSearch as well as Bash, including inside
  subagent threads; `UserPromptSubmit` delivered on every turn, not only the first.
  Two cautions for anyone re-running that check: in a subagent thread no attachment
  record is written to the transcript even though the context is delivered, so grepping
  transcripts under-reports and only wire capture is authoritative; and a matcher
  containing no regex metacharacters is compared by exact string equality, so `"Edit"`
  does not match `MultiEdit`.
- Report volume scales with children in scope. The dedup rule bounds it to one line per
  key transition, but a session that starts hundreds of children accumulates scan cost
  on every tool call.

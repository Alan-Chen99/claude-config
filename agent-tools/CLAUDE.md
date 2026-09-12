# agent-tools

Rust binary wrapping skill / Python tool invocations and Claude Code lifecycle hooks. Subcommand surface and root resolution are documented in the repo-root `CLAUDE.md`; this file covers internals that aren't obvious from the source.

## Source files

| File | What |
| --- | --- |
| `main.rs` | The `clap` subcommand surface, root resolution, and dispatch |
| `run.rs` | The `run` subcommand: scope, capture dir, `meta.json`, and the phase split `--background` needs |
| `core.rs` | The passthrough core `run` and `run-core` both drive: spawn, tee, drain, exit code |
| `capture.rs` | One stream's tee, its five diagnostics, and what it observed |
| `background.rs` | `fork` / `setsid` / readiness pipe — the only `unsafe` here, and the reason `background-probe` exists |
| `signals.rs` | SIGINT/SIGTERM/SIGHUP/SIGQUIT forwarded to the wrapped child |
| `status.rs` | One child's status derived from disk, and the report line it renders |
| `psrecord.rs` | `Record` and `Envelope` — the one serializable shape every renderer reads |
| `ps.rs` | The `ps` subcommand: collect captures, build records, dispatch to a format |
| `statusline.rs` | The one-line renderer behind `ps --format statusline` |
| `hook_pre.rs` | `PreToolUse`: rewrite a `Bash` or `Monitor` command so it runs wrapped |
| `hook_post.rs` | `PostToolUse` / `PostToolUseFailure`: derive, diff, report, commit |
| `hook_prompt.rs` | `UserPromptSubmit`: the same report, on the user-turn channel |
| `hook_input.rs` | The hook payloads, held raw where the runtime owns the shape |
| `ledger.rs` | `<scope>/.reported.json` and its `flock`: what the agent was last told |
| `events.rs` | The append-only per-run event log `ps --events` reads |
| `meta.rs` | `meta.json`, and `escape_control` — the guard every rendered field passes |
| `paths.rs` | State root, scope resolution, and the `user-shell` fallback for a `!` command |
| `procname.rs` | `comm` (default) and `--hide-cmdline` (opt-in) |
| `procstat.rs` | `/proc/<pid>/stat`: liveness and start ticks, read lossily |
| `claude.rs` | The `claude` subcommand: launch this checkout without installing it |
| `opencode.rs` | The `opencode` subcommand: `.env` mapping, then exec |

## The hidden `background-probe` subcommand

`agent-tools background-probe <mode>` runs `background::detach` once and prints what
the parent half learned. It is `hide = true`, so it is absent from `--help`, and it is
there for `tests/` alone: every property `--background` promises is a property of
processes — the parent returning before the child finishes, the child at PPID 1 in a
session of its own, a bailing child not flushing the parent's buffered stdout a second
time — and none of them is reachable from a `#[cfg(test)]` module inside a process that
must stay single-threaded to fork at all. So the test drives a real binary, and this is
that binary. Agents should never reach for it; `run --background` is the surface that
reports. `a_hidden_subcommand_is_not_wireable_from_settings` keeps it out of the set a
`settings.json` hook may name, so hiding it does not quietly widen what a hook can call.

## Prompt-coupled strings

These strings are emitted by `agent-tools` and quoted verbatim in the system prompt (`sys_prompt/alan-default-next.md`). The system prompt teaches the agent to recognize them. Any drift between the emitter and the prompt silently breaks recognition without breaking a single Rust test — the agent simply stops recognizing the text it was taught to look for. `scripts/check-prompt-coupling.sh` exists to catch exactly that, and is the reason the rows below carry needles precise enough to grep for.

Each such literal in `hook_post.rs` and `status.rs` carries a `// PROMPT-COUPLED` marker
on the line directly above it. A marker means the prompt quotes this text rather than
standing a placeholder in for it: `started {}, ran {}` is quoted, while `last byte {}s
ago` only fills the prompt's `<age>` slot and carries no marker. `check-prompt-coupling.sh`
asserts that each file's marker count equals the number of needles aimed at it, and does
so before any needle is grepped. That is what a needle-by-needle list cannot do on its
own: a literal shipped with its prompt sentence and no needle leaves the gate green while
the prompt goes false — the failure this script exists to prevent, arriving by the one
route a needle list cannot see. The count catches the marked-but-unpinned half of that;
the marker itself is the author's declaration, and the neighbouring markers are what tell
the next author one is due.

| Emitter                                                                                          | Prompt quote location                                  | Notes                                                                                              |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| `hook_post.rs` / `hook_prompt.rs` report header `"[agent-tools] run status:\n…"`, and the `"… unavailable this time"` fallback that shares its prefix | `sys_prompt/alan-default-next.md`, `# Using your tools`, the `agent-tools run` bullet list | Edit both sides together. `scripts/check-prompt-coupling.sh` fails if they drift. It matches the exact literal at each emit site, not the bare prefix: the prefix also occurs in the fallback branch, so a file-level grep passes over a drifted header. |
| `status.rs`'s `Display for StatusKey` → `producing`, `quiet(<bucket>)`, `exited(<code>)`, `final(<code>)`, `abandoned`, `spawn-failed(<error>)` | Same bullet list, the sentence beginning "Keys are" | Same rule, with a second consumer: these strings are also the ledger identity that decides whether a change has already been reported, so renaming one re-reports every live child once. `key_strings_are_stable_ledger_identities` pins the text; the coupling script pins the prompt to it. |
| `hook_post.rs::bg_notice` → `"BACKGROUNDED: Command was backgrounded. Cause: …"`                 | Same bullet list, the status bullet's closing sentence | The prompt keys off `BACKGROUNDED:` at the *start of a line*, which couples position as well as the prefix: `run`'s two notices join with a newline for that reason, and joining them with anything else leaves the second header mid-line where the prompt's rule cannot reach it. `hook_post_test::the_status_header_begins_a_line_even_beside_a_backgrounding_notice` pins it; `check-prompt-coupling.sh` matches literals, not position. The Bash tool returns a `backgroundTaskId` for an explicit `run_in_background: true` and for a foreground command moved to the background when it outruns its `timeout`, so the notice reaches the agent on both paths and the `Cause:` field is what separates them, along with the other reasons the tool's output schema names (`src/chunk-dbb93264.js:215694-215699`): a user's Ctrl+B, a turn abort, and a queued message needing to reach the model. A background with none of those fields set and no explicit `run_in_background` says so rather than naming one. Under `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` no tool response carries the id at all and `bg_notice` returns `None` on every call; that is a session-level choice rather than a property of this binary, so both sides stay in place either way and the coupling guard checks the pair regardless. See the repo-root `CLAUDE.md`. |
| `capture.rs`'s five diagnostics, every one written through `state`: the downstream-closed notice, the bound-reached notice (which names which bound), and one each for the capture's open, write loop and flush failures | Same bullet list, the passthrough bullet — "always prefixed `agent-tools:`" | The prompt promises the prefix, not the wording, so the guard pins one exact literal per emit site rather than the prefix: measured, dropping `agent-tools:` at one site still leaves four matches in the file, so a bare-prefix grep passes while any four of the five drift. Five sites because the open, the write loop and the flush each need their own message; the `failed (` needle runs on to `forwarding continues` so it cannot also match the flush's line and leave that site unpinned. Drift costs the agent the only thing separating a wrapper diagnostic from its command's own stderr. The notes segment carries the same facts on the status channel, which is what covers the cases stderr cannot — a notice about stderr itself, or about the one destination a merge made of both, since that is the closed descriptor in exactly those. Measured: `… 2>&1 \| head -3` delivers no notice and still reports `[downstream closed]`. `main.rs`'s `run` and `run-core` failure prints are the only other diagnostics reachable once the tees are running, so they carry the same prefix under the same promise; the guard pins `capture.rs`'s five, and a comment at each of those two sites carries the reason its spelling differs from the other subcommands'. |
| `status.rs::render`'s notes segment and `stat failed:` — `streams split: <why>`, `downstream closed`, `drain capped`, `capture capped`, `capture failed: <err>`, `[stat failed: <err>]` | Same bullet list, the status bullet, the sentence beginning "`<detail>` is" | Guarded, one needle per emit site: `check-prompt-coupling.sh` pins the whole `format!` / `push` expression rather than the words, because the bare words also occur in `status.rs`'s own render assertions, so a word-level grep passes over a drifted emitter. Each needle matches exactly one place in the file, and each was watched to fail — change the emitted string and the script names `status.rs`. The prompt teaches the agent that a bracket after the byte counts is facts rather than a second key, and names every one of them; renaming one leaves that bracket unexplained on a line the agent must still read. See "The notes segment" below for the emit conditions. |
| `hook_post.rs::collapse_running` → `"  still running: {body}  -> agent-tools ps"` | Same bullet list, the bullet beginning "Children still running" | The bare words `still running` also occur in `bg_notice`'s `"Process is still running (task_id: …)"` and in this file's own comments, so the guard pins the whole `format!` literal rather than the prefix — the same rule the notes-segment row above uses. `running_children_collapse_to_one_line_that_still_names_each_of_them` and `a_dropped_collapsed_line_is_announced_rather_than_silent` pin the behavior the prompt describes; the coupling script pins only the text describing it, and needs its own row because that text is not one of the render-line fields the row above already covers. |
| `run.rs`'s `--background` start line — `"{}  wrapper pid {wrapper_pid}  child pid {pid}"` | `sys_prompt/alan-default-next.md`, `# Using your tools`, the backgrounding bullet | The one line a backgrounded start prints, and the agent's only handle on the capture directory and the wrapper pid. It carries no `[agent-tools]` or `BACKGROUNDED:` marker — it is the command's own stdout — so an agent tells it from its child's first line of output by shape alone, and the prompt shows that shape. The needle is the whole format literal: the bare words also occur in this file and in the test that asserts the line, so a word-level grep passes over a drifted emitter. It sits outside the marker convention above, which covers the two files whose text reaches `additionalContext`; this one reaches the agent as stdout. |
| `main.rs::GATE_STDOUT` (printed by `agent-tools opencode.gate`)                                  | `opencode/agents/alan-default-ids.md`, step 4 ("gate stdout returns instructions") and step 5 ("reason in a thinking block about what it instructs") of the Doing-tasks list; G1 reinforces R002 (big-picture target), G4 cites R043 (cheap-rejection transparency), G6 cites R090 (no implicit work-assignment), G7 stands alone (evidence-vs-claim), all rules defined in the same agent body | The agent prompt references "gate stdout" without quoting it. If GATE_STDOUT were emptied or removed, the agent prompt would still direct the agent to "follow nothing" — silently no-ops the R060 mistake-check. Pointer-style: items reference rules in the agent body rather than restating them. If the body's R002, R043, or R090 is renumbered or removed, the matching G silently loses its referent. The closing sentence ("re-enter the gate at the next version") is the consumer for the step-5 iterate-until-clean trigger; the body's heredoc uses `turn-<X>-version-<Y>` tags that share this vocabulary. Edit both sides together; rebuild `agent-tools` so the binary actually emits the new text. |
| `main.rs::MIN_GATE_STDOUT` (printed by `agent-tools min.gate`)                                   | `opencode/agents/min.md`, step 4/5/6 wording; G1 reinforces R002 (big-picture target), G4 cites R043 (cheap-rejection transparency), G6 cites R090 (no implicit work-assignment), all defined in the same agent body | Diagnostic baseline counterpart to GATE_STDOUT — identical text minus G7 (the evidence-vs-claim check). Pointer-style: items reference rules in the agent body rather than restating them, so the gate is a reminder list rather than a complete checklist. If the body's R002, R043, or R090 is renumbered or removed, the matching G silently loses its referent. Edit both sides together; rebuild `agent-tools`. Cite layout was G3→R070 / G5→R090 before round 7 of the failure-mode investigation. |

## Process identity: `comm` (default) vs `--hide-cmdline` (opt-in)

`run.rs` exposes two knobs on how the wrapper appears to peer
processes.

**Default** — `procname::set_comm(desc-or-cmd[0])`. Sets the kernel
`comm` slot (15-byte cap, `ps -o comm=`, `/proc/*/comm`) to
`at:<hint>` where hint is `--desc` if given, else the wrapped
command. Argv (`/proc/*/cmdline`, `ps aux`, `ps -o args=`) is
untouched. Clarity for general debugging is the priority.

`comm_for` stops before a character that would cross the 15 bytes
rather than at 15 bytes, so a hint can end short of the cap. The
kernel truncates without regard for character boundaries, and half a
character is invalid UTF-8 in `/proc/<pid>/stat`, which `procstat`
must read for every liveness check. `procstat` reads that file
lossily for the same reason from the other side: `comm` holds
arbitrary bytes for *any* process, and treating an unreadable stat as
death would report a live wrapper as `final(<status>)`.

**Opt-in** — `agent-tools run --hide-cmdline ...` calls
`procname::hide_cmdline("agent-tools: <exe>")`. Zeros the argv
memory region and writes the new title in place. Peer processes
reading `ps aux` or `/proc/*/cmdline` cannot recover `--desc` or the
wrapped command line. `comm` is set to match. Use for probe /
contamination-sensitive work only.

Regardless of the flag, `desc` remains in `meta.json` for the intended
observability path (`agent-tools ps`, the status report); the
argv memory is not it.

Mechanism (hide path): `/proc/self/stat` fields 48/49 (`arg_start`,
`arg_end`) name the exact virtual-memory range the kernel serves as
`/proc/self/cmdline`. That range is in the wrapper's own address
space; a straight `write_bytes` + `copy_nonoverlapping` is enough.
No `prctl(PR_SET_MM, ...)` or CAP_SYS_RESOURCE needed. See
`src/procname.rs` for the full derivation. Regression guards in
`tests/run_test.rs`:
`default_leaves_argv_visible_and_sets_comm` and
`hide_cmdline_hides_desc_and_argv_from_proc_self_cmdline`.

Named in round 19 of the compliance-check failure-mode investigation
(F88): E-k3-nodontact quoted `agent-tools run --desc "E-k3-v8: Kimi
K3 + v8 + H17"` verbatim from `ps aux` (all runs pre-fix had the
leak; the hide fix now exists but is behind a flag so we do not lose
debugging clarity on non-probe work).

## The merge rule

A wrapped child gets **one** destination for both its streams when either of two things is true.
The ordinary one: the caller's own two descriptors provably reach one destination that cannot
disagree about where the next byte goes — the same file (same device and inode), both writable,
and either both pipes or both appending. `core::decide_merge` decides that case, by inspecting
`STDOUT_FILENO`/`STDERR_FILENO`, and is the whole of it *for a run that has a caller*. The other:
there is no caller to inspect, because the wrapper detached from one. `core::run_core`'s
`destination: Destination` parameter carries the distinction — `Destination::Caller` routes to
`decide_merge`; `Destination::Nowhere`, set for a `--background` run whose caller has gone, always
merges instead of asking. Asking would get the wrong answer: `detach_std_fds` has by then pointed
fd 1/2 at one `/dev/null` opened without `O_APPEND`, and `decide_merge` on that shape answers
split — correct for a real caller on a character device, and wrong for one that no longer exists.
`core::BACKGROUNDED`'s doc carries the rest of that argument. Everything else stays split.

Splitting destroys the order between the two streams and splices long lines, and neither is
repairable afterwards — that order exists only in the kernel, and by the time the wrapper has
two pipes it is gone. So the rule exists to keep it, not as an optimisation.

**It declines rather than guesses.** Whether two descriptors share an open file description is
not decidable from userspace, so the conditions make the question irrelevant: neither admissible
destination has an offset to disagree about, and merging two distinct ones would misroute the
caller's data. The enumeration is short for two different reasons, and the difference matters if
you extend it. A tty or `/dev/null` cannot be admitted — character devices are not uniformly
unseekable, so the class would be a guess. A socket *could* be, being provably unseekable like a
pipe, and is left out only because no measured caller presents one on both descriptors. Add a
destination when a caller needs it, not because it would be sound.

No flag overrides the decision for a run with a caller. The only decisive test would mean writing
to the caller's own file, and a flag could only demand the merge the rule refused. A run with no
caller is the one case a parameter *does* decide the outcome outright — `Destination::Nowhere`, not
a flag a caller sets, since a run that reaches it has no caller left to set one.

**`core::Merge` and `status::Capture` are one fact recorded twice.** A merged run opens one
`output` file; a split run opens `stdout` and `stderr`. `status::derive` reads the shape back off
whichever files exist, and `meta.json`'s `merge` field supplies only the *condition*. A change to
what either arm opens has to move both, or a report line describes files that are not there.

**Its reach is an environment assumption, not a contract.** In the Claude Code Bash tool both
descriptors are one appending description on one regular file, so ordinary calls merge and
`2>&1` is a no-op. A harness that spawns with `Command::output()` gets two fresh pipes, two
inodes, and a split — which is why almost every test in this repo sees the split path and almost
no production run does. Measure before assuming which one your case takes.

## Status reporting

`hook_post.rs` answers `PostToolUse` with an empty matcher (every tool) and
`PostToolUseFailure` (which the runtime dispatches *instead of* `PostToolUse` when a
tool result is an error). `hook_prompt.rs` answers `UserPromptSubmit`. All three are
delivery points for one report, produced by `hook_post::report_changes`:

1. **Derive.** Walk every `<tool_use_id>/<wrapper_pid>` capture dir in the scope and
   compute each child's status from facts on disk — `meta.json`, the wrapper pid's
   liveness and start ticks, and the size and mtime of `stdout` / `stderr`.
   `status::derive` is total: every input combination yields exactly one key.
2. **Diff.** Compare each key against the per-scope ledger of what the agent was last
   told about that child. An unchanged key produces no line, so silence means nothing
   changed rather than nothing being watched.
3. **Report.** Render one line per changed child that is not merely still running
   (`producing`, `quiet(<bucket>)`) — identity order makes the output reproducible
   rather than in `read_dir` order — and record in the ledger only the lines that fit
   under the `additionalContext` budget, settled children claiming it first. Children
   still running instead share one collapsed line, naming each of them under its key;
   if even that line does not fit what settled children left of the budget, a count of
   them is announced instead of dropped in silence. A dropped line — either form —
   stays pending and lands at the next delivery point; recording a line the agent never
   saw would retire that change permanently. For the same reason the ledger travels
   back to the hook uncommitted and is committed only once the write and flush have
   succeeded: a failed write must cost a repeat, never a loss.

Nothing polls and nothing is scheduled: status is computed at the moment of delivery,
so a report cannot describe a state older than the tool result it rides on.

`REPORT_BUDGET` is self-imposed, not forced. Claude Code caps hook `additionalContext`
at 8,000 characters and 200 lines, truncating and flagging rather than dropping (`Xxn`,
`src/chunk-dbb93264.js:47477-47502`), but only where an answer is sanitized through
`ego` (`:47524`) — the cloud-relay and callback hook paths. A local command hook's
parsed stdout reaches the consumer untouched (`gwe`, `:227133`, called at `:229544`).
Measured on 2.1.269: a PostToolUse command hook returning 18,611 characters over 401
lines arrived whole. The budget exists because the report rides on a tool result the
agent asked for and must not crowd it out.

### One derivation, four renderers

`status::derive` is the single place a capture directory becomes a status, and every
renderer goes through it. None re-derives, and none decides what is true — a renderer
chooses only what to *show*.

What holds them together is shared helpers, not a shared type, and the difference matters
to whoever adds the next one:

| Renderer | Reaches `derive` via | Selects live by |
| --- | --- | --- |
| push report (`hook_post::report_changes`) | `status::derive` directly, rendering with `status::render` | `StatusKey::is_still_running` — a partition, so `exited` gets a full line of its own |
| `ps --format text` (`ps::render_text`) | `status::derive` directly, rendering with `status::render` | `Status::is_terminal` |
| `ps --format json` (`ps::render_json`) | `psrecord::Record::build` | `Record::terminal` |
| statusline (`statusline::render_records`) | `psrecord::Record::build` | `Record::terminal`, plus a marker per key |

Two of the four never construct a `Record` at all, so nothing about a missing field
compiles or fails to compile for them: `derive`, `status::name`, `status::notes` and
`Status::duration_s` are what keep the facts identical, and `Record::build` is a fifth
helper that assembles those same four for the two renderers that want them as data.

So the guarantee is over the facts, and not over the *selection*: three different
predicates over one `StatusKey` are in use above, and a renderer picking the wrong one
disagrees with the others while every fact on it stays true. `exited` is where they part —
its process is finished and its wrapper is not — so a fourth renderer has to answer, by
hand, which of the three axes it means and what an `exited` child looks like under it.
`StatusKey::is_terminal`, `is_still_running`, `is_quiet` and `is_exited` each carry the
argument for their own axis; that is the reading a new renderer owes, and no compiler
prompts it.

### Report lines

One line per child whose status is anything but merely still running (`producing`,
`quiet(<bucket>)`), always:

```
<name> [<key>] pid <pid>, <timing><age>, <bytes> [<notes>] [stat failed: <errors>] -> <paths>
```

`<timing>` is the child's span, in whichever of three forms its record supports, each
carrying its own trailing `, `:

| Form | When |
| ------------------------- | ---------------------------------------------------------------------------------------------------- |
| `started <t>, ran <d>, `  | Terminal with a reap to time against: the span is finished, and `<d>` is the total it finished with.   |
| `started <t> (+<d>), `    | Live: the span is still growing, and `+` says so rather than leaving a stale total to read as final.   |
| `started <t>, `           | Terminal with no reap — `abandoned`, whose wrapper vanished before observing an end, and `spawn-failed`, where nothing ran to have a span. A duration here would assert one. |

It is empty when no `meta.json` reads, which also leaves `pid -`. That pairing is not what
identifies the shape: the `pid` fallback and `timing`'s arms are decided independently, so
a line is the crossing of the two, and `spawn-failed` renders `pid -` beside a `started
<t>, ` of its own — a start that produced no child. The trailing `, ` belongs to `<timing>`
rather than to its arms, so the empty case splices nothing onto the age and an arm added
later cannot forget it.

`<t>` is local (`status::fmt_local_hms`): a UTC instant rendered with no zone reads as
local anyway, so a reader correlating it against `date` is wrong by the offset with nothing
on the line saying so. `<d>` is `status::fmt_duration` — seconds, then `<m>m<ss>s`, then
`<h>h<mm>m` — never a bare float, which would make the reader do the division the line is
there to have already done.

Children still running share one collapsed line instead — `still running: [<key>]
<name>, <name>  -> agent-tools ps` — naming each of them under its key rather than
getting a line of this shape.

The two trailing bracketed groups are omitted entirely — brackets included — when
they hold nothing; the key's brackets are always there.

Four of its fields come off the record and carry arbitrary text: the name —
`--desc`, or the command when there is none — and the `merge`, `capture_error`, and
`spawn_error` strings. All four pass through `meta::escape_control`, which escapes
control characters; only the name is also bounded in length, by `status.rs`'s
`NAME_MAX` — one of the two callers of `cap_to`, the other being `ps`'s `CMD_MAX`.

`<timing>` adds none of either kind: an instant and a duration are both rendered from
numbers the wrapper stamped, so neither can carry text a record chose.

None of the three — `merge`, `capture_error`, `spawn_error` — is child-controlled
today: every producer is a wrapper-authored `io::Error`, an anyhow chain, or one of
`core::decide_merge`'s static conditions. A record read off disk is still not
trustworthy input: a hand-written `meta.json` carrying a newline in `capture_error`
made `agent-tools ps` emit a second physical line, reading as a status line for a
child that does not exist. A malformed record costs that record, not the history.
`spawn_error` reaches a line inside the status key, so `render` escapes the rendered
key rather than the single variant that carries text; the raw key stays the ledger
identity, where a newline is harmless JSON.

Both bounds exist because a line is a contract, not a display. A name containing a
newline renders a second line that reads as a status line for a child that does not
exist; any multi-line `bash -c` script with no `--desc` produces one. A line longer
than `REPORT_BUDGET` can never be selected by `bound`, so it is never recorded, and
that child's change is announced as omitted at every delivery point without ever
being delivered; a 9,000-character command produces one.

`ps` escapes its `cmd:` line for the same reason, and caps it at `ps.rs`'s `CMD_MAX`
through the same `status::cap_to`. A wrapped heredoc script runs to six figures, and `ps`
is read through a tool result that truncates, so one child's source would displace every
other child's status in the view an agent reaches for after a compaction. The cap is far
above any typed command, and the full text stays in `meta.json` beside the capture, whose
path the same line carries.

#### The notes segment

Everything that explains a difference from bare, in one bracketed group sitting
between the byte counts and the capture paths, `; `-separated. None of them names a
stream: `downstream closed` and the two capped notes are folded across both tees, so on a
split run they do not say which side it was. Stderr usually does, under the stream's own name —
but not when stderr is the descriptor that closed, which is one of the two shapes this
record exists for. In this order — which
`status::tests::a_difference_from_bare_is_readable_beside_the_key` pins by asserting the
whole bracket group rather than each note independently, since the prompt teaches the order:

| Note                    | Emitted when                                                                                                         |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `streams split: <why>`  | The capture is two files **and** `meta.merge` holds a condition other than `different destinations`.                 |
| `downstream closed`     | `meta.forward_closed` — a caller descriptor stopped accepting writes, so forwarding stopped there.                   |
| `drain capped`          | `meta.drain_capped` — post-close capture reached `core::DEFAULT_DRAIN_CAP_BYTES`, so the capture is short by design. |
| `capture capped`        | `meta.capture_capped` — the same size, counted from the first byte, for a run with nowhere to forward to (`--background`). Never beside `drain capped`: `capture::Bound` is one value per run. |
| `capture failed: <err>` | `meta.capture_error` — a capture file could not be written, so it is incomplete from that point on.                  |

The whole group is absent, brackets included, when none of them applies —
which is nearly every run. These lines land in every tool result, and a note that
is always there stops being read. `drain capped` is reachable only inside the
forwarding-failed branch, so it never appears without `downstream closed`;
`capture capped` is the opposite shape, reachable only where nothing is forwarded
at all, so it never appears with either.

`<why>` is `core::decide_merge`'s condition string: `descriptor could not be
inspected`, `descriptor flags could not be read`, `not both writable`, or `same
file, but not both appending`. It is never `different destinations`, the one
condition `render` suppresses: there the caller's own two descriptors already
reached two destinations, so bare kept the streams apart too and the split explains
nothing — and that is the shape of every harness spawning with two pipes, so noting
it would put a note on every line of every test run and none on production, which
merges. Whether the capture is one file or two is read off the files that exist
(`status::Capture`), never off the record; `meta.merge` supplies only the condition.

A line therefore carries up to **three** bracketed groups, in this order: the status
key (always), the notes (only when something differed from bare), and `[stat failed:
…]` (only when stat'ing a capture file failed with something other than *not created
yet*). The last two share bracket shape and `; ` separators while meaning different
things — the notes describe the run, `stat failed` describes this process's own
inability to read the capture files, and it alone is sourced from a live syscall
rather than from `meta.json`. Bracket count is what separates a clean line from one
carrying notes, and is asserted as such in `a_clean_run_carries_no_notes`.

### What `ps` adds, and what it admits

**`ps` never commits the ledger, in any format.** The ledger records what the agent was
told, and `ps` cannot observe whether its output reached one: it is read by a person on a
terminal, by `statusline.sh`, and through a tool result that truncates. Committing there
would retire a change the push report still owes, and that change is then never reported
again — the one loss the whole uncommitted-ledger design exists to prevent. `ps` derives
and renders; only a delivery point commits.

`ps` derives every capture's status the same way a report does, and shows one whether or
not its `meta.json` reads: `Capture::meta` is optional, and a directory with no readable
meta still derives `abandoned`. Dropping it instead would put the two consumers of one
derivation in disagreement about whether a child exists, in the view an agent turns to
after a compaction — the one place a child just called terminal must be findable.

For `--format json`/`text`, ordering is newest first — groups by their newest capture,
captures within a group by start time — because the output is read through a tool result
that truncates, and what started most recently is what the agent is still acting on.
Display groups by tool-use, so both levels sort the same direction or the newest capture
could sit under a group buried below older ones.

`--format statusline` orders the opposite way — see `statusline::render_records`. JSON's
`live` array ranks every running child and order there is only reading order; the bar
instead *selects*, dropping everything past its third slot to a bare count, so "which do I
list first" and "which three do I keep" are different questions that correctly get
different answers. The statusline also has no timer and freezes the instant the agent goes
idle, so its three slots go to the jobs most likely to still need watching — the ones
running longest, not the ones easiest for a person to remember unaided — and Claude Code
truncates the rendered line from the right, so oldest-first also keeps the job that matters
in the slot a narrow pane loses last.

Events are read per line. A line that will not parse costs that line, and the count
appears as `note: N unreadable event line(s) skipped`; a file that cannot be read at all is
named, `note: events unreadable for <tool_use_id>: <err>`. Both exist because the reachable
cause is a short write — the disk-full condition that also truncates a capture — so the
history goes missing exactly when it is worth having, and silence about a dropped record
reads as "nothing was written".

### A `TaskStop` result is not evidence about a child

`TaskStop` dispatches a signal and marks its own registry entry `killed`. It does not
wait for the process, confirm receipt, or escalate: a task that ignores SIGTERM runs
to completion while the tool reports `Successfully stopped task`. When that message
and a status report disagree — `[producing]` alongside "stopped" — the report is the
accurate half.

Upstream, both open: anthropics/claude-code#85200 (local_bash; the process tree
survives, and an orphaned `rm -rf` ran for 20 minutes past the stop) and
anthropics/claude-code#74638 ("TaskStop reports success while process survives", for
agents). Neither names the escalation gap: what arrives is SIGTERM, which is
trappable, and no SIGKILL follows.

Nothing here compensates for it. Polling a just-stopped child would add latency to a
delivery point in order to paper over an upstream defect, and the report is already
correct.

### The ledger

`<scope>/.reported.json` maps child identity (`<tool_use_id>/<wrapper_pid>`) to the
last key reported for it. `<scope>/.reported.lock` is a sibling sentinel holding an
exclusive `flock` for the lifetime of the `Ledger` value, so the derive-diff-report
cycle is atomic against parallel hooks: two tool calls finishing at once report each
child exactly once between them. The lock is a separate file from the JSON because the
commit is write-to-temp-then-rename, which would strand a lock held on the JSON's own
fd.

`flock` keys off the open file description rather than the process, so a second
`Ledger::open` on a scope this process already holds waits on this process's own lock,
which nothing can release. `open_scopes` turns that into an error at the door rather than
leaving it to expire against the deadline below, which would spend a second of the hook's
budget to reach the same answer with a worse message.

Acquisition is non-blocking, retried until `LOCK_WAIT`. Blocking would otherwise spend
the hook's whole 5s timeout and deliver nothing, and a delivery point silent because it
waited is indistinguishable from one with nothing to say. On expiry the error carries the
holder's path and the caller renders its "unavailable this time" line; no commit has
happened, so the changes are simply reported at the next delivery point.

The deadline bounds legitimate parallel hooks, not just a foreign holder: past it, one of
two racing delivery points announces the delay instead of serializing behind the other.
Measured at 16 concurrent hooks over 40 children, none reaches it — one reporter takes
every line, 0 duplicates, 0 losses — because the cycle it protects is a directory scan and
one small write.

An unreadable ledger is never quietly treated as empty. `reset_reason` is set, every
child then looks new, and the report leads with why — otherwise the agent sees a burst
of unexplained repeats.

### Scope isolation

Scope is `~/.claude/agent-tools/<session_id>/[<agent_id>]/`. The ledger and lock live
in that scope. A subagent's hook scans only its own scope, and `hook_prompt` always
passes `None` for the agent id, because a user turn reaches the main thread —
consuming a subagent's pending reports there would retire changes that subagent has
never been told about.

The discriminator is the directory name: under a `<tool_use_id>` dir a capture dir is
named for the wrapper pid, so an entry whose name does not parse as a `u32` is a
subagent dir and not this scope's to report. Real ids are `toolu_<base62>`, so the
assumption holds — but it is an assumption, not a check.

`run::publish_child_dir` relies on that same numeric test from the other side. It builds
the capture dir as `.starting-<wrapper_pid>`, writes the first `meta.json` into it, and
renames it onto its pid name; both scanners skip the staging name for the reason above,
and rename is atomic, so a scan sees the directory only once the meta that describes it is
inside. An attempt that dies before the rename leaves a `.starting-<pid>` holding at most
a meta and no output, which both scanners pass over: nothing was captured, and a child
that never got a capture has no fate to report. Nothing collects those remains — garbage
collection is a stated non-goal — and a later wrapper reusing the pid overwrites them.

### Why the matcher is empty

A consequence of a status change can arrive through any tool: a `Read` of the output
file, a `Grep` over it, a `Bash` command that inspects it. The matcher is `""` so that
whichever call first observes the consequence also carries the status that caused it.
`PostToolUseFailure` runs the same subcommand for the same reason — an errored tool
result is a delivery point like any other, and `PostToolUse` does not fire for it, so
without that block every failed tool call would be a delivery point arriving empty.

## Testing from a worktree

Per repo-root `CLAUDE.md`: **worktrees must NEVER run `install.sh`**. Build in place, then assert that the runtime root matches the binary's compile-time root:

```bash
cd agent-tools && cargo build --release
CLAUDE_CONFIG_ROOT=/path/to/worktree ./target/release/agent-tools skill <module> [args...]
```

There is no `--root` override. The binary's compile-time root is authoritative for every subcommand. `CLAUDE_CONFIG_ROOT` is only an assertion: if set to any other path, `agent-tools` exits non-zero; if the binary was built from a non-default worktree and the env var is unset, `agent-tools` exits non-zero.

### Launching an uninstalled checkout

```bash
cd agent-tools && cargo build --release
CLAUDE_CONFIG_ROOT=/path/to/worktree ./target/release/agent-tools claude [claude args...]
```

Four things decide whether a session exercises this checkout rather than the
installed one: the binary its hooks invoke, the `settings.json` registering
those hooks, the system prompt teaching the agent to read what they emit, and
the output style carrying `pre_output.record`. Wire three of the four and the
session looks healthy while testing the installed checkout, so `claude.rs`
wires all four from one place.

Isolation runs through `CLAUDE_CONFIG_DIR`, pointed at
`<root>/.claude/worktree-config/` (gitignored, so it dies with the worktree
rather than orphaning under `~/.claude`). The alternative — layering this
checkout's settings on the installed ones via `--settings` — double-registers
every hook, because settings sources are unioned rather than overridden, so
`hook-pre` and `hook-post` would each run twice per tool call. Suppressing the
user source with `--setting-sources` instead drops user-level skills, agents,
and output-styles along with it, which silently removes the output style the
prompt depends on.

The directory holds what `install.sh` would symlink into `~/.claude`, sourced
from this checkout, plus `CLAUDE.md`, `.credentials.json`, and `plugins` linked
from the real `~/.claude` because those are the machine's rather than the
checkout's. `settings.json` is **copied**, not linked: Claude Code rewrites it
in place when the model or theme changes mid-session, and a link would land
those writes on the tracked file. `.claude.json` is seeded once so onboarding is
skipped, then left alone because Claude Code rewrites it continuously.
Transcripts stay inside the config dir, so a test session does not appear in
`/resume` from a normal one.

Two guards run before launch, both for failures a session cannot report about
itself: every `agent-tools <sub>` the settings file wires must exist in this
build (a non-zero `UserPromptSubmit` hook blocks the turn outright, so a missing
subcommand yields a session that starts clean and then refuses every prompt),
and `scripts/check-prompt-coupling.sh` must pass.

The subcommand refuses to run when its root is the installed checkout's. That
request is what `claude.sh` already serves, and answering it here would produce
a session indistinguishable from a normal one — the silent wrong-checkout result
the root assertion exists to prevent, in the one place the assertion cannot
catch it, since a binary whose compiled root is the installed root satisfies
every check it makes.

For testing hook behavior end-to-end in a worktree, copy the built binary onto a test path and invoke it directly with synthetic hook input on stdin:

```bash
echo '{"session_id":"…","tool_name":"Bash",…}' | CLAUDE_CONFIG_ROOT=/path/to/worktree ./target/release/agent-tools hook-post
```

`tests/hook_post_test.rs` covers the tool-result channel (BACKGROUNDED notice and every cause the tool's output schema names, plus the unattributable case, notice combined with a report, notice surviving a failed report, ledger dedup, a new key for a known child, subagent isolation, the `PostToolUseFailure` event name echoed back, size-bounded reports that defer rather than lose lines, the lost-ledger announcement, report ordering, and the parallel-hook race). `tests/hook_prompt_test.rs` covers the user-turn channel (pending changes carried, the envelope shape the runtime reads, no context when nothing changed, no second carry of the same change, subagent isolation, and a failed report not erroring the user's turn).

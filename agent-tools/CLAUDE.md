# agent-tools

Rust binary wrapping skill / Python tool invocations and Claude Code lifecycle hooks. Subcommand surface and root resolution are documented in the repo-root `CLAUDE.md`; this file covers internals that aren't obvious from the source.

## Prompt-coupled strings

These strings are emitted by `agent-tools` and quoted verbatim in the system prompt (`sys_prompt/alan-default-next.md`). The system prompt teaches the agent to recognize them. Any drift between the emitter and the prompt silently breaks recognition without breaking a single Rust test — the agent simply stops recognizing the text it was taught to look for. `scripts/check-prompt-coupling.sh` exists to catch exactly that, and is the reason the rows below carry needles precise enough to grep for.

| Emitter                                                                                          | Prompt quote location                                  | Notes                                                                                              |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| `hook_post.rs` / `hook_prompt.rs` report header `"[agent-tools] run status:\n…"`, and the `"… unavailable this time"` fallback that shares its prefix | `sys_prompt/alan-default-next.md`, `# Using your tools`, the `agent-tools run` bullet list | Edit both sides together. `scripts/check-prompt-coupling.sh` fails if they drift. It matches the exact literal at each emit site, not the bare prefix: the prefix also occurs in the fallback branch, so a file-level grep passes over a drifted header. |
| `status.rs`'s `Display for StatusKey` → `producing`, `quiet(<bucket>)`, `exited(<code>)`, `final(<code>)`, `abandoned`, `spawn-failed(<error>)` | Same bullet list, the sentence beginning "Keys are" | Same rule, with a second consumer: these strings are also the ledger identity that decides whether a change has already been reported, so renaming one re-reports every live child once. `key_strings_are_stable_ledger_identities` pins the text; the coupling script pins the prompt to it. |
| `hook_post.rs::bg_notice` → `"BACKGROUNDED: Command was backgrounded. Cause: …"`                 | Same bullet list, closing sentence                     | The prompt keys off the bare substring `BACKGROUNDED:`, so only the prefix is coupled.             |
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
3. **Report.** Render one line per changed child — terminal keys first, identity
   breaking ties so the output is reproducible rather than in `read_dir` order — and
   record in the ledger only the lines that fit under the `additionalContext` budget.
   A dropped line stays pending and lands at the next delivery point; recording a line
   the agent never saw would retire that change permanently.

Nothing polls and nothing is scheduled: status is computed at the moment of delivery,
so a report cannot describe a state older than the tool result it rides on.

`REPORT_BUDGET` sits below the runtime's 10,000-character `additionalContext` cap
because anything longer is silently replaced with a short stub — which the agent would
read as "nothing else changed".

### The ledger

`<scope>/.reported.json` maps child identity (`<tool_use_id>/<wrapper_pid>`) to the
last key reported for it. `<scope>/.reported.lock` is a sibling sentinel holding an
exclusive `flock` for the lifetime of the `Ledger` value, so the derive-diff-report
cycle is atomic against parallel hooks: two tool calls finishing at once report each
child exactly once between them. The lock is a separate file from the JSON because the
commit is write-to-temp-then-rename, which would strand a lock held on the JSON's own
fd.

`flock` keys off the open file description rather than the process, so a second
`Ledger::open` on a scope this process already holds would block forever on this
process's own lock, with nothing able to release it. `open_scopes` turns that hang into
an error.

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

For testing hook behavior end-to-end in a worktree, copy the built binary onto a test path and invoke it directly with synthetic hook input on stdin:

```bash
echo '{"session_id":"…","tool_name":"Bash",…}' | CLAUDE_CONFIG_ROOT=/path/to/worktree ./target/release/agent-tools hook-post
```

`tests/hook_post_test.rs` covers the tool-result channel (BACKGROUNDED notice and its four causes, notice combined with a report, notice surviving a failed report, ledger dedup, a new key for a known child, subagent isolation, the `PostToolUseFailure` event name echoed back, size-bounded reports that defer rather than lose lines, the lost-ledger announcement, report ordering, and the parallel-hook race). `tests/hook_prompt_test.rs` covers the user-turn channel (pending changes carried, the envelope shape the runtime reads, no context when nothing changed, no second carry of the same change, subagent isolation, and a failed report not erroring the user's turn).

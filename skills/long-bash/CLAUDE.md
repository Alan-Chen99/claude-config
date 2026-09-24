# long-bash/

Protocol for a bash command that may outrun the Bash tool's timeout. Autoloads on its
`description`, so length is a direct cost.

## Files

| File       | What                            | When to read                         |
| ---------- | ------------------------------- | ------------------------------------ |
| `SKILL.md` | One worked example, plus the short list of things it is not free to vary | Editing the skill |

## Shape

The body is a single worked example with its expected output, explicitly labelled as an
example, followed by "Fixed, not example" — the four facts whose absence is a
deterministic failure rather than a worse choice. Everything else is left to runtime
judgement, including whether to timestamp output at all.

An earlier revision was a four-step procedure with a rationale paragraph per step. It
was twice the length for the same facts, and its steps read as required where most of
them were not. Adding a step is the default failure mode here: a new one has to carry a
fact from the fixed list, or it is prose the reader pays for on every autoload.

The subagent carve-out sits above the example, not in the trailing list, because it
invalidates the example wholesale for that reader. Measured 2026-09-21: with it in the
list, a subagent given a long command read all three sections, composed a background
plan, and only then hit the bullet that voided it — "roughly 40 of the skill's 73 lines
were dead text for me". The same reader found the old escape hatch circular: "hand the
task id back to the caller" needs a task id, which only `run_in_background: true`
produces, which the same sentence says gets killed. `agent-tools run --background` is
the answer and is now named.

## Measured 2026-09-21 against Claude Code 2.1.269

- A foreground command that outruns its `timeout` is auto-backgrounded, **including one
  whose first statement is `sleep`**. Upstream `yzs` (`chunk-dbb93264.js:215729`, gating
  the `onTimeout` handler at `:216563`) refuses to background a command whose first
  statement's first word is in `pzs = ["sleep"]` — but `agent-tools`'s own PreToolUse
  hook prepends `unset …; export AGENT_TOOLS_PARENT_DIR=…;` to every Bash command
  (`agent-tools/src/hook_pre.rs:50`), so the first statement is never `sleep` here and
  the guard cannot fire. The foreground `sleep ≥ 25 s` block still fires because it runs
  in `validateInput`, before the rewrite.
- Nothing a command printed is lost at a timeout. The tool result's stdout/stderr are
  empty strings, and the task's output file holds every byte, before and after the cap.
- `agent-tools run` execs; it is not a shell. `agent-tools run --desc x 'echo a && echo b'`
  exits 2 with `spawn [...]: No such file or directory`.
- A subagent is never re-invoked by a task notification. Its launch message differs from
  the main agent's and says so.
- `ps` records carry `elapsed_s` while live and `ran_s` once settled, never both.
- `awk` here is mawk 1.3.4, whose `strftime` the example's stamp depends on. `ts`
  (moreutils) is the idiomatic tool and is not installed; an `apt` install would be lost
  on the next container rebuild, and the skill is read on other machines besides.
- The foreground `sleep` block is narrower than "25 s or more": it fires only on the
  command's **first** statement (`echo hi; sleep 25` runs to completion) and only on a
  bare number (`sleep 30s` runs). The unit-suffix hole is deliberately left out of
  `SKILL.md` — the block's own message says not to route around it, and a skill that
  publishes the bypass is worse than one that is merely incomplete.
- A foreground Bash call that outruns its timeout does not return an empty result. It
  returns `Command did not complete within its <n>s timeout and was moved to the
  background (ID: …)` plus the output path — the same machinery an explicit launch gets.
  An over-max `timeout` is clamped silently, not rejected.
- `agent-tools run --background` survives a subagent's turn end: a 120 s probe launched
  by a subagent that returned at 13:52:33 was still producing at 13:53:29 and ran to
  completion. That is the one escape for a subagent whose command exceeds 600 s.

## Cut deliberately — do not re-add without a fact it carries

- The `bash -c 'echo started; cmd; echo exit=$?'` output wrapper. The wrapper records
  the exit code, and the task's output file ends with `[exited with code N]`.
- A `sleep 1` + read-the-file check right after launch. A command that dies on startup
  exits fast, and the completion notification arrives just as fast.
- The 5 GB output cap and its `[output truncated: exceeded 5GB disk cap]` marker; the
  `b`+8-char task-id format. True, and nothing acts on either.
- A pointer to Monitor. Monitor takes no file path, requires `description` and
  `timeout_ms`, expires after 30 minutes, and its own description argues against the
  `tail -f` shape this would need.
- Per-line timestamps were cut once on the grounds that `agent-tools ps` reports `now`,
  `started_at` and `last_byte_s`. That is true of the *run*, not of its *output*: `ps`
  cannot say which phase of a build consumed the hour. They are back, inside the example
  and explicitly optional.

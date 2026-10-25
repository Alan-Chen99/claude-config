# Backgrounded Bash commands in a transcript

A command reaches the background four ways, and only one of them is `run_in_background: true` on
the tool call. The four leading sentences are written by one builder, `src/chunk-j0tbz6ra.js:127904-127922`
(literal `Command was manually backgrounded by user with ID:`), chosen by a ternary chain in this
precedence order:

| Cause                                | Field set on `toolUseResult`   | Leading sentence of the tool_result content                                                                            |
| ------------------------------------ | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| User pressed Ctrl+B                  | `backgroundedByUser`           | `Command was manually backgrounded by user with ID: {id}. Output is being written to: {path}.`                            |
| Queued message needed to get through | `backgroundedToDeliverMessage` | `Command was moved to the background (ID: {id}) so that a message that arrived while it was running can reach you; it was not interrupted. Output is being written to: {path}.` |
| Hit its `timeout`                    | `timedOutAfterMs`              | `Command did not complete within its {N}s timeout and was moved to the background (ID: {id}). Output is being written to: {path}.` |
| Everything else                      | — (only `backgroundTaskId`)    | `Command running in background with ID: {id}. Output is being written to: {path}.`                                        |

`{N}` is `Math.max(1, Math.round(timedOutAfterMs / 1000))`, so the seconds figure is rounded and
floored at 1 — recover the exact value from `toolUseResult.timedOutAfterMs`, not from the string.

Two consequences:

- **Timeout auto-background is not the same sentence as an explicit `run_in_background: true`.**
  They were one sentence in v2.1.88; they are two now, and the timeout case additionally sets
  `timedOutAfterMs`. The cross-reference dance — collect `tool_use` ids that lacked
  `run_in_background`, then look for backgrounded results among them — is unnecessary.
- **The fourth row is a catch-all, not "explicit only."** `backgroundedByTurnAbort` is a real
  schema field (`src/chunk-j0tbz6ra.js:197874`) and the builder destructures it
  (`:127909`), but it branches only the follow-on sentence, never the leading one — so a
  turn-abort background opens with the same sentence as an explicit `run_in_background: true`.
  Check the field, not the string, to separate those two.

**Since 2.1.285 a fifth sentence can follow.** When any cause flag is set and the command is not
owned by a synchronous subagent, the builder appends `If it is still running after {duration} in
the background, it will be stopped and you will be notified.` (`src/chunk-j0tbz6ra.js:127917-127920`,
literal `in the background, it will be stopped and you will be notified`) — the background time
limit, which 2.1.288 scoped to unattended sessions (`-p`, SDK, CI, cloud). The leading sentence is
unchanged, so `startswith` classification is unaffected; a whole-string match is not.

## The schema fields

The Bash output schema (`src/chunk-j0tbz6ra.js:197865-197901`, literal
`"The standard output of the command"`) carries these background-related fields:

| Field                             | Type    | Meaning                                                                        |
| --------------------------------- | ------- | ------------------------------------------------------------------------------ |
| `backgroundTaskId`                | string  | Present whenever the command was backgrounded, however it got there            |
| `backgroundedByUser`              | boolean | The user pressed Ctrl+B                                                        |
| `backgroundedByTurnAbort`         | boolean | `@internal` — a plugin's turn abort moved the running command to the background |
| `backgroundedToDeliverMessage`    | boolean | `@internal` — moved aside so a message queued for the model could reach it     |
| `timedOutAfterMs`                 | number  | Set when the command hit its timeout and was auto-backgrounded; the timeout in ms |
| `backgroundEndsWithFinalResponse` | boolean | The command is owned by a synchronous subagent and dies at that agent's final response |
| `backgroundCwdHint`               | string  | Note that a backgrounded `cd`/`pushd`/`popd`/`chdir` did not change session cwd |

In the JSONL transcript these land in two places: the `toolUseResult` object on the `user` entry
carries the raw fields, and the `tool_result` block's `content` string carries the human-readable
message.

The same four causes are reported again as a structured `trigger` enum at
`src/chunk-j0tbz6ra.js:198727` (literal `tengu_bash_task_ack`), and its precedence differs:
`user`, `turn_abort`, `deliver_message`, timeout, then `explicit` — turn-abort ranks second there
and still has no leading-sentence branch. That path feeds telemetry, not the transcript.

`assistantAutoBackgrounded` is **gone** — 0 occurrences in 2.1.289. It survives only in the
v2.1.88 tree at `claude-code-src/src/tools/BashTool/BashTool.tsx:287`. The same is true of the
15-second `KAIROS` assistant-mode blocking budget and its `Command exceeded the assistant-mode
blocking budget (15s)` result string: `KAIROS`, `assistantAutoBackgrounded` and `assistant-mode
blocking budget` are each 0 occurrences across all 2,164 chunks. If you meet that string in a log,
it is a v2.1.88-era session.

## Recipes

```bash
# Classify every backgrounded Bash result by cause, off the raw fields
jq -r 'select(.type=="user" and (.toolUseResult|type=="object") and
  .toolUseResult.backgroundTaskId != null) |
  (if .toolUseResult.backgroundedByUser then "user-ctrl-b"
   elif .toolUseResult.backgroundedToDeliverMessage then "deliver-message"
   elif .toolUseResult.timedOutAfterMs then "timeout:\(.toolUseResult.timedOutAfterMs)ms"
   elif .toolUseResult.backgroundedByTurnAbort then "turn-abort"
   else "explicit-or-unknown" end)' file.jsonl | sort | uniq -c | sort -rn

# Same, off the leading sentence -- note the toolUseResult gate, which is load-bearing
jq -r 'select(.type=="user" and (.toolUseResult|type=="object") and
  .toolUseResult.backgroundTaskId != null) | .message.content[]? |
  select(.type=="tool_result") | (.content | tostring) |
  if startswith("Command was manually backgrounded by user") then "user-ctrl-b"
  elif startswith("Command was moved to the background (ID:") then "deliver-message"
  elif startswith("Command did not complete within its") then "timeout"
  elif startswith("Command running in background with ID:") then "explicit-or-turn-abort"
  else "other" end' file.jsonl | sort | uniq -c
```

```bash
# Extract background task IDs (all four message shapes)
jq -r 'select(.type=="user") | .message.content[]? |
  select(.type=="tool_result") | (.content | tostring) |
  capture("(?:with|\\() ?ID: (?<id>[A-Za-z0-9_-]+)") | .id' file.jsonl
```

## What the corpus here can and cannot settle

Measured over every log on this machine, 2026-10-05 (4,247 logs / 758,257 lines): 1,108
`toolUseResult` objects carry a `backgroundTaskId` — 942 bare, 77 with `timedOutAfterMs` only, 67
with `backgroundEndsWithFinalResponse` only, 22 with both. `backgroundedByUser`,
`backgroundedByTurnAbort` and `backgroundedToDeliverMessage` appear **zero** times. The leading
sentences agree exactly: 1,009 explicit-or-turn-abort and 99 timeout, no Ctrl+B and no
deliver-message. So those three fields' absence from `toolUseResult` is untested here, not
disproven — the schema declares them (`src/chunk-j0tbz6ra.js:197873-197875`) and this corpus holds
no instance of the events themselves. Until someone captures one, treat the `content` string as
the signal for those three causes and `timedOutAfterMs` as the signal for timeout.

**The `toolUseResult.backgroundTaskId` gate in both recipes above is not decoration.** Without it,
`startswith` over a `tool_result` block reports one Ctrl+B background that does not exist: the hit
is a log-analysing session whose own stdout *began* with the sentence. The raw substring
`manually backgrounded by user` occurs in 97 logs here and not once in a genuine backgrounded
result. A `grep` for a message shape finds discussion of it as readily as an instance; anchoring on
`startswith` narrows that to 1, and gating on the raw field to 0.

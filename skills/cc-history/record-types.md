# Transcript entry types

The roster below is the binary's own: a type -> retention-class map at
`src/chunk-j0tbz6ra.js:11325-11366` (literal `user: "transcript"`), read by the transcript
loader at `:11518-11538` (literal `oxr(Ae.type)`). It is the only exhaustive enumeration of
entry types in 2.1.289. A type missing from it is not rejected — the lookup falls through to
`accumulate` (`:11368`, literal `?? "accumulate"`).

**Retention** is what the loader's compaction planner does with the entry: `transcript` is the
conversation itself; `accumulate` entries are all kept; `last-wins` keeps only the newest per
session (per `leafUuid` for `summary` — `:11512`, literal `=== "summary" ? xe.leafUuid`);
`boundary-cleared` entries are the ones no branch re-adds, so they do not survive past the last
compact boundary.

**Seen** records whether the type actually occurs in `~/.claude/projects/` on this machine
(4,247 logs / 758,257 lines, measured 2026-10-05; `find ~/.claude/projects -name '*.jsonl' !
-path '*/workflows/*' -print0 | xargs -0 cat | jq -r 'select(type=="object") | .type' | sort |
uniq -c | sort -rn`). A `no` means the feature has not been used here — it is not evidence the
type is gone. Scope any such survey to `{project}/*.jsonl` and `{session}/subagents/agent-*.jsonl`:
`{session}/subagents/workflows/wf_<id>/journal.jsonl` is a different file format that happens to
share the extension, and its `started` / `result` records are not transcript entries.

| Type                                           | Retention        | Seen      | Description                                                                                |
| ---------------------------------------------- | ---------------- | --------- | ------------------------------------------------------------------------------------------ |
| `user`                                         | transcript       | yes       | User input or tool_result (1 content block per entry)                                      |
| `assistant`                                    | transcript       | yes       | Model response (1 content block per entry, normalized)                                     |
| `system`                                       | transcript       | yes       | System messages. `subtype` observed: `stop_hook_summary`, `turn_duration`, `local_command`, `compact_boundary`, `api_error`, `informational`, `model_refusal_no_fallback`, `scheduled_task_fire`, `away_summary`, `bridge_status`, `agents_killed`, `model_refusal_fallback`, `model_consent_fallback` |
| `attachment`                                   | transcript       | yes       | Injected context — system-reminders, hook output, skill listings. See SKILL.md             |
| `progress`                                     | boundary-cleared | no        | Streaming tool progress. `data.type` is `bash_progress` / `agent_progress` / `hook_progress` per `src/claude_config/cc_pretty/parse.py` |
| `file-history-snapshot`                        | boundary-cleared | yes       | File state snapshot (no top-level `timestamp` field)                                       |
| `file-history-delta`                           | boundary-cleared | yes       | Incremental backup against a snapshot; carries `messageId`, `snapshotMessageId`, `trackingPath`, `backup`, `timestamp` (`src/chunk-j0tbz6ra.js:17040`) |
| `last-prompt`                                  | boundary-cleared | yes       | Last user prompt (for resume picker)                                                       |
| `continued-in`                                 | boundary-cleared | no        | Names the session this one continued into, via `continuedInSessionId` (`src/chunk-zg0g4fdz.js:176`) |
| `api-request-shape` / `api-request-blob` / `api-request` | boundary-cleared | no | Captured request records, new in this build (`src/chunk-j0tbz6ra.js:11336-11338`)  |
| `content-replacement`                          | accumulate       | no        | Large content block replacement records                                                    |
| `fork-context-ref`                             | accumulate       | yes       | Written into a `fork` subagent's own file: `agentId`, `parentSessionId`, `parentLastUuid`, `contextLength` (record `src/chunk-j0tbz6ra.js:16601`, fields `src/chunk-x3dkgs4r.js:4706-4709`) |
| `frame-link`                                   | accumulate       | yes       | Artifact frame link; carries `artifactCount` (`src/chunk-j0tbz6ra.js:15307`)               |
| `memory-mode`                                  | accumulate       | no        | Memory-mode stamp: `mode`, `afterUuid`, `timestamp`, optional `reason`/`account`/`accountChoice` (`src/chunk-j0tbz6ra.js:15271`) |
| `artifact-comment-monitor`                     | accumulate       | yes       | Artifact comment watch record                                                              |
| `summary`                                      | last-wins        | no        | Conversation summary (for resume). Keyed by `leafUuid`, not `sessionId`                    |
| `custom-title`                                 | last-wins        | yes       | User-set session title                                                                     |
| `ai-title`                                     | last-wins        | yes       | AI-generated session title                                                                 |
| `ended-by-model`                               | last-wins        | no        | Session ended by the model (`src/chunk-j0tbz6ra.js:19094`)                                 |
| `tag`                                          | last-wins        | no        | Session tag (searchable in /resume)                                                        |
| `relocated`                                    | last-wins        | no        | Session cwd was relocated; carries `relocatedCwd` (`src/chunk-ar9714q3.js:590`)             |
| `agent-name` / `agent-color` / `agent-setting` | last-wins        | first two | Subagent display metadata                                                                  |
| `pr-link`                                      | last-wins        | no        | GitHub PR linked to session: `prNumber`, `prUrl`, `prRepository`, `timestamp` (`src/chunk-j0tbz6ra.js:15299`) |
| `artifact-autoreact-ledger`                    | last-wins        | yes       | Artifact auto-reply ledger; the loader repairs torn writes of it (`src/chunk-j0tbz6ra.js:11539`, `:11552`, `:11559`) |
| `bridge-session`                               | last-wins        | yes       | Bridged session: `bridgeSessionId`, `lastSequenceNum`, optional `declaredDialogKinds` (`src/chunk-j0tbz6ra.js:15314`) |
| `history-suppression`                          | last-wins        | no        | History suppressed, with `cause` (`src/chunk-t0wrcf3t.js:1300`)                             |
| `attribution-snapshot`                         | last-wins        | no        | Attribution snapshot. Written through the same torn-write-tolerant path as the ledger (line-prefix buffer at `src/chunk-t0wrcf3t.js:1105`), and exempted from boundary pruning at `src/chunk-j0tbz6ra.js:11639` |
| `mode`                                         | last-wins        | yes       | Session mode. Only `normal` observed here; `coordinator` is the documented other value     |
| `permission-mode`                              | last-wins        | yes       | Session permission mode. Observed: `bypassPermissions`, `default`, `auto`, `acceptEdits`   |
| `isolation-latch`                              | last-wins        | no        | Session isolation `side` (`src/chunk-j0tbz6ra.js:15259`)                                   |
| `dev-mods`                                     | last-wins        | no        | Dev-mods `folder`, new in this build (`src/chunk-j0tbz6ra.js:15264`)                       |
| `atis-latch`                                   | last-wins        | yes       | Latched `atis` value (`src/chunk-j0tbz6ra.js:15288`), sent as the `x-cc-atis` request header (`src/chunk-ajtyjx88.js:37721`) |
| `worktree-state`                               | last-wins        | no        | Worktree enter/exit state, via `worktreeSession` (`src/chunk-j0tbz6ra.js:15294`)           |
| `cost-state`                                   | last-wins        | yes       | Running totals: `totalCostUSD`, API/tool durations, lines added/removed, `modelUsage` (`src/chunk-j0tbz6ra.js:40213`) |
| `queue-operation`                              | last-wins        | yes       | Background task notifications OR user message queue ops                                    |
| `observer-ref`                                 | last-wins        | no        | Observer agent reference (`src/chunk-j0tbz6ra.js:16614`)                                   |

Types earlier revisions of this file listed that are **gone in 2.1.289**:

- `marble-origami-commit` / `-snapshot` / `-reset` — the context-collapse trio, dropped from the
  retention map and from the binary entirely (0 occurrences of `marble-origami`). Present on
  2.1.269; any recipe keyed on them returns empty.
- `speculation-accept` (and its `timeSavedMs` field) — 0 occurrences in the decompiled source,
  0 in any log on disk.
- `task-summary` — absent from the retention map and from every log on disk. Its one remaining
  occurrence in the binary, `src/chunk-92hm4yb6.js:9005`, is a React `key` prop, not an entry type.

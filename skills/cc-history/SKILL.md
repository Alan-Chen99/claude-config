---
name: cc-history
description: Reference documentation for analyzing Claude Code conversation history files
---

# Claude Code History Analysis

Reference documentation for querying and analyzing Claude Code's conversation history. Use shell commands and jq to extract information from JSONL conversation files.

## Directory Structure

```
~/.claude/projects/{encoded-path}/
  |-- {session-uuid}.jsonl          # Main conversation
  |-- {session-uuid}/
      |-- subagents/
      |   |-- agent-{agentId}.jsonl      # Subagent conversations
      |   |-- agent-{agentId}.meta.json  # {"agentType":"Explore","description":"...","toolUseId":"toolu_...","spawnDepth":1}
      |   |-- workflows/wf_{id}/         # Workflow tool runs (see note)
      |-- tool-results/             # Large tool outputs
```

`subagents/workflows/wf_{id}/journal.jsonl` is **not** a transcript. It holds `started` /
`result` records keyed by a content hash, and its sibling `agent-*.jsonl` files are ordinary
subagent transcripts. Exclude the journal from any survey that assumes every `.jsonl` under
`projects/` is a conversation.

## Project Path Resolution

Convert working directory to project directory:

```bash
PROJECT_DIR="$HOME/.claude/projects/$(echo "$PWD" | sed 's|[^a-zA-Z0-9]|-|g')"
```

Encoding rule: **every character outside `[a-zA-Z0-9]` becomes `-`** — slashes, dots,
underscores and spaces alike (`e.replace(/[^a-zA-Z0-9]/g, "-")`,
`src/chunk-jaqbht4s.js:681`). An encoded name longer than 200 characters is cut to 200 and
given a `-<base36 hash>` suffix (`src/chunk-jaqbht4s.js:684`; the limit `N6 = 200` is at
`:677`, the hash at `:678`). The result is joined under `<config dir>/projects/`
(`src/chunk-8jke7x2v.js:20` and `:46`).

Examples (all three are directory names present under `~/.claude/projects/`):

- `/Users/bill/.claude` -> `-Users-bill--claude`
- `/Users/bill/git/myproject` -> `-Users-bill-git-myproject`
- `/root/.emacs.d/elpaca/new/repos/claude-code-emacs` -> `-root--emacs-d-elpaca-new-repos-claude-code-emacs`

The third is the case a slash-only rule gets wrong. `.emacs.d` has a dot that is not
preceded by `/`, and it still becomes `-`; so does an underscore, which is why
`/tmp/foo_bar` lands at `-tmp-foo-bar`, not `-tmp-foo_bar`.

## Message Types

Transcript entries (each JSONL line). The roster below is the binary's own: a type ->
retention-class map at `src/chunk-dbb93264.js:237396-237435`, read by the transcript loader
at `:237586-237605`. It is the only exhaustive enumeration of entry types in 2.1.269. A type
missing from it is not rejected — the lookup falls through to `accumulate`
(`src/chunk-dbb93264.js:237436`).

**Retention** is what the loader's compaction planner does with the entry: `transcript` is
the conversation itself; `accumulate` entries are all kept; `last-wins` keeps only the newest
per session (per `leafUuid` for `summary` — `src/chunk-dbb93264.js:237581`);
`boundary-cleared` entries are the ones no branch re-adds, so they do not survive past the
last compact boundary.

**Seen** records whether the type actually occurs in `~/.claude/projects/` on this machine
(2,591 logs / 372,949 lines; `find ~/.claude/projects -name '*.jsonl' -print0 | xargs -0 cat
| jq -r 'select(type=="object") | .type' | sort | uniq -c | sort -rn`). A `no` means the
feature has not been used here — it is not evidence the type is gone. Two values that survey
turns up, `started` and `result`, are not transcript entries at all: they come from a
Workflow tool journal, `{session}/subagents/workflows/wf_<id>/journal.jsonl`, which is a
different file format that happens to share the `.jsonl` extension. Scope the survey to
`{project}/*.jsonl` and `{session}/subagents/agent-*.jsonl` to exclude it.

| Type                                            | Retention        | Seen | Description                                                                                |
| ----------------------------------------------- | ---------------- | ---- | ------------------------------------------------------------------------------------------ |
| `user`                                          | transcript       | yes  | User input or tool_result (1 content block per entry)                                      |
| `assistant`                                     | transcript       | yes  | Model response (1 content block per entry, normalized)                                     |
| `system`                                        | transcript       | yes  | System messages. `subtype` observed: `turn_duration`, `stop_hook_summary`, `local_command`, `compact_boundary`, `informational`, `away_summary`, `model_consent_fallback`, `agents_killed` |
| `attachment`                                    | transcript       | yes  | Injected context — system-reminders, hook output, skill listings. See "Attachments" below  |
| `progress`                                      | boundary-cleared | no   | Streaming tool progress. `data.type` is `bash_progress` / `agent_progress` / `hook_progress` per `src/claude_config/cc_pretty/parse.py` |
| `file-history-snapshot`                         | boundary-cleared | yes  | File state snapshot (no top-level `timestamp` field)                                       |
| `file-history-delta`                            | boundary-cleared | yes  | Incremental backup against a snapshot; carries `snapshotMessageId`, `trackingPath`, `backup` (`src/chunk-dbb93264.js:240877`) |
| `last-prompt`                                   | boundary-cleared | yes  | Last user prompt (for resume picker)                                                       |
| `continued-in`                                  | boundary-cleared | no   | Names the session this one continued into, via `continuedInSessionId` (`src/chunk-hfnv88ms.js:96`) |
| `marble-origami-commit`                         | boundary-cleared | no   | Context collapse commit                                                                    |
| `marble-origami-snapshot`                       | boundary-cleared | no   | Context collapse staged state                                                              |
| `marble-origami-reset`                          | boundary-cleared | no   | Context collapse reset                                                                     |
| `content-replacement`                           | accumulate       | no   | Large content block replacement records                                                    |
| `fork-context-ref`                              | accumulate       | yes  | Written into a `fork` subagent's own file: `agentId`, `contextLength`, `parentSessionId`, `parentLastUuid` (`src/chunk-dbb93264.js:240418`) |
| `frame-link`                                    | accumulate       | yes  | Artifact frame link; carries `artifactCount` (`src/chunk-dbb93264.js:239436`)              |
| `artifact-comment-monitor`                      | accumulate       | no   | Artifact comment watch record                                                              |
| `summary`                                       | last-wins        | no   | Conversation summary (for resume). Keyed by `leafUuid`, not `sessionId`                    |
| `custom-title`                                  | last-wins        | yes  | User-set session title                                                                     |
| `ai-title`                                      | last-wins        | yes  | AI-generated session title                                                                 |
| `ended-by-model`                                | last-wins        | no   | Session ended by the model (`src/chunk-dbb93264.js:242653`)                                |
| `tag`                                           | last-wins        | no   | Session tag (searchable in /resume)                                                        |
| `relocated`                                     | last-wins        | no   | Session cwd was relocated; carries `relocatedCwd` (`src/chunk-36a8cme1.js:399`)            |
| `agent-name` / `agent-color` / `agent-setting`  | last-wins        | first two | Subagent display metadata                                                             |
| `pr-link`                                       | last-wins        | no   | GitHub PR linked to session: `prNumber`, `prUrl`, `prRepository`, `timestamp` (`src/chunk-dbb93264.js:239428`) |
| `artifact-autoreact-ledger`                     | last-wins        | no   | Artifact auto-reply ledger; the loader repairs torn writes of it (`src/chunk-dbb93264.js:237606`, `:237619`, `:237626`) |
| `bridge-session`                                | last-wins        | yes  | Bridged session: `bridgeSessionId`, `lastSequenceNum` (`src/chunk-dbb93264.js:239443`)     |
| `history-suppression`                           | last-wins        | no   | History suppressed, with `cause` (`src/chunk-jaqbht4s.js:1267`)                            |
| `attribution-snapshot`                          | last-wins        | no   | Attribution snapshot. Written through the same torn-write-tolerant path as the ledger (line-prefix buffer at `src/chunk-jaqbht4s.js:1073`), and exempted from boundary pruning at `src/chunk-dbb93264.js:237698` |
| `mode`                                          | last-wins        | yes  | Session mode. Only `normal` observed here; `coordinator` is the documented other value     |
| `permission-mode`                               | last-wins        | yes  | Session permission mode. Observed: `bypassPermissions`, `default`, `auto`, `acceptEdits`   |
| `isolation-latch`                               | last-wins        | no   | Session isolation `side` (`src/chunk-dbb93264.js:239411`)                                  |
| `atis-latch`                                    | last-wins        | yes  | Latched `atis` value, the `x-cc-atis` request header (`src/chunk-5cs6j3p3.js:24911`)       |
| `worktree-state`                                | last-wins        | no   | Worktree enter/exit state                                                                  |
| `cost-state`                                    | last-wins        | yes  | Running totals: `totalCostUSD`, API/tool durations, lines added (`src/chunk-dbb93264.js:70446`) |
| `queue-operation`                               | last-wins        | yes  | Background task notifications OR user message queue ops                                    |
| `observer-ref`                                  | last-wins        | no   | Observer agent reference (`src/chunk-dbb93264.js:240431`)                                  |

Two types earlier revisions of this file listed are **gone in 2.1.269**:

- `speculation-accept` (and its `timeSavedMs` field) — 0 occurrences in the decompiled
  source, 0 in any log on disk. Any recipe keyed on it returns empty.
- `task-summary` — absent from the retention map and from every log on disk. Its one
  remaining occurrence in the binary, `src/chunk-rjc4dqgx.js:9383`, is a React `key` prop,
  not an entry type.

### Attachments

`attachment` entries are a separate stream from `user`/`assistant`, and they are where
injected context lives — system-reminders included. A reader who treats the three
conversational types as the whole transcript silently drops them; they are the single most
numerous non-conversational type here (71,932 of 372,949 lines). The payload is
`.attachment`, discriminated by `.attachment.type`. This repo's own parser models the
subtypes at `src/claude_config/cc_pretty/parse.py` (`AttachmentData`, `AttachmentRecord`).

```bash
# Attachment subtypes present in a log
jq -r 'select(.type=="attachment") | .attachment.type' file.jsonl | sort | uniq -c | sort -rn

# The model-visible text of a system-reminder-style attachment
jq -r 'select(.type=="attachment" and .attachment.type=="hook_additional_context") |
  .attachment.content | tostring' file.jsonl
```

Subtypes observed here, most frequent first: `hook_success`, `total_tokens_reminder`,
`hook_additional_context`, `deferred_tools_delta`, `skill_listing`, `agent_listing_delta`,
`auto_mode`, `prompt_snapshot`, `queued_command`, `environment`, `command_permissions`,
`date`, `session_context`, `remote_session_change`, `model`, `instructions`,
`edited_text_file`, `date_change`, `nested_memory`, `file`. The field carrying the text
varies by subtype (`text` for `total_tokens_reminder`, `content` for
`hook_additional_context`), so inspect `keys` before assuming one.

## Message Structure

Each line in a JSONL file is a message object. Messages are stored **already normalized**: each entry has exactly 1 content block, even when the API returned multiple blocks in a single response. See "Parallel Tool Calls" below for how to reassemble.

```json
{
  "type": "assistant",
  "uuid": "abc123",
  "parentUuid": "xyz789",
  "timestamp": "2025-01-15T19:39:16.000Z",
  "sessionId": "session-uuid",
  "isSidechain": false,
  "agentId": null,
  "requestId": "req_...",
  "message": {
    "id": "msg_01K...",
    "role": "assistant",
    "content": [{ "type": "tool_use", "name": "Bash", "input": {...}, "id": "toolu_..." }],
    "usage": {
      "input_tokens": 20000,
      "output_tokens": 500,
      "cache_read_input_tokens": 15000,
      "cache_creation_input_tokens": 5000
    }
  }
}
```

Key fields:
- `message.id` — API response message ID. **Shared** across all entries from the same API response (critical for parallel detection)
- `uuid` — unique per JSONL entry (derived via `deriveUUID(baseUuid, index)` for split messages)
- `parentUuid` — links to previous entry in chain
- `isSidechain` — `true` for subagent entries
- `agentId` — subagent identifier (present on sidechain entries)

Assistant message content block types (exactly 1 per entry):

- `type: "thinking"` — model thinking (has `thinking` field)
- `type: "tool_use"` — tool invocation (has `name`, `input`, `id` fields)
- `type: "text"` — text response (has `text` field)

User message content (exactly 1 per entry):

- String — actual user input
- `type: "tool_result"` — tool result (has `tool_use_id`, `content` fields)

## Common Queries

### Find Conversations

```bash
# List by modification time (most recent first)
ls -lt "$PROJECT_DIR"/*.jsonl

# Find by date
ls -la "$PROJECT_DIR"/*.jsonl | grep "Jan 15"

# Find by content
grep -l "search term" "$PROJECT_DIR"/*.jsonl
```

### Extract Messages

```bash
# Get message by line number (1-indexed)
sed -n '42p' file.jsonl | jq .

# Get message by uuid
jq -c 'select(.uuid=="abc123")' file.jsonl

# All user messages
jq -c 'select(.type=="user")' file.jsonl

# All assistant messages
jq -c 'select(.type=="assistant")' file.jsonl
```

### Tool Call Analysis

```bash
# List all tool calls
jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | {name, input}' file.jsonl

# Count tool calls by name
jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | .name' file.jsonl | sort | uniq -c | sort -rn

# Find specific tool calls
jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Bash")' file.jsonl
```

### Skill Invocation Detection

A skill reaches a log by one of three routes, and no single pattern catches all three.

| Route                | Where it appears                                    | Name to extract                              |
| -------------------- | --------------------------------------------------- | -------------------------------------------- |
| `Skill` tool         | `tool_use` block, `name == "Skill"`                 | `.input.skill` (plus optional `.input.args`) |
| `agent-tools skill`  | `tool_use` block, `name == "Bash"`, in `.input.command` | `agent-tools skill <skill_name>.<module>` |
| `python3 -m skills.` | same, `.input.command`                              | `python3 -m skills.<skill_name>.<module>`    |

The `Skill` tool is first-class in 2.1.269 — description at `src/chunk-dbb93264.js:222327`,
input schema `{skill, args?}` at `src/chunk-dbb93264.js:174508-174510`. The two bash routes
are this repo's own convention (`skills/CLAUDE.md`): custom skills go through `agent-tools`,
upstream skills through the direct `python3 -m` call. Both use underscores in the module
path, while `Skill` tool names use hyphens — `decision_critic` and `decision-critic` are the
same skill.

```bash
# Every skill invocation in a log, by route
jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") |
  if .name=="Skill" then "Skill:\(.input.skill)"
  elif .name=="Bash" then
    ((.input.command // "") |
     capture("(?<p>agent-tools skill|python3 -m skills\\.)\\s?(?<n>[a-z_]+)") | "Bash:\(.n)")
  else empty end' file.jsonl | sort | uniq -c | sort -rn

# Find conversations using a specific skill, either spelling, any route
grep -lE '"skill":"planner"|agent-tools skill planner\.|python3 -m skills\.planner\.' \
  "$PROJECT_DIR"/*.jsonl
```

`capture` on a non-matching string yields nothing rather than erroring, so the `Bash` branch
is safe on commands that invoke no skill.

Two cautions when counting. A log records the skill *listing* too — every session carries an
`attachment` of type `skill_listing` naming every available skill — so a bare `grep` for a
skill name finds sessions that merely had it available. And a session that analyses logs
captures other sessions' text as tool output, so string matches in a log about logs are not
invocations. Restricting to `tool_use` blocks, as the jq above does, avoids both.

### Token Usage

```bash
# Total tokens in conversation
jq -s '[.[].message.usage? | select(.) | .input_tokens + .output_tokens] | add' file.jsonl

# Token breakdown
jq -s '[.[].message.usage? | select(.)] | {
  input: (map(.input_tokens) | add),
  output: (map(.output_tokens) | add),
  cached: (map(.cache_read_input_tokens // 0) | add)
}' file.jsonl

# Token progression over time
jq -c 'select(.type=="assistant") | {ts: .timestamp[11:19], inp: .message.usage.input_tokens, out: .message.usage.output_tokens}' file.jsonl
```

### Taxonomy Aggregation

```bash
# Count messages by type
jq -s 'group_by(.type) | map({type: .[0].type, count: length})' file.jsonl

# Character count in user messages
jq -s '[.[] | select(.type=="user") | .message.content | length] | add' file.jsonl

# Thinking block character count
jq -s '[.[] | select(.type=="assistant") | .message.content[]? | select(.type=="thinking") | .thinking | length] | add' file.jsonl
```

### Subagent Analysis

```bash
# List subagents with metadata
for f in "${SESSION_DIR}/subagents/"*.meta.json; do
  echo "$(basename "$f" .meta.json): $(cat "$f")"
done

# Get subagent task description (first user message)
jq -c 'select(.type=="user") | .message.content' "${SESSION_DIR}/subagents/"agent-*.jsonl | head -1

# Find Agent tool calls in parent (these spawn subagents)
jq -c 'select(.type=="assistant" and .message.content[0].type=="tool_use" and
  .message.content[0].name=="Agent") | .message.content[0].input |
  {description, subagent_type}' file.jsonl
```

## Conversation Branching

Each `.jsonl` file contains the **entire conversation tree** (all branches), not separate files per branch. Branching is tracked via `parentUuid`:

- When user goes back in history and issues a new command, the new message gets the same `parentUuid` as where they branched from
- Multiple messages sharing the same `parentUuid` = sibling branches (fork point)

### Detecting Branch Points

```bash
# Find all fork points (messages with multiple children)
jq -s 'group_by(.parentUuid) | map(select(length > 1)) | .[] | {
  parentUuid: .[0].parentUuid,
  branches: length,
  timestamps: [.[].timestamp]
}' file.jsonl

# Show siblings at a known fork point
FORK_POINT="parent-uuid-here"
jq -c --arg fp "$FORK_POINT" 'select(.parentUuid==$fp) | {uuid, ts: .timestamp, preview: (.message.content | tostring)[:100]}' file.jsonl
```

### Extracting a Single Branch

To filter for exactly one branch, find a unique identifier in that branch, then walk the ancestor chain back to root.

**Step 1: Find target message uuid**

```bash
# By unique content
TARGET=$(jq -r 'select(.message.content | tostring | contains("unique-identifier")) | .uuid' file.jsonl | tail -1)

# By timestamp prefix
TARGET=$(jq -r 'select(.timestamp | startswith("2026-01-28T11:23")) | .uuid' file.jsonl | head -1)
```

**Step 2: Extract branch as JSONL stream**

```bash
# Outputs one message per line (JSONL), oldest first
extract_branch() {
  jq -c -s --arg target "$1" '
    (map({(.uuid): .}) | add) as $lookup |
    {chain: [], current: $target} |
    until(.current == null or ($lookup[.current] | not);
      ($lookup[.current]) as $msg |
      .chain += [$msg] |
      .current = $msg.parentUuid
    ) |
    .chain | reverse | .[]
  ' "$2"
}

# Usage: extract_branch <target-uuid> <file>
extract_branch "$TARGET" file.jsonl | jq -s 'length'
extract_branch "$TARGET" file.jsonl | jq 'select(.type=="user")'
```

**Step 3: Common branch queries**

```bash
# Message count
extract_branch "$TARGET" file.jsonl | jq -s 'length'

# User messages only
extract_branch "$TARGET" file.jsonl | jq 'select(.type=="user")'

# Tool calls
extract_branch "$TARGET" file.jsonl | jq 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | {name}'

# First and last messages (verify correct branch)
extract_branch "$TARGET" file.jsonl | jq -s '[.[0], .[-1]] | .[] | {type, ts: .timestamp}'
```

### Workflow: Pinpoint and Explore

```bash
# 1. Find conversation file
FILE=$(grep -l "unique-identifier" "$PROJECT_DIR"/*.jsonl)

# 2. Find matching messages (may show multiple branches)
jq -c 'select(.message.content | tostring | contains("unique-identifier")) | {uuid, ts: .timestamp, parentUuid}' "$FILE"

# 3. Pick target uuid from desired branch, then query
TARGET="uuid-from-step-2"
extract_branch "$TARGET" "$FILE" | jq 'select(.type=="user") | .message.content'
```

## Timing and Concurrency

**Citations in this file.** A bare `src/chunk-<hash>.js:<line>` is
`/repos/claude-code-decompiled/src/`, the 2.1.269 decompile, and is current. Anything
prefixed `claude-code-src/` is `/repos/claude-code-src/`, the **v2.1.88** sourcemap leak —
readable TypeScript, four-plus versions stale, kept only where it names a shape the
decompile does not. Never carry a `claude-code-src/` line number forward as current; chunk
hashes and line numbers both rotate per build, so re-resolve by grepping a string literal
(see `/repos/claude-code-decompiled/README.md`, "Re-resolving an old citation").

Original-name orientation, all **v2.1.88**: types in `claude-code-src/src/types/logs.ts`,
bash tool in `claude-code-src/src/tools/BashTool/BashTool.tsx`, shell command in
`claude-code-src/src/utils/ShellCommand.ts`, agent tool in
`claude-code-src/src/tools/AgentTool/runAgent.ts`, message normalization in
`claude-code-src/src/utils/messages.ts`.

### Timestamps

Most transcript entries have a `timestamp` field (ISO 8601 string, e.g. `"2025-01-15T19:39:16.000Z"`). Set at write time via `new Date().toISOString()`.

Present on, as measured over every log on disk
(`jq -r 'select(type=="object") | "\(.type)\t\(.timestamp != null)"'`): `user`,
`assistant`, `system`, `attachment`, `queue-operation`, `file-history-delta`, `frame-link`.
The binary also stamps one onto `pr-link` (`src/chunk-dbb93264.js:239433`), `continued-in`
(`src/chunk-hfnv88ms.js:97`) and `observer-ref` (`src/chunk-dbb93264.js:240433`) — none of
which occur here, so that is a source reading, not a measurement.

**Not present on**: `file-history-snapshot`, `last-prompt`, `ai-title`, `mode`,
`permission-mode`, `atis-latch`, `cost-state` — every one measured at zero out of thousands
of entries. For `file-history-snapshot`, use surrounding message timestamps as an
approximation, or read the nested `.snapshot.timestamp`.

Additional timing fields outside the JSONL transcript: SDK `result` messages carry
`duration_ms` and `duration_api_ms`, plus optional `ttft_ms`, `ttft_stream_ms` and
`time_to_request_ms` (`src/chunk-5cs6j3p3.js:17676-17685`). These are stream-json output, not
transcript entries — do not expect them in a `.jsonl` under `~/.claude/projects/`. An earlier
revision listed `task-summary` here as well; that entry type no longer exists (see "Message
Types").

Timestamps include milliseconds (e.g. `2026-05-05T18:39:20.417Z`). jq's `fromdateiso8601` requires integer-second format, so strip milliseconds first.

```bash
# Helper: strip milliseconds for fromdateiso8601
# .ts | split(".")[0] + "Z" | fromdateiso8601

# Wall-clock duration between consecutive messages (gaps > 10s)
jq -s '[.[] | select(.timestamp) | {type, ts: .timestamp}] as $msgs |
  [range(1; $msgs | length) | {
    from: $msgs[.-1].type, to: $msgs[.].type,
    gap_s: ((($msgs[.].ts | split(".")[0] + "Z") | fromdateiso8601) -
            (($msgs[.-1].ts | split(".")[0] + "Z") | fromdateiso8601))
  }] | .[] | select(.gap_s > 10)' file.jsonl
```

### Parallel Tool Calls

Messages are stored **already normalized** — each JSONL entry has exactly 1 content block. When the model makes N tool calls in a single API response, the JSONL contains N separate assistant entries, each with 1 `tool_use` block. Similarly, each tool result is a separate user entry with 1 `tool_result` block.

**Detection**: entries from the same API response share `message.id`. Group `tool_use` entries by `message.id` — groups with 2+ entries are parallel.

```bash
# Find parallel tool calls: group tool_use entries by message.id
jq -s '[.[] | select(.type=="assistant" and .message.content[0].type=="tool_use") |
  {mid: .message.id, tool: .message.content[0].name, uuid: .uuid[:8]}] |
  group_by(.mid) | map(select(length > 1)) | .[] |
  {msg_id: .[0].mid, count: length, tools: [.[].tool]}' file.jsonl

# Count how many turns used parallel tool calls
jq -s '[.[] | select(.type=="assistant" and .message.content[0].type=="tool_use") |
  .message.id] | group_by(.) | map(select(length > 1)) | length' file.jsonl
```

The `thinking` block preceding parallel tool calls shares the same `message.id`:

```bash
# Show full API response reconstruction (thinking + tool calls)
jq -s '[.[] | select(.type=="assistant") |
  {mid: .message.id, type: .message.content[0].type,
   name: .message.content[0].name?, uuid: .uuid[:8]}] |
  group_by(.mid) | map(select(length > 1))' file.jsonl | head -30
```

### Parallel Subagents

Subagent conversations are stored in `{session}/subagents/agent-{agentId}.jsonl`
(`src/chunk-8jke7x2v.js:61` builds the directory, `:66` the filename) with a companion
`.meta.json`. Each JSONL entry has `isSidechain: true` and an `agentId` field matching the
filename.

The `.meta.json` is richer than `{agentType, description}`. It is written by
`src/chunk-dbb93264.js:238224` (the file write at `:238238` and `:238245`), and the record
mirrored alongside it at `:238247-238317` enumerates the writable fields: `agentType`,
`isFork`, `isBuiltIn`, `worktreePath`, `worktreeBranch`, `cwd`, `spawnMode`, `description`,
`workflowPhase`, `name`, `toolUseId`, `parentAgentId`, `stoppedByUser`, `spawnDepth`,
`requestShape`, `requestNonInteractive`, `taskKind`, `teamName`, `color`, `planModeRequired`,
`customAgentType`, `model`, `permissionMode`. Every one is conditional — each is spread in
only when defined — so shapes vary widely. Key sets observed across 1,275 files on disk, most
common first:

```
{agentType, description, spawnDepth, toolUseId}
{agentType, description, parentAgentId, spawnDepth, toolUseId}
{agentType, description, model, spawnDepth, toolUseId}
{agentType, description}                                        # older sessions
```

`toolUseId` is the one that matters — see "Correlation" below. `parentAgentId` appears when a
subagent spawned a subagent; `spawnDepth` counts that nesting; `isFork`, `stoppedByUser`,
`requestShape` and `requestNonInteractive` turn up on smaller populations. `agentId` is not a
field — it is the filename.

Subagents that run **in the foreground** (sync) block the parent — the tool_result contains the full agent output.

Subagents that run **in the background** (async via `run_in_background: true`) return immediately. When completed, a `queue-operation` (operation: `enqueue`) with `<task-notification>` content is appended to the parent transcript.

Detection: parallel subagents share the same `message.id` on their `Agent` tool_use entries (same as parallel tool calls). Background agents have `run_in_background: true` in the tool input.

```bash
# Find Agent tool calls and their metadata
jq -c 'select(.type=="assistant" and .message.content[0].type=="tool_use" and
  .message.content[0].name=="Agent") |
  {id: .message.content[0].id, desc: .message.content[0].input.description,
   bg: .message.content[0].input.run_in_background, mid: .message.id}' file.jsonl

# Detect parallel agents: group Agent tool_use by message.id
jq -s '[.[] | select(.type=="assistant" and .message.content[0].type=="tool_use" and
  .message.content[0].name=="Agent") |
  {mid: .message.id, desc: .message.content[0].input.description}] |
  group_by(.mid) | map(select(length > 1)) | .[] |
  {parallel: length, descs: [.[].desc]}' file.jsonl

# List all subagent files with metadata
for f in "${SESSION_DIR}/subagents/"agent-*.meta.json; do
  echo "$(basename "$f" .meta.json): $(cat "$f")"
done

# Find queue-operation task notifications (background completions)
jq -c 'select(.type=="queue-operation" and .operation=="enqueue" and
  (.content // "" | test("<task-notification>"))) |
  {ts: .timestamp, content: .content[:200]}' file.jsonl
```

### Background Commands

When `run_in_background: true` is set on a Bash tool call, the command starts and the tool returns immediately. The tool result `content` string contains:

```
Command running in background with ID: {backgroundTaskId}. Output is being written to: {outputPath}
```

That is one of **four** sentences 2.1.269 can write here — a command can reach the background
without ever being asked to. See "Telling the Background Causes Apart" below; the other three
word the ID differently enough to break a naive parse.

The Bash output schema (`src/chunk-dbb93264.js:215693-215730`) carries these
background-related fields:

| Field                             | Type    | Meaning                                                                        |
| --------------------------------- | ------- | ------------------------------------------------------------------------------ |
| `backgroundTaskId`                | string  | Present whenever the command was backgrounded, however it got there            |
| `backgroundedByUser`              | boolean | The user pressed Ctrl+B                                                        |
| `backgroundedByTurnAbort`         | boolean | `@internal` — a plugin's turn abort moved the running command to the background |
| `backgroundedToDeliverMessage`    | boolean | `@internal` — moved aside so a message queued for the model could reach it     |
| `timedOutAfterMs`                 | number  | Set when the command hit its timeout and was auto-backgrounded; the timeout in ms |
| `backgroundEndsWithFinalResponse` | boolean | The command is owned by a synchronous subagent and dies at that agent's final response |
| `backgroundCwdHint`               | string  | Note that a backgrounded `cd`/`pushd`/`popd`/`chdir` did not change session cwd |

`assistantAutoBackgrounded` is **gone** — 0 occurrences in 2.1.269. It survives only in the
v2.1.88 tree at `claude-code-src/src/tools/BashTool/BashTool.tsx:287`.

In the JSONL transcript these land in two places: the `toolUseResult` object on the `user`
entry carries the raw fields, and the `tool_result` block's `content` string carries the
human-readable message.

```bash
# Raw background fields, straight off toolUseResult
jq -c 'select(.type=="user" and (.toolUseResult|type=="object") and
  .toolUseResult.backgroundTaskId != null) |
  {id: .toolUseResult.backgroundTaskId, byUser: .toolUseResult.backgroundedByUser,
   turnAbort: .toolUseResult.backgroundedByTurnAbort,
   deliver: .toolUseResult.backgroundedToDeliverMessage,
   timedOutMs: .toolUseResult.timedOutAfterMs}' file.jsonl
```

```bash
# Find all backgrounded Bash commands
jq -c 'select(.type=="user") | .message.content[]? |
  select(.type=="tool_result" and (.content | test("background")))' file.jsonl

# Extract background task IDs (all four message shapes)
jq -r 'select(.type=="user") | .message.content[]? |
  select(.type=="tool_result") | (.content | tostring) |
  capture("(?:with|\\() ?ID: (?<id>[A-Za-z0-9_-]+)") | .id' file.jsonl
```

### Telling the Background Causes Apart

In 2.1.269 the tool_result `content` string **names the cause**. One builder writes all four
variants (`src/chunk-dbb93264.js:135046-135057`), choosing by a ternary chain in this
precedence order:

| Cause                              | Field set on `toolUseResult`   | Leading sentence of the tool_result content                                                                            |
| ---------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| User pressed Ctrl+B                | `backgroundedByUser`           | `Command was manually backgrounded by user with ID: {id}. Output is being written to: {path}.`                            |
| Queued message needed to get through | `backgroundedToDeliverMessage` | `Command was moved to the background (ID: {id}) so that a message that arrived while it was running can reach you; it was not interrupted. Output is being written to: {path}.` |
| Hit its `timeout`                  | `timedOutAfterMs`              | `Command did not complete within its {N}s timeout and was moved to the background (ID: {id}). Output is being written to: {path}.` |
| Everything else                    | — (only `backgroundTaskId`)    | `Command running in background with ID: {id}. Output is being written to: {path}.`                                        |

`{N}` is `Math.max(1, Math.round(timedOutAfterMs / 1000))`, so the seconds figure is rounded
and floored at 1 — recover the exact value from `toolUseResult.timedOutAfterMs`, not from the
string.

Two consequences for anyone carrying forward an older reading of this file:

- **Timeout auto-background is no longer indistinguishable from an explicit
  `run_in_background: true`.** They were the same sentence in v2.1.88; they are different
  sentences now, and the timeout case additionally sets `timedOutAfterMs`. The
  cross-reference dance — collect `tool_use` ids that lacked `run_in_background`, then look
  for backgrounded results among them — is no longer needed.
- **The fourth row is a catch-all, not "explicit only."** `backgroundedByTurnAbort` is a real
  schema field (`src/chunk-dbb93264.js:215701`) but the message builder has no branch for it,
  so a turn-abort background produces the same sentence as an explicit
  `run_in_background: true`. Check the field, not the string, to separate those two.

A command backgrounded at its timeout comes back with `backgroundTaskId` and
`timedOutAfterMs` and **no** cause flag — measured on disk, e.g.
`{"backgroundTaskId":"bzaayu0oe","timedOutAfterMs":3000}` alongside
`Command did not complete within its 3s timeout ...`. Its `toolUseResult` keys are
`backgroundTaskId`, `backgroundCwdHint`, `interrupted`, `isImage`, `noOutputExpected`,
`stderr`, `stdout`, `timedOutAfterMs`, sometimes plus `backgroundEndsWithFinalResponse`.

**Which cause flags actually reach the transcript is only partly settled.** Measured over
every log on this machine: `timedOutAfterMs` appears on `toolUseResult` 35 times and
`backgroundEndsWithFinalResponse` 16 times. `backgroundedByUser`,
`backgroundedByTurnAbort` and `backgroundedToDeliverMessage` appear **zero** times — but so
do the events themselves. Counting only tool_result strings that *begin* with each sentence,
this corpus holds 769 explicit backgrounds and 40 timeouts, and **no** Ctrl+B, turn-abort or
deliver-message background at all. So their absence from `toolUseResult` is untested here,
not disproven: the schema declares them (`src/chunk-dbb93264.js:215700-215702`) and this
corpus cannot say whether they survive to disk. Until someone captures one, treat the
`content` string as the reliable signal for those three causes and `timedOutAfterMs` as the
reliable signal for timeout — which is how the two recipes below are ordered.

That same count is a warning about method. All 54 raw string matches for "manually
backgrounded by user" in this corpus sit inside *other* sessions' text, captured as tool
output by sessions that were analysing logs. A `grep` for a message shape finds discussion of
it as readily as an instance of it; anchoring on `startswith` over a `tool_result` block, as
above, is what separates the two.

```bash
# Classify every backgrounded Bash result by cause
jq -r 'select(.type=="user" and (.toolUseResult|type=="object") and
  .toolUseResult.backgroundTaskId != null) |
  (if .toolUseResult.backgroundedByUser then "user-ctrl-b"
   elif .toolUseResult.backgroundedToDeliverMessage then "deliver-message"
   elif .toolUseResult.timedOutAfterMs then "timeout:\(.toolUseResult.timedOutAfterMs)ms"
   elif .toolUseResult.backgroundedByTurnAbort then "turn-abort"
   else "explicit-or-unknown" end)' file.jsonl | sort | uniq -c | sort -rn

# String-only fallback, for logs where toolUseResult was not captured
jq -r 'select(.type=="user") | .message.content[]? |
  select(.type=="tool_result") | (.content | tostring) |
  select(test("background")) |
  if test("manually backgrounded by user") then "user-ctrl-b"
  elif test("so that a message that arrived") then "deliver-message"
  elif test("did not complete within its") then "timeout"
  else "explicit-or-turn-abort" end' file.jsonl | sort | uniq -c
```

The same four causes are reported a second time as a structured `trigger` enum at
`src/chunk-dbb93264.js:216494`, and its precedence differs: `user`, `turn_abort`,
`deliver_message`, then timeout — turn-abort ranks second there and has no branch at all in
the message builder. That path feeds telemetry, not the transcript; the transcript carries
the prose above and the `toolUseResult` fields.

**Removed in 2.1.269: the assistant-mode blocking budget.** Earlier revisions of this file
documented a 15-second `KAIROS` assistant-mode timer that auto-backgrounded blocking commands
with a distinctive `Command exceeded the assistant-mode blocking budget (15s)` result string,
and gave a `test("assistant-mode blocking budget")` recipe for finding it. None of it exists
any more: `KAIROS`, `assistantAutoBackgrounded`, and `assistant-mode blocking budget` are each
0 occurrences across all 1,677 chunks. The recipe returns empty on every log. It lives on only
in the v2.1.88 tree, at `claude-code-src/src/tools/BashTool/BashTool.tsx:973-983`. If you meet
that string in an old log, it is a v2.1.88-era session.

### Queue Operations

`queue-operation` entries serve two purposes:

1. **Task notifications**: `operation: "enqueue"` with `<task-notification>` XML in `content`. Contains `<task-id>`, `<tool-use-id>`, `<output-file>`, `<status>` (completed/failed), `<summary>`. Followed by `operation: "dequeue"` when consumed. Despite the name these are not only background *commands* — `<summary>` prefixes observed on disk are `Background command "X" completed (exit code N)` / `... failed with exit code N`, `Agent "X" finished` / `... failed: ...` / `... was stopped by Claude`, and `Monitor event: "X"` / `Monitor "X" stream ended` / `Monitor "X" script failed (exit N)`.
2. **User message queue**: `operation: "enqueue"` with plain text `content` (user typed while agent was busy). `operation: "remove"` or `"popAll"` when cleared.

```bash
# Separate task notifications from user message queue
jq -c 'select(.type=="queue-operation" and .operation=="enqueue") |
  if (.content // "" | test("<task-notification>"))
  then {kind: "task", ts: .timestamp,
    status: (.content | capture("<status>(?<s>[^<]+)") | .s),
    summary: (.content | capture("<summary>(?<s>[^<]+)") | .s)}
  else {kind: "user-msg", ts: .timestamp, preview: (.content // "")[:80]}
  end' file.jsonl
```

## Correlation

The subagent file name carries an `agentId` (`agent-a0759621527241c34.jsonl`) that the parent
transcript never mentions. Correlate through the companion `.meta.json` instead: it carries
`toolUseId`, which **is** the `id` of the `Agent` `tool_use` block in the parent.

```bash
# agentId -> the parent Agent call that spawned it
for f in "${SESSION_DIR}/subagents/"agent-*.meta.json; do
  id=$(basename "$f" .meta.json)
  tu=$(jq -r '.toolUseId // "none"' "$f")
  echo "$id  $tu  $(jq -r '"\(.agentType): \(.description)"' "$f")"
done

# ...and the other way: from a toolUseId back to the parent's tool_use input
jq -c --arg t "toolu_01RtsuZUajp1KogNP5FLJ5iq" \
  'select(.type=="assistant") | .message.content[]? |
   select(.type=="tool_use" and .id==$t) |
   {name, desc: .input.description, subagent_type: .input.subagent_type}' "$SESSION_FILE"
```

633 of the 641 `.meta.json` files written here since 2026-08-15 carry `toolUseId`; the eight
that do not are agents with no spawning tool call. Older files predating the field have only
`{agentType, description}`.

**The tool is named `Agent`, not `Task`.** A `Task` tool has not existed for some time; in
2.1.269 the only `"Task"` literals left are UI labels for the Ctrl+B background affordance
(`src/chunk-qxhez8yz.js:37`, `:50`, `:60`) and one backward-compatible alias check that
accepts either name (`src/chunk-5cs6j3p3.js:23139`). Correlation recipes keyed on
`.name=="Task"` return nothing.

Fallbacks, when `toolUseId` is absent:

1. `.meta.json` `description` matched against the parent's Agent `tool_use`
   `input.description` — unreliable when several agents share a description
2. `tool_use_id` inside a `<task-notification>` in a `queue-operation` entry, which links to
   the Agent `tool_use` `id` for asynchronous agents

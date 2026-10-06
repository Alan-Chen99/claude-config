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
`src/chunk-v0mb4zbj.js:696`). An encoded name longer than 200 characters is cut to 200 and
given a `-<base36 hash>` suffix (`src/chunk-v0mb4zbj.js:701`; the limit `Nie = 200` is at
`:691`, the hash at `:693`). The result is joined under `<config dir>/projects/`
(`src/chunk-acw83f1p.js:20` and `:46`, literal `i(we(), "projects")`).

Examples (all three are directory names present under `~/.claude/projects/`):

- `/Users/bill/.claude` -> `-Users-bill--claude`
- `/Users/bill/git/myproject` -> `-Users-bill-git-myproject`
- `/root/.emacs.d/elpaca/new/repos/claude-code-emacs` -> `-root--emacs-d-elpaca-new-repos-claude-code-emacs`

The third is the case a slash-only rule gets wrong. `.emacs.d` has a dot that is not
preceded by `/`, and it still becomes `-`; so does an underscore, which is why
`/tmp/foo_bar` lands at `-tmp-foo-bar`, not `-tmp-foo_bar`.

## Message Types

Every JSONL line is one transcript entry, discriminated by `.type`. Four types are the
conversation (`user`, `assistant`, `system`, `attachment`); the other thirty-six are session
metadata the compaction planner retains by class. `record-types.md` has the binary's own roster
with each type's retention class, fields, source citation and whether it occurs on this machine —
read it before writing a recipe keyed on a type, and before concluding a type is gone.

```bash
# Which types a log actually holds
jq -r 'select(type=="object") | .type' file.jsonl | sort | uniq -c | sort -rn
```

### Attachments

`attachment` entries are a separate stream from `user`/`assistant`, and they are where
injected context lives — system-reminders included. A reader who treats the three
conversational types as the whole transcript silently drops them; they are the single most
numerous non-conversational type here (202,192 of 758,257 lines). The payload is
`.attachment`, discriminated by `.attachment.type`. This repo's own parser models the
subtypes at `src/claude_config/cc_pretty/parse.py` (`AttachmentData`, `AttachmentRecord`).

```bash
# Attachment subtypes present in a log
jq -r 'select(.type=="attachment") | .attachment.type' file.jsonl | sort | uniq -c | sort -rn

# The model-visible text of a system-reminder-style attachment
jq -r 'select(.type=="attachment" and .attachment.type=="hook_additional_context") |
  .attachment.content | tostring' file.jsonl
```

Subtypes observed here, most frequent first (measured 2026-10-05): `hook_success`,
`total_tokens_reminder`, `output_style`, `hook_additional_context`,
`bash_output_audience_note`, `deferred_tools_delta`, `environment`,
`batching_reminder_sent`, `prompt_snapshot`, `skill_listing`, `date`,
`agent_listing_delta`, `session_context`, `model`, `auto_mode`, `instructions`,
`queued_command`, `task_reminder`, `command_permissions`, `nested_memory`,
`edited_text_file`, `silent_turn_reminder`, `mcp_instructions_delta`,
`deferred_tools_record`, `remote_session_change`, `file`, `compact_file_reference`,
`invoked_skills`, `read_truncation_notice`, `date_change`, `ultrathink_effort`,
`hook_blocking_error`, `task_status`, `advisor_tool`, `hook_non_blocking_error`. The field
carrying the text varies by subtype (`text` for `total_tokens_reminder`, `content` for
`hook_additional_context`), so inspect `keys` before assuming one. The roster is open: fifteen
of the subtypes above are ones an earlier revision of this list did not have, so re-run the
survey rather than trusting the list.

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

The `Skill` tool is first-class in 2.1.289 — description at `src/chunk-wgfrtm7w.js:133343`,
input schema `{skill, args?}` at `src/chunk-qec902z2.js:594-597` (literal `The name of a skill
from the available-skills list`). The two bash routes
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
`/repos/claude-code-decompiled/src/`, the 2.1.289 decompile, and is current. Anything
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
The binary also stamps one onto `pr-link` (`src/chunk-wgfrtm7w.js:172375`), `frame-link`
(`:172381`), `memory-mode` (`:172345`), `ended-by-model` (`:175786`), `continued-in`
(`src/chunk-bfmr5z4y.js:147`) and `observer-ref` (`src/chunk-wgfrtm7w.js:173495`) — only
`frame-link` occurs here, so the rest is a source reading, not a measurement.

**Not present on**: `file-history-snapshot`, `last-prompt`, `ai-title`, `mode`,
`permission-mode`, `atis-latch`, `cost-state` — every one measured at zero out of thousands
of entries. For `file-history-snapshot`, use surrounding message timestamps as an
approximation, or read the nested `.snapshot.timestamp`.

Additional timing fields outside the JSONL transcript: SDK `result` messages carry
`duration_ms` and `duration_api_ms`, plus optional `ttft_ms`, `ttft_stream_ms` and
`time_to_request_ms` (`src/chunk-ps4gchhg.js:7634-7638`, literal `time_to_request_ms`; four
more `@internal` timing fields follow it). These are stream-json output, not
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
(`src/chunk-acw83f1p.js:67` builds the directory, `:72` the filename) with a companion
`.meta.json`. Each JSONL entry has `isSidechain: true` and an `agentId` field matching the
filename.

The `.meta.json` is richer than `{agentType, description}`. It is written by
`src/chunk-wgfrtm7w.js:171031` (literal `persistAgentMetadata: storage write failed`; the file
write at `:171044` and `:171052`), and the record mirrored alongside it at `:171055-171123`
enumerates the writable fields: `agentType`,
`isFork`, `isBuiltIn`, `worktreePath`, `worktreeBranch`, `cwd`, `spawnMode`, `description`,
`workflowPhase`, `name`, `toolUseId`, `parentAgentId`, `stoppedByUser`, `spawnDepth`,
`requestShape`, `requestNonInteractive`, `taskKind`, `teamName`, `color`, `planModeRequired`,
`customAgentType`, `model`, `permissionMode`. Every one is conditional — each is spread in
only when defined — so shapes vary widely. Key sets observed across 2,354 files on disk, most
common first (measured 2026-10-05):

```
{agentType, description}                                        # older sessions
{agentType, description, model, requestNonInteractive, requestShape, spawnDepth, toolUseId}
{agentType, description, spawnDepth, toolUseId}
{agentType, description, requestNonInteractive, requestShape, spawnDepth, toolUseId}
{agentType, description, parentAgentId, spawnDepth, toolUseId}
{agentType, description, model, requestNonInteractive, requestShape, spawnDepth, workflowPhase}
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

When `run_in_background: true` is set on a Bash tool call, the command starts and the tool returns
immediately, and the `tool_result` content opens `Command running in background with ID: {id}.
Output is being written to: {path}.` That is one of **four** sentences 2.1.289 can write there — a
command can reach the background without ever being asked to, and two of the other three word the
ID differently enough to break a naive parse. The causes, the `toolUseResult` fields that carry
them, the classification recipes and what this machine's corpus can and cannot settle are in
`background-commands.md`.

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

1,558 of the 1,720 `.meta.json` files written here since 2026-08-15 carry `toolUseId`; of the
162 that do not, 151 carry `workflowPhase` instead — a workflow-phase agent has no spawning
`Agent` tool call. Older files predating the field have only `{agentType, description}`.

**In the transcript the tool is named `Agent`, not `Task`.** `"Task"` survives in 2.1.289 as a
name constant (`src/chunk-qws8heqd.js:17`, beside `ht = "Agent"` at `:11`), as keybinding-context
labels for the Ctrl+B background affordance (`src/chunk-1r3smv21.js:39`, `:52`;
`src/chunk-f4qx496g.js:189`, literal `task:background`), in the permission-rule name list
(`src/chunk-c06bg8hw.js:33555`, literal `BUILTIN_TOOL_NAMES`), and in alias checks that accept
either name (`src/chunk-g83p48tw.js:18211`, literal `e !== "Agent" && e !== "Task"`). One of
those matters when you read exported sessions rather than JSONL: SDK and
`--output-format stream-json` output renames `Agent` to `Task` on the way out
(`src/chunk-43jbw5qg.js:64`, applied to the `init` message's `tools` at `:141` and to a
permission request's `tool_name` at `src/chunk-mgxpmmsq.js:8725`) — pre-existing, not new in
this build. Inside a `.jsonl` under `~/.claude/projects/` the name is always `Agent`, so
correlation recipes keyed on `.name=="Task"` return nothing there.

Fallbacks, when `toolUseId` is absent:

1. `.meta.json` `description` matched against the parent's Agent `tool_use`
   `input.description` — unreliable when several agents share a description
2. `tool_use_id` inside a `<task-notification>` in a `queue-operation` entry, which links to
   the Agent `tool_use` `id` for asynchronous agents

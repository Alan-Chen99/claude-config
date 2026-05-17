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
      |   |-- agent-{agentId}.meta.json  # {"agentType":"Explore","description":"..."}
      |-- tool-results/             # Large tool outputs
```

## Project Path Resolution

Convert working directory to project directory:

```bash
PROJECT_DIR="~/.claude/projects/$(echo "$PWD" | sed 's|^/|-|; s|/\.|--|g; s|/|-|g')"
```

Encoding rules:

- Leading `/` becomes `-`
- Regular `/` becomes `-`
- `/.` (hidden directory) becomes `--`

Examples:

- `/Users/bill/.claude` -> `-Users-bill--claude`
- `/Users/bill/git/myproject` -> `-Users-bill-git-myproject`

## Message Types

Transcript entries (each JSONL line):

| Type                        | Description                                             |
| --------------------------- | ------------------------------------------------------- |
| `user`                      | User input or tool_result (1 content block per entry)   |
| `assistant`                 | Model response (1 content block per entry, normalized)  |
| `system`                    | System messages                                         |
| `queue-operation`           | Background task notifications OR user message queue ops |
| `file-history-snapshot`     | File state snapshot (no `timestamp` field)              |
| `summary`                   | Conversation summary (for resume)                       |
| `task-summary`              | Periodic agent status (has `timestamp`, `summary`)      |
| `custom-title`              | User-set session title                                  |
| `ai-title`                  | AI-generated session title                              |
| `last-prompt`               | Last user prompt (for resume picker)                    |
| `tag`                       | Session tag (searchable in /resume)                     |
| `pr-link`                   | GitHub PR linked to session                             |
| `agent-name` / `agent-color` / `agent-setting` | Subagent display metadata               |
| `mode`                      | Session mode (`coordinator` or `normal`)                |
| `worktree-state`            | Worktree enter/exit state                               |
| `content-replacement`       | Large content block replacement records                 |
| `marble-origami-commit`     | Context collapse commit                                 |
| `marble-origami-snapshot`   | Context collapse staged state                           |
| `speculation-accept`        | Speculation accepted (has `timeSavedMs`)                 |

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

Pattern: `python3 -m skills\.([a-z_]+)\.`

```bash
# Find all skill invocations
grep -oE "python3 -m skills\.[a-z_]+" file.jsonl | sort -u

# Find conversations using a specific skill
grep -l "python3 -m skills\.planner\." "$PROJECT_DIR"/*.jsonl
```

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

Source: `claude-code-src/` — types in `src/types/logs.ts`, bash tool in `src/tools/BashTool/BashTool.tsx`, shell command in `src/utils/ShellCommand.ts`, agent tool in `src/tools/AgentTool/runAgent.ts`, message normalization in `src/utils/messages.ts`.

### Timestamps

Most transcript entries have a `timestamp` field (ISO 8601 string, e.g. `"2025-01-15T19:39:16.000Z"`). Set at write time via `new Date().toISOString()`.

Present on: `user`, `assistant`, `system`, `queue-operation`, `task-summary`, `pr-link`, `speculation-accept`.

**Not present on**: `file-history-snapshot` (use surrounding message timestamps as approximation).

Additional timing fields outside the JSONL transcript:
- SDK result messages include `duration_ms` and `duration_api_ms` (total turn duration)
- `task-summary` entries include a separate `timestamp` for periodic agent status snapshots

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

Subagent conversations are stored in `{session}/subagents/agent-{agentId}.jsonl` with a companion `.meta.json` file containing `{"agentType":"Explore","description":"..."}`. Each JSONL entry has `isSidechain: true` and `agentId` field.

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

The Bash output schema (`src/tools/BashTool/BashTool.tsx:285-287`) includes:
- `backgroundTaskId` (string) — always present when backgrounded
- `backgroundedByUser` (boolean) — true if user pressed Ctrl+B
- `assistantAutoBackgrounded` (boolean) — true if assistant-mode budget exceeded

These fields appear in the raw tool output data. In the JSONL transcript, the tool_result `content` string contains the human-readable message with the background ID.

```bash
# Find all backgrounded Bash commands
jq -c 'select(.type=="user") | .message.content[]? |
  select(.type=="tool_result" and (.content | test("background")))' file.jsonl

# Extract background task IDs
jq -r 'select(.type=="user") | .message.content[]? |
  select(.type=="tool_result") | .content |
  capture("background.*ID: (?<id>[^ .]+)") | .id' file.jsonl
```

### Auto-Background After Timeout

Two distinct auto-background mechanisms exist:

1. **Tool timeout auto-background** (`ShellCommand.ts:135-141`): When the Bash tool's `timeout` parameter expires, if `shouldAutoBackground` is true, the command is backgrounded instead of killed. The `onTimeout` callback calls `shellCommand.background(taskId)`. The tool result content string says:
   ```
   Command running in background with ID: {id}. Output is being written to: {path}
   ```
   This is **indistinguishable** from an explicit `run_in_background: true` in the tool_result content — both produce the same message format.

2. **Assistant-mode blocking budget** (`BashTool.tsx:973-983`): In assistant mode (feature `KAIROS`), a 15-second timer auto-backgrounds any main-thread blocking command. The tool result content says:
   ```
   Command exceeded the assistant-mode blocking budget (15s) and was moved to the background with ID: {id}. ...
   ```
   This message is unique and detectable.

Detection strategy:

```bash
# Find assistant-mode auto-backgrounded commands (unique message)
jq -c 'select(.type=="user") | .message.content[]? |
  select(.type=="tool_result" and (.content | test("assistant-mode blocking budget")))' file.jsonl

# Find timeout-triggered or explicit backgrounds (same message format)
# Distinguish by checking if the preceding tool_use had run_in_background: true
# If run_in_background was NOT set, it was a timeout auto-background
jq -c 'select(.type=="assistant") | .message.content[]? |
  select(.type=="tool_use" and .name=="Bash" and
    (.input.run_in_background != true) and
    (.input.timeout != null))' file.jsonl

# Cross-reference: find Bash calls where result was backgrounded but input had no run_in_background
# Step 1: get tool_use IDs without run_in_background
jq -r 'select(.type=="assistant") | .message.content[]? |
  select(.type=="tool_use" and .name=="Bash" and (.input.run_in_background != true)) |
  .id' file.jsonl > /tmp/foreground_ids.txt
# Step 2: find tool_results for those IDs that mention "background"
jq -c --slurpfile ids <(jq -R . /tmp/foreground_ids.txt) '
  select(.type=="user") | .message.content[]? |
  select(.type=="tool_result" and
    (.tool_use_id as $id | $ids | any(. == $id)) and
    (.content | test("background")))' file.jsonl
```

Key distinction: `run_in_background: true` in the tool input means the model requested it. Absence of `run_in_background` + backgrounded result = timeout or assistant-mode auto-background. The "assistant-mode blocking budget" substring in the result uniquely identifies the KAIROS auto-background; all other auto-backgrounds are timeout-triggered.

### Queue Operations

`queue-operation` entries serve two purposes:

1. **Background task notifications**: `operation: "enqueue"` with `<task-notification>` XML in `content`. Contains `<task-id>`, `<tool-use-id>`, `<output-file>`, `<status>` (completed/failed), `<summary>`. Followed by `operation: "dequeue"` when consumed.
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

Subagent files (`agent-{agentId}.jsonl`) correlate to parent via:

1. `.meta.json` file: contains `agentType` and `description`
2. Match `description` to Agent `tool_use` blocks in parent by `input.description`
3. `tool_use_id` in `<task-notification>` links to the Agent tool_use `id` for background agents

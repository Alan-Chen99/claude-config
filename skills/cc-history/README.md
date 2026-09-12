# Claude Code History Analysis

Reference documentation for analyzing Claude Code conversation history files. This skill provides query patterns and structural knowledge for extracting insights from JSONL conversation logs.

## When to Use

- Analyzing token usage patterns in past conversations
- Finding conversations by date, content, or skill usage
- Understanding main-agent/sub-agent interaction patterns
- Debugging why a conversation grew large or behaved unexpectedly
- Extracting specific messages or tool invocations from history

## When NOT to Use

- Real-time conversation analysis (use current context instead)
- Modifying conversation history (files are append-only logs)
- Cross-project analysis (each project has separate history)

## Architecture

Claude Code stores conversation history in `~/.claude/projects/` with directories named after encoded working directory paths.

```
~/.claude/projects/
  |-- -Users-leon--claude/              # /Users/leon/.claude
  |   |-- {session-uuid}.jsonl          # Main conversation
  |   |-- {session-uuid}/
  |       |-- subagents/
  |       |   |-- agent-{agentId}.jsonl     # Subagent conversations
  |       |   |-- agent-{agentId}.meta.json # Agent type, description, toolUseId
  |       |-- tool-results/             # Large tool outputs
  |-- -Users-leon-git-myproject/        # /Users/leon/git/myproject
      |-- ...
```

### Path Encoding

Working directory paths are encoded by a single rule: **every character outside
`[a-zA-Z0-9]` becomes `-`**, then names over 200 characters get truncated and hashed. The
familiar slash cases are consequences of it, not the rule:

| Original         | Encoded          | Why                                        |
| ---------------- | ---------------- | ------------------------------------------ |
| `/Users/leon`    | `-Users-leon`    | Each `/` is non-alphanumeric               |
| `/git/project`   | `-git-project`   | Same                                       |
| `/.claude`       | `--claude`       | `/` and `.` are each replaced, giving two  |
| `/tmp/foo_bar`   | `-tmp-foo-bar`   | An underscore is replaced too              |
| `/root/.emacs.d` | `-root--emacs-d` | A dot not preceded by `/` is still replaced |

SKILL.md, "Project Path Resolution", has the working `sed` and the source citations. Keep the
two in step — a `/`-only rule silently produces a directory name that does not exist.

### Message Format

Each line in a JSONL file is a self-contained message with:

- `type`: Entry type. `user`, `assistant`, `system` and `attachment` are the four that make
  up the conversation itself; the other ~34 are session metadata and bookkeeping. See
  SKILL.md, "Message Types", for the full roster and its source citation — a reader who
  treats the conversational types as the whole file silently drops the `attachment` stream,
  which is where system-reminders, hook output and skill listings live
- `uuid`: Unique identifier for this message
- `parentUuid`: Links to predecessor message (forms conversation chain)
- `timestamp`: ISO 8601 timestamp, with milliseconds. Present on the conversational types
  and a few others; absent on most session-metadata types (SKILL.md, "Timestamps", has the
  measured list)
- `message`: Payload containing role, content, and usage statistics

Assistant messages have structured content blocks:

- Thinking blocks: Internal reasoning (signature-protected)
- Tool use blocks: Tool invocations with name and input
- Text blocks: Response text shown to user

## Invisible Knowledge

### Why Documentation-Only (No Python Scripts)

Shell commands + jq compose better than custom tooling for this use case:

1. **Format is stable**: JSONL with consistent schema
2. **Queries are ad-hoc**: No two analyses are identical
3. **jq is powerful**: Handles all JSON transformations needed
4. **Maintenance burden**: Python code requires updates when format changes

The documentation approach lets the LLM compose queries on demand rather than learning a custom API.

### Skill Recognition Has Three Patterns, Not One

A single regex used to be enough, when `python3 -m skills.{name}.{module}` was the only way a
skill got run. It no longer is, and the old regex silently under-counts rather than failing:

1. **The `Skill` tool.** Claude Code 2.1.269 has a first-class `Skill` tool, input
   `{skill, args?}`. It leaves a `tool_use` block, not a shell command, so no command-line
   regex sees it at all.
2. **`agent-tools skill {name}.{module}`.** This repo's own convention for custom skills
   (`skills/CLAUDE.md`). Also invisible to the old regex.
3. **`python3 -m skills.{name}.{module}`.** Still live, for upstream skills.

All three coexist in the logs on this machine. The right shape is therefore a small jq
expression over `tool_use` blocks rather than a regex over raw text — it also avoids two
false-positive sources a `grep` cannot: the per-session `skill_listing` attachment, which
names every *available* skill, and sessions that analyse other sessions and so quote their
text. SKILL.md, "Skill Invocation Detection", carries the expression.

The underlying design decision still holds: no enumeration of valid skill names is needed.
Note only that the two bash routes spell names with underscores and the `Skill` tool with
hyphens, so `decision_critic` and `decision-critic` are one skill.

### Subagent Correlation Is Cheap Now

This section used to describe a three-step text-matching dance, on the premise that the
`agentId` in the filename appears nowhere in the parent. The premise is still true; the
conclusion is not, because the companion `.meta.json` carries `toolUseId`, and that is
verbatim the `id` of the `Agent` `tool_use` block in the parent. One `jq -r .toolUseId` per
file and the join is exact.

Two corrections to the old text while we are here. The tool is **`Agent`**, not `Task` —
recipes keyed on `.name=="Task"` return nothing. And the `.meta.json` was already documented
in SKILL.md, so the two files disagreed with each other; they now agree.

Description-matching survives only as a fallback for `.meta.json` files old enough to predate
`toolUseId` (8 of 641 written here since 2026-08-15). It is unreliable when several agents
share a description, which parallel fan-out makes common — another reason the old advice was
worth replacing rather than keeping.

### Token Usage Fields

The four fields worth summing:

- `input_tokens`: Tokens in prompt (excluding cache)
- `output_tokens`: Tokens in response
- `cache_read_input_tokens`: Tokens read from cache
- `cache_creation_input_tokens`: Tokens written to cache

Total billable input = `input_tokens + cache_creation_input_tokens` (cache reads are cheaper).

They are not the whole object. A 2.1.269 assistant entry's `usage` carries eleven keys:
the four above plus `cache_creation` (a `{ephemeral_5m_input_tokens,
ephemeral_1h_input_tokens}` breakdown), `service_tier`, `inference_geo`, `iterations`,
`output_tokens_details`, `server_tool_use` and `speed`. Read `keys` before assuming a shape;
`jq -c 'select(.type=="assistant") | .message.usage | keys' file.jsonl | sort -u` settles it
for a given log.

## Example Usage

### Find Large Conversations

```bash
# Find conversations over 1MB
find "$PROJECT_DIR" -name "*.jsonl" -size +1M

# Get token totals for each
for f in "$PROJECT_DIR"/*.jsonl; do
  tokens=$(jq -s '[.[].message.usage? | select(.) | .input_tokens] | add' "$f")
  echo "$tokens $f"
done | sort -rn | head -10
```

### Analyze Skill Usage

```bash
# Which skills were used in a conversation? (all three invocation routes)
jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") |
  if .name=="Skill" then .input.skill
  elif .name=="Bash" then
    ((.input.command // "") |
     capture("(?:agent-tools skill|python3 -m skills\\.)\\s?(?<n>[a-z_]+)") | .n)
  else empty end' file.jsonl | sort -u

# Find all planner skill conversations (hyphen and underscore spellings)
grep -lE '"skill":"planner"|agent-tools skill planner\.|python3 -m skills\.planner\.' \
  "$PROJECT_DIR"/*.jsonl
```

### Token Growth Analysis

```bash
# Show token progression (identify where context grew)
jq -c 'select(.type=="assistant" and .message.usage.input_tokens > 50000) |
  {ts: .timestamp[11:19], tokens: .message.usage.input_tokens}' file.jsonl
```

## Related Skills

This skill provides the structural knowledge for history analysis. For analyzing specific patterns:

- **refactor**: Use when analyzing code quality patterns in past sessions
- **problem-analysis**: Use when investigating root causes of issues found in history
